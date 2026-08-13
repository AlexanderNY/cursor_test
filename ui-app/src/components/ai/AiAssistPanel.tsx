import { useEffect, useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { smmService } from '@/services/smm-service'
import { getErrorMessage } from '@/services/api-client'
import type {
  AiAssistAction,
  AiAssistActionId,
  AiProcessResponse,
  AiProcessResult,
} from '@/types/smm'

const NOTE_MAX = 300
const DEFAULT_CATEGORIES = ['новости', 'реклама', 'технологии', 'финансы', 'другое']

export interface AiAssistPanelProps {
  sourceText: string
  source?: 'inbox' | 'post'
  sourceId?: number
  /** Prefill / restrict visible actions */
  allowedActions?: AiAssistActionId[]
  defaultAction?: AiAssistActionId
  defaultNetwork?: string
  applyTargets?: { id: string; label: string }[]
  defaultApplyTarget?: string
  onApply: (text: string, meta: { action: AiAssistActionId; result: AiProcessResult; target?: string }) => void
  className?: string
}

function resultDisplayText(result: AiProcessResult, action: AiAssistActionId): string {
  if (action === 'categorize') {
    const conf =
      typeof result.confidence === 'number' ? ` (${Math.round(result.confidence * 100)}%)` : ''
    return `${result.category || result.text || ''}${conf}`
  }
  return result.text || ''
}

export function AiAssistPanel({
  sourceText,
  source,
  sourceId,
  allowedActions,
  defaultAction,
  defaultNetwork,
  applyTargets,
  defaultApplyTarget,
  onApply,
  className = '',
}: AiAssistPanelProps) {
  const [actions, setActions] = useState<AiAssistAction[]>([])
  const [actionId, setActionId] = useState<AiAssistActionId>(defaultAction || 'summarize')
  const [note, setNote] = useState('')
  const [tone, setTone] = useState('')
  const [maxLen, setMaxLen] = useState(500)
  const [categoriesText, setCategoriesText] = useState(DEFAULT_CATEGORIES.join(', '))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [response, setResponse] = useState<AiProcessResponse | null>(null)
  const [applyTarget, setApplyTarget] = useState(defaultApplyTarget || applyTargets?.[0]?.id || '')
  const [sourceExpanded, setSourceExpanded] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const list = await smmService.getAiActions()
        if (cancelled) return
        const filtered = allowedActions?.length
          ? list.filter((a) => allowedActions.includes(a.id))
          : list
        setActions(filtered)
        const preferred =
          (defaultAction && filtered.find((a) => a.id === defaultAction)?.id) ||
          filtered[0]?.id ||
          'summarize'
        setActionId(preferred)
      } catch {
        if (!cancelled) {
          const fallback: AiAssistAction[] = [
            { id: 'summarize', title: 'Саммари', description: 'Сократи текст', params: ['max_len', 'note'] },
            { id: 'categorize', title: 'Категория', description: 'Классификация', params: ['categories', 'note'] },
            { id: 'rewrite', title: 'Переписать', description: 'Переписать текст', params: ['tone', 'note'] },
            {
              id: 'reply_draft',
              title: 'Черновик ответа',
              description: 'Ответ на сообщение',
              params: ['tone', 'note'],
            },
          ]
          const filtered = allowedActions?.length
            ? fallback.filter((a) => allowedActions.includes(a.id))
            : fallback
          setActions(filtered)
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [allowedActions, defaultAction])

  const selected = useMemo(
    () => actions.find((a) => a.id === actionId) || actions[0],
    [actions, actionId],
  )

  async function handleGenerate() {
    const text = sourceText.trim()
    if (!text) {
      setError('Нет текста для обработки')
      return
    }
    setError('')
    setBusy(true)
    try {
      const categories = categoriesText
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
      const res = await smmService.aiProcess({
        action: actionId,
        text,
        source,
        source_id: sourceId,
        params: {
          note: note.trim() || undefined,
          tone: tone.trim() || undefined,
          network: defaultNetwork,
          max_len: actionId === 'summarize' ? maxLen : undefined,
          categories: actionId === 'categorize' ? categories : undefined,
        },
      })
      setResponse(res)
    } catch (err) {
      setResponse(null)
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function copyResult() {
    if (!response) return
    const text = resultDisplayText(response.result, response.action)
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      setError('Не удалось скопировать в буфер')
    }
  }

  const preview = sourceText.trim()
  const previewShort = preview.length > 160 ? `${preview.slice(0, 160)}…` : preview

  return (
    <div
      className={`rounded-xl border border-[var(--border-color)] bg-[var(--bg-tertiary)]/50 p-3 space-y-3 ${className}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-sm font-medium text-[var(--text-primary)]">AI помощник</h4>
        {selected && (
          <span className="text-xs text-[var(--text-muted)]">{selected.description}</span>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5">
        {actions.map((a) => (
          <button
            key={a.id}
            type="button"
            className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${
              actionId === a.id
                ? 'border-primary-500/60 bg-primary-500/15 text-[var(--text-primary)]'
                : 'border-[var(--border-color)] text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]'
            }`}
            onClick={() => {
              setActionId(a.id)
              setResponse(null)
            }}
          >
            {a.title}
          </button>
        ))}
      </div>

      {(actionId === 'rewrite' || actionId === 'reply_draft') && (
        <div>
          <label className="text-xs text-[var(--text-secondary)]">Тон (опционально)</label>
          <input
            className="mt-1 w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1.5 text-sm"
            value={tone}
            maxLength={80}
            placeholder={actionId === 'reply_draft' ? 'живой, короткий…' : 'деловой, дружелюбный…'}
            onChange={(e) => setTone(e.target.value)}
          />
        </div>
      )}

      {actionId === 'summarize' && (
        <div>
          <label className="text-xs text-[var(--text-secondary)]">Макс. длина</label>
          <input
            type="number"
            min={50}
            max={2000}
            className="mt-1 w-28 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1.5 text-sm"
            value={maxLen}
            onChange={(e) => setMaxLen(Number(e.target.value) || 500)}
          />
        </div>
      )}

      {actionId === 'categorize' && (
        <div>
          <label className="text-xs text-[var(--text-secondary)]">Категории (через запятую)</label>
          <input
            className="mt-1 w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1.5 text-sm"
            value={categoriesText}
            onChange={(e) => setCategoriesText(e.target.value)}
          />
        </div>
      )}

      <div>
        <div className="flex items-center justify-between gap-2">
          <label className="text-xs text-[var(--text-secondary)]">Уточнение (необязательно)</label>
          <span className="text-[10px] text-[var(--text-muted)]">
            {note.length}/{NOTE_MAX}
          </span>
        </div>
        <textarea
          className="mt-1 w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] p-2 text-sm min-h-[56px]"
          value={note}
          maxLength={NOTE_MAX}
          placeholder="Например: выдели только факты про даты"
          onChange={(e) => setNote(e.target.value)}
        />
      </div>

      <Button
        type="button"
        size="sm"
        disabled={busy || !preview}
        isLoading={busy}
        onClick={() => void handleGenerate()}
      >
        {busy ? 'Генерация…' : 'Сгенерировать'}
      </Button>

      {error && <Alert variant="error">{error}</Alert>}

      {response && (
        <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] p-3 space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-[var(--text-muted)]">
            <span>AI результат · {response.model} · {response.latency_ms} ms</span>
            <button
              type="button"
              className="underline hover:text-[var(--text-primary)]"
              onClick={() => setSourceExpanded((v) => !v)}
            >
              {sourceExpanded ? 'Скрыть исходный' : 'Исходный текст'}
            </button>
          </div>
          {sourceExpanded ? (
            <p className="text-xs whitespace-pre-wrap text-[var(--text-muted)] border-b border-[var(--border-color)] pb-2">
              {preview}
            </p>
          ) : (
            <p className="text-xs text-[var(--text-muted)]">{previewShort}</p>
          )}
          <div className="whitespace-pre-wrap text-sm text-[var(--text-primary)] min-h-[48px]">
            {resultDisplayText(response.result, response.action)}
          </div>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {applyTargets && applyTargets.length > 1 && (
              <select
                className="rounded-md border border-[var(--border-color)] bg-[var(--bg-tertiary)] px-2 py-1 text-xs"
                value={applyTarget}
                onChange={(e) => setApplyTarget(e.target.value)}
              >
                {applyTargets.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.label}
                  </option>
                ))}
              </select>
            )}
            <Button
              type="button"
              size="sm"
              onClick={() =>
                onApply(resultDisplayText(response.result, response.action), {
                  action: response.action,
                  result: response.result,
                  target: applyTarget || undefined,
                })
              }
            >
              Применить
            </Button>
            <Button type="button" size="sm" variant="secondary" onClick={() => void copyResult()}>
              В буфер
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => {
                setResponse(null)
                setError('')
              }}
            >
              Закрыть
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
