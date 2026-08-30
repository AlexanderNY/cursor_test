import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ThemeToggle } from '@/components/theme-toggle'
import { getSiteAuthSession } from '@/data/site/site-auth'

interface PageShellProps {
  children: ReactNode
  showBrandLink?: boolean
}

export function PageShell({ children, showBrandLink = true }: PageShellProps) {
  const session = getSiteAuthSession()
  const navItems = [
    { label: 'О нас', to: '/#about' },
    { label: 'Контакты', to: '/#contacts' },
    { label: 'Лекции', to: '/game/learn' },
    { label: 'Карта', to: '/game/learning-map' },
    ...(session
      ? [{ label: session.username, to: '/account', isLogin: true as const }]
      : [
          { label: 'Регистрация', to: '/register', isLogin: true as const },
          { label: 'Войти', to: '/login', isLogin: true as const },
        ]),
  ]

  const brand = (
    <>
      <span className="brand-mark">9–18</span>
      <span className="brand-domain">9to18.ru</span>
    </>
  )

  return (
    <div className="page">
      <div className="glow glow-a" aria-hidden />
      <div className="glow glow-b" aria-hidden />

      <div className="page-inner">
        <header className="site-header">
          {showBrandLink ? (
            <Link to="/" className="brand brand-link">
              {brand}
            </Link>
          ) : (
            <div className="brand">{brand}</div>
          )}

          <div className="site-header-actions">
            <nav className="site-nav" aria-label="Основное меню">
              {navItems.map((item) => (
                <Link
                  key={item.to + item.label}
                  to={item.to}
                  className={
                    'isLogin' in item && item.isLogin
                      ? 'site-nav-link site-nav-link-login'
                      : 'site-nav-link'
                  }
                >
                  {item.label}
                </Link>
              ))}
            </nav>
            <ThemeToggle />
          </div>
        </header>

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
