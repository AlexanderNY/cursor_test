import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import { getErrorMessage } from '@/services/api-client'
import type { BrandChannel } from '@/types/smm'
import { Switch } from '@/components/ui/switch'

interface Draft {
  discussionId: string
  discussionTitle: string
  enabled: boolean
}

function draftFromChannel(channel: BrandChannel): Draft {
  return {
    discussionId: channel.discussion_external_id || '',
    discussionTitle: channel.discussion_title || '',
    enabled: Boolean(channel.comments_collect_enabled),
  }
}

function isCollecting(channel: BrandChannel): boolean {
  return Boolean(channel.comments_collect_enabled && channel.discussion_external_id?.trim())
}

export function CommentSourcesCard() {
  const { channels, selectedBrandId, selectedBrand, refreshChannels } = useBrand()
  const ownTelegram = useMemo(
    () =>
      channels.filter(
        (channel) =>
          channel.network === 'tg' &&
          channel.role === 'own' &&
          (selectedBrandId == null || channel.brand_id === selectedBrandId),
      ),
    [channels, selectedBrandId],
  )
  const readyCount = ownTelegram.filter(isCollecting).length
  const [isOpen, setIsOpen] = useState(true)
  const [drafts, setDrafts] = useState<Record<number, Draft>>({})
  const [savingId, setSavingId] = useState<number | null>(null)
  const [rowError, setRowError] = useState<Record<number, string>>({})
  const [rowSuccess, setRowSuccess] = useState<Record<number, string>>({})

  useEffect(() => {
    setDrafts((prev) => {
      const next: Record<number, Draft> = {}
      for (const channel of ownTelegram) {
        next[channel.id] = prev[channel.id] ?? draftFromChannel(channel)
      }
      return next
    })
  }, [ownTelegram])

  function updateDraft(channelId: number, patch: Partial<Draft>) {
    setDrafts((prev) => ({
      ...prev,
      [channelId]: { ...(prev[channelId] ?? { discussionId: '', discussionTitle: '', enabled: false }), ...patch },
    }))
    setRowError((prev) => ({ ...prev, [channelId]: '' }))
    setRowSuccess((prev) => ({ ...prev, [channelId]: '' }))
  }

  async function saveChannel(event: FormEvent, channel: BrandChannel) {
    event.preventDefault()
    const draft = drafts[channel.id] ?? draftFromChannel(channel)
    const discussionId = draft.discussionId.trim()
    if (draft.enabled && !discussionId) {
      setRowError((prev) => ({
        ...prev,
        [channel.id]: 'Укажите id чата обсуждения, затем включите сбор.',
      }))
      return
    }
    setSavingId(channel.id)
    setRowError((prev) => ({ ...prev, [channel.id]: '' }))
    setRowSuccess((prev) => ({ ...prev, [channel.id]: '' }))
    try {
      const updated = await smmService.updateChannel(channel.brand_id, channel.id, {
        discussion_external_id: discussionId || null,
        discussion_title: draft.discussionTitle.trim() || null,
        comments_collect_enabled: draft.enabled && Boolean(discussionId),
      })
      setDrafts((prev) => ({ ...prev, [channel.id]: draftFromChannel(updated) }))
      await refreshChannels()
      setRowSuccess((prev) => ({
        ...prev,
        [channel.id]: updated.comments_collect_enabled
          ? 'Сбор включён. Бот подхватит чат в течение минуты.'
          : 'Сбор выключен.',
      }))
    } catch (err) {
      setRowError((prev) => ({ ...prev, [channel.id]: getErrorMessage(err) }))
    } finally {
      setSavingId(null)
    }
  }

  return (
    <Card className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle>Сбор комментариев</CardTitle>
            <CardDescription>
              {selectedBrand ? `${selectedBrand.name}. ` : ''}
              Комментарии читаются из чата обсуждения канала, не из ленты постов.
              {readyCount > 0
                ? ` Сбор включён у ${readyCount} ${readyCount === 1 ? 'канала' : 'каналов'}.`
                : ' Сбор ещё не включён.'}
            </CardDescription>
          </div>
          <Button type="button" size="sm" variant="ghost" onClick={() => setIsOpen((open) => !open)}>
            {isOpen ? 'Скрыть' : 'Настроить'}
          </Button>
        </div>
      </CardHeader>
      {isOpen && (
        <CardContent className="space-y-4">
          <ol className="list-decimal pl-5 text-sm text-[var(--text-secondary)] space-y-1">
            <li>В Telegram откройте обсуждение канала и скопируйте id чата, он выглядит как -100…</li>
            <li>Вставьте id ниже, включите сбор и сохраните. Аккаунт из Telegram → Auth должен состоять в этом чате.</li>
            <li>Новые сообщения появятся в списке. Reply отправит ответ в тот же чат.</li>
          </ol>
          {selectedBrandId == null && (
            <p className="text-sm text-[var(--text-muted)]">Выберите бренд в шапке.</p>
          )}
          {selectedBrandId != null && ownTelegram.length === 0 && (
            <p className="text-sm text-[var(--text-muted)]">
              Нет своих Telegram-каналов.{' '}
              <Link to="/channels" className="text-primary-400 hover:underline">
                Добавьте own-канал в Channels
              </Link>
            </p>
          )}
          {ownTelegram.map((channel) => {
            const draft = drafts[channel.id] ?? draftFromChannel(channel)
            const collecting = isCollecting(channel)
            return (
              <form
                key={channel.id}
                onSubmit={(event) => void saveChannel(event, channel)}
                className="rounded-lg border border-[var(--border-color)] p-3 space-y-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium text-[var(--text-primary)]">
                    {channel.title || channel.external_id}
                  </p>
                  <span className="text-[10px] uppercase tracking-wide text-[var(--text-muted)]">
                    {collecting ? 'Сбор включён' : 'Сбор выключен'}
                  </span>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <Switch
                    checked={draft.enabled}
                    onChange={(event) => updateDraft(channel.id, { enabled: event.target.checked })}
                  />
                  Собирать комментарии
                </label>
                <label className="block text-sm text-[var(--text-secondary)]">
                  Чат обсуждения
                  <input
                    className="mt-1 w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1.5 text-sm"
                    value={draft.discussionId}
                    placeholder="-100… или @username"
                    onChange={(event) => updateDraft(channel.id, { discussionId: event.target.value })}
                  />
                </label>
                <label className="block text-sm text-[var(--text-secondary)]">
                  Название чата
                  <input
                    className="mt-1 w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1.5 text-sm"
                    value={draft.discussionTitle}
                    placeholder="Необязательно, только для подписи"
                    onChange={(event) =>
                      updateDraft(channel.id, { discussionTitle: event.target.value })
                    }
                  />
                </label>
                {rowError[channel.id] && <Alert variant="error">{rowError[channel.id]}</Alert>}
                {rowSuccess[channel.id] && <Alert variant="success">{rowSuccess[channel.id]}</Alert>}
                <Button type="submit" size="sm" disabled={savingId === channel.id}>
                  {savingId === channel.id ? 'Saving…' : 'Сохранить'}
                </Button>
              </form>
            )
          })}
        </CardContent>
      )}
    </Card>
  )
}
