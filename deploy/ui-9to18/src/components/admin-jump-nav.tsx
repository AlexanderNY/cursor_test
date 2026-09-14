import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

export type AdminNavItem = {
  id: string
  label: string
  /** In-app path or absolute URL. Omit for in-page `#id` jump. */
  href?: string
  /** Same-page action (e.g. switch cabinet pane). Takes precedence over href. */
  onClick?: () => void
}

export type AdminNavGroup = {
  label: string
  items: AdminNavItem[]
}

/** Always-visible destinations for any admin screen. */
export const ADMIN_GLOBAL_MENU: AdminNavItem[] = [
  { id: 'nav-site-admin', label: 'Админка сайта', href: '/admin' },
  { id: 'nav-learn-cms', label: 'Learn CMS', href: '/game/learn/admin' },
  { id: 'nav-learn-new', label: 'Новая запись', href: '/game/learn/admin/new' },
  { id: 'nav-learning-map', label: 'Карта обучения', href: '/game/learning-map' },
  { id: 'nav-learn-public', label: 'Каталог Learn', href: '/game/learn' },
  { id: 'nav-account', label: 'Кабинет', href: '/account' },
]

type AdminJumpNavProps = {
  /** Page-local sections (#id) and extra links for this screen. */
  items?: AdminNavItem[]
  /** Links to service cabinets / public apps — same pill style as Админ. */
  serviceItems?: AdminNavItem[]
  /** Extra named groups (e.g. кабинет sections). Rendered after global/services. */
  groups?: AdminNavGroup[]
  /** Show global admin destinations. Default true. */
  showGlobal?: boolean
  ariaLabel?: string
  className?: string
}

function pathAndSearch(href: string): { pathname: string; search: string } {
  const [pathPart, searchPart = ''] = href.split('?')
  return { pathname: pathPart || '/', search: searchPart }
}

function isPathActive(pathname: string, search: string, href: string): boolean {
  if (!href.startsWith('/')) {
    return false
  }
  const target = pathAndSearch(href)
  if (target.pathname === '/admin') {
    return pathname === '/admin' || pathname.startsWith('/admin/')
  }
  if (target.pathname === '/game/learn/admin/new') {
    return pathname === '/game/learn/admin/new'
  }
  if (target.pathname === '/game/learn/admin') {
    if (pathname === '/game/learn/admin') {
      return true
    }
    return /^\/game\/learn\/admin\/(?!login$|new$)[a-z0-9-]+$/i.test(pathname)
  }
  if (target.pathname === '/account') {
    if (pathname !== '/account') {
      return false
    }
    const currentSection = new URLSearchParams(search).get('section') || ''
    const targetSection = new URLSearchParams(target.search).get('section') || ''
    return currentSection === targetSection
  }
  if (pathname !== target.pathname && !pathname.startsWith(`${target.pathname}/`)) {
    return false
  }
  if (!target.search) {
    return true
  }
  const current = new URLSearchParams(search)
  const wanted = new URLSearchParams(target.search)
  for (const [key, value] of wanted.entries()) {
    if (current.get(key) !== value) {
      return false
    }
  }
  return true
}

function NavLinkItem({
  item,
  pathname,
  search,
  activeHashId,
}: {
  item: AdminNavItem
  pathname: string
  search: string
  activeHashId: string
}) {
  const isExternal = Boolean(item.href && /^https?:\/\//i.test(item.href))
  const isRoute = Boolean(item.href && item.href.startsWith('/'))
  const isHash = !item.href

  let isActive = false
  if (isHash) {
    isActive = activeHashId === item.id
  } else if (isRoute && item.href) {
    isActive = isPathActive(pathname, search, item.href)
  }

  const className = isActive ? 'admin-jump-nav-link is-active' : 'admin-jump-nav-link'

  if (item.onClick) {
    return (
      <li key={item.id}>
        <button type="button" className={className} onClick={item.onClick}>
          {item.label}
        </button>
      </li>
    )
  }

  if (isRoute && item.href) {
    return (
      <li key={item.id}>
        <Link className={className} to={item.href} aria-current={isActive ? 'page' : undefined}>
          {item.label}
        </Link>
      </li>
    )
  }

  if (isExternal && item.href) {
    return (
      <li key={item.id}>
        <a className={className} href={item.href} target="_blank" rel="noreferrer">
          {item.label}
        </a>
      </li>
    )
  }

  return (
    <li key={item.id}>
      <a
        className={className}
        href={`#${item.id}`}
        onClick={(event) => {
          const node = document.getElementById(item.id)
          if (!node) {
            return
          }
          event.preventDefault()
          node.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }}
      >
        {item.label}
      </a>
    </li>
  )
}

function NavGroup({
  label,
  items,
  pathname,
  search,
  activeHashId,
}: {
  label: string
  items: AdminNavItem[]
  pathname: string
  search: string
  activeHashId: string
}) {
  if (items.length === 0) {
    return null
  }
  return (
    <div className="admin-jump-nav-group">
      <p className="admin-jump-nav-label">{label}</p>
      <ul className="admin-jump-nav-list">
        {items.map((item) => (
          <NavLinkItem
            key={item.id}
            item={item}
            pathname={pathname}
            search={search}
            activeHashId={activeHashId}
          />
        ))}
      </ul>
    </div>
  )
}

/** Sticky admin menu: global destinations always at hand + optional page sections. */
export function AdminJumpNav({
  items = [],
  serviceItems = [],
  groups = [],
  showGlobal = true,
  ariaLabel = 'Меню админки',
  className,
}: AdminJumpNavProps) {
  const { pathname, search } = useLocation()
  const hashItems = useMemo(
    () => [
      ...items.filter((item) => !item.href && !item.onClick),
      ...groups.flatMap((group) => group.items.filter((item) => !item.href && !item.onClick)),
    ],
    [items, groups],
  )
  const [activeId, setActiveId] = useState(hashItems[0]?.id || '')

  useEffect(() => {
    const ids = hashItems.map((item) => item.id)
    if (ids.length === 0) {
      return
    }
    const nodes = ids
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => Boolean(el))
    if (nodes.length === 0) {
      return
    }
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)
        if (visible[0]?.target?.id) {
          setActiveId(visible[0].target.id)
        }
      },
      { rootMargin: '-20% 0px -55% 0px', threshold: [0.1, 0.35, 0.6] },
    )
    nodes.forEach((node) => observer.observe(node))
    return () => observer.disconnect()
  }, [hashItems])

  const localItems = items
  const hasAnything =
    (showGlobal && ADMIN_GLOBAL_MENU.length > 0) ||
    serviceItems.length > 0 ||
    groups.some((g) => g.items.length > 0) ||
    localItems.length > 0

  if (!hasAnything) {
    return null
  }

  return (
    <nav
      className={['admin-jump-nav', className].filter(Boolean).join(' ')}
      aria-label={ariaLabel}
    >
      {showGlobal ? (
        <NavGroup
          label="Админ"
          items={ADMIN_GLOBAL_MENU}
          pathname={pathname}
          search={search}
          activeHashId={activeId}
        />
      ) : null}
      <NavGroup
        label="Сервисы"
        items={serviceItems}
        pathname={pathname}
        search={search}
        activeHashId={activeId}
      />
      {groups.map((group) => (
        <NavGroup
          key={group.label}
          label={group.label}
          items={group.items}
          pathname={pathname}
          search={search}
          activeHashId={activeId}
        />
      ))}
      {localItems.length > 0 ? (
        <NavGroup
          label="На странице"
          items={localItems}
          pathname={pathname}
          search={search}
          activeHashId={activeId}
        />
      ) : null}
    </nav>
  )
}
