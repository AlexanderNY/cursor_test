import { forwardRef, InputHTMLAttributes } from 'react'

type SwitchProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'>

export const Switch = forwardRef<HTMLInputElement, SwitchProps>(function Switch(
  { disabled, className = '', ...props },
  ref,
) {
  return (
    <span className={`relative inline-flex h-6 w-11 shrink-0 align-middle ${className}`}>
      <input
        {...props}
        ref={ref}
        type="checkbox"
        disabled={disabled}
        className="peer absolute inset-0 z-10 h-full w-full cursor-pointer appearance-none rounded-full opacity-0 disabled:cursor-not-allowed"
      />
      <span
        aria-hidden
        className="pointer-events-none h-6 w-11 rounded-full bg-[var(--bg-tertiary)] transition-colors peer-checked:bg-primary-500 peer-indeterminate:bg-primary-500/70 peer-focus-visible:ring-2 peer-focus-visible:ring-primary-500/50 peer-disabled:opacity-50"
      />
      <span
        aria-hidden
        className="pointer-events-none absolute left-1 top-1 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-5 peer-indeterminate:translate-x-2.5 peer-disabled:opacity-50"
      />
    </span>
  )
})
