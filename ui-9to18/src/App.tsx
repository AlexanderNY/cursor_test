import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { GameSectionPage } from '@/pages/game-section-page'
import { HomePage } from '@/pages/home-page'

const BowlGamePage = lazy(() =>
  import('@/game/bowl/bowl-game-page').then((module) => ({ default: module.BowlGamePage })),
)

function BowlGameFallback() {
  return (
    <div className="bowl-screen bowl-menu">
      <div className="bowl-menu-card">
        <p className="bowl-subtitle">Загрузка Bowl…</p>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route
        path="/game/bowl"
        element={
          <Suspense fallback={<BowlGameFallback />}>
            <BowlGamePage />
          </Suspense>
        }
      />
      <Route path="/game/:slug" element={<GameSectionPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
