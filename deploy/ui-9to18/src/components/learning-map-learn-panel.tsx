import { Link } from 'react-router-dom'
import { learnRubrics } from '@/data/learn'
import type { LearnPost } from '@/data/learn/learn-store'
import {
  seasonLabel,
  type MapLearnLink,
} from '@/data/learning-map/map-learn-links'

interface LearningMapLearnPanelProps {
  branchTitle: string
  link: MapLearnLink
  posts: LearnPost[]
  isReady: boolean
  completedSlugs?: Set<string>
}

export function LearningMapLearnPanel({
  branchTitle,
  link,
  posts,
  isReady,
  completedSlugs,
}: LearningMapLearnPanelProps) {
  const bySlug = new Map(posts.map((post) => [post.slug, post]))
  const lectures = link.episodeSlugs
    .map((slug) => bySlug.get(slug))
    .filter((post): post is LearnPost => Boolean(post))
  const missingCount = link.episodeSlugs.length - lectures.length
  const doneCount = lectures.filter((p) => completedSlugs?.has(p.slug)).length

  const rubricTags = link.rubricIds
    .map((id) => learnRubrics.find((rubric) => rubric.id === id)?.title)
    .filter((title): title is string => Boolean(title))

  const sectionTags = [...new Set([...link.tags, ...rubricTags])]

  return (
    <div className="lm-learn-panel">
      <header className="lm-learn-header">
        <div>
          <p className="lm-panel-eyebrow">Раздел Learn</p>
          <h3 className="lm-learn-title">{branchTitle}</h3>
        </div>
        <Link to="/game/learn" className="lm-btn lm-learn-all">
          Все лекции →
        </Link>
      </header>

      <p className="lm-learn-desc">{link.description}</p>
      {lectures.length > 0 && completedSlugs ? (
        <p className="lm-detail-empty">
          Прогресс ветки: {doneCount}/{lectures.length}
        </p>
      ) : null}

      {sectionTags.length > 0 ? (
        <div className="lm-tags" aria-label="Теги раздела">
          {sectionTags.map((tag) => (
            <span key={tag} className="lm-tag">
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      <div className="lm-learn-lectures">
        <h4 className="lm-learn-subtitle">Состав лекций</h4>
        {!isReady ? (
          <p className="lm-detail-empty">Загрузка лекций…</p>
        ) : lectures.length === 0 ? (
          <p className="lm-detail-empty">
            Пока нет лекций в Learn для этой ветки карты.
            {missingCount > 0 ? ` (ожидалось: ${missingCount})` : null}
          </p>
        ) : (
          <ul className="lm-lecture-list">
            {lectures.map((post) => {
              const rubricTitle =
                learnRubrics.find((rubric) => rubric.id === post.rubricId)?.title ||
                post.rubricId
              return (
                <li key={post.slug}>
                  <Link to={`/game/learn/${post.slug}`} className="lm-lecture-row">
                    <span className="lm-lecture-main">
                      <span className="lm-lecture-code">{post.episode}</span>
                      <span className="lm-lecture-title">
                        {completedSlugs?.has(post.slug) ? '✓ ' : ''}
                        {post.shortTitle || post.title}
                      </span>
                    </span>
                    <span className="lm-lecture-tags">
                      <span className="lm-tag lm-tag-soft">{seasonLabel(post.episode)}</span>
                      <span className="lm-tag lm-tag-soft">{rubricTitle}</span>
                    </span>
                  </Link>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
