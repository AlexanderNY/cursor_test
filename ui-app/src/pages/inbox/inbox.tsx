import { useEffect, useState } from 'react'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import type { InboxItem, InboxStatus, InboxType } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'

export function InboxPage() {
  const { brands, selectedBrandId, selectedBrand } = useBrand()
  const [items, setItems] = useState<InboxItem[]>([])
  const [selected, setSelected] = useState<InboxItem | null>(null)
  const [network, setNetwork] = useState<string>('')
  const [type, setType] = useState<string>('')
  const [status, setStatus] = useState<string>('new')
  const [reply, setReply] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function load() {
    setLoading(true)
    setError('')
    try {
      const res = await smmService.listInbox({
        brand_id: selectedBrandId ?? undefined,
        network: network || undefined,
        type: type || undefined,
        status: status || undefined,
        limit: 50,
      })
      setItems(res.items)
      if (selected && !res.items.some((i) => i.id === selected.id)) {
        setSelected(null)
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [selectedBrandId, network, type, status])

  function brandColor(brandId?: number | null): string {
    return brands.find((b) => b.id === brandId)?.color ?? '#64748b'
  }

  async function handleRead(item: InboxItem) {
    try {
      const updated = await smmService.markInboxRead(item.id)
      setItems((prev) => prev.map((i) => (i.id === item.id ? updated : i)))
      setSelected(updated)
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
    if (!selected || !reply.trim()) return
    try {
      const updated = await smmService.replyInbox(selected.id, reply.trim())
      setItems((prev) => prev.map((i) => (i.id === selected.id ? updated : i)))
      setSelected(updated)
      setReply('')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Inbox"
        description={
          selectedBrand
            ? `Единая лента DM / комментарии / реакции · ${selectedBrand.name}`
            : 'Единая лента DM / комментарии / реакции TG + VK'
        }
      />
      {error && <Alert variant="error">{error}</Alert>}

      <div className="flex flex-wrap gap-2 mb-4">
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
          value={type}
          onChange={(e) => setType(e.target.value as InboxType | '')}
        >
          <option value="">All types</option>
          <option value="dm">DM</option>
          <option value="comment">Comment</option>
          <option value="reaction">Reaction</option>
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
          <option value="archived">Archived</option>
        </select>
        <Button variant="secondary" onClick={() => void load()} disabled={loading}>
          Refresh
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardContent className="p-0 divide-y divide-[var(--border-color)] max-h-[70vh] overflow-y-auto">
            {items.length === 0 && (
              <p className="p-4 text-sm text-[var(--text-muted)]">
                {loading ? 'Loading…' : 'Inbox пуст. Collector будет наполнять ленту.'}
              </p>
            )}
            {items.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  setSelected(item)
                  if (item.status === 'new') void handleRead(item)
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
                    <span className="uppercase">{item.network} · {item.type}</span>
                    <span>{item.status}</span>
                  </div>
                  <p className="text-sm font-medium truncate">{item.author || 'Unknown'}</p>
                  <p className="text-sm text-[var(--text-secondary)] truncate">{item.text}</p>
                </div>
              </button>
            ))}
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardContent className="p-4 space-y-4 min-h-[320px]">
            {!selected && (
              <p className="text-sm text-[var(--text-muted)]">Выберите сообщение</p>
            )}
            {selected && (
              <>
                <div className="flex items-center gap-2">
                  <span
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: brandColor(selected.brand_id) }}
                  />
                  <span className="text-sm text-[var(--text-muted)] uppercase">
                    {selected.network} · {selected.type}
                  </span>
                </div>
                <h3 className="text-lg font-semibold">{selected.author || 'Unknown'}</h3>
                <p className="whitespace-pre-wrap text-[var(--text-primary)]">{selected.text}</p>
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm" onClick={() => void handleArchive(selected)}>
                    Archive
                  </Button>
                </div>
                <div className="space-y-2 pt-4 border-t border-[var(--border-color)]">
                  <Input
                    label="Reply"
                    value={reply}
                    onChange={(e) => setReply(e.target.value)}
                    placeholder="Ответ…"
                  />
                  <Button onClick={() => void handleReply()} disabled={!reply.trim()}>
                    Send reply
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
