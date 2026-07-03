import { useCallback, useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/ui/empty-state'
import { TableSkeleton } from '@/components/ui/skeleton'
import { gameService } from '@/services/game-service'
import type { GameLeaderboardEntry, GameSessionStats, GameMode } from '@/types/game'

interface RatingSectionProps {
  modeId: number | null
  modeTitle?: string
  showModeFilter?: boolean
  quizModes?: GameMode[]
  filterModeId?: number | null
  onFilterModeIdChange?: (modeId: number | null) => void
  className?: string
}

function formatPlayerName(
  username?: string | null,
  firstName?: string | null,
  telegramUserId?: number,
): string {
  if (username) return `@${username}`
  if (firstName) return firstName
  return telegramUserId ? String(telegramUserId) : '—'
}

function formatDate(iso?: string | null): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('ru-RU')
  } catch {
    return iso
  }
}

export function RatingSection({
  modeId,
  modeTitle,
  showModeFilter = false,
  quizModes = [],
  filterModeId = null,
  onFilterModeIdChange,
  className = 'mt-6',
}: RatingSectionProps) {
  const [leaderboard, setLeaderboard] = useState<GameLeaderboardEntry[]>([])
  const [sessions, setSessions] = useState<GameSessionStats[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const loadStats = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try {
      const [ratingRows, sessionRows] = await Promise.all([
        gameService.listLeaderboard(50),
        gameService.listSessions(modeId ?? undefined, 100),
      ])
      setLeaderboard(ratingRows)
      setSessions(sessionRows)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить статистику')
      setLeaderboard([])
      setSessions([])
    } finally {
      setIsLoading(false)
    }
  }, [modeId])

  useEffect(() => {
    loadStats()
  }, [loadStats])

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg">Рейтинг и прохождения</CardTitle>
        <CardDescription>
          Статистика завершённых игр
          {modeTitle ? ` · фильтр по режиму «${modeTitle}»` : showModeFilter ? ' · все режимы викторины' : ''}.
          Обновляется при загрузке страницы.
        </CardDescription>
        {showModeFilter && onFilterModeIdChange && quizModes.length > 0 && (
          <div className="mt-3 max-w-xs">
            <label className="mb-1 block text-xs text-[var(--text-secondary)]">Режим</label>
            <select
              className="w-full rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
              value={filterModeId ?? ''}
              onChange={(e) => {
                const value = e.target.value
                onFilterModeIdChange(value ? Number.parseInt(value, 10) : null)
              }}
            >
              <option value="">Все режимы викторины</option>
              {quizModes.map((mode) => (
                <option key={mode.id} value={mode.id}>
                  {mode.title}
                </option>
              ))}
            </select>
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-8">
        {error && (
          <p className="text-sm text-red-400">{error}</p>
        )}

        <div>
          <h3 className="mb-3 text-sm font-semibold text-[var(--text-primary)]">
            Топ игроков (лучший результат)
          </h3>
          {isLoading ? (
            <TableSkeleton rows={5} />
          ) : leaderboard.length === 0 ? (
            <EmptyState title="Пока нет результатов" description="Завершите игру в боте." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                    <th className="py-2 pr-3">#</th>
                    <th className="py-2 pr-3">Игрок</th>
                    <th className="py-2 pr-3">Верно</th>
                    <th className="py-2 pr-3">Время</th>
                    <th className="py-2">Дата</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.map((row, index) => (
                    <tr key={row.telegram_user_id} className="border-b border-[var(--border-color)]/60">
                      <td className="py-2 pr-3">{index + 1}</td>
                      <td className="py-2 pr-3">
                        {formatPlayerName(row.username, null, row.telegram_user_id)}
                      </td>
                      <td className="py-2 pr-3">
                        {row.correct_count}/{row.total_questions}
                      </td>
                      <td className="py-2 pr-3">
                        {row.duration_sec != null ? `${row.duration_sec} с` : '—'}
                      </td>
                      <td className="py-2">{formatDate(row.finished_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div>
          <h3 className="mb-3 text-sm font-semibold text-[var(--text-primary)]">
            История прохождений
          </h3>
          {isLoading ? (
            <TableSkeleton rows={5} />
          ) : sessions.length === 0 ? (
            <EmptyState title="Нет завершённых игр" description="История появится после первых прохождений." />
          ) : (
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-[var(--bg-primary)]">
                  <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                    <th className="py-2 pr-3">Игрок</th>
                    <th className="py-2 pr-3">Режим</th>
                    <th className="py-2 pr-3">Верно</th>
                    <th className="py-2 pr-3">Время</th>
                    <th className="py-2">Дата</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((row) => (
                    <tr key={row.session_id} className="border-b border-[var(--border-color)]/60">
                      <td className="py-2 pr-3">
                        {formatPlayerName(row.username, row.first_name, row.telegram_user_id)}
                      </td>
                      <td className="py-2 pr-3">{row.mode_title}</td>
                      <td className="py-2 pr-3">
                        {row.correct_count}/{row.total_questions}
                      </td>
                      <td className="py-2 pr-3">
                        {row.duration_sec != null ? `${row.duration_sec} с` : '—'}
                      </td>
                      <td className="py-2">{formatDate(row.finished_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
