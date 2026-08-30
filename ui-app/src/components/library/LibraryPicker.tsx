import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { smmService } from '@/services/smm-service'
import { getErrorMessage } from '@/services/api-client'
import type { ContentTemplate, MediaPack, TemplateKind } from '@/types/smm'

const KIND_LABEL: Record<TemplateKind, string> = {
  prompt: 'Prompt',
  cta: 'CTA',
  utm: 'UTM',
  post_body: 'Текст',
}

export interface LibraryPickerProps {
  brandId: number | null | undefined
  onApplyText: (text: string, meta: { kind: TemplateKind; mode: string; title: string }) => void
  onApplyPrompt?: (note: string, title: string) => void
  onApplyMedia?: (keys: string[], caption?: string | null) => void
  className?: string
  /** Limit template kinds shown */
  kinds?: TemplateKind[]
}

export function LibraryPicker({
  brandId,
  onApplyText,
  onApplyPrompt,
  onApplyMedia,
  className = '',
  kinds,
}: LibraryPickerProps) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState<'templates' | 'media'>('templates')
  const [templates, setTemplates] = useState<ContentTemplate[]>([])
  const [packs, setPacks] = useState<MediaPack[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open || !brandId) return
    let cancelled = false
    ;(async () => {
      setBusy(true)
      setError('')
      try {
        const [tpls, media] = await Promise.all([
          smmService.listTemplates(brandId),
          smmService.listMediaPacks(brandId),
        ])
        if (cancelled) return
        setTemplates(
          kinds?.length ? tpls.filter((t) => kinds.includes(t.kind)) : tpls,
        )
        setPacks(media)
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err))
      } finally {
        if (!cancelled) setBusy(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [open, brandId, kinds])

  async function handleTemplate(t: ContentTemplate) {
    setBusy(true)
    setError('')
    try {
      const res = await smmService.applyTemplate(t.id)
      if (res.applied.mode === 'prompt') {
        onApplyPrompt?.(res.applied.prompt_note || res.text, t.title)
      } else {
        onApplyText(res.text, {
          kind: res.applied.kind,
          mode: res.applied.mode,
          title: t.title,
        })
      }
      setOpen(false)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  function handlePack(p: MediaPack) {
    onApplyMedia?.(p.object_keys, p.caption)
    setOpen(false)
  }

  if (!brandId) {
    return (
      <p className={`text-xs text-[var(--text-muted)] ${className}`}>
        Выберите бренд, чтобы открыть библиотеку
      </p>
    )
  }

  return (
    <div className={className}>
      <Button type="button" size="sm" variant="secondary" onClick={() => setOpen((v) => !v)}>
        {open ? 'Скрыть библиотеку' : 'Из библиотеки'}
      </Button>
      {open && (
        <div className="mt-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] p-3 space-y-2">
          <div className="flex gap-2 text-xs">
            <button
              type="button"
              className={tab === 'templates' ? 'underline font-medium' : 'text-[var(--text-muted)]'}
              onClick={() => setTab('templates')}
            >
              Шаблоны
            </button>
            <button
              type="button"
              className={tab === 'media' ? 'underline font-medium' : 'text-[var(--text-muted)]'}
              onClick={() => setTab('media')}
            >
              Медиа
            </button>
          </div>
          {error && <p className="text-xs text-red-400">{error}</p>}
          {busy && <p className="text-xs text-[var(--text-muted)]">Загрузка…</p>}
          {tab === 'templates' && (
            <ul className="max-h-40 overflow-y-auto space-y-1">
              {templates.length === 0 && !busy && (
                <li className="text-xs text-[var(--text-muted)]">Нет шаблонов</li>
              )}
              {templates.map((t) => (
                <li key={t.id}>
                  <button
                    type="button"
                    disabled={busy}
                    className="w-full text-left text-sm rounded px-2 py-1.5 hover:bg-[var(--bg-tertiary)] flex justify-between gap-2"
                    onClick={() => void handleTemplate(t)}
                  >
                    <span className="truncate">{t.title}</span>
                    <span className="text-[10px] uppercase text-[var(--text-muted)] shrink-0">
                      {KIND_LABEL[t.kind] || t.kind}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {tab === 'media' && (
            <ul className="max-h-40 overflow-y-auto space-y-1">
              {packs.length === 0 && !busy && (
                <li className="text-xs text-[var(--text-muted)]">Нет медиа-пакетов</li>
              )}
              {packs.map((p) => (
                <li key={p.id}>
                  <button
                    type="button"
                    disabled={busy || !onApplyMedia}
                    className="w-full text-left text-sm rounded px-2 py-1.5 hover:bg-[var(--bg-tertiary)] flex justify-between gap-2"
                    onClick={() => handlePack(p)}
                  >
                    <span className="truncate">{p.title}</span>
                    <span className="text-[10px] text-[var(--text-muted)] shrink-0">
                      {p.object_keys.length} файлов
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
