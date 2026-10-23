import { useState, FormEvent, useEffect, useCallback } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { twitterService } from '@/services/twitter-service'
import type { TwitterProfile, TwitterScheduleType, TwitterFollowingUser } from '@/types/twitter'
import { useAuth } from '@/contexts/auth-context'
import { useBrand } from '@/contexts/brand-context'
import { canManagePlatformAuth } from '@/types/smm'
import { Switch } from '@/components/ui/switch'
import { allowedOAuthUrl } from '@/utils/safe-url'

function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

const LEGACY_TAB_REDIRECT: Record<string, string> = {
  posts: '/analytics',
  create: '/posts',
  calendar: '/calendar?network=tw',
  profile: '/channels',
  processing: '/channels',
}

function TwitterHubMap() {
  const { selectedBrandId } = useBrand()
  const calendarHref = selectedBrandId
    ? `/calendar?brand=${selectedBrandId}&network=tw`
    : '/calendar?network=tw'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Brand → Channel</CardTitle>
        <CardDescription>
          Здесь только OAuth и сессия X. Источники (@handle), collect/publish и цели — в Channels.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="grid gap-3 sm:grid-cols-2 text-sm">
          <li>
            <Link to="/analytics" className="text-primary-400 hover:underline font-medium">
              Posts → Analytics
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Очередь и лента по каналам бренда (не отдельный список на /twitter).
            </p>
          </li>
          <li>
            <Link to={calendarHref} className="text-primary-400 hover:underline font-medium">
              Calendar → общий календарь
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Расписание публикаций, фильтр network=tw.
            </p>
          </li>
          <li>
            <Link to="/channels" className="text-primary-400 hover:underline font-medium">
              Profile Settings → Channels
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Добавьте канал network=Twitter с external_id=@handle, включите Collect.
            </p>
          </li>
          <li>
            <Link to="/channels" className="text-primary-400 hover:underline font-medium">
              Чтение каналов
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              tw-bot читает x.com/@handle через браузер (логин ниже) или API (OAuth).
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

export function TwitterPage() {
  const { user } = useAuth()
  const hasTeam = Boolean(user?.group_id || user?.role_in_group)
  const canAuth = canManagePlatformAuth(user?.role_in_group, hasTeam)
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState<'auth' | 'session'>('auth')

  const [publishEnabled, setPublishEnabled] = useState(false)
  const [collectEnabled, setCollectEnabled] = useState(false)
  const [scheduleType, setScheduleType] = useState<TwitterScheduleType>('immediate')
  const [timeIntervals, setTimeIntervals] = useState<Array<{ id: string; start: string; end: string }>>([
    { id: generateId(), start: '', end: '' },
  ])
  const [useProxy, setUseProxy] = useState(false)
  const [proxyUser, setProxyUser] = useState('')
  const [proxyPass, setProxyPass] = useState('')
  const [proxyHost, setProxyHost] = useState('')
  const [proxyPort, setProxyPort] = useState('')
  const [twitterUsername, setTwitterUsername] = useState('')
  const [twitterPassword, setTwitterPassword] = useState('')
  const [takeScreenshotCollect, setTakeScreenshotCollect] = useState(false)
  const [screenshotXpath, setScreenshotXpath] = useState('')
  const [twitterConnected, setTwitterConnected] = useState(false)
  const [twitterRestId, setTwitterRestId] = useState<string | null>(null)

  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [isConnectingOAuth, setIsConnectingOAuth] = useState(false)
  const [followingUsers, setFollowingUsers] = useState<TwitterFollowingUser[]>([])
  const [followingNextToken, setFollowingNextToken] = useState<string | null>(null)
  const [isLoadingFollowing, setIsLoadingFollowing] = useState(false)
  const [isSavingCredentials, setIsSavingCredentials] = useState(false)
  const [seleniumUsers, setSeleniumUsers] = useState<TwitterFollowingUser[]>([])
  const [isLoadingSelenium, setIsLoadingSelenium] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadProfile = useCallback(async () => {
    setIsLoadingProfile(true)
    try {
      const profile = await twitterService.getProfile()
      if (profile) {
        setPublishEnabled(profile.publish_enabled)
        setCollectEnabled(profile.collect_enabled)
        setScheduleType(profile.schedule_type ?? 'immediate')
        if (profile.time_intervals && profile.time_intervals.length > 0) {
          setTimeIntervals(
            profile.time_intervals.map((interval) => ({
              id: generateId(),
              start: interval.start,
              end: interval.end ?? '',
            }))
          )
        }
        setUseProxy(profile.use_proxy || false)
        setProxyUser(profile.proxy_user || '')
        setProxyPass(profile.proxy_pass || '')
        setProxyHost(profile.proxy_host || '')
        setProxyPort(profile.proxy_port?.toString() || '')
        setTwitterUsername(profile.twitter_username || '')
        setTwitterPassword('')
        setTakeScreenshotCollect(profile.take_screenshot_collect ?? false)
        setScreenshotXpath(profile.screenshot_xpath || '')
        setTwitterConnected(profile.twitter_connected ?? false)
        setTwitterRestId(profile.twitter_rest_id ?? null)
      }
    } catch (err) {
      console.error('Failed to load profile:', err)
    } finally {
      setIsLoadingProfile(false)
    }
  }, [])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  useEffect(() => {
    const legacyTab = searchParams.get('tab')
    if (legacyTab && LEGACY_TAB_REDIRECT[legacyTab]) {
      navigate(LEGACY_TAB_REDIRECT[legacyTab], { replace: true })
      return
    }
    if (searchParams.get('auth') === '1') {
      setActiveTab('auth')
      searchParams.delete('auth')
      setSearchParams(searchParams, { replace: true })
    }
  }, [searchParams, setSearchParams, navigate])

  useEffect(() => {
    if (searchParams.get('oauth') === 'success' || searchParams.get('oauth') === 'error') {
      const message =
        searchParams.get('message') ||
        (searchParams.get('oauth') === 'success' ? 'Connected to X successfully' : 'Connection failed')
      setSuccess(searchParams.get('oauth') === 'success' ? message : '')
      setError(searchParams.get('oauth') === 'error' ? message : '')
      searchParams.delete('oauth')
      searchParams.delete('message')
      setSearchParams(searchParams, { replace: true })
      void loadProfile()
    }
  }, [searchParams, setSearchParams, loadProfile])

  function addTimeInterval() {
    if (timeIntervals.length < 3) {
      setTimeIntervals([...timeIntervals, { id: generateId(), start: '', end: '' }])
    }
  }

  function removeTimeInterval(id: string) {
    if (timeIntervals.length > 1) {
      setTimeIntervals(timeIntervals.filter((interval) => interval.id !== id))
    }
  }

  function updateTimeInterval(id: string, field: 'start' | 'end', value: string) {
    setTimeIntervals(
      timeIntervals.map((interval) => (interval.id === id ? { ...interval, [field]: value } : interval))
    )
  }

  async function handleConnectX() {
    setError('')
    setSuccess('')
    setIsConnectingOAuth(true)
    try {
      const url = await twitterService.getOAuthUrl()
      const allowed = allowedOAuthUrl(url)
      if (!allowed) {
        setError('OAuth URL is not allowed')
        return
      }
      window.location.href = allowed
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get OAuth URL')
    } finally {
      setIsConnectingOAuth(false)
    }
  }

  function buildProfilePayload(): Record<string, unknown> {
    const profile: Record<string, unknown> = {
      publish_enabled: publishEnabled,
      collect_enabled: collectEnabled,
      schedule_type: scheduleType,
      time_intervals:
        scheduleType === 'intervals'
          ? timeIntervals.filter((interval) => interval.start && interval.end).map((interval) => ({
              start: interval.start,
              end: interval.end,
            }))
          : [],
      use_proxy: useProxy,
      proxy_user: useProxy ? proxyUser : undefined,
      proxy_pass: useProxy ? proxyPass : undefined,
      proxy_host: useProxy ? proxyHost : undefined,
      proxy_port: useProxy ? (proxyPort ? Number(proxyPort) : undefined) : undefined,
      twitter_username: twitterUsername || undefined,
      take_screenshot_collect: takeScreenshotCollect,
      screenshot_xpath: screenshotXpath.trim() || undefined,
    }
    if (twitterPassword.trim()) {
      profile.twitter_password = twitterPassword.trim()
    }
    return profile
  }

  async function handleSaveSession(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsLoading(true)
    try {
      await twitterService.saveProfile(buildProfilePayload() as TwitterProfile)
      setSuccess('Session settings saved')
      setTwitterPassword('')
      await loadProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleSaveCredentials(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSavingCredentials(true)
    try {
      await twitterService.saveProfile(buildProfilePayload() as TwitterProfile)
      setSuccess('Credentials saved')
      setTwitterPassword('')
      await loadProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save credentials')
    } finally {
      setIsSavingCredentials(false)
    }
  }

  async function refreshFollowing() {
    setError('')
    setSuccess('')
    setIsLoadingFollowing(true)
    try {
      const res = await twitterService.getFollowing({ max_results: 50 })
      setFollowingUsers(res.users)
      setFollowingNextToken(res.next_token ?? null)
      setSuccess(
        res.users.length === 0
          ? 'Authorization OK, the following list is empty'
          : 'Subscriptions loaded'
      )
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load following'
      setError(msg)
      setFollowingUsers([])
      setFollowingNextToken(null)
    } finally {
      setIsLoadingFollowing(false)
    }
  }

  async function loadMoreFollowing() {
    if (!followingNextToken) return
    const token = followingNextToken
    setError('')
    setIsLoadingFollowing(true)
    try {
      const res = await twitterService.getFollowing({
        max_results: 50,
        pagination_token: token,
      })
      setFollowingUsers((prev) => [...prev, ...res.users])
      setFollowingNextToken(res.next_token ?? null)
      setSuccess('Subscriptions loaded')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load following')
    } finally {
      setIsLoadingFollowing(false)
    }
  }

  async function runSeleniumVerify() {
    setError('')
    setSuccess('')
    setIsLoadingSelenium(true)
    try {
      const res = await twitterService.verifySelenium()
      if (res.ok) {
        setSeleniumUsers(res.users)
        setSuccess(
          res.message?.trim() ||
            (res.users.length === 0
              ? 'Selenium: вход подтверждён, список подписок пуст или не распознан'
              : 'Selenium: подписки загружены')
        )
      } else {
        setSeleniumUsers([])
        const baseErr = res.error || 'Проверка Selenium не удалась'
        setError(
          res.diag_s3_key ? `${baseErr} (диагностика в S3: ${res.diag_s3_key})` : baseErr
        )
      }
    } catch (err) {
      setSeleniumUsers([])
      setError(err instanceof Error ? err.message : 'Selenium verify failed')
    } finally {
      setIsLoadingSelenium(false)
    }
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="Twitter / X"
        description="OAuth и сессия браузера. Каналы (@handle) — в Channels."
      />

      <TwitterHubMap />

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

      <div className="flex border-b border-[var(--border-color)] mt-4">
        {canAuth && (
          <button
            type="button"
            className={`px-6 py-3 text-sm font-medium transition-all relative ${
              activeTab === 'auth'
                ? 'text-primary-400'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
            onClick={() => setActiveTab('auth')}
          >
            Авторизация
            {activeTab === 'auth' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />
            )}
          </button>
        )}
        <button
          type="button"
          className={`px-6 py-3 text-sm font-medium transition-all relative ${
            activeTab === 'session'
              ? 'text-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => setActiveTab('session')}
        >
          Session
          {activeTab === 'session' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />
          )}
        </button>
      </div>

      {activeTab === 'auth' && canAuth && (
        <Card className="animate-slide-up mt-4">
          <CardHeader>
            <CardTitle>Авторизация</CardTitle>
            <CardDescription>
              OAuth — публикация через API. Логин/пароль — чтение таймлайнов brand-каналов в браузере
              (рекомендуемый путь для Free/Basic API).
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingProfile ? (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading...</div>
            ) : (
              <div className="space-y-8">
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] space-y-3">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                    Подключение (OAuth 2.0)
                  </h3>
                  <p className="text-sm text-[var(--text-secondary)]">
                    Нужен для постинга и API-проверки. Redirect URI должен совпадать с{' '}
                    <code className="text-xs">TWITTER_OAUTH_REDIRECT_URI</code>.
                  </p>
                  <div className="flex flex-wrap items-center gap-3">
                    <Button type="button" onClick={() => void handleConnectX()} isLoading={isConnectingOAuth}>
                      Подключить X
                    </Button>
                    <span className="text-sm text-[var(--text-secondary)]">
                      {twitterConnected ? (
                        <>
                          Подключено
                          {twitterRestId ? ` (id ${twitterRestId})` : ''}
                        </>
                      ) : (
                        'Не подключено'
                      )}
                    </span>
                  </div>
                </div>

                <form onSubmit={handleSaveCredentials} className="space-y-4">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                    Учётные данные (браузер)
                  </h3>
                  <p className="text-xs text-[var(--text-muted)]">
                    Для сбора постов из Channels: tw-bot открывает x.com/@handle под этой сессией.
                    API пароль не принимает.
                  </p>
                  <div className="grid gap-4 md:grid-cols-2">
                    <Input
                      label="Логин X (@handle)"
                      type="text"
                      value={twitterUsername}
                      onChange={(e) => setTwitterUsername(e.target.value)}
                      placeholder="@handle"
                      autoComplete="username"
                    />
                    <Input
                      label="Пароль"
                      type="password"
                      value={twitterPassword}
                      onChange={(e) => setTwitterPassword(e.target.value)}
                      placeholder="Оставьте пустым, чтобы не менять"
                      autoComplete="current-password"
                    />
                  </div>
                  <Button type="submit" isLoading={isSavingCredentials} variant="secondary">
                    Сохранить учётные данные
                  </Button>
                </form>

                <div className="space-y-4 pt-2 border-t border-[var(--border-color)]">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                    Проверка авторизации
                  </h3>
                  <p className="text-xs text-[var(--text-muted)]">
                    API: список подписок (нужен OAuth с follows.read). Браузер: вход Selenium.
                  </p>
                  <div className="flex flex-wrap gap-3">
                    <Button
                      type="button"
                      onClick={() => void refreshFollowing()}
                      isLoading={isLoadingFollowing}
                    >
                      Проверить (API / подписки)
                    </Button>
                    {followingNextToken && (
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => void loadMoreFollowing()}
                        isLoading={isLoadingFollowing}
                      >
                        Загрузить ещё
                      </Button>
                    )}
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => void runSeleniumVerify()}
                      isLoading={isLoadingSelenium}
                    >
                      Проверить через браузер
                    </Button>
                  </div>
                  {followingUsers.length > 0 && (
                    <ul className="mt-4 space-y-2 max-h-80 overflow-y-auto rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-3">
                      {followingUsers.map((u) => (
                        <li
                          key={u.id}
                          className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-[var(--text-primary)] border-b border-[var(--border-color)] border-opacity-50 pb-2 last:border-0 last:pb-0"
                        >
                          <span className="font-mono text-primary-400">@{u.username ?? u.id}</span>
                          {u.name && (
                            <span className="text-[var(--text-secondary)]">{u.name}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                  {seleniumUsers.length > 0 && (
                    <ul className="mt-2 space-y-2 max-h-64 overflow-y-auto rounded-xl border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-3">
                      <li className="text-xs font-medium text-[var(--text-secondary)] mb-2">
                        Selenium
                      </li>
                      {seleniumUsers.map((u) => (
                        <li
                          key={`se-${u.id}`}
                          className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-[var(--text-primary)] border-b border-[var(--border-color)] border-opacity-50 pb-2 last:border-0 last:pb-0"
                        >
                          <span className="font-mono text-primary-400">@{u.username ?? u.id}</span>
                          {u.name && (
                            <span className="text-[var(--text-secondary)]">{u.name}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 'session' && (
        <Card className="animate-slide-up mt-4">
          <CardHeader>
            <CardTitle>Session / browser</CardTitle>
            <CardDescription>
              Прокси и скриншоты для tw-bot. Collect/Publish по источникам — в{' '}
              <Link to="/channels" className="text-primary-400 hover:underline">
                Channels
              </Link>
              . Legacy «лента Following» ниже — только если нет brand-каналов.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingProfile ? (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading profile...</div>
            ) : (
              <form onSubmit={handleSaveSession} className="space-y-8">
                <div className="space-y-4">
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <Switch
                      checked={publishEnabled}
                      onChange={(e) => setPublishEnabled(e.target.checked)}
                    />
                    <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                      Enable publishing (tw-bot, нужен OAuth)
                    </span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <Switch
                      checked={collectEnabled}
                      onChange={(e) => setCollectEnabled(e.target.checked)}
                    />
                    <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                      Legacy: собирать Following (если нет каналов в бренде)
                    </span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <Switch
                      checked={takeScreenshotCollect}
                      onChange={(e) => setTakeScreenshotCollect(e.target.checked)}
                    />
                    <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                      Screenshot tweets when collecting
                    </span>
                  </label>
                  {takeScreenshotCollect && (
                    <Input
                      label="XPath for tweet container (optional)"
                      type="text"
                      value={screenshotXpath}
                      onChange={(e) => setScreenshotXpath(e.target.value)}
                      placeholder="//article[@data-testid='tweet']"
                    />
                  )}
                </div>

                <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
                  <label className="text-sm font-medium text-[var(--text-secondary)] block">
                    Schedule (legacy profile collect)
                  </label>
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="radio"
                        name="scheduleType"
                        value="immediate"
                        checked={scheduleType === 'immediate'}
                        onChange={() => setScheduleType('immediate')}
                        className="w-4 h-4 text-primary-500"
                      />
                      <span className="text-[var(--text-primary)]">Immediate</span>
                    </label>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="radio"
                        name="scheduleType"
                        value="intervals"
                        checked={scheduleType === 'intervals'}
                        onChange={() => setScheduleType('intervals')}
                        className="w-4 h-4 text-primary-500"
                      />
                      <span className="text-[var(--text-primary)]">By time intervals</span>
                    </label>
                  </div>
                  {scheduleType === 'intervals' && (
                    <div className="space-y-3 mt-4 animate-slide-down">
                      {timeIntervals.map((interval, index) => (
                        <div key={interval.id} className="flex gap-3 items-end">
                          <Input
                            label={`Interval ${index + 1} start`}
                            type="time"
                            value={interval.start}
                            onChange={(e) => updateTimeInterval(interval.id, 'start', e.target.value)}
                            className="flex-1"
                          />
                          <Input
                            label="End"
                            type="time"
                            value={interval.end}
                            onChange={(e) => updateTimeInterval(interval.id, 'end', e.target.value)}
                            className="flex-1"
                          />
                          {timeIntervals.length > 1 && (
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => removeTimeInterval(interval.id)}
                              className="px-3 text-red-400 hover:text-red-300"
                            >
                              Remove
                            </Button>
                          )}
                        </div>
                      ))}
                      {timeIntervals.length < 3 && (
                        <Button type="button" variant="secondary" size="sm" onClick={addTimeInterval}>
                          Add interval
                        </Button>
                      )}
                    </div>
                  )}
                </div>

                <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Proxy</h3>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <Switch checked={useProxy} onChange={(e) => setUseProxy(e.target.checked)} />
                    <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                      Use proxy
                    </span>
                  </label>
                  {useProxy && (
                    <div className="grid gap-4 md:grid-cols-2 animate-slide-down p-4 bg-[var(--bg-secondary)] rounded-xl">
                      <Input
                        label="Proxy user"
                        type="text"
                        value={proxyUser}
                        onChange={(e) => setProxyUser(e.target.value)}
                      />
                      <Input
                        label="Proxy password"
                        type="password"
                        value={proxyPass}
                        onChange={(e) => setProxyPass(e.target.value)}
                      />
                      <Input
                        label="Proxy host"
                        type="text"
                        value={proxyHost}
                        onChange={(e) => setProxyHost(e.target.value)}
                      />
                      <Input
                        label="Proxy port"
                        type="number"
                        value={proxyPort}
                        onChange={(e) => setProxyPort(e.target.value)}
                      />
                    </div>
                  )}
                </div>

                <CardFooter className="px-0">
                  <Button type="submit" isLoading={isLoading} className="w-full sm:w-auto">
                    Save session settings
                  </Button>
                </CardFooter>
              </form>
            )}
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
