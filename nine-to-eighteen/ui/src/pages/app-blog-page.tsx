import { useEffect, useState, type ReactNode } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { LearnContent } from '@/components/learn-content'
import { StructuredPostView } from '@/components/structured-post-view'
import {
  siteGetApp,
  siteListPosts,
  type SiteApp,
  type SitePost,
} from '@/data/site/site-api'
import { blogHref, blogPostHref, getSectionBySlug, serviceOpenTarget } from '@/data/sections'
import { safeHref } from '@/data/safe-url'
import { parsePostBody } from '@/data/site/structured-post'
import { canManageApp, isSuperAdmin } from '@/data/site/site-auth'

function PublicFrame({
  embedded,
  children,
  article,
}: {
  embedded: boolean
  children: ReactNode
  article?: boolean
}) {
  if (embedded) {
    return <div className="account-embed">{children}</div>
  }
  return <PageShell content={article ? 'article' : 'default'}>{children}</PageShell>
}

function sectionFallbackApp(slug: string): SiteApp | null {
  const section = getSectionBySlug(slug)
  if (!section) {
    return null
  }
  return {
    slug: section.slug,
    title: section.title,
    subtitle: section.subtitle,
    description: section.description,
    accent: section.accent,
    emoji: section.emoji || '',
    externalHref: section.href || '',
    appPath: section.appPath || '',
    isVisible: true,
    sortOrder: 0,
  }
}

export type AppBlogPageProps = {
  embedded?: boolean
  slug?: string
  onOpenPost?: (postSlug: string) => void
  onOpenAdmin?: () => void
}

export function AppBlogPage({
  embedded = false,
  slug: slugProp,
  onOpenPost,
  onOpenAdmin,
}: AppBlogPageProps = {}) {
  const { slug: slugParam = '' } = useParams()
  const slug = slugProp || slugParam
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
        const fallback = sectionFallbackApp(slug)
        if (fallback) {
          setApp(fallback)
          setPosts([])
          setError('')
          return
        }
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

  const openTarget = app
    ? serviceOpenTarget({
        slug: app.slug,
        appPath: app.appPath,
        href: app.externalHref,
      })
    : null
  const hasService = Boolean(openTarget && openTarget.href !== blogHref(slug))

  return (
    <PublicFrame embedded={embedded}>
      {embedded ? null : (
        <Link to="/" className="back-link">
          ← На главную
        </Link>
      )}
      {!ready ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : error || !app ? (
        <p className="learn-admin-error">{error || 'Приложение не найдено'}</p>
      ) : (
        <>
          <header className="learn-header">
            <p className="learn-eyebrow">
              {app.emoji ? `${app.emoji} ` : ''}
              Блог сервиса
            </p>
            <h1 className="learn-title">{app.title}</h1>
            <p className="learn-lead">{app.subtitle}</p>
            {app.description ? (
              <div className="app-description">
                <LearnContent content={app.description} format="markdown" />
              </div>
            ) : null}
            <div className="learn-admin-actions">
              {hasService && openTarget ? (
                openTarget.external ? (
                  <a
                    href={openTarget.href}
                    className="learn-admin-btn learn-admin-btn-primary"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Открыть сервис ↗
                  </a>
                ) : (
                  <Link to={openTarget.href} className="learn-admin-btn learn-admin-btn-primary">
                    Открыть сервис
                  </Link>
                )
              ) : null}
              {canManageApp(app.slug) ? (
                onOpenAdmin ? (
                  <button type="button" className="learn-admin-btn" onClick={onOpenAdmin}>
                    {isSuperAdmin() ? 'Супер-админ · правка' : 'Кабинет владельца'}
                  </button>
                ) : (
                  <Link to={`/admin/apps/${app.slug}`} className="learn-admin-btn">
                    {isSuperAdmin() ? 'Супер-админ · правка' : 'Кабинет владельца'}
                  </Link>
                )
              ) : null}
            </div>
          </header>

          <section aria-labelledby="app-blog-list">
            <h2 id="app-blog-list" className="learn-section-title">
              Записи
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
                      {onOpenPost ? (
                        <button
                          type="button"
                          className="learn-episode-card"
                          onClick={() => onOpenPost(post.slug)}
                        >
                          <span className="learn-episode-title">{post.title}</span>
                          {excerpt ? (
                            <span className="learn-section-note">{excerpt.trim()}…</span>
                          ) : null}
                        </button>
                      ) : (
                        <Link
                          to={blogPostHref(app.slug, post.slug)}
                          className="learn-episode-card"
                        >
                          <span className="learn-episode-title">{post.title}</span>
                          {excerpt ? (
                            <span className="learn-section-note">{excerpt.trim()}…</span>
                          ) : null}
                        </Link>
                      )}
                    </li>
                  )
                })}
              </ul>
            )}
          </section>
        </>
      )}
    </PublicFrame>
  )
}

export type AppPostPageProps = {
  embedded?: boolean
  slug?: string
  postSlug?: string
  onBack?: () => void
}

export function AppPostPage({
  embedded = false,
  slug: slugProp,
  postSlug: postSlugProp,
  onBack,
}: AppPostPageProps = {}) {
  const { slug: slugParam = '', postSlug: postSlugParam = '' } = useParams()
  const slug = slugProp || slugParam
  const postSlug = postSlugProp || postSlugParam
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
    <PublicFrame embedded={embedded} article>
      {onBack ? (
        <button type="button" className="back-link" onClick={onBack}>
          ← К блогу {app?.title || slug}
        </button>
      ) : (
        <Link to={blogHref(slug)} className="back-link">
          ← К блогу {app?.title || slug}
        </Link>
      )}
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
    </PublicFrame>
  )
}

/** Old `/app/:slug` bookmarks open the product, not the blog. */
export function AppEntryRedirect() {
  const { slug = '' } = useParams()
  const [target, setTarget] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const fallback = getSectionBySlug(slug)
    const go = (appPath: string, externalHref: string) => {
      if (cancelled) {
        return
      }
      const next = serviceOpenTarget({ slug, appPath, href: externalHref })
      if (next.external) {
        const safe = safeHref(next.href)
        if (safe) {
          window.location.replace(safe)
          return
        }
        setTarget(blogHref(slug))
        return
      }
      setTarget(next.href)
    }
    siteGetApp(slug)
      .then((app) => go(app.appPath, app.externalHref))
      .catch(() => go(fallback?.appPath || '', fallback?.href || ''))
    return () => {
      cancelled = true
    }
  }, [slug])

  if (!target) {
    return (
      <PageShell>
        <p className="learn-section-note">Открываем сервис…</p>
      </PageShell>
    )
  }
  return <Navigate to={target} replace />
}

/** Old `/app/:slug/:postSlug` bookmarks land on the blog article. */
export function LegacyAppPostRedirect() {
  const { slug = '', postSlug = '' } = useParams()
  return <Navigate to={blogPostHref(slug, postSlug)} replace />
}
