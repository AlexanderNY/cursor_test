import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import type { AnalyticsOverview, AnalyticsPost, BrandChannel } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'

type Tab = 'overview' | 'competitors'

export function SmmAnalyticsPage() {
  const { selectedBrandId, channels, refreshChannels } = useBrand()
  const [tab, setTab] = useState<Tab>('overview')
  const [period, setPeriod] = useState('7d')
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null)
  const [posts, setPosts] = useState<AnalyticsPost[]>([])
  const [error, setError] = useState('')
  const [compNetwork, setCompNetwork] = useState<'tg' | 'vk'>('tg')
  const [compId, setCompId] = useState('')
  const [compTitle, setCompTitle] = useState('')
  const [compPosts, setCompPosts] = useState<unknown[]>([])
  const [selectedComp, setSelectedComp] = useState<BrandChannel | null>(null)

  const competitors = channels.filter((c) => c.role === 'competitor')

  useEffect(() => {
    void (async () => {
      setError('')
      try {
        const [ov, list] = await Promise.all([
          smmService.analyticsOverview(selectedBrandId, period),
          smmService.analyticsPosts(selectedBrandId, 'er'),
        ])
        setOverview(ov)
        setPosts(list)
      } catch (err) {
        setError(getErrorMessage(err))
      }
    })()
  }, [selectedBrandId, period])

  async function handleAddCompetitor() {
    if (!selectedBrandId || !compId.trim()) return
    try {
      await smmService.addCompetitor({
        brand_id: selectedBrandId,
        network: compNetwork,
        external_id: compId.trim(),
        title: compTitle.trim() || compId.trim(),
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
        description="Сквозная сводка охватов, ER и конкуренты"
      />
      {error && <Alert variant="error">{error}</Alert>}

      <div className="flex gap-2 mb-4">
        <Button variant={tab === 'overview' ? 'primary' : 'secondary'} onClick={() => setTab('overview')}>
          Overview
        </Button>
        <Button
          variant={tab === 'competitors' ? 'primary' : 'secondary'}
          onClick={() => setTab('competitors')}
        >
          Competitors
        </Button>
        <Link to="/telegram" className="ml-auto text-sm text-primary-400 hover:underline self-center">
          TG deep-dive →
        </Link>
      </div>

      {tab === 'overview' && (
        <>
          <div className="mb-4">
            <select
              className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            >
              <option value="7d">7 days</option>
              <option value="30d">30 days</option>
            </select>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
            {[
              ['Reach', overview?.reach],
              ['Engagement', overview?.engagement],
              ['ER %', overview?.er],
              ['Posts', overview?.posts],
            ].map(([label, value]) => (
              <Card key={String(label)}>
                <CardContent className="p-4">
                  <p className="text-xs text-[var(--text-muted)]">{label}</p>
                  <p className="text-2xl font-semibold">{value ?? '—'}</p>
                </CardContent>
              </Card>
            ))}
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Best posts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {posts.length === 0 && (
                <p className="text-sm text-[var(--text-muted)]">Нет данных</p>
              )}
              {posts.map((p) => (
                <div
                  key={`${p.network}-${p.id}`}
                  className="flex justify-between gap-4 border-b border-[var(--border-color)] py-2 text-sm"
                >
                  <div className="min-w-0">
                    <span className="uppercase text-[var(--text-muted)] mr-2">{p.network}</span>
                    {p.text || '—'}
                  </div>
                  <div className="shrink-0 text-[var(--text-muted)]">
                    ER {p.er}% · {p.views} views
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      )}

      {tab === 'competitors' && (
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
                  onChange={(e) => setCompNetwork(e.target.value as 'tg' | 'vk')}
                >
                  <option value="tg">Telegram</option>
                  <option value="vk">VKontakte</option>
                </select>
                <Input value={compId} onChange={(e) => setCompId(e.target.value)} placeholder="External ID" />
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
              <pre className="text-xs overflow-auto max-h-96">
                {JSON.stringify(compPosts, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </div>
      )}
    </PageContainer>
  )
}
