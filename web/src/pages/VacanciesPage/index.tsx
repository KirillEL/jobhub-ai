import { useEffect, useMemo, useState } from 'react'
import { fetchVacancies } from '../../api.ts'
import { useAuth } from '../../auth/AuthContext'
import { useVacancySearch } from '../../features/vacancies/useVacancySearch'
import { useI18n } from '../../shared/i18n'
import Button from '../../shared/ui/Button'
import Card from '../../shared/ui/Card'
import EmptyState from '../../shared/ui/EmptyState'
import PageHeader from '../../shared/ui/PageHeader'
import type { Vacancy } from '../../types'
import { formatSalary } from '../../utils/vacancy'
import './styles.scss'

type ExportMode = 'visible' | 'full'
type SortKey = 'title' | 'company' | 'city' | 'salary'
type SortDirection = 'asc' | 'desc'
type ExportState =
  | null
  | { type: 'preparing' }
  | { type: 'progress'; current: number; total: number; percent: number }
  | { type: 'done'; count: number }
  | { type: 'error'; message: string }

export default function VacanciesPage() {
  const { accessToken } = useAuth()
  const { t } = useI18n()
  const vacancies = useVacancySearch(accessToken)
  const [selectedVacancy, setSelectedVacancy] = useState<Vacancy | null>(null)
  const [isExportingAll, setIsExportingAll] = useState(false)
  const [exportState, setExportState] = useState<ExportState>(null)
  const [exportMode, setExportMode] = useState<ExportMode>('visible')
  const [sortKey, setSortKey] = useState<SortKey>('title')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  const [filtersOpen, setFiltersOpen] = useState(false)

  const pageRows = useMemo(() => {
    const rows = vacancies.items.map((item) => ({
      id: item.external_id,
      title: item.title,
      company: item.company ?? 'Не указана',
      city: item.city ?? '-',
      salary: formatSalary(item),
      vacancy: item,
    }))

    const getSalaryValue = (vacancy: Vacancy): number => {
      if (vacancy.salary_from != null) return vacancy.salary_from
      if (vacancy.salary_to != null) return vacancy.salary_to
      return Number.NEGATIVE_INFINITY
    }

    rows.sort((left, right) => {
      if (sortKey === 'salary') {
        const compared = getSalaryValue(left.vacancy) - getSalaryValue(right.vacancy)
        return sortDirection === 'asc' ? compared : -compared
      }

      const leftValue =
        sortKey === 'title' ? left.title : sortKey === 'company' ? left.company : left.city
      const rightValue =
        sortKey === 'title' ? right.title : sortKey === 'company' ? right.company : right.city
      const compared = leftValue.localeCompare(rightValue, 'ru')
      return sortDirection === 'asc' ? compared : -compared
    })

    return rows
  }, [sortDirection, sortKey, vacancies.items])

  useEffect(() => {
    if (!vacancies.items.length) {
      setSelectedVacancy(null)
      return
    }
    setSelectedVacancy((current) => {
      if (!current) return null
      return vacancies.items.find((item) => item.external_id === current.external_id) ?? null
    })
  }, [vacancies.items])

  function toCsvCell(value: string): string {
    return `"${value.replace(/"/g, '""')}"`
  }

  function handleSort(nextSortKey: SortKey): void {
    if (sortKey === nextSortKey) {
      setSortDirection((current) => (current === 'asc' ? 'desc' : 'asc'))
      return
    }
    setSortKey(nextSortKey)
    setSortDirection('asc')
  }

  function buildCsvLines(items: Vacancy[], mode: ExportMode): string[] {
    if (mode === 'visible') {
      const headers = [
        t('vacancies.table.title'),
        t('vacancies.table.company'),
        t('vacancies.table.city'),
        t('vacancies.table.salary'),
      ]
      const lines = [headers.map((cell) => toCsvCell(cell)).join(',')]
      for (const item of items) {
        lines.push(
          [item.title, item.company ?? t('common.notSpecifiedFem'), item.city ?? '-', formatSalary(item)]
            .map((cell) => toCsvCell(String(cell)))
            .join(','),
        )
      }
      return lines
    }

    const headers = [
      t('common.id'),
      t('vacancies.table.title'),
      t('vacancies.table.company'),
      t('vacancies.table.city'),
      t('vacancies.table.salary'),
      t('vacancies.preview.experience'),
      t('vacancies.preview.schedule'),
      t('vacancies.preview.sourceLink'),
    ]
    const lines = [headers.map((cell) => toCsvCell(cell)).join(',')]
    for (const item of items) {
      lines.push(
        [
          item.external_id,
          item.title,
          item.company ?? '',
          item.city ?? '',
          formatSalary(item),
          item.experience ?? '',
          item.schedule ?? '',
          item.url,
        ]
          .map((cell) => toCsvCell(String(cell)))
          .join(','),
      )
    }
    return lines
  }

  function handleExportCsv(): void {
    if (!pageRows.length) return
    const lines = buildCsvLines(
      pageRows.map((row) => row.vacancy),
      exportMode,
    )

    const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8' })
    const href = window.URL.createObjectURL(blob)
    const link = window.document.createElement('a')
    const stamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
    link.href = href
    link.download = `vacancies-page-${stamp}.csv`
    window.document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(href)
  }

  async function handleExportAllCsv(): Promise<void> {
    if (isExportingAll) return

    setIsExportingAll(true)
    setExportState({ type: 'preparing' })
    try {
      const limit = 500
      let offset = 0
      let total = 0
      const allItems: Vacancy[] = []

      do {
        const response = await fetchVacancies(
          {
            search: vacancies.filters.search.trim() || undefined,
            city: vacancies.filters.city.trim() || undefined,
            experience: vacancies.filters.experience.trim() || undefined,
            limit,
            offset,
          },
          accessToken ?? undefined,
        )
        allItems.push(...response.items)
        total = response.total
        offset += response.items.length
        const percent = total ? Math.min(100, Math.round((allItems.length / total) * 100)) : 100
        setExportState({ type: 'progress', current: allItems.length, total: total || allItems.length, percent })
        if (response.items.length === 0) break
      } while (offset < total)
      const lines = buildCsvLines(allItems, exportMode)
      const blob = new Blob([`\uFEFF${lines.join('\n')}`], { type: 'text/csv;charset=utf-8' })
      const href = window.URL.createObjectURL(blob)
      const link = window.document.createElement('a')
      const stamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
      link.href = href
      link.download = `vacancies-all-${stamp}.csv`
      window.document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(href)
      setExportState({ type: 'done', count: allItems.length })
    } catch (error) {
      setExportState({ type: 'error', message: error instanceof Error ? error.message : 'Export failed' })
    } finally {
      setIsExportingAll(false)
    }
  }

  const filterTags = [
    vacancies.filters.search.trim() && { key: 'search', label: vacancies.filters.search.trim() },
    vacancies.filters.city.trim() && { key: 'city', label: vacancies.filters.city.trim() },
    vacancies.filters.experience.trim() && {
      key: 'exp',
      label: vacancies.filters.experience.trim(),
    },
    vacancies.filters.limit !== 50 && { key: 'limit', label: String(vacancies.filters.limit) },
  ].filter(Boolean) as { key: string; label: string }[]

  return (
    <main className="layout vacancies-page">
      <PageHeader title={t('vacancies.title')} subtitle={t('vacancies.subtitle')} />

      <Card className={`filters-panel ${filtersOpen ? 'is-open' : ''}`}>
        <button
          type="button"
          className="filters-panel__toggle"
          onClick={() => setFiltersOpen((open) => !open)}
          aria-expanded={filtersOpen}
          aria-controls="filters-panel-body"
        >
          <span className="filters-panel__chevron" aria-hidden>
            {filtersOpen ? '▼' : '▶'}
          </span>
          <span className="filters-panel__title">{t('vacancies.filtersPanelTitle')}</span>
          {!filtersOpen && (
            <span className="filters-panel__summary">
              {filterTags.length > 0
                ? filterTags.map((tag) => (
                    <span key={tag.key} className="filters-panel__tag">
                      {tag.label}
                    </span>
                  ))
                : (
                    <span className="filters-panel__tag filters-panel__tag--empty">
                      {t('vacancies.filtersSummaryNone')}
                    </span>
                  )}
            </span>
          )}
        </button>
        <div id="filters-panel-body" className="filters-panel__body" hidden={!filtersOpen}>
          <form className="filters-grid" onSubmit={(event) => event.preventDefault()}>
            <label>
              {t('vacancies.filters.search')}
              <input
                value={vacancies.filters.search}
                onChange={(event) => vacancies.updateFilter('search', event.target.value)}
                placeholder={t('vacancies.filters.searchPlaceholder')}
              />
            </label>
            <label>
              {t('vacancies.filters.city')}
              <input
                value={vacancies.filters.city}
                onChange={(event) => vacancies.updateFilter('city', event.target.value)}
                placeholder={t('vacancies.filters.cityPlaceholder')}
              />
            </label>
            <label>
              {t('vacancies.filters.experience')}
              <input
                value={vacancies.filters.experience}
                onChange={(event) => vacancies.updateFilter('experience', event.target.value)}
                placeholder={t('vacancies.filters.experiencePlaceholder')}
              />
            </label>
            <label>
              {t('vacancies.filters.limit')}
              <input
                type="number"
                min={1}
                max={500}
                value={vacancies.filters.limit}
                onChange={(event) => vacancies.updateFilter('limit', Number(event.target.value))}
              />
            </label>
            <Button
              type="button"
              onClick={() => void vacancies.reload(0)}
              disabled={vacancies.loading || vacancies.hasErrors}
            >
              {t('common.apply')}
            </Button>
          </form>
          {vacancies.errors.search ? <p className="field-error">{vacancies.errors.search}</p> : null}
          {vacancies.errors.city ? <p className="field-error">{vacancies.errors.city}</p> : null}
          {vacancies.errors.experience ? <p className="field-error">{vacancies.errors.experience}</p> : null}
          {vacancies.errors.limit ? <p className="field-error">{vacancies.errors.limit}</p> : null}
        </div>
      </Card>

      <section className="vacancies-workspace">
        <Card className="vacancies-table-card">
          <div className="table-tools">
            <p>
              {t('common.resultLabel')}: {vacancies.total} | {t('common.pageLabel')} {vacancies.currentPage} /{' '}
              {vacancies.totalPages}
            </p>
            <div className="table-tools__actions">
              <label title={t('common.exportMode')}>
                {t('common.exportModeShort')}
                <select
                  value={exportMode}
                  onChange={(event) => setExportMode(event.target.value as ExportMode)}
                  disabled={isExportingAll}
                >
                  <option value="visible">{t('common.exportModeVisible')}</option>
                  <option value="full">{t('common.exportModeFull')}</option>
                </select>
              </label>
              <Button type="button" variant="secondary" onClick={handleExportCsv} disabled={!pageRows.length} title={t('common.exportCsvPage')}>
                {t('common.exportCsvPageShort')}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => void handleExportAllCsv()}
                disabled={isExportingAll || vacancies.loading || vacancies.total === 0}
                title={t('common.exportCsvAll')}
              >
                {isExportingAll ? t('common.exportInProgress') : t('common.exportCsvAllShort')}
              </Button>
              <Button
                type="button"
                variant="secondary"
                className="table-tools__nav"
                onClick={() => void vacancies.goToPage(vacancies.currentPage - 1)}
                disabled={vacancies.loading || vacancies.currentPage <= 1}
                title={t('common.previous')}
                aria-label={t('common.previous')}
              >
                ‹
              </Button>
              <Button
                type="button"
                variant="secondary"
                className="table-tools__nav"
                onClick={() => void vacancies.goToPage(vacancies.currentPage + 1)}
                disabled={vacancies.loading || vacancies.currentPage >= vacancies.totalPages}
                title={t('common.next')}
                aria-label={t('common.next')}
              >
                ›
              </Button>
            </div>
          </div>
          {exportState ? (
            <p className="form-hint">
              {exportState.type === 'preparing'
                ? t('vacancies.exportPreparing')
                : exportState.type === 'progress'
                  ? t('vacancies.exportProgress', exportState)
                  : exportState.type === 'done'
                    ? t('vacancies.exportDone', exportState)
                    : t('vacancies.exportError', { message: exportState.message })}
            </p>
          ) : null}
          {vacancies.error ? <p className="field-error">{vacancies.error}</p> : null}
          {pageRows.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>
                      <button
                        type="button"
                        className={`table-sort ${sortKey === 'title' ? 'is-active' : ''}`}
                        onClick={() => handleSort('title')}
                      >
                        <span>{t('vacancies.table.title')}</span>
                        <span
                          className={`table-sort__indicator ${sortKey === 'title' ? `is-${sortDirection}` : ''}`}
                          aria-hidden="true"
                        />
                      </button>
                    </th>
                    <th>
                      <button
                        type="button"
                        className={`table-sort ${sortKey === 'company' ? 'is-active' : ''}`}
                        onClick={() => handleSort('company')}
                      >
                        <span>{t('vacancies.table.company')}</span>
                        <span
                          className={`table-sort__indicator ${sortKey === 'company' ? `is-${sortDirection}` : ''}`}
                          aria-hidden="true"
                        />
                      </button>
                    </th>
                    <th>
                      <button
                        type="button"
                        className={`table-sort ${sortKey === 'city' ? 'is-active' : ''}`}
                        onClick={() => handleSort('city')}
                      >
                        <span>{t('vacancies.table.city')}</span>
                        <span
                          className={`table-sort__indicator ${sortKey === 'city' ? `is-${sortDirection}` : ''}`}
                          aria-hidden="true"
                        />
                      </button>
                    </th>
                    <th>
                      <button
                        type="button"
                        className={`table-sort ${sortKey === 'salary' ? 'is-active' : ''}`}
                        onClick={() => handleSort('salary')}
                      >
                        <span>{t('vacancies.table.salary')}</span>
                        <span
                          className={`table-sort__indicator ${sortKey === 'salary' ? `is-${sortDirection}` : ''}`}
                          aria-hidden="true"
                        />
                      </button>
                    </th>
                    <th className="table-col-details">{t('vacancies.table.details')}</th>
                  </tr>
                </thead>
                <tbody>
                  {pageRows.map((row) => (
                    <tr
                      key={row.id}
                      className={`vacancies-row ${selectedVacancy?.external_id === row.id ? 'is-active' : ''}`}
                      onClick={() => setSelectedVacancy(row.vacancy)}
                    >
                      <td>{row.title}</td>
                      <td>{row.company}</td>
                      <td>{row.city}</td>
                      <td>{row.salary}</td>
                      <td className="table-col-details">
                        <span
                          className="row-detail-trigger"
                          onClick={(event) => {
                            event.stopPropagation()
                            setSelectedVacancy(row.vacancy)
                          }}
                          title={t('common.open')}
                          aria-label={t('common.open')}
                        >
                          {selectedVacancy?.external_id === row.id ? '✓' : '→'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState
              title={t('vacancies.emptyTitle')}
              description={t('vacancies.emptyDescription')}
            />
          )}
        </Card>

        <div
          className={`preview-drawer-backdrop ${selectedVacancy ? 'is-visible' : ''}`}
          aria-hidden
          onClick={() => setSelectedVacancy(null)}
        />
        <aside
          className={`preview-drawer ${selectedVacancy ? 'is-open' : ''}`}
          aria-label={t('vacancies.preview.drawerLabel')}
        >
          {selectedVacancy ? (
            <>
              <div className="preview-drawer__header">
                <div className="preview-drawer__title-block">
                  <h3 className="preview-drawer__title">{selectedVacancy.title}</h3>
                  <p className="preview-drawer__subtitle">
                    {selectedVacancy.company ?? t('vacancies.preview.companyMissing')}
                  </p>
                </div>
                <button
                  type="button"
                  className="preview-drawer__close"
                  onClick={() => setSelectedVacancy(null)}
                  aria-label={t('common.close')}
                >
                  <span className="preview-drawer__close-icon" aria-hidden />
                </button>
              </div>
              <div className="preview-drawer__body">
                <div className="preview-panel">
                  <div className="preview-panel__tags">
                    <span className="preview-panel__tag">
                      {t('vacancies.preview.city')}: {selectedVacancy.city ?? t('common.notSpecifiedMasc')}
                    </span>
                    <span className="preview-panel__tag">
                      {t('vacancies.preview.experience')}: {selectedVacancy.experience ?? t('common.notSpecifiedMasc')}
                    </span>
                    <span className="preview-panel__tag">
                      {t('vacancies.preview.schedule')}: {selectedVacancy.schedule ?? t('common.notSpecifiedMasc')}
                    </span>
                    <span className="preview-panel__tag">
                      {t('vacancies.preview.salary')}: {formatSalary(selectedVacancy)}
                    </span>
                  </div>
                  <div className="preview-panel__grid">
                    <div className="preview-panel__meta-card">
                      <strong>{t('vacancies.preview.publishDate')}</strong>
                      <span>
                        {selectedVacancy.published_at
                          ? new Date(selectedVacancy.published_at).toLocaleDateString('ru-RU')
                          : t('common.notSpecified')}
                      </span>
                    </div>
                    <div className="preview-panel__meta-card">
                      <strong>{t('vacancies.preview.sourceLink')}</strong>
                      <a href={selectedVacancy.url} target="_blank" rel="noreferrer">
                        {t('common.openInNewTab')}
                      </a>
                    </div>
                  </div>
                  <div className="preview-panel__description">
                    <h4>{t('vacancies.preview.descriptionTitle')}</h4>
                    <p>{selectedVacancy.description?.trim() || t('vacancies.preview.descriptionMissing')}</p>
                  </div>
                  <div className="preview-panel__actions">
                    <Button
                      type="button"
                      onClick={() => window.open(selectedVacancy.url, '_blank', 'noopener,noreferrer')}
                    >
                      {t('common.goToVacancy')}
                    </Button>
                  </div>
                </div>
              </div>
            </>
          ) : null}
        </aside>
      </section>
    </main>
  )
}
