import { FormEvent, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { Switch } from '@/components/ui/switch'
import { smmService } from '@/services/smm-service'
import type { BrandChannel, ChannelRssFeed } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'
import { parseQuotaError } from '@/lib/quota'
import { formatDateTime } from '@/utils/date'

const MAX_FEEDS = 10

function readFeeds(channel: BrandChannel) {
  const feeds = channel.rss_feeds || []
  return {
    urls: feeds.map((feed) => feed.url),
    enabled: feeds.length === 0 ? true : feeds.every((feed) => feed.enabled !== false),
    intervalMin: feeds[0]?.interval_min || 60,
    suffix: feeds[0]?.suffix || '',
  }
}

type PreviewItem = { id: string; text_preview: string; feed_url: string }

type RssRunResult = {
  created: number
  status: string
  errors: { url?: string; error: string }[]
}

function feedSignature(feeds: ChannelRssFeed[], enabled: boolean, intervalMin: number, suffix: string): string {
  return feeds
    .map((feed) => `${feed.url}|${enabled}|${intervalMin}|${suffix}`)
    .join('\n')
}

export function ChannelRssCard({
  channel,
  onUpdated,
}: {
  channel: BrandChannel
  onUpdated: (channel: BrandChannel) => void
}) {
  const initial = readFeeds(channel)
  const [urls, setUrls] = useState<string[]>(initial.urls)
  const [enabled, setEnabled] = useState(initial.enabled)
  const [intervalMin, setIntervalMin] = useState(initial.intervalMin)
  const [suffix, setSuffix] = useState(initial.suffix)
  const [draft, setDraft] = useState('')
  const [error, setError] = useState('')
  const [upgradeHint, setUpgradeHint] = useState('')
  const [success, setSuccess] = useState('')
  const [saving, setSaving] = useState(false)
  const [busy, setBusy] = useState<'preview' | 'run' | null>(null)
  const [preview, setPreview] = useState<PreviewItem[] | null>(null)
  const [runResult, setRunResult] = useState<RssRunResult | null>(null)
  const [loadedId, setLoadedId] = useState(channel.id)

  if (loadedId !== channel.id) {
    const next = readFeeds(channel)
    setLoadedId(channel.id)
    setUrls(next.urls)
    setEnabled(next.enabled)
    setIntervalMin(next.intervalMin)
    setSuffix(next.suffix)
    setDraft('')
    setPreview(null)
    setRunResult(null)
    setError('')
    setSuccess('')
    setUpgradeHint('')
  }

  function apply(next: BrandChannel) {
    const feeds = readFeeds(next)
    setUrls(feeds.urls)
    setEnabled(feeds.enabled)
    setIntervalMin(feeds.intervalMin)
    setSuffix(feeds.suffix)
    setDraft('')
  }

  const savedSignature = useMemo(() => {
    const saved = readFeeds(channel)
    return feedSignature(channel.rss_feeds || [], saved.enabled, saved.intervalMin, saved.suffix)
  }, [channel])
  const dirty = feedSignature(urls.map((url) => ({ url })), enabled, intervalMin, suffix) !== savedSignature

  function showError(err: unknown) {
    const quota = parseQuotaError(err)
    if (quota) {
      setError(quota.message)
      setUpgradeHint(quota.upgrade_url || '/pricing')
      return
    }
    setUpgradeHint('')
    setError(getErrorMessage(err))
  }

  function addUrl() {
    const url = draft.trim()
    if (!url) return
    if (!/^https?:\/\//i.test(url)) {
      setError('Укажите http(s) URL ленты')
      setUpgradeHint('')
      return
    }
    if (urls.includes(url)) {
      setError('Эта лента уже в списке')
      setUpgradeHint('')
      return
    }
    if (urls.length >= MAX_FEEDS) {
      setError(`Не больше ${MAX_FEEDS} RSS-лент на канал`)
      setUpgradeHint('')
      return
    }
    setUrls((prev) => [...prev, url])
    setDraft('')
    setError('')
    setUpgradeHint('')
  }

  async function save(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError('')
    setUpgradeHint('')
    setSuccess('')
    setPreview(null)
    setRunResult(null)
    try {
      const updated = await smmService.updateChannel(channel.brand_id, channel.id, {
        rss_feeds: urls.map((url) => ({
          url,
          enabled,
          interval_min: intervalMin,
          suffix: suffix.trim(),
        })),
      })
      apply(updated)
      onUpdated(updated)
      setSuccess(urls.length ? 'RSS-ленты сохранены' : 'RSS-ленты очищены')
    } catch (err) {
      showError(err)
    } finally {
      setSaving(false)
    }
  }

  async function showPreview() {
    setBusy('preview')
    setError('')
    setUpgradeHint('')
    setSuccess('')
    setRunResult(null)
    try {
      const res = await smmService.previewChannelRss(channel.id, 5)
      setPreview(res.items)
      if (res.errors?.length) {
        setError(res.errors.map((item) => item.error).join('; '))
      }
    } catch (err) {
      setPreview(null)
      showError(err)
    } finally {
      setBusy(null)
    }
  }

  async function runNow() {
    setBusy('run')
    setError('')
    setUpgradeHint('')
    setSuccess('')
    try {
      const res = await smmService.runChannelRss(channel.id, 10)
      setRunResult({
        created: res.created,
        status: res.status,
        errors: res.errors || [],
      })
      setPreview(null)
      if (res.errors?.length) {
        setError(res.errors.map((item) => item.error).filter(Boolean).join('; '))
      } else {
        setSuccess(
          res.created
            ? `В очередь добавлено ${res.created} (${res.status})`
            : 'Новых записей нет',
        )
      }
      const fresh = await smmService.getChannel(channel.id)
      apply(fresh)
      onUpdated(fresh)
    } catch (err) {
      showError(err)
    } finally {
      setBusy(null)
    }
  }

  const lastRunByUrl = useMemo(() => {
    const map = new Map<string, string>()
    for (const feed of channel.rss_feeds || []) {
      if (feed.last_run_at) map.set(feed.url, feed.last_run_at)
    }
    return map
  }, [channel.rss_feeds])

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>RSS-ленты</CardTitle>
        <CardDescription>
          Новые записи попадают в очередь публикаций этого канала. Планировщик проверяет ленты
          по интервалу. Нужна функция Automations на тарифе.
        </CardDescription>
      </CardHeader>
      <form onSubmit={save}>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="error">
              {error}
              {upgradeHint && (
                <>
                  {' '}
                  <Link to={upgradeHint} className="underline text-primary-400">
                    Тарифы
                  </Link>
                </>
              )}
            </Alert>
          )}
          {success && <Alert variant="success">{success}</Alert>}
          <label className="flex items-center gap-2 text-sm font-medium">
            <Switch checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
            Сбор RSS включён
          </label>
          <div className="flex flex-col sm:flex-row gap-2 sm:items-end">
            <div className="flex-1">
              <Input
                label="URL ленты"
                type="url"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addUrl()
                  }
                }}
                placeholder="https://example.com/rss"
              />
            </div>
            <Button type="button" variant="secondary" className="h-11" onClick={addUrl}>
              Добавить
            </Button>
          </div>
          {urls.length === 0 && (
            <p className="text-sm text-[var(--text-muted)]">Лент пока нет</p>
          )}
          <ul className="space-y-2">
            {urls.map((url) => (
              <li
                key={url}
                className="flex items-start justify-between gap-3 rounded border border-[var(--border-color)] px-3 py-2 text-sm"
              >
                <div className="min-w-0">
                  <p className="break-all text-[var(--text-primary)]">{url}</p>
                  {lastRunByUrl.get(url) && (
                    <p className="text-xs text-[var(--text-muted)] mt-1">
                      Последний сбор: {formatDateTime(lastRunByUrl.get(url))}
                    </p>
                  )}
                </div>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={() => setUrls((prev) => prev.filter((item) => item !== url))}
                >
                  Удалить
                </Button>
              </li>
            ))}
          </ul>
          <div className="grid gap-3 sm:grid-cols-2">
            <Input
              label="Интервал, минут"
              type="number"
              min={15}
              max={1440}
              value={intervalMin}
              onChange={(e) => setIntervalMin(Number(e.target.value) || 60)}
            />
            <Input
              label="Подпись в конце поста"
              value={suffix}
              onChange={(e) => setSuffix(e.target.value)}
              placeholder="#brand"
            />
          </div>
          <p className="text-xs text-[var(--text-muted)]">
            Если канал ещё не подключён, записи сохраняются как черновики. Иначе — в очередь
            согласования, когда она включена на тарифе.
          </p>
          {dirty && (
            <p className="text-xs text-amber-400">Сохраните список, чтобы собрать ленту или открыть превью.</p>
          )}
          {preview && (
            <div className="rounded bg-[var(--bg-primary)] p-3 space-y-2">
              <p className="text-xs text-[var(--text-muted)]">
                {preview.length ? `Превью: ${preview.length}` : 'Новых записей нет'}
              </p>
              {preview.map((item) => (
                <p key={item.id} className="text-xs border-b border-[var(--border-color)] py-1 whitespace-pre-wrap">
                  {item.text_preview}
                </p>
              ))}
            </div>
          )}
          {runResult && runResult.errors.length > 0 && runResult.created > 0 && (
            <p className="text-xs text-[var(--text-muted)]">
              Создано {runResult.created}, статус {runResult.status}
            </p>
          )}
        </CardContent>
        <CardFooter className="flex flex-wrap gap-2">
          <Button type="submit" disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={dirty || busy !== null || (channel.rss_feeds || []).length === 0}
            isLoading={busy === 'preview'}
            onClick={() => void showPreview()}
          >
            Preview
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={dirty || busy !== null || (channel.rss_feeds || []).length === 0}
            isLoading={busy === 'run'}
            onClick={() => void runNow()}
          >
            Собрать сейчас
          </Button>
        </CardFooter>
      </form>
    </Card>
  )
}

