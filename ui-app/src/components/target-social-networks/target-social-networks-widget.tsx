import type { TargetSocialNetworkKey, TargetSocialNetworks } from './types'
import { TARGET_SOCIAL_LABELS, TARGET_SOCIAL_NETWORK_ORDER } from './types'

export interface TargetSocialNetworksWidgetProps {
  value: TargetSocialNetworks
  onChange: (next: TargetSocialNetworks) => void
  /** Отключить отдельные пункты (например только чтение) */
  disabled?: Partial<Record<TargetSocialNetworkKey, boolean>>
  className?: string
}

export function TargetSocialNetworksWidget({
  value,
  onChange,
  disabled = {},
  className = '',
}: TargetSocialNetworksWidgetProps) {
  function toggle(key: TargetSocialNetworkKey) {
    if (disabled[key]) return
    onChange({ ...value, [key]: !value[key] })
  }

  return (
    <div className={className}>
      <span className="text-sm font-medium text-[var(--text-secondary)] block mb-3">
        Target Social Networks
      </span>
      <div className="flex flex-wrap gap-x-6 gap-y-3">
        {TARGET_SOCIAL_NETWORK_ORDER.map((key) => (
          <label
            key={key}
            className={`flex items-center gap-2 ${disabled[key] ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
          >
            <input
              type="checkbox"
              checked={value[key]}
              disabled={disabled[key]}
              onChange={() => toggle(key)}
              className="w-4 h-4 rounded border-[var(--border-color)] text-primary-500 focus:ring-primary-500/50"
            />
            <span className="text-sm text-[var(--text-primary)]">{TARGET_SOCIAL_LABELS[key]}</span>
          </label>
        ))}
      </div>
    </div>
  )
}
