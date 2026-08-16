import { Link } from 'react-router-dom'
import { useBrand } from '@/contexts/brand-context'

interface BrandContextBarProps {
  className?: string
}

/** Постоянный индикатор выбранного Brand — виден на любом экране. */
export function BrandContextBar({ className = '' }: BrandContextBarProps) {
  const { selectedBrand, selectedBrandId, brands } = useBrand()

  if (brands.length === 0) return null

  if (!selectedBrandId || !selectedBrand) {
    return (
      <div
        className={`flex items-center gap-2 rounded-xl border border-dashed border-[var(--border-color)] bg-[var(--bg-tertiary)]/40 px-3 py-2 text-sm text-[var(--text-muted)] ${className}`}
        role="status"
      >
        <span className="h-2.5 w-2.5 rounded-full bg-[var(--text-muted)]/50" aria-hidden />
        <span>
          Brand не выбран — данные по всем брендам.{' '}
          <Link to="/brands" className="text-primary-400 hover:underline">
            Выбрать бренд
          </Link>
        </span>
      </div>
    )
  }

  return (
    <div
      className={`sticky top-0 z-10 flex items-center gap-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] px-3 py-2 shadow-sm ${className}`}
      role="status"
      aria-label={`Работаем с брендом ${selectedBrand.name}`}
    >
      <span
        className="h-3 w-3 shrink-0 rounded-full ring-2 ring-[var(--bg-tertiary)]"
        style={{ backgroundColor: selectedBrand.color ?? '#64748b' }}
        aria-hidden
      />
      <div className="min-w-0 flex-1">
        <p className="text-[10px] uppercase tracking-wide text-[var(--text-muted)] leading-none mb-0.5">
          Работаем с
        </p>
        <p className="text-sm font-medium text-[var(--text-primary)] truncate">
          {selectedBrand.name}
        </p>
      </div>
      <Link
        to="/brands"
        className="shrink-0 text-xs text-primary-400 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 rounded"
      >
        Сменить
      </Link>
    </div>
  )
}
