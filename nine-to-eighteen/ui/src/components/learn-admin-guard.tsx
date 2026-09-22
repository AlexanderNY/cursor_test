import { ReactNode, useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { isSuperAdmin, refreshSiteAuthSession } from '@/data/site/site-auth'

/** Learn CMS: только супер-админ сайта 9to18 (site JWT). */
export function LearnAdminGuard({ children }: { children: ReactNode }) {
  const location = useLocation()
  const [status, setStatus] = useState<'loading' | 'ok' | 'deny'>('loading')

  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const site = await refreshSiteAuthSession().catch(() => null)
        if (cancelled) return
        setStatus(isSuperAdmin(site) ? 'ok' : 'deny')
      } catch {
        if (!cancelled) setStatus('deny')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [location.pathname])

  if (status === 'loading') {
    return (
      <div className="page">
        <div className="page-inner">
          <p className="home-subtitle">Проверка доступа…</p>
        </div>
      </div>
    )
  }

  if (status === 'deny') {
    return (
      <Navigate
        to="/game/learn/admin/login"
        replace
        state={{ from: location.pathname }}
      />
    )
  }

  return <>{children}</>
}
