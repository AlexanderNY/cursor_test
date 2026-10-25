import { useState, FormEvent, useEffect, useCallback } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { threadsService } from '@/services/threads-service'
import { getErrorMessage } from '@/services/api-client'
import { useAuth } from '@/contexts/auth-context'
import { useBrand } from '@/contexts/brand-context'
import { canManagePlatformAuth } from '@/types/smm'
import { formatDateTime } from '@/utils/date'
import { allowedOAuthUrl } from '@/utils/safe-url'
import type { ThreadsConfig, PublishScheduleType, TimeInterval } from '@/types/threads'
import type {
  ThreadsAuthStatus,
  ThreadsAuthVerify,
  ThreadsSeleniumAttemptResult,
  ThreadsSeleniumSessionRow,
} from '@/types/threads'
const AUTH_STATUS_POLL_INTERVAL_MS = 15_000

function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

const LEGACY_TAB_REDIRECT: Record<string, string> = {
  posts: '/analytics',
  create: '/posts',
  calendar: '/calendar?network=threads',
  profile: '/channels',
  processing: '/channels',
  session: '/channels',
}

function ThreadsHubMap() {
  const { selectedBrandId } = useBrand()
  const calendarHref = selectedBrandId
    ? `/calendar?brand=${selectedBrandId}&network=threads`
    : '/calendar?network=threads'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Brand → Channel</CardTitle>
        <CardDescription>
          Здесь только OAuth и сессия Meta/Instagram. Источники (@handle), collect/publish — в Channels.
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
              Расписание, фильтр network=threads.
            </p>
          </li>
          <li>
            <Link to="/channels" className="text-primary-400 hover:underline font-medium">
              Profile Settings → Channels
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Канал network=Threads, external_id=@handle, включите Collect.
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

export function ThreadsPage() {
  const { user } = useAuth()
  const hasTeam = Boolean(user?.group_id || user?.role_in_group)
  const canAuth = canManagePlatformAuth(user?.role_in_group, hasTeam)
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const [authStatus, setAuthStatus] = useState<ThreadsAuthStatus | null>(null)
  const [instagramHandle, setInstagramHandle] = useState('')
  const [metaLogin, setMetaLogin] = useState('')
  const [metaPassword, setMetaPassword] = useState('')
  const [isVerifyingAuth, setIsVerifyingAuth] = useState(false)
  const [verifyResult, setVerifyResult] = useState<ThreadsAuthVerify | null>(null)
  const [isSavingAuthHandle, setIsSavingAuthHandle] = useState(false)
  const [seleniumEmail, setSeleniumEmail] = useState('')
  const [seleniumPassword, setSeleniumPassword] = useState('')
  const [isSeleniumLoading, setIsSeleniumLoading] = useState(false)
  const [seleniumAttemptResult, setSeleniumAttemptResult] = useState<ThreadsSeleniumAttemptResult | null>(null)
  const [seleniumLastSession, setSeleniumLastSession] = useState<ThreadsSeleniumSessionRow | null>(null)

  const [publishEnabled, setPublishEnabled] = useState(false)
  const [collectEnabled, setCollectEnabled] = useState(false)
  const [takeScreenshotCollect, setTakeScreenshotCollect] = useState(false)
  const [publishScheduleType, setPublishScheduleType] = useState<PublishScheduleType>('on_new_messages')
  const [timeIntervals, setTimeIntervals] = useState<Array<{ id: string; start: string; end: string }>>([
    { id: generateId(), start: '', end: '' },
  ])

  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const connectedEffective = Boolean(authStatus?.connected_effective ?? authStatus?.connected)

  const loadProfile = useCallback(async () => {
    setIsLoadingProfile(true)
    try {
      const profile = await threadsService.getProfile()
      if (profile) {
        setInstagramHandle(profile.instagram_handle || '')
        setMetaLogin(profile.meta_login || '')
        setMetaPassword('')
        setPublishEnabled(profile.publish_enabled)
        setCollectEnabled(profile.collect_enabled)
        setTakeScreenshotCollect(Boolean(profile.take_screenshot_collect))
        setPublishScheduleType(
          (profile.schedule_type as PublishScheduleType) === 'by_intervals'
            ? 'by_intervals'
            : 'on_new_messages'
        )
        if (profile.time_intervals?.length) {
          setTimeIntervals(
            profile.time_intervals.map((interval: TimeInterval) => ({
              id: generateId(),
              start: interval.start,
              end: interval.end ?? '',
            }))
          )
        }
      }
    } catch (err) {
      console.error('Failed to load Threads profile:', err)
    } finally {
      setIsLoadingProfile(false)
    }
  }, [])

  const loadAuthStatus = useCallback(async () => {
    if (!user?.id) return
    try {
      const status = await threadsService.getAuthStatus(user.id)
      setAuthStatus(status)
    } catch (err) {
      console.error('[ThreadsPage] Failed to load auth status:', err)
    }
  }, [user?.id])

  const loadSeleniumLastSession = useCallback(async () => {
    if (!user?.id) return
    try {
      const data = await threadsService.getSeleniumLastSession()
      setSeleniumLastSession(data.session)
    } catch {
      setSeleniumLastSession(null)
    }
  }, [user?.id])

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

  useEffect(() => {
    if (searchParams.get('oauth') === 'success' || searchParams.get('oauth') === 'error') {
      if (user?.id) void loadAuthStatus()
      const message =
        searchParams.get('message') ||
        (searchParams.get('oauth') === 'success' ? 'Connected successfully' : 'Connection failed')
      setSuccess(searchParams.get('oauth') === 'success' ? message : '')
      setError(searchParams.get('oauth') === 'error' ? message : '')
      searchParams.delete('oauth')
      searchParams.delete('message')
      setSearchParams(searchParams, { replace: true })
    }
  }, [searchParams, setSearchParams, user?.id, loadAuthStatus])

  useEffect(() => {
    if (!user?.id) return
    void loadAuthStatus()
    const interval = setInterval(loadAuthStatus, AUTH_STATUS_POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [user?.id, loadAuthStatus])

  useEffect(() => {
    if (!user?.id) return
    void loadSeleniumLastSession()
  }, [user?.id, loadSeleniumLastSession])

  function buildConfigPayload(): ThreadsConfig {
    const payload: ThreadsConfig = {
      instagram_handle: instagramHandle || undefined,
      publish_enabled: publishEnabled,
      collect_enabled: collectEnabled,
      schedule_type: publishScheduleType === 'by_intervals' ? 'by_intervals' : 'on_new_messages',
      time_intervals:
        publishScheduleType === 'by_intervals'
          ? timeIntervals
              .filter((i) => i.start && i.end)
              .map((i) => ({ start: i.start, end: i.end }))
          : [],
      process_enabled: false,
      take_screenshot_collect: takeScreenshotCollect,
      meta_login: metaLogin || undefined,
    }
    if (metaPassword.trim()) {
      payload.meta_password = metaPassword.trim()
    }
    return payload
  }

  async function handleSaveAuthIdentity(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSavingAuthHandle(true)
    try {
      await threadsService.saveConfig(buildConfigPayload())
      setSuccess('Учётные данные сохранены')
      setMetaPassword('')
      await loadProfile()
      await threadsService.reloadBot()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsSavingAuthHandle(false)
    }
  }

  async function handleConnectThreads() {
    setError('')
    try {
      const { url } = await threadsService.getAuthUrl()
      const allowed = allowedOAuthUrl(url)
      if (!allowed) {
        setError('OAuth URL is not allowed')
        return
      }
      window.location.href = allowed
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function handleVerifyThreadsAuth() {
    if (!user?.id) return
    setIsVerifyingAuth(true)
    setVerifyResult(null)
    setError('')
    try {
      const result = await threadsService.verifyAuth(user.id)
      setVerifyResult(result)
      await loadAuthStatus()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsVerifyingAuth(false)
    }
  }

  async function handleSeleniumAttempt(e: FormEvent) {
    e.preventDefault()
    setError('')
    const email = seleniumEmail.trim()
    if (!email || !seleniumPassword.trim()) {
      setError('Укажите email/телефон и пароль Meta')
      return
    }
    setIsSeleniumLoading(true)
    try {
      const r = await threadsService.seleniumAttempt(email, seleniumPassword)
      setSeleniumAttemptResult(r)
      setSeleniumPassword('')
      await loadSeleniumLastSession()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsSeleniumLoading(false)
    }
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="Threads"
        description="OAuth Meta и сессия браузера. Каналы (@handle) — в Channels."
      />

      <ThreadsHubMap />

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
              OAuth — публикация через Graph API. Логин Instagram/Meta — чтение brand-каналов в браузере
              (threads.net/@handle). Можно также использовать учётку из раздела Instagram.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-8">
            {isLoadingProfile ? (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading...</div>
            ) : (
              <>
                <form onSubmit={handleSaveAuthIdentity} className="space-y-4">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Идентичность</h3>
                  <div className="grid gap-4 md:grid-cols-2">
                    <Input
                      label="@username (подпись / свой handle)"
                      type="text"
                      value={instagramHandle}
                      onChange={(e) => setInstagramHandle(e.target.value)}
                      placeholder="mybrand"
                      autoComplete="username"
                    />
                    <Input
                      label="Логин для браузера (email / @ig)"
                      type="text"
                      value={metaLogin}
                      onChange={(e) => setMetaLogin(e.target.value)}
                      placeholder="email или username Instagram"
                      autoComplete="username"
                    />
                    <Input
                      label="Пароль (браузер collect)"
                      type="password"
                      value={metaPassword}
                      onChange={(e) => setMetaPassword(e.target.value)}
                      placeholder="Оставьте пустым, чтобы не менять"
                      autoComplete="current-password"
                    />
                  </div>
                  <Button type="submit" isLoading={isSavingAuthHandle} variant="secondary">
                    Сохранить учётные данные
                  </Button>
                </form>

                <div className="flex flex-wrap items-center gap-3 p-3 rounded-lg bg-[var(--bg-tertiary)]">
                  <div
                    className={`w-3 h-3 rounded-full shrink-0 ${
                      connectedEffective ? 'bg-green-400' : 'bg-amber-400'
                    }`}
                  />
                  <div className="text-sm text-[var(--text-secondary)] min-w-0 flex-1">
                    <div>
                      {connectedEffective
                        ? 'OAuth токен активен'
                        : authStatus?.connected
                          ? 'Токен есть, но истёк — переподключитесь'
                          : 'OAuth не подключён'}
                    </div>
                    {authStatus?.expires_at && (
                      <div className="text-xs text-[var(--text-muted)] mt-1">
                        Истекает: {formatDateTime(authStatus.expires_at)}
                      </div>
                    )}
                    {authStatus?.threads_user_id && (
                      <div className="text-xs text-[var(--text-muted)] mt-0.5">
                        Threads user id: {authStatus.threads_user_id}
                      </div>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2 ml-auto">
                    <Button variant="ghost" size="sm" type="button" onClick={() => void loadAuthStatus()}>
                      Обновить
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      type="button"
                      isLoading={isVerifyingAuth}
                      onClick={() => void handleVerifyThreadsAuth()}
                    >
                      Проверить у Meta
                    </Button>
                    <Button type="button" size="sm" onClick={() => void handleConnectThreads()}>
                      Connect with Threads
                    </Button>
                  </div>
                </div>

                {verifyResult && (
                  <div
                    className={`p-4 rounded-lg border text-sm ${
                      verifyResult.valid
                        ? 'border-green-500/40 bg-green-500/5 text-green-400'
                        : 'border-amber-500/40 bg-amber-500/5 text-amber-200'
                    }`}
                  >
                    <p className="font-medium">
                      {verifyResult.valid ? 'Проверка пройдена' : 'Проверка не пройдена'}
                    </p>
                    <p className="mt-1 text-[var(--text-secondary)]">{verifyResult.message}</p>
                  </div>
                )}

                <div className="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] space-y-3">
                  <h3 className="text-sm font-semibold">Диагностика Selenium</h3>
                  <p className="text-xs text-[var(--text-muted)]">
                    Разовая проверка входа (пароль не сохраняется). Для постоянного collect сохраните логин
                    выше. Нужен ENABLE_THREADS_SELENIUM_FALLBACK=true.
                  </p>
                  <form
                    onSubmit={(ev) => {
                      void handleSeleniumAttempt(ev)
                    }}
                    className="space-y-3"
                  >
                    <div className="grid gap-3 sm:grid-cols-2 max-w-2xl">
                      <Input
                        label="Email / телефон"
                        type="text"
                        value={seleniumEmail}
                        onChange={(e) => setSeleniumEmail(e.target.value)}
                      />
                      <Input
                        label="Пароль (не сохраняется)"
                        type="password"
                        value={seleniumPassword}
                        onChange={(e) => setSeleniumPassword(e.target.value)}
                      />
                    </div>
                    <Button type="submit" variant="secondary" size="sm" isLoading={isSeleniumLoading}>
                      Запустить проверку
                    </Button>
                  </form>
                  {seleniumAttemptResult && (
                    <div className="text-sm rounded-md bg-[var(--bg-tertiary)] p-3 space-y-1">
                      <p className="font-medium">Статус: {seleniumAttemptResult.status}</p>
                      <p className="text-[var(--text-secondary)]">{seleniumAttemptResult.message}</p>
                    </div>
                  )}
                  {seleniumLastSession && (
                    <p className="text-xs text-[var(--text-muted)]">
                      Последняя сессия #{seleniumLastSession.id}: {seleniumLastSession.status}
                    </p>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      ) : (
        <Alert variant="info" className="mt-4">
          Подключать Threads может владелец или админ команды.{' '}
          <Link to="/channels" className="underline">
            К каналам
          </Link>
        </Alert>
      )}
    </PageContainer>
  )
}
