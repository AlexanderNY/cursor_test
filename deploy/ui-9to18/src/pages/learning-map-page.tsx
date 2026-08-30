import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { LearningMindmap } from '@/components/learning-mindmap'
import { PageShell } from '@/components/page-shell'
import { learningMapRoot, learningMapStats } from '@/data/learning-map'
import { countNodes, parseOutlineMarkdown, type MindNode } from '@/data/learning-map/parse-outline'
import { siteGetLearningMap } from '@/data/site/site-api'

export function LearningMapPage() {
  const [root, setRoot] = useState<MindNode>(learningMapRoot)
  const [mapKey, setMapKey] = useState('default')
  const [sourceLabel, setSourceLabel] = useState('встроенная')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    void siteGetLearningMap()
      .then((data) => {
        if (cancelled) {
          return
        }
        if (data.source === 'custom' && data.markdown.trim()) {
          const parsed = parseOutlineMarkdown(data.markdown)
          setRoot(parsed)
          setMapKey(`custom-${data.updatedAt || data.chars}`)
          setSourceLabel(
            data.updatedBy
              ? `загружена админом (${data.updatedBy})`
              : 'загружена админом',
          )
          return
        }
        setRoot(learningMapRoot)
        setMapKey('default')
        setSourceLabel('встроенная')
      })
      .catch(() => {
        if (!cancelled) {
          setRoot(learningMapRoot)
          setMapKey('default')
          setSourceLabel('встроенная')
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  const stats = useMemo(
    () => ({
      nodes: countNodes(root),
      branches: root.children.length,
    }),
    [root],
  )

  return (
    <PageShell>
      <Link to="/" className="back-link">
        ← На главную
      </Link>

      <header className="learn-header">
        <p className="learn-eyebrow">🗺️ Карта обучения</p>
        <h1 className="learn-title">Подготовка к собеседованию</h1>
        <p className="learn-lead">
          Mind map: масштаб, ветки, теги (фильтр и цвета), пунктирные связи. Клик по листу —
          описание и Anki. «Выгрузить MD» / Anki ↓ / Anki ▶.
          {loading ? ' Загрузка…' : ` Источник: ${sourceLabel}.`}
        </p>
      </header>

      <LearningMindmap
        key={mapKey}
        root={root}
        branchCount={stats.branches || learningMapStats.branches}
        nodeCount={stats.nodes || learningMapStats.nodes}
      />
    </PageShell>
  )
}
