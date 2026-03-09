import { useAuth } from '../../auth/AuthContext'
import { useInsights } from '../../features/insights/useInsights'
import { useVacancySearch } from '../../features/vacancies/useVacancySearch'
import { useI18n } from '../../shared/i18n'
import Card from '../../shared/ui/Card'
import EmptyState from '../../shared/ui/EmptyState'
import PageHeader from '../../shared/ui/PageHeader'
import './styles.scss'

export default function InsightsPage() {
  const { accessToken } = useAuth()
  const { t } = useI18n()
  const vacancies = useVacancySearch(accessToken)
  const insights = useInsights(accessToken, {
    search: vacancies.filters.search,
    city: vacancies.filters.city,
    experience: vacancies.filters.experience,
  })

  return (
    <main className="layout insights-page">
      <PageHeader title={t('insights.title')} subtitle={t('insights.subtitle')} />
      {insights.error ? <p className="field-error">{insights.error}</p> : null}
      <section className="cards-grid">
        <Card>
          <h3>{t('insights.topCompanies')}</h3>
          {insights.topCompanies.length ? (
            <ul className="simple-list">
              {insights.topCompanies.map((item) => (
                <li key={item.company}>
                  <span>{item.company}</span>
                  <strong>{item.count}</strong>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title={t('insights.emptyTitle')} description={t('insights.emptyCompaniesDescription')} />
          )}
        </Card>
        <Card>
          <h3>{t('insights.topSkills')}</h3>
          {insights.topSkills.length ? (
            <ul className="simple-list">
              {insights.topSkills.map((item) => (
                <li key={item.skill}>
                  <span>{item.skill}</span>
                  <strong>{item.count}</strong>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title={t('insights.emptyTitle')} description={t('insights.emptySkillsDescription')} />
          )}
        </Card>
      </section>
    </main>
  )
}
