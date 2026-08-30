import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import type { ContentTemplate, MediaPack, TemplateKind } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'

const KINDS: { id: TemplateKind; label: string }[] = [
  { id: 'prompt', label: 'Prompt' },
  { id: 'cta', label: 'CTA' },
  { id: 'utm', label: 'UTM' },
  { id: 'post_body', label: 'Текст поста' },
]

type TabId = 'templates' | 'media'

export function LibraryPage() {
  const { selectedBrandId, selectedBrand, brands } = useBrand()
  const [tab, setTab] = useState<TabId>('templates')
  const [templates, setTemplates] = useState<ContentTemplate[]>([])
  const [packs, setPacks] = useState<MediaPack[]>([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [busy, setBusy] = useState(false)

  const [kind, setKind] = useState<TemplateKind>('cta')
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [utmBase, setUtmBase] = useState('')
  const [utmSource, setUtmSource] = useState('')
  const [utmMedium, setUtmMedium] = useState('')
  const [utmCampaign, setUtmCampaign] = useState('')
  const [utmPreview, setUtmPreview] = useState('')

  const [packTitle, setPackTitle] = useState('')
  const [packKeys, setPackKeys] = useState('')
  const [packCaption, setPackCaption] = useState('')

  const brandId = selectedBrandId

  async function load() {
    if (!brandId) {
      setTemplates([])
      setPacks([])
      return
    }
    setError('')
    try {
      const [tpls, media] = await Promise.all([
        smmService.listTemplates(brandId),
        smmService.listMediaPacks(brandId),
      ])
      setTemplates(tpls)
      setPacks(media)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  useEffect(() => {
    void load()
  }, [brandId])

  useEffect(() => {
    if (kind !== 'utm' || !utmBase.trim()) {
      setUtmPreview('')
      return
    }
    let cancelled = false
    const params: Record<string, string> = {}
    if (utmSource.trim()) params.utm_source = utmSource.trim()
    if (utmMedium.trim()) params.utm_medium = utmMedium.trim()
    if (utmCampaign.trim()) params.utm_campaign = utmCampaign.trim()
    void smmService
      .buildUtmUrl(utmBase.trim(), params)
      .then((r) => {
        if (!cancelled) setUtmPreview(r.url)
      })
      .catch(() => {
        if (!cancelled) setUtmPreview('')
      })
    return () => {
      cancelled = true
    }
  }, [kind, utmBase, utmSource, utmMedium, utmCampaign])

  async function handleCreateTemplate(e: FormEvent) {
    e.preventDefault()
    if (!brandId || !title.trim()) return
    setBusy(true)
    setError('')
    setSuccess('')
    try {
      const metadata: Record<string, unknown> = {}
      let bodyVal = body
      if (kind === 'utm') {
        metadata.base_url = utmBase.trim() || body.trim()
        metadata.params = {
          ...(utmSource.trim() ? { utm_source: utmSource.trim() } : {}),
          ...(utmMedium.trim() ? { utm_medium: utmMedium.trim() } : {}),
          ...(utmCampaign.trim() ? { utm_campaign: utmCampaign.trim() } : {}),
        }
        bodyVal = utmPreview || metadata.base_url as string
      }
      if (kind === 'cta') {
        metadata.networks = ['tg', 'vk']
      }
      await smmService.createTemplate(brandId, {
        kind,
        title: title.trim(),
        body: bodyVal,
        metadata,
      })
      setTitle('')
      setBody('')
      setUtmBase('')
      setUtmSource('')
      setUtmMedium('')
      setUtmCampaign('')
      setSuccess('Шаблон сохранён')
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function handleCreatePack(e: FormEvent) {
    e.preventDefault()
    if (!brandId || !packTitle.trim()) return
    setBusy(true)
    setError('')
    setSuccess('')
    try {
      const keys = packKeys
        .split(/[\n,]+/)
        .map((s) => s.trim())
        .filter(Boolean)
      await smmService.createMediaPack(brandId, {
        title: packTitle.trim(),
        object_keys: keys,
        caption: packCaption.trim() || undefined,
      })
      setPackTitle('')
      setPackKeys('')
      setPackCaption('')
      setSuccess('Медиа-пакет сохранён')
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function removeTemplate(id: number) {
    try {
      await smmService.deleteTemplate(id)
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function removePack(id: number) {
    try {
      await smmService.deleteMediaPack(id)
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Library"
        description="Шаблоны промптов, CTA/UTM и медиа-пакеты бренда"
      />
      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      {!brandId && (
        <Alert variant="error">
          Выберите бренд в шапке или создайте на{' '}
          <Link to="/brands" className="underline">
            Brands
          </Link>
        </Alert>
      )}

      {brandId && (
        <>
          <p className="text-sm text-[var(--text-muted)] mb-4">
            Бренд:{' '}
            <span className="text-[var(--text-primary)]">
              {selectedBrand?.name || brands.find((b) => b.id === brandId)?.name || brandId}
            </span>
            {' · '}
            <Link to="/posts" className="text-primary-400 hover:underline">
              Вставить в пост
            </Link>
          </p>

          <div className="flex gap-2 mb-4">
            <Button
              variant={tab === 'templates' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setTab('templates')}
            >
              Templates
            </Button>
            <Button
              variant={tab === 'media' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setTab('media')}
            >
              Media packs
            </Button>
          </div>

          {tab === 'templates' && (
            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Новый шаблон</CardTitle>
                  <CardDescription>prompt · CTA · UTM · текст поста</CardDescription>
                </CardHeader>
                <CardContent>
                  <form className="space-y-3" onSubmit={(e) => void handleCreateTemplate(e)}>
                    <div>
                      <label className="text-sm text-[var(--text-secondary)] block mb-1">Тип</label>
                      <select
                        className="w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-tertiary)] px-3 py-2 text-sm"
                        value={kind}
                        onChange={(e) => setKind(e.target.value as TemplateKind)}
                      >
                        {KINDS.map((k) => (
                          <option key={k.id} value={k.id}>
                            {k.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <Input
                      label="Название"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="Например: CTA подписаться"
                      required
                    />
                    {kind === 'utm' ? (
                      <>
                        <Input
                          label="Base URL"
                          value={utmBase}
                          onChange={(e) => setUtmBase(e.target.value)}
                          placeholder="https://example.com/landing"
                          required
                        />
                        <div className="grid grid-cols-3 gap-2">
                          <Input
                            label="utm_source"
                            value={utmSource}
                            onChange={(e) => setUtmSource(e.target.value)}
                          />
                          <Input
                            label="utm_medium"
                            value={utmMedium}
                            onChange={(e) => setUtmMedium(e.target.value)}
                          />
                          <Input
                            label="utm_campaign"
                            value={utmCampaign}
                            onChange={(e) => setUtmCampaign(e.target.value)}
                          />
                        </div>
                        {utmPreview && (
                          <p className="text-xs text-[var(--text-muted)] break-all">
                            Preview: {utmPreview}
                          </p>
                        )}
                      </>
                    ) : (
                      <div>
                        <label className="text-sm text-[var(--text-secondary)] block mb-1">
                          {kind === 'prompt' ? 'Текст промпта' : 'Текст'}
                        </label>
                        <textarea
                          className="w-full min-h-[100px] rounded-md border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-2 text-sm"
                          value={body}
                          onChange={(e) => setBody(e.target.value)}
                          placeholder={
                            kind === 'cta'
                              ? 'Подписывайтесь на канал →'
                              : kind === 'prompt'
                                ? 'Перепиши короче, сохрани факты'
                                : 'Текст evergreen-поста'
                          }
                        />
                      </div>
                    )}
                    <Button type="submit" disabled={busy || !title.trim()}>
                      Сохранить
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Сохранённые ({templates.length})</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 max-h-[480px] overflow-y-auto">
                  {templates.length === 0 && (
                    <p className="text-sm text-[var(--text-muted)]">Пока пусто</p>
                  )}
                  {templates.map((t) => (
                    <div
                      key={t.id}
                      className="flex items-start justify-between gap-2 border-b border-[var(--border-color)] py-2"
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{t.title}</p>
                        <p className="text-[10px] uppercase text-[var(--text-muted)]">{t.kind}</p>
                        <p className="text-xs text-[var(--text-muted)] line-clamp-2 mt-0.5">
                          {t.body || JSON.stringify(t.metadata)}
                        </p>
                      </div>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => void removeTemplate(t.id)}
                      >
                        Удалить
                      </Button>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          )}

          {tab === 'media' && (
            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Новый медиа-пакет</CardTitle>
                  <CardDescription>
                    Object keys / URL из MinIO uploads (по одному на строку)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form className="space-y-3" onSubmit={(e) => void handleCreatePack(e)}>
                    <Input
                      label="Название"
                      value={packTitle}
                      onChange={(e) => setPackTitle(e.target.value)}
                      required
                    />
                    <div>
                      <label className="text-sm text-[var(--text-secondary)] block mb-1">
                        Object keys
                      </label>
                      <textarea
                        className="w-full min-h-[80px] rounded-md border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-2 text-sm font-mono"
                        value={packKeys}
                        onChange={(e) => setPackKeys(e.target.value)}
                        placeholder="/uploads/tg/photo1.jpg"
                      />
                    </div>
                    <Input
                      label="Caption (опц.)"
                      value={packCaption}
                      onChange={(e) => setPackCaption(e.target.value)}
                    />
                    <Button type="submit" disabled={busy || !packTitle.trim()}>
                      Сохранить
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Пакеты ({packs.length})</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 max-h-[480px] overflow-y-auto">
                  {packs.length === 0 && (
                    <p className="text-sm text-[var(--text-muted)]">Пока пусто</p>
                  )}
                  {packs.map((p) => (
                    <div
                      key={p.id}
                      className="flex items-start justify-between gap-2 border-b border-[var(--border-color)] py-2"
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{p.title}</p>
                        <p className="text-xs text-[var(--text-muted)]">
                          {p.object_keys.length} файл(ов)
                          {p.caption ? ` · ${p.caption.slice(0, 60)}` : ''}
                        </p>
                      </div>
                      <Button size="sm" variant="secondary" onClick={() => void removePack(p.id)}>
                        Удалить
                      </Button>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          )}
        </>
      )}
    </PageContainer>
  )
}
