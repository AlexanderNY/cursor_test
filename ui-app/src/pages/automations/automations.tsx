import { FormEvent, useEffect, useState } from 'react'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import type { AutomationRule, AutomationType } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'

export function AutomationsPage() {
  const { selectedBrandId, ownChannels } = useBrand()
  const [rules, setRules] = useState<AutomationRule[]>([])
  const [type, setType] = useState<AutomationType>('rss')
  const [source, setSource] = useState('')
  const [suffix, setSuffix] = useState('')
  const [keywords, setKeywords] = useState('')
  const [targetIds, setTargetIds] = useState<number[]>([])
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  async function load() {
    try {
      setRules(await smmService.listAutomations(selectedBrandId ?? undefined))
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

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (!selectedBrandId) {
      setError('Выберите бренд')
      return
    }
    setSaving(true)
    setError('')
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
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function toggleEnabled(rule: AutomationRule) {
    try {
      await smmService.updateAutomation(rule.id, { enabled: !rule.enabled })
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function remove(rule: AutomationRule) {
    try {
      await smmService.deleteAutomation(rule.id)
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Automations"
        description="RSS → review queue (pending_approval on Standard+), repost, mentions"
      />
      {error && <Alert variant="error">{error}</Alert>}

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
                <option value="rss">RSS → channels</option>
                <option value="tg_repost">TG source → repost</option>
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
                      <input
                        type="checkbox"
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
              <Button type="submit" disabled={saving || !selectedBrandId}>
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
                <div className="flex gap-2">
                  <Button size="sm" variant="secondary" onClick={() => void toggleEnabled(r)}>
                    Toggle
                  </Button>
                  {r.type === 'rss' && (
                    <Button
                      size="sm"
                      onClick={async () => {
                        try {
                          const res = await smmService.runAutomation(r.id)
                          setError('')
                          alert(
                            `Created ${res.created} jobs (${res.status}). Open Calendar to review.`,
                          )
                        } catch (err) {
                          setError(getErrorMessage(err))
                        }
                      }}
                    >
                      Run now
                    </Button>
                  )}
                  <Button size="sm" variant="ghost" onClick={() => void remove(r)}>
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
