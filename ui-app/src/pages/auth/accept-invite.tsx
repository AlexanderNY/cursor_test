import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { authService } from '@/services/auth-service'
import type { InvitePeekResponse } from '@/types/auth'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { getErrorMessage } from '@/services/api-client'
import { roleLabel } from '@/types/smm'

export function AcceptInvitePage() {
  const { token = '' } = useParams<{ token: string }>()
  const { user, isAuthenticated, isLoading, refreshUserData } = useAuth()
  const navigate = useNavigate()
  const [peek, setPeek] = useState<InvitePeekResponse | null>(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!token) return
    void (async () => {
      try {
        setPeek(await authService.peekInvite(token))
      } catch (e) {
        setError(getErrorMessage(e))
      }
    })()
  }, [token])

  async function handleAccept() {
    if (!token) return
    setBusy(true)
    setError('')
    try {
      const res = await authService.acceptInvite(token)
      await refreshUserData()
      setSuccess(
        res.already_member
          ? `Вы уже в команде «${res.group_name}»`
          : `Вы вступили в «${res.group_name}» как ${roleLabel(res.role_in_group)}`,
      )
      setTimeout(() => navigate('/team'), 1200)
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const signUpHref = `/sign-up?invite=${encodeURIComponent(token)}`
  const signInHref = `/sign-in?invite=${encodeURIComponent(token)}`

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Приглашение в команду</CardTitle>
          <CardDescription>
            {peek
              ? `«${peek.group_name}» · роль ${roleLabel(peek.role_in_group)}`
              : 'Загрузка…'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && <Alert variant="error">{error}</Alert>}
          {success && <Alert variant="success">{success}</Alert>}
          {peek && peek.status !== 'pending' && !success && (
            <Alert variant="warning">Приглашение недоступно: {peek.status}</Alert>
          )}
          {peek?.email && (
            <p className="text-sm text-[var(--text-muted)]">
              Для email: <strong>{peek.email}</strong>
              {user?.email && user.email.toLowerCase() !== peek.email.toLowerCase() && (
                <> · вы вошли как {user.email}</>
              )}
            </p>
          )}

          {isLoading ? (
            <p className="text-sm text-[var(--text-muted)]">Проверка сессии…</p>
          ) : isAuthenticated ? (
            <Button
              disabled={busy || peek?.status !== 'pending'}
              onClick={() => void handleAccept()}
            >
              {busy ? 'Принимаем…' : 'Принять приглашение'}
            </Button>
          ) : (
            <div className="flex flex-wrap gap-2">
              <Link to={signUpHref}>
                <Button>Зарегистрироваться</Button>
              </Link>
              <Link to={signInHref}>
                <Button variant="secondary">Войти</Button>
              </Link>
            </div>
          )}

          <p className="text-sm">
            <Link to="/team" className="text-primary-400 hover:underline">
              ← К команде
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
