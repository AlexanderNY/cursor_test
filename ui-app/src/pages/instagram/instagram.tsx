import { useState, FormEvent, useEffect, useCallback } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { instagramService } from '@/services/instagram-service'
import type {
  InstagramFollowingUser,
  InstagramProfile,
  ScheduleType,
} from '@/types/instagram'
import { useAuth } from '@/contexts/auth-context'
import { useBrand } from '@/contexts/brand-context'
import { canManagePlatformAuth } from '@/types/smm'

function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

const LEGACY_TAB_REDIRECT: Record<string, string> = {
  posts: '/analytics',
  create: '/posts',
  calendar: '/calendar?network=instagram',
  profile: '/channels',
  processing: '/channels',
  session: '/channels',
}

function InstagramHubMap() {
  const { selectedBrandId } = useBrand()
  const calendarHref = selectedBrandId
    ? `/calendar?brand=${selectedBrandId}&network=instagram`
    : '/calendar?network=instagram'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Brand → Channel</CardTitle>
        <CardDescription>
          Здесь только сессия Instagram (instagrapi). Источники (@username), collect/publish — в Channels.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="grid gap-3 sm:grid-cols-2 text-sm">
          <li>
            <Link to="/analytics" className="text-primary-400 hover:underline font-medium">
              Posts → Analytics
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Очередь и лента по каналам бренда.
            </p>
          </li>
          <li>
            <Link to={calendarHref} className="text-primary-400 hover:underline font-medium">
              Calendar → общий календарь
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Расписание, фильтр network=instagram.
            </p>
          </li>
          <li>
            <Link to="/channels" className="text-primary-400 hover:underline font-medium">
              Profile Settings → Channels
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Канал network=Instagram, external_id=@username, включите Collect.
            </p>
          </li>
          <li>
            <Link to="/channels" className="text-primary-400 hover:underline font-medium">
              Обработка → канал
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Настроить → Обработка у конкретного канала.
            </p>
          </li>
        </ul>
        <p className="mt-4 text-sm">
          Создать пост:{' '}
          <Link to="/posts" className="text-primary-400 hover:underline">
            Posts
          </Link>
          {' · '}
          очередь:{' '}
          <Link to="/inbox" className="text-primary-400 hover:underline">
            Inbox
          </Link>
        </p>
      </CardContent>
    </Card>
  )
}

export function InstagramPage() {
  const { user } = useAuth()
  const hasTeam = Boolean(user?.group_id || user?.role_in_group)
  const canAuth = canManagePlatformAuth(user?.role_in_group, hasTeam)
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const [publishEnabled, setPublishEnabled] = useState(false)
  const [collectEnabled, setCollectEnabled] = useState(false)
  const [scheduleType, setScheduleType] = useState<ScheduleType>('immediate')
  const [timeIntervals, setTimeIntervals] = useState<Array<{ id: string; start: string; end: string }>>([
    { id: generateId(), start: '', end: '' },
  ])
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [verificationCode, setVerificationCode] = useState('')
  const [usernamesToRead, setUsernamesToRead] = useState<Array<{ id: string; value: string }>>([
    { id: generateId(), value: '' },
  ])

  const [hasInstagramSession, setHasInstagramSession] = useState(false)
  const [instagramLastAuthError, setInstagramLastAuthError] = useState<string | null>(null)
  const [instagramVerificationPending, setInstagramVerificationPending] = useState(false)

  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [isSavingAuth, setIsSavingAuth] = useState(false)
  const [isLoginTesting, setIsLoginTesting] = useState(false)
  const [lastDiagnosticImage, setLastDiagnosticImage] = useState<string | null>(null)
  const [followingPreview, setFollowingPreview] = useState<InstagramFollowingUser[]>([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadProfile = useCallback(async () => {
    setIsLoadingProfile(true)
    try {
      const profile = await instagramService.getProfile()
      if (profile) {
        setPublishEnabled(profile.publish_enabled ?? false)
        setCollectEnabled(profile.collect_enabled ?? false)
        setScheduleType((profile.schedule_type as ScheduleType) ?? 'immediate')
        const ti = profile.time_intervals
        if (Array.isArray(ti) && ti.length > 0 && ti[0]?.start) {
          setTimeIntervals(
            ti.map((interval) => ({
              id: generateId(),
              start: interval.start ?? '',
              end: interval.end ?? '',
            }))
          )
        }
        setUsername(profile.username ?? '')
        setPassword('')
        setVerificationCode('')
        setHasInstagramSession(profile.has_instagram_session ?? false)
        setInstagramLastAuthError(profile.instagram_last_auth_error ?? null)
        setInstagramVerificationPending(profile.instagram_verification_pending ?? false)
        const ur = profile.usernames_to_read
        if (Array.isArray(ur) && ur.length > 0) {
          setUsernamesToRead(ur.map((u) => ({ id: generateId(), value: String(u) })))
        }
      }
    } catch (err) {
      console.error('Failed to load profile:', err)
    } finally {
      setIsLoadingProfile(false)
    }
  }, [])

  useEffect(() => {
    void loadProfile()
  }, [loadProfile])

  useEffect(() => {
    const legacyTab = searchParams.get('tab')
    if (legacyTab && LEGACY_TAB_REDIRECT[legacyTab]) {
      navigate(LEGACY_TAB_REDIRECT[legacyTab], { replace: true })
      return
    }
    if (searchParams.get('auth') === '1') {
      searchParams.delete('auth')
      setSearchParams(searchParams, { replace: true })
    }
  }, [searchParams, setSearchParams, navigate])

  function buildProfilePayload(options?: { includeVerificationCode?: boolean }): Partial<InstagramProfile> {
    const timeIntervalsPayload =
      scheduleType === 'intervals'
        ? timeIntervals.filter((i) => i.start && i.end).map(({ start, end }) => ({ start, end }))
        : []
    const usernamesPayload = usernamesToRead.map((f) => f.value.trim()).filter(Boolean)
    const payload: Partial<InstagramProfile> = {
      publish_enabled: publishEnabled,
      collect_enabled: collectEnabled,
      schedule_type: scheduleType,
      time_intervals: timeIntervalsPayload,
      username: username || undefined,
      password: password || undefined,
      usernames_to_read: usernamesPayload,
    }
    if (options?.includeVerificationCode && verificationCode.trim()) {
      payload.instagram_verification_code = verificationCode.trim()
    }
    return payload
  }

  async function handleSaveAuth(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSavingAuth(true)
    try {
      await instagramService.saveProfile(buildProfilePayload({ includeVerificationCode: true }))
      setSuccess('Учётные данные сохранены')
      setVerificationCode('')
      await loadProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить учётные данные')
    } finally {
      setIsSavingAuth(false)
    }
  }

  async function handleLoginTest() {
    setError('')
    setSuccess('')
    setLastDiagnosticImage(null)
    setFollowingPreview([])
    setIsLoginTesting(true)
    try {
      const result = await instagramService.loginTest(50)
      if (result.ok) {
        setLastDiagnosticImage(null)
        const n = result.following?.length ?? result.following_count ?? 0
        setFollowingPreview(result.following ?? [])
        const via = result.auth_method === 'selenium' ? ' · способ: браузер (Selenium)' : ''
        setSuccess(
          result.instagram_user_id != null
            ? `Вход выполнен (id: ${result.instagram_user_id})${n > 0 ? ` · подписок: ${n}` : ''}${via}`
            : `Вход выполнен${n > 0 ? ` · подписок: ${n}` : ''}${via}`
        )
      } else {
        const b64 = result.selenium_diagnostic_image_base64?.trim()
        if (b64) {
          setLastDiagnosticImage(b64.startsWith('data:') ? b64 : `data:image/png;base64,${b64}`)
        }
        const extra =
          result.selenium_status && result.selenium_status !== 'success'
            ? ` [Selenium: ${result.selenium_status}]`
            : ''
        const diag = result.selenium_diagnostic_s3_key
          ? ` Диагностика (S3): ${result.selenium_diagnostic_s3_key}`
          : ''
        setError((result.message || 'Вход не выполнен') + extra + diag)
      }
      await loadProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Проверка входа не удалась')
    } finally {
      setIsLoginTesting(false)
    }
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="Instagram"
        description="Сессия instagrapi. Каналы (@username) — в Channels."
      />

      <InstagramHubMap />

      {error && (
        <Alert variant="error" className="animate-slide-down mt-4">
          {error}
        </Alert>
      )}
      {success && (
        <Alert variant="success" className="animate-slide-down mt-4">
          {success}
        </Alert>
      )}

      {canAuth ? (
        <Card className="animate-slide-up mt-4">
          <CardHeader>
            <CardTitle>Авторизация</CardTitle>
            <CardDescription>
              Логин/пароль для instagrapi. Сессия хранится на сервере. Для сбора brand-каналов нужна
              рабочая сессия (кнопка «Проверить вход»).
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSaveAuth}>
            <CardContent className="space-y-4">
              {isLoadingProfile ? (
                <p className="text-sm text-[var(--text-muted)]">Загрузка…</p>
              ) : (
                <>
                  <div className="flex flex-wrap items-center gap-2 text-sm">
                    <span className="font-medium">Сессия:</span>
                    <span
                      className={
                        hasInstagramSession
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-[var(--text-muted)]'
                      }
                    >
                      {hasInstagramSession ? 'да' : 'нет'}
                    </span>
                    {instagramVerificationPending && (
                      <span className="text-amber-600 dark:text-amber-400">
                        Ожидается 2FA — введите код, сохраните, снова «Проверить вход».
                      </span>
                    )}
                  </div>
                  {instagramLastAuthError && (
                    <p className="text-sm text-red-600 dark:text-red-400 break-words">
                      Последняя ошибка: {instagramLastAuthError}
                    </p>
                  )}
                  <div className="grid gap-4 md:grid-cols-2">
                    <Input
                      label="Имя пользователя"
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="instagram_username"
                      autoComplete="username"
                    />
                    <Input
                      label="Пароль"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Оставьте пустым, чтобы не менять"
                      autoComplete="current-password"
                    />
                    <Input
                      label="Код 2FA (если нужен)"
                      type="text"
                      value={verificationCode}
                      onChange={(e) => setVerificationCode(e.target.value)}
                      placeholder="123456"
                      autoComplete="one-time-code"
                    />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button type="submit" isLoading={isSavingAuth} variant="secondary">
                      Сохранить учётные данные
                    </Button>
                    <Button
                      type="button"
                      onClick={() => void handleLoginTest()}
                      isLoading={isLoginTesting}
                    >
                      Проверить вход
                    </Button>
                  </div>
                  {followingPreview.length > 0 && (
                    <ul className="mt-2 max-h-48 overflow-y-auto rounded-xl border border-[var(--border-color)] p-3 text-sm space-y-1">
                      {followingPreview.map((u) => (
                        <li key={u.pk}>
                          <span className="font-mono text-primary-400">@{u.username}</span>
                          {u.full_name && (
                            <span className="text-[var(--text-secondary)] ml-2">{u.full_name}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                  {lastDiagnosticImage && (
                    <img
                      src={lastDiagnosticImage}
                      alt="Selenium diag"
                      className="mt-2 max-h-64 rounded border border-[var(--border-color)]"
                    />
                  )}
                </>
              )}
            </CardContent>
          </form>
        </Card>
      ) : (
        <Alert variant="info" className="mt-4">
          Подключать Instagram может владелец или админ команды.{' '}
          <Link to="/channels" className="underline">
            К каналам
          </Link>
        </Alert>
      )}
    </PageContainer>
  )
}
