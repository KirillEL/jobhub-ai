import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AuthForm from '../../components/auth/AuthForm'
import ToastStack from '../../components/common/ToastStack'
import { useAuth } from '../../auth/AuthContext'
import { useToasts } from '../../hooks/useToasts'
import { useI18n } from '../../shared/i18n'
import type { LoginPayload, RegisterPayload } from '../../types'
import './styles.scss'

type AuthFormState = RegisterPayload & LoginPayload

export default function AuthPage() {
  const navigate = useNavigate()
  const { login, register } = useAuth()
  const { toasts, pushToast, removeToast } = useToasts()
  const { t } = useI18n()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState<AuthFormState>({
    email: '',
    password: '',
    full_name: '',
  })

  async function handleSubmit(): Promise<void> {
    setLoading(true)
    try {
      if (mode === 'register') {
        await register({
          email: form.email,
          password: form.password,
          full_name: form.full_name?.trim() || undefined,
        })
        pushToast('success', t('auth.toastRegisterSuccessTitle'), t('auth.toastRegisterSuccessText'))
      } else {
        await login({ email: form.email, password: form.password })
        pushToast('success', t('auth.toastLoginSuccessTitle'), t('auth.toastLoginSuccessText'))
      }
      setForm((prev) => ({ ...prev, password: '' }))
      navigate('/', { replace: true })
    } catch (authError) {
      pushToast(
        'error',
        mode === 'register' ? t('auth.toastRegisterErrorTitle') : t('auth.toastLoginErrorTitle'),
        authError instanceof Error ? authError.message : t('auth.toastAuthErrorText'),
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <ToastStack toasts={toasts} onClose={removeToast} />
      <section className="auth-page__shell">
        <article className="auth-page__intro">
          <div className="auth-page__badge">{t('auth.badge')}</div>
          <h1>{t('auth.heroTitle')}</h1>
          <p className="subtitle auth-page__subtitle">
            {t('auth.heroSubtitle')}
          </p>
          <div className="auth-page__meta">
            <span>{t('auth.meta1')}</span>
            <span>{t('auth.meta2')}</span>
            <span>{t('auth.meta3')}</span>
          </div>
          <div className="auth-page__stats">
            <div className="auth-page__stat">
              <strong>{t('auth.stat1Title')}</strong>
              <span>{t('auth.stat1Text')}</span>
            </div>
            <div className="auth-page__stat">
              <strong>{t('auth.stat2Title')}</strong>
              <span>{t('auth.stat2Text')}</span>
            </div>
            <div className="auth-page__stat">
              <strong>{t('auth.stat3Title')}</strong>
              <span>{t('auth.stat3Text')}</span>
            </div>
          </div>
        </article>

        <article className="auth-page__card">
          <AuthForm
            mode={mode}
            loading={loading}
            value={form}
            onChange={setForm}
            onSubmit={handleSubmit}
            onToggleMode={() => setMode((prev) => (prev === 'login' ? 'register' : 'login'))}
            className="auth-form auth-form--page"
          />
        </article>
      </section>
    </main>
  )
}
