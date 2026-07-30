import { useEffect, useState, type FormEvent } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { coreService } from '@/services/core-service'
import type { AiSettingsResponse } from '@/types/core'

export function AiCheckSection() {
  const [text, setText] = useState('')
  const [reply, setReply] = useState('')
  const [model, setModel] = useState('')
  const [latencyMs, setLatencyMs] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [isRunning, setIsRunning] = useState(false)

  const [aiSettings, setAiSettings] = useState<AiSettingsResponse | null>(null)
  const [isLoadingSettings, setIsLoadingSettings] = useState(true)
  const [isSavingSettings, setIsSavingSettings] = useState(false)
  const [settingsError, setSettingsError] = useState('')
  const [settingsMessage, setSettingsMessage] = useState('')

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setIsLoadingSettings(true)
      setSettingsError('')
      try {
        const settings = await coreService.getAiSettings()
        if (!cancelled) setAiSettings(settings)
      } catch (e) {
        if (!cancelled) {
          setSettingsError(e instanceof Error ? e.message : 'Не удалось загрузить настройки AI')
        }
      } finally {
        if (!cancelled) setIsLoadingSettings(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  async function handleToggleAi(enabled: boolean) {
    setSettingsError('')
    setSettingsMessage('')
    setIsSavingSettings(true)
    try {
      const settings = await coreService.setAiEnabled(enabled)
      setAiSettings(settings)
      setSettingsMessage(
        enabled
          ? 'Нейросеть включена — сервисы снова вызывают Ollama.'
          : 'Нейросеть отключена — вызовы Ollama пропускаются (фолбэки без AI).'
      )
    } catch (e) {
      setSettingsError(e instanceof Error ? e.message : 'Не удалось сохранить настройку AI')
    } finally {
      setIsSavingSettings(false)
    }
  }

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

  const isAiEnabled = aiSettings?.enabled ?? true

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Нейросеть (Ollama)</CardTitle>
          <CardDescription>
            Отключите AI для отладки остального функционала без вызовов модели. Контейнер Ollama
            может оставаться запущенным — запросы просто не отправляются.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {settingsError && <Alert variant="error">{settingsError}</Alert>}
          {settingsMessage && <Alert variant="success">{settingsMessage}</Alert>}

          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-3">
                <span
                  className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
                    isLoadingSettings
                      ? 'bg-[var(--bg-tertiary)] text-[var(--text-muted)]'
                      : isAiEnabled
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-amber-500/20 text-amber-400'
                  }`}
                >
                  {isLoadingSettings ? 'Загрузка…' : isAiEnabled ? 'Включена' : 'Отключена'}
                </span>
                {aiSettings?.model && (
                  <span className="text-sm text-[var(--text-muted)]">{aiSettings.model}</span>
                )}
              </div>
              {aiSettings?.service_url && (
                <p className="text-xs text-[var(--text-muted)] font-mono">{aiSettings.service_url}</p>
              )}
            </div>

            <div className="flex gap-2">
              <Button
                type="button"
                variant={isAiEnabled ? 'secondary' : 'default'}
                disabled={isLoadingSettings || isSavingSettings || !isAiEnabled}
                isLoading={isSavingSettings && isAiEnabled}
                onClick={() => handleToggleAi(false)}
              >
                Отключить
              </Button>
              <Button
                type="button"
                variant={!isAiEnabled ? 'secondary' : 'default'}
                disabled={isLoadingSettings || isSavingSettings || isAiEnabled}
                isLoading={isSavingSettings && !isAiEnabled}
                onClick={() => handleToggleAi(true)}
              >
                Включить
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>AI</CardTitle>
          <CardDescription>
            Отправьте произвольный текст в AI-контейнер и проверьте ответ модели.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!isAiEnabled && (
            <Alert variant="warning" className="mb-4">
              Нейросеть отключена — тестовый запрос недоступен. Включите AI выше.
            </Alert>
          )}

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
                disabled={isRunning || !isAiEnabled}
                className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all duration-200 resize-y min-h-[120px]"
              />
            </div>

            <Button type="submit" disabled={isRunning || !isAiEnabled || !text.trim()}>
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
    </div>
  )
}
