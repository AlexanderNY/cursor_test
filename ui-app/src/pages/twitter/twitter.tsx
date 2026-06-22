import { useState, FormEvent, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { apiClient } from '@/services/api-client'
import { twitterService } from '@/services/twitter-service'
import {
  TargetSocialNetworksWidget,
  createDefaultTargets,
  type TargetSocialNetworks,
} from '@/components/target-social-networks'
import type { TwitterProfile, TwitterScheduleType, TwPostRow, TwitterFollowingUser } from '@/types/twitter'

function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

function screenshotUrl(path: string): string {
  if (path.startsWith('http')) return path
  const base = apiClient.defaults.baseURL ?? '/api'
  const origin = typeof window !== 'undefined' ? window.location.origin : ''
  return `${origin}${base}${path.startsWith('/') ? '' : '/'}${path}`
}

export function TwitterPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState<'create' | 'auth' | 'posts' | 'profile'>('create')

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

  const [postText, setPostText] = useState('')
  const [postTargets, setPostTargets] = useState<TargetSocialNetworks>(() =>
    createDefaultTargets('tw')
  )

  const [posts, setPosts] = useState<TwPostRow[]>([])
  const [isLoadingPosts, setIsLoadingPosts] = useState(false)
  const [hasLoadedPosts, setHasLoadedPosts] = useState(false)

  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [isCreatingPost, setIsCreatingPost] = useState(false)
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

  useEffect(() => {
    if (activeTab === 'posts' && !hasLoadedPosts) {
      void loadPosts()
    }
  }, [activeTab, hasLoadedPosts])

  async function loadPosts() {
    setIsLoadingPosts(true)
    setError('')
    try {
      const data = await twitterService.getPosts(50, 0)
      setPosts(data)
      setHasLoadedPosts(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load posts')
    } finally {
      setIsLoadingPosts(false)
    }
  }

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
      window.location.href = url
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

  async function handleSaveProfile(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsLoading(true)

    try {
      await twitterService.saveProfile(buildProfilePayload() as TwitterProfile)
      setSuccess('Profile settings saved successfully')
      setTwitterPassword('')
      await loadProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile settings')
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

  async function handleCreatePost(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsCreatingPost(true)

    if (postText.length > 280) {
      setError('Post text cannot exceed 280 characters')
      setIsCreatingPost(false)
      return
    }

    try {
      await twitterService.createPost({
        text: postText,
        to_tg: postTargets.tg,
        to_tw: postTargets.tw,
        to_wp: postTargets.wp,
        to_vk: postTargets.vk,
        to_threads: postTargets.threads,
        to_dzen: postTargets.dzen,
        to_instagram: postTargets.instagram,
      })
      setSuccess('Post queued successfully')
      setPostText('')
      setHasLoadedPosts(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create post')
    } finally {
      setIsCreatingPost(false)
    }
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader title="Twitter / X Integration" description="Connect X, manage posting and feed collection" />

      {error && (
        <Alert variant="error" className="animate-slide-down">
          {error}
        </Alert>
      )}

      {success && (
        <Alert variant="success" className="animate-slide-down">
          {success}
        </Alert>
      )}

      <div className="flex border-b border-[var(--border-color)]">
        <button
          className={`px-6 py-3 text-sm font-medium transition-all relative ${
            activeTab === 'create'
              ? 'text-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => setActiveTab('create')}
        >
          Create Post
          {activeTab === 'create' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />
          )}
        </button>
        <button
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
        <button
          className={`px-6 py-3 text-sm font-medium transition-all relative ${
            activeTab === 'posts'
              ? 'text-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => setActiveTab('posts')}
        >
          Posts
          {activeTab === 'posts' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />
          )}
        </button>
        <button
          className={`px-6 py-3 text-sm font-medium transition-all relative ${
            activeTab === 'profile'
              ? 'text-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => setActiveTab('profile')}
        >
          Profile Settings
          {activeTab === 'profile' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />
          )}
        </button>
      </div>

      {activeTab === 'create' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 text-primary-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
              Create post
            </CardTitle>
            <CardDescription>Creates a row in tw_posts for the pipeline (max 280 characters)</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreatePost} className="space-y-6">
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">Post text</label>
                <textarea
                  value={postText}
                  onChange={(e) => setPostText(e.target.value)}
                  maxLength={280}
                  rows={6}
                  className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                  placeholder="Enter your post..."
                  required
                />
                <p className="text-xs text-[var(--text-muted)] mt-2">
                  {postText.length} / 280 characters
                </p>
              </div>
              <TargetSocialNetworksWidget value={postTargets} onChange={setPostTargets} />
              <CardFooter className="px-0">
                <Button type="submit" isLoading={isCreatingPost} className="w-full sm:w-auto">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5 mr-2"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                  </svg>
                  Queue post
                </Button>
              </CardFooter>
            </form>
          </CardContent>
        </Card>
      )}

      {activeTab === 'auth' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 text-primary-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                />
              </svg>
              Авторизация
            </CardTitle>
            <CardDescription>
              OAuth для API X; логин и пароль — для автоматизации (tw-bot / скриншоты), не для REST.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingProfile ? (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading...</div>
            ) : (
              <div className="space-y-8">
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] space-y-3">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Подключение (OAuth 2.0)</h3>
                  <p className="text-sm text-[var(--text-secondary)]">
                    Для постинга и проверки подписок нужен OAuth. Redirect URI должен совпадать с{' '}
                    <code className="text-xs">TWITTER_OAUTH_REDIRECT_URI</code>. После смены scope (
                    <code className="text-xs">follows.read</code>) выполните подключение заново.
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
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Учётные данные</h3>
                  <p className="text-xs text-[var(--text-muted)]">
                    Официальный API X не принимает пароль. Поля ниже сохраняются для сценариев с браузером / прокси.
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
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Проверка авторизации</h3>
                  <p className="text-xs text-[var(--text-muted)]">
                    Запрашиваем список подписок через X API (нужен OAuth с правом follows.read).
                  </p>
                  <div className="flex flex-wrap gap-3">
                    <Button
                      type="button"
                      onClick={() => void refreshFollowing()}
                      isLoading={isLoadingFollowing}
                    >
                      Проверить (список подписок)
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
                  </div>
                  {followingUsers.length > 0 && (
                    <ul className="mt-4 space-y-2 max-h-80 overflow-y-auto rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-3">
                      {followingUsers.map((u) => (
                        <li
                          key={u.id}
                          className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-[var(--text-primary)] border-b border-[var(--border-color)] border-opacity-50 pb-2 last:border-0 last:pb-0"
                        >
                          <span className="font-mono text-primary-400">
                            @{u.username ?? u.id}
                          </span>
                          {u.name && (
                            <span className="text-[var(--text-secondary)]">{u.name}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}

                  <div className="space-y-3 pt-4 border-t border-[var(--border-color)]">
                    <p className="text-xs text-[var(--text-muted)]">
                      Если OAuth или API недоступны (403, план разработчика): проверка через браузер в tw-bot. Не
                      заменяет OAuth для публикации по API. Возможны капча, 2FA и блокировки — см. правила X.
                    </p>
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => void runSeleniumVerify()}
                      isLoading={isLoadingSelenium}
                    >
                      Проверить через браузер (Selenium)
                    </Button>
                    {seleniumUsers.length > 0 && (
                      <ul className="mt-2 space-y-2 max-h-64 overflow-y-auto rounded-xl border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-3">
                        <li className="text-xs font-medium text-[var(--text-secondary)] mb-2">Список (веб-страница)</li>
                        {seleniumUsers.map((u) => (
                          <li
                            key={`se-${u.id}`}
                            className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-[var(--text-primary)] border-b border-[var(--border-color)] border-opacity-50 pb-2 last:border-0 last:pb-0"
                          >
                            <span className="font-mono text-primary-400">@{u.username ?? u.id}</span>
                            {u.name && <span className="text-[var(--text-secondary)]">{u.name}</span>}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 'posts' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 text-primary-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 10h16M4 14h10"
                />
              </svg>
              Posts
            </CardTitle>
            <CardDescription>Your tw_posts records (status reflects pipeline and tw-bot)</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingPosts ? (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading...</div>
            ) : posts.length === 0 ? (
              <div className="text-center py-8 text-[var(--text-muted)]">No posts yet.</div>
            ) : (
              <ul className="space-y-4">
                {posts.map((p) => (
                  <li
                    key={p.id}
                    className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]"
                  >
                    <div className="flex flex-wrap gap-2 items-center text-xs text-[var(--text-muted)] mb-2">
                      <span className="font-mono">#{p.id}</span>
                      {p.status && (
                        <span className="px-2 py-0.5 rounded bg-[var(--bg-tertiary)]">{p.status}</span>
                      )}
                      {p.created_at && <span>{new Date(p.created_at).toLocaleString()}</span>}
                    </div>
                    {p.url && (
                      <a
                        href={p.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary-400 hover:underline break-all"
                      >
                        {p.url}
                      </a>
                    )}
                    {p.post_text && (
                      <p className="text-[var(--text-primary)] mt-2 whitespace-pre-wrap">{p.post_text}</p>
                    )}
                    {p.screenshot && (
                      <img
                        src={screenshotUrl(p.screenshot)}
                        alt=""
                        className="mt-3 max-h-48 rounded-lg border border-[var(--border-color)] object-contain"
                      />
                    )}
                  </li>
                ))}
              </ul>
            )}
            <div className="mt-4">
              <Button type="button" variant="secondary" size="sm" onClick={() => void loadPosts()}>
                Refresh
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'profile' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 text-primary-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              Profile settings
            </CardTitle>
            <CardDescription>Publishing, collection, proxy (tw-bot). Авторизация — вкладка «Авторизация».</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingProfile ? (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading profile...</div>
            ) : (
              <form onSubmit={handleSaveProfile} className="space-y-8">
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-5 w-5 text-primary-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                      />
                    </svg>
                    Publishing & collection
                  </h3>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={publishEnabled}
                        onChange={(e) => setPublishEnabled(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                      Enable publishing (tw-bot)
                    </span>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={collectEnabled}
                        onChange={(e) => setCollectEnabled(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                      Enable feed collection (tw-bot)
                    </span>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={takeScreenshotCollect}
                        onChange={(e) => setTakeScreenshotCollect(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                      Screenshot tweets when collecting (url-bot / Selenium)
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
                  <label className="text-sm font-medium text-[var(--text-secondary)] block">Schedule</label>
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
                      <span className="text-[var(--text-primary)]">Immediate (on new items)</span>
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
                              <svg
                                xmlns="http://www.w3.org/2000/svg"
                                className="h-5 w-5"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                />
                              </svg>
                            </Button>
                          )}
                        </div>
                      ))}
                      {timeIntervals.length < 3 && (
                        <Button type="button" variant="secondary" size="sm" onClick={addTimeInterval}>
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-4 w-4 mr-2"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                          </svg>
                          Add interval
                        </Button>
                      )}
                    </div>
                  )}
                </div>

                <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Proxy</h3>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={useProxy}
                        onChange={(e) => setUseProxy(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
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
                        placeholder="Proxy username"
                      />
                      <Input
                        label="Proxy password"
                        type="password"
                        value={proxyPass}
                        onChange={(e) => setProxyPass(e.target.value)}
                        placeholder="Proxy password"
                      />
                      <Input
                        label="Proxy host"
                        type="text"
                        value={proxyHost}
                        onChange={(e) => setProxyHost(e.target.value)}
                        placeholder="Proxy host"
                      />
                      <Input
                        label="Proxy port"
                        type="number"
                        value={proxyPort}
                        onChange={(e) => setProxyPort(e.target.value)}
                        placeholder="Proxy port"
                      />
                    </div>
                  )}
                </div>

                <CardFooter className="px-0">
                  <Button type="submit" isLoading={isLoading} className="w-full sm:w-auto">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-5 w-5 mr-2"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Save profile settings
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
