import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { DataTable, type DataTableColumn } from '@/components/ui/data-table'
import { CheckCircleIcon, XCircleIcon } from '@/components/icons'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import type { BrandChannel, ChannelRole, PlatformStatusResponse } from '@/types/smm'
import { authStatusLabel, publishAllowed } from '@/hooks/use-platform-readiness'
import { getErrorMessage } from '@/services/api-client'

type ChannelRow = BrandChannel & { brand_name?: string; brand_color?: string }

function FlagStatusIcon({
  on,
  label,
  title,
  na = false,
}: {
  on: boolean
  label: string
  title?: string
  na?: boolean
}) {
  if (na) {
    return (
      <span
        className="inline-flex items-center justify-center text-[var(--text-muted)]"
        title={title || `${label}: недоступно`}
        aria-label={`${label}: n/a`}
      >
        <span className="text-xs font-medium tracking-wide">—</span>
      </span>
    )
  }
  return on ? (
    <span
      className="inline-flex text-emerald-400"
      title={title || `${label}: включено`}
      aria-label={`${label}: on`}
    >
      <CheckCircleIcon size={20} />
    </span>
  ) : (
    <span
      className="inline-flex text-[var(--text-muted)] opacity-60"
      title={title || `${label}: выключено`}
      aria-label={`${label}: off`}
    >
      <XCircleIcon size={20} />
    </span>
  )
}

export function ChannelsPage() {
  const {
    brands,
    selectedBrandId,
    setSelectedBrandId,
    refreshChannels,
    refreshBrands,
    isLoading: isLoadingBrands,
  } = useBrand()
  const [channels, setChannels] = useState<ChannelRow[]>([])
  const [error, setError] = useState('')
  const [limits, setLimits] = useState<{ max_own_channels?: number; tariff?: string }>({})
  const [network, setNetwork] = useState<'tg' | 'vk'>('tg')
  const [externalId, setExternalId] = useState('')
  const [title, setTitle] = useState('')
  const [role, setRole] = useState<ChannelRole>('own')
  const [brandId, setBrandId] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)
  const [loadingList, setLoadingList] = useState(false)
  const [filterTitle, setFilterTitle] = useState('')
  const [filterNetwork, setFilterNetwork] = useState<'all' | 'tg' | 'vk'>('all')
  const [platformStatus, setPlatformStatus] = useState<PlatformStatusResponse | null>(null)
  const hasBrands = brands.length > 0

  async function load() {
    setError('')
    setLoadingList(true)
    try {
      const [list, palette, platforms] = await Promise.all([
        smmService.listAllChannels(selectedBrandId ?? undefined),
        smmService.getPalette(),
        smmService.platformStatus().catch(() => null),
      ])
      setChannels(list)
      setPlatformStatus(platforms)
      setLimits({
        max_own_channels: palette.max_own_channels,
        tariff: (palette as { tariff?: string }).tariff,
      })
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoadingList(false)
    }
  }

  useEffect(() => {
    void refreshBrands()
  }, [refreshBrands])

  useEffect(() => {
    if (!hasBrands) {
      setChannels([])
      return
    }
    void load()
  }, [selectedBrandId, hasBrands])

  useEffect(() => {
    if (selectedBrandId) setBrandId(selectedBrandId)
    else if (brands[0]) setBrandId(brands[0].id)
  }, [selectedBrandId, brands])

  const ownCount = channels.filter((c) => c.role === 'own').length
  const hasCollectOrAlert = channels.some((c) => c.collect_enabled || c.alert_enabled)
  const tgOwnPending = channels.filter(
    (c) => c.network === 'tg' && c.role === 'own' && c.auth_status !== 'connected',
  )
  const tgConnected = Boolean(platformStatus?.tg?.connected)

  const filtered = useMemo(() => {
    const q = filterTitle.trim().toLowerCase()
    return channels.filter((c) => {
      if (filterNetwork !== 'all' && c.network !== filterNetwork) return false
      if (!q) return true
      const hay = `${c.title || ''} ${c.external_id} ${c.brand_name || ''}`.toLowerCase()
      return hay.includes(q)
    })
  }, [channels, filterTitle, filterNetwork])

  async function handleAdd(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (!brandId) {
      setError('Выберите бренд')
      return
    }
    if (!externalId.trim()) {
      setError('Укажите ID канала')
      return
    }
    setSaving(true)
    try {
      await smmService.addChannel(brandId, {
        network,
        external_id: externalId.trim(),
        title: title.trim() || externalId.trim(),
        role,
        kind: network === 'vk' ? 'public' : 'channel',
      })
      setExternalId('')
      setTitle('')
      await load()
      await refreshChannels()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function recheckAuth(ch: ChannelRow) {
    try {
      setError('')
      await smmService.recheckChannelAuth(ch.id)
      await load()
      await refreshChannels()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function remove(ch: ChannelRow) {
    try {
      await smmService.deleteChannel(ch.brand_id, ch.id)
      await load()
      await refreshChannels()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const columns: DataTableColumn<ChannelRow>[] = useMemo(
    () => [
      {
        key: 'network',
        header: 'Сеть',
        render: (_v, row) => (
          <span className="font-semibold uppercase tracking-wide text-[var(--text-primary)]">
            {row.network === 'vk' ? 'VK' : 'TG'}
          </span>
        ),
      },
      {
        key: 'external_id',
        header: 'ID канала',
        render: (_v, row) => (
          <code className="text-xs text-[var(--text-primary)] break-all">{row.external_id}</code>
        ),
      },
      {
        key: 'title',
        header: 'Title',
        render: (_v, row) => (
          <div className="min-w-[140px]">
            <div className="text-[var(--text-primary)] font-medium">
              {row.title || '—'}
            </div>
            {row.brand_name && (
              <div className="text-xs text-[var(--text-muted)] flex items-center gap-1.5 mt-0.5">
                <span
                  className="inline-block h-2 w-2 rounded-full shrink-0"
                  style={{ backgroundColor: row.brand_color || '#64748b' }}
                />
                {row.brand_name}
              </div>
            )}
          </div>
        ),
      },
      {
        key: 'role',
        header: 'Тип',
        render: (_v, row) => (
          <span className="text-xs uppercase tracking-wide text-[var(--text-secondary)]">
            {row.role}
          </span>
        ),
      },
      {
        key: 'auth_status',
        header: 'Auth',
        render: (_v, row) => (
          <div className="flex flex-col gap-1 min-w-[5rem]">
            <span
              className={`text-xs font-medium ${
                row.auth_status === 'connected' || row.auth_status === 'not_required'
                  ? 'text-emerald-400'
                  : 'text-amber-400'
              }`}
              title={row.auth_error || undefined}
            >
              {authStatusLabel(row.auth_status)}
            </span>
            {row.role !== 'competitor' && (
              <button
                type="button"
                className="text-xs text-primary-400 hover:underline text-left"
                onClick={() => void recheckAuth(row)}
              >
                Recheck
              </button>
            )}
          </div>
        ),
      },
      {
        key: 'publish_enabled',
        header: 'Publish',
        render: (_v, row) => (
          <FlagStatusIcon
            on={!!row.publish_enabled}
            label="Publish"
            na={row.role !== 'own'}
            title={
              row.role !== 'own'
                ? 'Publish только для own'
                : row.publish_enabled
                  ? publishAllowed(row)
                    ? 'Publish включён в настройках канала'
                    : 'Publish включён, но ownership не подтверждён — Recheck'
                  : 'Publish выключен — включите в «Настроить» → Публикация'
            }
          />
        ),
      },
      {
        key: 'collect_enabled',
        header: 'Collect',
        render: (_v, row) => (
          <FlagStatusIcon
            on={!!row.collect_enabled}
            label="Collect"
            title={
              row.collect_enabled
                ? 'Collect включён в настройках канала'
                : 'Collect выключен — включите в «Настроить» → Сбор'
            }
          />
        ),
      },
      {
        key: 'alert_enabled',
        header: 'Alert',
        render: (_v, row) => (
          <FlagStatusIcon
            on={!!row.alert_enabled}
            label="Alert"
            na={row.network !== 'tg'}
            title={
              row.network !== 'tg'
                ? 'Alerting пока только для Telegram'
                : row.alert_enabled
                  ? 'Alert включён в настройках канала'
                  : 'Alert выключен — включите в «Настроить» → Алерты'
            }
          />
        ),
      },
      {
        key: 'actions',
        header: '',
        render: (_v, row) => (
          <div className="flex items-center gap-2 justify-end whitespace-nowrap">
            <Link to={`/channels/${row.id}`}>
              <Button size="sm" variant="secondary">
                Настроить
              </Button>
            </Link>
            <Button size="sm" variant="ghost" onClick={() => void remove(row)}>
              Remove
            </Button>
          </div>
        ),
      },
    ],
    [channels],
  )

  return (
    <PageContainer>
      <PageHeader
        title="Channels"
        description="Единый хаб каналов · Brand → Channels → поток → Analytics"
      />
      {error && (
        <div className="mb-4" role="alert">
          <Alert variant="error">{error}</Alert>
        </div>
      )}
      {!error && !tgConnected && hasBrands && (
        <Alert variant="info" className="mb-4">
          Для Collect/Publish по Telegram сначала авторизуйтесь:{' '}
          <Link to="/telegram" className="underline font-medium">
            Telegram → Auth
          </Link>
          . После кода вернитесь сюда и нажмите Recheck у канала.
        </Alert>
      )}
      {!error && tgConnected && tgOwnPending.length > 0 && (
        <Alert variant="info" className="mb-4">
          Telegram подключён. Подтвердите собственность: в таблице нажмите{' '}
          <strong>Recheck</strong> у канала
          {tgOwnPending.length === 1
            ? ` «${tgOwnPending[0].title || tgOwnPending[0].external_id}»`
            : ` (${tgOwnPending.length} шт.)`}
          , затем откройте <strong>Настроить</strong> и включите Publish. Collect можно
          настроить уже сейчас.
        </Alert>
      )}
      {!error && tgConnected && tgOwnPending.length === 0 && channels.some((c) => c.network === 'tg' && c.role === 'own') && (
        <Alert variant="success" className="mb-4">
          TG-каналы подтверждены. Флаги Publish / Collect / Alert задаются в{' '}
          <strong>Настроить</strong>. Далее —{' '}
          <Link to="/posts" className="underline">
            Posts
          </Link>
          .
        </Alert>
      )}

      {isLoadingBrands && !hasBrands ? (
        <p className="text-sm text-[var(--text-muted)]">Загрузка брендов…</p>
      ) : !hasBrands ? (
        <Card>
          <CardHeader>
            <CardTitle>Сначала создайте бренд</CardTitle>
            <CardDescription>
              Каналы привязываются к бренду. Без бренда добавлять и управлять каналами нельзя.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link
              to="/brands"
              className="inline-flex items-center text-sm font-medium text-primary-400 hover:underline"
            >
              Перейти в Brands →
            </Link>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card className="mb-4">
            <CardContent className="py-3 flex flex-wrap gap-4 text-sm">
              <span className="text-emerald-400">Brand ✓</span>
              <span className={channels.length ? 'text-emerald-400' : 'text-[var(--text-muted)]'}>
                Channels {channels.length ? '✓' : '· добавьте канал'}
              </span>
              <span className={hasCollectOrAlert ? 'text-emerald-400' : 'text-[var(--text-muted)]'}>
                Collect/Alert {hasCollectOrAlert ? '✓' : '· Настроить → Сбор/Алерты'}
              </span>
              <Link to="/analytics" className="text-primary-400 hover:underline ml-auto">
                Analytics →
              </Link>
            </CardContent>
          </Card>

          <div className="flex flex-wrap gap-3 mb-4 text-sm text-[var(--text-secondary)]">
            <span>
              Own: {ownCount}
              {limits.max_own_channels != null ? ` / ${limits.max_own_channels}` : ''}
            </span>
            {limits.tariff && <span className="uppercase">Plan: {limits.tariff}</span>}
            <Link to="/brands" className="text-primary-400 hover:underline">
              Manage brands →
            </Link>
            <Link to="/telegram" className="text-primary-400 hover:underline">
              Telegram auth →
            </Link>
            <Link to="/vkontakte" className="text-primary-400 hover:underline">
              VK auth →
            </Link>
            <Link to="/inbox" className="text-primary-400 hover:underline">
              Inbox →
            </Link>
          </div>

          <Card className="mb-4">
            <CardHeader>
              <CardTitle>Add channel</CardTitle>
              <CardDescription>Discovery: подписки VK / channels TG в силосах</CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={handleAdd}
                className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6 items-end"
              >
                <div>
                  <label className="text-sm text-[var(--text-secondary)]">Brand</label>
                  <select
                    className="w-full mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                    value={brandId ?? ''}
                    onChange={(e) => {
                      const id = e.target.value ? Number(e.target.value) : null
                      setBrandId(id)
                      if (id) setSelectedBrandId(id)
                    }}
                  >
                    {brands.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-[var(--text-secondary)]">Сеть</label>
                  <select
                    className="w-full mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                    value={network}
                    onChange={(e) => setNetwork(e.target.value as 'tg' | 'vk')}
                  >
                    <option value="tg">Telegram</option>
                    <option value="vk">VKontakte</option>
                  </select>
                </div>
                <Input
                  label="ID канала"
                  value={externalId}
                  onChange={(e) => setExternalId(e.target.value)}
                  placeholder="-100… / group id"
                />
                <Input label="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
                <div>
                  <label className="text-sm text-[var(--text-secondary)]">Тип</label>
                  <select
                    className="w-full mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                    value={role}
                    onChange={(e) => setRole(e.target.value as ChannelRole)}
                  >
                    <option value="own">own</option>
                    <option value="source">source</option>
                    <option value="competitor">competitor</option>
                  </select>
                </div>
                <Button type="submit" disabled={saving || !brandId}>
                  {saving ? 'Adding…' : 'Add'}
                </Button>
              </form>
            </CardContent>
          </Card>

          <div className="flex flex-wrap gap-3 mb-3">
            <div className="min-w-[180px] flex-1">
              <Input
                label="Filter by title"
                value={filterTitle}
                onChange={(e) => setFilterTitle(e.target.value)}
                placeholder="Title / id / brand"
              />
            </div>
            <div>
              <label className="text-sm text-[var(--text-secondary)]">Network</label>
              <select
                className="block mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                value={filterNetwork}
                onChange={(e) => setFilterNetwork(e.target.value as 'all' | 'tg' | 'vk')}
              >
                <option value="all">All</option>
                <option value="tg">Telegram</option>
                <option value="vk">VKontakte</option>
              </select>
            </div>
          </div>

          <DataTable
            columns={columns}
            data={filtered}
            keyExtractor={(row) => row.id}
            isLoading={loadingList}
            emptyMessage={
              channels.length === 0
                ? 'Нет каналов — добавьте выше'
                : 'Нет совпадений по фильтру'
            }
          />
        </>
      )}
    </PageContainer>
  )
}
