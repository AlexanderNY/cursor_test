import { forwardRef, ButtonHTMLAttributes } from 'react'
import { CheckIcon } from '@/components/icons'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
  success?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'primary', size = 'md', isLoading, success, children, disabled, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus-visible:ring-2 disabled:opacity-50 disabled:cursor-not-allowed'
    
    const variantStyles = {
      primary: success
        ? 'bg-emerald-500/20 border border-emerald-500/50 text-emerald-400 focus:ring-emerald-500/50'
        : 'bg-gradient-to-r from-primary-500 to-primary-600 text-white hover:from-primary-600 hover:to-primary-700 focus:ring-primary-500/50 shadow-lg shadow-primary-500/25',
      secondary: success
        ? 'bg-emerald-500/20 border border-emerald-500/50 text-emerald-400 focus:ring-emerald-500/50'
        : 'bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] hover:border-primary-500/50 focus:ring-primary-500/50',
      danger: success
        ? 'bg-emerald-500/20 border border-emerald-500/50 text-emerald-400 focus:ring-emerald-500/50'
        : 'bg-gradient-to-r from-red-500 to-red-600 text-white hover:from-red-600 hover:to-red-700 focus:ring-red-500/50 shadow-lg shadow-red-500/25',
      ghost: success
        ? 'bg-emerald-500/20 border border-emerald-500/50 text-emerald-400 focus:ring-emerald-500/50'
        : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]/50 focus:ring-primary-500/50',
    }
    
    const sizeStyles = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-6 py-3',
      lg: 'px-8 py-4 text-lg',
    }

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        )}
        {success && !isLoading && (
          <>
            <CheckIcon className="-ml-1 mr-2 h-4 w-4" />
            <span>Saved</span>
          </>
        )}
        {!success && !isLoading && children}
      </button>
    )
  }
)

Button.displayName = 'Button'


