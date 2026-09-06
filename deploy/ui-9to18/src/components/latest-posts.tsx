import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import type { SiteLatestPost } from '@/data/site/site-api'

type LatestPostsProps = {
  items: SiteLatestPost[]
}

function formatDate(value: string): string {
  if (!value) {
    return ''
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value.slice(0, 10)
  }
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function LatestPosts({ items }: LatestPostsProps) {
  if (items.length === 0) {
    return null
  }

  return (
    <section className="latest-posts" aria-labelledby="latest-posts-title">
      <div className="latest-posts-head">
        <h2 id="latest-posts-title" className="section-block-title">
          Свежие статьи
        </h2>
        <p className="section-block-lead">
          Пять последних публикаций из блогов всех сервисов на площадке.
        </p>
      </div>
      <ul className="latest-posts-list">
        {items.map((item) => (
          <li key={`${item.appSlug}/${item.postSlug}`}>
            <Link
              to={item.href || `/app/${item.appSlug}/${item.postSlug}`}
              className="latest-posts-card"
              style={{ '--post-accent': item.accent || '#2dd4bf' } as CSSProperties}
            >
              <p className="latest-posts-meta">
                {item.emoji ? <span aria-hidden>{item.emoji} </span> : null}
                {item.appTitle || item.appSlug}
                {item.publishedAt ? ` · ${formatDate(item.publishedAt)}` : null}
              </p>
              <h3 className="latest-posts-title">{item.title}</h3>
              {item.excerpt ? <p className="latest-posts-excerpt">{item.excerpt}</p> : null}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}
