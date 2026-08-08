import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { guideService, type GuideBlock, type GuideBlockStyle } from '@/services/guide-service'
import { getErrorMessage } from '@/services/api-client'
import { renderGuideMarkdown, styleToCss, titleStyle, subtitleStyle, bodyStyle } from '@/lib/guide-render'

const STYLE_FIELDS: { key: keyof GuideBlockStyle; label: string; placeholder: string }[] = [
  { key: 'titleColor', label: 'Цвет заголовка', placeholder: '#e2e8f0' },
  { key: 'subtitleColor', label: 'Цвет подзаголовка', placeholder: '#94a3b8' },
  { key: 'textColor', label: 'Цвет текста', placeholder: '#cbd5e1' },
  { key: 'backgroundColor', label: 'Фон блока', placeholder: '#1e293b' },
  { key: 'borderColor', label: 'Цвет рамки', placeholder: '#334155' },
  { key: 'borderRadius', label: 'Скругление', placeholder: '12px' },
  { key: 'padding', label: 'Внутренний отступ', placeholder: '16px' },
  { key: 'titleFontSize', label: 'Размер заголовка', placeholder: '1.25rem' },
  { key: 'bodyFontSize', label: 'Размер текста', placeholder: '14px' },
  { key: 'titleFontWeight', label: 'Насыщенность заголовка', placeholder: '600' },
]

const emptyDraft = (): Partial<GuideBlock> & { slug: string; style: GuideBlockStyle } => ({
  slug: '',
  toc_label: '',
  title: '',
  subtitle: '',
  body: '',
  sort_order: 100,
  is_visible: true,
  style: {},
})

export function GuideBlocksAdmin() {
  const [blocks, setBlocks] = useState<GuideBlock[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [draft, setDraft] = useState(emptyDraft())
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [creating, setCreating] = useState(false)

  async function load() {
    setLoading(true)
    setError('')
    try {
      const list = await guideService.listAdmin()
      setBlocks(list)
      if (selectedId != null) {
        const found = list.find((b) => b.id === selectedId)
        if (found) selectBlock(found)
      }
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  function selectBlock(b: GuideBlock) {
    setCreating(false)
    setSelectedId(b.id)
    setDraft({
      slug: b.slug,
      toc_label: b.toc_label,
      title: b.title,
      subtitle: b.subtitle,
      body: b.body,
      sort_order: b.sort_order,
      is_visible: b.is_visible,
      style: { ...(b.style || {}) },
    })
    setSuccess('')
  }

  function startCreate() {
    setCreating(true)
    setSelectedId(null)
    setDraft(emptyDraft())
    setSuccess('')
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      if (creating) {
        if (!draft.slug?.trim()) {
          setError('Укажите slug')
          return
        }
        const created = await guideService.create({
          slug: draft.slug.trim(),
          toc_label: draft.toc_label || '',
          title: draft.title || '',
          subtitle: draft.subtitle || '',
          body: draft.body || '',
          sort_order: Number(draft.sort_order) || 0,
          is_visible: draft.is_visible !== false,
          style: draft.style || {},
        })
        setSuccess('Блок создан')
        await load()
        selectBlock(created)
      } else if (selectedId != null) {
        const updated = await guideService.update(selectedId, {
          slug: draft.slug,
          toc_label: draft.toc_label,
          title: draft.title,
          subtitle: draft.subtitle,
          body: draft.body,
          sort_order: Number(draft.sort_order) || 0,
          is_visible: draft.is_visible !== false,
          style: draft.style || {},
        })
        setSuccess('Сохранено')
        await load()
        selectBlock(updated)
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (selectedId == null) return
    if (!confirm('Удалить блок?')) return
    setError('')
    try {
      await guideService.remove(selectedId)
      setSelectedId(null)
      setDraft(emptyDraft())
      setSuccess('Удалено')
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function handleSeed() {
    setError('')
    try {
      const list = await guideService.seed()
      setBlocks(list)
      setSuccess('Дефолтные блоки добавлены (существующие slug не перезаписаны)')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  function setStyleField(key: keyof GuideBlockStyle, value: string) {
    setDraft((prev) => ({
      ...prev,
      style: { ...(prev.style || {}), [key]: value },
    }))
  }

  const previewStyle = draft.style || {}

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle>Справка (блоки /about)</CardTitle>
        <CardDescription>
          Редактирование текста и стиля блоков публичной справки. Markdown: абзацы, списки (- / 1.),{' '}
          <code>### заголовок</code>, <code>**жирный**</code>.{' '}
          <Link to="/about" className="text-primary-400 hover:underline" target="_blank" rel="noreferrer">
            Открыть /about
          </Link>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <Alert variant="error">{error}</Alert>}
        {success && <Alert variant="success">{success}</Alert>}

        <div className="flex flex-wrap gap-2">
          <Button type="button" size="sm" variant="secondary" onClick={() => void load()} disabled={loading}>
            Обновить
          </Button>
          <Button type="button" size="sm" onClick={startCreate}>
            Новый блок
          </Button>
          <Button type="button" size="sm" variant="secondary" onClick={() => void handleSeed()}>
            Seed defaults
          </Button>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-2">
            <p className="text-sm text-[var(--text-muted)]">Блоки</p>
            {loading && <p className="text-sm text-[var(--text-muted)]">Загрузка…</p>}
            <ul className="space-y-1 max-h-[480px] overflow-y-auto">
              {blocks.map((b) => (
                <li key={b.id}>
                  <button
                    type="button"
                    onClick={() => selectBlock(b)}
                    className={`w-full text-left rounded-lg border px-3 py-2 text-sm transition-colors ${
                      selectedId === b.id && !creating
                        ? 'border-primary-500 bg-primary-500/10'
                        : 'border-[var(--border-color)] hover:bg-[var(--bg-tertiary)]'
                    }`}
                  >
                    <span className="font-medium">{b.title || b.slug}</span>
                    <span className="block text-xs text-[var(--text-muted)]">
                      #{b.sort_order} · {b.slug}
                      {!b.is_visible ? ' · скрыт' : ''}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <form onSubmit={handleSave} className="lg:col-span-2 space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <Input
                label="Slug (id секции)"
                value={draft.slug || ''}
                onChange={(e) => setDraft((p) => ({ ...p, slug: e.target.value }))}
                required
              />
              <Input
                label="Метка в оглавлении"
                value={draft.toc_label || ''}
                onChange={(e) => setDraft((p) => ({ ...p, toc_label: e.target.value }))}
              />
              <Input
                label="Заголовок"
                value={draft.title || ''}
                onChange={(e) => setDraft((p) => ({ ...p, title: e.target.value }))}
              />
              <Input
                label="Порядок"
                type="number"
                value={draft.sort_order ?? 0}
                onChange={(e) => setDraft((p) => ({ ...p, sort_order: Number(e.target.value) }))}
              />
            </div>
            <Input
              label="Подзаголовок"
              value={draft.subtitle || ''}
              onChange={(e) => setDraft((p) => ({ ...p, subtitle: e.target.value }))}
            />
            <div>
              <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">Текст (body)</label>
              <textarea
                value={draft.body || ''}
                onChange={(e) => setDraft((p) => ({ ...p, body: e.target.value }))}
                rows={12}
                className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={draft.is_visible !== false}
                onChange={(e) => setDraft((p) => ({ ...p, is_visible: e.target.checked }))}
              />
              Видимый на /about
            </label>

            <div>
              <p className="text-sm font-medium text-[var(--text-secondary)] mb-2">Стиль блока</p>
              <div className="grid gap-3 sm:grid-cols-2">
                {STYLE_FIELDS.map((f) => (
                  <div key={f.key} className="flex items-end gap-2">
                    <div className="flex-1">
                      <Input
                        label={f.label}
                        value={(draft.style?.[f.key] as string) || ''}
                        placeholder={f.placeholder}
                        onChange={(e) => setStyleField(f.key, e.target.value)}
                      />
                    </div>
                    {f.key.toLowerCase().includes('color') && (
                      <input
                        type="color"
                        className="h-10 w-10 rounded border border-[var(--border-color)] bg-transparent cursor-pointer mb-0.5"
                        value={
                          /^#[0-9a-fA-F]{6}$/.test((draft.style?.[f.key] as string) || '')
                            ? (draft.style?.[f.key] as string)
                            : '#64748b'
                        }
                        onChange={(e) => setStyleField(f.key, e.target.value)}
                        title="Палитра"
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={saving || (!creating && selectedId == null)}>
                {saving ? 'Сохранение…' : creating ? 'Создать' : 'Сохранить'}
              </Button>
              {!creating && selectedId != null && (
                <Button type="button" variant="danger" onClick={() => void handleDelete()}>
                  Удалить
                </Button>
              )}
            </div>

            <div>
              <p className="text-sm text-[var(--text-muted)] mb-2">Превью</p>
              <div
                className="rounded-xl border border-[var(--border-color)] p-4 bg-[var(--bg-secondary)]/40"
                style={styleToCss(previewStyle)}
              >
                <h3 className="text-lg mb-1" style={titleStyle(previewStyle)}>
                  {draft.title || 'Заголовок'}
                </h3>
                {draft.subtitle ? (
                  <p className="text-sm mb-3 opacity-80" style={subtitleStyle(previewStyle)}>
                    {draft.subtitle}
                  </p>
                ) : null}
                <div className="text-sm" style={bodyStyle(previewStyle)}>
                  {renderGuideMarkdown(draft.body || '_пустой body_', previewStyle.textColor)}
                </div>
              </div>
            </div>
          </form>
        </div>
      </CardContent>
    </Card>
  )
}
