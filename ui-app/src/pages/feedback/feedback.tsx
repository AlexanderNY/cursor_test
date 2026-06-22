import { useState, FormEvent } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { useAuth } from '@/contexts/auth-context'
import { useToast } from '@/contexts/toast-context'
import { feedbackService } from '@/services/feedback-service'
import type { FeedbackType } from '@/types/core'
import { FEEDBACK_TYPE_LABELS } from '@/types/core'

const FEEDBACK_TYPES: FeedbackType[] = ['bug_report', 'suggestion', 'contact_author']

export function FeedbackPage() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const [type, setType] = useState<FeedbackType>('bug_report')
  const [text, setText] = useState('')
  const [email, setEmail] = useState(user?.email ?? '')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setIsSuccess(false)

    const trimmedText = text.trim()
    if (!trimmedText) {
      setError('Введите текст сообщения')
      return
    }

    setIsSubmitting(true)
    try {
      await feedbackService.submitFeedback({
        type,
        text: trimmedText,
        email: email.trim() || undefined,
      })
      setIsSuccess(true)
      setText('')
      addToast('Сообщение отправлено', 'success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить сообщение')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Обратная связь"
        description="Сообщите об ошибке, предложите доработку или свяжитесь с автором"
      />

      <Card className="animate-slide-up max-w-2xl">
        <CardHeader>
          <CardTitle>Форма обратной связи</CardTitle>
          <CardDescription>
            Выберите тип обращения и опишите ваш вопрос или предложение
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="error" className="mb-6 animate-slide-down">
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="feedback-type"
                className="text-sm font-medium text-[var(--text-secondary)] block mb-2"
              >
                Тип обращения
              </label>
              <select
                id="feedback-type"
                value={type}
                onChange={(e) => setType(e.target.value as FeedbackType)}
                className="w-full rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50"
              >
                {FEEDBACK_TYPES.map((feedbackType) => (
                  <option key={feedbackType} value={feedbackType}>
                    {FEEDBACK_TYPE_LABELS[feedbackType]}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label
                htmlFor="feedback-text"
                className="text-sm font-medium text-[var(--text-secondary)] block mb-2"
              >
                Сообщение
              </label>
              <textarea
                id="feedback-text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Опишите проблему, предложение или вопрос..."
                rows={6}
                required
                className="w-full rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 resize-y min-h-[120px]"
              />
            </div>

            <Input
              label="E-mail для обратной связи"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <Button
              type="submit"
              isLoading={isSubmitting}
              success={isSuccess}
              className="w-full sm:w-auto"
            >
              Отправить
            </Button>
          </form>
        </CardContent>
      </Card>
    </PageContainer>
  )
}
