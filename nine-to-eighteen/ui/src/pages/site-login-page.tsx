import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import {
  siteForgotPassword,
  siteLogin,
  siteRegister,
  siteResetPassword,
  SiteApiError,
} from '@/data/site/site-api'
import { setSiteAuthSession } from '@/data/site/site-auth'

type AuthMode = 'login' | 'register' | 'reset'

function modeFromPath(pathname: string, wantReset: boolean): AuthMode {
  if (wantReset) {
    return 'reset'
  }
  return pathname.startsWith('/register') ? 'register' : 'login'
}

/** Only same-origin relative paths (block //evil.com and external URLs). */
function safeReturnPath(raw: string | null | undefined): string | null {
  if (!raw) return null
  const value = raw.trim()
  if (!value.startsWith('/')) return null
  if (value.startsWith('//')) return null
  if (value.includes('://')) return null
  return value
}

export function SiteLoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const from = useMemo(() => {
    const fromState = safeReturnPath(
      (location.state as { from?: string } | null)?.from,
    )
    const fromQuery = safeReturnPath(searchParams.get('next'))
    return fromState || fromQuery || '/account'
  }, [location.state, searchParams])
  const [mode, setMode] = useState<AuthMode>(() =>
    modeFromPath(location.pathname, searchParams.get('reset') === '1'),
  )
  const [login, setLogin] = useState('')
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setMode(modeFromPath(location.pathname, searchParams.get('reset') === '1'))
    setError('')
    setMessage('')
  }, [location.pathname, searchParams])

  function switchMode(next: AuthMode) {
    setMode(next)
    setError('')
    setMessage('')
    if (next === 'reset') {
      navigate('/login?reset=1', { replace: true, state: location.state })
      return
    }
    navigate(next === 'register' ? '/register' : '/login', {
      replace: true,
      state: location.state,
    })
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)
    try {
      if (mode === 'reset') {
        if (!resetToken.trim()) {
          const forgot = await siteForgotPassword(login.trim())
          if (forgot.resetToken) {
            setResetToken(forgot.resetToken)
            setMessage('Токен сброса создан (режим разработки — скопируйте токен ниже).')
          } else {
            setMessage(
              forgot.detail ||
                'Если аккаунт существует, инструкции по сбросу будут отправлены.',
            )
          }
          return
        }
        await siteResetPassword({
          token: resetToken.trim(),
          new_password: newPassword,
        })
        setMessage('Пароль обновлён. Можно войти.')
        setMode('login')
        navigate('/login', { replace: true, state: location.state })
        return
      }
      const result =
        mode === 'login'
          ? await siteLogin({ login: login.trim(), password })
          : await siteRegister({
              email: email.trim(),
              username: username.trim(),
              password,
            })
      setSiteAuthSession({
        accessToken: result.access_token,
        siteRole: result.user.siteRole,
        username: result.user.username,
        email: result.user.email,
        appAdmin: result.user.appAdmin || [],
      })
      navigate(from, { replace: true })
    } catch (err) {
      if (err instanceof SiteApiError) {
        setError(err.message)
      } else {
        setError(err instanceof Error ? err.message : 'Ошибка')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageShell>
      <Link to="/" className="back-link">
        ← На главную
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">9to18 · аккаунт</p>
        <h1 className="learn-title">
          {mode === 'login' ? 'Войти' : mode === 'register' ? 'Регистрация' : 'Сброс пароля'}
        </h1>
        <p className="learn-lead">
          {mode === 'register'
            ? 'Регистрация создаёт аккаунт пользователя: чтение всех страниц и блогов сервисов, личный кабинет и связь с разработчиками.'
            : mode === 'reset'
              ? 'Запросите сброс по email/username. Если SMTP недоступен, вставьте токен вручную (в dev он может появиться в ответе API).'
              : 'Вход в контур сайта 9to18 (отдельно от CopyParse).'}
        </p>
      </header>

      <div className="learn-tabs" role="tablist">
        <button
          type="button"
          className={`learn-tab${mode === 'login' ? ' is-active' : ''}`}
          onClick={() => switchMode('login')}
        >
          Вход
        </button>
        <button
          type="button"
          className={`learn-tab${mode === 'register' ? ' is-active' : ''}`}
          onClick={() => switchMode('register')}
        >
          Регистрация
        </button>
        <button
          type="button"
          className={`learn-tab${mode === 'reset' ? ' is-active' : ''}`}
          onClick={() => switchMode('reset')}
        >
          Сброс
        </button>
      </div>

      <form className="learn-admin-form" onSubmit={handleSubmit} style={{ maxWidth: '22rem' }}>
        {mode === 'login' ? (
          <label className="learn-admin-field">
            <span>Email или username</span>
            <input
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              autoComplete="username"
              required
            />
          </label>
        ) : null}
        {mode === 'register' ? (
          <>
            <label className="learn-admin-field">
              <span>Email</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </label>
            <label className="learn-admin-field">
              <span>Username (латиница, цифры, _)</span>
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
                minLength={3}
                maxLength={64}
                pattern="[A-Za-z0-9_]+"
                title="Только латинские буквы, цифры и подчёркивание"
              />
            </label>
          </>
        ) : null}
        {mode === 'reset' ? (
          <>
            <label className="learn-admin-field">
              <span>Email или username</span>
              <input
                value={login}
                onChange={(e) => setLogin(e.target.value)}
                autoComplete="username"
                required={!resetToken}
              />
            </label>
            <label className="learn-admin-field">
              <span>Токен сброса</span>
              <input
                value={resetToken}
                onChange={(e) => setResetToken(e.target.value)}
                placeholder="Вставьте токен, если он у вас есть"
              />
            </label>
            {resetToken ? (
              <label className="learn-admin-field">
                <span>Новый пароль</span>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  minLength={8}
                  required
                  autoComplete="new-password"
                />
              </label>
            ) : null}
          </>
        ) : (
          <label className="learn-admin-field">
            <span>Пароль</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              required
              minLength={mode === 'register' ? 8 : 1}
            />
          </label>
        )}
        {message ? <p className="learn-admin-ok">{message}</p> : null}
        {error ? <p className="learn-admin-error">{error}</p> : null}
        <button type="submit" className="learn-admin-btn learn-admin-btn-primary" disabled={loading}>
          {loading
            ? '…'
            : mode === 'login'
              ? 'Войти'
              : mode === 'register'
                ? 'Создать аккаунт'
                : resetToken
                  ? 'Задать новый пароль'
                  : 'Запросить сброс'}
        </button>
      </form>
    </PageShell>
  )
}
