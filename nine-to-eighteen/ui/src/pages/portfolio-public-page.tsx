import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import {
  portfolioGetPublic,
  type PublicPortfolio,
} from '@/data/site/portfolio-api'
import { SiteApiError } from '@/data/site/site-api'

export function PortfolioPublicPage() {
  const { handle = '' } = useParams<{ handle: string }>()
  const [page, setPage] = useState<PublicPortfolio | null>(null)
  const [loading, setLoading] = useState(true)
  const [missing, setMissing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setMissing(false)
    setError('')
    setPage(null)
    void portfolioGetPublic(handle)
      .then((data) => {
        if (!cancelled) setPage(data)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        if (err instanceof SiteApiError && err.status === 404) {
          setMissing(true)
          return
        }
        setError(err instanceof Error ? err.message : 'Не удалось открыть страницу')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [handle])

  return (
    <PageShell>
      <Link to="/" className="back-link">
        ← На главную
      </Link>
      {loading ? <p className="learn-section-note">Загрузка…</p> : null}
      {missing ? (
        <header className="learn-header">
          <p className="learn-eyebrow">Портфолио</p>
          <h1 className="learn-title">Страница не опубликована</h1>
          <p className="learn-lead">
            Адреса нет, либо владелец ещё не открыл страницу.{' '}
            <Link to="/game/portfolio">Собрать свою</Link>
          </p>
        </header>
      ) : null}
      {error ? <p className="learn-admin-error">{error}</p> : null}
      {page ? (
        <>
          <header className="learn-header">
            <p className="learn-eyebrow">Портфолио · /p/{page.handle}</p>
            <h1 className="learn-title">{page.displayName}</h1>
            {page.headline ? <p className="learn-lead">{page.headline}</p> : null}
            {page.city ? <p className="learn-section-note">{page.city}</p> : null}
          </header>
          {page.summary ? (
            <section className="info-section">
              <h2 className="section-block-title">О себе</h2>
              <p className="portfolio-text">{page.summary}</p>
            </section>
          ) : null}
          {page.pinnedResume ? (
            <section className="info-section">
              <h2 className="section-block-title">Резюме</h2>
              <p>
                <strong>{page.pinnedResume.title || page.pinnedResume.versionName}</strong>
                {page.pinnedResume.specialization
                  ? ` · ${page.pinnedResume.specialization}`
                  : ''}
              </p>
              {page.pinnedResume.about ? (
                <p className="portfolio-text">{page.pinnedResume.about}</p>
              ) : null}
            </section>
          ) : null}
          <div className="portfolio-grid">
            {page.cases.map((item) => (
              <article key={item.id} className="portfolio-case">
                <h2 className="learn-section-title">{item.title}</h2>
                {item.role ? <p className="learn-section-note">{item.role}</p> : null}
                {item.stack.length > 0 ? (
                  <p className="portfolio-case-meta">
                    {item.stack.map((tag) => (
                      <span key={tag} className="portfolio-chip">
                        {tag}
                      </span>
                    ))}
                  </p>
                ) : null}
                <h3 className="portfolio-label">Задача</h3>
                <p className="portfolio-text">{item.problem}</p>
                <h3 className="portfolio-label">Что сделано</h3>
                <p className="portfolio-text">{item.work}</p>
                <h3 className="portfolio-label">Результат</h3>
                <p className="portfolio-text">{item.outcome}</p>
                {item.certTrackTitle ? (
                  item.certCode ? (
                    <p>
                      <Link to={`/game/cert/${item.certCode}`} className="portfolio-chip">
                        Диплом: {item.certTrackTitle}
                      </Link>
                    </p>
                  ) : (
                    <p className="portfolio-chip">{item.certTrackTitle}</p>
                  )
                ) : null}
                {item.learn.length > 0 ? (
                  <ul className="contacts-list">
                    {item.learn.map((episode) => (
                      <li key={episode.slug}>
                        <Link to={`/game/learn/${episode.slug}`}>
                          {episode.episode ? `${episode.episode} · ` : ''}
                          {episode.title}
                        </Link>
                      </li>
                    ))}
                  </ul>
                ) : null}
                <p className="portfolio-actions">
                  {item.repoUrl ? (
                    <a href={item.repoUrl} target="_blank" rel="noopener noreferrer">
                      Репозиторий
                    </a>
                  ) : null}
                  {item.demoUrl ? (
                    <a href={item.demoUrl} target="_blank" rel="noopener noreferrer">
                      Демо
                    </a>
                  ) : null}
                </p>
              </article>
            ))}
          </div>
        </>
      ) : null}
    </PageShell>
  )
}
