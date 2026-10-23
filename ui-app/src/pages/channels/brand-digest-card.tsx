import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { smmService } from '@/services/smm-service'
import type { BrandChannel, DigestJob, DigestPreviewItem } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'
import { formatDateTime } from '@/utils/date'
import { Switch } from '@/components/ui/switch'

const RUN_MATCH_MS = 5 * 60 * 1000

function closestDigestPreview(
  lastRunAt: string,
  previews: DigestPreviewItem[],
): DigestPreviewItem | null {
  const runAt = new Date(lastRunAt).getTime()
  if (Number.isNaN(runAt)) return null
  let match: DigestPreviewItem | null = null
  let bestDelta = RUN_MATCH_MS
  for (const item of previews) {
    if (!item.created_at) continue
    const createdAt = new Date(item.created_at).getTime()
    if (Number.isNaN(createdAt)) continue
    const delta = Math.abs(createdAt - runAt)
    if (delta > bestDelta) continue
    match = item
    bestDelta = delta
  }
  return match
}

function nextDigestRunLabel(job: DigestJob): string {
  if (!job.enabled) return 'не запланирован — сводка выключена'
  if (!job.source_channel_ids?.length) return 'не запланирован — не выбраны каналы-источники'
  if (job.publish_channel_id == null) return 'не запланирован — не выбран канал публикации'
  if (!job.last_run_at) return 'в ближайшую минуту, если уже есть накопленный текст'
  const lastRun = new Date(job.last_run_at).getTime()
  if (Number.isNaN(lastRun)) return 'в ближайшую минуту'
  const nextRun = lastRun + (job.interval_min || 60) * 60 * 1000
  if (nextRun <= Date.now()) return 'в ближайшую минуту'
  return formatDateTime(new Date(nextRun))
}

function lastDigestRunDetail(job: DigestJob, previews: DigestPreviewItem[]): string {
  if (!job.last_run_at) return 'Цикл ещё ни разу не обрабатывал эту сводку.'
  const preview = closestDigestPreview(job.last_run_at, previews)
  if (!preview) {
    return 'Сводка не создана: к моменту запуска не было накопленных сообщений.'
  }
  const missAt = job.last_cover_miss_at ? new Date(job.last_cover_miss_at).getTime() : NaN
  const runAt = new Date(job.last_run_at).getTime()
  const missedCover =
    !Number.isNaN(missAt) && !Number.isNaN(runAt) && Math.abs(missAt - runAt) <= RUN_MATCH_MS
  const coverNote = missedCover
    ? ` Картинка не подобрана${job.last_cover_miss_theme ? `: ${job.last_cover_miss_theme}` : ''}.`
    : ''
  return `Опубликована сводка из ${preview.message_count} сообщ.${coverNote}`
}

interface BrandDigestCardProps {
  brandId: number
  channels: BrandChannel[]
}

export function BrandDigestCard({ brandId, channels }: BrandDigestCardProps) {
  const [job, setJob] = useState<DigestJob | null>(null)
  const [previews, setPreviews] = useState<DigestPreviewItem[]>([])
  const [enabled, setEnabled] = useState(false)
  const [sourceIds, setSourceIds] = useState<number[]>([])
  const [publishId, setPublishId] = useState<number | null>(null)
  const [intervalMin, setIntervalMin] = useState(60)
  const [processPrompt, setProcessPrompt] = useState('')
  const [summaryPrompt, setSummaryPrompt] = useState('')
  const [attachCover, setAttachCover] = useState(true)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const sourceCandidates = useMemo(
    () =>
      channels.filter(
        (c) =>
          c.brand_id === brandId &&
          Boolean(c.collect_enabled) &&
          (c.network === 'tg' || c.network === 'vk'),
      ),
    [channels, brandId],
  )

  const publishCandidates = useMemo(
    () =>
      channels.filter(
        (c) =>
          c.brand_id === brandId &&
          c.role === 'own' &&
          (c.network === 'tg' || c.network === 'vk'),
      ),
    [channels, brandId],
  )

  useEffect(() => {
    let cancelled = false
    void (async () => {
      setLoading(true)
      setError('')
      try {
        const [digest, items] = await Promise.all([
          smmService.getDigestJob(brandId),
          smmService.listDigestPreviews(brandId, 3).catch(() => []),
        ])
        if (cancelled) return
        setJob(digest)
        setEnabled(Boolean(digest.enabled))
        setSourceIds(digest.source_channel_ids || [])
        setPublishId(digest.publish_channel_id ?? null)
        setIntervalMin(digest.interval_min || 60)
        setProcessPrompt(digest.process_prompt || '')
        setSummaryPrompt(digest.summary_prompt || '')
        setAttachCover(digest.attach_cover_image !== false)
        setPreviews(items)
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err))
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [brandId])

  function toggleSource(id: number) {
    setSourceIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setSaving(true)
    try {
      const saved = await smmService.saveDigestJob(brandId, {
        enabled,
        source_channel_ids: sourceIds,
        publish_channel_id: publishId,
        interval_min: intervalMin,
        process_prompt: processPrompt,
        summary_prompt: summaryPrompt,
        attach_cover_image: attachCover,
      })
      setJob(saved)
      setSuccess('Сводка сохранена')
      const items = await smmService.listDigestPreviews(brandId, 3).catch(() => [])
      setPreviews(items)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card className="mb-4">
      <CardHeader>
        <CardTitle>Часовая сводка</CardTitle>
        <CardDescription>
          Сообщения с выбранных каналов вычитываются и копятся. Раз в интервал публикуется
          одна сводка в own-канал. Отдельные сообщения не уходят в публикацию.
        </CardDescription>
      </CardHeader>
      <form onSubmit={onSubmit}>
        <CardContent className="space-y-4">
          {error && <Alert variant="error">{error}</Alert>}
          {success && <Alert variant="success">{success}</Alert>}
          {loading ? (
            <p className="text-sm text-[var(--text-muted)]">Загрузка…</p>
          ) : (
            <>
              {job && (
                <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)]/40 p-3 space-y-1 text-xs">
                  <p className="text-sm font-semibold text-[var(--text-primary)]">Последний запуск</p>
                  <p className="text-[var(--text-secondary)]">
                    Время: {job.last_run_at ? formatDateTime(job.last_run_at) : 'ещё не было'}
                  </p>
                  <p className="text-[var(--text-secondary)]">{lastDigestRunDetail(job, previews)}</p>
                  <p className="text-[var(--text-muted)]">Следующий: {nextDigestRunLabel(job)}</p>
                </div>
              )}

              <label className="flex items-center gap-2 text-sm font-medium">
                <Switch
                  checked={enabled}
                  onChange={(e) => setEnabled(e.target.checked)}
                />
                Сводка включена
              </label>

              <label className="flex items-center gap-2 text-sm font-medium">
                <Switch
                  checked={attachCover}
                  onChange={(e) => setAttachCover(e.target.checked)}
                />
                Картинка из заготовок
              </label>
              <p className="text-xs text-[var(--text-muted)] -mt-2 pl-6">
                AI выделит тему и подберёт media pack по тегам. Если заготовки нет — сводка
                уйдёт без картинки, а вам придёт уведомление.{' '}
                <Link to="/library" className="text-primary-400 hover:underline">
                  Library → Media packs
                </Link>
              </p>

              <Input
                label="Интервал (мин)"
                type="number"
                min={5}
                max={1440}
                value={intervalMin}
                onChange={(e) => setIntervalMin(Number(e.target.value) || 60)}
              />

              <div className="space-y-2">
                <h4 className="text-sm font-medium">Каналы-источники</h4>
                <p className="text-xs text-[var(--text-muted)]">
                  Нужен включённый Collect на TG/VK каналах бренда.
                </p>
                {sourceCandidates.length === 0 ? (
                  <p className="text-sm text-[var(--text-muted)]">
                    Нет каналов с Collect. Включите сбор в «Настроить».
                  </p>
                ) : (
                  <div className="space-y-2">
                    {sourceCandidates.map((c) => (
                      <label
                        key={c.id}
                        className="flex items-start gap-3 rounded-md border border-[var(--border-color)] p-3 text-sm cursor-pointer"
                      >
                        <Switch
                          className="mt-0.5"
                          checked={sourceIds.includes(c.id)}
                          onChange={() => toggleSource(c.id)}
                        />
                        <span>
                          <span className="font-medium">{c.title || c.external_id}</span>
                          <span className="block text-xs text-[var(--text-muted)]">
                            {c.network.toUpperCase()} · {c.external_id}
                          </span>
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-medium">Куда публиковать</h4>
                {publishCandidates.length === 0 ? (
                  <p className="text-sm text-[var(--text-muted)]">
                    Нет own TG/VK каналов для публикации.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {publishCandidates.map((c) => (
                      <label
                        key={c.id}
                        className="flex items-start gap-3 rounded-md border border-[var(--border-color)] p-3 text-sm cursor-pointer"
                      >
                        <input
                          type="radio"
                          className="mt-0.5"
                          name="digest-publish"
                          checked={publishId === c.id}
                          onChange={() => setPublishId(c.id)}
                        />
                        <span>
                          <span className="font-medium">{c.title || c.external_id}</span>
                          <span className="block text-xs text-[var(--text-muted)]">
                            {c.network.toUpperCase()} · {c.external_id}
                          </span>
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <label className="text-sm text-[var(--text-secondary)]">
                  Обработчик каждого сообщения
                </label>
                <textarea
                  className="w-full mt-1 min-h-[72px] rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                  value={processPrompt}
                  onChange={(e) => setProcessPrompt(e.target.value)}
                  placeholder="Вычитай текст…"
                />
              </div>

              <div>
                <label className="text-sm text-[var(--text-secondary)]">Инструкция сводки</label>
                <textarea
                  className="w-full mt-1 min-h-[72px] rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                  value={summaryPrompt}
                  onChange={(e) => setSummaryPrompt(e.target.value)}
                  placeholder="Краткая сводка тем и фактов…"
                />
              </div>

              <div className="rounded-lg border border-[var(--border-color)] p-3 space-y-2">
                <p className="text-xs font-semibold">Последние сводки</p>
                {previews.length === 0 ? (
                  <p className="text-xs text-[var(--text-muted)]">Пока нет сохранённых сводок.</p>
                ) : (
                  previews.map((d) => (
                    <div
                      key={d.id}
                      className="text-xs space-y-1 border-t border-[var(--border-color)] pt-2 first:border-0 first:pt-0"
                    >
                      <p className="text-[var(--text-muted)]">
                        {formatDateTime(d.created_at)} · {d.message_count} сообщ.
                      </p>
                      <p className="text-[var(--text-primary)] line-clamp-4 whitespace-pre-wrap">
                        {d.digest_text}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </>
          )}
        </CardContent>
        <CardFooter>
          <Button type="submit" disabled={saving || loading}>
            {saving ? 'Saving…' : 'Сохранить сводку'}
          </Button>
        </CardFooter>
      </form>
    </Card>
  )
}
