import { useEffect, useState } from 'react'
import { Link, Navigate, useParams, useSearchParams } from 'react-router-dom'
import { LearnContent } from '@/components/learn-content'
import { MermaidBlock } from '@/components/learn-mermaid'
import { PageShell } from '@/components/page-shell'
import { formatPublishDate, isPostPublished } from '@/data/learn/learn-store'
import {
  getAdjacentPosts,
  getPublishedPosts,
  rubricTitleById,
  useLearnPost,
  useLearnPosts,
} from '@/data/learn/use-learn-posts'

type LearnTab = 'theory' | 'lab' | 'cheatsheet'

const tabs: { id: LearnTab; label: string }[] = [
  { id: 'theory', label: 'Теория' },
  { id: 'lab', label: 'Лаба' },
  { id: 'cheatsheet', label: 'Шпаргалка' },
]

export function LearnEpisodePage() {
  const { slug = '' } = useParams()
  const [searchParams] = useSearchParams()
  const isPreview = searchParams.get('preview') === '1'
  const { post: episode, isReady } = useLearnPost(slug)
  const { posts } = useLearnPosts()
  const [activeTab, setActiveTab] = useState<LearnTab>('theory')

  useEffect(() => {
    setActiveTab('theory')
  }, [slug])

  if (!isReady) {
    return (
      <PageShell>
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
      <PageShell>
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

  const rubricTitle = rubricTitleById(episode.rubricId)
  const adjacent = getAdjacentPosts(getPublishedPosts(posts), episode.slug)

  return (
    <PageShell>
      <Link to="/game/learn" className="back-link">
        ← К оглавлению Learn
      </Link>

      <header className="learn-episode-header">
        <p className="learn-eyebrow">
          {episode.episode}
          {rubricTitle ? ` · ${rubricTitle}` : ''}
        </p>
        <h1 className="learn-title">{episode.title}</h1>
        <p className="learn-section-note">
          {isLive
            ? `Опубликовано ${formatPublishDate(episode.publishedAt)}`
            : `Превью · публикация ${formatPublishDate(episode.publishedAt)}`}
        </p>
        <p className="learn-admin-entry">
          <Link to={`/game/learn/admin/${episode.slug}`} className="learn-admin-link">
            Редактировать
          </Link>
        </p>
      </header>

      <div className="learn-tabs" role="tablist" aria-label="Разделы выпуска">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id
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

      <div
        id={`panel-${activeTab}`}
        role="tabpanel"
        aria-labelledby={`tab-${activeTab}`}
        className="learn-panel"
      >
        {activeTab === 'theory' && (
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
                  {episode.links
                    .filter((link) => link.href !== '#')
                    .map((link) => (
                      <li key={link.href + link.label}>
                        <a href={link.href} target="_blank" rel="noreferrer">
                          {link.label}
                        </a>
                      </li>
                    ))}
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
        )}

        {activeTab === 'lab' && (
          <LearnContent content={episode.lab} format={episode.labFormat} />
        )}

        {activeTab === 'cheatsheet' && (
          <LearnContent content={episode.cheatsheet} format={episode.cheatsheetFormat} />
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
