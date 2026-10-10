import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  resumeCreate,
  resumeList,
  type SiteResumeSummary,
} from '@/data/site/resume-api'

type HhResumePickPanelProps = {
  /** Path suffix after `/game/hh-resume/:id/` — e.g. `quiz` or `path`. */
  mode: 'quiz' | 'path'
  onPicked: (resumeId: string) => void
}

/** Choose an existing resume or create one — never auto-create on bare URLs. */
export function HhResumePickPanel({ mode, onPicked }: HhResumePickPanelProps) {
  const [items, setItems] = useState<SiteResumeSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const list = await resumeList()
        if (!cancelled) setItems(list)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Не удалось загрузить список')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  async function onCreate() {
    setBusy(true)
    setError('')
    try {
      const created = await resumeCreate({
        version_name: items.length === 0 ? 'Основное' : `Версия ${items.length + 1}`,
      })
      onPicked(created.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать резюме')
    } finally {
      setBusy(false)
    }
  }

  const title = mode === 'quiz' ? 'опросник' : 'путь'
  const latest = items[0]

  return (
    <div className="hh-quiz-card" style={{ maxWidth: '28rem' }}>
      <h2 className="account-subheading">Выберите резюме для {title}</h2>
      <p className="learn-section-note">
        Откройте существующую версию или создайте новую — автоматическое создание отключено.
      </p>
      {error ? <p className="learn-admin-error">{error}</p> : null}
      {loading ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : (
        <>
          {items.length > 0 ? (
            <ul className="account-list" style={{ listStyle: 'none', padding: 0 }}>
              {items.map((item) => (
                <li key={item.id} style={{ marginBottom: '0.5rem' }}>
                  <button
                    type="button"
                    className="learn-admin-btn learn-admin-btn-primary"
                    disabled={busy}
                    onClick={() => onPicked(item.id)}
                  >
                    {item.versionName || 'Без названия'}
                    {item.title ? ` · ${item.title}` : ''}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="learn-section-note">Пока нет версий резюме.</p>
          )}
          <div className="account-actions">
            <button
              type="button"
              className="learn-admin-btn learn-admin-btn-primary"
              disabled={busy}
              onClick={() => void onCreate()}
            >
              {busy ? '…' : 'Создать новое'}
            </button>
            {latest ? (
              <button
                type="button"
                className="learn-admin-btn"
                disabled={busy}
                onClick={() => onPicked(latest.id)}
              >
                Открыть последнее
              </button>
            ) : null}
            <Link to="/game/hh-resume" className="learn-admin-btn">
              К списку
            </Link>
          </div>
        </>
      )}
    </div>
  )
}
