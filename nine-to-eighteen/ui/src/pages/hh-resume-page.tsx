import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import {
  resumeCreate,
  resumeDelete,
  resumeList,
  type SiteResumeSummary,
} from '@/data/site/resume-api'
import { getSiteAuthSession } from '@/data/site/site-auth'

/** Список версий резюме (несколько на пользователя). */
export function HhResumePage() {
  const session = getSiteAuthSession()
  const navigate = useNavigate()
  const [items, setItems] = useState<SiteResumeSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const list = await resumeList()
      setItems(list)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить список')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!session) {
      setLoading(false)
      return
    }
    void load()
  }, [session, load])

  async function onCreate(copyFrom?: string) {
    setBusy(true)
    setError('')
    setOk('')
    try {
      const created = await resumeCreate(
        copyFrom
          ? { version_name: 'Новая версия', copy_from: copyFrom }
          : { version_name: items.length === 0 ? 'Основное' : `Версия ${items.length + 1}` },
      )
      setOk('Резюме создано')
      navigate(`/game/hh-resume/${created.id}/edit`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать')
    } finally {
      setBusy(false)
    }
  }

  async function onDelete(id: string, name: string) {
    if (!window.confirm(`Удалить резюме «${name}»?`)) {
      return
    }
    setBusy(true)
    setError('')
    try {
      await resumeDelete(id)
      setOk('Удалено')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить')
    } finally {
      setBusy(false)
    }
  }

  if (!session) {
    return (
      <PageShell>
        <Link to="/" className="back-link">
          ← На главную
        </Link>
        <header className="learn-header">
          <p className="learn-eyebrow">Сервис · Резюме</p>
          <h1 className="learn-title">Резюме</h1>
          <p className="learn-lead">
            Нужен аккаунт 9to18: несколько версий резюме, опросник и навыки из Learn.
          </p>
          <p className="learn-section-note">
            <Link to="/login">Войти</Link>
            {' · '}
            <Link to="/register">Регистрация</Link>
          </p>
        </header>
      </PageShell>
    )
  }

  return (
    <PageShell>
      <Link to="/" className="back-link">
        ← На главную
      </Link>

      <header className="learn-header">
        <p className="learn-eyebrow">Сервис · Резюме</p>
        <h1 className="learn-title">Мои резюме</h1>
        <p className="learn-lead">
          Несколько версий под разные роли (например Backend и Data Analyst). Анкета и фото — в{' '}
          <Link to="/account">кабинете</Link>.
        </p>
        {error ? <p className="learn-admin-error">{error}</p> : null}
        {ok ? <p className="learn-admin-ok">{ok}</p> : null}
      </header>

      <div className="account-actions" style={{ marginBottom: '1.25rem' }}>
        <button
          type="button"
          className="learn-admin-btn learn-admin-btn-primary"
          disabled={busy}
          onClick={() => void onCreate()}
        >
          Создать резюме
        </button>
        <Link to="/account" className="learn-admin-btn">
          Анкета
        </Link>
      </div>

      {loading ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : items.length === 0 ? (
        <p className="learn-section-note">
          Пока нет резюме. Создайте первое — затем пройдите опросник и обогатите навыками из Learn.
        </p>
      ) : (
        <ul className="hh-resume-version-list">
          {items.map((item) => (
            <li key={item.id} className="hh-resume-version-card">
              <div>
                <h2 className="account-subheading">{item.versionName}</h2>
                <p className="learn-section-note">
                  {item.specialization || item.title || 'Без специализации'}
                  {item.updatedAt ? ` · ${new Date(item.updatedAt).toLocaleString('ru-RU')}` : ''}
                </p>
              </div>
              <div className="account-actions">
                <Link
                  to={`/game/hh-resume/${item.id}`}
                  className="learn-admin-btn learn-admin-btn-primary"
                >
                  Открыть
                </Link>
                <Link to={`/game/hh-resume/${item.id}/edit`} className="learn-admin-btn">
                  Доработать
                </Link>
                <Link to={`/game/hh-resume/${item.id}/quiz`} className="learn-admin-btn">
                  Опросник
                </Link>
                <button
                  type="button"
                  className="learn-admin-btn"
                  disabled={busy}
                  onClick={() => void onCreate(item.id)}
                >
                  Дублировать
                </button>
                <button
                  type="button"
                  className="learn-admin-btn"
                  disabled={busy}
                  onClick={() => void onDelete(item.id, item.versionName)}
                >
                  Удалить
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </PageShell>
  )
}
