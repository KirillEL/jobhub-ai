import { useEffect, useState } from 'react'
import { fetchVacancyInsights } from '../../api.ts'
import { useI18n } from '../../shared/i18n'
import type { CompanyStat, SkillStat } from '../../types'

interface InsightFilters {
  search: string
  city: string
  experience: string
}

export function useInsights(accessToken: string | null, filters: InsightFilters) {
  const { locale, t } = useI18n()
  const [topSkills, setTopSkills] = useState<SkillStat[]>([])
  const [topCompanies, setTopCompanies] = useState<CompanyStat[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      setLoading(true)
      setError(null)
      try {
        const result = await fetchVacancyInsights(
          {
            search: filters.search.trim() || undefined,
            city: filters.city.trim() || undefined,
            experience: filters.experience.trim() || undefined,
            limit: 8,
          },
          accessToken ?? undefined,
        )
        if (cancelled) return
        setTopSkills(result.top_skills)
        setTopCompanies(result.top_companies)
      } catch (loadError) {
        if (cancelled) return
        setTopSkills([])
        setTopCompanies([])
        setError(loadError instanceof Error ? loadError.message : t('errors.hooks.insightsLoadFailed'))
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void run()
    return () => {
      cancelled = true
    }
  }, [accessToken, filters.city, filters.experience, filters.search, locale, t])

  return { topSkills, topCompanies, loading, error }
}
