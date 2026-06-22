import type { HTMLAttributes } from 'react'

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {}

export function Skeleton({ className = '', ...props }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded bg-[var(--bg-tertiary)] ${className}`.trim()}
      {...props}
    />
  )
}

export function SkeletonText({ lines = 3, className = '' }: { lines?: number; className?: string }) {
  return (
    <div className={`space-y-2 ${className}`.trim()}>
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton
          key={i}
          className={`h-4 ${i === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full'}`}
        />
      ))}
    </div>
  )
}

export function SkeletonCard({ className = '' }: { className?: string } = {}) {
  return (
    <div className={`rounded-2xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-6 ${className}`.trim()}>
      <Skeleton className="mb-4 h-6 w-1/3" />
      <SkeletonText lines={4} />
      <div className="mt-4 flex gap-2">
        <Skeleton className="h-10 w-24 rounded-xl" />
        <Skeleton className="h-10 w-24 rounded-xl" />
      </div>
    </div>
  )
}

interface TableSkeletonProps {
  rows?: number
  cols?: number
  className?: string
}

export function TableSkeleton({ rows = 5, cols = 4, className = '' }: TableSkeletonProps) {
  return (
    <div className={`overflow-hidden rounded-xl border border-[var(--border-color)] ${className}`.trim()}>
      <div className="border-b border-[var(--border-color)] bg-[var(--bg-tertiary)] px-4 py-3">
        <div className="flex gap-4">
          {Array.from({ length: cols }, (_, i) => (
            <Skeleton key={i} className="h-4 flex-1" />
          ))}
        </div>
      </div>
      <div className="divide-y divide-[var(--border-color)]">
        {Array.from({ length: rows }, (_, i) => (
          <div key={i} className="flex gap-4 px-4 py-3">
            {Array.from({ length: cols }, (_, j) => (
              <Skeleton key={j} className="h-4 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
