import { useState, useEffect, FormEvent, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { SkeletonCard } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/ui'
import { threadsService } from '@/services/threads-service'
import { getErrorMessage } from '@/services/api-client'
import {
  TargetSocialNetworksWidget,
  createDefaultTargets,
  type TargetSocialNetworks,
} from '@/components/target-social-networks'
import { useAuth } from '@/contexts/auth-context'
import type { ThreadsConfig, ThreadsPostListItem, TimeInterval, PublishScheduleType } from '@/types/threads'
import type {
  ThreadsAuthStatus,
  ThreadsAuthVerify,
  ThreadsSeleniumAttemptResult,
  ThreadsSeleniumSessionRow,
} from '@/types/threads'

const AUTH_STATUS_POLL_INTERVAL_MS = 15_000
const THREADS_TEXT_LIMIT = 500

function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

const SCHEDULE_MINUTES = [0, 15, 30, 45] as const
type ScheduleMinute = (typeof SCHEDULE_MINUTES)[number]

export function ThreadsPage() {
  const { user } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()

  const [activeTab, setActiveTab] = useState<'create' | 'posts' | 'profile' | 'processing' | 'auth'>(
    () => (searchParams.get('auth') === '1' ? 'auth' : 'create')
  )

  const [authStatus, setAuthStatus] = useState<ThreadsAuthStatus | null>(null)
  const [instagramHandle, setInstagramHandle] = useState('')
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
  const [publishScheduleType, setPublishScheduleType] = useState<PublishScheduleType>('on_new_messages')
  const [publishScheduleHour, setPublishScheduleHour] = useState(9)
  const [publishScheduleMinute, setPublishScheduleMinute] = useState<ScheduleMinute>(0)
  const [processEnabled, setProcessEnabled] = useState(false)
  const [processingDescription, setProcessingDescription] = useState('')
  const [removeEmojis, setRemoveEmojis] = useState(false)
  const [removeImages, setRemoveImages] = useState(false)
  const [cleanHtml, setCleanHtml] = useState(false)
  const [processServiceWordpress, setProcessServiceWordpress] = useState(false)
  const [processServiceTelegram, setProcessServiceTelegram] = useState(false)
  const [processServiceTwitter, setProcessServiceTwitter] = useState(false)
  const [processServiceVkontakte, setProcessServiceVkontakte] = useState(false)
  const [processServiceThreads, setProcessServiceThreads] = useState(false)
  const [statusReviewAfterProcess, setStatusReviewAfterProcess] = useState(false)
  const [addStaticHtml, setAddStaticHtml] = useState(false)
  const [staticHtmlContent, setStaticHtmlContent] = useState('')

  const [postText, setPostText] = useState('')
  const [postTargets, setPostTargets] = useState<TargetSocialNetworks>(() =>
    createDefaultTargets('threads')
  )
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)

  const [posts, setPosts] = useState<ThreadsPostListItem[]>([])
  const [isLoadingPosts, setIsLoadingPosts] = useState(false)
  const [hasLoadedPosts, setHasLoadedPosts] = useState(false)
  const [editingPostId, setEditingPostId] = useState<number | null>(null)
  const [deletingPostId, setDeletingPostId] = useState<number | null>(null)

  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [isCreatingPost, setIsCreatingPost] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    loadProfile()
  }, [])

  useEffect(() => {
    if (searchParams.get('oauth') === 'success' || searchParams.get('oauth') === 'error') {
      if (user?.id) loadAuthStatus()
      const message = searchParams.get('message') || (searchParams.get('oauth') === 'success' ? 'Connected successfully' : 'Connection failed')
      setSuccess(searchParams.get('oauth') === 'success' ? message : '')
      setError(searchParams.get('oauth') === 'error' ? message : '')
      searchParams.delete('oauth')
      searchParams.delete('message')
      setSearchParams(searchParams, { replace: true })
    }
  }, [searchParams, setSearchParams, user?.id])

  const loadAuthStatus = useCallback(async () => {
    if (!user?.id) return
    try {
      const status = await threadsService.getAuthStatus(user.id)
      setAuthStatus(status)
    } catch (err) {
      console.error('[ThreadsPage] Failed to load auth status:', err)
    }
  }, [user?.id])

  useEffect(() => {
    if (!user?.id) return
    loadAuthStatus()
    const interval = setInterval(loadAuthStatus, AUTH_STATUS_POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [user?.id, loadAuthStatus])

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
    if (activeTab === 'auth' && user?.id) {
      void loadSeleniumLastSession()
    }
  }, [activeTab, user?.id, loadSeleniumLastSession])

  useEffect(() => {
    if (activeTab === 'posts' && !hasLoadedPosts) loadPosts()
  }, [activeTab, hasLoadedPosts])

  async function loadProfile() {
    setIsLoadingProfile(true)
    setError('')
    try {
      const profile = await threadsService.getProfile()
      if (profile) {
        setInstagramHandle((profile.instagram_handle ?? '').replace(/^@/, ''))
        setPublishEnabled(profile.publish_enabled ?? false)
        setCollectEnabled(profile.collect_enabled ?? false)
        setPublishScheduleType((profile.schedule_type as PublishScheduleType) || 'on_new_messages')
        const ti = profile.time_intervals
        if (Array.isArray(ti) && ti.length > 0 && ti[0]?.start) {
          const [h, m] = ti[0].start.split(':').map(Number)
          setPublishScheduleHour(Number.isFinite(h) ? Math.max(0, Math.min(23, h)) : 9)
          const rawMin = Number.isFinite(m) ? m : 0
          setPublishScheduleMinute(SCHEDULE_MINUTES.reduce((prev, curr) =>
            Math.abs(curr - rawMin) < Math.abs(prev - rawMin) ? curr : prev
          ) as ScheduleMinute)
        }
        setProcessEnabled(profile.process_enabled ?? false)
        setProcessingDescription(profile.processing_description || '')
        setRemoveEmojis(profile.remove_emojis ?? false)
        setRemoveImages(profile.remove_images ?? false)
        setCleanHtml(profile.clean_html ?? false)
        const ps = profile.process_services
        if (Array.isArray(ps)) {
          setProcessServiceWordpress(ps.includes('wordpress'))
          setProcessServiceTelegram(ps.includes('telegram'))
          setProcessServiceTwitter(ps.includes('twitter'))
          setProcessServiceVkontakte(ps.includes('vkontakte'))
          setProcessServiceThreads(ps.includes('threads'))
        }
        setStatusReviewAfterProcess(profile.status_review_after_process ?? false)
        setAddStaticHtml(profile.add_static_html ?? false)
        setStaticHtmlContent((profile.static_html_content ?? '').slice(0, 1000))
      }
    } catch (err) {
      console.log('Threads profile not found, using defaults', err)
    } finally {
      setIsLoadingProfile(false)
    }
  }

  async function loadPosts() {
    setIsLoadingPosts(true)
    setError('')
    try {
      const data = await threadsService.getPosts()
      setPosts(data)
      setHasLoadedPosts(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load posts')
    } finally {
      setIsLoadingPosts(false)
    }
  }

  async function handleDeletePost(postId: number) {
    if (deletingPostId !== null) return
    setDeletingPostId(postId)
    setError('')
    try {
      await threadsService.deletePost(postId)
      setPosts((prev) => prev.filter((p) => p.id !== postId))
      setSuccess('Post deleted successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete post')
    } finally {
      setDeletingPostId(null)
    }
  }

  async function handleEditPost(postId: number) {
    setError('')
    try {
      const post = await threadsService.getPost(postId)
      setPostText(post.post_text ?? '')
      setEditingPostId(postId)
      setImagePreview(post.images && post.images.length > 0 ? post.images[0] : null)
      setImageFile(null)
      setActiveTab('create')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load post for editing')
    }
  }

  async function handleCreatePost(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsCreatingPost(true)
    if (postText.length > THREADS_TEXT_LIMIT) {
      setError(`Post text cannot exceed ${THREADS_TEXT_LIMIT} characters`)
      setIsCreatingPost(false)
      return
    }
    try {
      if (editingPostId !== null) {
        await threadsService.updatePost(editingPostId, postText, imageFile || undefined)
        setSuccess('Post updated successfully')
        setEditingPostId(null)
        setPostText('')
        setImageFile(null)
        setImagePreview(null)
        loadPosts()
      } else {
        await threadsService.createPost(postText, imageFile || undefined, postTargets)
        setSuccess('Post created successfully')
        setPostText('')
        setImageFile(null)
        setImagePreview(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : (editingPostId !== null ? 'Failed to update post' : 'Failed to create post'))
    } finally {
      setIsCreatingPost(false)
    }
  }

  async function handleSaveProfile(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSavingProfile(true)
    const timeIntervals = publishScheduleType === 'by_intervals'
      ? [{ start: `${String(publishScheduleHour).padStart(2, '0')}:${String(publishScheduleMinute).padStart(2, '0')}` }]
      : []
    try {
      await threadsService.saveConfig({
        instagram_handle: instagramHandle.trim().replace(/^@/, '') || undefined,
        publish_enabled: publishEnabled,
        collect_enabled: collectEnabled,
        schedule_type: publishScheduleType,
        time_intervals: timeIntervals,
      })
      await threadsService.reloadBot()
      setSuccess('Profile settings saved successfully')
      setTimeout(loadAuthStatus, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile settings')
    } finally {
      setIsSavingProfile(false)
    }
  }

  async function handleSaveProcessing(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSavingProfile(true)
    const timeIntervals = publishScheduleType === 'by_intervals'
      ? [{ start: `${String(publishScheduleHour).padStart(2, '0')}:${String(publishScheduleMinute).padStart(2, '0')}` }]
      : []
    try {
      await threadsService.saveConfig({
        instagram_handle: instagramHandle.trim().replace(/^@/, '') || undefined,
        publish_enabled: publishEnabled,
        collect_enabled: collectEnabled,
        schedule_type: publishScheduleType,
        time_intervals: timeIntervals,
        process_enabled: processEnabled,
        processing_description: processEnabled ? processingDescription || undefined : undefined,
        remove_emojis: removeEmojis,
        remove_images: removeImages,
        clean_html: cleanHtml,
        process_services: [
          ...(processServiceWordpress ? ['wordpress'] : []),
          ...(processServiceTelegram ? ['telegram'] : []),
          ...(processServiceTwitter ? ['twitter'] : []),
          ...(processServiceVkontakte ? ['vkontakte'] : []),
          ...(processServiceThreads ? ['threads'] : []),
        ],
        status_review_after_process: statusReviewAfterProcess,
        add_static_html: addStaticHtml,
        static_html_content: addStaticHtml ? (staticHtmlContent || undefined)?.slice(0, 1000) : undefined,
      })
      await threadsService.reloadBot()
      setSuccess('Processing settings saved successfully')
      setTimeout(loadAuthStatus, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save processing settings')
    } finally {
      setIsSavingProfile(false)
    }
  }

  function handleImageChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) {
      setImageFile(file)
      const reader = new FileReader()
      reader.onloadend = () => setImagePreview(reader.result as string)
      reader.readAsDataURL(file)
    }
  }

  function removeImage() {
    setImageFile(null)
    setImagePreview(null)
  }

  async function handleConnectThreads() {
    setError('')
    try {
      const { url } = await threadsService.getAuthUrl()
      window.location.href = url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get OAuth URL')
    }
  }

  async function handleSaveAuthIdentity(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSavingAuthHandle(true)
    const timeIntervals = publishScheduleType === 'by_intervals'
      ? [{ start: `${String(publishScheduleHour).padStart(2, '0')}:${String(publishScheduleMinute).padStart(2, '0')}` }]
      : []
    const raw = instagramHandle.trim().replace(/^@/, '')
    try {
      await threadsService.saveConfig({
        instagram_handle: raw || undefined,
        publish_enabled: publishEnabled,
        collect_enabled: collectEnabled,
        schedule_type: publishScheduleType,
        time_intervals: timeIntervals,
        process_enabled: processEnabled,
        processing_description: processEnabled ? processingDescription || undefined : undefined,
        remove_emojis: removeEmojis,
        remove_images: removeImages,
        clean_html: cleanHtml,
        process_services: [
          ...(processServiceWordpress ? ['wordpress'] : []),
          ...(processServiceTelegram ? ['telegram'] : []),
          ...(processServiceTwitter ? ['twitter'] : []),
          ...(processServiceVkontakte ? ['vkontakte'] : []),
          ...(processServiceThreads ? ['threads'] : []),
        ],
        status_review_after_process: statusReviewAfterProcess,
        add_static_html: addStaticHtml,
        static_html_content: addStaticHtml ? (staticHtmlContent || undefined)?.slice(0, 1000) : undefined,
      })
      await threadsService.reloadBot()
      setSuccess('Имя пользователя сохранено')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить')
    } finally {
      setIsSavingAuthHandle(false)
    }
  }

  async function handleVerifyThreadsAuth() {
    if (!user?.id) return
    setError('')
    setVerifyResult(null)
    setIsVerifyingAuth(true)
    try {
      const result = await threadsService.verifyAuth(user.id)
      setVerifyResult(result)
      if (result.persisted_threads_user_id) {
        await loadAuthStatus()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Проверка не удалась')
    } finally {
      setIsVerifyingAuth(false)
    }
  }

  const connectedEffective = authStatus?.connected_effective ?? authStatus?.connected
  const showAuthBlock = authStatus != null && !connectedEffective

  async function handleSeleniumAttempt(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSeleniumAttemptResult(null)
    const email = seleniumEmail.trim()
    if (!email || !seleniumPassword) {
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
      <PageHeader title="Threads Integration" description="Manage your Threads posts and settings" />

      {error && <Alert variant="error" className="animate-slide-down">{error}</Alert>}
      {success && <Alert variant="success" className="animate-slide-down">{success}</Alert>}

      <div className="flex border-b border-[var(--border-color)]">
        {(['create', 'posts', 'profile', 'processing', 'auth'] as const).map((tab) => (
          <button
            key={tab}
            className={`px-6 py-3 text-sm font-medium transition-all relative flex items-center gap-1.5 ${
              activeTab === tab
                ? tab === 'auth' ? 'text-amber-400' : 'text-primary-400'
                : showAuthBlock && tab === 'auth'
                  ? 'text-amber-400 animate-pulse'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
            onClick={() => {
              if (tab === 'create') {
                setEditingPostId(null)
                setPostText('')
                setImageFile(null)
                setImagePreview(null)
              }
              setActiveTab(tab)
            }}
          >
            {tab === 'create' && 'Create Post'}
            {tab === 'posts' && 'Posts'}
            {tab === 'profile' && 'Profile Settings'}
            {tab === 'processing' && 'Обработка'}
            {tab === 'auth' && (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                Авторизация
                {showAuthBlock && <span className="inline-block w-2 h-2 bg-amber-400 rounded-full" />}
              </>
            )}
            {activeTab === tab && (
              <div className={`absolute bottom-0 left-0 right-0 h-0.5 ${tab === 'auth' ? 'bg-amber-500' : 'bg-primary-500'}`} />
            )}
          </button>
        ))}
      </div>

      {activeTab === 'auth' && (
        <Card className="animate-slide-up border-amber-500/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-400">Threads авторизация</CardTitle>
            <CardDescription>{authStatus?.message ?? 'Проверка статуса...'}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <form onSubmit={handleSaveAuthIdentity} className="space-y-4 p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
              <p className="text-sm text-[var(--text-muted)]">
                Укажите имя пользователя Instagram / Threads (без пароля): оно сохраняется в профиле для подписи.
                Доступ к API Meta выдаётся только через кнопку «Connect with Threads» (OAuth).
              </p>
              <div>
                <label htmlFor="threads-instagram-handle" className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                  Имя пользователя (@username)
                </label>
                <Input
                  id="threads-instagram-handle"
                  type="text"
                  autoComplete="username"
                  placeholder="например: mybrand"
                  value={instagramHandle}
                  onChange={(e) => setInstagramHandle(e.target.value)}
                  className="max-w-md"
                />
              </div>
              <Button type="submit" isLoading={isSavingAuthHandle} variant="secondary" size="sm">
                Сохранить имя пользователя
              </Button>
            </form>

            <div className="flex flex-wrap items-center gap-3 p-3 rounded-lg bg-[var(--bg-tertiary)]">
              <div
                className={`w-3 h-3 rounded-full shrink-0 ${
                  connectedEffective ? 'bg-green-400' : 'bg-amber-400 animate-pulse'
                }`}
              />
              <div className="text-sm text-[var(--text-secondary)] min-w-0 flex-1">
                <div>
                  {connectedEffective
                    ? 'Токен в базе, срок по локальному времени не истёк'
                    : authStatus?.connected
                      ? 'Токен сохранён, но помечен как истекший по времени — проверьте у Meta или переподключитесь'
                      : 'Не подключено'}
                </div>
                {authStatus?.expires_at && (
                  <div className="text-xs text-[var(--text-muted)] mt-1">
                    Истекает (UTC): {new Date(authStatus.expires_at).toLocaleString()}
                  </div>
                )}
                {authStatus?.threads_user_id && (
                  <div className="text-xs text-[var(--text-muted)] mt-0.5">
                    Threads user id: {authStatus.threads_user_id}
                  </div>
                )}
              </div>
              <div className="flex flex-wrap gap-2 ml-auto">
                <Button variant="ghost" size="sm" type="button" onClick={() => { void loadAuthStatus() }}>
                  Обновить статус
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  type="button"
                  isLoading={isVerifyingAuth}
                  onClick={() => { void handleVerifyThreadsAuth() }}
                >
                  Проверить у Meta
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
                <p className="font-medium">{verifyResult.valid ? 'Проверка пройдена' : 'Проверка не пройдена'}</p>
                <p className="mt-1 text-[var(--text-secondary)]">{verifyResult.message}</p>
                {verifyResult.graph_user_id && (
                  <p className="text-xs mt-2 text-[var(--text-muted)]">Graph user id: {verifyResult.graph_user_id}</p>
                )}
                {verifyResult.persisted_threads_user_id && (
                  <p className="text-xs mt-1 text-[var(--text-muted)]">Threads user id записан в профиль из ответа Meta.</p>
                )}

                {(verifyResult.scopes && verifyResult.scopes.length > 0) && (
                  <div className="mt-4 text-left">
                    <p className="text-xs font-medium text-[var(--text-secondary)] mb-2">Scopes (debug_token)</p>
                    <ul className="flex flex-wrap gap-1.5">
                      {verifyResult.scopes.map((s) => (
                        <li
                          key={s}
                          className="text-xs px-2 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--text-primary)]"
                        >
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {verifyResult.permissions_error && (
                  <p className="text-xs mt-3 text-amber-300/90">
                    Разрешения не загружены: {verifyResult.permissions_error}
                  </p>
                )}

                {verifyResult.permissions && verifyResult.permissions.length > 0 && (
                  <div className="mt-4 text-left overflow-x-auto">
                    <p className="text-xs font-medium text-[var(--text-secondary)] mb-2">
                      Подписки приложения (OAuth permissions)
                    </p>
                    <table className="w-full text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-[var(--border-color)] text-[var(--text-muted)]">
                          <th className="text-left py-1.5 pr-3 font-medium">Разрешение</th>
                          <th className="text-left py-1.5 font-medium">Статус</th>
                        </tr>
                      </thead>
                      <tbody>
                        {verifyResult.permissions.map((row) => (
                          <tr key={`${row.permission}-${row.status}`} className="border-b border-[var(--border-color)]/60 last:border-0">
                            <td className="py-1.5 pr-3 font-mono text-[var(--text-primary)]">{row.permission}</td>
                            <td className="py-1.5">
                              <span
                                className={
                                  row.status === 'granted'
                                    ? 'text-green-400'
                                    : 'text-[var(--text-muted)]'
                                }
                              >
                                {row.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {!connectedEffective && (
              <div className="p-4 rounded-lg border border-amber-500/30 bg-amber-500/5">
                <p className="text-sm text-[var(--text-muted)] mb-4">
                  Подключите аккаунт Threads через Meta для публикации постов.
                </p>
                <Button onClick={handleConnectThreads}>Connect with Threads</Button>
              </div>
            )}
            {connectedEffective && (
              <div className="p-4 rounded-lg border border-green-500/30 bg-green-500/5">
                <p className="text-sm text-green-400">OAuth-токен сохранён; при сбоях публикации нажмите «Проверить у Meta».</p>
              </div>
            )}

            <div className="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] space-y-3">
              <CardTitle className="text-base text-[var(--text-primary)]">Резервный диагностический вход (Selenium)</CardTitle>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Если OAuth не срабатывает, можно проверить веб-вход Meta в headless-браузере на сервере. Это не выдаёт Graph API
                токен и не включает публикацию через API — только диагностика. Возможны блокировки со стороны Meta (ToS).
                На сервере должно быть включено: ENABLE_THREADS_SELENIUM_FALLBACK=true.
              </p>
              <form onSubmit={(ev) => { void handleSeleniumAttempt(ev) }} className="space-y-3">
                <div className="grid gap-3 sm:grid-cols-2 max-w-2xl">
                  <div>
                    <label htmlFor="threads-selenium-email" className="text-xs font-medium text-[var(--text-secondary)] block mb-1">
                      Email или телефон Meta
                    </label>
                    <Input
                      id="threads-selenium-email"
                      type="text"
                      autoComplete="username"
                      value={seleniumEmail}
                      onChange={(e) => setSeleniumEmail(e.target.value)}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label htmlFor="threads-selenium-pass" className="text-xs font-medium text-[var(--text-secondary)] block mb-1">
                      Пароль (не сохраняется)
                    </label>
                    <Input
                      id="threads-selenium-pass"
                      type="password"
                      autoComplete="current-password"
                      value={seleniumPassword}
                      onChange={(e) => setSeleniumPassword(e.target.value)}
                      className="w-full"
                    />
                  </div>
                </div>
                <Button type="submit" variant="secondary" size="sm" isLoading={isSeleniumLoading}>
                  Запустить проверку в браузере
                </Button>
              </form>
              {seleniumAttemptResult && (
                <div className="text-sm rounded-md bg-[var(--bg-tertiary)] p-3 space-y-1">
                  <p className="font-medium text-[var(--text-primary)]">Статус: {seleniumAttemptResult.status}</p>
                  <p className="text-[var(--text-secondary)]">{seleniumAttemptResult.message}</p>
                  {seleniumAttemptResult.diagnostic_image_data_url && (
                    <div className="mt-2">
                      <img
                        alt="Диагностика Selenium"
                        src={seleniumAttemptResult.diagnostic_image_data_url}
                        className="max-w-full rounded border border-[var(--border-color)]"
                      />
                    </div>
                  )}
                  {seleniumAttemptResult.diagnostic_s3_key && (
                    <p className="text-xs font-mono text-amber-300/90 mt-2 break-all">
                      Диагностика в S3: {seleniumAttemptResult.diagnostic_s3_key}
                    </p>
                  )}
                  {seleniumAttemptResult.disclaimer && (
                    <p className="text-xs text-[var(--text-muted)] mt-2">{seleniumAttemptResult.disclaimer}</p>
                  )}
                </div>
              )}
              {seleniumLastSession && (
                <div className="text-xs text-[var(--text-muted)] border-t border-[var(--border-color)] pt-3">
                  <p className="font-medium text-[var(--text-secondary)] mb-1">Последняя сессия в журнале</p>
                  <p>#{seleniumLastSession.id} — {seleniumLastSession.status}</p>
                  {seleniumLastSession.detail_message && <p className="mt-0.5">{seleniumLastSession.detail_message}</p>}
                  {seleniumLastSession.updated_at && (
                    <p className="mt-1">{new Date(seleniumLastSession.updated_at).toLocaleString()}</p>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'create' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle>{editingPostId !== null ? 'Edit Threads Post' : 'Create Threads Post'}</CardTitle>
            <CardDescription>Max {THREADS_TEXT_LIMIT} characters</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreatePost} className="space-y-6">
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">Post Text</label>
                <textarea
                  value={postText}
                  onChange={(e) => setPostText(e.target.value)}
                  maxLength={THREADS_TEXT_LIMIT}
                  rows={6}
                  className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                  placeholder="Enter your post text..."
                  required
                />
                <p className="text-xs text-[var(--text-muted)] mt-2">{postText.length} / {THREADS_TEXT_LIMIT}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">Image (optional)</label>
                {imagePreview ? (
                  <div className="relative">
                    <img src={imagePreview} alt="Preview" className="max-w-full h-auto rounded-xl border border-[var(--border-color)]" />
                    <Button type="button" variant="ghost" size="sm" onClick={removeImage} className="absolute top-2 right-2 text-red-400 hover:text-red-300">×</Button>
                  </div>
                ) : (
                  <div className="border-2 border-dashed border-[var(--border-color)] rounded-xl p-6 text-center">
                    <input type="file" accept="image/*" onChange={handleImageChange} className="hidden" id="threads-image-upload" />
                    <label htmlFor="threads-image-upload" className="cursor-pointer">Click to upload image</label>
                  </div>
                )}
              </div>
              {editingPostId === null && (
                <TargetSocialNetworksWidget value={postTargets} onChange={setPostTargets} />
              )}
              <CardFooter className="px-0">
                <Button type="submit" isLoading={isCreatingPost} className="w-full sm:w-auto">
                  {editingPostId !== null ? 'Update Post' : 'Create Post'}
                </Button>
              </CardFooter>
            </form>
          </CardContent>
        </Card>
      )}

      {activeTab === 'posts' && (
        <Card className="animate-slide-up">
          <CardHeader className="flex flex-row items-center justify-between gap-2">
            <div>
              <CardTitle>Posts</CardTitle>
              <CardDescription>Your Threads posts</CardDescription>
            </div>
            <Button type="button" variant="secondary" size="sm" onClick={loadPosts} isLoading={isLoadingPosts}>Refresh</Button>
          </CardHeader>
          <CardContent>
            {isLoadingPosts && posts.length === 0 && (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <SkeletonCard key={i} />
                ))}
              </div>
            )}
            {!isLoadingPosts && posts.length === 0 && hasLoadedPosts && (
              <EmptyState title="No posts found" description="You have not created any posts yet." />
            )}
            {!isLoadingPosts && posts.length > 0 && (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                      <th className="py-2 pr-4 font-medium">Text</th>
                      <th className="py-2 pr-4 font-medium">Status</th>
                      <th className="py-2 pr-4 font-medium">Created</th>
                      <th className="py-2 pr-4 font-medium w-24 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {posts.map((post, index) => (
                      <tr key={post.id ?? index} className="border-b border-[var(--border-color)] last:border-0">
                        <td className="py-2 pr-4 text-[var(--text-primary)]"><div className="max-w-md truncate">{post.post_text}</div></td>
                        <td className="py-2 pr-4"><span className="inline-flex items-center rounded-full bg-[var(--bg-secondary)] px-2 py-0.5 text-xs font-medium">{post.status}</span></td>
                        <td className="py-2 pr-4 text-[var(--text-secondary)]">{new Date(post.created_at).toLocaleDateString()}</td>
                        <td className="py-2 pr-4 text-right">
                          <button type="button" onClick={() => post.id != null && handleEditPost(post.id)} disabled={post.id == null} className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-primary-400" title="Edit">✎</button>
                          <button type="button" onClick={() => post.id != null && handleDeletePost(post.id)} disabled={post.id == null || deletingPostId === post.id} className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-red-400" title="Delete">🗑</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 'profile' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle>Profile Settings</CardTitle>
            <CardDescription>Configure Threads publishing and schedule</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingProfile ? (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading profile...</div>
            ) : (
              <form onSubmit={handleSaveProfile} className="space-y-6">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" checked={publishEnabled} onChange={(e) => setPublishEnabled(e.target.checked)} className="sr-only peer" />
                  <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                  <span className="text-[var(--text-primary)]">Enable publishing</span>
                </label>
                {publishEnabled && (
                  <div className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-4">
                    <p className="text-sm text-[var(--text-muted)]">Connect your Threads account in the Auth tab.</p>
                    <div>
                      <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">Publish Schedule</label>
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input type="radio" name="threadsSchedule" value="on_new_messages" checked={publishScheduleType === 'on_new_messages'} onChange={() => setPublishScheduleType('on_new_messages')} className="w-4 h-4 text-primary-500" />
                        <span className="text-[var(--text-primary)]">When new messages are checked</span>
                      </label>
                      <label className="flex items-center gap-3 cursor-pointer mt-2">
                        <input type="radio" name="threadsSchedule" value="by_intervals" checked={publishScheduleType === 'by_intervals'} onChange={() => setPublishScheduleType('by_intervals')} className="w-4 h-4 text-primary-500" />
                        <span className="text-[var(--text-primary)]">By time intervals</span>
                      </label>
                      {publishScheduleType === 'by_intervals' && (
                        <div className="flex flex-wrap gap-4 mt-4">
                          <div>
                            <label className="text-sm font-medium text-[var(--text-secondary)] block mb-1">Hour</label>
                            <select value={publishScheduleHour} onChange={(e) => setPublishScheduleHour(Number(e.target.value))} className="w-full px-4 py-2.5 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)]">
                              {Array.from({ length: 24 }, (_, i) => <option key={i} value={i}>{String(i).padStart(2, '0')}</option>)}
                            </select>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-[var(--text-secondary)] block mb-1">Minutes</label>
                            <select value={publishScheduleMinute} onChange={(e) => setPublishScheduleMinute(Number(e.target.value) as ScheduleMinute)} className="w-full px-4 py-2.5 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)]">
                              {SCHEDULE_MINUTES.map((m) => <option key={m} value={m}>{String(m).padStart(2, '0')}</option>)}
                            </select>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                <CardFooter className="px-0">
                  <Button type="submit" isLoading={isSavingProfile}>Save Profile Settings</Button>
                </CardFooter>
              </form>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 'processing' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle>Обработка</CardTitle>
            <CardDescription>Настройки обработки постов перед публикацией</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingProfile ? (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading profile...</div>
            ) : (
              <form onSubmit={handleSaveProcessing} className="space-y-6">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" checked={processEnabled} onChange={(e) => setProcessEnabled(e.target.checked)} className="sr-only peer" />
                  <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                  <span className="text-[var(--text-primary)]">Обрабатывать перед публикацией</span>
                </label>
                {processEnabled && (
                  <textarea value={processingDescription} onChange={(e) => setProcessingDescription(e.target.value)} rows={4} className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)]" placeholder="Описание обработки..." />
                )}
                {['removeEmojis', 'removeImages', 'cleanHtml'].map((key, i) => {
                  const [val, setVal] = key === 'removeEmojis' ? [removeEmojis, setRemoveEmojis] : key === 'removeImages' ? [removeImages, setRemoveImages] : [cleanHtml, setCleanHtml]
                  const label = key === 'removeEmojis' ? 'Удалить смайлики/эмодзи' : key === 'removeImages' ? 'Удалить картинки' : 'Очистить HTML'
                  return (
                    <label key={key} className="flex items-center gap-3 cursor-pointer">
                      <input type="checkbox" checked={val} onChange={(e) => setVal(e.target.checked)} className="sr-only peer" />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                      <span className="text-[var(--text-primary)]">{label}</span>
                    </label>
                  )
                })}
                <div className="space-y-3">
                  <span className="text-sm font-medium text-[var(--text-secondary)] block">Для каких сервисов</span>
                  <div className="flex flex-wrap gap-4">
                    {[
                      ['wordpress', processServiceWordpress, setProcessServiceWordpress],
                      ['telegram', processServiceTelegram, setProcessServiceTelegram],
                      ['twitter', processServiceTwitter, setProcessServiceTwitter],
                      ['vkontakte', processServiceVkontakte, setProcessServiceVkontakte],
                      ['threads', processServiceThreads, setProcessServiceThreads],
                    ].map(([name, checked, setChecked]) => (
                      <label key={String(name)} className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={checked} onChange={(e) => setChecked(e.target.checked)} className="w-4 h-4 text-primary-500 rounded" />
                        <span className="text-[var(--text-primary)]">{String(name)}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" checked={statusReviewAfterProcess} onChange={(e) => setStatusReviewAfterProcess(e.target.checked)} className="sr-only peer" />
                  <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                  <span className="text-[var(--text-primary)]">Перевести пост в статус review после обработки</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" checked={addStaticHtml} onChange={(e) => setAddStaticHtml(e.target.checked)} className="sr-only peer" />
                  <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                  <span className="text-[var(--text-primary)]">Добавлять статичный HTML</span>
                </label>
                {addStaticHtml && (
                  <textarea value={staticHtmlContent} onChange={(e) => setStaticHtmlContent(e.target.value.slice(0, 1000))} rows={4} maxLength={1000} className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)]" placeholder="Статичный HTML (до 1000 символов)" />
                )}
                <CardFooter className="px-0">
                  <Button type="submit" isLoading={isSavingProfile}>Сохранить настройки обработки</Button>
                </CardFooter>
              </form>
            )}
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
