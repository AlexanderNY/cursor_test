import { Link } from 'react-router-dom'

const DEVELOPERS = [
  { name: 'CopyParse', role: 'Product' },
  { name: 'Control Panel team', role: 'Engineering' },
]

export function Footer() {
  return (
    <footer className="shrink-0 border-t border-[var(--border-color)] bg-[var(--bg-secondary)] px-4 md:px-6 py-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between text-xs text-[var(--text-muted)]">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <span>© {new Date().getFullYear()} Control Panel</span>
          <span className="hidden sm:inline text-[var(--border-color)]">|</span>
          <span>
            Разработка:{' '}
            {DEVELOPERS.map((d, i) => (
              <span key={d.name}>
                {i > 0 ? ', ' : ''}
                <span className="text-[var(--text-secondary)]">{d.name}</span>
                <span className="text-[var(--text-muted)]"> ({d.role})</span>
              </span>
            ))}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/about"
            className="text-[var(--text-secondary)] hover:text-primary-400 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 rounded"
          >
            Справка
          </Link>
          <Link
            to="/feedback"
            className="text-[var(--text-secondary)] hover:text-primary-400 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 rounded"
          >
            Обратная связь
          </Link>
          <Link
            to="/next"
            className="text-[var(--text-secondary)] hover:text-primary-400 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 rounded"
          >
            Что далее
          </Link>
        </div>
      </div>
    </footer>
  )
}
