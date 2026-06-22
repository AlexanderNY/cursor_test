import { NavLink, Link } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { navItems, groupNavItem, adminNavItems } from '@/config/nav'

const iconClassName = 'h-5 w-5'

export function Sidebar() {
  const { user } = useAuth()

  return (
    <aside className="w-64 h-screen bg-[var(--bg-secondary)] border-r border-[var(--border-color)] flex flex-col">
      <div className="p-6 border-b border-[var(--border-color)]">
        <h1 className="text-xl font-bold text-gradient">Control Panel</h1>
        {user && (
          <>
            <p className="text-sm text-[var(--text-muted)] mt-1 truncate">
              {user.username}
            </p>
            <p className="text-xs text-[var(--text-muted)] mt-0.5 truncate">
              {user.role ?? '—'} ·{' '}
              <Link
                to="/profile?tab=billing"
                className="text-primary-400 hover:text-primary-300 hover:underline focus:outline-none focus:underline focus-visible:ring-2 focus-visible:ring-primary-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--bg-secondary)] rounded"
              >
                {user.tariff ?? 'free'}
              </Link>
            </p>
            {user.group_name && (
              <p className="text-xs text-[var(--text-muted)] mt-0.5 truncate" title={`Группа: ${user.group_name} · ${user.role_in_group === 'manager' ? 'менеджер' : 'автор'}`}>
                Группа: {user.group_name} · {user.role_in_group === 'manager' ? 'менеджер' : 'автор'}
              </p>
            )}
          </>
        )}
      </div>

      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `nav-link ${isActive ? 'nav-link-active' : ''}`
            }
          >
            <item.Icon className={iconClassName} />
            <span>{item.label}</span>
          </NavLink>
        ))}
        {(user?.role === 'manager' || user?.role === 'author') && (
          <>
            <div className="my-4 border-t border-[var(--border-color)]"></div>
            <NavLink
              to={groupNavItem.path}
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link-active' : ''}`
              }
            >
              <groupNavItem.Icon className={iconClassName} />
              <span>{groupNavItem.label}</span>
            </NavLink>
          </>
        )}
        {user?.role === 'admin' && (
          <>
            <div className="my-4 border-t border-[var(--border-color)]"></div>
            {adminNavItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'nav-link-active' : ''}`
                }
              >
                <item.Icon className={iconClassName} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </>
        )}
      </nav>

      <div className="p-4 border-t border-[var(--border-color)] space-y-3">
        <Link
          to="/feedback"
          className="nav-link w-full justify-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className={iconClassName} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <span>Обратная связь</span>
        </Link>
        <p className="text-xs text-[var(--text-muted)] text-center">
          © 2026 Control Panel ·{' '}
          <Link to="/about" className="text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 rounded">About</Link>
          {' · '}
          <Link to="/pricing" className="text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 rounded">Pricing</Link>
        </p>
      </div>
    </aside>
  )
}
