import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import { getErrorMessage } from '@/services/api-client'
import type { Brand, BrandPromptSnippet } from '@/types/smm'

const MAX_SNIPPETS = 5

function emptySnippet(): BrandPromptSnippet {
  return { title: '', text: '' }
}

export function hasBrandVoice(brand: Pick<Brand, 'tone_of_voice' | 'style_notes' | 'prompt_snippets'>): boolean {
  if (brand.tone_of_voice?.trim() || brand.style_notes?.trim()) return true
  return (brand.prompt_snippets ?? []).some((snippet) => snippet.title?.trim() || snippet.text?.trim())
}

function voiceSnapshot(brand: Brand | null): string {
  if (!brand) return ''
  return [
    brand.id,
    brand.tone_of_voice ?? '',
    brand.style_notes ?? '',
    JSON.stringify(brand.prompt_snippets ?? []),
  ].join('|')
}

interface BrandVoiceEditorProps {
  brandId: number
}

export function BrandVoiceEditor({ brandId }: BrandVoiceEditorProps) {
  const { brands, refreshBrands } = useBrand()
  const brand = useMemo(
    () => brands.find((item) => item.id === brandId) ?? null,
    [brands, brandId],
  )
  const snapshot = voiceSnapshot(brand)
  const brandRef = useRef(brand)
  brandRef.current = brand

  const [isOpen, setIsOpen] = useState(false)
  const [editTone, setEditTone] = useState('')
  const [editNotes, setEditNotes] = useState('')
  const [editSnippets, setEditSnippets] = useState<BrandPromptSnippet[]>([])
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    setError('')
    setSuccess('')
  }, [brandId])

  useEffect(() => {
    const current = brandRef.current
    if (!current) {
      setEditTone('')
      setEditNotes('')
      setEditSnippets([])
      return
    }
    setEditTone(current.tone_of_voice || '')
    setEditNotes(current.style_notes || '')
    setEditSnippets(
      current.prompt_snippets?.length
        ? current.prompt_snippets.map((snippet) => ({
            title: snippet.title || '',
            text: snippet.text || '',
          }))
        : [],
    )
  }, [snapshot])

  if (!brand) return null

  const summary = [brand.tone_of_voice, brand.style_notes].filter(Boolean).join(' · ')
  const snippetCount = (brand.prompt_snippets ?? []).filter((snippet) => snippet.text?.trim()).length

  async function handleSave(event: FormEvent) {
    event.preventDefault()
    setIsSaving(true)
    setError('')
    setSuccess('')
    try {
      const snippets = editSnippets
        .map((snippet) => ({
          title: snippet.title.trim().slice(0, 80),
          text: snippet.text.trim().slice(0, 500),
        }))
        .filter((snippet) => snippet.title || snippet.text)
        .slice(0, MAX_SNIPPETS)
      await smmService.updateBrand(brandId, {
        tone_of_voice: editTone.trim() || null,
        style_notes: editNotes.trim() || null,
        prompt_snippets: snippets,
      })
      await refreshBrands()
      setSuccess('Голос бренда сохранён')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)]/40 p-2.5 space-y-2">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-xs font-medium text-[var(--text-primary)]">Голос бренда</p>
          <p className="text-[11px] text-[var(--text-muted)] truncate">
            {summary
              ? summary
              : 'Не задан. Пустой тон в переписывании возьмёт этот голос.'}
            {snippetCount > 0 ? ` · шаблонов: ${snippetCount}` : ''}
          </p>
        </div>
        <Button type="button" size="sm" variant="ghost" onClick={() => setIsOpen((open) => !open)}>
          {isOpen ? 'Скрыть' : hasBrandVoice(brand) ? 'Изменить' : 'Задать'}
        </Button>
      </div>

      {isOpen && (
        <form onSubmit={handleSave} className="space-y-3">
          <p className="text-[11px] text-[var(--text-muted)]">
            Подставляется в переписывание и адаптацию, если тон для этого запуска не задан вручную.
          </p>
          <div>
            <label className="text-xs text-[var(--text-secondary)]">
              Tone of voice ({editTone.length}/500)
            </label>
            <textarea
              className="mt-1 w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] p-2 text-sm min-h-[72px]"
              value={editTone}
              maxLength={500}
              placeholder="Например: дружелюбный, экспертный, без канцелярита"
              onChange={(event) => setEditTone(event.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-[var(--text-secondary)]">
              Style notes ({editNotes.length}/1000)
            </label>
            <textarea
              className="mt-1 w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] p-2 text-sm min-h-[56px]"
              value={editNotes}
              maxLength={1000}
              placeholder="Не используем эмодзи; обращение на «вы»; CTA в конце"
              onChange={(event) => setEditNotes(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs text-[var(--text-secondary)]">
                Prompt snippets ({editSnippets.length}/{MAX_SNIPPETS})
              </p>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                disabled={editSnippets.length >= MAX_SNIPPETS}
                onClick={() => setEditSnippets((prev) => [...prev, emptySnippet()])}
              >
                + Snippet
              </Button>
            </div>
            {editSnippets.map((snippet, idx) => (
              <div
                key={idx}
                className="rounded-lg border border-[var(--border-color)] p-3 space-y-2"
              >
                <div className="flex gap-2">
                  <Input
                    label="Название"
                    value={snippet.title}
                    onChange={(event) =>
                      setEditSnippets((prev) =>
                        prev.map((item, index) =>
                          index === idx ? { ...item, title: event.target.value } : item,
                        ),
                      )
                    }
                  />
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    className="self-end"
                    onClick={() => setEditSnippets((prev) => prev.filter((_, index) => index !== idx))}
                  >
                    Удалить
                  </Button>
                </div>
                <textarea
                  className="w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] p-2 text-sm min-h-[48px]"
                  value={snippet.text}
                  maxLength={500}
                  placeholder="Текст уточнения для AI…"
                  onChange={(event) =>
                    setEditSnippets((prev) =>
                      prev.map((item, index) =>
                        index === idx ? { ...item, text: event.target.value } : item,
                      ),
                    )
                  }
                />
              </div>
            ))}
          </div>
          {error && <Alert variant="error">{error}</Alert>}
          {success && <Alert variant="success">{success}</Alert>}
          <Button type="submit" size="sm" disabled={isSaving}>
            {isSaving ? 'Saving…' : 'Сохранить голос'}
          </Button>
        </form>
      )}
    </div>
  )
}
