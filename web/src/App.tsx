import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/AuthContext'
import './App.scss'
import { useI18n } from './shared/i18n'
import AuthPage from './pages/AuthPage'
import AppShell from './layout/AppShell'
import DashboardPage from './pages/DashboardPage'
import InsightsPage from './pages/InsightsPage'
import JobsPage from './pages/JobsPage'
import ChatPage from './pages/ChatPage'
import OnboardingPage from './pages/OnboardingPage'
import SettingsPage from './pages/SettingsPage'
import VacanciesPage from './pages/VacanciesPage'

function ProtectedShell({ isAuthenticated }: { isAuthenticated: boolean }) {
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />
  }
  return <AppShell />
}

function App() {
  const { isAuthReady, isAuthenticated } = useAuth()
  const { t } = useI18n()

  if (!isAuthReady) {
    return (
      <main className="layout">
        <section className="panel">
          <h2>{t('app.loadingTitle')}</h2>
          <p className="subtitle">{t('app.loadingSubtitle')}</p>
          <div className="loader-progress">
            <div className="loader-progress__value" style={{ width: '60%' }} />
          </div>
        </section>
      </main>
    )
  }

  return (
    <Routes>
      <Route path="/auth" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <AuthPage />} />
      <Route path="/" element={<ProtectedShell isAuthenticated={isAuthenticated} />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="onboarding" element={<OnboardingPage />} />
        <Route path="jobs" element={<JobsPage />} />
        <Route path="vacancies" element={<VacanciesPage />} />
        <Route path="insights" element={<InsightsPage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to={isAuthenticated ? '/dashboard' : '/auth'} replace />} />
    </Routes>
  )
}

export default App
