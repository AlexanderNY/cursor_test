import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PageContainer, PageHeader, Select } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { useBrand } from '@/contexts/brand-context'
import { useAuth } from '@/contexts/auth-context'
import { smmService } from '@/services/smm-service'
import { telegramService } from '@/services/telegram-service'
import type {
  AnalyticsCohort,
  AnalyticsCommentsSummary,
  AnalyticsFunnel,
  AnalyticsInsight,
  AnalyticsOverview,
  AnalyticsPost,
  AnalyticsTrendPoint,
  BestTimeSlot,
  BrandChannel,
  ChannelOpsStat,
  ChannelStatsResponse,
  PipelineCounts,
} from '@/types/smm'
import { canViewTeamAnalytics } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'
import { formatDateTime } from '@/utils/date'
import { networkLabel } from '@/lib/smm-networks'
import { PlanGate } from '@/components/billing/PlanGate'
import { TelegramAnalyticsPanel } from './telegram-analytics'
import {
  AnalyticsChartsSection,
  BestTimesHeatmap,
  CommentsVolumeChart,
} from './components/analytics-charts'
import { PostDetailDrawer } from './components/post-detail-drawer'

const EMPTY_PIPELINE: PipelineCounts = {
  collected: 0,
  processed: 0,
  sent: 0,
  failed: 0,
  alerts_sent: 0,
}

const EMPTY_CHANNEL_STATS: ChannelStatsResponse = {
  period: '7d',
  totals: EMPTY_PIPELINE,
  by_network: [],
  by_brand: [],
  channels: [],
}

function formatCount(value: number | null | undefined): string {
  if (value == null) return '—'
  return value.toLocaleString('ru-RU')
}

type Tab = 'overview' | 'channels' | 'messages' | 'competitors' | 'telegram'

export function SmmAnalyticsPage() {
  const { user } = useAuth()
  const hasTeam = Boolean(user?.group_id || user?.role_in_group)
  const canView = canViewTeamAnalytics(user?.role_in_group, hasTeam, user?.role)
  const { selectedBrandId, setSelectedBrandId, selectedBrand, channels, refreshChannels, brands } = useBrand()
  const [searchParams, setSearchParams] = useSearchParams()
  const [tab, setTab] = useState<Tab>('overview')
  const [period, setPeriod] = useState('7d')
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null)
  const [compareOverview, setCompareOverview] = useState<AnalyticsOverview | null>(null)
  const [posts, setPosts] = useState<AnalyticsPost[]>([])
  const [pipeline, setPipeline] = useState<ChannelStatsResponse>(EMPTY_CHANNEL_STATS)
  const [messageEvents, setMessageEvents] = useState<
    { id: string; direction: string; network: string; created_at?: string; channel_title?: string; text?: string }[]
  >([])
  const [growthPoints, setGrowthPoints] = useState<{ date: string; subscribers: number }[]>([])
  const [trendPoints, setTrendPoints] = useState<AnalyticsTrendPoint[]>([])
  const [funnel, setFunnel] = useState<AnalyticsFunnel | null>(null)
  const [cohort, setCohort] = useState<AnalyticsCohort | null>(null)
  const [commentsSummary, setCommentsSummary] = useState<AnalyticsCommentsSummary | null>(null)
  const [insights, setInsights] = useState<AnalyticsInsight[]>([])
  const [bestSlots, setBestSlots] = useState<BestTimeSlot[]>([])
  const [canBestTimes, setCanBestTimes] = useState(false)
  const [canChannelStats, setCanChannelStats] = useState(true)
  const [channelStatsBlocked, setChannelStatsBlocked] = useState(false)
  const [comparePrev, setComparePrev] = useState(false)
  const [compareBrandId, setCompareBrandId] = useState<number | null>(null)
  const [drillPost, setDrillPost] = useState<AnalyticsPost | null>(null)
  const [error, setError] = useState('')
  const [compNetwork, setCompNetwork] = useState<'tg' | 'vk' | 'url'>('tg')
  const [compId, setCompId] = useState('')
  const [compTitle, setCompTitle] = useState('')
  const [compPosts, setCompPosts] = useState<
    { id?: number; text?: string | null; posted_at?: string | null; collected_at?: string | null }[]
  >([])
  const [selectedComp, setSelectedComp] = useState<BrandChannel | null>(null)
  const [canCompetitors, setCanCompetitors] = useState(true)
  const [canTgListening, setCanTgListening] = useState(true)
  const [tgListening, setTgListening] = useState<{
    messages_collected?: number
    alerts_sent?: number
    alerts_suppressed?: number
    health?: { alert_sent?: number; alert_suppressed?: number; digests?: number; suppression_rate?: number }
  } | null>(null)

  const focusChannelId = useMemo(() => {
    const raw = searchParams.get('channel_id')
    if (!raw) return null
    const n = Number(raw)
    return Number.isFinite(n) && n > 0 ? n : null
  }, [searchParams])

  const focusChannel = useMemo(() => {
    const fromBrand = channels.find((c) => c.id === focusChannelId)
    if (fromBrand) return fromBrand
    const fromStats = pipeline.channels.find((c) => c.channel_id === focusChannelId)
    if (!fromStats) return null
    return {
      id: fromStats.channel_id,
      title: fromStats.title,
      external_id: fromStats.external_id,
      network: fromStats.network,
      brand_name: fromStats.brand_name,
    }
  }, [channels, focusChannelId, pipeline.channels])

  const focusNetwork = useMemo(() => {
    const raw = (searchParams.get('network') || '').trim().toLowerCase()
    return raw || null
  }, [searchParams])

  const filterChannels = useMemo(() => {
    const byId = new Map<
      number,
      { id: number; title?: string | null; external_id: string; network: string; brand_name?: string | null }
    >()
    for (const s of pipeline.channels) {
      byId.set(s.channel_id, {
        id: s.channel_id,
        title: s.title,
        external_id: s.external_id,
        network: s.network,
        brand_name: s.brand_name,
      })
    }
    for (const c of channels) {
      if (c.role === 'competitor') continue
      byId.set(c.id, {
        id: c.id,
        title: c.title,
        external_id: c.external_id,
        network: c.network,
        brand_name: c.brand_name,
      })
    }
    if (focusChannel && !byId.has(focusChannel.id)) {
      byId.set(focusChannel.id, {
        id: focusChannel.id,
        title: focusChannel.title,
        external_id: focusChannel.external_id,
        network: focusChannel.network,
        brand_name: focusChannel.brand_name,
      })
    }
    let list = [...byId.values()]
    if (focusNetwork) list = list.filter((c) => c.network === focusNetwork)
    return list.sort((a, b) => (a.title || a.external_id).localeCompare(b.title || b.external_id))
  }, [channels, focusChannel, focusNetwork, pipeline.channels])

  const networkOptions = useMemo(() => {
    const nets = new Set<string>()
    for (const row of pipeline.by_network) {
      if (row.network) nets.add(row.network)
    }
    for (const c of pipeline.channels) {
      if (c.network) nets.add(c.network)
    }
    return [...nets].sort()
  }, [pipeline.by_network, pipeline.channels])

  function patchSearch(updates: Record<string, string | null>) {
    const next = new URLSearchParams(searchParams)
    for (const [key, value] of Object.entries(updates)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    if (selectedBrandId) next.set('brand_id', String(selectedBrandId))
    else next.delete('brand_id')
    setSearchParams(next, { replace: true })
  }

  function setChannelFilter(id: number | null) {
    patchSearch({ channel_id: id ? String(id) : null })
  }

  function setNetworkFilter(network: string | null) {
    patchSearch({
      network,
      channel_id: null,
    })
  }

  useEffect(() => {
    const tabParam = searchParams.get('tab')
    if (tabParam === 'telegram' || tabParam === 'overview' || tabParam === 'channels' || tabParam === 'messages' || tabParam === 'competitors') {
      setTab(tabParam)
    }
    const periodParam = searchParams.get('period')
    if (periodParam === '7d' || periodParam === '30d' || periodParam === '90d') {
      setPeriod(periodParam)
    }
  }, [searchParams])

  const didApplyUrlBrand = useRef(false)
  useEffect(() => {
    if (didApplyUrlBrand.current) return
    didApplyUrlBrand.current = true
    const brandRaw = searchParams.get('brand_id')
    if (!brandRaw) return
    const brandId = Number(brandRaw)
    if (Number.isFinite(brandId) && brandId > 0 && brandId !== selectedBrandId) {
      setSelectedBrandId(brandId)
    }
  }, [searchParams, selectedBrandId, setSelectedBrandId])

  useEffect(() => {
    const current = searchParams.get('brand_id')
    const nextVal = selectedBrandId ? String(selectedBrandId) : null
    if ((current || null) === nextVal) return
    const next = new URLSearchParams(searchParams)
    if (nextVal) next.set('brand_id', nextVal)
    else next.delete('brand_id')
    setSearchParams(next, { replace: true })
  }, [selectedBrandId, searchParams, setSearchParams])

  useEffect(() => {
    if (!focusChannelId || channels.length === 0) return
    if (channels.some((c) => c.id === focusChannelId)) return
    const next = new URLSearchParams(searchParams)
    next.delete('channel_id')
    setSearchParams(next, { replace: true })
  }, [channels, focusChannelId, searchParams, setSearchParams])

  const periodHalfCompare = useMemo(() => {
    if (!comparePrev || trendPoints.length < 4) return null
    const mid = Math.floor(trendPoints.length / 2)
    const first = trendPoints.slice(0, mid)
    const second = trendPoints.slice(mid)
    const sumViews = (ps: AnalyticsTrendPoint[]) => ps.reduce((s, p) => s + (p.views || 0), 0)
    const sumEng = (ps: AnalyticsTrendPoint[]) => ps.reduce((s, p) => s + (p.engagement || 0), 0)
    const er = (ps: AnalyticsTrendPoint[]) => {
      const v = sumViews(ps)
      return v ? Math.round((sumEng(ps) / v) * 10000) / 100 : 0
    }
    return {
      reach: sumViews(first),
      engagement: sumEng(first),
      er: er(first),
      posts: first.reduce((s, p) => s + (p.posts || 0), 0),
      reach2: sumViews(second),
      engagement2: sumEng(second),
      er2: er(second),
    }
  }, [comparePrev, trendPoints])

  const competitors = channels.filter((c) => c.role === 'competitor')

  const visibleChannelStats = useMemo(() => {
    let list = pipeline.channels
    if (focusNetwork) list = list.filter((s) => s.network === focusNetwork)
    if (focusChannelId) list = list.filter((s) => s.channel_id === focusChannelId)
    return list
  }, [pipeline.channels, focusChannelId, focusNetwork])

  const visibleNetworks = useMemo(() => {
    if (!focusNetwork) return pipeline.by_network
    return pipeline.by_network.filter((n) => n.network === focusNetwork)
  }, [pipeline.by_network, focusNetwork])

  const visibleBrands = useMemo(() => {
    if (selectedBrandId) {
      return pipeline.by_brand.filter((b) => b.brand_id === selectedBrandId)
    }
    if (focusChannelId) {
      const row = visibleChannelStats[0]
      if (!row) return []
      return pipeline.by_brand.filter((b) => b.brand_id === row.brand_id)
    }
    return pipeline.by_brand
  }, [pipeline.by_brand, selectedBrandId, focusChannelId, visibleChannelStats])

  const kpi = useMemo((): PipelineCounts => {
    if (focusChannelId) {
      const row = visibleChannelStats[0]
      return {
        collected: row?.collected ?? row?.received ?? 0,
        processed: null,
        sent: row?.sent ?? 0,
        failed: row?.failed ?? 0,
        alerts_sent: row?.alerts_sent ?? 0,
      }
    }
    if (focusNetwork) {
      const row = visibleNetworks[0]
      if (!row) return EMPTY_PIPELINE
      return row
    }
    return pipeline.totals
  }, [focusChannelId, focusNetwork, visibleChannelStats, visibleNetworks, pipeline.totals])

  useEffect(() => {
    if (!canView) return
    void (async () => {
      const plan = await smmService.getPlan().catch(() => null)
      const feats = (plan?.limits?.features || {}) as Record<string, boolean>
      setCanCompetitors(Boolean(feats.competitors))
      setCanBestTimes(Boolean(feats.best_times))
      setCanChannelStats(feats.channel_stats !== false)
      setCanTgListening(feats.tg_listening !== false)
    })()
  }, [canView])

  useEffect(() => {
    if (!canView || tab === 'telegram') return
    void (async () => {
      setError('')
      try {
        const plan = await smmService.getPlan().catch(() => null)
        const feats = (plan?.limits?.features || {}) as Record<string, boolean>
        setCanCompetitors(Boolean(feats.competitors))
        setCanBestTimes(Boolean(feats.best_times))
        setCanChannelStats(feats.channel_stats !== false)
        setCanTgListening(feats.tg_listening !== false)

        let stats: ChannelStatsResponse = { ...EMPTY_CHANNEL_STATS, period }
        setChannelStatsBlocked(false)
        try {
          stats = await smmService.channelStats(selectedBrandId, period)
        } catch (err: unknown) {
          const status = (err as { response?: { status?: number } })?.response?.status
          if (status === 402) setChannelStatsBlocked(true)
          else throw err
        }

        const [
          ov,
          list,
          messagesData,
          growth,
          trends,
          funnelData,
          cohortData,
          commentsData,
          insightsData,
        ] = await Promise.all([
          smmService.analyticsOverview(selectedBrandId, period, focusChannelId),
          smmService.analyticsPosts(selectedBrandId, 'er', focusChannelId),
          smmService.analyticsMessages(selectedBrandId, period, focusChannelId).catch(() => ({
            posts: [],
            events: [],
          })),
          smmService.analyticsGrowth(selectedBrandId, focusChannelId, period).catch(() => ({
            points: [],
            subscriber_growth: 0,
          })),
          smmService.analyticsPostTrends(selectedBrandId, period, focusChannelId).catch(() => ({
            points: [],
          })),
          smmService.analyticsFunnel(selectedBrandId, period, focusChannelId).catch(() => null),
          smmService.analyticsCohort(selectedBrandId, period, focusChannelId).catch(() => null),
          smmService.analyticsComments(selectedBrandId, period, focusChannelId).catch(() => null),
          smmService.analyticsInsights(selectedBrandId, period, focusChannelId).catch(() => ({
            insights: [],
          })),
        ])
        setOverview(ov)
        setPosts(list)
        setPipeline(stats)
        setMessageEvents(messagesData.events ?? [])
        setGrowthPoints(growth.points ?? [])
        setTrendPoints(trends.points ?? [])
        setFunnel(funnelData)
        setCohort(cohortData)
        setCommentsSummary(commentsData)
        setInsights(insightsData.insights ?? [])

        if (feats.best_times) {
          const bt = await smmService.bestTimes(selectedBrandId, focusChannelId).catch(() => ({ slots: [] }))
          setBestSlots(bt.slots ?? [])
        } else {
          setBestSlots([])
        }

        if (compareBrandId && compareBrandId !== selectedBrandId) {
          const other = await smmService
            .analyticsOverview(compareBrandId, period, null)
            .catch(() => null)
          setCompareOverview(other)
        } else {
          setCompareOverview(null)
        }

        // TG Listening SKU strip (ops) — shared period, shown on Overview
        try {
          const tgPeriod = period === '90d' ? '30d' : period
          const [tgOv, tgHealth] = await Promise.all([
            telegramService.getAnalyticsOverview(tgPeriod, focusChannel?.external_id || undefined),
            telegramService.getAnalyticsHealth('24h'),
          ])
          setTgListening({
            messages_collected: tgOv?.messages_collected,
            alerts_sent: tgOv?.alerts_sent,
            alerts_suppressed: tgOv?.alerts_suppressed,
            health: tgHealth,
          })
        } catch {
          setTgListening(null)
        }
      } catch (err) {
        setError(getErrorMessage(err))
      }
    })()
  }, [canView, selectedBrandId, period, tab, focusChannelId, compareBrandId, focusChannel?.external_id])

  async function handleExportCsv() {
    try {
      const blob = await smmService.exportAnalyticsCsv(selectedBrandId, period, focusChannelId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'smm-analytics.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

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

  if (!canView) {
    return (
      <PageContainer>
        <PageHeader title="Analytics" description="Статистика команды" />
        <Alert variant="warning">
          Аналитика доступна только администратору команды.
        </Alert>
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <PageHeader
        title="Analytics"
        description="Engagement (охват/ER) и Telegram Listening (сбор/алерты/health) — общие фильтры периода и канала"
      />
      {error && <Alert variant="error">{error}</Alert>}
      {focusChannel && (
        <Alert variant="info">
          Канал: <strong>{focusChannel.title || focusChannel.external_id}</strong>
          {' · '}
          {networkLabel(focusChannel.network)}
          {focusChannel.brand_name ? ` · ${focusChannel.brand_name}` : ''}
          {' · '}
          <button type="button" className="underline" onClick={() => setChannelFilter(null)}>
            сбросить канал
          </button>
          {' · '}
          <Link to={`/channels/${focusChannel.id}`} className="underline">
            настроить поток
          </Link>
        </Alert>
      )}

      <div className="flex flex-wrap gap-2 mb-4">
        <Button variant={tab === 'overview' ? 'primary' : 'secondary'} onClick={() => setTab('overview')}>
          Engagement
        </Button>
        <Button variant={tab === 'channels' ? 'primary' : 'secondary'} onClick={() => setTab('channels')}>
          Каналы
        </Button>
        <Button variant={tab === 'messages' ? 'primary' : 'secondary'} onClick={() => setTab('messages')}>
          Messages
        </Button>
        <Button
          variant={tab === 'competitors' ? 'primary' : 'secondary'}
          onClick={() => setTab('competitors')}
        >
          Competitors
        </Button>
        <Button variant={tab === 'telegram' ? 'primary' : 'secondary'} onClick={() => setTab('telegram')}>
          TG Listening
        </Button>
        {(tab === 'overview' || tab === 'channels' || tab === 'messages') && (
          <>
            <Button variant="secondary" onClick={() => void handleExportCsv()}>
              Export CSV
            </Button>
            <Button variant="secondary" className="print:hidden" onClick={() => window.print()}>
              Print / PDF
            </Button>
          </>
        )}
      </div>

      {(tab === 'overview' || tab === 'channels' || tab === 'messages' || tab === 'telegram') && (
        <div className="grid gap-2 sm:grid-cols-3 lg:max-w-3xl mb-4">
          <Select
            value={period}
            onChange={(e) => {
              setPeriod(e.target.value)
              patchSearch({ period: e.target.value })
            }}
            aria-label="Период"
          >
            <option value="7d">7 дней</option>
            <option value="30d">30 дней</option>
            <option value="90d">90 дней</option>
          </Select>
          {tab !== 'telegram' ? (
            <Select
              value={focusNetwork ?? ''}
              onChange={(e) => setNetworkFilter(e.target.value || null)}
              aria-label="Соцсеть"
            >
              <option value="">Все соцсети</option>
              {networkOptions.map((net) => (
                <option key={net} value={net}>
                  {networkLabel(net)}
                </option>
              ))}
            </Select>
          ) : (
            <div className="rounded-md border border-[var(--border-color)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-muted)]">
              Telegram ops
            </div>
          )}
          <Select
            value={focusChannelId != null ? String(focusChannelId) : ''}
            onChange={(e) => {
              const id = e.target.value ? Number(e.target.value) : null
              if (!id) {
                setChannelFilter(null)
                return
              }
              const ch = filterChannels.find((c) => c.id === id)
              patchSearch({
                channel_id: String(id),
                network: ch?.network || focusNetwork,
              })
            }}
            disabled={filterChannels.length === 0}
            aria-label="Канал"
          >
            <option value="">Все каналы</option>
            {(tab === 'telegram'
              ? filterChannels.filter((c) => c.network === 'tg')
              : filterChannels
            ).map((c) => (
              <option key={c.id} value={c.id}>
                {c.title || c.external_id} · {networkLabel(c.network)}
                {!selectedBrandId && c.brand_name ? ` · ${c.brand_name}` : ''}
              </option>
            ))}
          </Select>
        </div>
      )}

      {tab === 'telegram' && (
        <PlanGate allowed={canTgListening} featureLabel="Telegram Listening">
          <TelegramAnalyticsPanel
            chatIdFilter={focusChannel?.external_id || null}
            period={period === '90d' ? '30d' : period}
            onPeriodChange={(p) => {
              setPeriod(p)
              patchSearch({ period: p })
            }}
          />
        </PlanGate>
      )}

      {tab === 'channels' && (
        <PlanGate allowed={canChannelStats && !channelStatsBlocked} featureLabel="Channel stats">
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Каналы</CardTitle>
              <CardDescription>
                Собрано / обработано / отправлено по счётчикам канала (brand_id / channel_id на постах).
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PipelineChannelTable
                rows={visibleChannelStats}
                focusChannelId={focusChannelId}
                selectedBrandId={selectedBrandId}
                showBrand={!selectedBrandId}
                onSelectChannel={(id) =>
                  setChannelFilter(focusChannelId === id ? null : id)
                }
              />
            </CardContent>
          </Card>
        </PlanGate>
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
                      <tr
                        key={`${p.network}-${p.id}`}
                        className="border-b border-[var(--border-color)] cursor-pointer hover:bg-[var(--bg-tertiary)]/50"
                        onClick={() => setDrillPost(p)}
                      >
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
          <p className="text-sm text-[var(--text-muted)] -mt-2">
            {selectedBrand ? `Бренд: ${selectedBrand.name}` : 'Все бренды (переключатель в шапке)'}
            {pipeline.days != null ? ` · период ${pipeline.days} дн.` : ''}
            {period === '90d' || period === '30d'
              ? pipeline.days != null &&
                pipeline.days < (period === '90d' ? 90 : 30)
                ? ' (тариф ограничивает глубину статистики)'
                : ''
              : ''}
          </p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-2">
            {[
              ['Собрано', kpi.collected, 'Вычитанные сообщения с каналов'],
              ['Обработано', kpi.processed, 'Посты, прошедшие процессор (по соцсети)'],
              ['Отправлено', kpi.sent, 'Публикации и исходящие'],
              ['Ошибки', kpi.failed, 'Сбои сбора или отправки'],
            ].map(([label, value, hint]) => (
              <Card key={String(label)}>
                <CardContent className="p-4">
                  <p className="text-xs text-[var(--text-muted)]">{label}</p>
                  <p className="text-2xl font-semibold">{formatCount(value as number | null)}</p>
                  <p className="text-xs text-[var(--text-muted)] mt-1">{hint}</p>
                </CardContent>
              </Card>
            ))}
          </div>
          <Alert variant="info">
            Собрано и отправлено — из счётчиков каналов. Обработано берётся из хаба постов по соцсети,
            поэтому в разрезе канала и бренда стоит прочерк.
          </Alert>

          <div className="grid gap-4">
            <Card>
              <CardHeader>
                <CardTitle>По соцсетям</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-[var(--text-muted)] border-b border-[var(--border-color)]">
                        <th className="py-2 pr-2">Сеть</th>
                        <th className="py-2 pr-2">Каналы</th>
                        <th className="py-2 pr-2">Собрано</th>
                        <th className="py-2 pr-2">Обработано</th>
                        <th className="py-2">Отправлено</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visibleNetworks.map((n) => (
                        <tr
                          key={n.network}
                          className={`border-b border-[var(--border-color)] cursor-pointer ${
                            focusNetwork === n.network ? 'bg-[var(--bg-tertiary)]' : 'hover:bg-[var(--bg-tertiary)]/50'
                          }`}
                          onClick={() =>
                            setNetworkFilter(focusNetwork === n.network ? null : n.network)
                          }
                        >
                          <td className="py-2 pr-2">{networkLabel(n.network)}</td>
                          <td className="py-2 pr-2">{n.channels ?? '—'}</td>
                          <td className="py-2 pr-2">{formatCount(n.collected)}</td>
                          <td className="py-2 pr-2">{formatCount(n.processed)}</td>
                          <td className="py-2">{formatCount(n.sent)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {visibleNetworks.length === 0 && (
                    <p className="text-sm text-[var(--text-muted)] py-4">Нет данных за период</p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>По брендам</CardTitle>
                <CardDescription>
                  {selectedBrandId
                    ? 'Сейчас выбран один бренд в шапке — переключите на «All brands», чтобы сравнить все.'
                    : 'Обработано по бренду недоступно: у постов нет brand_id.'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-[var(--text-muted)] border-b border-[var(--border-color)]">
                        <th className="py-2 pr-2">Бренд</th>
                        <th className="py-2 pr-2">Каналы</th>
                        <th className="py-2 pr-2">Собрано</th>
                        <th className="py-2 pr-2">Обработано</th>
                        <th className="py-2">Отправлено</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visibleBrands.map((b) => (
                        <tr key={b.brand_id ?? 'none'} className="border-b border-[var(--border-color)]">
                          <td className="py-2 pr-2">{b.brand_name || '—'}</td>
                          <td className="py-2 pr-2">{b.channels ?? '—'}</td>
                          <td className="py-2 pr-2">{formatCount(b.collected)}</td>
                          <td className="py-2 pr-2">{formatCount(b.processed)}</td>
                          <td className="py-2">{formatCount(b.sent)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {visibleBrands.length === 0 && (
                    <p className="text-sm text-[var(--text-muted)] py-4">Нет данных за период</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          <PlanGate allowed={canChannelStats && !channelStatsBlocked} featureLabel="Channel stats" soft>
          <Card>
            <CardHeader>
              <CardTitle>По каналам</CardTitle>
            </CardHeader>
            <CardContent>
              <PipelineChannelTable
                rows={visibleChannelStats}
                focusChannelId={focusChannelId}
                selectedBrandId={selectedBrandId}
                showBrand={!selectedBrandId}
                onSelectChannel={(id) =>
                  setChannelFilter(focusChannelId === id ? null : id)
                }
              />
            </CardContent>
          </Card>
          </PlanGate>

          <div className="flex flex-wrap gap-3 items-center text-sm mb-2">
            <label className="inline-flex items-center gap-2">
              <input
                type="checkbox"
                checked={comparePrev}
                onChange={(e) => setComparePrev(e.target.checked)}
              />
              Сравнить половины периода (1-я vs 2-я)
            </label>
            {brands.length >= 2 && (
              <Select
                value={compareBrandId != null ? String(compareBrandId) : ''}
                onChange={(e) => setCompareBrandId(e.target.value ? Number(e.target.value) : null)}
                aria-label="Сравнить с брендом"
              >
                <option value="">Без сравнения бренда</option>
                {brands
                  .filter((b) => b.id !== selectedBrandId)
                  .map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
              </Select>
            )}
          </div>

          {insights.length > 0 && (
            <div className="grid gap-2 mb-4">
              {insights.map((ins) => (
                <Alert key={ins.type + ins.title} variant={ins.severity === 'warning' ? 'warning' : 'info'}>
                  <strong>{ins.title}</strong> — {ins.message}
                </Alert>
              ))}
            </div>
          )}

          {tgListening && (
            <PlanGate allowed={canTgListening} featureLabel="Telegram Listening" soft>
              <Card className="mb-4">
                <CardHeader>
                  <CardTitle>Telegram Listening</CardTitle>
                  <CardDescription>
                    Мониторинг конкурентов, алерты и дайджесты ·{' '}
                    <button
                      type="button"
                      className="underline text-primary-400"
                      onClick={() => {
                        setTab('telegram')
                        patchSearch({ tab: 'telegram' })
                      }}
                    >
                      подробнее
                    </button>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 text-sm">
                    <div className="rounded-lg border border-[var(--border-color)] p-3">
                      <p className="text-xs text-[var(--text-muted)]">Collected</p>
                      <p className="text-xl font-semibold">{tgListening.messages_collected ?? 0}</p>
                    </div>
                    <div className="rounded-lg border border-[var(--border-color)] p-3">
                      <p className="text-xs text-[var(--text-muted)]">Alerts sent</p>
                      <p className="text-xl font-semibold">{tgListening.alerts_sent ?? 0}</p>
                    </div>
                    <div className="rounded-lg border border-[var(--border-color)] p-3">
                      <p className="text-xs text-[var(--text-muted)]">Suppressed</p>
                      <p className="text-xl font-semibold">{tgListening.alerts_suppressed ?? 0}</p>
                    </div>
                    <div className="rounded-lg border border-[var(--border-color)] p-3">
                      <p className="text-xs text-[var(--text-muted)]">Health 24h</p>
                      <p className="text-sm font-medium">
                        digests {tgListening.health?.digests ?? 0}
                        {tgListening.health?.suppression_rate != null
                          ? ` · ${(tgListening.health.suppression_rate * 100).toFixed(0)}% suppress`
                          : ''}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </PlanGate>
          )}

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {[
              ['Охват', overview?.reach, compareOverview?.reach, periodHalfCompare?.reach],
              ['Вовлечённость', overview?.engagement, compareOverview?.engagement, periodHalfCompare?.engagement],
              ['ER %', overview?.er, compareOverview?.er, periodHalfCompare?.er],
              ['Посты', overview?.posts, compareOverview?.posts, periodHalfCompare?.posts],
              ['Подписчики Δ', overview?.subscriber_growth, compareOverview?.subscriber_growth, null],
            ].map(([label, value, other, half]) => (
              <Card key={String(label)}>
                <CardContent className="p-4">
                  <p className="text-xs text-[var(--text-muted)]">{label}</p>
                  <p className="text-2xl font-semibold">{value ?? '—'}</p>
                  {compareOverview && (
                    <p className="text-xs text-[var(--text-muted)] mt-1">vs бренд: {other ?? '—'}</p>
                  )}
                  {periodHalfCompare && half != null && (
                    <p className="text-xs text-[var(--text-muted)] mt-1">1-я пол. периода: {half}</p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          <AnalyticsChartsSection
            trendPoints={trendPoints}
            growthPoints={growthPoints}
            funnel={funnel}
            cohort={cohort}
          />

          <div className="grid gap-4 lg:grid-cols-2 mt-4">
            <Card>
              <CardHeader>
                <CardTitle>Комментарии</CardTitle>
                <CardDescription>
                  Всего {commentsSummary?.total ?? 0} · без ответа {commentsSummary?.unanswered ?? 0}
                  {commentsSummary?.median_reply_hours != null
                    ? ` · медиана ответа ${commentsSummary.median_reply_hours} ч`
                    : ''}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <CommentsVolumeChart points={commentsSummary?.by_day || []} />
                {commentsSummary && Object.keys(commentsSummary.by_sentiment || {}).length > 0 && (
                  <p className="text-xs text-[var(--text-muted)] mt-2">
                    Sentiment:{' '}
                    {Object.entries(commentsSummary.by_sentiment)
                      .map(([k, v]) => `${k} ${v}`)
                      .join(' · ')}
                  </p>
                )}
              </CardContent>
            </Card>
            <PlanGate allowed={canBestTimes} featureLabel="Best times" soft>
              <Card>
                <CardHeader>
                  <CardTitle>Best times</CardTitle>
                  <CardDescription>
                    {focusChannelId ? 'Для выбранного канала' : 'По опубликованным TG-постам бренда'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <BestTimesHeatmap slots={bestSlots} />
                </CardContent>
              </Card>
            </PlanGate>
          </div>

          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Лучшие посты</CardTitle>
              <CardDescription>Кликните по строке для истории метрик и комментариев</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[var(--text-muted)] border-b border-[var(--border-color)]">
                      <th className="py-2 pr-2">Сеть</th>
                      <th className="py-2 pr-2">Канал</th>
                      <th className="py-2 pr-2">Опубликован</th>
                      <th className="py-2 pr-2">Views</th>
                      <th className="py-2 pr-2">Пост</th>
                      <th className="py-2">ER</th>
                    </tr>
                  </thead>
                  <tbody>
                    {posts.map((p) => (
                      <tr
                        key={`${p.network}-${p.id}`}
                        className="border-b border-[var(--border-color)] align-top cursor-pointer hover:bg-[var(--bg-tertiary)]/50"
                        onClick={() => setDrillPost(p)}
                      >
                        <td className="py-2 pr-2 uppercase">{p.network}</td>
                        <td className="py-2 pr-2">{p.channel_title || p.channel_external_id || '—'}</td>
                        <td className="py-2 pr-2 whitespace-nowrap">
                          {p.published_at ? formatDateTime(p.published_at) : '—'}
                        </td>
                        <td className="py-2 pr-2">{p.views}</td>
                        <td className="py-2 pr-2 max-w-md truncate">{p.text}</td>
                        <td className="py-2">{p.er}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {posts.length === 0 && (
                  <p className="text-sm text-[var(--text-muted)] py-4">Нет постов с метриками</p>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      <PostDetailDrawer post={drillPost} onClose={() => setDrillPost(null)} />

      {tab === 'competitors' && (
        <PlanGate allowed={canCompetitors} featureLabel="Competitors">
        <div className="space-y-3">
          <Alert variant="info">
            Полноценный мониторинг — в{' '}
            <Link to="/competitors" className="underline">
              Competitors
            </Link>
            : cadence, best time, темы, viral alerts и идеи постов.
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

function PipelineChannelTable({
  rows,
  focusChannelId,
  selectedBrandId,
  showBrand,
  onSelectChannel,
}: {
  rows: ChannelOpsStat[]
  focusChannelId: number | null
  selectedBrandId: number | null
  showBrand: boolean
  onSelectChannel: (id: number) => void
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[var(--text-muted)] border-b border-[var(--border-color)]">
            <th className="py-2 pr-2">Канал</th>
            {showBrand && <th className="py-2 pr-2">Бренд</th>}
            <th className="py-2 pr-2">Сеть</th>
            <th className="py-2 pr-2">Собрано</th>
            <th className="py-2 pr-2">Обработано</th>
            <th className="py-2 pr-2">Отправлено</th>
            <th className="py-2 pr-2">Ошибки</th>
            <th className="py-2">Конв. %</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr
              key={c.channel_id}
              className={`border-b border-[var(--border-color)] cursor-pointer ${
                focusChannelId === c.channel_id ? 'bg-[var(--bg-tertiary)]' : 'hover:bg-[var(--bg-tertiary)]/50'
              }`}
              onClick={() => onSelectChannel(c.channel_id)}
            >
              <td className="py-2 pr-2">{c.title || c.external_id}</td>
              {showBrand && <td className="py-2 pr-2">{c.brand_name || '—'}</td>}
              <td className="py-2 pr-2">{networkLabel(c.network)}</td>
              <td className="py-2 pr-2">{formatCount(c.collected ?? c.received)}</td>
              <td className="py-2 pr-2">{formatCount(c.processed)}</td>
              <td className="py-2 pr-2">{formatCount(c.sent)}</td>
              <td className="py-2 pr-2">{formatCount(c.failed)}</td>
              <td className="py-2">
                <span>{c.conversion_pct ?? 0}%</span>
                {' · '}
                <Link
                  to={`/analytics?channel_id=${c.channel_id}${selectedBrandId ? `&brand_id=${selectedBrandId}` : ''}`}
                  className="text-primary-400 hover:underline text-xs"
                  onClick={(e) => e.stopPropagation()}
                >
                  детали
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && (
        <p className="text-sm text-[var(--text-muted)] py-4">Нет данных за период</p>
      )}
    </div>
  )
}
