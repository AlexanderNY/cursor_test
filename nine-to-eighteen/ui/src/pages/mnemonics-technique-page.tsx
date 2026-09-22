import { Link, Navigate, useParams } from 'react-router-dom'
import { MnemonicTrainerWorkspace } from '@/components/mnemonic-trainer-workspace'
import { PageShell } from '@/components/page-shell'
import { getTechniqueMeta } from '@/data/mnemonics/types'
import { isMnemonicTechniqueId } from '@/data/site/structured-post'

export function MnemonicsTechniquePage() {
  const { technique = '' } = useParams<{ technique: string }>()
  if (!isMnemonicTechniqueId(technique)) {
    return <Navigate to="/game/mnemonics" replace />
  }
  const meta = getTechniqueMeta(technique)
  if (!meta) {
    return <Navigate to="/game/mnemonics" replace />
  }

  return (
    <PageShell content="article">
      <Link to="/game/mnemonics" className="back-link">
        ← Все мнемотехники
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Тренажёр · {meta.id}</p>
        <h1 className="learn-title">{meta.title}</h1>
        <p className="learn-lead">
          {meta.subtitle}. Готовые примеры (можно тренировать сразу) и форма для своих.
        </p>
      </header>
      <MnemonicTrainerWorkspace technique={technique} />
    </PageShell>
  )
}
