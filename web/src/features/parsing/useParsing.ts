import { useState } from 'react'
import { triggerParsing } from '../../api.ts'
import { validatePages, validateQuery } from '../../utils/validation'

export function useParsing(accessToken: string | null) {
  const [query, setQuery] = useState('python backend')
  const [pages, setPages] = useState(2)
  const [submitting, setSubmitting] = useState(false)

  const queryError = validateQuery(query)
  const pagesError = validatePages(pages)
  const hasErrors = Boolean(queryError || pagesError)

  async function runParsing(): Promise<{ jobId: number; collected: number } | null> {
    if (!accessToken || hasErrors) return null
    setSubmitting(true)
    try {
      const response = await triggerParsing(query, pages, accessToken, {
        idempotencyKey: `${Date.now()}-${Math.random().toString(36).slice(2, 12)}`,
      })
      return { jobId: response.job_id, collected: response.collected }
    } finally {
      setSubmitting(false)
    }
  }

  return {
    query,
    setQuery,
    pages,
    setPages,
    submitting,
    queryError,
    pagesError,
    hasErrors,
    runParsing,
  }
}
