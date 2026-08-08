import { useCallback, useEffect, useState } from 'react'
import { NavLink, Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { useBrand } from '@/contexts/brand-context'
import { navItems, groupNavItem, adminNavItems } from '@/config/nav'
import { smmService } from '@/services/smm-service'

const iconClassName = 'h-5 w-5'
const INBOX_BADGE_POLL_MS = 25_000

export function Sidebar() {
  const { user } = useAuth()
  const { selectedBrandId } = useBrand()
  const location = useLocation()
  const [newComments, setNewComments] = useState(0)

  const loadBadge = useCallback(async () => {
    if (!user) return
    try {
      const res = await smmService.listInbox({
        brand_id: selectedBrandId ?? undefined,
        type: 'comment',
        status: 'new',
        limit: 50,
      })
      setNewComments(res.items?.length ?? 0)
    } catch {
      /* ignore */
    }
  }, [user, selectedBrandId])

  useEffect(() => {
    if (!user) return
    void loadBadge()
    const t = setInterval(() => void loadBadge(), INBOX_BADGE_POLL_MS)
    return () => clearInterval(t)
  }, [user, loadBadge])

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
              <p className="text-xs text-[var(--text-muted)] mt-0.5 truncate" title={`Группа: ${user.group_name} · ${user.role_in_group ?? ''}`}>
                Team: {user.group_name} · {user.role_in_group === 'admin' || user.role_in_group === 'manager' ? 'Admin' : user.role_in_group === 'analyst' ? 'Analyst' : 'Editor'}
              </p>
            )}
          </>
        )}
      </div>

      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path === '/inbox' ? '/inbox?mode=comments' : item.path}
            className={({ isActive }) =>
              `nav-link ${isActive || (item.path === '/inbox' && location.pathname === '/inbox') ? 'nav-link-active' : ''}`
            }
          >
            <item.Icon className={iconClassName} />
            <span className="flex-1">{item.label}</span>
            {item.path === '/inbox' && newComments > 0 && (
              <span className="ml-auto text-[10px] font-semibold min-w-[1.25rem] h-5 px-1.5 rounded-full bg-amber-500 text-white flex items-center justify-center">
                {newComments > 99 ? '99+' : newComments}
              </span>
            )}
          </NavLink>
        ))}
        {(user?.role === 'manager' || user?.role === 'author' || user?.role === 'admin' || user?.role_in_group || user?.group_id) && (
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
          className="nav-link w-full justify-center border border-[var(--border-color)]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className={iconClassName} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <span>Обратная связь</span>
        </Link>
        <p className="text-xs text-[var(--text-muted)] text-center">
          © 2026 Control Panel
        </p>
      </div>
    </aside>
  )
}
