import { useState } from 'react'
import { GUIDE_TABS, type GuideEntry, type GuideTabId } from './guide-content'

interface GuideScreenProps {
  onBack: () => void
}

function GuideEntryCard({ entry }: { entry: GuideEntry }) {
  return (
    <article className="bowl-guide-entry">
      <header className="bowl-guide-entry-header">
        {entry.emoji && <span className="bowl-guide-entry-emoji">{entry.emoji}</span>}
        <h3
          className="bowl-guide-entry-title"
          style={entry.color ? { color: entry.color } : undefined}
        >
          {entry.title}
        </h3>
      </header>
      <p className="bowl-guide-entry-summary">{entry.summary}</p>
      {entry.details.length > 0 && (
        <ul className="bowl-guide-entry-list">
          {entry.details.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      )}
      {entry.tips && entry.tips.length > 0 && (
        <div className="bowl-guide-entry-tips">
          <span className="bowl-guide-tip-label">Совет</span>
          <ul className="bowl-guide-entry-list">
            {entry.tips.map((tip) => (
              <li key={tip}>{tip}</li>
            ))}
          </ul>
        </div>
      )}
    </article>
  )
}

export function GuideScreen({ onBack }: GuideScreenProps) {
  const [activeTab, setActiveTab] = useState<GuideTabId>('mechanics')
  const tab = GUIDE_TABS.find((item) => item.id === activeTab) ?? GUIDE_TABS[0]

  return (
    <div className="bowl-screen bowl-menu">
      <div className="bowl-guide-card">
        <div className="bowl-brand">
          <span className="bowl-brand-mark">Bowl</span>
          <span className="bowl-brand-domain">Справочник</span>
        </div>
        <h1 className="bowl-title">Как играть</h1>
        <p className="bowl-subtitle bowl-guide-subtitle">
          Механики, объекты, враги и перки — всё, что встретите в чаше.
        </p>

        <div className="bowl-guide-tabs" role="tablist" aria-label="Разделы справочника">
          {GUIDE_TABS.map((item) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={activeTab === item.id}
              className={`bowl-guide-tab${activeTab === item.id ? ' bowl-guide-tab-active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div className="bowl-guide-scroll" role="tabpanel">
          {tab.intro && <p className="bowl-guide-intro">{tab.intro}</p>}
          {tab.sections.map((section) => (
            <section key={section.title} className="bowl-guide-section">
              <h2 className="bowl-settings-group-title">{section.title}</h2>
              {section.entries.map((entry) => (
                <GuideEntryCard key={entry.id} entry={entry} />
              ))}
            </section>
          ))}
        </div>

        <div className="bowl-settings-actions">
          <button type="button" className="bowl-btn bowl-btn-ghost" onClick={onBack}>
            ← Назад в меню
          </button>
        </div>
      </div>
    </div>
  )
}
