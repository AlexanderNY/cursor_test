import { useToast } from '@/contexts/toast-context'
import { CheckCircleIcon, XCircleIcon } from '@/components/icons'

const variantStyles = {
  success: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
  error: 'bg-red-500/10 border-red-500/30 text-red-400',
  info: 'bg-primary-500/10 border-primary-500/30 text-primary-400',
} as const

export function ToastContainer() {
  const { toasts, removeToast } = useToast()

  if (toasts.length === 0) return null

  return (
    <div
      className="fixed top-4 right-4 z-[100] flex flex-col gap-2 max-w-md"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-start gap-3 px-4 py-3 rounded-xl border shadow-lg ${variantStyles[toast.variant]}`}
          role="status"
        >
          <span className="flex-shrink-0 mt-0.5">
            {toast.variant === 'success' && <CheckCircleIcon className="h-5 w-5" />}
            {toast.variant === 'error' && <XCircleIcon className="h-5 w-5" />}
            {toast.variant === 'info' && <CheckCircleIcon className="h-5 w-5" />}
          </span>
          <p className="flex-1 text-sm">{toast.message}</p>
          <button
            type="button"
            onClick={() => removeToast(toast.id)}
            className="flex-shrink-0 p-1 rounded hover:opacity-80 focus:outline-none focus-visible:ring-2 focus-visible:ring-current"
            aria-label="Dismiss"
          >
            <span className="sr-only">Dismiss</span>
            <span aria-hidden>×</span>
          </button>
        </div>
      ))}
    </div>
  )
}
