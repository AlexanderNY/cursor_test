import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useParams, useSearchParams } from 'react-router-dom'
import { LabPythonRunner } from '@/components/lab-python-runner'
import { LabSqlRunner } from '@/components/lab-sql-runner'
import {
  isGitTrainerEpisode,
  LabGitRunner,
} from '@/components/lab-git-runner'
import { LearnContent } from '@/components/learn-content'
import { MermaidBlock } from '@/components/learn-mermaid'
import { LearnPostBadges } from '@/components/learn-post-badges'
import { PageShell } from '@/components/page-shell'
import { StructuredPostView } from '@/components/structured-post-view'
import { levelLabel, profileLabel } from '@/data/learn/labels'
import { safeHref, safeImageSrc } from '@/data/safe-url'
import { formatPublishDate, isPostPublished } from '@/data/learn/learn-store'
import { usePageSeo } from '@/data/learn/use-page-seo'
import {
  getAdjacentPosts,
  getPublishedPosts,
  rubricTitleById,
  useLearnPost,
  useLearnPosts,
} from '@/data/learn/use-learn-posts'
import { useSiteLearnProgress } from '@/data/site/use-learn-progress'
import { hydrateLearnStructured } from '@/data/site/structured-post'
import { ARTICLE_MNEMONICS } from '@/data/mnemonics/article-mnemonics'
import { practiceForSlug } from '@/game/practice/links'

type LearnTab = 'article' | 'lab' | 'cheatsheet'

function learnTabFromQuery(value: string | null): LearnTab {
  if (value === 'lab' || value === 'cheatsheet' || value === 'article') {
    return value
  }
  return 'article'
}

const tabs: { id: LearnTab; label: string }[] = [
  { id: 'article', label: 'Статья' },
  { id: 'lab', label: 'Лаба' },
  { id: 'cheatsheet', label: 'Шпаргалка' },
]

export function LearnEpisodePage() {
  const { slug = '' } = useParams()
  const [searchParams] = useSearchParams()
  const isPreview = searchParams.get('preview') === '1'
  const { post: episode, isReady } = useLearnPost(slug, { preview: isPreview })
  const { posts } = useLearnPosts()
  const [activeTab, setActiveTab] = useState<LearnTab>(() =>
    learnTabFromQuery(searchParams.get('tab')),
  )
  const {
    completedSlugs,
    isAuthed,
    setCompleted,
    isReady: progressReady,
  } = useSiteLearnProgress()
  const [progressBusy, setProgressBusy] = useState(false)

  useEffect(() => {
    setActiveTab(learnTabFromQuery(searchParams.get('tab')))
  }, [slug, searchParams])

  const hydrated = useMemo(() => {
    if (!episode) {
      return null
    }
    const base = hydrateLearnStructured(episode.structured, {
      lab: episode.lab,
      cheatsheet: episode.cheatsheet,
      cheatsheetFormat: episode.cheatsheetFormat,
      diagram: episode.diagram,
    })
    if ((base.mnemonics || []).length > 0) {
      return base
    }
    const extra = ARTICLE_MNEMONICS[episode.slug]
    if (!extra) {
      return base
    }
    return { ...base, mnemonics: [extra] }
  }, [episode])

  const seoDescription =
    episode?.seoDescription?.trim() ||
    episode?.excerpt?.trim() ||
    hydrated?.intro?.trim().slice(0, 400) ||
    ''
  const seoTitle = episode
    ? episode.seoTitle?.trim() || `${episode.title} · Learn · 9to18`
    : undefined
  const canonical =
    episode?.canonicalUrl?.trim() ||
    (episode ? `https://9to18.ru/game/learn/${episode.slug}` : undefined)

  usePageSeo({
    title: seoTitle,
    description: seoDescription,
    image: episode?.coverUrl?.trim() || undefined,
    canonical,
    keywords:
      episode?.seoKeywords?.length
        ? episode.seoKeywords
        : episode?.tags?.length
          ? episode.tags
          : undefined,
  })

  if (!isReady) {
    return (
      <PageShell content="article">
        <p className="learn-section-note">Загрузка…</p>
      </PageShell>
    )
  }

  if (!episode) {
    return <Navigate to="/game/learn" replace />
  }

  const isLive = isPostPublished(episode)

  if (!isLive && !isPreview) {
    return (
      <PageShell content="article">
        <Link to="/game/learn" className="back-link">
          ← К оглавлению Learn
        </Link>
        <header className="learn-episode-header">
          <p className="learn-eyebrow">{episode.episode}</p>
          <h1 className="learn-title">{episode.title}</h1>
          <p className="learn-lead">
            Выпуск ещё не опубликован. Дата публикации:{' '}
            <strong>{formatPublishDate(episode.publishedAt)}</strong>
          </p>
        </header>
      </PageShell>
    )
  }

  const practiceLink = practiceForSlug(episode.slug)
  const rubricTitle = rubricTitleById(episode.rubricId)
  const adjacent = getAdjacentPosts(getPublishedPosts(posts), episode.slug)
  const isDone = completedSlugs.has(episode.slug)
  const labContent = (hydrated?.lab || episode.lab || '').trim()
  const cheatsheetHtml = (hydrated?.cheatsheetHtml || '').trim()
  const cheatsheetLegacy = episode.cheatsheet.trim()
  const hasLab = Boolean(labContent)
  const hasCheatsheet = Boolean(cheatsheetHtml || cheatsheetLegacy)
  const visibleTabs = tabs.filter((tab) => {
    if (tab.id === 'article') return true
    if (tab.id === 'lab') return hasLab
    if (tab.id === 'cheatsheet') return hasCheatsheet
    return false
  })
  const shownTab: LearnTab =
    activeTab === 'lab' && !hasLab
      ? 'article'
      : activeTab === 'cheatsheet' && !hasCheatsheet
        ? 'article'
        : activeTab

  async function toggleProgress() {
    if (!isAuthed) {
      return
    }
    setProgressBusy(true)
    try {
      await setCompleted(episode!.slug, !isDone)
    } finally {
      setProgressBusy(false)
    }
  }

  return (
    <PageShell content="article">
      <Link to="/game/learn" className="back-link">
        ← К оглавлению Learn
      </Link>

      <header className="learn-episode-header">
        {safeImageSrc(episode.coverUrl) ? (
          <div className="learn-cover">
            <img src={safeImageSrc(episode.coverUrl) || undefined} alt="" />
          </div>
        ) : null}
        <p className="learn-eyebrow">
          {episode.episode}
          {rubricTitle ? ` · ${rubricTitle}` : ''}
        </p>
        <h1 className="learn-title">{episode.title}</h1>
        <LearnPostBadges
          profiles={episode.profiles}
          level={episode.level}
          tags={episode.tags}
          durationMin={episode.durationMin}
        />
        {episode.author?.trim() ? (
          <p className="learn-section-note learn-author">
            Автор:{' '}
            {safeHref(episode.authorUrl) ? (
              <a href={safeHref(episode.authorUrl) || undefined} target="_blank" rel="noreferrer">
                {episode.author.trim()}
              </a>
            ) : (
              episode.author.trim()
            )}
          </p>
        ) : null}
        {episode.excerpt?.trim() ? (
          <p className="learn-lead">{episode.excerpt.trim()}</p>
        ) : null}
        {episode.prerequisites?.length ? (
          <p className="learn-section-note">
            Сначала пройдите:{' '}
            {episode.prerequisites.map((prereq, index) => (
              <span key={prereq}>
                {index > 0 ? ', ' : null}
                <Link to={`/game/learn/${prereq}`}>{prereq}</Link>
              </span>
            ))}
          </p>
        ) : null}
        <p className="learn-section-note">
          {isLive
            ? `Опубликовано ${formatPublishDate(episode.publishedAt)}`
            : `Превью · публикация ${formatPublishDate(episode.publishedAt)}`}
          {episode.profiles?.length
            ? ` · ${episode.profiles.map((id) => profileLabel(id)).join(', ')}`
            : ''}
          {episode.level ? ` · ${levelLabel(episode.level)}` : ''}
        </p>
        <div className="learn-admin-actions">
          {isAuthed && progressReady ? (
            <button
              type="button"
              className="learn-admin-btn learn-admin-btn-primary"
              disabled={progressBusy}
              onClick={() => void toggleProgress()}
            >
              {isDone ? 'Снять отметку «пройдено»' : 'Отметить пройденным'}
            </button>
          ) : (
            <Link to="/login" className="learn-admin-btn learn-admin-btn-primary">
              Войти, чтобы отмечать прогресс
            </Link>
          )}
          {isAuthed && isDone ? (
            <Link to="/game/hh-resume" className="learn-admin-btn">
              Добавить в резюме
            </Link>
          ) : null}
          <Link to={`/game/learn/admin/${episode.slug}`} className="learn-admin-btn">
            Редактировать
          </Link>
          {practiceLink ? (
            <Link to={practiceLink.href} className="learn-admin-btn">
              {practiceLink.label}
            </Link>
          ) : null}
        </div>
      </header>

      {visibleTabs.length > 1 ? (
        <div className="learn-tabs" role="tablist" aria-label="Разделы выпуска">
          {visibleTabs.map((tab) => {
            const isActive = shownTab === tab.id
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                id={`tab-${tab.id}`}
                aria-selected={isActive}
                aria-controls={`panel-${tab.id}`}
                className={isActive ? 'learn-tab is-active' : 'learn-tab'}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            )
          })}
        </div>
      ) : null}

      <div
        id={`panel-${shownTab}`}
        role="tabpanel"
        aria-labelledby={`tab-${shownTab}`}
        className="learn-panel"
      >
        {shownTab === 'article' &&
          (hydrated ? (
            <>
              <StructuredPostView
                post={hydrated}
                appSlug="learn"
                postSlug={episode.slug}
                sourceType="learn"
              />
              {episode.links.length > 0 && (
                <section className="learn-links" aria-labelledby="learn-links-heading">
                  <h2 id="learn-links-heading" className="learn-panel-heading">
                    Ссылки
                  </h2>
                  <ul>
                    {episode.links
                      .filter((link) => link.href !== '#')
                      .map((link) => {
                        const href = safeHref(link.href)
                        const isInternal = Boolean(href?.startsWith('/') && !href.startsWith('//'))
                        const isExternal = Boolean(
                          href?.startsWith('http://') || href?.startsWith('https://'),
                        )
                        return (
                          <li key={link.href + link.label}>
                            {href && isInternal ? (
                              <Link to={href}>{link.label}</Link>
                            ) : href && isExternal ? (
                              <a href={href} target="_blank" rel="noreferrer">
                                {link.label}
                              </a>
                            ) : (
                              <span>{link.label}</span>
                            )}
                          </li>
                        )
                      })}
                    {episode.links
                      .filter((link) => link.href === '#')
                      .map((link) => (
                        <li key={link.label} className="learn-link-local">
                          {link.label}
                        </li>
                      ))}
                  </ul>
                </section>
              )}
            </>
          ) : (
            <>
              <LearnContent content={episode.theory} format={episode.theoryFormat} />
              {episode.diagram.trim() ? (
                <section className="learn-diagram" aria-labelledby="learn-diagram-heading">
                  <h2 id="learn-diagram-heading" className="learn-panel-heading">
                    Схема
                  </h2>
                  <MermaidBlock chart={episode.diagram} />
                </section>
              ) : null}
              {episode.links.length > 0 && (
                <section className="learn-links" aria-labelledby="learn-links-heading">
                  <h2 id="learn-links-heading" className="learn-panel-heading">
                    Ссылки
                  </h2>
                  <ul>
                    {episode.links.map((link) => (
                      <li key={link.href + link.label}>{link.label}</li>
                    ))}
                  </ul>
                </section>
              )}
            </>
          ))}

        {shownTab === 'lab' && hasLab && (
          <>
            <LearnContent content={labContent} format={episode.labFormat} />
            {episode.episode.toUpperCase().startsWith('SQL') ? (
              <LabSqlRunner labMarkdown={labContent} episode={episode.episode} />
            ) : isGitTrainerEpisode(episode.episode, episode.slug) ? (
              <LabGitRunner
                labMarkdown={labContent}
                episode={episode.episode}
                slug={episode.slug}
              />
            ) : (
              <LabPythonRunner labMarkdown={labContent} />
            )}
          </>
        )}

        {shownTab === 'cheatsheet' && hasCheatsheet && (
          <section className="learn-cheatsheet" aria-labelledby="learn-cheat-heading">
            <h2 id="learn-cheat-heading" className="learn-panel-heading">
              Шпаргалка
            </h2>
            {cheatsheetHtml ? (
              <LearnContent content={cheatsheetHtml} format="html" />
            ) : (
              <LearnContent content={cheatsheetLegacy} format={episode.cheatsheetFormat} />
            )}
          </section>
        )}
      </div>

      <nav className="learn-pager" aria-label="Соседние выпуски">
        {adjacent.prev ? (
          <Link to={`/game/learn/${adjacent.prev.slug}`} className="learn-pager-link">
            ← {adjacent.prev.episode} {adjacent.prev.shortTitle}
          </Link>
        ) : (
          <span />
        )}
        {adjacent.next ? (
          <Link to={`/game/learn/${adjacent.next.slug}`} className="learn-pager-link learn-pager-next">
            {adjacent.next.episode} {adjacent.next.shortTitle} →
          </Link>
        ) : (
          <span />
        )}
      </nav>
    </PageShell>
  )
}
