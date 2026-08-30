import { ReactNode, useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import {
  canEditLearn,
  clearLearnAuthSession,
  getLearnAuthSession,
} from '@/data/learn/learn-auth'
import { apiGetProfile } from '@/data/learn/learn-api'
import { isSuperAdmin, refreshSiteAuthSession } from '@/data/site/site-auth'

/**
 * Доступ в Learn-админку: CopyParse admin/author ИЛИ супер-админ сайта (SSO-lite).
 * Запись контента через API по-прежнему требует CopyParse JWT, если gateway его ждёт;
 * супер-админ сайта хотя бы видит UI и статус сессии.
 */
export function LearnAdminGuard({ children }: { children: ReactNode }) {
  const location = useLocation()
  const [status, setStatus] = useState<'loading' | 'ok' | 'deny'>('loading')

  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const site = await refreshSiteAuthSession().catch(() => null)
        if (cancelled) return
        if (isSuperAdmin(site)) {
          setStatus('ok')
          return
        }
        const session = getLearnAuthSession()
        if (!session?.accessToken) {
          setStatus('deny')
          return
        }
        const profile = await apiGetProfile()
        if (cancelled) return
        if (!canEditLearn(profile.role)) {
          clearLearnAuthSession()
          setStatus('deny')
          return
        }
        setStatus('ok')
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
