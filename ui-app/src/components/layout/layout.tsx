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
      <div className="min-h-screen flex flex-col max-w-[100vw] overflow-x-hidden">
        <MobileNav />
        <NotificationToasts />
        <main className="flex-1 min-w-0 pt-20 px-4 pb-4 overflow-x-auto">
          <BrandContextBar className="mb-4" />
          <div className="min-w-0 w-full">
            <Outlet />
          </div>
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-screen max-w-[100vw] overflow-x-hidden">
      <Header />
      <NotificationToasts />
      <div className="flex flex-1 min-h-0 min-w-0">
        <Sidebar />
        <main className="flex-1 min-w-0 overflow-x-auto overflow-y-auto p-6 flex flex-col">
          <BrandContextBar className="mb-4 shrink-0" />
          <div className="flex-1 min-h-0 min-w-0 w-full">
            <Outlet />
          </div>
        </main>
      </div>
      <Footer />
    </div>
  )
}
