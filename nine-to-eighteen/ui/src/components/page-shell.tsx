import { useEffect, useState, type ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ThemeToggle } from '@/components/theme-toggle'
import { useSiteAuthSession } from '@/data/site/site-auth'

interface PageShellProps {
  children: ReactNode
  showBrandLink?: boolean
  /** Public reading UI (mobile-first) vs CMS / cabinet (desktop-first). */
  variant?: 'public' | 'admin'
  /** Narrower column and larger type for articles. */
  content?: 'default' | 'article'
}

interface SiteNavItem {
  label: string
  to: string
  isActive: (pathname: string, hash: string) => boolean
}

const SITE_NAV: SiteNavItem[] = [
  {
    label: 'О нас',
    to: '/#about',
    isActive: (pathname, hash) => pathname === '/' && hash === '#about',
  },
  {
    label: 'Контакты',
    to: '/#contacts',
    isActive: (pathname, hash) => pathname === '/' && hash === '#contacts',
  },
  {
    label: 'Лекции',
    to: '/game/learn',
    isActive: (pathname) => pathname === '/game/learn' || pathname.startsWith('/game/learn/'),
  },
  {
    label: 'Карта',
    to: '/game/learning-map',
    isActive: (pathname) =>
      pathname === '/game/learning-map' || pathname.startsWith('/game/learning-map/'),
  },
]

function MenuIcon({ isOpen }: { isOpen: boolean }) {
  return (
    <span className={`site-nav-toggle-icon${isOpen ? ' is-open' : ''}`} aria-hidden>
      <span />
      <span />
      <span />
    </span>
  )
}

export function PageShell({
  children,
  showBrandLink = true,
  variant = 'public',
  content = 'default',
}: PageShellProps) {
  const location = useLocation()
  const session = useSiteAuthSession()
  const [isNavOpen, setIsNavOpen] = useState(false)

  useEffect(() => {
    setIsNavOpen(false)
  }, [location.pathname, location.search, location.hash])

  useEffect(() => {
    if (!isNavOpen) {
      return
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsNavOpen(false)
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [isNavOpen])

  const brand = (
    <>
      <span className="brand-mark">9–18</span>
      <span className="brand-text">
        <span className="brand-domain">9to18.ru</span>
        <span className="brand-tag">проекты и учёба</span>
      </span>
    </>
  )

  const pageClass = [
    'page',
    variant === 'admin' ? 'page--admin' : 'page--public',
    content === 'article' ? 'page--article' : '',
  ]
    .filter(Boolean)
    .join(' ')

  const isLoginActive = location.pathname === '/login'
  const isRegisterActive = location.pathname === '/register'
  const isAccountActive = location.pathname === '/account' || location.pathname.startsWith('/account/')

  return (
    <div className={pageClass}>
      <div className="page-glows" aria-hidden>
        <div className="glow glow-a" />
        <div className="glow glow-b" />
      </div>

      {isNavOpen ? (
        <button
          type="button"
          className="site-nav-backdrop"
          aria-label="Закрыть меню"
          onClick={() => setIsNavOpen(false)}
        />
      ) : null}

      <header className="site-header">
        <div className="site-header-bar">
          {showBrandLink ? (
            <Link to="/" className="brand brand-link">
              {brand}
            </Link>
          ) : (
            <div className="brand">{brand}</div>
          )}

          <button
            type="button"
            className="site-nav-toggle"
            aria-expanded={isNavOpen}
            aria-controls="site-nav"
            aria-label={isNavOpen ? 'Закрыть меню' : 'Открыть меню'}
            onClick={() => setIsNavOpen((open) => !open)}
          >
            <MenuIcon isOpen={isNavOpen} />
          </button>

          <div id="site-nav" className={`site-header-actions${isNavOpen ? ' is-open' : ''}`}>
            <nav className="site-nav" aria-label="Основное меню">
              {SITE_NAV.map((item) => {
                const isActive = item.isActive(location.pathname, location.hash)
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={isActive ? 'site-nav-link is-active' : 'site-nav-link'}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    {item.label}
                  </Link>
                )
              })}
            </nav>
            <div className="site-header-tools">
              <ThemeToggle />
              {session ? (
                <Link
                  to="/account"
                  className={isAccountActive ? 'site-nav-account is-active' : 'site-nav-account'}
                  aria-current={isAccountActive ? 'page' : undefined}
                >
                  {session.username}
                </Link>
              ) : (
                <>
                  <Link
                    to="/login"
                    className={isLoginActive ? 'site-nav-login is-active' : 'site-nav-login'}
                    aria-current={isLoginActive ? 'page' : undefined}
                  >
                    Войти
                  </Link>
                  <Link
                    to="/register"
                    className={isRegisterActive ? 'site-nav-cta is-active' : 'site-nav-cta'}
                  >
                    Регистрация
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="page-inner">
        <main className="page-main">{children}</main>

        <footer className="site-footer">
          <div className="site-footer-brand">
            <span className="site-footer-mark">9–18</span>
            <p className="site-footer-lead">
              Площадка взаимного продвижения проектов и учебных материалов.
            </p>
          </div>
          <div className="site-footer-meta">
            <p>
              Разработка: стек CopyParse — FastAPI, PostgreSQL, React. Учебный контент и блоги
              приложений ведутся на этой же инфраструктуре.
            </p>
            <p className="site-footer-copy">
              © {new Date().getFullYear()} 9to18.ru ·{' '}
              <Link to="/#contacts">Связаться с разработчиками</Link>
            </p>
          </div>
        </footer>
      </div>
    </div>
  )
}
