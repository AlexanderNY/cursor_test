import { Link } from 'react-router-dom'
import { levelLabel } from '@/data/learn/labels'
import type { StudyPath, StudyPathItem } from '@/data/learn/study-path'

type LearnStudyPathProps = {
  path: StudyPath
  completedSlugs: Set<string>
}

function StudyPathList({
  items,
  completedSlugs,
  direction,
}: {
  items: StudyPathItem[]
  completedSlugs: Set<string>
  direction: 'before' | 'after'
}) {
  return (
    <ul className="learn-study-path-list">
      {items.map(({ slug, post }) => {
        const isDone = completedSlugs.has(slug)
        return (
          <li key={slug} className={isDone ? 'is-done' : undefined}>
            {post ? (
              <Link to={`/game/learn/${slug}`}>
                {direction === 'before' ? '← ' : ''}
                {post.shortTitle || post.title}
                {direction === 'after' ? ' →' : ''}
              </Link>
            ) : (
              <span className="learn-link-local">{slug}</span>
            )}
            {post?.level ? <span className="learn-study-path-meta"> · {levelLabel(post.level)}</span> : null}
            {isDone ? <span className="learn-study-path-meta"> · пройдено</span> : null}
          </li>
        )
      })}
    </ul>
  )
}

export function LearnStudyPath({ path, completedSlugs }: LearnStudyPathProps) {
  if (path.before.length === 0 && path.after.length === 0) {
    return null
  }
  const pendingBefore = path.before.filter((item) => !completedSlugs.has(item.slug)).length
  return (
    <section className="learn-study-path" aria-labelledby="learn-study-path-heading">
      <h2 id="learn-study-path-heading" className="learn-panel-heading">
        Порядок изучения
      </h2>
      <div className="learn-study-path-columns">
        {path.before.length > 0 ? (
          <div>
            <h3 className="learn-study-path-title">Изучить до</h3>
            <p className="learn-section-note">
              {pendingBefore > 0
                ? 'Без этих выпусков часть терминов будет непонятна.'
                : 'Всё, на что опирается выпуск, уже пройдено.'}
            </p>
            <StudyPathList items={path.before} completedSlugs={completedSlugs} direction="before" />
          </div>
        ) : null}
        {path.after.length > 0 ? (
          <div>
            <h3 className="learn-study-path-title">Изучить после</h3>
            <p className="learn-section-note">Эти выпуски опираются на текущий.</p>
            <StudyPathList items={path.after} completedSlugs={completedSlugs} direction="after" />
          </div>
        ) : null}
      </div>
    </section>
  )
}
