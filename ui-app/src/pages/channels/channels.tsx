import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
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
  const [discDraft, setDiscDraft] = useState<Record<number, string>>({})
  const [titleDraft, setTitleDraft] = useState<Record<number, string>>({})
  const [savingTitleId, setSavingTitleId] = useState<number | null>(null)
  const [filterTitle, setFilterTitle] = useState('')
  const [filterNetwork, setFilterNetwork] = useState<'all' | 'tg' | 'vk'>('all')
  const hasBrands = brands.length > 0

  async function load() {
    setError('')
    try {
      const [list, palette] = await Promise.all([
        smmService.listAllChannels(selectedBrandId ?? undefined),
        smmService.getPalette(),
      ])
      setChannels(list)
      const drafts: Record<number, string> = {}
      const titles: Record<number, string> = {}
      for (const c of list) {
        drafts[c.id] = c.discussion_external_id || ''
        titles[c.id] = c.title || ''
      }
      setDiscDraft(drafts)
      setTitleDraft(titles)
      setLimits({
        max_own_channels: palette.max_own_channels,
        tariff: (palette as { tariff?: string }).tariff,
      })
    } catch (err) {
      setError(getErrorMessage(err))
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
    field: 'publish_enabled' | 'collect_enabled' | 'comments_collect_enabled' | 'alert_enabled',
  ) {
    try {
      if (field === 'alert_enabled' && ch.network !== 'tg') {
        setError('Alerting пока только для Telegram')
        return
      }
      await smmService.updateChannel(ch.brand_id, ch.id, {
        [field]: !ch[field],
      })
      await load()
      await refreshChannels()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function saveDiscussion(ch: ChannelRow) {
    const raw = (discDraft[ch.id] ?? '').trim()
    try {
      await smmService.updateChannel(ch.brand_id, ch.id, {
        discussion_external_id: raw || '',
        comments_collect_enabled: raw ? true : false,
      })
      await load()
      await refreshChannels()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function saveTitle(ch: ChannelRow) {
    const next = (titleDraft[ch.id] ?? '').trim() || ch.external_id
    if (next === (ch.title || '')) return
    setSavingTitleId(ch.id)
    setError('')
    try {
      await smmService.updateChannel(ch.brand_id, ch.id, { title: next })
      await load()
      await refreshChannels()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSavingTitleId(null)
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

  return (
    <PageContainer>
      <PageHeader
        title="Channels"
        description="Единый хаб каналов · Brand → Channels → поток (условия / обработка / alert) → Analytics"
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

          <div className="flex flex-wrap gap-3 mb-4">
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

          <div className="grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle>Add channel</CardTitle>
                <CardDescription>Discovery: подписки VK / channels TG в силосах</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAdd} className="space-y-3">
                  <div>
                    <label className="text-sm text-[var(--text-secondary)]">Brand</label>
                    <select
                      className="w-full mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2"
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
                  <select
                    className="w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2"
                    value={network}
                    onChange={(e) => setNetwork(e.target.value as 'tg' | 'vk')}
                  >
                    <option value="tg">Telegram</option>
                    <option value="vk">VKontakte</option>
                  </select>
                  <Input
                    label="External ID"
                    value={externalId}
                    onChange={(e) => setExternalId(e.target.value)}
                    placeholder="-100… / group id"
                  />
                  <Input label="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
                  <select
                    className="w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2"
                    value={role}
                    onChange={(e) => setRole(e.target.value as ChannelRole)}
                  >
                    <option value="own">own (publish)</option>
                    <option value="source">source (collect)</option>
                    <option value="competitor">competitor (Full)</option>
                  </select>
                  <Button type="submit" disabled={saving || !brandId}>
                    Add
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>All channels</CardTitle>
                <CardDescription>
                  publish / collect / alert · «Настроить» — условия, обработка, alerting
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {filtered.length === 0 && (
                  <p className="text-sm text-[var(--text-muted)]">
                    {channels.length === 0 ? 'Нет каналов — добавьте слева' : 'Нет совпадений по фильтру'}
                  </p>
                )}
                {filtered.map((c) => (
                  <div
                    key={c.id}
                    className="rounded-lg border border-[var(--border-color)] p-3 space-y-2"
                  >
                    <div className="flex flex-wrap items-center gap-3">
                      <span
                        className="h-3 w-3 rounded-full shrink-0"
                        style={{ backgroundColor: c.brand_color || '#64748b' }}
                      />
                      <div className="min-w-0 flex-1 space-y-2">
                        <p className="text-xs text-[var(--text-muted)]">
                          <span className="uppercase mr-2">{c.network}</span>
                          {c.brand_name} · {c.role} · {c.external_id}
                        </p>
                        <div className="flex flex-wrap items-end gap-2">
                          <div className="flex-1 min-w-[160px]">
                            <Input
                              label="Title"
                              value={titleDraft[c.id] ?? ''}
                              onChange={(e) =>
                                setTitleDraft((prev) => ({ ...prev, [c.id]: e.target.value }))
                              }
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  e.preventDefault()
                                  void saveTitle(c)
                                }
                              }}
                              placeholder={c.external_id}
                            />
                          </div>
                          <Button
                            size="sm"
                            variant="secondary"
                            disabled={
                              savingTitleId === c.id ||
                              (titleDraft[c.id] ?? '').trim() === (c.title || '')
                            }
                            onClick={() => void saveTitle(c)}
                          >
                            {savingTitleId === c.id ? 'Saving…' : 'Save title'}
                          </Button>
                        </div>
                      </div>
                      <label className="flex items-center gap-1 text-xs">
                        <input
                          type="checkbox"
                          checked={!!c.publish_enabled}
                          onChange={() => void toggleFlag(c, 'publish_enabled')}
                          disabled={c.role !== 'own'}
                        />
                        publish
                      </label>
                      <label className="flex items-center gap-1 text-xs">
                        <input
                          type="checkbox"
                          checked={!!c.collect_enabled}
                          onChange={() => void toggleFlag(c, 'collect_enabled')}
                        />
                        collect
                      </label>
                      <label
                        className="flex items-center gap-1 text-xs"
                        title={c.network !== 'tg' ? 'Alerting пока только для Telegram' : undefined}
                      >
                        <input
                          type="checkbox"
                          checked={!!c.alert_enabled}
                          onChange={() => void toggleFlag(c, 'alert_enabled')}
                          disabled={c.network !== 'tg'}
                        />
                        alert
                      </label>
                      <Link to={`/channels/${c.id}`}>
                        <Button size="sm" variant="secondary">
                          Настроить
                        </Button>
                      </Link>
                      <Link
                        to={`/analytics?brand_id=${c.brand_id}&channel_id=${c.id}`}
                        className="text-xs text-primary-400 hover:underline"
                      >
                        Analytics
                      </Link>
                      <Button size="sm" variant="ghost" onClick={() => void remove(c)}>
                        Remove
                      </Button>
                    </div>
                    {c.network === 'tg' && c.role === 'own' && (
                      <div className="flex flex-wrap items-end gap-2 pl-6">
                        <div className="flex-1 min-w-[180px]">
                          <Input
                            label="Discussion chat id"
                            value={discDraft[c.id] ?? ''}
                            onChange={(e) =>
                              setDiscDraft((prev) => ({ ...prev, [c.id]: e.target.value }))
                            }
                            placeholder="-100… (группа комментариев)"
                          />
                        </div>
                        <label className="flex items-center gap-1 text-xs pb-2">
                          <input
                            type="checkbox"
                            checked={!!c.comments_collect_enabled}
                            onChange={() => void toggleFlag(c, 'comments_collect_enabled')}
                            disabled={
                              !c.discussion_external_id && !(discDraft[c.id] || '').trim()
                            }
                          />
                          comments
                        </label>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => void saveDiscussion(c)}
                        >
                          Save discussion
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </PageContainer>
  )
}
