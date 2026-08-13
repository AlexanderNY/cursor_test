import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { Layout } from '@/components/layout/layout'
import { SignInPage } from '@/pages/auth/sign-in'
import { SignUpPage } from '@/pages/auth/sign-up'
import { ResetPasswordPage } from '@/pages/auth/reset-password'
import { ProfilePage } from '@/pages/profile/profile'
import { TelegramPage } from '@/pages/telegram/telegram'
import { ThreadsPage } from '@/pages/threads/threads'
import { WordPressPage } from '@/pages/stubs/wordpress'
import { TwitterPage } from '@/pages/twitter'
import { VKontaktePage } from '@/pages/vkontakte'
import { DzenPage } from '@/pages/stubs/dzen'
import { InstagramPage } from '@/pages/stubs/instagram'
import { CustomURLPage } from '@/pages/stubs/custom-url'
import { CreatePostPage } from '@/pages/create-post'
import { AdministrationPage } from '@/pages/administration'
import { PollsPage, PollsIndexRedirect, PollsContentSection, PollsDiagnosticsSection, PollsRatingPage, PollsOrdersPage } from '@/pages/polls'
import { ChecksPage, ChecksIndexRedirect, AiCheckSection, ServicesStatusSection, ProcessorSection, CollectorSection, SchedulerSection, PostingDiagnosticsSection } from '@/pages/checks'
import { TeamPage } from '@/pages/team/team'
import { BrandsPage } from '@/pages/brands/brands'
import { ChannelsPage } from '@/pages/channels/channels'
import { ChannelFlowPage } from '@/pages/channels/channel-flow'
import { InboxPage } from '@/pages/inbox/inbox'
import { CalendarPage } from '@/pages/calendar/calendar'
import { SmmAnalyticsPage } from '@/pages/smm-analytics/analytics'
import { AutomationsPage } from '@/pages/automations/automations'
import { FigmaPreviewPage } from '@/pages/figma-preview'
import { AboutPage } from '@/pages/about/about'
import { PricingPage } from '@/pages/pricing/pricing'
import { FeedbackPage } from '@/pages/feedback'
import { RouteLoader } from '@/components/route-loader'

interface ProtectedRouteProps {
  children: React.ReactNode
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) return <RouteLoader />

  if (!isAuthenticated) {
    return <Navigate to="/sign-in" replace />
  }

  return <>{children}</>
}

interface AdminRouteProps {
  children: React.ReactNode
}

function AdminRoute({ children }: AdminRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) return <RouteLoader />

  if (!isAuthenticated) {
    return <Navigate to="/sign-in" replace />
  }

  if (user?.role !== 'admin') {
    return <Navigate to="/profile" replace />
  }

  return <>{children}</>
}

interface PublicRouteProps {
  children: React.ReactNode
}

function PublicRoute({ children }: PublicRouteProps) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) return <RouteLoader />

  if (isAuthenticated) {
    return <Navigate to="/profile" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <Routes>
      <Route path="/sign-in" element={<PublicRoute><SignInPage /></PublicRoute>} />
      <Route path="/sign-up" element={<PublicRoute><SignUpPage /></PublicRoute>} />
      <Route path="/reset-password" element={<PublicRoute><ResetPasswordPage /></PublicRoute>} />

      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/profile" replace />} />
        <Route path="about" element={<AboutPage />} />
        <Route path="guide" element={<Navigate to="/about" replace />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="billing" element={<Navigate to="/profile?tab=billing" replace />} />
        <Route path="statistics" element={<Navigate to="/profile?tab=statistics" replace />} />
        <Route path="brands" element={<BrandsPage />} />
        <Route path="channels" element={<ChannelsPage />} />
        <Route path="channels/:channelId" element={<ChannelFlowPage />} />
        <Route path="inbox" element={<InboxPage />} />
        <Route path="calendar" element={<CalendarPage />} />
        <Route path="analytics" element={<SmmAnalyticsPage />} />
        <Route path="automations" element={<AutomationsPage />} />
        <Route path="telegram" element={<TelegramPage />} />
        <Route path="threads" element={<ThreadsPage />} />
        <Route path="wordpress" element={<WordPressPage />} />
        <Route path="twitter" element={<TwitterPage />} />
        <Route path="vkontakte" element={<VKontaktePage />} />
        <Route path="dzen" element={<DzenPage />} />
        <Route path="instagram" element={<InstagramPage />} />
        <Route path="custom-url" element={<CustomURLPage />} />
        <Route path="posts" element={<CreatePostPage />} />
        <Route path="create-post" element={<Navigate to="/posts" replace />} />
        <Route path="team" element={<TeamPage />} />
        <Route path="group" element={<Navigate to="/team" replace />} />
        <Route path="administration" element={<AdminRoute><AdministrationPage /></AdminRoute>} />
        <Route path="polls" element={<AdminRoute><PollsPage /></AdminRoute>}>
          <Route index element={<PollsIndexRedirect />} />
          <Route path="content" element={<PollsContentSection />} />
          <Route path="diagnostics" element={<PollsDiagnosticsSection />} />
          <Route path="rating" element={<PollsRatingPage />} />
          <Route path="orders" element={<PollsOrdersPage />} />
        </Route>
        <Route path="checks" element={<AdminRoute><ChecksPage /></AdminRoute>}>
          <Route index element={<ChecksIndexRedirect />} />
          <Route path="services-status" element={<ServicesStatusSection />} />
          <Route path="processor" element={<ProcessorSection />} />
          <Route path="collector" element={<CollectorSection />} />
          <Route path="scheduler" element={<SchedulerSection />} />
          <Route path="posting-diagnostics" element={<PostingDiagnosticsSection />} />
          <Route path="ai" element={<AiCheckSection />} />
        </Route>
        <Route path="pricing" element={<PricingPage />} />
        <Route path="feedback" element={<FeedbackPage />} />
      </Route>

      <Route path="figma-preview" element={<FigmaPreviewPage />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App


