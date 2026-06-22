import { useState } from 'react'

const navItems = [
  { id: 'overview', label: 'Overview', icon: 'grid' },
  { id: 'clusters', label: 'Clusters', icon: 'server' },
  { id: 'nodes', label: 'Nodes', icon: 'cpu' },
  { id: 'pods', label: 'Pods', icon: 'box' },
  { id: 'deployments', label: 'Deployments', icon: 'layers' },
  { id: 'settings', label: 'Settings', icon: 'cog' },
] as const

function NavIcon({ name }: { name: string }) {
  const paths: Record<string, React.ReactNode> = {
    grid: (
      <>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
      </>
    ),
    server: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
    ),
    cpu: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18 6h-2m2-6h2M5 15H3m2-6H3m18 6h-2M5 9h14m-6 6v-2m-4 2v-2" />
    ),
    box: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
    ),
    layers: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    ),
    cog: (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    ),
  }
  return (
    <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
      {paths[name] ?? null}
    </svg>
  )
}

export function K8sSidebar() {
  const [activeId, setActiveId] = useState<string>('overview')

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-[var(--border-color)] bg-[var(--bg-secondary)]">
      <div className="flex h-14 items-center border-b border-[var(--border-color)] px-4">
        <span className="font-semibold text-[var(--text-primary)]">K8s Console</span>
      </div>
      <nav className="flex-1 space-y-0.5 p-3">
        {navItems.map((item) => {
          const isActive = activeId === item.id
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setActiveId(item.id)}
              className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500/50 ${
                isActive
                  ? 'bg-primary-500/10 text-primary-400'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]/50 hover:text-[var(--text-primary)]'
              }`}
            >
              <NavIcon name={item.icon} />
              {item.label}
            </button>
          )
        })}
      </nav>
    </aside>
  )
}
