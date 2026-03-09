export interface Vacancy {
  external_id: string
  title: string
  description?: string | null
  company?: string | null
  city?: string | null
  salary_from?: number | null
  salary_to?: number | null
  currency?: string | null
  experience?: string | null
  schedule?: string | null
  url: string
  published_at?: string | null
}

export interface VacancyListResponse {
  items: Vacancy[]
  total: number
  limit: number
  offset: number
}

export interface ParseResponse {
  status: string
  message: string
  collected: number
  job_id: number
  new_count: number
  updated_count: number
}

export interface ParseJobStatus {
  job_id: number
  query: string
  pages: number
  status: string
  started_at: string
  finished_at?: string | null
  parser_message?: string | null
  error_message?: string | null
  collected?: number | null
  saved_count?: number | null
  new_count?: number | null
  updated_count?: number | null
}

export interface ParseJobListResponse {
  items: ParseJobStatus[]
}

export interface SkillStat {
  skill: string
  count: number
}

export interface CompanyStat {
  company: string
  count: number
}

export interface VacancyInsightsResponse {
  top_skills: SkillStat[]
  top_companies: CompanyStat[]
}

export interface VacancyCleanupResponse {
  removed: number
}

export interface HealthResponse {
  status: string
  database: string
}

export interface AuthTokens {
  access_token: string
  token_type: string
}

export interface UserProfile {
  id: number
  email: string
  full_name?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface RegisterPayload {
  email: string
  password: string
  full_name?: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface UpdateProfilePayload {
  full_name?: string | null
}
