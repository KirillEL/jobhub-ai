import { useCallback, useEffect, useState } from 'react'
import { fetchParsingJobs, fetchParsingJobStatus } from '../../api.ts'
import { useI18n } from '../../shared/i18n'
import type { ParseJobStatus } from '../../types'

const JOB_LIMIT = 12
const POLL_INTERVAL_MS = 2500
const TERMINAL_STATUSES = new Set(['done', 'failed'])

function isPollingStatus(status: string): boolean {
  return !TERMINAL_STATUSES.has(status)
}

export function useJobs(accessToken: string | null) {
  const { locale, t } = useI18n()
  const [jobs, setJobs] = useState<ParseJobStatus[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    if (!accessToken) return
    setLoading(true)
    setError(null)
    try {
      const result = await fetchParsingJobs(JOB_LIMIT, accessToken)
      setJobs(result.items)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : t('errors.hooks.jobsLoadFailed'))
    } finally {
      setLoading(false)
    }
  }, [accessToken, t])

  const refreshOne = useCallback(
    async (jobId: number) => {
      if (!accessToken) return
      const updated = await fetchParsingJobStatus(jobId, accessToken)
      setJobs((current) => {
        const rest = current.filter((item) => item.job_id !== updated.job_id)
        return [updated, ...rest].slice(0, JOB_LIMIT)
      })
    },
    [accessToken],
  )

  useEffect(() => {
    void reload()
  }, [locale, reload])

  // Poll pending/running jobs so status updates without reload
  useEffect(() => {
    const toPoll = jobs.filter((j) => isPollingStatus(j.status)).map((j) => j.job_id)
    if (toPoll.length === 0 || !accessToken) return

    const interval = setInterval(async () => {
      for (const id of toPoll) {
        try {
          const updated = await fetchParsingJobStatus(id, accessToken)
          setJobs((current) => {
            const rest = current.filter((item) => item.job_id !== updated.job_id)
            return [updated, ...rest].slice(0, JOB_LIMIT)
          })
        } catch {
          // keep showing current status, retry next tick
        }
      }
    }, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [jobs, accessToken])

  return { jobs, loading, error, reload, refreshOne }
}
