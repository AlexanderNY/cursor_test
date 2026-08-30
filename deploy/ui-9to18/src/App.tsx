import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { LearnAdminGuard } from '@/components/learn-admin-guard'
import { GameSectionPage } from '@/pages/game-section-page'
import { HomePage } from '@/pages/home-page'
import { SiteLoginPage } from '@/pages/site-login-page'
import { SiteAccountPage } from '@/pages/site-account-page'
import { AppBlogPage, AppPostPage } from '@/pages/app-blog-page'
import { AppAdminPage, SiteAdminPage } from '@/pages/site-admin-page'

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

const LearnAdminLoginPage = lazy(() =>
  import('@/pages/learn-admin-login-page').then((module) => ({
    default: module.LearnAdminLoginPage,
  })),
)

const LearningMapPage = lazy(() =>
  import('@/pages/learning-map-page').then((module) => ({
    default: module.LearningMapPage,
  })),
)

const TasksPage = lazy(() =>
  import('@/pages/tasks-page').then((module) => ({ default: module.TasksPage })),
)

const CertPage = lazy(() =>
  import('@/pages/cert-page').then((module) => ({ default: module.CertPage })),
)

const QuizPage = lazy(() =>
  import('@/pages/quiz-page').then((module) => ({ default: module.QuizPage })),
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
      <Route path="/login" element={<SiteLoginPage />} />
      <Route path="/register" element={<SiteLoginPage />} />
      <Route path="/account" element={<SiteAccountPage />} />
      <Route path="/admin" element={<SiteAdminPage />} />
      <Route path="/admin/apps/:slug" element={<AppAdminPage />} />
      <Route path="/app/:slug" element={<AppBlogPage />} />
      <Route path="/app/:slug/:postSlug" element={<AppPostPage />} />
      <Route
        path="/game/tasks"
        element={
          <Suspense fallback={<LearnFallback />}>
            <TasksPage />
          </Suspense>
        }
      />
      <Route
        path="/game/cert"
        element={
          <Suspense fallback={<LearnFallback />}>
            <CertPage />
          </Suspense>
        }
      />
      <Route
        path="/game/quiz"
        element={
          <Suspense fallback={<LearnFallback />}>
            <QuizPage />
          </Suspense>
        }
      />
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
        path="/game/learn/admin/login"
        element={
          <Suspense fallback={<LearnFallback />}>
            <LearnAdminLoginPage />
          </Suspense>
        }
      />
      <Route
        path="/game/learn/admin"
        element={
          <Suspense fallback={<LearnFallback />}>
            <LearnAdminGuard>
              <LearnAdminPage />
            </LearnAdminGuard>
          </Suspense>
        }
      />
      <Route
        path="/game/learn/admin/new"
        element={
          <Suspense fallback={<LearnFallback />}>
            <LearnAdminGuard>
              <LearnAdminEditPage />
            </LearnAdminGuard>
          </Suspense>
        }
      />
      <Route
        path="/game/learn/admin/:slug"
        element={
          <Suspense fallback={<LearnFallback />}>
            <LearnAdminGuard>
              <LearnAdminEditPage />
            </LearnAdminGuard>
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
      <Route
        path="/game/learning-map"
        element={
          <Suspense fallback={<LearnFallback />}>
            <LearningMapPage />
          </Suspense>
        }
      />
      <Route path="/game/:slug" element={<GameSectionPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
