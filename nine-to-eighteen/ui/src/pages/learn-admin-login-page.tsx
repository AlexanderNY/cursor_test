import { Link, useLocation } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { getSiteAuthSession, isSuperAdmin } from '@/data/site/site-auth'

export function LearnAdminLoginPage() {
  const location = useLocation()
  const from =
    (location.state as { from?: string } | null)?.from || '/game/learn/admin'
  const session = getSiteAuthSession()
  const canEdit = isSuperAdmin(session)

  return (
    <PageShell>
      <Link to="/game/learn" className="back-link">
        ← К Learn
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Learn · Админка</p>
        <h1 className="learn-title">Вход</h1>
        <p className="learn-lead">
          Редактирование Learn доступно супер-админу сайта 9to18. Войдите в аккаунт сайта с ролью{' '}
          <strong>site_admin</strong>.
        </p>
      </header>
      {canEdit ? (
        <p className="learn-section-note">
          Вы уже вошли как <strong>{session?.username}</strong>.{' '}
          <Link to={from}>Открыть админку →</Link>
        </p>
      ) : (
        <p className="learn-section-note">
          <Link to={`/login?next=${encodeURIComponent(from)}`}>Войти на сайт</Link>
          {' · '}
          <Link to="/account">Личный кабинет</Link>
        </p>
      )}
    </PageShell>
  )
}
