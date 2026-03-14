import type {
  AuthTokens,
  HealthResponse,
  LoginPayload,
  ParseJobListResponse,
  ParseJobStatus,
  ParseResponse,
  RegisterPayload,
  TelegramReportSettings,
  TelegramReportSettingsUpdate,
  UpdateProfilePayload,
  UserProfile,
  VacancyCleanupResponse,
  VacancyInsightsResponse,
  VacancyListResponse,
} from './types'
import { translate } from './shared/i18n'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const DEFAULT_TIMEOUT_MS = 20_000
const TRANSIENT_STATUSES = new Set([502, 503, 504])

function buildUrl(path: string): string {
  return `${API_BASE_URL}${path}`
}

function buildAuthHeaders(accessToken?: string, contentType = true): HeadersInit {
  const headers: Record<string, string> = {}
  if (contentType) headers['Content-Type'] = 'application/json'
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`
  return headers
}

export class ApiError extends Error {
  status: number
  detail?: string
  isTimeout: boolean
  constructor(message: string, status: number, detail?: string, isTimeout = false) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.isTimeout = isTimeout
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}

interface RequestOptions {
  path: string
  method?: string
  accessToken?: string
  body?: unknown
  fallbackError: string
  allowAuthRefresh?: boolean
  retries?: number
  retryStatuses?: Set<number>
  signal?: AbortSignal
  timeoutMs?: number
  contentType?: boolean
  credentials?: RequestCredentials
}

interface AuthSessionHandlers {
  onTokenRefresh?: (token: string) => void
  onAuthFailure?: () => void
}

let authHandlers: AuthSessionHandlers | null = null
let refreshInFlight: Promise<string> | null = null

export function setAuthSessionHandlers(handlers: AuthSessionHandlers | null): void {
  authHandlers = handlers
}

async function parseJsonOrTextError(response: Response, fallback: string): Promise<{ detail: string }> {
  const body = await response.text()
  if (!body) return { detail: fallback }
  try {
    const parsed = JSON.parse(body) as { detail?: string }
    return { detail: parsed.detail || fallback }
  } catch {
    return { detail: body }
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

function backoffDelay(attempt: number): number {
  return Math.min(700, 150 * attempt)
}

async function refreshAccessToken(): Promise<string> {
  if (!refreshInFlight) {
    refreshInFlight = authRefresh()
      .then((tokens) => {
        authHandlers?.onTokenRefresh?.(tokens.access_token)
        return tokens.access_token
      })
      .catch((error) => {
        authHandlers?.onAuthFailure?.()
        throw error
      })
      .finally(() => {
        refreshInFlight = null
      })
  }
  return refreshInFlight
}

async function requestJson<T>(options: RequestOptions): Promise<T> {
  const {
    path,
    method = 'GET',
    accessToken,
    body,
    fallbackError,
    allowAuthRefresh = false,
    retries = 0,
    retryStatuses = TRANSIENT_STATUSES,
    signal,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    contentType = body !== undefined,
    credentials,
  } = options

  let currentAccessToken = accessToken

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    let timeoutId: number | null = null
    const controller = new AbortController()
    let timeoutTriggered = false

    if (signal) {
      if (signal.aborted) {
        controller.abort(signal.reason)
      } else {
        signal.addEventListener('abort', () => controller.abort(signal.reason), { once: true })
      }
    }

    if (timeoutMs > 0) {
      timeoutId = window.setTimeout(() => {
        timeoutTriggered = true
        controller.abort()
      }, timeoutMs)
    }

    try {
      const response = await fetch(buildUrl(path), {
        method,
        headers: buildAuthHeaders(currentAccessToken, contentType),
        credentials,
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      })

      if (response.ok) {
        if (response.status === 204) {
          return undefined as T
        }
        return (await response.json()) as T
      }

      if (allowAuthRefresh && response.status === 401 && currentAccessToken) {
        currentAccessToken = await refreshAccessToken()
        continue
      }

      if (retryStatuses.has(response.status) && attempt < retries) {
        await sleep(backoffDelay(attempt + 1))
        continue
      }

      const { detail } = await parseJsonOrTextError(response, fallbackError)
      throw new ApiError(detail, response.status, detail)
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }

      if (timeoutTriggered) {
        if (attempt < retries) {
          await sleep(backoffDelay(attempt + 1))
          continue
        }
        throw new ApiError(translate('errors.api.requestTimedOut', { fallback: fallbackError }), 0, fallbackError, true)
      }

      if (attempt < retries) {
        await sleep(backoffDelay(attempt + 1))
        continue
      }

      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ApiError(translate('errors.api.requestCancelled'), 0, fallbackError)
      }

      throw new ApiError(fallbackError, 0, fallbackError)
    } finally {
      if (timeoutId) {
        window.clearTimeout(timeoutId)
      }
    }
  }

  throw new ApiError(fallbackError, 0, fallbackError)
}

export async function authRegister(payload: RegisterPayload): Promise<AuthTokens> {
  return requestJson<AuthTokens>({
    path: '/api/v1/auth/register',
    method: 'POST',
    body: payload,
    fallbackError: translate('errors.api.registrationFailed'),
    credentials: 'include',
  })
}

export async function authLogin(payload: LoginPayload): Promise<AuthTokens> {
  return requestJson<AuthTokens>({
    path: '/api/v1/auth/login',
    method: 'POST',
    body: payload,
    fallbackError: translate('errors.api.loginFailed'),
    credentials: 'include',
  })
}

export async function authRefresh(): Promise<AuthTokens> {
  return requestJson<AuthTokens>({
    path: '/api/v1/auth/refresh',
    method: 'POST',
    fallbackError: translate('errors.api.sessionRefreshFailed'),
    credentials: 'include',
  })
}

export async function authLogout(): Promise<void> {
  await requestJson<void>({
    path: '/api/v1/auth/logout',
    method: 'POST',
    fallbackError: translate('errors.api.logoutFailed'),
    credentials: 'include',
  })
}

export async function authGetMe(accessToken: string): Promise<UserProfile> {
  return requestJson<UserProfile>({
    path: '/api/v1/auth/me',
    accessToken,
    fallbackError: translate('errors.api.profileFetchFailed'),
    allowAuthRefresh: true,
    contentType: false,
  })
}

export async function authUpdateMe(
  payload: UpdateProfilePayload,
  accessToken: string,
): Promise<UserProfile> {
  return requestJson<UserProfile>({
    path: '/api/v1/auth/me',
    method: 'PATCH',
    accessToken,
    body: payload,
    fallbackError: translate('errors.api.profileUpdateFailed'),
    allowAuthRefresh: true,
  })
}

export async function triggerParsing(
  query: string,
  pages: number,
  accessToken: string,
  options?: { signal?: AbortSignal; idempotencyKey?: string },
): Promise<ParseResponse> {
  const idempotencyKey = options?.idempotencyKey
  return requestJson<ParseResponse>({
    path: '/api/v1/parsing/jobs',
    method: 'POST',
    accessToken,
    body: {
      query,
      pages,
      idempotency_key: idempotencyKey,
    },
    fallbackError: translate('errors.api.parseRequestFailed'),
    allowAuthRefresh: true,
    retries: 1,
    signal: options?.signal,
  })
}

export async function fetchParsingJobStatus(
  jobId: number,
  accessToken?: string,
  options?: { signal?: AbortSignal },
): Promise<ParseJobStatus> {
  return requestJson<ParseJobStatus>({
    path: `/api/v1/parsing/jobs/${jobId}`,
    accessToken,
    fallbackError: translate('errors.api.parseJobStatusFailed'),
    allowAuthRefresh: true,
    contentType: false,
    signal: options?.signal,
  })
}

export async function fetchParsingJobs(
  limit: number,
  accessToken?: string,
  options?: { signal?: AbortSignal },
): Promise<ParseJobListResponse> {
  const query = new URLSearchParams()
  query.set('limit', String(limit))
  return requestJson<ParseJobListResponse>({
    path: `/api/v1/parsing/jobs?${query.toString()}`,
    accessToken,
    fallbackError: translate('errors.api.parseJobsFailed'),
    allowAuthRefresh: true,
    contentType: false,
    signal: options?.signal,
  })
}

export async function fetchHealth(options?: { signal?: AbortSignal }): Promise<HealthResponse> {
  return requestJson<HealthResponse>({
    path: '/api/v1/health',
    fallbackError: translate('errors.api.healthCheckFailed'),
    contentType: false,
    retries: 1,
    signal: options?.signal,
    timeoutMs: 6000,
  })
}

export async function fetchVacancies(
  params: {
    city?: string
    experience?: string
    search?: string
    limit: number
    offset: number
  },
  accessToken?: string,
  options?: { signal?: AbortSignal },
): Promise<VacancyListResponse> {
  const query = new URLSearchParams()
  if (params.city) query.set('city', params.city)
  if (params.experience) query.set('experience', params.experience)
  if (params.search) query.set('search', params.search)
  query.set('limit', String(params.limit))
  query.set('offset', String(params.offset))

  return requestJson<VacancyListResponse>({
    path: `/api/v1/vacancies?${query.toString()}`,
    accessToken,
    fallbackError: translate('errors.api.vacanciesFailed'),
    allowAuthRefresh: true,
    retries: 1,
    contentType: false,
    signal: options?.signal,
  })
}

export async function fetchVacancyInsights(
  params: {
    city?: string
    experience?: string
    search?: string
    limit: number
  },
  accessToken?: string,
  options?: { signal?: AbortSignal },
): Promise<VacancyInsightsResponse> {
  const query = new URLSearchParams()
  if (params.city) query.set('city', params.city)
  if (params.experience) query.set('experience', params.experience)
  if (params.search) query.set('search', params.search)
  query.set('limit', String(params.limit))

  return requestJson<VacancyInsightsResponse>({
    path: `/api/v1/vacancies/insights?${query.toString()}`,
    accessToken,
    fallbackError: translate('errors.api.insightsFailed'),
    allowAuthRefresh: true,
    retries: 1,
    contentType: false,
    signal: options?.signal,
  })
}

export async function clearMyVacancies(accessToken: string): Promise<VacancyCleanupResponse> {
  return requestJson<VacancyCleanupResponse>({
    path: '/api/v1/vacancies/my',
    method: 'DELETE',
    accessToken,
    fallbackError: translate('errors.api.vacancyCleanupFailed'),
    allowAuthRefresh: true,
    contentType: false,
  })
}

export async function getTelegramReportSettings(
  accessToken: string,
  options?: { signal?: AbortSignal },
): Promise<TelegramReportSettings> {
  return requestJson<TelegramReportSettings>({
    path: '/api/v1/settings/telegram-report',
    accessToken,
    fallbackError: translate('errors.api.settingsFetchFailed'),
    allowAuthRefresh: true,
    contentType: false,
    signal: options?.signal,
  })
}

export async function updateTelegramReportSettings(
  payload: TelegramReportSettingsUpdate,
  accessToken: string,
): Promise<TelegramReportSettings> {
  return requestJson<TelegramReportSettings>({
    path: '/api/v1/settings/telegram-report',
    method: 'PUT',
    accessToken,
    body: payload,
    fallbackError: translate('errors.api.settingsUpdateFailed'),
    allowAuthRefresh: true,
  })
}
