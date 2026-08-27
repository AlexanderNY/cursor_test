import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { SectionTile } from '@/components/section-tile'
import { sections } from '@/data/sections'

export function HomePage() {
  return (
    <PageShell showBrandLink={false}>
      <header className="home-header">
        <h1 className="home-title">Разделы</h1>
        <p className="home-subtitle">Выберите раздел для перехода</p>
        <p className="home-admin-link">
          <Link to="/game/learn/admin">Админка Learn</Link>
        </p>
      </header>

      <div className="sections-grid">
        {sections.map((section) => (
          <SectionTile key={section.slug} section={section} />
        ))}
      </div>
    </PageShell>
  )
}
