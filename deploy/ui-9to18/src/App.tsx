import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { GameSectionPage } from '@/pages/game-section-page'
import { HomePage } from '@/pages/home-page'

const BowlGamePage = lazy(() =>
  import('@/game/bowl/bowl-game-page').then((module) => ({ default: module.BowlGamePage })),
)

const LearnIndexPage = lazy(() =>
  import('@/pages/learn-index-page').then((module) => ({ default: module.LearnIndexPage })),
)

const LearnEpisodePage = lazy(() =>
  import('@/pages/learn-episode-page').then((module) => ({ default: module.LearnEpisodePage })),
)

const LearnAdminPage = lazy(() =>
  import('@/pages/learn-admin-page').then((module) => ({ default: module.LearnAdminPage })),
)

const LearnAdminEditPage = lazy(() =>
  import('@/pages/learn-admin-edit-page').then((module) => ({
    default: module.LearnAdminEditPage,
  })),
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

function LearnFallback() {
  return (
    <div className="page">
      <div className="page-inner">
        <p className="home-subtitle">Загрузка Learn…</p>
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
      <Route
        path="/game/learn"
        element={
          <Suspense fallback={<LearnFallback />}>
            <LearnIndexPage />
          </Suspense>
        }
      />
      <Route
        path="/game/learn/admin"
        element={
          <Suspense fallback={<LearnFallback />}>
            <LearnAdminPage />
          </Suspense>
        }
      />
      <Route
        path="/game/learn/admin/new"
        element={
          <Suspense fallback={<LearnFallback />}>
            <LearnAdminEditPage />
          </Suspense>
        }
      />
      <Route
        path="/game/learn/admin/:slug"
        element={
          <Suspense fallback={<LearnFallback />}>
            <LearnAdminEditPage />
          </Suspense>
        }
      />
      <Route
        path="/game/learn/:slug"
        element={
          <Suspense fallback={<LearnFallback />}>
            <LearnEpisodePage />
          </Suspense>
        }
      />
      <Route path="/game/:slug" element={<GameSectionPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
