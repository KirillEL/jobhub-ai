import { useEffect, useState } from 'react'
import { fetchHealth } from '../../api.ts'
import { useI18n } from '../../shared/i18n'

export type HealthState = 'checking' | 'ok' | 'degraded'

const HEALTH_POLL_MS = 45_000

export function useHealthStatus() {
  const { locale, t } = useI18n()
  const [state, setState] = useState<HealthState>('checking')
  const [message, setMessage] = useState(t('health.checking'))

  useEffect(() => {
    let active = true
    let intervalId: number | null = null

    const runCheck = async () => {
      try {
        const result = await fetchHealth()
        if (!active) return
        const isHealthy = result.status === 'ok' && result.database === 'ok'
        setState(isHealthy ? 'ok' : 'degraded')
        setMessage(
          isHealthy
            ? t('health.stable')
            : t('health.degraded', { api: result.status, db: result.database }),
        )
      } catch {
        if (!active) return
        setState('degraded')
        setMessage(t('health.unavailable'))
      }
    }

    void runCheck()
    intervalId = window.setInterval(() => {
      void runCheck()
    }, HEALTH_POLL_MS)

    return () => {
      active = false
      if (intervalId) window.clearInterval(intervalId)
    }
  }, [locale, t])

  return { state, message }
}
