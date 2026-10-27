import { Link, useLocation } from 'react-router-dom'
import { prefetchPyodideRuntime } from '@/game/bowl/pyodide-prefetch'

const TRAINERS = [
  { id: 'code', label: 'Code', to: '/game/code' },
  { id: 'sql', label: 'SQL', to: '/game/sql' },
  { id: 'git', label: 'Git', to: '/game/git' },
] as const

export function TrainerTabs() {
  const { pathname } = useLocation()

  return (
    <nav className="learn-tabs" aria-label="Тренажёры">
      {TRAINERS.map((trainer) => {
        const isActive = pathname === trainer.to
        return (
          <Link
            key={trainer.id}
            to={trainer.to}
            className={`learn-tab${isActive ? ' is-active' : ''}`}
            aria-current={isActive ? 'page' : undefined}
            onMouseEnter={trainer.id === 'code' ? prefetchPyodideRuntime : undefined}
            onFocus={trainer.id === 'code' ? prefetchPyodideRuntime : undefined}
          >
            {trainer.label}
          </Link>
        )
      })}
    </nav>
  )
}
