import { useState, FormEvent, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import {
  createDefaultTargets,
  EMPTY_SELECTED_BRAND_CHANNELS,
  type TargetSocialNetworks,
  type SelectedBrandChannels,
} from '@/components/target-social-networks'
import { dzenService } from '@/services/dzen-service'
import { getErrorMessage } from '@/services/api-client'
import { formatDateTime } from '@/utils/date'
import { useAuth } from '@/contexts/auth-context'
import { canManagePlatformAuth } from '@/types/smm'
import type {
  DzenProfile,
  DzenPostListItem,
  DzenCollectSource,
  ScheduleType,
  DzenSubscriptionItem,
  DzenVerifyResponse,
} from '@/types/dzen'

function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

interface DynamicField {
  id: string
  value: string
}

const DZEN_MAX_LENGTH = 1500
const DZEN_AUTH_DIAG_STORAGE_KEY = 'dzen_auth_diag_url'

function readStoredDiagUrl(): string | null {
  try {
    return sessionStorage.getItem(DZEN_AUTH_DIAG_STORAGE_KEY)
  } catch {
    return null
  }
}

function writeStoredDiagUrl(url: string | null): void {
  try {
    if (url && !url.startsWith('data:')) {
      sessionStorage.setItem(DZEN_AUTH_DIAG_STORAGE_KEY, url)
    } else {
      sessionStorage.removeItem(DZEN_AUTH_DIAG_STORAGE_KEY)
    }
  } catch {
    /* ignore quota / private mode */
  }
}

function isTimeoutError(err: unknown): boolean {
  const text = `${axios.isAxiosError(err) ? err.code || '' : ''} ${getErrorMessage(err)}`.toLowerCase()
  return (
    (axios.isAxiosError(err) && err.code === 'ECONNABORTED') ||
    text.includes('timeout') ||
    text.includes('timed out') ||
    text.includes('таймаут')
  )
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export function DzenPage() {
  const { user } = useAuth()
  const hasTeam = Boolean(user?.group_id || user?.role_in_group)
  const canAuth = canManagePlatformAuth(user?.role_in_group, hasTeam)
  const [activeTab, setActiveTab] = useState<'create' | 'posts' | 'profile' | 'auth'>('posts')

  const [publishEnabled, setPublishEnabled] = useState(false)
  const [collectEnabled, setCollectEnabled] = useState(false)
  const [scheduleType, setScheduleType] = useState<ScheduleType>('immediate')
  const [timeIntervals, setTimeIntervals] = useState<Array<{ id: string; start: string; end: string }>>([
    { id: generateId(), start: '', end: '' },
  ])
  const [rssFeedUrl, setRssFeedUrl] = useState('')
  const [channelName, setChannelName] = useState('')
  const [channelsToRead, setChannelsToRead] = useState<DynamicField[]>([{ id: generateId(), value: '' }])
  const [rssToken, setRssToken] = useState('')
  const [yandexLogin, setYandexLogin] = useState('')
  const [yandexPassword, setYandexPassword] = useState('')
  const [dzenStudioUrl, setDzenStudioUrl] = useState('')
  const [collectSource, setCollectSource] = useState<DzenCollectSource>('rss')
  const [lastAuthError, setLastAuthError] = useState<string | null>(null)

  const [postText, setPostText] = useState('')
  const [postTitle, setPostTitle] = useState('')
  const [postTargets] = useState<TargetSocialNetworks>(() =>
    createDefaultTargets('dzen')
  )
  const [selectedChannels, setSelectedChannels] = useState<SelectedBrandChannels>({
    ...EMPTY_SELECTED_BRAND_CHANNELS,
  })
  const [imageFiles, setImageFiles] = useState<FileList | null>(null)
  const [videoFiles, setVideoFiles] = useState<FileList | null>(null)
  const [editingPostId, setEditingPostId] = useState<number | null>(null)

  const [posts, setPosts] = useState<DzenPostListItem[]>([])
  const [isLoadingPosts, setIsLoadingPosts] = useState(false)
  const [hasLoadedPosts, setHasLoadedPosts] = useState(false)
  const [deletingPostId, setDeletingPostId] = useState<number | null>(null)

  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [isVerifyingAuth, setIsVerifyingAuth] = useState(false)
  const [verifySubscriptions, setVerifySubscriptions] = useState<DzenSubscriptionItem[]>([])
  const [verifyInfoMessage, setVerifyInfoMessage] = useState<string | null>(null)
  const [needPushCode, setNeedPushCode] = useState(false)
  const [pushCode, setPushCode] = useState('')
  const [verifyDiagImageUrl, setVerifyDiagImageUrl] = useState<string | null>(null)
  const [diagImageLoadError, setDiagImageLoadError] = useState(false)
  const [isRefreshingDiag, setIsRefreshingDiag] = useState(false)
  const [isLiveDiag, setIsLiveDiag] = useState(false)
  const [liveDiagFrameId, setLiveDiagFrameId] = useState(0)
  const [isCreatingPost, setIsCreatingPost] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const liveDiagActiveRef = useRef(false)
  const liveDiagGenerationRef = useRef(0)

  const loadProfile = useCallback(async () => {
    setIsLoadingProfile(true)
    setError('')
    try {
      const profile = await dzenService.getProfile()
      setLastAuthError(null)
      if (profile) {
        setLastAuthError(profile.last_auth_error ?? null)
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
        setRssFeedUrl(profile.rss_feed_url ?? '')
        setChannelName(profile.channel_name ?? '')
        const cr = profile.channels_to_read
        if (Array.isArray(cr) && cr.length > 0) {
          setChannelsToRead(cr.map((url) => ({ id: generateId(), value: String(url) })))
        }
        setRssToken(profile.rss_token ?? '')
        setYandexLogin(profile.yandex_login ?? '')
        setYandexPassword('')
        setDzenStudioUrl(profile.dzen_studio_url ?? '')
        setCollectSource((profile.collect_source as DzenCollectSource) ?? 'rss')
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
    if (activeTab === 'posts' && !hasLoadedPosts) {
      loadPosts()
    }
  }, [activeTab, hasLoadedPosts])

  useEffect(() => {
    if (activeTab === 'auth') {
      const stored = readStoredDiagUrl()
      if (stored) {
        setVerifyDiagImageUrl(stored)
        setDiagImageLoadError(false)
      }
    }
  }, [activeTab])

  useEffect(() => {
    return () => {
      liveDiagActiveRef.current = false
      liveDiagGenerationRef.current += 1
    }
  }, [])

  async function loadPosts() {
    setIsLoadingPosts(true)
    setError('')
    try {
      const data = await dzenService.getPosts()
      setPosts(data)
      setHasLoadedPosts(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load posts')
    } finally {
      setIsLoadingPosts(false)
    }
  }

  async function handleCreatePost(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsCreatingPost(true)
    if (postText.length > DZEN_MAX_LENGTH) {
      setError(`Post text cannot exceed ${DZEN_MAX_LENGTH} characters`)
      setIsCreatingPost(false)
      return
    }
    try {
      if (editingPostId !== null) {
        await dzenService.updatePost(editingPostId, { text: postText, title: postTitle || undefined })
        setSuccess('Post updated successfully')
        setEditingPostId(null)
        setPostText('')
        setPostTitle('')
        if (hasLoadedPosts) loadPosts()
      } else {
        const hasFiles = imageFiles?.length || videoFiles?.length
        if (hasFiles) {
          const formData = new FormData()
          formData.append('text', postText)
          if (postTitle) formData.append('title', postTitle)
          if (imageFiles) {
            for (let i = 0; i < imageFiles.length; i++) {
              formData.append('images', imageFiles[i])
            }
          }
          if (videoFiles) {
            for (let i = 0; i < videoFiles.length; i++) {
              formData.append('videos', videoFiles[i])
            }
          }
          await dzenService.createPostWithFiles(formData)
        } else {
          await dzenService.createPost({
            text: postText,
            title: postTitle || undefined,
            to_tg: postTargets.tg,
            to_tw: postTargets.tw,
            to_wp: postTargets.wp,
            to_vk: postTargets.vk,
            to_dzen: postTargets.dzen,
            to_threads: postTargets.threads,
            to_instagram: postTargets.instagram,
            target_channels: selectedChannels.tg,
            target_groups: selectedChannels.vk,
          })
        }
        setSuccess('Post created successfully')
        setPostText('')
        setPostTitle('')
        setImageFiles(null)
        setVideoFiles(null)
        setSelectedChannels({ ...EMPTY_SELECTED_BRAND_CHANNELS })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save post')
    } finally {
      setIsCreatingPost(false)
    }
  }

  async function handleEditPost(id: number) {
    setError('')
    try {
      const post = await dzenService.getPost(id)
      setPostText(post.post_text ?? '')
      setPostTitle(post.title ?? '')
      setEditingPostId(id)
      setActiveTab('create')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load post')
    }
  }

  async function handleDeletePost(id: number) {
    setError('')
    setDeletingPostId(id)
    try {
      await dzenService.deletePost(id)
      setSuccess('Post deleted')
      if (hasLoadedPosts) loadPosts()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete post')
    } finally {
      setDeletingPostId(null)
    }
  }

  function buildProfilePayload(): Partial<DzenProfile> {
    const timeIntervalsPayload =
      scheduleType === 'intervals'
        ? timeIntervals.filter((i) => i.start && i.end).map(({ start, end }) => ({ start, end }))
        : []
    const channelsToReadPayload = channelsToRead.map((f) => f.value.trim()).filter(Boolean)
    const payload: Partial<DzenProfile> = {
      publish_enabled: publishEnabled,
      collect_enabled: collectEnabled,
      schedule_type: scheduleType,
      time_intervals: timeIntervalsPayload,
      rss_feed_url: rssFeedUrl || undefined,
      channel_name: channelName || undefined,
      channels_to_read: channelsToReadPayload,
      rss_token: rssToken || undefined,
      yandex_login: yandexLogin || undefined,
      dzen_studio_url: dzenStudioUrl || undefined,
      collect_source: collectSource,
    }
    if (yandexPassword.length > 0) {
      payload.yandex_password = yandexPassword
    }
    return payload
  }

  async function handleSaveProfile(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSavingProfile(true)
    try {
      await dzenService.saveProfile(buildProfilePayload())
      setSuccess('Profile settings saved successfully')
      await loadProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile settings')
    } finally {
      setIsSavingProfile(false)
    }
  }

  async function handleSaveCredentials(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setVerifyInfoMessage(null)
    setVerifySubscriptions([])
    setIsSavingProfile(true)
    try {
      await dzenService.saveProfile(buildProfilePayload())
      setSuccess('Учётные данные и остальные настройки профиля сохранены')
      await loadProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить профиль')
    } finally {
      setIsSavingProfile(false)
    }
  }

  function setDiagFromResponse(url: string | null | undefined, clearOnSuccess: boolean) {
    if (url) {
      writeStoredDiagUrl(url)
      setVerifyDiagImageUrl(url)
      setDiagImageLoadError(false)
      setLiveDiagFrameId((n) => n + 1)
      return
    }
    if (clearOnSuccess) {
      writeStoredDiagUrl(null)
      setVerifyDiagImageUrl(null)
      setDiagImageLoadError(false)
    }
  }

  function stopLiveDiagStream(): void {
    liveDiagActiveRef.current = false
    liveDiagGenerationRef.current += 1
    setIsLiveDiag(false)
  }

  function startLiveDiagStream(): void {
    const generation = liveDiagGenerationRef.current + 1
    liveDiagGenerationRef.current = generation
    liveDiagActiveRef.current = true
    setIsLiveDiag(true)

    void (async () => {
      while (liveDiagActiveRef.current && liveDiagGenerationRef.current === generation) {
        try {
          const diag = await dzenService.fetchVerifyPendingDiag()
          if (!liveDiagActiveRef.current || liveDiagGenerationRef.current !== generation) {
            break
          }
          if (diag.need_push_code) {
            setNeedPushCode(true)
            setVerifyInfoMessage(diag.message ?? 'Введите код из пуш-уведомления.')
          }
          if (diag.diag_image_url) {
            setDiagFromResponse(diag.diag_image_url, false)
          }
        } catch {
          /* keep polling every 3s */
        }
        await sleep(3000)
      }
      if (liveDiagGenerationRef.current === generation) {
        setIsLiveDiag(false)
      }
    })()
  }

  async function refreshPendingDiagScreenshot(pollMs = 0): Promise<boolean> {
    setIsRefreshingDiag(true)
    const deadline = Date.now() + pollMs
    let lastError: string | null = null
    let first = true
    let gotImage = false
    try {
      while (first || Date.now() < deadline) {
        if (!first) {
          await sleep(3000)
        }
        first = false
        try {
          const diag = await dzenService.fetchVerifyPendingDiag()
          if (diag.need_push_code) {
            setNeedPushCode(true)
            setVerifyInfoMessage(diag.message ?? 'Введите код из пуш-уведомления.')
          }
          if (diag.diag_image_url) {
            setDiagFromResponse(diag.diag_image_url, false)
            gotImage = true
            if (pollMs <= 0) {
              return true
            }
          } else if (diag.error) {
            lastError = diag.error
          }
        } catch (err) {
          lastError = getErrorMessage(err)
        }
        if (pollMs <= 0) {
          break
        }
      }
      if (!gotImage && lastError) {
        setError((prev) => {
          if (!prev) return lastError as string
          if (prev.includes(lastError as string)) return prev
          return `${prev} ${lastError}`
        })
      }
      return gotImage
    } finally {
      setIsRefreshingDiag(false)
    }
  }

  function applyVerifyResponse(res: DzenVerifyResponse) {
    if (res.diag_image_url) {
      setDiagFromResponse(res.diag_image_url, false)
    } else if (res.ok) {
      setDiagFromResponse(null, true)
    }
    if (res.ok) {
      setVerifySubscriptions(res.subscriptions ?? [])
      setVerifyInfoMessage(res.message ?? null)
      if (res.subscriptions?.length) {
        setSuccess('Авторизация подтверждена, список подписок загружен.')
      } else if (res.message) {
        setSuccess('Вход выполнен.')
      } else {
        setSuccess('Авторизация подтверждена.')
      }
    } else {
      setVerifySubscriptions(res.subscriptions ?? [])
      setError(res.error ?? 'Не удалось проверить авторизацию')
    }
  }

  async function handleVerifyAuth() {
    setError('')
    setSuccess('')
    setVerifyInfoMessage(null)
    setNeedPushCode(false)
    setPushCode('')
    setVerifySubscriptions([])
    setIsVerifyingAuth(true)
    startLiveDiagStream()
    try {
      const res = await dzenService.verifyYandexStart()
      await loadProfile()
      if (res.ok && res.need_push_code) {
        setNeedPushCode(true)
        setVerifyInfoMessage(res.message ?? 'Введите код из пуш-уведомления.')
        setDiagFromResponse(res.diag_image_url, false)
        // live-стрим продолжает показывать экран пуш-кода каждые 3 с
        return
      }
      stopLiveDiagStream()
      applyVerifyResponse(res)
    } catch (err) {
      setVerifySubscriptions([])
      if (isTimeoutError(err)) {
        setError(
          'Превышен таймаут ожидания ответа. На экране — live-снимок браузера бота (обновление каждые 3 с).'
        )
      } else {
        setError(getErrorMessage(err) || 'Ошибка проверки авторизации')
        // ещё немного крутим live, затем останавливаем
        await sleep(12_000)
        stopLiveDiagStream()
      }
    } finally {
      setIsVerifyingAuth(false)
    }
  }

  async function handlePushCodeSubmit() {
    const code = pushCode.trim()
    if (!code) {
      setError('Введите код из пуш-уведомления.')
      return
    }
    setError('')
    setSuccess('')
    setIsVerifyingAuth(true)
    if (!liveDiagActiveRef.current) {
      startLiveDiagStream()
    }
    try {
      const res = await dzenService.verifyYandexPushCode(code)
      await loadProfile()
      if (res.ok) {
        setNeedPushCode(false)
        setPushCode('')
        stopLiveDiagStream()
        applyVerifyResponse(res)
        return
      }
      if (res.need_push_code) {
        setNeedPushCode(true)
        setDiagFromResponse(res.diag_image_url, false)
        setError(res.error ?? 'Повторите ввод кода.')
        return
      }
      setNeedPushCode(false)
      stopLiveDiagStream()
      applyVerifyResponse(res)
    } catch (err) {
      if (isTimeoutError(err)) {
        setError(
          'Превышен таймаут после отправки кода. Live-скрин бота продолжает обновляться каждые 3 с.'
        )
      } else {
        setError(getErrorMessage(err) || 'Ошибка отправки кода')
      }
    } finally {
      setIsVerifyingAuth(false)
    }
  }

  function addChannelToRead() {
    setChannelsToRead((prev) => [...prev, { id: generateId(), value: '' }])
  }
  function removeChannelToRead(id: string) {
    if (channelsToRead.length > 1) setChannelsToRead((prev) => prev.filter((f) => f.id !== id))
  }
  function updateChannelToRead(id: string, value: string) {
    setChannelsToRead((prev) => prev.map((f) => (f.id === id ? { ...f, value } : f)))
  }

  function addTimeInterval() {
    if (timeIntervals.length < 5) {
      setTimeIntervals((prev) => [...prev, { id: generateId(), start: '', end: '' }])
    }
  }
  function removeTimeInterval(id: string) {
    if (timeIntervals.length > 1) {
      setTimeIntervals((prev) => prev.filter((i) => i.id !== id))
    }
  }
  function updateTimeInterval(id: string, field: 'start' | 'end', value: string) {
    setTimeIntervals((prev) =>
      prev.map((i) => (i.id === id ? { ...i, [field]: value } : i))
    )
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="Яндекс Дзен"
        description="RSS, Selenium-бот (публикация и своя лента), посты с картинками и видео"
      />
      <p className="mb-4 text-sm flex flex-wrap gap-4">
        <Link to="/posts" className="text-primary-400 hover:underline">
          Создать пост → /posts
        </Link>
      </p>

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
        {[
          { key: 'posts' as const, label: 'Посты' },
          { key: 'profile' as const, label: 'Настройки' },
          { key: 'auth' as const, label: 'Авторизация' },
        ]
          .filter(({ key }) => key !== 'auth' || canAuth)
          .map(({ key, label }) => (
          <button
            key={key}
            className={`px-6 py-3 text-sm font-medium transition-all relative ${
              activeTab === key ? 'text-primary-400' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
            onClick={() => setActiveTab(key)}
          >
            {label}
            {activeTab === key && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />}
          </button>
        ))}
      </div>

      {activeTab === 'create' && editingPostId === null && (
        <Alert className="mt-4">
          Создание постов — на странице{' '}
          <Link to="/posts" className="text-primary-400 hover:underline">
            Posts
          </Link>
        </Alert>
      )}

      {activeTab === 'create' && editingPostId !== null && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">Редактировать пост</CardTitle>
            <CardDescription>До {DZEN_MAX_LENGTH} символов. Можно добавить заголовок.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreatePost} className="space-y-6">
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">Заголовок (необязательно)</label>
                <Input
                  value={postTitle}
                  onChange={(e) => setPostTitle(e.target.value.slice(0, 200))}
                  placeholder="Заголовок поста"
                  className="max-w-md"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">Текст поста</label>
                <textarea
                  value={postText}
                  onChange={(e) => setPostText(e.target.value)}
                  maxLength={DZEN_MAX_LENGTH}
                  rows={8}
                  className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                  placeholder="Введите текст..."
                />
                <p className="text-xs text-[var(--text-muted)] mt-2">
                  {postText.length} / {DZEN_MAX_LENGTH} символов
                </p>
              </div>
              <CardFooter className="px-0">
                <Button type="submit" isLoading={isCreatingPost} className="w-full sm:w-auto">
                  Сохранить
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
              <CardTitle>Посты</CardTitle>
              <CardDescription>Посты Дзен (ручные и из вычитки RSS)</CardDescription>
            </div>
            <Button type="button" variant="secondary" size="sm" onClick={loadPosts} disabled={isLoadingPosts}>
              Обновить
            </Button>
          </CardHeader>
          <CardContent>
            {isLoadingPosts && posts.length === 0 && (
              <div className="text-center py-8 text-[var(--text-muted)]">Загрузка...</div>
            )}
            {!isLoadingPosts && posts.length === 0 && hasLoadedPosts && (
              <div className="text-center py-8 text-[var(--text-muted)]">Нет постов.</div>
            )}
            {!isLoadingPosts && posts.length > 0 && (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                      <th className="py-2 pr-4 font-medium">Текст / заголовок</th>
                      <th className="py-2 pr-4 font-medium">Статус</th>
                      <th className="py-2 pr-4 font-medium">Дата</th>
                      <th className="py-2 pr-4 font-medium w-24 text-right">Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {posts.map((post, index) => (
                      <tr key={post.id ?? index} className="border-b border-[var(--border-color)] last:border-0">
                        <td className="py-2 pr-4 text-[var(--text-primary)] max-w-md truncate">
                          {post.title ? `${post.title}: ` : ''}{post.post_text}
                        </td>
                        <td className="py-2 pr-4">
                          <span className="inline-flex items-center rounded-full bg-[var(--bg-secondary)] px-2 py-0.5 text-xs font-medium text-[var(--text-secondary)]">
                            {post.status}
                          </span>
                        </td>
                        <td className="py-2 pr-4 text-[var(--text-secondary)]">
                          {formatDateTime(post.created_at)}
                        </td>
                        <td className="py-2 pr-4 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              type="button"
                              onClick={() => post.id != null && handleEditPost(post.id)}
                              disabled={post.id == null}
                              className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-primary-400 hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-50"
                              title="Редактировать"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                            </button>
                            <button
                              type="button"
                              onClick={() => post.id != null && handleDeletePost(post.id)}
                              disabled={post.id == null || deletingPostId === post.id}
                              className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-red-400 hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-50"
                              title="Удалить"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
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
            <CardTitle>Настройки канала Дзен</CardTitle>
            <CardDescription>RSS, Selenium (студия), вычитка каналов, расписание. Логин Яндекса — во вкладке «Авторизация».</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingProfile ? (
              <div className="text-center py-8 text-[var(--text-muted)]">Загрузка...</div>
            ) : (
              <form onSubmit={handleSaveProfile} className="space-y-8">
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Публикация (RSS)</h3>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input type="checkbox" checked={publishEnabled} onChange={(e) => setPublishEnabled(e.target.checked)} className="sr-only peer" />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">Включить публикацию в Дзен по RSS</span>
                  </label>
                  <Input label="URL вашей RSS-ленты (для робота Дзена)" value={rssFeedUrl} onChange={(e) => setRssFeedUrl(e.target.value)} placeholder="https://..." />
                  <Input label="Название канала" value={channelName} onChange={(e) => setChannelName(e.target.value)} placeholder="Отображается в RSS" />
                  <Input label="Токен для доступа к RSS (необязательно)" type="password" value={rssToken} onChange={(e) => setRssToken(e.target.value)} placeholder="?token=..." />
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-[var(--text-secondary)] block">Расписание</label>
                    <div className="space-y-3">
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input type="radio" name="schedule" checked={scheduleType === 'immediate'} onChange={() => setScheduleType('immediate')} className="w-4 h-4 text-primary-500" />
                        <span className="text-[var(--text-primary)]">Сразу</span>
                      </label>
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input type="radio" name="schedule" checked={scheduleType === 'intervals'} onChange={() => setScheduleType('intervals')} className="w-4 h-4 text-primary-500" />
                        <span className="text-[var(--text-primary)]">По интервалам</span>
                      </label>
                    </div>
                    {scheduleType === 'intervals' && (
                      <div className="space-y-3 mt-4">
                        {timeIntervals.map((interval, idx) => (
                          <div key={interval.id} className="flex gap-3 items-end">
                            <Input label={`Начало ${idx + 1}`} type="time" value={interval.start} onChange={(e) => updateTimeInterval(interval.id, 'start', e.target.value)} className="flex-1" />
                            <Input label="Конец" type="time" value={interval.end} onChange={(e) => updateTimeInterval(interval.id, 'end', e.target.value)} className="flex-1" />
                            {timeIntervals.length > 1 && (
                              <Button type="button" variant="ghost" size="sm" onClick={() => removeTimeInterval(interval.id)} className="text-red-400 hover:text-red-300">
                                Удалить
                              </Button>
                            )}
                          </div>
                        ))}
                        {timeIntervals.length < 5 && (
                          <Button type="button" variant="secondary" size="sm" onClick={addTimeInterval}>
                            Добавить интервал
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Selenium (dzen-bot)</h3>
                  <p className="text-xs text-[var(--text-muted)]">
                    Публикация в интерфейс Дзена и сбор своей ленты из студии. Режим сбора: только RSS, только Selenium или оба.
                  </p>
                  <p className="text-sm text-[var(--text-secondary)]">
                    Логин и пароль Яндекса задаются во вкладке «Авторизация».
                  </p>
                  <Input
                    label="URL студии / списка публикаций"
                    value={dzenStudioUrl}
                    onChange={(e) => setDzenStudioUrl(e.target.value)}
                    placeholder="https://dzen.ru/profile/editor/..."
                  />
                  <div className="space-y-2">
                    <span className="text-sm font-medium text-[var(--text-secondary)] block">Источник сбора в ленту</span>
                    <div className="flex flex-wrap gap-4">
                      {(
                        [
                          ['rss', 'Только RSS (чужие ленты)'],
                          ['selenium', 'Только Selenium (своя студия)'],
                          ['both', 'RSS + Selenium'],
                        ] as const
                      ).map(([value, label]) => (
                        <label key={value} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="radio"
                            name="collect_source"
                            checked={collectSource === value}
                            onChange={() => setCollectSource(value)}
                            className="w-4 h-4 text-primary-500"
                          />
                          <span className="text-[var(--text-primary)] text-sm">{label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Вычитка каналов (RSS)</h3>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input type="checkbox" checked={collectEnabled} onChange={(e) => setCollectEnabled(e.target.checked)} className="sr-only peer" />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">Собирать посты из внешних RSS-лент</span>
                  </label>
                  {collectEnabled && (
                    <div className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-4 border border-[var(--border-color)]">
                      <p className="text-xs text-[var(--text-muted)]">Укажите URL RSS-лент каналов Дзен или других источников. Посты будут добавляться в список.</p>
                      {channelsToRead.map((field) => (
                        <div key={field.id} className="flex gap-3">
                          <Input
                            placeholder="https://example.com/feed.rss"
                            value={field.value}
                            onChange={(e) => updateChannelToRead(field.id, e.target.value)}
                            className="flex-1"
                          />
                          {channelsToRead.length > 1 && (
                            <Button type="button" variant="ghost" size="sm" onClick={() => removeChannelToRead(field.id)} className="px-3 text-red-400 hover:text-red-300">
                              Удалить
                            </Button>
                          )}
                        </div>
                      ))}
                      <Button type="button" variant="secondary" size="sm" onClick={addChannelToRead}>
                        Добавить RSS
                      </Button>
                    </div>
                  )}
                </div>

                <CardFooter className="px-0">
                  <Button type="submit" isLoading={isSavingProfile}>
                    Сохранить настройки
                  </Button>
                </CardFooter>
              </form>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 'auth' && canAuth && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle>Авторизация Яндекс</CardTitle>
            <CardDescription>
              Учётные данные для dzen-bot (Selenium). Пароль с сервера не подставляется — введите заново, чтобы сменить.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingProfile ? (
              <div className="text-center py-8 text-[var(--text-muted)]">Загрузка...</div>
            ) : (
              <div className="space-y-6">
                {lastAuthError && (
                  <Alert variant="error" className="text-sm">
                    Последняя ошибка бота: {lastAuthError}
                  </Alert>
                )}
                <form onSubmit={handleSaveCredentials} className="space-y-4">
                  <Input
                    label="Логин Яндекс"
                    value={yandexLogin}
                    onChange={(e) => setYandexLogin(e.target.value)}
                    placeholder="email или логин"
                    autoComplete="username"
                  />
                  <Input
                    label="Пароль Яндекс"
                    type="password"
                    value={yandexPassword}
                    onChange={(e) => setYandexPassword(e.target.value)}
                    placeholder="Оставьте пустым в настройках, чтобы не менять сохранённый"
                    autoComplete="current-password"
                  />
                  <div className="flex flex-wrap gap-3">
                    <Button type="submit" isLoading={isSavingProfile}>
                      Сохранить учётные данные
                    </Button>
                    <Button type="button" variant="secondary" isLoading={isVerifyingAuth} onClick={() => void handleVerifyAuth()}>
                      Проверить авторизацию
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      isLoading={isRefreshingDiag}
                      onClick={() => void refreshPendingDiagScreenshot(0)}
                    >
                      Обновить скрин
                    </Button>
                    {(isLiveDiag || needPushCode) && (
                      <Button type="button" variant="ghost" onClick={() => stopLiveDiagStream()}>
                        Остановить трансляцию
                      </Button>
                    )}
                  </div>
                </form>
                {(verifyDiagImageUrl || isRefreshingDiag || isLiveDiag || isVerifyingAuth) && (
                  <div className="space-y-2">
                    <p className="text-xs text-[var(--text-muted)]">
                      {isLiveDiag || isVerifyingAuth
                        ? 'Live: экран браузера бота (обновление каждые 3 секунды)'
                        : 'Снимок экрана для диагностики (страница в браузере бота):'}
                    </p>
                    {verifyDiagImageUrl && !diagImageLoadError ? (
                      <img
                        key={liveDiagFrameId}
                        src={verifyDiagImageUrl}
                        alt="Диагностика Selenium"
                        className="max-w-full rounded-xl border border-[var(--border-color)] max-h-96 object-contain bg-[var(--bg-secondary)]"
                        onLoad={() => setDiagImageLoadError(false)}
                        onError={() => setDiagImageLoadError(true)}
                      />
                    ) : verifyDiagImageUrl && diagImageLoadError ? (
                      <p className="text-sm text-[var(--text-secondary)]">
                        Не удалось показать скрин. Нажмите «Обновить скрин».
                      </p>
                    ) : (
                      <p className="text-sm text-[var(--text-secondary)]">Ожидаем первый кадр с бота…</p>
                    )}
                  </div>
                )}
                {needPushCode && (
                  <div className="space-y-3 p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                    <p className="text-sm text-[var(--text-primary)]">Введите код из пуш-уведомления в приложении Яндекса.</p>
                    <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
                      <div className="flex-1">
                        <Input
                          label="Код"
                          value={pushCode}
                          onChange={(e) => setPushCode(e.target.value.replace(/\s/g, ''))}
                          placeholder="Например 123456"
                          inputMode="numeric"
                          autoComplete="one-time-code"
                        />
                      </div>
                      <Button
                        type="button"
                        variant="secondary"
                        isLoading={isVerifyingAuth}
                        onClick={() => void handlePushCodeSubmit()}
                      >
                        Отправить код
                      </Button>
                    </div>
                  </div>
                )}
                {verifyInfoMessage && (
                  <Alert variant="warning" className="text-sm">
                    {verifyInfoMessage}
                  </Alert>
                )}
                {verifySubscriptions.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">Подписки (проверка)</h3>
                    <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                      <table className="min-w-full text-sm">
                        <thead>
                          <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                            <th className="py-2 px-3 font-medium">Название</th>
                            <th className="py-2 px-3 font-medium">Ссылка</th>
                          </tr>
                        </thead>
                        <tbody>
                          {verifySubscriptions.map((s, i) => (
                            <tr key={`${s.url}-${i}`} className="border-b border-[var(--border-color)] last:border-0">
                              <td className="py-2 px-3 text-[var(--text-primary)] align-top">{s.title}</td>
                              <td className="py-2 px-3 align-top">
                                <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-primary-400 hover:underline break-all">
                                  {s.url}
                                </a>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
