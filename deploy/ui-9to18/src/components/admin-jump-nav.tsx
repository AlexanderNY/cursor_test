import { useEffect, useState } from 'react'

export type AdminNavItem = {
  id: string
  label: string
  href?: string
}

type AdminJumpNavProps = {
  items: AdminNavItem[]
  ariaLabel?: string
}

/** Sticky jump menu for long admin pages. */
export function AdminJumpNav({ items, ariaLabel = 'Разделы админки' }: AdminJumpNavProps) {
  const [activeId, setActiveId] = useState(items[0]?.id || '')

  useEffect(() => {
    const ids = items.filter((item) => !item.href).map((item) => item.id)
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
  }, [items])

  return (
    <nav className="admin-jump-nav" aria-label={ariaLabel}>
      <ul className="admin-jump-nav-list">
        {items.map((item) => {
          const isExternal = Boolean(item.href)
          const isActive = !isExternal && activeId === item.id
          const className = isActive
            ? 'admin-jump-nav-link is-active'
            : 'admin-jump-nav-link'
          if (item.href) {
            return (
              <li key={item.id}>
                <a className={className} href={item.href}>
                  {item.label}
                </a>
              </li>
            )
          }
          return (
            <li key={item.id}>
              <a className={className} href={`#${item.id}`}>
                {item.label}
              </a>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
