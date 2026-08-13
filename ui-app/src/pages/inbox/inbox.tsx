import { FormEvent, KeyboardEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { AiAssistPanel } from '@/components/ai/AiAssistPanel'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import type { InboxItem, InboxStatus } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'
import { formatDateTime } from '@/utils/date'

const DEFAULT_SNIPPETS = [
  'Спасибо!',
  'Сейчас гляну…',
  'Отличный вопрос!',
  'Напишите в ЛС — разберёмся',
  'Уже в работе',
  'Да, всё верно',
  'Хорошая идея, спасибо!',
]

const COMMENTS_POLL_MS = 20_000
const DEFAULT_POLL_MS = 12_000

function snippetsKey(brandId: number | null): string {
  return `smm_reply_snippets_${brandId ?? 'all'}`
}

function loadSnippets(brandId: number | null): string[] {
  try {
    const raw = localStorage.getItem(snippetsKey(brandId))
    if (!raw) return DEFAULT_SNIPPETS
    const parsed = JSON.parse(raw) as unknown
    if (Array.isArray(parsed) && parsed.every((x) => typeof x === 'string')) {
      return parsed.length > 0 ? parsed : DEFAULT_SNIPPETS
    }
  } catch {
    /* ignore */
  }
  return DEFAULT_SNIPPETS
}

function saveSnippets(brandId: number | null, list: string[]) {
  localStorage.setItem(snippetsKey(brandId), JSON.stringify(list.slice(0, 12)))
}

function formatAge(iso?: string | null): string {
  return formatDateTime(iso, '')
}

function channelLabel(
  item: InboxItem,
  ownChannels: { id: number; title?: string | null; external_id: string }[],
): string {
  if (!item.channel_id) return item.thread_id || ''
  const ch = ownChannels.find((c) => c.id === item.channel_id)
  return ch?.title || ch?.external_id || String(item.channel_id)
}

export function InboxPage() {
  const { brands, selectedBrandId, selectedBrand, ownChannels } = useBrand()
  const [searchParams, setSearchParams] = useSearchParams()
  const modeParam = searchParams.get('mode')
  const isCommentsMode = modeParam === 'comments' || modeParam === 'comment'

  const [items, setItems] = useState<InboxItem[]>([])
  const [selected, setSelected] = useState<InboxItem | null>(null)
  const [network, setNetwork] = useState('')
  const [status, setStatus] = useState('')
  const [reply, setReply] = useState('')
  const [editedText, setEditedText] = useState('')
  const [redirectIds, setRedirectIds] = useState<number[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [snippets, setSnippets] = useState<string[]>(() => loadSnippets(selectedBrandId))
  const [snippetEdit, setSnippetEdit] = useState('')
  const replyRef = useRef<HTMLTextAreaElement>(null)
  const knownIdsRef = useRef<Set<number>>(new Set())
  const notifyReadyRef = useRef(false)

  const typeFilter = isCommentsMode ? 'comment' : ''

  const pollMs = isCommentsMode ? COMMENTS_POLL_MS : DEFAULT_POLL_MS

  useEffect(() => {
    setSnippets(loadSnippets(selectedBrandId))
  }, [selectedBrandId])

  const brandColor = useCallback(
    (brandId?: number | null): string => {
      return brands.find((b) => b.id === brandId)?.color ?? '#64748b'
    },
    [brands],
  )

  const load = useCallback(
    async (opts?: { silent?: boolean }) => {
      if (!opts?.silent) setLoading(true)
      setError('')
      try {
        const res = await smmService.listInbox({
          brand_id: selectedBrandId ?? undefined,
          network: network || undefined,
          type: typeFilter || undefined,
          status: status || undefined,
          limit: 50,
        })
        const next = res.items
        if (notifyReadyRef.current && isCommentsMode) {
          const fresh = next.filter(
            (i) => i.status === 'new' && !knownIdsRef.current.has(i.id),
          )
          if (fresh.length > 0 && typeof Notification !== 'undefined') {
            if (Notification.permission === 'granted') {
              const first = fresh[0]
              new Notification('Новый комментарий', {
                body: `${first.author || 'Unknown'}: ${(first.text || '').slice(0, 120)}`,
                tag: `inbox-comment-${first.id}`,
              })
            }
          }
        }
        knownIdsRef.current = new Set(next.map((i) => i.id))
        notifyReadyRef.current = true
        setItems(next)
        setSelected((prev) => {
          if (!prev) return prev
          const updated = next.find((i) => i.id === prev.id)
          return updated ?? null
        })
      } catch (err) {
        setError(getErrorMessage(err))
      } finally {
        if (!opts?.silent) setLoading(false)
      }
    },
    [selectedBrandId, network, typeFilter, status, isCommentsMode],
  )

  useEffect(() => {
    void load()
    const t = setInterval(() => void load({ silent: true }), pollMs)
    return () => clearInterval(t)
  }, [load, pollMs])

  useEffect(() => {
    if (!isCommentsMode || !selected) return
    const id = window.setTimeout(() => replyRef.current?.focus(), 50)
    return () => clearTimeout(id)
  }, [isCommentsMode, selected?.id])

  function setMode(comments: boolean) {
    const next = new URLSearchParams(searchParams)
    if (comments) next.set('mode', 'comments')
    else next.delete('mode')
    setSearchParams(next, { replace: true })
  }

  async function ensureNotifyPermission() {
    if (typeof Notification === 'undefined') return
    if (Notification.permission === 'default') {
      await Notification.requestPermission()
    }
  }

  async function handleRead(item: InboxItem) {
    try {
      const updated = await smmService.markInboxRead(item.id)
      setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)))
      setSelected(updated)
      setEditedText(updated.edited_text || updated.text || '')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function handleArchive(item: InboxItem) {
    try {
      await smmService.archiveInbox(item.id)
      setItems((prev) => prev.filter((i) => i.id !== item.id))
      setSelected(null)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function handleReply() {
    if (!selected || !reply.trim() || sending) return
    setSending(true)
    setError('')
    try {
      const updated = await smmService.replyInbox(selected.id, reply.trim())
      setItems((prev) => prev.map((i) => (i.id === selected.id ? updated : i)))
      setSelected(updated)
      if (updated.status === 'replied') setReply('')
      if (updated.reply_error) setError(updated.reply_error)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSending(false)
    }
  }

  function onReplyKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key !== 'Enter') return
    if (e.shiftKey) return
    // Enter or Ctrl/Cmd+Enter sends (Shift+Enter = newline)
    if (!e.ctrlKey && !e.metaKey && e.key === 'Enter') {
      e.preventDefault()
      void handleReply()
      return
    }
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault()
      void handleReply()
    }
  }

  async function handleSaveEdit() {
    if (!selected) return
    try {
      const updated = await smmService.editInbox(selected.id, editedText)
      setItems((prev) => prev.map((i) => (i.id === selected.id ? updated : i)))
      setSelected(updated)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function handleRedirect(pending = false) {
    if (!selected || redirectIds.length === 0) return
    const targets = ownChannels
      .filter((c) => redirectIds.includes(c.id))
      .map((c) => ({ network: c.network, external_id: c.external_id }))
    try {
      await smmService.redirectInbox(selected.id, {
        targets,
        use_edited: true,
        pending_approval: pending,
      })
      setRedirectIds([])
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  function insertSnippet(text: string) {
    setReply((prev) => (prev ? `${prev.trim()} ${text}` : text))
    replyRef.current?.focus()
  }

  function addSnippet(e: FormEvent) {
    e.preventDefault()
    const t = snippetEdit.trim()
    if (!t) return
    const next = [...snippets.filter((s) => s !== t), t].slice(0, 12)
    setSnippets(next)
    saveSnippets(selectedBrandId, next)
    setSnippetEdit('')
  }

  const newCount = useMemo(
    () => items.filter((i) => i.status === 'new').length,
    [items],
  )

  return (
    <PageContainer>
      <PageHeader
        title={isCommentsMode ? 'Inbox · Comments' : 'Inbox'}
        description={
          isCommentsMode
            ? `Быстрые ответы в discussion · poll ${COMMENTS_POLL_MS / 1000}s${
                selectedBrand ? ` · ${selectedBrand.name}` : ''
              }`
            : selectedBrand
              ? `DM / comments / reactions · ${selectedBrand.name}`
              : 'Единая лента TG + VK'
        }
      />
      {error && <Alert variant="error">{error}</Alert>}

      <div className="flex flex-wrap gap-2 mb-4 items-center">
        <div className="flex rounded-md border border-[var(--border-color)] overflow-hidden text-sm">
          <button
            type="button"
            className={`px-3 py-2 ${!isCommentsMode ? 'bg-[var(--bg-tertiary)] font-medium' : ''}`}
            onClick={() => setMode(false)}
          >
            All
          </button>
          <button
            type="button"
            className={`px-3 py-2 border-l border-[var(--border-color)] ${
              isCommentsMode ? 'bg-[var(--bg-tertiary)] font-medium' : ''
            }`}
            onClick={() => {
              setMode(true)
              void ensureNotifyPermission()
            }}
          >
            Comments{newCount > 0 && isCommentsMode ? ` (${newCount})` : ''}
          </button>
        </div>
        <select
          className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
          value={network}
          onChange={(e) => setNetwork(e.target.value)}
        >
          <option value="">All networks</option>
          <option value="tg">Telegram</option>
          <option value="vk">VKontakte</option>
        </select>
        <select
          className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value as InboxStatus | '')}
        >
          <option value="">All statuses</option>
          <option value="new">New</option>
          <option value="read">Read</option>
          <option value="replied">Replied</option>
          <option value="reply_failed">Reply failed</option>
          <option value="archived">Archived</option>
        </select>
        <Button variant="secondary" onClick={() => void load()} disabled={loading}>
          Refresh
        </Button>
        {isCommentsMode && typeof Notification !== 'undefined' && Notification.permission !== 'granted' && (
          <Button size="sm" variant="ghost" onClick={() => void ensureNotifyPermission()}>
            Enable desktop alerts
          </Button>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardContent className="p-0 divide-y divide-[var(--border-color)] max-h-[70vh] overflow-y-auto">
            {items.length === 0 && (
              <p className="p-4 text-sm text-[var(--text-muted)]">
                {loading
                  ? 'Loading…'
                  : isCommentsMode
                    ? 'Нет комментариев. Привяжите Discussion chat в Channels.'
                    : 'Inbox пуст.'}
              </p>
            )}
            {items.map((item) => {
              const isNew = item.status === 'new'
              return (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  setSelected(item)
                  setEditedText(item.edited_text || item.text || '')
                  setReply('')
                  if (isNew) void handleRead(item)
                }}
                className={`w-full text-left px-3 py-3 flex gap-3 hover:bg-[var(--bg-tertiary)] ${
                  selected?.id === item.id ? 'bg-[var(--bg-tertiary)]' : ''
                }`}
              >
                <span
                  className="w-1 rounded-full shrink-0"
                  style={{ backgroundColor: brandColor(item.brand_id) }}
                />
                <div className="min-w-0 flex-1">
                  <div className="flex justify-between gap-2 text-xs text-[var(--text-muted)]">
                    <span className="uppercase flex items-center gap-1.5">
                      {isNew && (
                        <span
                          className="inline-block h-1.5 w-1.5 rounded-full bg-primary-500"
                          title="New"
                          aria-label="New"
                        />
                      )}
                      {item.network}
                      {!isCommentsMode && ` · ${item.type}`}
                    </span>
                    <span>{formatAge(item.created_at)}</span>
                  </div>
                  <p className={`text-sm truncate ${isNew ? 'font-semibold text-[var(--text-primary)]' : 'font-medium'}`}>
                    {item.author || 'Unknown'}
                  </p>
                  <p className={`text-sm truncate ${isNew ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)]'}`}>
                    {item.text}
                  </p>
                  <p className="text-xs text-[var(--text-muted)] truncate mt-0.5">
                    {channelLabel(item, ownChannels)}
                    {item.status !== 'new' && item.status !== 'read' ? ` · ${item.status}` : ''}
                  </p>
                </div>
              </button>
              )
            })}
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardContent className="p-4 space-y-4 min-h-[320px]">
            {!selected && <p className="text-sm text-[var(--text-muted)]">Выберите сообщение</p>}
            {selected && (
              <>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <h3 className="text-lg font-semibold">{selected.author || 'Unknown'}</h3>
                    <p className="text-xs text-[var(--text-muted)]">
                      {channelLabel(selected, ownChannels)} · {formatAge(selected.created_at)} ·{' '}
                      {selected.status}
                    </p>
                  </div>
                  <Button variant="secondary" size="sm" onClick={() => void handleArchive(selected)}>
                    Archive
                  </Button>
                </div>
                <p className="whitespace-pre-wrap text-[var(--text-primary)]">{selected.text}</p>
                {selected.status === 'reply_failed' && selected.reply_error && (
                  <Alert variant="error">{selected.reply_error}</Alert>
                )}

                <AiAssistPanel
                  sourceText={selected.text || ''}
                  source="inbox"
                  sourceId={selected.id}
                  defaultAction="reply_draft"
                  defaultNetwork={selected.network || 'tg'}
                  applyTargets={[
                    { id: 'reply', label: 'В ответ' },
                    { id: 'edited', label: 'В edit before redirect' },
                  ]}
                  defaultApplyTarget="reply"
                  onApply={(text, meta) => {
                    if (meta.target === 'edited') {
                      setEditedText(text)
                    } else {
                      setReply(text)
                      replyRef.current?.focus()
                    }
                  }}
                />

                <div className="space-y-2 pt-2 border-t border-[var(--border-color)]">
                  <div className="flex flex-wrap gap-1.5">
                    {snippets.map((s) => (
                      <button
                        key={s}
                        type="button"
                        className="text-xs px-2 py-1 rounded border border-[var(--border-color)] hover:bg-[var(--bg-tertiary)]"
                        onClick={() => insertSnippet(s)}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                  <form onSubmit={addSnippet} className="flex gap-2">
                    <input
                      className="flex-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1 text-xs"
                      placeholder="Новый сниппет…"
                      value={snippetEdit}
                      onChange={(e) => setSnippetEdit(e.target.value)}
                    />
                    <Button type="submit" size="sm" variant="ghost" disabled={!snippetEdit.trim()}>
                      Add
                    </Button>
                  </form>
                  <label className="text-sm text-[var(--text-secondary)]">
                    Reply in thread
                    <span className="text-[var(--text-muted)] ml-2 font-normal">
                      Enter — отправить · Shift+Enter — новая строка
                    </span>
                  </label>
                  <textarea
                    ref={replyRef}
                    className="w-full mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] p-2 text-sm min-h-[88px]"
                    value={reply}
                    onChange={(e) => setReply(e.target.value)}
                    onKeyDown={onReplyKeyDown}
                    placeholder="Быстрый ответ…"
                  />
                  <div className="flex flex-wrap gap-2">
                    <Button onClick={() => void handleReply()} disabled={!reply.trim() || sending}>
                      {sending ? 'Sending…' : 'Reply'}
                    </Button>
                  </div>
                </div>

                {!isCommentsMode && (
                  <>
                    <div>
                      <label className="text-sm text-[var(--text-secondary)]">Edit before redirect</label>
                      <textarea
                        className="w-full mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] p-2 text-sm min-h-[80px]"
                        value={editedText}
                        onChange={(e) => setEditedText(e.target.value)}
                      />
                      <Button
                        size="sm"
                        variant="secondary"
                        className="mt-2"
                        onClick={() => void handleSaveEdit()}
                      >
                        Save edit
                      </Button>
                    </div>
                    <div className="space-y-2 pt-4 border-t border-[var(--border-color)]">
                      <p className="text-sm font-medium text-[var(--text-secondary)]">
                        Redirect / Repost (secondary)
                      </p>
                      <div className="space-y-1 max-h-28 overflow-y-auto">
                        {ownChannels.map((c) => (
                          <label key={c.id} className="flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={redirectIds.includes(c.id)}
                              onChange={() =>
                                setRedirectIds((prev) =>
                                  prev.includes(c.id)
                                    ? prev.filter((x) => x !== c.id)
                                    : [...prev, c.id],
                                )
                              }
                            />
                            <span className="uppercase text-[var(--text-muted)]">{c.network}</span>
                            {c.title || c.external_id}
                          </label>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="secondary"
                          disabled={redirectIds.length === 0}
                          onClick={() => void handleRedirect(false)}
                        >
                          Redirect now
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={redirectIds.length === 0}
                          onClick={() => void handleRedirect(true)}
                        >
                          Send for approval
                        </Button>
                      </div>
                    </div>
                  </>
                )}

                {isCommentsMode && (
                  <details className="pt-2 border-t border-[var(--border-color)] text-sm">
                    <summary className="cursor-pointer text-[var(--text-secondary)]">
                      Redirect / Repost (secondary)
                    </summary>
                    <div className="mt-2 space-y-2">
                      <div className="space-y-1 max-h-28 overflow-y-auto">
                        {ownChannels.map((c) => (
                          <label key={c.id} className="flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={redirectIds.includes(c.id)}
                              onChange={() =>
                                setRedirectIds((prev) =>
                                  prev.includes(c.id)
                                    ? prev.filter((x) => x !== c.id)
                                    : [...prev, c.id],
                                )
                              }
                            />
                            <span className="uppercase text-[var(--text-muted)]">{c.network}</span>
                            {c.title || c.external_id}
                          </label>
                        ))}
                      </div>
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={redirectIds.length === 0}
                        onClick={() => void handleRedirect(false)}
                      >
                        Redirect now
                      </Button>
                    </div>
                  </details>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
