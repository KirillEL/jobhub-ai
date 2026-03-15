import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useI18n } from '../shared/i18n'
import Button from '../shared/ui/Button'
import { useTheme } from '../shared/theme/ThemeProvider'

const SIDEBAR_STORAGE_KEY = 'jobhub-sidebar-collapsed'

function getInitialSidebarCollapsed(): boolean {
  try {
    const stored = localStorage.getItem(SIDEBAR_STORAGE_KEY)
    return stored === 'true'
  } catch {
    return false
  }
}

export default function AppShell() {
  const navigate = useNavigate()
  const { profile, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const { locale, setLocale, t } = useI18n()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(getInitialSidebarCollapsed)

  function toggleSidebar() {
    setSidebarCollapsed((prev) => {
      const next = !prev
      try {
        localStorage.setItem(SIDEBAR_STORAGE_KEY, String(next))
      } catch { }
      return next
    })
  }

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
    <div className={`app-shell ${sidebarCollapsed ? 'is-sidebar-collapsed' : ''}`}>
      <aside className="app-sidebar" aria-expanded={!sidebarCollapsed}>
        <div className="app-sidebar__inner">
          <div className="app-brand">
            <span className="app-brand__logo">JH</span>
            <div className="app-brand__text">
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
                title={item.label}
              >
                <span className="app-nav__link-label">{item.label}</span>
                <span className="app-nav__link-short" aria-hidden>
                  {item.label.charAt(0)}
                </span>
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="app-sidebar__footer">
          <p className="app-sidebar__footer-email">{profile?.email ?? t('app.notAuthorized')}</p>
          <Button variant="secondary" onClick={handleLogout} className="app-sidebar__logout-btn">
            <span className="app-sidebar__logout-label">{t('app.logout')}</span>
            <span className="app-sidebar__logout-short" aria-hidden>↳</span>
          </Button>
          <button
            type="button"
            className="app-sidebar__toggle"
            onClick={toggleSidebar}
            title={sidebarCollapsed ? t('app.sidebarExpand') : t('app.sidebarCollapse')}
            aria-label={sidebarCollapsed ? t('app.sidebarExpand') : t('app.sidebarCollapse')}
          >
            <span className="app-sidebar__toggle-icon" aria-hidden>
              {sidebarCollapsed ? '›' : '‹'}
            </span>
          </button>
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
