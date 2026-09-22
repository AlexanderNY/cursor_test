import { FormEvent, useState } from 'react'
import { siteSubmitContact, SiteApiError } from '@/data/site/site-api'

interface ContactFormProps {
  appSlug?: string
}

export function ContactForm({ appSlug = '' }: ContactFormProps) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [ok, setOk] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setOk(false)

    const trimmedMessage = message.trim()
    const trimmedEmail = email.trim()
    if (!trimmedEmail) {
      setError('Укажите email для ответа')
      return
    }
    if (!trimmedMessage) {
      setError('Введите текст сообщения')
      return
    }

    setLoading(true)
    try {
      await siteSubmitContact({
        name: name.trim(),
        email: trimmedEmail,
        message: trimmedMessage,
        app_slug: appSlug || undefined,
      })
      setOk(true)
      setName('')
      setEmail('')
      setMessage('')
    } catch (err) {
      if (err instanceof SiteApiError) {
        setError(err.message)
      } else {
        setError(err instanceof Error ? err.message : 'Не удалось отправить')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="contact-form" onSubmit={handleSubmit} noValidate>
      <p className="contact-form-lead">
        Напишите нам — ответим на указанный email. Сообщения попадают в общую
        админку обратной связи.
      </p>

      {error && <p className="contact-form-error" role="alert">{error}</p>}
      {ok && (
        <p className="contact-form-ok" role="status">
          Сообщение отправлено. Спасибо!
        </p>
      )}

      <label className="contact-form-field">
        <span>Имя</span>
        <input
          type="text"
          name="name"
          autoComplete="name"
          maxLength={120}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Как к вам обращаться"
        />
      </label>

      <label className="contact-form-field">
        <span>
          Email <em>*</em>
        </span>
        <input
          type="email"
          name="email"
          autoComplete="email"
          required
          maxLength={254}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
        />
      </label>

      <label className="contact-form-field">
        <span>
          Сообщение <em>*</em>
        </span>
        <textarea
          name="message"
          required
          rows={5}
          maxLength={4000}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Вопрос, предложение или проблема"
        />
      </label>

      <button type="submit" className="contact-form-submit" disabled={loading}>
        {loading ? 'Отправка…' : 'Отправить'}
      </button>
    </form>
  )
}
