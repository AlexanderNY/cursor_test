import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { smmService } from '@/services/smm-service'
import type {
  BrandChannel,
  ChannelAlertDelivery,
  ChannelAlertRule,
  ChannelProcessingConfig,
} from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'

type FlowTab = 'collect' | 'processing' | 'alerting'

function newRuleId(): string {
  return crypto.randomUUID?.() || `rule-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function emptyRule(): ChannelAlertRule {
  return {
    id: newRuleId(),
    enabled: true,
    priority: 0,
    save_conditions: [],
    conditions_mode: 'any_of',
    dedup_window_sec: 3600,
    min_text_length: 0,
    stop_on_match: false,
  }
}

export function ChannelFlowPage() {
  const { channelId: channelIdParam } = useParams()
  const channelId = Number(channelIdParam)
  const navigate = useNavigate()

  const [channel, setChannel] = useState<BrandChannel | null>(null)
  const [tab, setTab] = useState<FlowTab>('collect')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const [conditionsText, setConditionsText] = useState('')
  const [processing, setProcessing] = useState<ChannelProcessingConfig>({})
  const [delivery, setDelivery] = useState<ChannelAlertDelivery>({})
  const [rules, setRules] = useState<ChannelAlertRule[]>([])

  useEffect(() => {
    if (!Number.isFinite(channelId) || channelId <= 0) {
      setError('Invalid channel id')
      setLoading(false)
      return
    }
    void (async () => {
      setLoading(true)
      setError('')
      try {
        const ch = await smmService.getChannel(channelId)
        setChannel(ch)
        setConditionsText((ch.save_conditions || []).join('\n'))
        setProcessing(ch.processing || {})
        setDelivery(ch.alert_delivery || {})
        setRules(ch.alert_rules?.length ? ch.alert_rules : [])
      } catch (err) {
        setError(getErrorMessage(err))
      } finally {
        setLoading(false)
      }
    })()
  }, [channelId])

  const analyticsHref = useMemo(() => {
    if (!channel) return '/analytics'
    const q = new URLSearchParams({
      brand_id: String(channel.brand_id),
      channel_id: String(channel.id),
    })
    return `/analytics?${q.toString()}`
  }, [channel])

  async function saveCollect(e: FormEvent) {
    e.preventDefault()
    if (!channel) return
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const save_conditions = conditionsText
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean)
        .slice(0, 20)
      const updated = await smmService.updateChannel(channel.brand_id, channel.id, {
        save_conditions,
      })
      setChannel(updated)
      setSuccess('Условия сбора сохранены')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function saveProcessing(e: FormEvent) {
    e.preventDefault()
    if (!channel) return
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const updated = await smmService.updateChannel(channel.brand_id, channel.id, {
        processing,
      })
      setChannel(updated)
      setSuccess('Обработка сохранена')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function saveAlerting(e: FormEvent) {
    e.preventDefault()
    if (!channel) return
    if (channel.network !== 'tg') {
      setError('Alerting пока только для Telegram')
      return
    }
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const cleanedRules = rules.map((r) => ({
        ...r,
        id: r.id || newRuleId(),
        save_conditions: (r.save_conditions || [])
          .map((c) => String(c).trim())
          .filter(Boolean)
          .slice(0, 10),
      }))
      const updated = await smmService.updateChannel(channel.brand_id, channel.id, {
        alert_delivery: {
          channel_to_post: (delivery.channel_to_post || '').trim() || null,
          channel_to_post_title: (delivery.channel_to_post_title || '').trim() || null,
          alert_text: (delivery.alert_text || '').trim() || null,
          include_ai_summary: Boolean(delivery.include_ai_summary),
        },
        alert_rules: cleanedRules,
        alert_enabled: channel.alert_enabled ?? false,
      })
      setChannel(updated)
      setRules(updated.alert_rules || [])
      setDelivery(updated.alert_delivery || {})
      setSuccess('Alerting сохранён')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  function updateRule(id: string, patch: Partial<ChannelAlertRule>) {
    setRules((prev) => prev.map((r) => (r.id === id ? { ...r, ...patch } : r)))
  }

  if (loading) {
    return (
      <PageContainer>
        <p className="text-sm text-[var(--text-muted)]">Загрузка канала…</p>
      </PageContainer>
    )
  }

  if (!channel) {
    return (
      <PageContainer>
        <Alert variant="error">{error || 'Канал не найден'}</Alert>
        <Button className="mt-4" variant="secondary" onClick={() => navigate('/channels')}>
          ← Channels
        </Button>
      </PageContainer>
    )
  }

  const isTg = channel.network === 'tg'

  return (
    <PageContainer>
      <PageHeader
        title={channel.title || channel.external_id}
        description={`${channel.network.toUpperCase()} · ${channel.role} · ${channel.brand_name || `brand #${channel.brand_id}`}`}
      />
      <div className="flex flex-wrap gap-3 mb-4 text-sm">
        <Link to="/channels" className="text-primary-400 hover:underline">
          ← Channels
        </Link>
        <Link to={analyticsHref} className="text-primary-400 hover:underline">
          Смотреть аналитику →
        </Link>
      </div>
      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      <div className="flex gap-2 mb-4 flex-wrap">
        {(
          [
            ['collect', 'Сбор'],
            ['processing', 'Обработка'],
            ['alerting', 'Alerting'],
          ] as const
        ).map(([id, label]) => (
          <Button
            key={id}
            size="sm"
            variant={tab === id ? 'primary' : 'secondary'}
            onClick={() => setTab(id)}
          >
            {label}
          </Button>
        ))}
      </div>

      {tab === 'collect' && (
        <Card>
          <CardHeader>
            <CardTitle>Save Conditions</CardTitle>
            <CardDescription>
              Условия сбора для этого канала (по одному на строку). Пустой список — сохранять все
              сообщения.
            </CardDescription>
          </CardHeader>
          <form onSubmit={saveCollect}>
            <CardContent>
              <textarea
                className="w-full min-h-[160px] rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                value={conditionsText}
                onChange={(e) => setConditionsText(e.target.value)}
                placeholder={"keyword\n#hashtag"}
              />
            </CardContent>
            <CardFooter>
              <Button type="submit" disabled={saving}>
                {saving ? 'Saving…' : 'Save'}
              </Button>
            </CardFooter>
          </form>
        </Card>
      )}

      {tab === 'processing' && (
        <Card>
          <CardHeader>
            <CardTitle>Обработка</CardTitle>
            <CardDescription>Настройки обработки сообщений с этого канала перед публикацией</CardDescription>
          </CardHeader>
          <form onSubmit={saveProcessing}>
            <CardContent className="space-y-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={!!processing.process_enabled}
                  onChange={(e) =>
                    setProcessing((p) => ({ ...p, process_enabled: e.target.checked }))
                  }
                />
                Обрабатывать перед публикацией
              </label>
              <div>
                <label className="text-sm text-[var(--text-secondary)]">Описание обработки</label>
                <textarea
                  className="w-full mt-1 min-h-[80px] rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                  value={processing.processing_description || ''}
                  onChange={(e) =>
                    setProcessing((p) => ({ ...p, processing_description: e.target.value }))
                  }
                />
              </div>
              <div className="flex flex-wrap gap-4 text-sm">
                {(
                  [
                    ['remove_emojis', 'Удалить эмодзи'],
                    ['remove_images', 'Удалить картинки'],
                    ['clean_html', 'Очистить HTML'],
                    ['status_review_after_process', 'На review после обработки'],
                  ] as const
                ).map(([key, label]) => (
                  <label key={key} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={!!processing[key]}
                      onChange={(e) => setProcessing((p) => ({ ...p, [key]: e.target.checked }))}
                    />
                    {label}
                  </label>
                ))}
              </div>
              <div>
                <p className="text-sm text-[var(--text-secondary)] mb-2">Целевые сервисы</p>
                <div className="flex flex-wrap gap-4 text-sm">
                  {(
                    [
                      ['telegram', 'Telegram'],
                      ['wordpress', 'WordPress'],
                      ['twitter', 'Twitter'],
                      ['vkontakte', 'VKontakte'],
                    ] as const
                  ).map(([svc, label]) => {
                    const selected = (processing.process_services || []).includes(svc)
                    return (
                      <label key={svc} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={selected}
                          onChange={(e) => {
                            const cur = new Set(processing.process_services || [])
                            if (e.target.checked) cur.add(svc)
                            else cur.delete(svc)
                            setProcessing((p) => ({
                              ...p,
                              process_services: Array.from(cur),
                            }))
                          }}
                        />
                        {label}
                      </label>
                    )
                  })}
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button type="submit" disabled={saving}>
                {saving ? 'Saving…' : 'Save'}
              </Button>
            </CardFooter>
          </form>
        </Card>
      )}

      {tab === 'alerting' && (
        <Card>
          <CardHeader>
            <CardTitle>Alerting</CardTitle>
            <CardDescription>
              Несколько правил матчинга + одно общее оповещение (куда и текст). Сейчас только TG.
            </CardDescription>
          </CardHeader>
          <form onSubmit={saveAlerting}>
            <CardContent className="space-y-6">
              {!isTg && (
                <Alert variant="error">Alerting для {channel.network.toUpperCase()} пока недоступен</Alert>
              )}
              <div className="space-y-3 p-3 rounded-lg border border-[var(--border-color)]">
                <h4 className="text-sm font-medium">Оповещение (одно на канал)</h4>
                <Input
                  label="Channel to post"
                  value={delivery.channel_to_post || ''}
                  onChange={(e) =>
                    setDelivery((d) => ({ ...d, channel_to_post: e.target.value }))
                  }
                  placeholder="-100… или @channel"
                  disabled={!isTg}
                />
                <Input
                  label="Title (optional)"
                  value={delivery.channel_to_post_title || ''}
                  onChange={(e) =>
                    setDelivery((d) => ({ ...d, channel_to_post_title: e.target.value }))
                  }
                  disabled={!isTg}
                />
                <div>
                  <label className="text-sm text-[var(--text-secondary)]">Alert text</label>
                  <textarea
                    className="w-full mt-1 min-h-[80px] rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                    value={delivery.alert_text || ''}
                    onChange={(e) => setDelivery((d) => ({ ...d, alert_text: e.target.value }))}
                    disabled={!isTg}
                  />
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={!!delivery.include_ai_summary}
                    onChange={(e) =>
                      setDelivery((d) => ({ ...d, include_ai_summary: e.target.checked }))
                    }
                    disabled={!isTg}
                  />
                  Include AI summary
                </label>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-sm font-medium">Правила матчинга</h4>
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    disabled={!isTg || rules.length >= 10}
                    onClick={() => setRules((prev) => [...prev, emptyRule()])}
                  >
                    Add rule
                  </Button>
                </div>
                {rules.length === 0 && (
                  <p className="text-sm text-[var(--text-muted)]">Нет правил — добавьте хотя бы одно</p>
                )}
                {rules.map((rule, idx) => (
                  <div
                    key={rule.id}
                    className="p-3 rounded-lg border border-[var(--border-color)] space-y-2"
                  >
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="text-xs text-[var(--text-muted)]">#{idx + 1}</span>
                      <label className="flex items-center gap-1 text-xs">
                        <input
                          type="checkbox"
                          checked={rule.enabled !== false}
                          onChange={(e) => updateRule(rule.id, { enabled: e.target.checked })}
                          disabled={!isTg}
                        />
                        enabled
                      </label>
                      <Input
                        label="Priority"
                        type="number"
                        className="w-24"
                        value={String(rule.priority ?? 0)}
                        onChange={(e) =>
                          updateRule(rule.id, { priority: Number(e.target.value) || 0 })
                        }
                        disabled={!isTg}
                      />
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        onClick={() => setRules((prev) => prev.filter((r) => r.id !== rule.id))}
                        disabled={!isTg}
                      >
                        Remove
                      </Button>
                    </div>
                    <textarea
                      className="w-full min-h-[72px] rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                      placeholder="Save conditions (one per line)"
                      value={(rule.save_conditions || []).join('\n')}
                      onChange={(e) =>
                        updateRule(rule.id, {
                          save_conditions: e.target.value
                            .split('\n')
                            .map((s) => s.trim())
                            .filter(Boolean),
                        })
                      }
                      disabled={!isTg}
                    />
                    <div className="flex flex-wrap gap-3 text-xs">
                      <label className="flex items-center gap-1">
                        Mode
                        <select
                          className="rounded border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1"
                          value={rule.conditions_mode || 'any_of'}
                          onChange={(e) =>
                            updateRule(rule.id, {
                              conditions_mode: e.target.value as 'any_of' | 'all_of',
                            })
                          }
                          disabled={!isTg}
                        >
                          <option value="any_of">any_of</option>
                          <option value="all_of">all_of</option>
                        </select>
                      </label>
                      <label className="flex items-center gap-1">
                        Dedup sec
                        <input
                          type="number"
                          className="w-24 rounded border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1"
                          value={rule.dedup_window_sec ?? 3600}
                          onChange={(e) =>
                            updateRule(rule.id, {
                              dedup_window_sec: Number(e.target.value) || 0,
                            })
                          }
                          disabled={!isTg}
                        />
                      </label>
                      <label className="flex items-center gap-1">
                        <input
                          type="checkbox"
                          checked={!!rule.stop_on_match}
                          onChange={(e) =>
                            updateRule(rule.id, { stop_on_match: e.target.checked })
                          }
                          disabled={!isTg}
                        />
                        stop on match
                      </label>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
            <CardFooter className="flex flex-wrap gap-2">
              <Button type="submit" disabled={saving || !isTg}>
                {saving ? 'Saving…' : 'Save alerting'}
              </Button>
              <Link to={analyticsHref}>
                <Button type="button" variant="secondary">
                  Смотреть аналитику
                </Button>
              </Link>
            </CardFooter>
          </form>
        </Card>
      )}
    </PageContainer>
  )
}
