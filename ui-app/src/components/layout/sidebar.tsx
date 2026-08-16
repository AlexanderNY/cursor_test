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
    <aside className="w-56 lg:w-64 shrink-0 self-stretch bg-[var(--bg-secondary)] border-r border-[var(--border-color)] flex flex-col min-h-0">
      {user && (
        <div className="px-4 py-2.5 border-b border-[var(--border-color)] shrink-0">
          <p className="text-xs text-[var(--text-muted)] truncate">
            {user.role ?? '—'} ·{' '}
            <Link
              to="/profile?tab=billing"
              className="text-primary-400 hover:text-primary-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 rounded"
            >
              {user.tariff ?? 'free'}
            </Link>
          </p>
          {user.group_name && (
            <p
              className="text-xs text-[var(--text-muted)] mt-0.5 truncate"
              title={`Группа: ${user.group_name} · ${user.role_in_group ?? ''}`}
            >
              Team: {user.group_name}
            </p>
          )}
        </div>
      )}

      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto min-h-0">
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
        {(user?.role === 'manager' ||
          user?.role === 'author' ||
          user?.role === 'admin' ||
          user?.role_in_group ||
          user?.group_id) && (
          <>
            <div className="my-3 border-t border-[var(--border-color)]" />
            <NavLink
              to={groupNavItem.path}
              className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
            >
              <groupNavItem.Icon className={iconClassName} />
              <span>{groupNavItem.label}</span>
            </NavLink>
          </>
        )}
        {user?.role === 'admin' && (
          <>
            <div className="my-3 border-t border-[var(--border-color)]" />
            {adminNavItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
              >
                <item.Icon className={iconClassName} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </>
        )}
      </nav>
    </aside>
  )
}
