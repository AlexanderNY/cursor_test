import { Link } from 'react-router-dom'
import { useBrand } from '@/contexts/brand-context'
import type {
  SelectedBrandChannels,
  TargetSocialNetworkKey,
  TargetSocialNetworks,
} from './types'
import { EMPTY_SELECTED_BRAND_CHANNELS, TARGET_SOCIAL_LABELS, TARGET_SOCIAL_NETWORK_ORDER } from './types'

export interface TargetSocialNetworksWidgetProps {
  value: TargetSocialNetworks
  onChange: (next: TargetSocialNetworks) => void
  /** Выбранные brand-каналы (external_id) для tg/vk */
  selectedChannels?: SelectedBrandChannels
  onSelectedChannelsChange?: (next: SelectedBrandChannels) => void
  /** Отключить отдельные пункты (например только чтение) */
  disabled?: Partial<Record<TargetSocialNetworkKey, boolean>>
  className?: string
}

export function TargetSocialNetworksWidget({
  value,
  onChange,
  selectedChannels = EMPTY_SELECTED_BRAND_CHANNELS,
  onSelectedChannelsChange,
  disabled = {},
  className = '',
}: TargetSocialNetworksWidgetProps) {
  const { selectedBrandId, publishableChannels } = useBrand()

  const tgChannels = publishableChannels.filter((c) => c.network === 'tg')
  const vkChannels = publishableChannels.filter((c) => c.network === 'vk')
  const showChannelPicker = Boolean(onSelectedChannelsChange)

  function toggle(key: TargetSocialNetworkKey) {
    if (disabled[key]) return
    const nextEnabled = !value[key]
    onChange({ ...value, [key]: nextEnabled })
    if (!nextEnabled && onSelectedChannelsChange && (key === 'tg' || key === 'vk')) {
      onSelectedChannelsChange({ ...selectedChannels, [key]: [] })
    }
  }

  function toggleChannel(network: 'tg' | 'vk', externalId: string) {
    if (!onSelectedChannelsChange || disabled[network]) return
    const current = selectedChannels[network]
    const isSelected = current.includes(externalId)
    const nextList = isSelected
      ? current.filter((id) => id !== externalId)
      : [...current, externalId]
    onSelectedChannelsChange({ ...selectedChannels, [network]: nextList })
    if (!isSelected && !value[network]) {
      onChange({ ...value, [network]: true })
    }
  }

  function renderChannelList(network: 'tg' | 'vk', channels: typeof publishableChannels) {
    if (!showChannelPicker || !value[network]) return null

    if (!selectedBrandId) {
      return (
        <p className="mt-2 ml-6 text-xs text-[var(--text-muted)]">
          Выберите Brand в шапке, чтобы указать каналы. Добавить каналы можно в{' '}
          <Link to="/channels" className="text-primary-400 hover:underline">
            Channels
          </Link>
          .
        </p>
      )
    }

    if (channels.length === 0) {
      return (
        <p className="mt-2 ml-6 text-xs text-[var(--text-muted)]">
          Нет own-каналов с publish_enabled — добавьте в{' '}
          <Link to="/channels" className="text-primary-400 hover:underline">
            Channels
          </Link>
          .
        </p>
      )
    }

    return (
      <div className="mt-2 ml-6 space-y-1.5 max-h-40 overflow-y-auto">
        {channels.map((ch) => {
          const id = String(ch.external_id)
          return (
            <label
              key={ch.id}
              className={`flex items-center gap-2 text-sm ${
                disabled[network] ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'
              }`}
            >
              <input
                type="checkbox"
                checked={selectedChannels[network].includes(id)}
                disabled={disabled[network]}
                onChange={() => toggleChannel(network, id)}
                className="w-3.5 h-3.5 rounded border-[var(--border-color)] text-primary-500 focus:ring-primary-500/50"
              />
              <span className="text-[var(--text-primary)]">{ch.title || id}</span>
              <span className="font-mono text-xs text-[var(--text-muted)]">{id}</span>
            </label>
          )
        })}
      </div>
    )
  }

  return (
    <div className={className}>
      <span className="text-sm font-medium text-[var(--text-secondary)] block mb-3">
        Target Social Networks
      </span>
      <div className="flex flex-col gap-y-3">
        {TARGET_SOCIAL_NETWORK_ORDER.map((key) => (
          <div key={key}>
            <label
              className={`flex items-center gap-2 ${
                disabled[key] ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'
              }`}
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
            {key === 'tg' && renderChannelList('tg', tgChannels)}
            {key === 'vk' && renderChannelList('vk', vkChannels)}
          </div>
        ))}
      </div>
    </div>
  )
}
