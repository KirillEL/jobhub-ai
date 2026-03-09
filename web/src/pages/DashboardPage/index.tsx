import { useMemo } from 'react'
import { useAuth } from '../../auth/AuthContext'
import { useHealthStatus } from '../../features/health/useHealthStatus'
import { useInsights } from '../../features/insights/useInsights'
import { useJobs } from '../../features/jobs/useJobs'
import { useVacancySearch } from '../../features/vacancies/useVacancySearch'
import { translateJobStatus, useI18n } from '../../shared/i18n'
import Card from '../../shared/ui/Card'
import PageHeader from '../../shared/ui/PageHeader'
import './styles.scss'

export default function DashboardPage() {
  const { accessToken, profile } = useAuth()
  const { t, locale } = useI18n()
  const health = useHealthStatus()
  const jobs = useJobs(accessToken)
  const vacancies = useVacancySearch(accessToken)
  const insights = useInsights(accessToken, {
    search: vacancies.filters.search,
    city: vacancies.filters.city,
    experience: vacancies.filters.experience,
  })
  const activeFilters = useMemo(
    () =>
      [vacancies.filters.search, vacancies.filters.city, vacancies.filters.experience]
        .map((item) => item.trim())
        .filter(Boolean).length,
    [vacancies.filters.city, vacancies.filters.experience, vacancies.filters.search],
  )

  return (
    <main className="layout dashboard-page">
      <PageHeader
        title={t('dashboard.title')}
        subtitle={t('dashboard.subtitle')}
      />
      <section className="stats-grid">
        <Card className="stat-card">
          <span>{t('dashboard.totalVacancies')}</span>
          <strong>{vacancies.total}</strong>
        </Card>
        <Card className="stat-card">
          <span>{t('dashboard.activeFilters')}</span>
          <strong>{activeFilters}</strong>
        </Card>
        <Card className="stat-card">
          <span>{t('dashboard.currentPage')}</span>
          <strong>
            {vacancies.currentPage}/{vacancies.totalPages}
          </strong>
        </Card>
        <Card className="stat-card">
          <span>{t('dashboard.service')}</span>
          <strong>{t(`dashboard.serviceState.${health.state}`)}</strong>
        </Card>
      </section>

      <section className="cards-grid">
        <Card>
          <h3>{t('dashboard.profileTitle')}</h3>
          <p className="subtitle">
            {t('dashboard.account')}: {profile?.email ?? t('common.unknown')}
          </p>
          <p>{health.message}</p>
        </Card>
        <Card>
          <h3>{t('dashboard.recentJobs')}</h3>
          <p className="subtitle">
            {jobs.loading ? t('dashboard.pipelineUpdating') : t('dashboard.pipelineCurrent')}
          </p>
          <ul className="simple-list">
            {jobs.jobs.slice(0, 4).map((job) => (
              <li key={job.job_id}>
                <strong>#{job.job_id}</strong> {job.query} - {translateJobStatus(job.status, locale)}
              </li>
            ))}
          </ul>
        </Card>
        <Card>
          <h3>{t('dashboard.topCompanies')}</h3>
          <ul className="simple-list">
            {insights.topCompanies.slice(0, 5).map((item) => (
              <li key={item.company}>
                <span>{item.company}</span>
                <strong>{item.count}</strong>
              </li>
            ))}
          </ul>
        </Card>
        <Card>
          <h3>{t('dashboard.topSkills')}</h3>
          <ul className="simple-list">
            {insights.topSkills.slice(0, 5).map((item) => (
              <li key={item.skill}>
                <span>{item.skill}</span>
                <strong>{item.count}</strong>
              </li>
            ))}
          </ul>
        </Card>
      </section>
    </main>
  )
}
