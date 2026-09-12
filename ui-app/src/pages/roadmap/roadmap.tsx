import { useCallback, useEffect, useState, FormEvent } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { useAuth } from '@/contexts/auth-context'
import { useToast } from '@/contexts/toast-context'
import { roadmapService } from '@/services/roadmap-service'
import type { RoadmapItem } from '@/types/core'

export function RoadmapPage() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const isAdmin = user?.role === 'admin'

  const [items, setItems] = useState<RoadmapItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [votingId, setVotingId] = useState<number | null>(null)
  const [mutatingId, setMutatingId] = useState<number | null>(null)

  const [newTitle, setNewTitle] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [createError, setCreateError] = useState('')

  const loadItems = useCallback(async () => {
    setError('')
    try {
      const response = await roadmapService.listItems()
      setItems(response.items || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить список')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadItems()
  }, [loadItems])

  async function handleVote(itemId: number) {
    setVotingId(itemId)
    try {
      const result = await roadmapService.toggleVote(itemId)
      setItems((prev) =>
        prev
          .map((item) =>
            item.id === itemId
              ? { ...item, voted: result.voted, vote_count: result.vote_count }
              : item,
          )
          .sort((a, b) => b.vote_count - a.vote_count || b.id - a.id),
      )
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Не удалось проголосовать', 'error')
    } finally {
      setVotingId(null)
    }
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    setCreateError('')
    const title = newTitle.trim()
    if (!title) {
      setCreateError('Введите название')
      return
    }

    setIsCreating(true)
    try {
      const created = await roadmapService.createItem({
        title,
        description: newDescription.trim() || undefined,
      })
      setItems((prev) => [created, ...prev])
      setNewTitle('')
      setNewDescription('')
      addToast('Пункт добавлен', 'success')
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Не удалось создать пункт')
    } finally {
      setIsCreating(false)
    }
  }

  async function handleArchive(item: RoadmapItem) {
    setMutatingId(item.id)
    try {
      const updated = await roadmapService.updateItem(item.id, { is_active: !item.is_active })
      setItems((prev) => {
        if (!isAdmin && !updated.is_active) {
          return prev.filter((row) => row.id !== item.id)
        }
        return prev.map((row) => (row.id === item.id ? { ...row, ...updated } : row))
      })
      addToast(updated.is_active ? 'Пункт восстановлен' : 'Пункт архивирован', 'success')
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Не удалось обновить пункт', 'error')
    } finally {
      setMutatingId(null)
    }
  }

  async function handleDelete(item: RoadmapItem) {
    if (!window.confirm(`Удалить «${item.title}» вместе с голосами?`)) {
      return
    }
    setMutatingId(item.id)
    try {
      await roadmapService.deleteItem(item.id)
      setItems((prev) => prev.filter((row) => row.id !== item.id))
      addToast('Пункт удалён', 'success')
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Не удалось удалить пункт', 'error')
    } finally {
      setMutatingId(null)
    }
  }

  const activeItems = items.filter((item) => item.is_active)
  const archivedItems = isAdmin ? items.filter((item) => !item.is_active) : []

  return (
    <PageContainer maxWidth="default">
      <PageHeader
        title="Что далее"
        description="Голосуйте, какие доработки делать в первую очередь"
      />

      {error && (
        <Alert variant="error" className="mb-6 animate-slide-down">
          {error}
        </Alert>
      )}

      {isAdmin && (
        <Card className="animate-slide-up mb-6 max-w-2xl">
          <CardHeader>
            <CardTitle>Добавить вариант</CardTitle>
            <CardDescription>Только администраторы могут предлагать пункты для голосования</CardDescription>
          </CardHeader>
          <CardContent>
            {createError && (
              <Alert variant="error" className="mb-4">
                {createError}
              </Alert>
            )}
            <form onSubmit={handleCreate} className="space-y-4">
              <Input
                label="Название"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Например: улучшение календаря"
                required
              />
              <div>
                <label
                  htmlFor="roadmap-description"
                  className="text-sm font-medium text-[var(--text-secondary)] block mb-2"
                >
                  Описание (необязательно)
                </label>
                <textarea
                  id="roadmap-description"
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 resize-y"
                  placeholder="Кратко, зачем это нужно"
                />
              </div>
              <Button type="submit" isLoading={isCreating} className="w-full sm:w-auto">
                Добавить
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <p className="text-sm text-[var(--text-muted)]">Загрузка…</p>
      ) : activeItems.length === 0 ? (
        <Card className="animate-slide-up">
          <CardContent className="py-8">
            <p className="text-sm text-[var(--text-muted)] text-center">
              Пока нет активных вариантов для голосования
              {isAdmin ? '. Добавьте первый пункт выше.' : '.'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <ul className="space-y-3">
          {activeItems.map((item) => (
            <li key={item.id}>
              <Card className="animate-slide-up">
                <CardContent className="py-4 flex flex-col sm:flex-row sm:items-start gap-4">
                  <button
                    type="button"
                    onClick={() => void handleVote(item.id)}
                    disabled={votingId === item.id || !item.is_active}
                    className={`shrink-0 flex flex-col items-center justify-center min-w-[4.5rem] rounded-lg border px-3 py-2 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 ${
                      item.voted
                        ? 'border-primary-500 bg-primary-500/10 text-primary-400'
                        : 'border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:border-primary-500/50'
                    }`}
                    aria-pressed={item.voted}
                    aria-label={item.voted ? 'Снять голос' : 'Проголосовать'}
                  >
                    <span className="text-lg leading-none" aria-hidden>
                      ▲
                    </span>
                    <span className="text-sm font-semibold mt-1">{item.vote_count}</span>
                  </button>

                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-semibold text-[var(--text-primary)]">{item.title}</h3>
                    {item.description && (
                      <p className="mt-1 text-sm text-[var(--text-secondary)] whitespace-pre-wrap">
                        {item.description}
                      </p>
                    )}
                  </div>

                  {isAdmin && (
                    <div className="flex flex-wrap gap-2 shrink-0">
                      <Button
                        type="button"
                        variant="secondary"
                        disabled={mutatingId === item.id}
                        onClick={() => void handleArchive(item)}
                      >
                        В архив
                      </Button>
                      <Button
                        type="button"
                        variant="secondary"
                        disabled={mutatingId === item.id}
                        onClick={() => void handleDelete(item)}
                      >
                        Удалить
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
      )}

      {archivedItems.length > 0 && (
        <div className="mt-8">
          <h2 className="text-sm font-semibold text-[var(--text-secondary)] mb-3">Архив</h2>
          <ul className="space-y-3 opacity-80">
            {archivedItems.map((item) => (
              <li key={item.id}>
                <Card>
                  <CardContent className="py-4 flex flex-col sm:flex-row sm:items-start gap-4">
                    <div className="shrink-0 flex flex-col items-center justify-center min-w-[4.5rem] rounded-lg border border-[var(--border-color)] px-3 py-2 text-[var(--text-muted)]">
                      <span className="text-lg leading-none" aria-hidden>
                        ▲
                      </span>
                      <span className="text-sm font-semibold mt-1">{item.vote_count}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-base font-semibold text-[var(--text-primary)]">{item.title}</h3>
                      {item.description && (
                        <p className="mt-1 text-sm text-[var(--text-secondary)]">{item.description}</p>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-2 shrink-0">
                      <Button
                        type="button"
                        variant="secondary"
                        disabled={mutatingId === item.id}
                        onClick={() => void handleArchive(item)}
                      >
                        Восстановить
                      </Button>
                      <Button
                        type="button"
                        variant="secondary"
                        disabled={mutatingId === item.id}
                        onClick={() => void handleDelete(item)}
                      >
                        Удалить
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </li>
            ))}
          </ul>
        </div>
      )}
    </PageContainer>
  )
}
