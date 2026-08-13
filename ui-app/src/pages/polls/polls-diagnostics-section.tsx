import { useCallback, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { EmptyState } from '@/components/ui/empty-state'
import { gameService } from '@/services/game-service'
import type { GameBotDiagnostics, DiagnosticStatus } from '@/types/game'
import { usePollsContext } from './polls-context'
import { formatDateTime } from '@/utils/date'

const STATUS_LABELS: Record<DiagnosticStatus, string> = {
  ok: 'OK',
  warning: 'Внимание',
  error: 'Ошибка',
}

const STATUS_CLASSES: Record<DiagnosticStatus, string> = {
  ok: 'bg-emerald-500/15 text-emerald-400',
  warning: 'bg-amber-500/15 text-amber-400',
  error: 'bg-red-500/15 text-red-400',
}

const OVERALL_LABELS: Record<DiagnosticStatus, string> = {
  ok: 'Бот готов к работе',
  warning: 'Есть предупреждения',
  error: 'Обнаружены проблемы',
}

export function PollsDiagnosticsSection() {
  const { selectedBotId, selectedMode } = usePollsContext()
  const [diagnostics, setDiagnostics] = useState<GameBotDiagnostics | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const runDiagnostics = useCallback(async () => {
    if (!selectedBotId) return

    setIsLoading(true)
    setError('')
    setDiagnostics(null)
    try {
      const data = await gameService.getBotDiagnostics(selectedBotId)
      setDiagnostics(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось выполнить диагностику')
    } finally {
      setIsLoading(false)
    }
  }, [selectedBotId])

  if (!selectedBotId) {
    return (
      <EmptyState
        title="Выберите бота"
        description="Добавьте или выберите Telegram-бота в настройках выше."
      />
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-lg">Диагностика бота</CardTitle>
            <CardDescription>
              Проверка токена, polling, режимов, S3 и публичных URL для выбранного бота.
            </CardDescription>
          </div>
          <Button type="button" onClick={runDiagnostics} isLoading={isLoading}>
            Запустить диагностику
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <Alert variant="error">{error}</Alert>}

        {diagnostics && (
          <>
            <div className="flex flex-wrap items-center gap-3 rounded-xl border border-[var(--border-color)] p-4">
              <span
                className={`rounded-full px-3 py-1 text-sm font-medium ${STATUS_CLASSES[diagnostics.overall_status]}`}
              >
                {OVERALL_LABELS[diagnostics.overall_status]}
              </span>
              <span className="text-sm text-[var(--text-secondary)]">
                {diagnostics.bot_name} ·{' '}
                {formatDateTime(diagnostics.collected_at)}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                    <th className="pb-2 pr-3 font-medium">Проверка</th>
                    <th className="pb-2 pr-3 font-medium">Статус</th>
                    <th className="pb-2 font-medium">Результат</th>
                  </tr>
                </thead>
                <tbody>
                  {diagnostics.checks.map((check) => (
                    <tr key={check.key} className="border-b border-[var(--border-color)]/60">
                      <td className="py-3 pr-3 text-[var(--text-primary)]">{check.label}</td>
                      <td className="py-3 pr-3">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs ${STATUS_CLASSES[check.status]}`}
                        >
                          {STATUS_LABELS[check.status]}
                        </span>
                      </td>
                      <td className="py-3 text-[var(--text-secondary)]">{check.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {diagnostics.hints.length > 0 && (
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
                <h4 className="mb-2 text-sm font-semibold text-[var(--text-primary)]">
                  Рекомендации
                </h4>
                <ul className="list-disc space-y-1 pl-5 text-sm text-[var(--text-secondary)]">
                  {diagnostics.hints.map((hint) => (
                    <li key={hint}>{hint}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}

        {!diagnostics && !isLoading && !error && (
          <EmptyState
            title="Диагностика не запускалась"
            description={
              selectedMode
                ? `Нажмите «Запустить диагностику» для проверки бота режима «${selectedMode.title}».`
                : 'Нажмите «Запустить диагностику» для проверки выбранного бота.'
            }
          />
        )}
      </CardContent>
    </Card>
  )
}
