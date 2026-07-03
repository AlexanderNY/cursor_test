import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { EmptyState } from '@/components/ui/empty-state'
import { TableSkeleton } from '@/components/ui/skeleton'
import { gameService } from '@/services/game-service'
import type { GameBot } from '@/types/game'

interface BotsSettingsSectionProps {
  selectedBotId: number | null
  onSelectBot: (botId: number) => void
  onBotsLoaded: (bots: GameBot[]) => void
  onBotsChanged: () => void
}

export function BotsSettingsSection({
  selectedBotId,
  onSelectBot,
  onBotsLoaded,
  onBotsChanged,
}: BotsSettingsSectionProps) {
  const [bots, setBots] = useState<GameBot[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [newBotName, setNewBotName] = useState('')
  const [newBotToken, setNewBotToken] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [savingBotId, setSavingBotId] = useState<number | null>(null)
  const [deletingBotId, setDeletingBotId] = useState<number | null>(null)

  const [editingBotId, setEditingBotId] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [editToken, setEditToken] = useState('')

  const loadBots = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try {
      const data = await gameService.listBots()
      setBots(data)
      onBotsLoaded(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить ботов')
      setBots([])
    } finally {
      setIsLoading(false)
    }
  }, [onBotsLoaded])

  useEffect(() => {
    loadBots()
  }, [loadBots])

  async function handleCreateBot(e: FormEvent) {
    e.preventDefault()
    if (!newBotName.trim() || !newBotToken.trim()) return

    setIsCreating(true)
    setError('')
    setSuccess('')
    try {
      await gameService.createBot({
        name: newBotName.trim(),
        token: newBotToken.trim(),
        is_active: true,
      })
      setNewBotName('')
      setNewBotToken('')
      setSuccess('Бот добавлен')
      await loadBots()
      onBotsChanged()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать бота')
    } finally {
      setIsCreating(false)
    }
  }

  function startEdit(bot: GameBot) {
    setEditingBotId(bot.id)
    setEditName(bot.name)
    setEditToken(bot.token)
    setError('')
    setSuccess('')
  }

  async function handleSaveEdit(botId: number) {
    setSavingBotId(botId)
    setError('')
    setSuccess('')
    try {
      await gameService.updateBot(botId, {
        name: editName.trim() || undefined,
        token: editToken.trim() || undefined,
      })
      setEditingBotId(null)
      setSuccess('Настройки бота сохранены')
      await loadBots()
      onBotsChanged()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить бота')
    } finally {
      setSavingBotId(null)
    }
  }

  async function handleToggleActive(bot: GameBot) {
    setSavingBotId(bot.id)
    setError('')
    try {
      await gameService.updateBot(bot.id, { is_active: !bot.is_active })
      await loadBots()
      onBotsChanged()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось обновить бота')
    } finally {
      setSavingBotId(null)
    }
  }

  async function handleDelete(bot: GameBot) {
    if (!window.confirm(`Удалить бота «${bot.name}»? Режимы этого бота нужно удалить заранее.`)) {
      return
    }
    setDeletingBotId(bot.id)
    setError('')
    try {
      await gameService.deleteBot(bot.id)
      setSuccess('Бот удалён')
      await loadBots()
      onBotsChanged()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить бота')
    } finally {
      setDeletingBotId(null)
    }
  }

  return (
    <div className="space-y-4 rounded-xl border border-[var(--border-color)] p-4">
      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Настройки Telegram-ботов</h3>
        <p className="mt-1 text-xs text-[var(--text-secondary)]">
          Каждый бот — отдельный опрос/игра. Режимы привязываются к выбранному боту.
        </p>
      </div>

      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      <form className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]" onSubmit={handleCreateBot}>
        <Input
          placeholder="Имя бота (например: Флаги)"
          value={newBotName}
          onChange={(e) => setNewBotName(e.target.value)}
        />
        <Input
          placeholder="Токен от @BotFather"
          value={newBotToken}
          onChange={(e) => setNewBotToken(e.target.value)}
        />
        <Button type="submit" disabled={isCreating || !newBotName.trim() || !newBotToken.trim()} isLoading={isCreating}>
          Добавить бота
        </Button>
      </form>

      {isLoading ? (
        <TableSkeleton rows={2} />
      ) : bots.length === 0 ? (
        <EmptyState title="Нет ботов" description="Добавьте токен из @BotFather." />
      ) : (
        <ul className="space-y-2">
          {bots.map((bot) => {
            const isSelected = bot.id === selectedBotId
            const isEditing = editingBotId === bot.id
            return (
              <li
                key={bot.id}
                className={`rounded-xl border p-3 ${
                  isSelected
                    ? 'border-primary-500 bg-primary-500/10'
                    : 'border-[var(--border-color)]'
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <button
                    type="button"
                    className="text-left"
                    onClick={() => onSelectBot(bot.id)}
                  >
                    <p className="font-medium text-[var(--text-primary)]">{bot.name}</p>
                    <p className="text-xs text-[var(--text-secondary)]">
                      {bot.username ? `@${bot.username}` : 'username не задан'}
                      {bot.is_polling ? ' · polling активен' : ' · polling выкл'}
                      {!bot.is_active && ' · выключен'}
                    </p>
                  </button>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      onClick={() => startEdit(bot)}
                    >
                      Изменить
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      isLoading={savingBotId === bot.id}
                      onClick={() => handleToggleActive(bot)}
                    >
                      {bot.is_active ? 'Выключить' : 'Включить'}
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="danger"
                      isLoading={deletingBotId === bot.id}
                      onClick={() => handleDelete(bot)}
                    >
                      Удалить
                    </Button>
                  </div>
                </div>

                {isEditing ? (
                  <div className="mt-3 grid gap-2 sm:grid-cols-2">
                    <Input
                      placeholder="Имя"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                    />
                    <Input
                      placeholder="Токен"
                      value={editToken}
                      onChange={(e) => setEditToken(e.target.value)}
                    />
                    <div className="sm:col-span-2 flex gap-2">
                      <Button
                        type="button"
                        size="sm"
                        isLoading={savingBotId === bot.id}
                        onClick={() => handleSaveEdit(bot.id)}
                      >
                        Сохранить
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => setEditingBotId(null)}
                      >
                        Отмена
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p className="mt-2 truncate text-xs font-mono text-[var(--text-secondary)]">
                    {bot.token}
                  </p>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
