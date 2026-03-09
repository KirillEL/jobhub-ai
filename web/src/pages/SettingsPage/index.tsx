import { useState } from 'react'
import { clearMyVacancies } from '../../api.ts'
import { useAuth } from '../../auth/AuthContext'
import { useI18n } from '../../shared/i18n'
import Button from '../../shared/ui/Button'
import Card from '../../shared/ui/Card'
import Modal from '../../shared/ui/Modal'
import PageHeader from '../../shared/ui/PageHeader'
import { useTheme } from '../../shared/theme/ThemeProvider'
import { validateFullName } from '../../utils/validation'
import './styles.scss'

type MessageState = { key: string; params?: Record<string, string | number> } | null

export default function SettingsPage() {
  const { accessToken, profile, updateProfile } = useAuth()
  const { theme, setTheme } = useTheme()
  const { t } = useI18n()
  const [fullName, setFullName] = useState(profile?.full_name ?? '')
  const [saving, setSaving] = useState(false)
  const [cleanupOpen, setCleanupOpen] = useState(false)
  const [cleanupLoading, setCleanupLoading] = useState(false)
  const [message, setMessage] = useState<MessageState>(null)

  const nameError = validateFullName(fullName)

  async function handleProfileSave() {
    if (nameError) return
    setSaving(true)
    setMessage(null)
    try {
      await updateProfile({ full_name: fullName.trim() || null })
      setMessage({ key: 'settings.profileSaved' })
    } catch (error) {
      setMessage(error instanceof Error ? { key: error.message } : { key: 'settings.profileUpdateFailed' })
    } finally {
      setSaving(false)
    }
  }

  async function handleCleanup() {
    if (!accessToken) return
    setCleanupLoading(true)
    setMessage(null)
    try {
      const result = await clearMyVacancies(accessToken)
      setMessage({ key: 'settings.cleanupDone', params: { count: result.removed } })
      setCleanupOpen(false)
    } catch (error) {
      setMessage(error instanceof Error ? { key: error.message } : { key: 'settings.cleanupFailed' })
    } finally {
      setCleanupLoading(false)
    }
  }

  return (
    <main className="layout settings-page">
      <PageHeader title={t('settings.title')} subtitle={t('settings.subtitle')} />

      <section className="cards-grid">
        <Card>
          <h3>{t('settings.profile')}</h3>
          <label>
            {t('settings.email')}
            <input value={profile?.email ?? ''} disabled />
          </label>
          <label>
            {t('settings.name')}
            <input value={fullName} onChange={(event) => setFullName(event.target.value)} />
            {nameError ? <span className="field-error">{nameError}</span> : null}
          </label>
          <Button className="save-btn" onClick={handleProfileSave} disabled={saving || Boolean(nameError)}>
            {saving ? t('settings.saving') : t('settings.save')}
          </Button>
        </Card>

        <Card>
          <h3>{t('settings.appearance')}</h3>
          <p className="subtitle">
            {t('settings.currentTheme')}: {theme === 'light' ? t('settings.light') : t('settings.dark')}
          </p>
          <div className="inline-buttons">
            <Button variant={theme === 'light' ? 'primary' : 'secondary'} onClick={() => setTheme('light')}>
              {t('settings.light')}
            </Button>
            <Button variant={theme === 'dark' ? 'primary' : 'secondary'} onClick={() => setTheme('dark')}>
              {t('settings.dark')}
            </Button>
          </div>
        </Card>

        <Card>
          <h3>{t('settings.data')}</h3>
          <p className="subtitle">{t('settings.cleanupDescription')}</p>
          <Button className="settings_cleanup__btn" variant="danger" onClick={() => setCleanupOpen(true)}>
            {t('settings.cleanup')}
          </Button>
        </Card>
      </section>

      {message ? <p className="form-hint">{t(message.key, message.params)}</p> : null}
      {cleanupOpen ? (
        <Modal
          title={t('settings.cleanupModalTitle')}
          text={t('settings.cleanupModalText')}
          confirmLabel={t('settings.cleanupModalConfirm')}
          loading={cleanupLoading}
          onConfirm={() => void handleCleanup()}
          onCancel={() => setCleanupOpen(false)}
        />
      ) : null}
    </main>
  )
}
