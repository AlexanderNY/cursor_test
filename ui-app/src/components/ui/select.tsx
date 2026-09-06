import { forwardRef, SelectHTMLAttributes } from 'react'

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
}

const controlClass =
  'w-full h-11 px-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-sm leading-tight text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed'

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className = '', label, error, children, ...props }, ref) => {
    return (
      <div className="w-full min-w-0">
        {label && (
          <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
            {label}
          </label>
        )}
        <select
          ref={ref}
          className={`${controlClass} ${error ? 'border-red-500 focus:ring-red-500/50 focus:border-red-500' : ''} ${className}`}
          {...props}
        >
          {children}
        </select>
        {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      </div>
    )
  },
)

Select.displayName = 'Select'
