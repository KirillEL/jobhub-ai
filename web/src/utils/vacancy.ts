import type { Vacancy } from '../types'
import { translate } from '../shared/i18n'

export interface VacancyMeta {
  favorite: boolean
  tags: string[]
}

export type VacancyMetaMap = Record<string, VacancyMeta>

export function formatSalary(vacancy: Vacancy): string {
  const from = vacancy.salary_from
  const to = vacancy.salary_to
  const currency = vacancy.currency ?? ''
  if (from == null && to == null) return translate('common.notSpecifiedFem')
  if (from != null && to != null) return `${from} - ${to} ${currency}`.trim()
  if (from != null) return `${translate('salary.from')} ${from} ${currency}`.trim()
  return `${translate('salary.to')} ${to} ${currency}`.trim()
}

export function parseLimit(value: string | null): number {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return 50
  return Math.min(500, Math.max(1, Math.floor(parsed)))
}

export function parsePage(value: string | null): number {
  const parsed = Number(value)
  if (!Number.isFinite(parsed)) return 1
  return Math.max(1, Math.floor(parsed))
}

export function toPercent(value: number, max: number): number {
  if (max <= 0) return 0
  return Math.max(8, Math.round((value / max) * 100))
}

export function loadCollapsedState(key: string): boolean {
  try {
    if (typeof window === 'undefined') return false
    return window.localStorage.getItem(key) === '1'
  } catch {
    return false
  }
}

export function saveCollapsedState(key: string, value: boolean): void {
  try {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(key, value ? '1' : '0')
  } catch {
    // ignore storage errors in restricted environments
  }
}

export function loadVacancyMetaState(key: string): VacancyMetaMap {
  try {
    if (typeof window === 'undefined') return {}
    const raw = window.localStorage.getItem(key)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as Record<string, { favorite?: unknown; tags?: unknown }>
    const normalized: VacancyMetaMap = {}

    for (const [externalId, value] of Object.entries(parsed)) {
      if (!value || typeof value !== 'object') continue
      const favorite = value.favorite === true
      const tags = Array.isArray(value.tags)
        ? value.tags.filter((tag): tag is string => typeof tag === 'string').map((tag) => tag.trim()).filter(Boolean)
        : []
      if (!favorite && tags.length === 0) continue
      normalized[externalId] = { favorite, tags }
    }
    return normalized
  } catch {
    return {}
  }
}

export function saveVacancyMetaState(key: string, value: VacancyMetaMap): void {
  try {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // ignore storage errors in restricted environments
  }
}

export function buildSparkline(values: number[]): string {
  if (!values.length) return ''
  const width = 120
  const height = 40
  const padding = 4
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const range = maxValue - minValue || 1

  return values
    .map((value, index) => {
      const x = padding + (index * (width - padding * 2)) / Math.max(1, values.length - 1)
      const y = height - padding - ((value - minValue) / range) * (height - padding * 2)
      return `${x},${y}`
    })
    .join(' ')
}
