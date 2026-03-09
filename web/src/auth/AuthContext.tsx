import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import {
  authGetMe,
  authLogin,
  authLogout,
  authRefresh,
  authRegister,
  authUpdateMe,
  setAuthSessionHandlers,
} from '../api.ts'
import { translate } from '../shared/i18n'
import type { LoginPayload, RegisterPayload, UpdateProfilePayload, UserProfile } from '../types'

interface AuthContextValue {
  accessToken: string | null
  profile: UserProfile | null
  isAuthReady: boolean
  isAuthenticated: boolean
  login: (payload: LoginPayload) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => Promise<void>
  refreshSession: () => Promise<void>
  updateProfile: (payload: UpdateProfilePayload) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [isAuthReady, setIsAuthReady] = useState(false)

  useEffect(() => {
    void bootstrapAuth()
  }, [])

  useEffect(() => {
    setAuthSessionHandlers({
      onTokenRefresh: (token) => {
        setAccessToken(token)
      },
      onAuthFailure: () => {
        setAccessToken(null)
        setProfile(null)
      },
    })
    return () => setAuthSessionHandlers(null)
  }, [])

  async function bootstrapAuth() {
    try {
      const tokens = await authRefresh()
      setAccessToken(tokens.access_token)
      const me = await authGetMe(tokens.access_token)
      setProfile(me)
    } catch {
      setAccessToken(null)
      setProfile(null)
    } finally {
      setIsAuthReady(true)
    }
  }

  async function login(payload: LoginPayload) {
    const tokens = await authLogin(payload)
    setAccessToken(tokens.access_token)
    const me = await authGetMe(tokens.access_token)
    setProfile(me)
  }

  async function register(payload: RegisterPayload) {
    const tokens = await authRegister(payload)
    setAccessToken(tokens.access_token)
    const me = await authGetMe(tokens.access_token)
    setProfile(me)
  }

  async function logout() {
    await authLogout()
    setAccessToken(null)
    setProfile(null)
  }

  async function refreshSession() {
    const tokens = await authRefresh()
    setAccessToken(tokens.access_token)
    const me = await authGetMe(tokens.access_token)
    setProfile(me)
  }

  async function updateProfile(payload: UpdateProfilePayload) {
    if (!accessToken) {
      throw new Error(translate('errors.common.notAuthenticated'))
    }
    const updated = await authUpdateMe(payload, accessToken)
    setProfile(updated)
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      accessToken,
      profile,
      isAuthReady,
      isAuthenticated: Boolean(accessToken),
      login,
      register,
      logout,
      refreshSession,
      updateProfile,
    }),
    [accessToken, profile, isAuthReady],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return context
}
