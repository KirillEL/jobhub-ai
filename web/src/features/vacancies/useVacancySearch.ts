import { useCallback, useEffect, useMemo, useState } from 'react'
import { fetchVacancies } from '../../api.ts'
import { useI18n } from '../../shared/i18n'
import type { Vacancy } from '../../types'
import { validateLimit, validateOptionalText } from '../../utils/validation'

interface Filters {
  search: string
  city: string
  experience: string
  limit: number
}

const INITIAL_FILTERS: Filters = {
  search: '',
  city: '',
  experience: '',
  limit: 30,
}

export function useVacancySearch(accessToken: string | null) {
  const { locale, t } = useI18n()
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS)
  const [offset, setOffset] = useState(0)
  const [items, setItems] = useState<Vacancy[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const errors = useMemo(
    () => ({
      search: validateOptionalText(filters.search, 120, t('vacancies.filters.search')),
      city: validateOptionalText(filters.city, 80, t('vacancies.filters.city')),
      experience: validateOptionalText(filters.experience, 40, t('vacancies.filters.experience')),
      limit: validateLimit(filters.limit),
    }),
    [filters, t],
  )

  const hasErrors = Boolean(errors.search || errors.city || errors.experience || errors.limit)
  const currentPage = Math.floor(offset / filters.limit) + 1
  const totalPages = Math.max(1, Math.ceil(total / filters.limit))

  const reload = useCallback(
    async (nextOffset: number) => {
      setLoading(true)
      setError(null)
      try {
        const result = await fetchVacancies(
          {
            search: filters.search.trim() || undefined,
            city: filters.city.trim() || undefined,
            experience: filters.experience.trim() || undefined,
            limit: filters.limit,
            offset: nextOffset,
          },
          accessToken ?? undefined,
        )
        setItems(result.items)
        setTotal(result.total)
        setOffset(result.offset)
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : t('errors.hooks.vacanciesLoadFailed'))
      } finally {
        setLoading(false)
      }
    },
    [accessToken, filters.city, filters.experience, filters.limit, filters.search, t],
  )

  useEffect(() => {
    if (hasErrors) return
    void reload(0)
  }, [filters.city, filters.experience, filters.limit, filters.search, hasErrors, locale, reload])

  function updateFilter<Key extends keyof Filters>(key: Key, value: Filters[Key]) {
    setFilters((current) => ({ ...current, [key]: value }))
  }

  async function goToPage(page: number) {
    const nextPage = Math.max(1, Math.min(page, totalPages))
    const nextOffset = (nextPage - 1) * filters.limit
    if (nextOffset === offset || loading) return
    await reload(nextOffset)
  }

  return {
    filters,
    updateFilter,
    items,
    total,
    loading,
    error,
    errors,
    hasErrors,
    currentPage,
    totalPages,
    reload,
    goToPage,
  }
}
