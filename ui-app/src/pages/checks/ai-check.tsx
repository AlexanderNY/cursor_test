import { useState, type FormEvent } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { coreService } from '@/services/core-service'

export function AiCheckSection() {
  const [text, setText] = useState('')
  const [reply, setReply] = useState('')
  const [model, setModel] = useState('')
  const [latencyMs, setLatencyMs] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [isRunning, setIsRunning] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = text.trim()
    if (!trimmed) {
      setError('Введите текст для проверки')
      return
    }

    setError('')
    setReply('')
    setModel('')
    setLatencyMs(null)
    setIsRunning(true)

    try {
      const result = await coreService.runAiCheck(trimmed)
      setReply(result.reply)
      setModel(result.model)
      setLatencyMs(result.latency_ms)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось выполнить запрос к AI')
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI</CardTitle>
        <CardDescription>
          Отправьте произвольный текст в AI-контейнер и проверьте ответ модели.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="ai-check-text" className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
              Текст запроса
            </label>
            <textarea
              id="ai-check-text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={6}
              placeholder="Например: Кратко объясни, что такое Docker."
              disabled={isRunning}
              className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all duration-200 resize-y min-h-[120px]"
            />
          </div>

          <Button type="submit" disabled={isRunning || !text.trim()}>
            {isRunning ? 'Проверка…' : 'Проверка'}
          </Button>
        </form>

        {error && (
          <Alert variant="error" className="mt-4">
            {error}
          </Alert>
        )}

        {(reply || isRunning) && (
          <div className="mt-6 space-y-2">
            <div className="flex flex-wrap items-center gap-3 text-sm text-[var(--text-muted)]">
              <span>Ответ модели</span>
              {model && <span>· {model}</span>}
              {latencyMs != null && <span>· {latencyMs} ms</span>}
            </div>
            <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-4 min-h-[80px] whitespace-pre-wrap text-[var(--text-primary)]">
              {isRunning && !reply ? 'Ожидание ответа от AI…' : reply}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
