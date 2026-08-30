import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import type { AnalyticsOverview, AnalyticsPost, BrandChannel } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'
import { formatDateTime } from '@/utils/date'
import { PlanGate } from '@/components/billing/PlanGate'
import { TelegramAnalyticsPanel } from './telegram-analytics'

type Tab = 'overview' | 'channels' | 'messages' | 'competitors' | 'telegram'

export function SmmAnalyticsPage() {
  const { selectedBrandId, setSelectedBrandId, channels, refreshChannels } = useBrand()
  const [searchParams, setSearchParams] = useSearchParams()
  const [tab, setTab] = useState<Tab>('overview')
  const [period, setPeriod] = useState('7d')
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null)
  const [posts, setPosts] = useState<AnalyticsPost[]>([])
  const [channelStats, setChannelStats] = useState<
    {
      channel_id: number
      network: string
      external_id: string
      title?: string
      sent: number
      received: number
      failed: number
      alerts_sent?: number
      conversion_pct?: number
      role?: string
    }[]
  >([])
  const [messageEvents, setMessageEvents] = useState<
    { id: string; direction: string; network: string; created_at?: string; channel_title?: string; text?: string }[]
  >([])
  const [growthPoints, setGrowthPoints] = useState<{ date: string; subscribers: number }[]>([])
  const [error, setError] = useState('')
  const [compNetwork, setCompNetwork] = useState<'tg' | 'vk' | 'url'>('tg')
  const [compId, setCompId] = useState('')
  const [compTitle, setCompTitle] = useState('')
  const [compPosts, setCompPosts] = useState<
    { id?: number; text?: string; posted_at?: string; collected_at?: string }[]
  >([])
  const [selectedComp, setSelectedComp] = useState<BrandChannel | null>(null)
  const [canCompetitors, setCanCompetitors] = useState(true)

  const focusChannelId = useMemo(() => {
    const raw = searchParams.get('channel_id')
    if (!raw) return null
    const n = Number(raw)
    return Number.isFinite(n) && n > 0 ? n : null
  }, [searchParams])

  const focusChannel = useMemo(
    () => channels.find((c) => c.id === focusChannelId) || null,
    [channels, focusChannelId],
  )

  const filterChannels = useMemo(() => {
    const list = channels.filter((c) => c.role !== 'competitor')
    if (focusChannel && !list.some((c) => c.id === focusChannel.id)) {
      return [focusChannel, ...list]
    }
    return list
  }, [channels, focusChannel])

  function setChannelFilter(id: number | null) {
    const next = new URLSearchParams(searchParams)
    if (id) next.set('channel_id', String(id))
    else next.delete('channel_id')
    if (selectedBrandId) next.set('brand_id', String(selectedBrandId))
    setSearchParams(next, { replace: true })
  }

  useEffect(() => {
    const tabParam = searchParams.get('tab')
    if (tabParam === 'telegram' || tabParam === 'overview' || tabParam === 'channels' || tabParam === 'messages' || tabParam === 'competitors') {
      setTab(tabParam)
    }
  }, [searchParams])

  useEffect(() => {
    const brandRaw = searchParams.get('brand_id')
    if (!brandRaw) return
    const brandId = Number(brandRaw)
    if (Number.isFinite(brandId) && brandId > 0 && brandId !== selectedBrandId) {
      setSelectedBrandId(brandId)
    }
  }, [searchParams, selectedBrandId, setSelectedBrandId])

  useEffect(() => {
    if (!focusChannelId || channels.length === 0) return
    if (channels.some((c) => c.id === focusChannelId)) return
    const next = new URLSearchParams(searchParams)
    next.delete('channel_id')
    setSearchParams(next, { replace: true })
  }, [channels, focusChannelId, searchParams, setSearchParams])

  const competitors = channels.filter((c) => c.role === 'competitor')

  const visibleChannelStats = useMemo(() => {
    if (!focusChannelId) return channelStats
    return channelStats.filter((s) => s.channel_id === focusChannelId)
  }, [channelStats, focusChannelId])

  useEffect(() => {
    if (tab === 'telegram') return
    void (async () => {
      setError('')
      try {
        const plan = await smmService.getPlan().catch(() => null)
        const feats = (plan?.limits?.features || {}) as Record<string, boolean>
        setCanCompetitors(Boolean(feats.competitors))
        const [ov, list, stats, messagesData, growth] = await Promise.all([
          smmService.analyticsOverview(selectedBrandId, period, focusChannelId),
          smmService.analyticsPosts(selectedBrandId, 'er', focusChannelId),
          smmService.channelStats(selectedBrandId, period).catch(() => ({ channels: [] })),
          smmService.analyticsMessages(selectedBrandId, period, focusChannelId).catch(() => ({
            posts: [],
            events: [],
          })),
          smmService.analyticsGrowth(selectedBrandId).catch(() => ({ points: [], subscriber_growth: 0 })),
        ])
        setOverview(ov)
        setPosts(list)
        setChannelStats(stats.channels ?? [])
        setMessageEvents(messagesData.events ?? [])
        setGrowthPoints(growth.points ?? [])
      } catch (err) {
        setError(getErrorMessage(err))
      }
    })()
  }, [selectedBrandId, period, tab, focusChannelId])

  async function handleAddCompetitor() {
    if (!selectedBrandId) return
    const isUrl = compNetwork === 'url'
    if (!isUrl && !compId.trim()) return
    if (isUrl && !compId.trim()) return
    try {
      await smmService.addCompetitor({
        brand_id: selectedBrandId,
        network: compNetwork,
        external_id: isUrl ? undefined : compId.trim(),
        url: isUrl ? compId.trim() : undefined,
        title: compTitle.trim() || compId.trim(),
        alert_enabled: true,
      })
      setCompId('')
      setCompTitle('')
      await refreshChannels()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function loadCompPosts(ch: BrandChannel) {
    setSelectedComp(ch)
    try {
      setCompPosts(await smmService.competitorPosts(ch.id))
    } catch (err) {
      setError(getErrorMessage(err))
      setCompPosts([])
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Analytics"
        description="Сквозная сводка охватов, ER, конкуренты и аналитика по сетям"
      />
      {error && <Alert variant="error">{error}</Alert>}
      {focusChannel && (
        <Alert variant="info">
          Фильтр по каналу: <strong>{focusChannel.title || focusChannel.external_id}</strong>
          {' · '}
          <button type="button" className="underline" onClick={() => setChannelFilter(null)}>
            сбросить
          </button>
          {' · '}
          <Link to={`/channels/${focusChannel.id}`} className="underline">
            настроить поток
          </Link>
        </Alert>
      )}

      <div className="flex flex-wrap gap-2 mb-4">
        <Button variant={tab === 'overview' ? 'primary' : 'secondary'} onClick={() => setTab('overview')}>
          Overview
        </Button>
        <Button variant={tab === 'channels' ? 'primary' : 'secondary'} onClick={() => setTab('channels')}>
          Operations
        </Button>
        <Button variant={tab === 'messages' ? 'primary' : 'secondary'} onClick={() => setTab('messages')}>
          Messages
        </Button>
        <Button
          variant={tab === 'competitors' ? 'primary' : 'secondary'}
          onClick={() => setTab('competitors')}
          disabled={!canCompetitors}
          title={!canCompetitors ? 'Competitors require Full plan' : undefined}
        >
          Competitors
        </Button>
        <Button variant={tab === 'telegram' ? 'primary' : 'secondary'} onClick={() => setTab('telegram')}>
          Telegram
        </Button>
        {!canCompetitors && (
          <Link to="/pricing" className="text-sm text-primary-400 hover:underline self-center">
            Upgrade for competitors
          </Link>
        )}
      </div>

      {(tab === 'overview' || tab === 'channels' || tab === 'messages') && (
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <select
            className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
          >
            <option value="7d">7 days</option>
            <option value="30d">30 days</option>
          </select>
          <select
            className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm min-w-[14rem]"
            value={focusChannelId ?? ''}
            onChange={(e) => setChannelFilter(e.target.value ? Number(e.target.value) : null)}
            disabled={filterChannels.length === 0}
          >
            <option value="">All channels</option>
            {filterChannels.map((c) => (
              <option key={c.id} value={c.id}>
                {c.title || c.external_id} · {c.network.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      )}

      {tab === 'telegram' && (
        <TelegramAnalyticsPanel chatIdFilter={focusChannel?.external_id || null} />
      )}

      {tab === 'channels' && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Operations by channel</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[var(--text-muted)] border-b border-[var(--border-color)]">
                    <th className="py-2 pr-2">Channel</th>
                    <th className="py-2 pr-2">Net</th>
                    <th className="py-2 pr-2">Received</th>
                    <th className="py-2 pr-2">Sent</th>
                    <th className="py-2 pr-2">Alerts</th>
                    <th className="py-2 pr-2">Failed</th>
                    <th className="py-2">Conv. %</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleChannelStats.map((c) => (
                    <tr
                      key={c.channel_id}
                      className={`border-b border-[var(--border-color)] cursor-pointer ${
                        focusChannelId === c.channel_id ? 'bg-[var(--bg-tertiary)]' : 'hover:bg-[var(--bg-tertiary)]/50'
                      }`}
                      onClick={() =>
                        setChannelFilter(focusChannelId === c.channel_id ? null : c.channel_id)
                      }
                    >
                      <td className="py-2 pr-2">{c.title || c.external_id}</td>
                      <td className="py-2 pr-2 uppercase">{c.network}</td>
                      <td className="py-2 pr-2">{c.received}</td>
                      <td className="py-2 pr-2">{c.sent}</td>
                      <td className="py-2 pr-2">{c.alerts_sent ?? 0}</td>
                      <td className="py-2 pr-2">{c.failed}</td>
                      <td className="py-2">
                        <span>{c.conversion_pct ?? 0}%</span>
                        {' · '}
                        <Link
                          to={`/analytics?channel_id=${c.channel_id}${selectedBrandId ? `&brand_id=${selectedBrandId}` : ''}`}
                          className="text-primary-400 hover:underline text-xs"
                          onClick={(e) => e.stopPropagation()}
                        >
                          details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {visibleChannelStats.length === 0 && (
                <p className="text-sm text-[var(--text-muted)] py-4">Нет данных за период</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {tab === 'messages' && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Messages & events</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h4 className="text-sm font-medium mb-2">Recent events</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[var(--text-muted)] border-b border-[var(--border-color)]">
                      <th className="py-2 pr-2">When</th>
                      <th className="py-2 pr-2">Type</th>
                      <th className="py-2 pr-2">Net</th>
                      <th className="py-2 pr-2">Channel</th>
                      <th className="py-2">Preview</th>
                    </tr>
                  </thead>
                  <tbody>
                    {messageEvents.map((ev) => (
                      <tr key={ev.id} className="border-b border-[var(--border-color)]">
                        <td className="py-2 pr-2 whitespace-nowrap">
                          {ev.created_at ? formatDateTime(ev.created_at) : '—'}
                        </td>
                        <td className="py-2 pr-2">{ev.direction}</td>
                        <td className="py-2 pr-2 uppercase">{ev.network}</td>
                        <td className="py-2 pr-2">{ev.channel_title || '—'}</td>
                        <td className="py-2 text-[var(--text-muted)]">{ev.text || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {messageEvents.length === 0 && (
                  <p className="text-sm text-[var(--text-muted)] py-4">Нет событий за период</p>
                )}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium mb-2">Posts (engagement)</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[var(--text-muted)] border-b border-[var(--border-color)]">
                      <th className="py-2 pr-2">Net</th>
                      <th className="py-2 pr-2">Channel</th>
                      <th className="py-2 pr-2">Published</th>
                      <th className="py-2 pr-2">Views</th>
                      <th className="py-2 pr-2">Likes</th>
                      <th className="py-2 pr-2">Post</th>
                      <th className="py-2">ER</th>
                    </tr>
                  </thead>
                  <tbody>
                    {posts.map((p) => (
                      <tr key={`${p.network}-${p.id}`} className="border-b border-[var(--border-color)]">
                        <td className="py-2 pr-2 uppercase">{p.network}</td>
                        <td className="py-2 pr-2">{p.channel_title || p.channel_external_id || '—'}</td>
                        <td className="py-2 pr-2 whitespace-nowrap">
                          {p.published_at ? formatDateTime(p.published_at) : '—'}
                        </td>
                        <td className="py-2 pr-2">{p.views}</td>
                        <td className="py-2 pr-2">{p.likes}</td>
                        <td className="py-2 pr-2 max-w-xs truncate">{p.text}</td>
                        <td className="py-2">{p.er}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {tab === 'overview' && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5 mb-6">
            {[
              ['Reach', overview?.reach],
              ['Engagement', overview?.engagement],
              ['ER %', overview?.er],
              ['Posts', overview?.posts],
              ['Subscribers Δ', overview?.subscriber_growth],
            ].map(([label, value]) => (
              <Card key={String(label)}>
                <CardContent className="p-4">
                  <p className="text-xs text-[var(--text-muted)]">{label}</p>
                  <p className="text-2xl font-semibold">{value ?? '—'}</p>
                </CardContent>
              </Card>
            ))}
          </div>
          {growthPoints.length > 0 && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Subscriber growth</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-[var(--text-muted)] border-b border-[var(--border-color)]">
                        <th className="py-2 pr-2">Date</th>
                        <th className="py-2">Subscribers</th>
                      </tr>
                    </thead>
                    <tbody>
                      {growthPoints.map((p) => (
                        <tr key={p.date} className="border-b border-[var(--border-color)]">
                          <td className="py-2 pr-2">{p.date}</td>
                          <td className="py-2">{p.subscribers}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
          <Card>
            <CardHeader>
              <CardTitle>Best posts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[var(--text-muted)] border-b border-[var(--border-color)]">
                      <th className="py-2 pr-2">Net</th>
                      <th className="py-2 pr-2">Channel ID</th>
                      <th className="py-2 pr-2">Title</th>
                      <th className="py-2 pr-2">Published</th>
                      <th className="py-2 pr-2">Post</th>
                      <th className="py-2">ER</th>
                    </tr>
                  </thead>
                  <tbody>
                    {posts.map((p) => (
                      <tr key={`${p.network}-${p.id}`} className="border-b border-[var(--border-color)] align-top">
                        <td className="py-2 pr-2 uppercase text-[var(--text-muted)]">{p.network}</td>
                        <td className="py-2 pr-2 whitespace-nowrap">
                          {p.channel_id ?? p.channel_external_id ?? '—'}
                        </td>
                        <td className="py-2 pr-2">
                          {p.channel_title || '—'}
                          {p.channel_id && p.channel_external_id ? (
                            <span className="block text-xs text-[var(--text-muted)]">{p.channel_external_id}</span>
                          ) : null}
                        </td>
                        <td className="py-2 pr-2 whitespace-nowrap">
                          {formatDateTime(p.published_at || p.created_at)}
                        </td>
                        <td className="py-2 pr-2 min-w-[12rem] max-w-md">{p.text || '—'}</td>
                        <td className="py-2 whitespace-nowrap text-[var(--text-muted)]">
                          {p.er}% · {p.views} views
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {posts.length === 0 && (
                  <p className="text-sm text-[var(--text-muted)] py-4">Нет данных</p>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {tab === 'competitors' && (
        <PlanGate allowed={canCompetitors} featureLabel="Competitors">
        <div className="space-y-3">
          <Alert variant="info">
            Полноценный мониторинг конкурентов — в разделе{' '}
            <Link to="/competitors" className="underline">
              Competitors
            </Link>
            : дайджесты, compare и алерты.
          </Alert>
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Добавить конкурента</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {!selectedBrandId && (
                <Alert variant="error">Сначала выберите бренд</Alert>
              )}
              <div className="grid gap-2 sm:grid-cols-2">
                <select
                  className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2"
                  value={compNetwork}
                  onChange={(e) => setCompNetwork(e.target.value as 'tg' | 'vk' | 'url')}
                >
                  <option value="tg">Telegram</option>
                  <option value="vk">VKontakte</option>
                  <option value="url">URL / RSS</option>
                </select>
                <Input
                  value={compId}
                  onChange={(e) => setCompId(e.target.value)}
                  placeholder={compNetwork === 'url' ? 'https://…' : 'External ID'}
                />
                <Input value={compTitle} onChange={(e) => setCompTitle(e.target.value)} placeholder="Title" />
                <Button onClick={() => void handleAddCompetitor()} disabled={!selectedBrandId}>
                  Add
                </Button>
              </div>
              <ul className="space-y-2">
                {competitors.map((c) => (
                  <li key={c.id}>
                    <button
                      type="button"
                      className="w-full text-left rounded border border-[var(--border-color)] px-3 py-2 text-sm hover:bg-[var(--bg-tertiary)]"
                      onClick={() => void loadCompPosts(c)}
                    >
                      <span className="uppercase text-[var(--text-muted)] mr-2">{c.network}</span>
                      {c.title || c.external_id}
                    </button>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>
                Posts {selectedComp ? `· ${selectedComp.title || selectedComp.external_id}` : ''}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {compPosts.length === 0 && (
                <p className="text-sm text-[var(--text-muted)]">
                  Снимки появятся после сбора коллектором
                </p>
              )}
              <ul className="space-y-2 max-h-96 overflow-auto text-sm">
                {compPosts.map((p, i) => (
                  <li key={p.id ?? i} className="border-b border-[var(--border-color)] pb-2">
                    <span className="text-xs text-[var(--text-muted)]">
                      {formatDateTime(p.posted_at || p.collected_at)}
                    </span>
                    <p className="line-clamp-4">{p.text || '—'}</p>
                  </li>
                ))}
              </ul>
              <Link to="/competitors" className="inline-block mt-3 text-sm text-primary-400 hover:underline">
                Open Competitors →
              </Link>
            </CardContent>
          </Card>
        </div>
        </div>
        </PlanGate>
      )}
    </PageContainer>
  )
}
