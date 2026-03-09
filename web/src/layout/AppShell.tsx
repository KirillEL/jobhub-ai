import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../shared/i18n'
import Button from '../shared/ui/Button'
import { useTheme } from '../shared/theme/ThemeProvider'

export default function AppShell() {
  const navigate = useNavigate()
  const { profile, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const { locale, setLocale, t } = useI18n()

  const navItems = [
    { to: '/dashboard', label: t('app.nav.dashboard') },
    { to: '/onboarding', label: t('app.nav.onboarding') },
    { to: '/jobs', label: t('app.nav.jobs') },
    { to: '/vacancies', label: t('app.nav.vacancies') },
    { to: '/insights', label: t('app.nav.insights') },
    { to: '/chat', label: t('app.nav.chat') },
    { to: '/settings', label: t('app.nav.settings') },
  ]

  async function handleLogout() {
    await logout()
    navigate('/auth', { replace: true })
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div>
          <div className="app-brand">
            <span className="app-brand__logo">JH</span>
            <div>
              <strong>JobHub</strong>
              <p>{t('app.brandSubtitle')}</p>
            </div>
          </div>
          <nav className="app-nav" aria-label={t('app.mainMenu')}>
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                className={({ isActive }) => `app-nav__link ${isActive ? 'is-active' : ''}`}
                to={item.to}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="app-sidebar__footer">
          <p>{profile?.email ?? t('app.notAuthorized')}</p>
          <Button variant="secondary" onClick={handleLogout}>
            {t('app.logout')}
          </Button>
        </div>
      </aside>

      <section className="app-main">
        <header className="app-topbar">
          <p>
            {t('app.platformMode')}: {theme === 'light' ? t('app.light') : t('app.dark')}
          </p>
          <div className="inline-buttons">
            <Button variant={locale === 'ru' ? 'secondary' : 'ghost'} onClick={() => setLocale('ru')}>
              RU
            </Button>
            <Button variant={locale === 'en' ? 'secondary' : 'ghost'} onClick={() => setLocale('en')}>
              EN
            </Button>
          </div>
          <Button variant="ghost" onClick={toggleTheme}>
            {t('app.toggleTheme')}
          </Button>
        </header>
        <div className="app-content">
          <Outlet />
        </div>
      </section>
    </div>
  )
}
