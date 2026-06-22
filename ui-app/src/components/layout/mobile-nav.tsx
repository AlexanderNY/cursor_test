import { useState } from 'react'
import { NavLink, Link } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { useTheme } from '@/contexts/theme-context'
import { Button } from '@/components/ui'
import { MenuIcon, CloseIcon, SunIcon, MoonIcon, LogOutIcon } from '@/components/icons'
import { navItems, groupNavItem, adminNavItems } from '@/config/nav'

const iconClassName = 'h-5 w-5'

export function MobileNav() {
  const [isOpen, setIsOpen] = useState(false)
  const { user, logout } = useAuth()
  const { isDarkMode, toggleTheme } = useTheme()

  return (
    <>
      <header className="md:hidden fixed top-0 left-0 right-0 h-16 bg-[var(--bg-secondary)] border-b border-[var(--border-color)] flex items-center justify-between px-4 z-40">
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="p-2 rounded-xl hover:bg-[var(--bg-tertiary)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50"
          aria-label="Open menu"
        >
          <MenuIcon className="h-6 w-6" />
        </button>

        <h1 className="text-lg font-bold text-gradient">Control Panel</h1>

        <button
          type="button"
          onClick={toggleTheme}
          className="p-2 rounded-xl hover:bg-[var(--bg-tertiary)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50"
          aria-label={isDarkMode ? 'Switch to light theme' : 'Switch to dark theme'}
        >
          {isDarkMode ? <SunIcon className={iconClassName} /> : <MoonIcon className={iconClassName} />}
        </button>
      </header>

      {isOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsOpen(false)}
          aria-hidden
        />
      )}

      <div
        className={`md:hidden fixed top-0 left-0 bottom-0 w-72 bg-[var(--bg-secondary)] border-r border-[var(--border-color)] z-50 transform transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-4 border-b border-[var(--border-color)] flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gradient">Control Panel</h1>
            {user && (
              <>
                <p className="text-sm text-[var(--text-muted)] truncate">{user.username}</p>
                <p className="text-xs text-[var(--text-muted)] truncate">
                  {user.role ?? '—'} ·{' '}
                  <Link to="/profile?tab=billing" onClick={() => setIsOpen(false)} className="text-primary-400 hover:text-primary-300 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 rounded">
                    {user.tariff ?? 'free'}
                  </Link>
                </p>
              </>
            )}
          </div>
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            className="p-2 rounded-xl hover:bg-[var(--bg-tertiary)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50"
            aria-label="Close menu"
          >
            <CloseIcon className={iconClassName} />
          </button>
        </div>

        <nav className="p-4 space-y-1 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 140px)' }}>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setIsOpen(false)}
              className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
            >
              <item.Icon className={iconClassName} />
              <span>{item.label}</span>
            </NavLink>
          ))}
          {(user?.role === 'manager' || user?.role === 'author') && (
            <>
              <div className="my-4 border-t border-[var(--border-color)]" />
              <NavLink
                to={groupNavItem.path}
                onClick={() => setIsOpen(false)}
                className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
              >
                <groupNavItem.Icon className={iconClassName} />
                <span>{groupNavItem.label}</span>
              </NavLink>
            </>
          )}
          {user?.role === 'admin' && (
            <>
              <div className="my-4 border-t border-[var(--border-color)]" />
              {adminNavItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsOpen(false)}
                  className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
                >
                  <item.Icon className={iconClassName} />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </>
          )}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[var(--border-color)] space-y-3">
          <Link
            to="/feedback"
            onClick={() => setIsOpen(false)}
            className="nav-link w-full justify-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className={iconClassName} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <span>Обратная связь</span>
          </Link>
          <Button variant="secondary" className="w-full" onClick={logout}>
            <LogOutIcon className="h-5 w-5 mr-2" />
            Logout
          </Button>
        </div>
      </div>
    </>
  )
}
