import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { LearnContent } from '@/components/learn-content'
import { StructuredPostView } from '@/components/structured-post-view'
import {
  siteGetApp,
  siteListPosts,
  type SiteApp,
  type SitePost,
} from '@/data/site/site-api'
import { parsePostBody } from '@/data/site/structured-post'
import { canManageApp, isSuperAdmin } from '@/data/site/site-auth'

export function AppBlogPage() {
  const { slug = '' } = useParams()
  const [app, setApp] = useState<SiteApp | null>(null)
  const [posts, setPosts] = useState<SitePost[]>([])
  const [error, setError] = useState('')
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    setReady(false)
    Promise.all([siteGetApp(slug), siteListPosts(slug)])
      .then(([nextApp, nextPosts]) => {
        if (cancelled) return
        setApp(nextApp)
        setPosts(nextPosts)
        setError('')
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Не удалось загрузить')
        setApp(null)
        setPosts([])
      })
      .finally(() => {
        if (!cancelled) setReady(true)
      })
    return () => {
      cancelled = true
    }
  }, [slug])

  return (
    <PageShell>
      <Link to="/" className="back-link">
        ← На главную
      </Link>
      {!ready ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : error || !app ? (
        <p className="learn-admin-error">{error || 'Приложение не найдено'}</p>
      ) : (
        <>
          <header className="learn-header">
            <p className="learn-eyebrow">
              {app.emoji ? `${app.emoji} ` : ''}
              Страница сервиса
            </p>
            <h1 className="learn-title">{app.title}</h1>
            <p className="learn-lead">{app.subtitle}</p>
            {app.description ? (
              <div className="app-description">
                <LearnContent content={app.description} format="markdown" />
              </div>
            ) : null}
            <div className="learn-admin-actions">
              {app.appPath ? (
                <Link to={app.appPath} className="learn-admin-btn learn-admin-btn-primary">
                  Открыть приложение
                </Link>
              ) : null}
              {app.externalHref ? (
                <a
                  href={app.externalHref}
                  className="learn-admin-btn"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {app.slug === 'e2e-tester' ? 'Панель тестера ↗' : 'Внешний сайт ↗'}
                </a>
              ) : null}
              {canManageApp(app.slug) ? (
                <Link to={`/admin/apps/${app.slug}`} className="learn-admin-btn">
                  {isSuperAdmin() ? 'Супер-админ · правка' : 'Кабинет владельца'}
                </Link>
              ) : null}
            </div>
          </header>

          <section aria-labelledby="app-blog-list">
            <h2 id="app-blog-list" className="learn-section-title">
              Блог сервиса
            </h2>
            {posts.length === 0 ? (
              <p className="learn-section-note">Пока нет опубликованных записей.</p>
            ) : (
              <ul className="learn-episode-list">
                {posts.map((post) => {
                  const { structured } = parsePostBody(post.body)
                  const excerpt = structured
                    ? structured.intro.slice(0, 160)
                    : post.body.replace(/[#*_`>\-\[\]()]/g, ' ').slice(0, 160)
                  return (
                    <li key={post.id}>
                      <Link
                        to={`/app/${app.slug}/${post.slug}`}
                        className="learn-episode-card"
                      >
                        <span className="learn-episode-title">{post.title}</span>
                        {excerpt ? (
                          <span className="learn-section-note">{excerpt.trim()}…</span>
                        ) : null}
                      </Link>
                    </li>
                  )
                })}
              </ul>
            )}
          </section>
        </>
      )}
    </PageShell>
  )
}

export function AppPostPage() {
  const { slug = '', postSlug = '' } = useParams()
  const [app, setApp] = useState<SiteApp | null>(null)
  const [post, setPost] = useState<SitePost | null>(null)
  const [error, setError] = useState('')
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    setReady(false)
    Promise.all([
      siteGetApp(slug),
      import('@/data/site/site-api').then((m) => m.siteGetPost(slug, postSlug)),
    ])
      .then(([nextApp, nextPost]) => {
        if (cancelled) return
        setApp(nextApp)
        setPost(nextPost)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Не найдено')
      })
      .finally(() => {
        if (!cancelled) setReady(true)
      })
    return () => {
      cancelled = true
    }
  }, [slug, postSlug])

  const parsed = post ? parsePostBody(post.body) : null

  return (
    <PageShell>
      <Link to={`/app/${slug}`} className="back-link">
        ← К сервису {app?.title || slug}
      </Link>
      {!ready ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : error || !post ? (
        <p className="learn-admin-error">{error || 'Запись не найдена'}</p>
      ) : (
        <>
          <header className="learn-episode-header">
            <p className="learn-eyebrow">{app?.title}</p>
            <h1 className="learn-title">{post.title}</h1>
          </header>
          {parsed?.structured ? (
            <StructuredPostView
              post={parsed.structured}
              appSlug={slug}
              postSlug={post.slug}
            />
          ) : (
            <LearnContent content={parsed?.legacyMarkdown || post.body} format="markdown" />
          )}
        </>
      )}
    </PageShell>
  )
}
