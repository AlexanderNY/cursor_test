import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { DataTable, type DataTableColumn } from '@/components/ui/data-table'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import type { BrandChannel, ChannelRole } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'

type ChannelRow = BrandChannel & { brand_name?: string; brand_color?: string }

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
  const hasBrands = brands.length > 0

  async function load() {
    setError('')
    setLoadingList(true)
    try {
      const [list, palette] = await Promise.all([
        smmService.listAllChannels(selectedBrandId ?? undefined),
        smmService.getPalette(),
      ])
      setChannels(list)
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
    if (!brandId || !externalId.trim()) return
    setSaving(true)
    setError('')
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

  async function toggleFlag(
    ch: ChannelRow,
    field: 'publish_enabled' | 'collect_enabled' | 'alert_enabled',
  ) {
    try {
      if (field === 'alert_enabled' && ch.network !== 'tg') {
        setError('Alerting пока только для Telegram')
        return
      }
      const next = !ch[field]
      if (field === 'alert_enabled' && next) {
        const hasKeywords = (ch.alert_rules || []).some((r) =>
          (r.save_conditions || []).some((c) => String(c).trim()),
        )
        const delivery = ch.alert_delivery || {}
        const hasTargets =
          Boolean((delivery.alert_targets || []).length) ||
          Boolean((delivery.channel_to_post || '').trim())
        const hasText = Boolean((delivery.alert_text || '').trim())
        if (!hasKeywords || !hasTargets || !hasText) {
          setError(
            'Сначала откройте «Настроить» → Алерты: ключевые слова, куда слать и текст уведомления',
          )
          return
        }
      }
      await smmService.updateChannel(ch.brand_id, ch.id, {
        [field]: next,
      })
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
        key: 'publish_enabled',
        header: 'Publish',
        render: (_v, row) => (
          <input
            type="checkbox"
            checked={!!row.publish_enabled}
            disabled={row.role !== 'own'}
            onChange={() => void toggleFlag(row, 'publish_enabled')}
            aria-label="publish"
          />
        ),
      },
      {
        key: 'collect_enabled',
        header: 'Collect',
        render: (_v, row) => (
          <input
            type="checkbox"
            checked={!!row.collect_enabled}
            onChange={() => void toggleFlag(row, 'collect_enabled')}
            aria-label="collect"
          />
        ),
      },
      {
        key: 'alert_enabled',
        header: 'Alert',
        render: (_v, row) => (
          <input
            type="checkbox"
            checked={!!row.alert_enabled}
            disabled={row.network !== 'tg'}
            title={row.network !== 'tg' ? 'Alerting пока только для Telegram' : undefined}
            onChange={() => void toggleFlag(row, 'alert_enabled')}
            aria-label="alert"
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
    // toggleFlag/remove close over latest load — intentional recreate on channels change
    [channels],
  )

  return (
    <PageContainer>
      <PageHeader
        title="Channels"
        description="Единый хаб каналов · Brand → Channels → поток → Analytics"
      />
      {error && <Alert variant="error">{error}</Alert>}

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
                Collect/Alert {hasCollectOrAlert ? '✓' : '· включите флаг'}
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
                  Add
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
