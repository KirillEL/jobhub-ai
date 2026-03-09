import { useState } from 'react'
import { useI18n } from '../../shared/i18n'
import type { LoginPayload, RegisterPayload } from '../../types'
import { validateEmail, validateFullName, validatePassword } from '../../utils/validation'
import EyeIcon from '../icons/EyeIcon'
import './styles.scss'

type AuthFormState = RegisterPayload & LoginPayload

interface AuthFormProps {
  mode: 'login' | 'register'
  loading: boolean
  value: AuthFormState
  onChange: (next: AuthFormState) => void
  onSubmit: () => Promise<void>
  onToggleMode: () => void
  className?: string
}

export default function AuthForm({
  mode,
  loading,
  value,
  onChange,
  onSubmit,
  onToggleMode,
  className,
}: AuthFormProps) {
  const { t } = useI18n()
  const [isPasswordVisible, setIsPasswordVisible] = useState(false)
  const [submitAttempted, setSubmitAttempted] = useState(false)
  const [touched, setTouched] = useState({
    email: false,
    password: false,
    full_name: false,
  })
  const isRegisterMode = mode === 'register'
  const emailError = validateEmail(value.email)
  const passwordError = validatePassword(value.password)
  const fullNameError = isRegisterMode ? validateFullName(value.full_name ?? '') : null
  const hasErrors = Boolean(emailError || passwordError || fullNameError)

  async function handleSubmit(event: React.FormEvent): Promise<void> {
    event.preventDefault()
    setSubmitAttempted(true)
    if (hasErrors) return
    await onSubmit()
  }

  function canShowError(fieldTouched: boolean): boolean {
    return submitAttempted || fieldTouched
  }

  return (
    <form className={className ?? 'auth-form'} onSubmit={handleSubmit} noValidate>
      <span className="pill">{isRegisterMode ? t('auth.form.registerPill') : t('auth.form.loginPill')}</span>
      <h3>{isRegisterMode ? t('auth.form.registerTitle') : t('auth.form.loginTitle')}</h3>
      <p className="auth-form__hint">
        {isRegisterMode
          ? t('auth.form.registerHint')
          : t('auth.form.loginHint')}
      </p>
      <label>
        {t('auth.form.email')}
        <input
          type="email"
          value={value.email}
          onChange={(event) => onChange({ ...value, email: event.target.value.trim() })}
          onBlur={() => setTouched((prev) => ({ ...prev, email: true }))}
          className={canShowError(touched.email) && emailError ? 'input-error' : undefined}
          required
        />
        {canShowError(touched.email) && emailError ? <span className="field-error">{emailError}</span> : null}
      </label>
      {isRegisterMode ? (
        <label>
          {t('auth.form.name')}
          <input
            value={value.full_name ?? ''}
            onChange={(event) => onChange({ ...value, full_name: event.target.value })}
            onBlur={() => setTouched((prev) => ({ ...prev, full_name: true }))}
            className={canShowError(touched.full_name) && fullNameError ? 'input-error' : undefined}
            placeholder={t('auth.form.namePlaceholder')}
          />
          {canShowError(touched.full_name) && fullNameError ? (
            <span className="field-error">{fullNameError}</span>
          ) : null}
        </label>
      ) : null}
      <label>
        {t('auth.form.password')}
        <div className="password-field">
          <input
            type={isPasswordVisible ? 'text' : 'password'}
            value={value.password}
            onChange={(event) => onChange({ ...value, password: event.target.value })}
            onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
            className={canShowError(touched.password) && passwordError ? 'input-error' : undefined}
            minLength={8}
            autoComplete={isRegisterMode ? 'new-password' : 'current-password'}
            required
          />
          <button
            type="button"
            className="password-toggle"
            onClick={() => setIsPasswordVisible((prev) => !prev)}
            aria-label={isPasswordVisible ? t('auth.form.hidePassword') : t('auth.form.showPassword')}
          >
            <EyeIcon visible={isPasswordVisible} />
          </button>
        </div>
        {canShowError(touched.password) && passwordError ? (
          <span className="field-error">{passwordError}</span>
        ) : null}
      </label>
      <div className="auth-actions">
        <button type="submit" disabled={loading || hasErrors}>
          {loading ? t('auth.form.waiting') : isRegisterMode ? t('auth.form.createAccount') : t('auth.form.loginButton')}
        </button>
        <button type="button" className="btn--secondary btn--ghost" onClick={onToggleMode}>
          {isRegisterMode ? t('auth.form.haveAccount') : t('auth.form.createAccountSecondary')}
        </button>
      </div>
    </form>
  )
}
