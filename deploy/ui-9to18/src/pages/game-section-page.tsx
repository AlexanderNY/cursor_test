import { Link, Navigate, useParams } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { getSectionBySlug } from '@/data/sections'

export function GameSectionPage() {
  const { slug } = useParams<{ slug: string }>()
  const section = slug ? getSectionBySlug(slug) : undefined

  if (!section) {
    return <Navigate to="/" replace />
  }

  return (
    <PageShell>
      <main className="section-page">
        <Link to="/" className="back-link">
          ← На главную
        </Link>

        <div className="section-page-header">
          {section.emoji && (
            <span className="section-page-emoji" aria-hidden>
              {section.emoji}
            </span>
          )}
          <h1 className="section-page-title">{section.title}</h1>
          <p className="section-page-subtitle">{section.subtitle}</p>
        </div>

        <div className="status" role="status">
          <span className="status-dot" />
          <span>Раздел в разработке</span>
        </div>
      </main>
    </PageShell>
  )
}
