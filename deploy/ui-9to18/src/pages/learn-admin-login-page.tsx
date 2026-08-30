import { FormEvent, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { apiGetProfile, apiLogin } from '@/data/learn/learn-api'
import { canEditLearn, clearLearnAuthSession, setLearnAuthSession } from '@/data/learn/learn-auth'

export function LearnAdminLoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const from =
    (location.state as { from?: string } | null)?.from || '/game/learn/admin'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const tokens = await apiLogin(username.trim(), password)
      setLearnAuthSession({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        role: 'guest',
        username: username.trim(),
      })
      const profile = await apiGetProfile()
      if (!canEditLearn(profile.role)) {
        clearLearnAuthSession()
        setError('Нужна роль admin или author')
        return
      }
      setLearnAuthSession({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        role: profile.role || 'guest',
        username: profile.username || username.trim(),
      })
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка входа')
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageShell>
      <Link to="/game/learn" className="back-link">
        ← К Learn
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Learn · Админка</p>
        <h1 className="learn-title">Вход</h1>
        <p className="learn-lead">
          Аккаунт CopyParse с ролью <strong>admin</strong> или <strong>author</strong>. Контент
          хранится на сервере, не в localStorage.
        </p>
      </header>
      <form className="learn-admin-form" onSubmit={(e) => void handleSubmit(e)}>
        {error ? <p className="learn-section-note" style={{ color: '#b91c1c' }}>{error}</p> : null}
        <label className="learn-admin-field">
          <span>Логин</span>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </label>
        <label className="learn-admin-field">
          <span>Пароль</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        <button type="submit" className="learn-admin-link" disabled={loading}>
          {loading ? 'Вход…' : 'Войти'}
        </button>
      </form>
    </PageShell>
  )
}
