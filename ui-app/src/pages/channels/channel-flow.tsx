import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { ConditionsEditor } from '@/components/conditions-editor'
import { smmService } from '@/services/smm-service'
import type {
  BrandChannel,
  ChannelAlertDelivery,
  ChannelAlertRule,
  ChannelProcessingConfig,
  ConditionsMode,
} from '@/types/smm'
import { publishAllowed, authStatusLabel } from '@/hooks/use-platform-readiness'
import { getErrorMessage } from '@/services/api-client'

type FlowTab = 'collect' | 'processing' | 'publish' | 'alerting'

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

function normalizeConditions(list: string[] | undefined): string[] {
  return (list || [])
    .map((c) => String(c).trim())
    .filter(Boolean)
    .slice(0, 20)
}

function sameExternalId(a?: string | null, b?: string | null): boolean {
  if (!a || !b) return false
  const x = String(a).trim()
  const y = String(b).trim()
  if (x === y) return true
  try {
    return Number(x) === Number(y)
  } catch {
    return false
  }
}

export function ChannelFlowPage() {
  const { channelId: channelIdParam } = useParams()
  const channelId = Number(channelIdParam)
  const navigate = useNavigate()

  const [channel, setChannel] = useState<BrandChannel | null>(null)
  const [brandChannels, setBrandChannels] = useState<BrandChannel[]>([])
  const [tab, setTab] = useState<FlowTab>('collect')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const [conditions, setConditions] = useState<string[]>([])
  const [conditionsMode, setConditionsMode] = useState<ConditionsMode>('any_of')
  const [processing, setProcessing] = useState<ChannelProcessingConfig>({})
  const [publishTargets, setPublishTargets] = useState<number[]>([])
  const [collectEnabled, setCollectEnabled] = useState(false)
  const [publishEnabled, setPublishEnabled] = useState(false)
  const [alertEnabled, setAlertEnabled] = useState(false)
  const [delivery, setDelivery] = useState<ChannelAlertDelivery>({})
  const [alertTargets, setAlertTargets] = useState<number[]>([])
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
        setConditions(ch.save_conditions || [])
        setConditionsMode(ch.conditions_mode === 'all_of' ? 'all_of' : 'any_of')
        setProcessing(ch.processing || {})
        setPublishTargets(ch.publish_targets || [])
        setCollectEnabled(Boolean(ch.collect_enabled))
        setPublishEnabled(Boolean(ch.publish_enabled))
        setAlertEnabled(Boolean(ch.alert_enabled))
        const nextDelivery = ch.alert_delivery || {}
        setDelivery(nextDelivery)
        setRules(ch.alert_rules?.length ? ch.alert_rules : [emptyRule()])
        const siblings = await smmService.listChannels(ch.brand_id)
        setBrandChannels(siblings)
        const storedTargets = (nextDelivery.alert_targets || []).filter(
          (id) => Number.isFinite(id) && id > 0,
        )
        if (storedTargets.length > 0) {
          setAlertTargets(storedTargets)
        } else if (nextDelivery.channel_to_post) {
          const matched = siblings.find(
            (c) =>
              c.role === 'own' &&
              c.network === 'tg' &&
              sameExternalId(c.external_id, nextDelivery.channel_to_post),
          )
          setAlertTargets(matched ? [matched.id] : [])
        } else {
          setAlertTargets([])
        }
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

  const ownPublishCandidates = useMemo(() => {
    if (!channel) return []
    return brandChannels.filter(
      (c) => c.role === 'own' && c.id !== channel.id && Boolean(c.external_id),
    )
  }, [brandChannels, channel])

  const ownAlertCandidates = useMemo(() => {
    if (!channel) return []
    return brandChannels.filter(
      (c) =>
        c.role === 'own' &&
        c.network === 'tg' &&
        c.id !== channel.id &&
        Boolean(c.external_id),
    )
  }, [brandChannels, channel])

  async function saveCollect(e: FormEvent) {
    e.preventDefault()
    if (!channel) return
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const save_conditions = normalizeConditions(conditions)
      const updated = await smmService.updateChannel(channel.brand_id, channel.id, {
        save_conditions,
        conditions_mode: conditionsMode,
        collect_enabled: collectEnabled,
      })
      setChannel(updated)
      setCollectEnabled(Boolean(updated.collect_enabled))
      setConditions(updated.save_conditions || [])
      setConditionsMode(updated.conditions_mode === 'all_of' ? 'all_of' : 'any_of')
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
      const { process_services: _drop, ...rest } = processing
      const updated = await smmService.updateChannel(channel.brand_id, channel.id, {
        processing: rest,
      })
      setChannel(updated)
      setProcessing(updated.processing || {})
      setSuccess('Обработка сохранена')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function savePublish(e: FormEvent) {
    e.preventDefault()
    if (!channel) return
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const updated = await smmService.updateChannel(channel.brand_id, channel.id, {
        publish_targets: publishTargets,
        publish_enabled: publishEnabled && publishTargets.length > 0,
      })
      setChannel(updated)
      setPublishTargets(updated.publish_targets || [])
      setPublishEnabled(Boolean(updated.publish_enabled))
      setSuccess('Целевые каналы публикации сохранены')
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
    setError('')
    setSuccess('')
    const cleanedRules = rules
      .map((r) => ({
        ...r,
        id: r.id || newRuleId(),
        conditions_mode: r.conditions_mode === 'all_of' ? 'all_of' : 'any_of',
        save_conditions: normalizeConditions(r.save_conditions).slice(0, 10),
      }))
      .filter((r) => r.save_conditions.length > 0)
    const selected = ownAlertCandidates.filter((c) => alertTargets.includes(c.id))
    const alertText = (delivery.alert_text || '').trim()
    if (selected.length === 0) {
      setError('Выберите хотя бы один канал, куда отправлять алерт')
      return
    }
    if (!alertText) {
      setError('Укажите текст уведомления')
      return
    }
    if (cleanedRules.length === 0) {
      setError('Добавьте ключевые слова (например: Внимание) — без них алерт не сработает')
      return
    }
    setSaving(true)
    try {
      const first = selected[0]
      const updated = await smmService.updateChannel(channel.brand_id, channel.id, {
        alert_delivery: {
          alert_targets: selected.map((c) => c.id),
          channel_to_post: first?.external_id || null,
          channel_to_post_title: first?.title || null,
          alert_text: alertText,
          include_ai_summary: Boolean(delivery.include_ai_summary),
        },
        alert_rules: cleanedRules,
        alert_enabled: alertEnabled,
      })
      setChannel(updated)
      setAlertEnabled(Boolean(updated.alert_enabled))
      setRules(updated.alert_rules?.length ? updated.alert_rules : [emptyRule()])
      const nextDelivery = updated.alert_delivery || {}
      setDelivery(nextDelivery)
      setAlertTargets(nextDelivery.alert_targets || selected.map((c) => c.id))
      setSuccess('Алерты сохранены')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  function updateRule(id: string, patch: Partial<ChannelAlertRule>) {
    setRules((prev) => prev.map((r) => (r.id === id ? { ...r, ...patch } : r)))
  }

  function togglePublishTarget(id: number) {
    setPublishTargets((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  function toggleAlertTarget(id: number) {
    setAlertTargets((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
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
      {channel.role === 'own' && !publishAllowed(channel) && (
        <Alert variant="warning">
          Публикация недоступна: собственность канала не подтверждена (
          {authStatusLabel(channel.auth_status)}
          {channel.auth_error ? ` — ${channel.auth_error}` : ''}). Канал можно настроить для
          сбора/алертов. Для Publish подключите{' '}
          <Link to={channel.network === 'vk' ? '/vkontakte' : '/telegram'} className="underline">
            {channel.network === 'vk' ? 'VK' : 'Telegram'}
          </Link>{' '}
          и нажмите Recheck на Channels.
        </Alert>
      )}

      <div className="flex gap-2 mb-4 flex-wrap">
        {(
          [
            ['collect', 'Сбор'],
            ['processing', 'Обработка'],
            ['publish', 'Публикация'],
            ['alerting', 'Алерты'],
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
              Условия сбора для этого канала. Пустой список — сохранять все сообщения.
              Отдельно от алертов: сбор кладёт пост в базу, алерт сразу пишет в ваши каналы.
            </CardDescription>
          </CardHeader>
          <form onSubmit={saveCollect}>
            <CardContent className="space-y-4">
              <label className="flex items-center gap-2 text-sm font-medium">
                <input
                  type="checkbox"
                  checked={collectEnabled}
                  onChange={(e) => setCollectEnabled(e.target.checked)}
                />
                Сбор включён (Collect)
              </label>
              <ConditionsEditor
                conditions={conditions}
                mode={conditionsMode}
                onConditionsChange={setConditions}
                onModeChange={setConditionsMode}
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
            <CardDescription>
              Настройки обработки сообщений с этого канала перед публикацией
            </CardDescription>
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
              <div className="rounded-lg border border-[var(--border-color)] p-3 space-y-1">
                <label className="flex items-center gap-2 text-sm font-medium">
                  <input
                    type="checkbox"
                    checked={!!processing.status_review_after_process}
                    onChange={(e) =>
                      setProcessing((p) => ({
                        ...p,
                        status_review_after_process: e.target.checked,
                      }))
                    }
                  />
                  На review после обработки
                </label>
                <p className="text-xs text-[var(--text-muted)] pl-6">
                  Пост останется на ручной проверке перед публикацией в целевые каналы.
                </p>
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

      {tab === 'publish' && (
        <Card>
          <CardHeader>
            <CardTitle>Публикация</CardTitle>
            <CardDescription>
              Целевые каналы публикации — own-каналы этого бренда, куда уйдут обработанные
              сообщения.
            </CardDescription>
          </CardHeader>
          <form onSubmit={savePublish}>
            <CardContent className="space-y-3">
              <label className="flex items-center gap-2 text-sm font-medium">
                <input
                  type="checkbox"
                  checked={publishEnabled}
                  disabled={channel.role !== 'own' || !publishAllowed(channel)}
                  onChange={(e) => setPublishEnabled(e.target.checked)}
                />
                Публикация включена (Publish)
                {channel.role === 'own' && !publishAllowed(channel) && (
                  <span className="text-xs text-amber-400 font-normal">
                    — сначала Recheck ownership в Channels
                  </span>
                )}
              </label>
              {ownPublishCandidates.length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">
                  Нет own-каналов бренда для выбора. Добавьте каналы с ролью own в хабе Channels.
                </p>
              ) : (
                <div className="space-y-2">
                  {ownPublishCandidates.map((c) => {
                    const selected = publishTargets.includes(c.id)
                    return (
                      <label
                        key={c.id}
                        className="flex items-start gap-3 rounded-md border border-[var(--border-color)] p-3 text-sm cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          className="mt-0.5"
                          checked={selected}
                          onChange={() => togglePublishTarget(c.id)}
                        />
                        <span>
                          <span className="font-medium">
                            {c.title || c.external_id}
                          </span>
                          <span className="block text-xs text-[var(--text-muted)]">
                            {c.network.toUpperCase()} · {c.external_id}
                            {c.publish_enabled === false ? ' · publish off' : ''}
                          </span>
                        </span>
                      </label>
                    )
                  })}
                </div>
              )}
              {publishTargets.length > 0 && (
                <p className="text-xs text-[var(--text-muted)]">
                  Выбрано: {publishTargets.length}
                </p>
              )}
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
            <CardTitle>Алерты</CardTitle>
            <CardDescription>
              Куда отправлять уведомление, когда в этом канале появляется сообщение с ключевыми
              словами. Сейчас только Telegram.
            </CardDescription>
          </CardHeader>
          <form onSubmit={saveAlerting}>
            <CardContent className="space-y-6">
              {!isTg && (
                <Alert variant="error">
                  Алерты для {channel.network.toUpperCase()} пока недоступны
                </Alert>
              )}

              <label className="flex items-center gap-2 text-sm font-medium">
                <input
                  type="checkbox"
                  checked={alertEnabled}
                  disabled={!isTg}
                  onChange={(e) => setAlertEnabled(e.target.checked)}
                />
                Алерты включены (Alert)
              </label>

              <div className="space-y-3">
                <h4 className="text-sm font-medium">Куда отправлять</h4>
                <p className="text-xs text-[var(--text-muted)]">
                  Свои (own) Telegram-каналы бренда — как на вкладке «Публикация», но для мгновенного
                  уведомления, а не для готового поста.
                </p>
                {ownAlertCandidates.length === 0 ? (
                  <p className="text-sm text-[var(--text-muted)]">
                    Нет own-каналов Telegram для выбора. Добавьте каналы с ролью own в хабе Channels.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {ownAlertCandidates.map((c) => {
                      const selected = alertTargets.includes(c.id)
                      return (
                        <label
                          key={c.id}
                          className="flex items-start gap-3 rounded-md border border-[var(--border-color)] p-3 text-sm cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            className="mt-0.5"
                            checked={selected}
                            disabled={!isTg}
                            onChange={() => toggleAlertTarget(c.id)}
                          />
                          <span>
                            <span className="font-medium">{c.title || c.external_id}</span>
                            <span className="block text-xs text-[var(--text-muted)]">
                              {c.network.toUpperCase()} · {c.external_id}
                            </span>
                          </span>
                        </label>
                      )
                    })}
                  </div>
                )}
                {alertTargets.length > 0 && (
                  <p className="text-xs text-[var(--text-muted)]">Выбрано: {alertTargets.length}</p>
                )}
              </div>

              <div className="space-y-3">
                <h4 className="text-sm font-medium">Текст уведомления</h4>
                <textarea
                  className="w-full min-h-[80px] rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                  value={delivery.alert_text || ''}
                  onChange={(e) => setDelivery((d) => ({ ...d, alert_text: e.target.value }))}
                  placeholder="Заголовок алерта, например: Срочно / совпадение по ключу"
                  disabled={!isTg}
                />
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={!!delivery.include_ai_summary}
                    onChange={(e) =>
                      setDelivery((d) => ({ ...d, include_ai_summary: e.target.checked }))
                    }
                    disabled={!isTg}
                  />
                  Добавить краткое AI-резюме к тексту
                </label>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <h4 className="text-sm font-medium">Когда отправлять</h4>
                    <p className="text-xs text-[var(--text-muted)] mt-1">
                      Ключевые слова в тексте сообщения источника. Если совпало — алерт уходит в
                      выбранные каналы. Не путать со вкладкой «Сбор»: там пост сохраняется в базу,
                      здесь сразу уведомление.
                    </p>
                  </div>
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    disabled={!isTg || rules.length >= 10}
                    onClick={() => setRules((prev) => [...prev, emptyRule()])}
                  >
                    Ещё набор слов
                  </Button>
                </div>
                {rules.map((rule, idx) => (
                  <div
                    key={rule.id}
                    className="p-3 rounded-lg border border-[var(--border-color)] space-y-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-xs text-[var(--text-muted)]">
                        Набор #{idx + 1}
                        {rules.length > 1 ? ' — сработает, если совпал этот список' : ''}
                      </span>
                      {rules.length > 1 && (
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          onClick={() => setRules((prev) => prev.filter((r) => r.id !== rule.id))}
                          disabled={!isTg}
                        >
                          Удалить
                        </Button>
                      )}
                    </div>
                    <ConditionsEditor
                      conditions={rule.save_conditions || []}
                      mode={rule.conditions_mode === 'all_of' ? 'all_of' : 'any_of'}
                      onConditionsChange={(save_conditions) =>
                        updateRule(rule.id, { save_conditions })
                      }
                      onModeChange={(conditions_mode) => updateRule(rule.id, { conditions_mode })}
                      disabled={!isTg}
                      maxItems={10}
                      placeholder="Ключевое слово или фраза"
                    />
                  </div>
                ))}
              </div>
            </CardContent>
            <CardFooter>
              <Button type="submit" disabled={saving || !isTg}>
                {saving ? 'Saving…' : 'Save'}
              </Button>
            </CardFooter>
          </form>
        </Card>
      )}
    </PageContainer>
  )
}
