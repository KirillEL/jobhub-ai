import type { FormEvent } from 'react'
import { useAuth } from '../../auth/AuthContext'
import { useJobs } from '../../features/jobs/useJobs'
import { useParsing } from '../../features/parsing/useParsing'
import { translateJobStatus, useI18n } from '../../shared/i18n'
import Button from '../../shared/ui/Button'
import Card from '../../shared/ui/Card'
import EmptyState from '../../shared/ui/EmptyState'
import PageHeader from '../../shared/ui/PageHeader'
import './styles.scss'

export default function JobsPage() {
  const { accessToken } = useAuth()
  const { t, locale } = useI18n()
  const jobs = useJobs(accessToken)
  const parsing = useParsing(accessToken)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const result = await parsing.runParsing()
    if (result) {
      await jobs.reload()
      await jobs.refreshOne(result.jobId)
    }
  }

  return (
    <main className="layout jobs-page">
      <PageHeader title={t('jobs.title')} subtitle={t('jobs.subtitle')} />

      <div className="cards-grid cards-grid--wide">
        <Card>
          <h3>{t('jobs.newJob')}</h3>
          <form className="stack-form" onSubmit={handleSubmit}>
            <label>
              {t('jobs.query')}
              <input value={parsing.query} onChange={(event) => parsing.setQuery(event.target.value)} />
              {parsing.queryError ? <span className="field-error">{parsing.queryError}</span> : null}
            </label>
            <label>
              {t('jobs.pages')}
              <input
                type="number"
                min={1}
                max={20}
                value={parsing.pages}
                onChange={(event) => parsing.setPages(Number(event.target.value))}
              />
              {parsing.pagesError ? <span className="field-error">{parsing.pagesError}</span> : null}
            </label>
            <Button type="submit" disabled={parsing.submitting || parsing.hasErrors}>
              {parsing.submitting ? t('jobs.running') : t('jobs.run')}
            </Button>
          </form>
        </Card>

        <Card>
          <h3>{t('jobs.history')}</h3>
          {jobs.error ? <p className="field-error">{jobs.error}</p> : null}
          {jobs.jobs.length ? (
            <ul className="simple-list job-history-list">
              {jobs.jobs.map((job) => {
                const isInProgress = job.status === 'pending' || job.status === 'running'
                return (
                  <li
                    key={job.job_id}
                    className={`job-history-item ${isInProgress ? 'job-history-item--loading' : ''} ${job.status === 'done' ? 'job-history-item--done' : ''} ${job.status === 'failed' ? 'job-history-item--failed' : ''}`}
                  >
                    <span className="job-history-item__main">
                      <strong>#{job.job_id}</strong> {job.query} ({job.pages} {t('jobs.pages').toLowerCase()})
                      {job.status === 'done' ? (
                        <small className="job-history-item__details">
                          {job.collected ?? 0} collected | {job.saved_count ?? 0} saved | +{job.new_count ?? 0} new
                        </small>
                      ) : null}
                      {job.status === 'failed' && job.error_message ? (
                        <small className="job-history-item__error">{job.error_message}</small>
                      ) : null}
                    </span>
                    <span className="job-history-item__status">
                      {isInProgress && <span className="job-history-item__spinner" aria-hidden="true" />}
                      <span className="job-history-item__status-text" key={job.status}>
                        {translateJobStatus(job.status, locale)}
                      </span>
                    </span>
                  </li>
                )
              })}
            </ul>
          ) : (
            <EmptyState title={t('jobs.emptyTitle')} description={t('jobs.emptyDescription')} />
          )}
        </Card>
      </div>
    </main>
  )
}
