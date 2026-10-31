import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { QuotaBanner } from '@/components/billing/QuotaBanner'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import type { AutomationRule, AutomationType, UsageSummary } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'
import { parseQuotaError } from '@/lib/quota'
import { Switch } from '@/components/ui/switch'

type PreviewState = {
  automationId: number
  items: { id: string; text_preview: string }[]
  would_create: number
  status: string
  targets: { network: string; external_id: string }[]
}

export function AutomationsPage() {
  const { selectedBrandId, ownChannels } = useBrand()
  const [rules, setRules] = useState<AutomationRule[]>([])
  const [type, setType] = useState<AutomationType>('tg_repost')
  const [source, setSource] = useState('')
  const [suffix, setSuffix] = useState('')
  const [keywords, setKeywords] = useState('')
  const [targetIds, setTargetIds] = useState<number[]>([])
  const [error, setError] = useState('')
  const [upgradeHint, setUpgradeHint] = useState('')
  const [saving, setSaving] = useState(false)
  const [usage, setUsage] = useState<UsageSummary | null>(null)
  const [preview, setPreview] = useState<PreviewState | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)

  const automationsMetric = useMemo(
    () => usage?.metrics?.find((m) => m.key === 'max_automations'),
    [usage],
  )
  const atAutomationLimit =
    automationsMetric != null &&
    automationsMetric.limit > 0 &&
    (automationsMetric.used ?? 0) >= automationsMetric.limit

  async function load() {
    try {
      const [list, planUsage] = await Promise.all([
        smmService.listAutomations(selectedBrandId ?? undefined),
        smmService.getUsageSummary().catch(() => null),
      ])
      setRules(list)
      setUsage(planUsage)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  useEffect(() => {
    void load()
  }, [selectedBrandId])

  function toggleTarget(id: number) {
    setTargetIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  function handleApiError(err: unknown) {
    const quota = parseQuotaError(err)
    if (quota) {
      setError(quota.message)
      setUpgradeHint(quota.upgrade_url || '/pricing')
      return
    }
    setUpgradeHint('')
    setError(getErrorMessage(err))
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (!selectedBrandId) {
      setError('Выберите бренд')
      return
    }
    if (atAutomationLimit) {
      setError(
        `Лимит автоматизаций исчерпан (${automationsMetric?.used}/${automationsMetric?.limit}). Обновите план.`,
      )
      setUpgradeHint('/pricing')
      return
    }
    setSaving(true)
    setError('')
    setUpgradeHint('')
    try {
      const config: Record<string, unknown> = {
        target_channel_ids: targetIds,
        suffix: suffix || undefined,
      }
      if (type === 'rss') config.source_url = source
      else if (type === 'tg_repost') config.source_channel = source
      else config.keywords = keywords.split(',').map((k) => k.trim()).filter(Boolean)

      await smmService.createAutomation({
        brand_id: selectedBrandId,
        type,
        config,
        enabled: true,
      })
      setSource('')
      setSuffix('')
      setKeywords('')
      await load()
    } catch (err) {
      handleApiError(err)
    } finally {
      setSaving(false)
    }
  }

  async function toggleEnabled(rule: AutomationRule) {
    try {
      await smmService.updateAutomation(rule.id, { enabled: !rule.enabled })
      await load()
    } catch (err) {
      handleApiError(err)
    }
  }

  async function remove(rule: AutomationRule) {
    try {
      await smmService.deleteAutomation(rule.id)
      if (preview?.automationId === rule.id) setPreview(null)
      await load()
    } catch (err) {
      handleApiError(err)
    }
  }

  async function showPreview(rule: AutomationRule) {
    setBusyId(rule.id)
    setError('')
    setUpgradeHint('')
    try {
      const res = await smmService.previewAutomation(rule.id, 5)
      setPreview({
        automationId: rule.id,
        items: res.items,
        would_create: res.would_create,
        status: res.status,
        targets: res.targets,
      })
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusyId(null)
    }
  }

  async function runNow(rule: AutomationRule) {
    setBusyId(rule.id)
    setError('')
    setUpgradeHint('')
    try {
      const res = await smmService.runAutomation(rule.id)
      setPreview(null)
      alert(
        `Создано ${res.created} job(s), статус ${res.status}. Откройте календарь: при ошибке цели придёт уведомление.`,
      )
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Automations"
        description="TG repost и RSS → очередь jobs (pending_approval на Standard+). RSS одного своего канала — в карточке канала, вкладка «Сбор»."
      />
      <QuotaBanner metrics={usage?.metrics} focusKey="max_automations" className="mb-4" />
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
      {automationsMetric && automationsMetric.limit > 0 && (
        <p className="text-sm text-[var(--text-muted)] mb-4">
          Автоматизации: {automationsMetric.used ?? 0} / {automationsMetric.limit}
          {atAutomationLimit && (
            <>
              {' · '}
              <Link to="/pricing" className="text-primary-400 hover:underline">
                Upgrade
              </Link>
            </>
          )}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Новое правило</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-3">
              <select
                className="w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2"
                value={type}
                onChange={(e) => setType(e.target.value as AutomationType)}
              >
                <option value="tg_repost">TG source → repost</option>
                <option value="rss">RSS → channels</option>
                <option value="mention">Mention keywords</option>
              </select>
              {type === 'rss' && (
                <Input
                  label="RSS URL"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  placeholder="https://…"
                />
              )}
              {type === 'tg_repost' && (
                <Input
                  label="Source channel ID"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  placeholder="Telegram chat / channel id"
                />
              )}
              {type === 'mention' && (
                <Input
                  label="Keywords (comma-separated)"
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                />
              )}
              <Input
                label="Suffix / hashtag / comment"
                value={suffix}
                onChange={(e) => setSuffix(e.target.value)}
                placeholder="#brand"
              />
              <div>
                <p className="text-sm text-[var(--text-secondary)] mb-2">Target own channels</p>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {ownChannels.map((c) => (
                    <label key={c.id} className="flex items-center gap-2 text-sm">
                      <Switch
                        checked={targetIds.includes(c.id)}
                        onChange={() => toggleTarget(c.id)}
                      />
                      <span className="uppercase text-[var(--text-muted)]">{c.network}</span>
                      {c.title || c.external_id}
                    </label>
                  ))}
                  {ownChannels.length === 0 && (
                    <p className="text-xs text-[var(--text-muted)]">Добавьте own-каналы в Brands</p>
                  )}
                </div>
              </div>
              <Button
                type="submit"
                disabled={saving || !selectedBrandId || atAutomationLimit}
                title={atAutomationLimit ? 'Лимит тарифа' : undefined}
              >
                Create
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Правила</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {rules.length === 0 && (
              <p className="text-sm text-[var(--text-muted)]">Нет правил</p>
            )}
            {rules.map((r) => (
              <div
                key={r.id}
                className="rounded border border-[var(--border-color)] p-3 text-sm space-y-2"
              >
                <div className="flex justify-between">
                  <span className="font-medium uppercase">{r.type}</span>
                  <span className={r.enabled ? 'text-emerald-500' : 'text-[var(--text-muted)]'}>
                    {r.enabled ? 'on' : 'off'}
                  </span>
                </div>
                <pre className="text-xs text-[var(--text-muted)] overflow-auto">
                  {JSON.stringify(r.config, null, 2)}
                </pre>
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" variant="secondary" onClick={() => void toggleEnabled(r)}>
                    Toggle
                  </Button>
                  {(r.type === 'rss' || r.type === 'tg_repost') && (
                    <>
                      <Button
                        size="sm"
                        variant="secondary"
                        isLoading={busyId === r.id}
                        onClick={() => void showPreview(r)}
                      >
                        Preview
                      </Button>
                      <Button
                        size="sm"
                        isLoading={busyId === r.id}
                        onClick={() => void runNow(r)}
                      >
                        Run now
                      </Button>
                    </>
                  )}
                  <Button size="sm" variant="ghost" onClick={() => void remove(r)}>
                    Delete
                  </Button>
                </div>
                {preview?.automationId === r.id && (
                  <div className="mt-2 rounded bg-[var(--bg-secondary)] p-2 space-y-1">
                    <p className="text-xs text-[var(--text-muted)]">
                      Превью: {preview.would_create} новых → статус {preview.status}, целей{' '}
                      {preview.targets.length}
                    </p>
                    {preview.items.length === 0 && (
                      <p className="text-xs text-[var(--text-muted)]">
                        Нет новых постов (уже в seen_ids или источник пуст)
                      </p>
                    )}
                    {preview.items.map((item) => (
                      <p key={item.id} className="text-xs border-b border-[var(--border-color)] py-1">
                        {item.text_preview}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
