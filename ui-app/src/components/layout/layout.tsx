import { Outlet } from 'react-router-dom'
import { Sidebar } from './sidebar'
import { Header } from './header'
import { Footer } from './footer'
import { MobileNav } from './mobile-nav'
import { NotificationToasts } from './notification-toasts'
import { BrandContextBar } from './brand-context-bar'
import { useIsMobile } from '@/hooks'

export function Layout() {
  const isMobile = useIsMobile()

  if (isMobile) {
    return (
      <div className="min-h-screen flex flex-col">
        <MobileNav />
        <NotificationToasts />
        <main className="flex-1 pt-20 px-4 pb-4">
          <BrandContextBar className="mb-4" />
          <Outlet />
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <NotificationToasts />
      <div className="flex flex-1 min-h-0">
        <Sidebar />
        <main className="flex-1 min-w-0 overflow-auto p-6 flex flex-col">
          <BrandContextBar className="mb-4 shrink-0" />
          <div className="flex-1 min-h-0">
            <Outlet />
          </div>
        </main>
      </div>
      <Footer />
    </div>
  )
}
