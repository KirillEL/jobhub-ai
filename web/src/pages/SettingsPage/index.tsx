import { useEffect, useState } from 'react'
import {
  clearMyVacancies,
  getTelegramReportSettings,
  updateTelegramReportSettings,
} from '../../api.ts'
import { useAuth } from '../../auth/AuthContext'
import ToastStack from '../../components/common/ToastStack'
import { useToasts } from '../../hooks/useToasts'
import { useI18n } from '../../shared/i18n'
import Button from '../../shared/ui/Button'
import Card from '../../shared/ui/Card'
import Modal from '../../shared/ui/Modal'
import PageHeader from '../../shared/ui/PageHeader'
import { useTheme } from '../../shared/theme/ThemeProvider'
import type { TelegramReportSettingsUpdate } from '../../types'
import { validateFullName } from '../../utils/validation'
import './styles.scss'

export default function SettingsPage() {
  const { accessToken, profile, updateProfile } = useAuth()
  const { theme, setTheme } = useTheme()
  const { t } = useI18n()
  const { toasts, pushToast, removeToast } = useToasts()
  const [fullName, setFullName] = useState(profile?.full_name ?? '')
  const [saving, setSaving] = useState(false)
  const [cleanupOpen, setCleanupOpen] = useState(false)
  const [cleanupLoading, setCleanupLoading] = useState(false)

  const [telegramEnabled, setTelegramEnabled] = useState(false)
  const [telegramChatId, setTelegramChatId] = useState('')
  const [telegramHour, setTelegramHour] = useState(9)
  const [telegramMinute, setTelegramMinute] = useState(0)
  const [telegramTimezone, setTelegramTimezone] = useState('Europe/Moscow')
  const [telegramQuery, setTelegramQuery] = useState('python backend')
  const [telegramPages, setTelegramPages] = useState(1)
  const [telegramSaving, setTelegramSaving] = useState(false)
  const [telegramLoaded, setTelegramLoaded] = useState(false)

  const nameError = validateFullName(fullName)

  useEffect(() => {
    if (!accessToken) return
    getTelegramReportSettings(accessToken)
      .then((data) => {
        setTelegramEnabled(data.enabled)
        setTelegramChatId(data.telegram_chat_id ?? '')
        setTelegramHour(data.report_hour)
        setTelegramMinute(data.report_minute)
        setTelegramTimezone(data.report_timezone)
        setTelegramQuery(data.report_query)
        setTelegramPages(data.report_pages)
      })
      .catch(() => {})
      .finally(() => setTelegramLoaded(true))
  }, [accessToken])

  async function handleTelegramReportSave() {
    if (!accessToken) return
    setTelegramSaving(true)
    const payload: TelegramReportSettingsUpdate = {
      enabled: telegramEnabled,
      telegram_chat_id: telegramChatId.trim() || null,
      report_hour: telegramHour,
      report_minute: telegramMinute,
      report_timezone: telegramTimezone,
      report_query: telegramQuery,
      report_pages: telegramPages,
    }
    try {
      await updateTelegramReportSettings(payload, accessToken)
      pushToast('success', t('settings.telegramReportSaved'))
    } catch {
      pushToast('error', t('settings.telegramReportSaveFailed'))
    } finally {
      setTelegramSaving(false)
    }
  }

  async function handleProfileSave() {
    if (nameError) return
    setSaving(true)
    try {
      await updateProfile({ full_name: fullName.trim() || null })
      pushToast('success', t('settings.profileSaved'))
    } catch (error) {
      pushToast(
        'error',
        t('settings.profileUpdateFailed'),
        error instanceof Error ? error.message : undefined
      )
    } finally {
      setSaving(false)
    }
  }

  async function handleCleanup() {
    if (!accessToken) return
    setCleanupLoading(true)
    try {
      const result = await clearMyVacancies(accessToken)
      pushToast('success', t('settings.cleanupDone', { count: result.removed }))
      setCleanupOpen(false)
    } catch (error) {
      pushToast(
        'error',
        t('settings.cleanupFailed'),
        error instanceof Error ? error.message : undefined
      )
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
            <Button
              variant={theme === 'light' ? 'primary' : 'secondary'}
              onClick={() => {
                setTheme('light')
                pushToast('success', t('settings.themeUpdated'))
              }}
            >
              {t('settings.light')}
            </Button>
            <Button
              variant={theme === 'dark' ? 'primary' : 'secondary'}
              onClick={() => {
                setTheme('dark')
                pushToast('success', t('settings.themeUpdated'))
              }}
            >
              {t('settings.dark')}
            </Button>
          </div>
        </Card>

        <Card>
          <h3>{t('settings.telegramReport')}</h3>
          <p className="subtitle">{t('settings.telegramReportDescription')}</p>
          {telegramLoaded && (
            <>
              <div className="settings-report-row">
                <span className="settings-report-label">{t('settings.telegramReportEnable')}</span>
                <button
                  type="button"
                  role="switch"
                  aria-checked={telegramEnabled}
                  className="settings-report-switch"
                  onClick={() => setTelegramEnabled(!telegramEnabled)}
                >
                  <span className="settings-report-switch__thumb" aria-hidden />
                </button>
              </div>
              <p className="settings-hint">{t('settings.telegramReportInstructions')}</p>
              <label>
                {t('settings.telegramReportChatId')}
                <input
                  type="text"
                  value={telegramChatId}
                  onChange={(e) => setTelegramChatId(e.target.value)}
                  placeholder={t('settings.telegramReportChatIdPlaceholder')}
                />
              </label>
              <div className="settings-row">
                <label>
                  {t('settings.telegramReportTime')}
                  <div className="settings-time">
                    <select
                      value={telegramHour}
                      onChange={(e) => setTelegramHour(Number(e.target.value))}
                    >
                      {Array.from({ length: 24 }, (_, i) => (
                        <option key={i} value={i}>
                          {String(i).padStart(2, '0')}
                        </option>
                      ))}
                    </select>
                    <span>:</span>
                    <select
                      value={telegramMinute}
                      onChange={(e) => setTelegramMinute(Number(e.target.value))}
                    >
                      {Array.from({ length: 60 }, (_, m) => (
                        <option key={m} value={m}>
                          {String(m).padStart(2, '0')}
                        </option>
                      ))}
                    </select>
                  </div>
                </label>
                <label>
                  {t('settings.telegramReportTimezone')}
                  <select
                    value={telegramTimezone}
                    onChange={(e) => setTelegramTimezone(e.target.value)}
                  >
                    <option value="Europe/Moscow">Europe/Moscow</option>
                    <option value="Europe/Kyiv">Europe/Kyiv</option>
                    <option value="Europe/Minsk">Europe/Minsk</option>
                    <option value="UTC">UTC</option>
                  </select>
                </label>
              </div>
              <label>
                {t('settings.telegramReportQuery')}
                <input
                  type="text"
                  value={telegramQuery}
                  onChange={(e) => setTelegramQuery(e.target.value)}
                  placeholder={t('settings.telegramReportQueryPlaceholder')}
                />
              </label>
              <label>
                {t('settings.telegramReportPages')}
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={telegramPages}
                  onChange={(e) => setTelegramPages(Number(e.target.value) || 1)}
                />
              </label>
              <Button
                className="save-btn"
                onClick={() => void handleTelegramReportSave()}
                disabled={telegramSaving}
              >
                {telegramSaving ? t('settings.saving') : t('settings.save')}
              </Button>
            </>
          )}
        </Card>

        <Card>
          <h3>{t('settings.data')}</h3>
          <p className="subtitle">{t('settings.cleanupDescription')}</p>
          <Button className="settings_cleanup__btn" variant="danger" onClick={() => setCleanupOpen(true)}>
            {t('settings.cleanup')}
          </Button>
        </Card>
      </section>

      <ToastStack toasts={toasts} onClose={removeToast} />
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
