import { useState, FormEvent, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import {
  TargetSocialNetworksWidget,
  createDefaultTargets,
  type TargetSocialNetworks,
} from '@/components/target-social-networks'
import { TipTapEditor } from '@/components/ui/tiptap-editor'
import { apiClient } from '@/services/api-client'
import { vkontakteService } from '@/services/vkontakte-service'
import { useAuth } from '@/contexts/auth-context'
import type {
  VKontakteProfile,
  VKontaktePostListItem,
  ScheduleType,
  VKAuthStatus,
  VKSubscriptionItem,
} from '@/types/vkontakte'

function htmlToPlainText(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return (div.textContent ?? div.innerText ?? '').trim()
}

function imagePreviewUrl(url: string): string {
  if (url.startsWith('http')) return url
  const base = apiClient.defaults.baseURL ?? '/api'
  const origin = typeof window !== 'undefined' ? window.location.origin : ''
  return `${origin}${base}${url.startsWith('/') ? '' : '/'}${url}`
}

function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

interface DynamicField {
  id: string
  value: string
}

const VK_MAX_LENGTH = 15985
const AUTH_STATUS_POLL_INTERVAL_MS = 15_000

export function VKontaktePage() {
  const { user } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState<'create' | 'posts' | 'profile' | 'processing' | 'auth'>(() =>
    searchParams.get('auth') === '1' ? 'auth' : 'create'
  )
  const [authStatus, setAuthStatus] = useState<VKAuthStatus | null>(null)
  const [subscriptions, setSubscriptions] = useState<VKSubscriptionItem[]>([])
  const [subscriptionsSource, setSubscriptionsSource] = useState<string | null>(null)
  const [subscriptionsHint, setSubscriptionsHint] = useState<string | null>(null)
  const [loadingSubscriptions, setLoadingSubscriptions] = useState(false)
  const [vkSeleniumOpen, setVkSeleniumOpen] = useState(false)
  const [vkSeleniumLogin, setVkSeleniumLogin] = useState('')
  const [vkSeleniumPassword, setVkSeleniumPassword] = useState('')
  const [loadingSeleniumVerify, setLoadingSeleniumVerify] = useState(false)

  // Profile state
  const [publishEnabled, setPublishEnabled] = useState(false)
  const [collectEnabled, setCollectEnabled] = useState(false)
  const [scheduleType, setScheduleType] = useState<ScheduleType>('immediate')
  const [timeIntervals, setTimeIntervals] = useState<Array<{ id: string; start: string; end: string }>>([
    { id: generateId(), start: '', end: '' },
  ])
  const [ownerId, setOwnerId] = useState('')
  const [friendsOnly, setFriendsOnly] = useState(false)
  const [fromGroup, setFromGroup] = useState(true)
  const [message, setMessage] = useState('')
  const [attachments, setAttachments] = useState('')
  const [signed, setSigned] = useState(false)
  const [markAsAds, setMarkAsAds] = useState(false)
  const [accessToken, setAccessToken] = useState('')
  const [vkAppId, setVkAppId] = useState('')
  const [vkAppSecret, setVkAppSecret] = useState('')
  const [vkFrontendUrl, setVkFrontendUrl] = useState('http://localhost:8100')
  const [vkPublicGatewayUrl, setVkPublicGatewayUrl] = useState('http://localhost:8000')
  const [groupsToRead, setGroupsToRead] = useState<DynamicField[]>([{ id: generateId(), value: '' }])
  const [groupToPost, setGroupToPost] = useState('')
  const [processEnabled, setProcessEnabled] = useState(false)
  const [processingDescription, setProcessingDescription] = useState('')
  const [removeEmojis, setRemoveEmojis] = useState(false)
  const [removeImages, setRemoveImages] = useState(false)
  const [cleanHtml, setCleanHtml] = useState(false)
  const [processServiceWordpress, setProcessServiceWordpress] = useState(false)
  const [processServiceTelegram, setProcessServiceTelegram] = useState(false)
  const [processServiceTwitter, setProcessServiceTwitter] = useState(false)
  const [processServiceVkontakte, setProcessServiceVkontakte] = useState(false)
  const [statusReviewAfterProcess, setStatusReviewAfterProcess] = useState(false)
  const [addStaticHtml, setAddStaticHtml] = useState(false)
  const [staticHtmlContent, setStaticHtmlContent] = useState('')

  // Create post state (editor content is HTML; we send plain text to API)
  const [postContent, setPostContent] = useState('')
  const [postImages, setPostImages] = useState<string[]>([])
  const [postTargets, setPostTargets] = useState<TargetSocialNetworks>(() =>
    createDefaultTargets('vk')
  )
  const [editingPostId, setEditingPostId] = useState<number | null>(null)

  // Posts list
  const [posts, setPosts] = useState<VKontaktePostListItem[]>([])
  const [isLoadingPosts, setIsLoadingPosts] = useState(false)
  const [hasLoadedPosts, setHasLoadedPosts] = useState(false)
  const [deletingPostId, setDeletingPostId] = useState<number | null>(null)

  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [isCreatingPost, setIsCreatingPost] = useState(false)
  const [uploadingImage, setUploadingImage] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadProfile = useCallback(async () => {
    setIsLoadingProfile(true)
    setError('')
    try {
      const profile = await vkontakteService.getProfile()
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
        setOwnerId(profile.owner_id ?? '')
        setFriendsOnly(profile.friends_only ?? false)
        setFromGroup(profile.from_group ?? true)
        setMessage(profile.message ?? '')
        setAttachments(profile.attachments ?? '')
        setSigned(profile.signed ?? false)
        setMarkAsAds(profile.mark_as_ads ?? false)
        setAccessToken(profile.access_token ?? '')
        setVkAppId(profile.vk_app_id ?? '')
        setVkAppSecret(profile.vk_app_secret ?? '')
        setVkFrontendUrl(profile.vk_frontend_url?.trim() || 'http://localhost:8100')
        setVkPublicGatewayUrl(profile.vk_public_gateway_url?.trim() || 'http://localhost:8000')
        const gr = profile.groups_to_read
        if (Array.isArray(gr) && gr.length > 0) {
          setGroupsToRead(gr.map((g) => ({ id: generateId(), value: String(g) })))
        }
        setGroupToPost(profile.group_to_post ?? '')
        setProcessEnabled(profile.process_enabled ?? false)
        setProcessingDescription(profile.processing_description ?? '')
        setRemoveEmojis(profile.remove_emojis ?? false)
        setRemoveImages(profile.remove_images ?? false)
        setCleanHtml(profile.clean_html ?? false)
        const ps = profile.process_services
        if (Array.isArray(ps)) {
          setProcessServiceWordpress(ps.includes('wordpress'))
          setProcessServiceTelegram(ps.includes('telegram'))
          setProcessServiceTwitter(ps.includes('twitter'))
          setProcessServiceVkontakte(ps.includes('vkontakte'))
        }
        setStatusReviewAfterProcess(profile.status_review_after_process ?? false)
        setAddStaticHtml(profile.add_static_html ?? false)
        setStaticHtmlContent((profile.static_html_content ?? '').slice(0, 1000))
      }
    } catch (err) {
      console.error('Failed to load profile:', err)
    } finally {
      setIsLoadingProfile(false)
    }
  }, [])

  const loadAuthStatus = useCallback(async () => {
    if (!user?.id) return
    try {
      const status = await vkontakteService.getAuthStatus(user.id)
      setAuthStatus(status)
    } catch (err) {
      console.error('[VKontaktePage] Failed to load auth status:', err)
    }
  }, [user?.id])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  useEffect(() => {
    if (searchParams.get('auth') === '1') {
      setActiveTab('auth')
      searchParams.delete('auth')
      setSearchParams(searchParams, { replace: true })
    }
  }, [searchParams, setSearchParams])

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
    if (activeTab === 'posts' && !hasLoadedPosts) {
      loadPosts()
    }
  }, [activeTab, hasLoadedPosts])

  async function loadPosts() {
    setIsLoadingPosts(true)
    setError('')
    try {
      const data = await vkontakteService.getPosts()
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
    const text = htmlToPlainText(postContent)
    if (text.length > VK_MAX_LENGTH) {
      setError(`Post text cannot exceed ${VK_MAX_LENGTH} characters`)
      setIsCreatingPost(false)
      return
    }
    const imagesList = postImages.filter(Boolean)
    try {
      if (editingPostId !== null) {
        await vkontakteService.updatePost(editingPostId, {
          text,
          images: imagesList.length ? imagesList : undefined,
        })
        setSuccess('Post updated successfully')
        setEditingPostId(null)
        setPostContent('')
        setPostImages([])
        if (hasLoadedPosts) loadPosts()
      } else {
        await vkontakteService.createPost({
          text,
          to_tg: postTargets.tg,
          to_tw: postTargets.tw,
          to_wp: postTargets.wp,
          to_vk: postTargets.vk,
          to_threads: postTargets.threads,
          to_dzen: postTargets.dzen,
          to_instagram: postTargets.instagram,
          images: imagesList.length ? imagesList : undefined,
        })
        setSuccess('Post created successfully')
        setPostContent('')
        setPostImages([])
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
      const post = await vkontakteService.getPost(id)
      setPostContent(post.post_text ?? '')
      const imgs = post.images
      setPostImages(Array.isArray(imgs) && imgs.length > 0 ? [...imgs] : [])
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
      await vkontakteService.deletePost(id)
      setSuccess('Post deleted')
      if (hasLoadedPosts) loadPosts()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete post')
    } finally {
      setDeletingPostId(null)
    }
  }

  function buildProfilePayload(): Partial<VKontakteProfile> {
    const timeIntervalsPayload =
      scheduleType === 'intervals'
        ? timeIntervals.filter((i) => i.start && i.end).map(({ start, end }) => ({ start, end }))
        : []
    const groupsToReadPayload = groupsToRead
      .map((f) => f.value.trim())
      .filter(Boolean)
      .map((v) => (v.startsWith('-') ? parseInt(v, 10) : parseInt(v, 10)))
      .filter((n) => !Number.isNaN(n))
    return {
      publish_enabled: publishEnabled,
      collect_enabled: collectEnabled,
      schedule_type: scheduleType,
      time_intervals: timeIntervalsPayload,
      owner_id: ownerId || undefined,
      friends_only: friendsOnly,
      from_group: fromGroup,
      message: message || undefined,
      attachments: attachments || undefined,
      signed: signed,
      mark_as_ads: markAsAds,
      access_token: accessToken && accessToken !== '***' ? accessToken : undefined,
      vk_app_id: vkAppId.trim() || undefined,
      vk_app_secret: vkAppSecret && vkAppSecret !== '***' ? vkAppSecret : undefined,
      vk_frontend_url: vkFrontendUrl.trim() || undefined,
      vk_public_gateway_url: vkPublicGatewayUrl.trim() || undefined,
      groups_to_read: groupsToReadPayload,
      group_to_post: groupToPost || undefined,
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
      ],
      status_review_after_process: statusReviewAfterProcess,
      add_static_html: addStaticHtml,
      static_html_content: addStaticHtml ? staticHtmlContent?.slice(0, 1000) : undefined,
    }
  }

  async function persistFullVkProfile(successMessage: string) {
    setError('')
    setSuccess('')
    setIsSavingProfile(true)
    try {
      await vkontakteService.saveProfile(buildProfilePayload())
      setSuccess(successMessage)
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
    try {
      await vkontakteService.saveProfile(buildProfilePayload())
      setSuccess('Processing settings saved successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save processing settings')
    } finally {
      setIsSavingProfile(false)
    }
  }

  async function handleSaveProfile(e: FormEvent) {
    e.preventDefault()
    await persistFullVkProfile('Profile settings saved successfully')
  }

  async function loadSubscriptions() {
    setLoadingSubscriptions(true)
    setError('')
    setSubscriptionsHint(null)
    try {
      const res = await vkontakteService.getSubscriptions()
      setSubscriptions(res.subscriptions ?? [])
      setSubscriptionsSource(res.source === 'user_oauth' ? 'Пользовательский OAuth (users.getSubscriptions)' : 'Токен сообщества (groups.getById)')
      setSubscriptionsHint(res.message ?? null)
      setSuccess(res.count > 0 ? `Загружено записей: ${res.count}` : 'Запрос выполнен, список пуст.')
    } catch (err) {
      setSubscriptions([])
      setSubscriptionsSource(null)
      setVkSeleniumOpen(true)
      setError(err instanceof Error ? err.message : 'Не удалось загрузить подписки')
    } finally {
      setLoadingSubscriptions(false)
    }
  }

  async function verifySeleniumFallback() {
    setLoadingSeleniumVerify(true)
    setError('')
    setSuccess('')
    try {
      const res = await vkontakteService.verifySelenium(vkSeleniumLogin.trim(), vkSeleniumPassword)
      setVkSeleniumPassword('')
      if (!res.ok) {
        const base = res.error ?? 'Ошибка резервного входа VK (Selenium)'
        setError(
          res.diagnostic_s3_key
            ? `${base} Диагностический скриншот сохранён в S3: ${res.diagnostic_s3_key}`
            : base
        )
        return
      }
      setSubscriptions(res.subscriptions ?? [])
      setSubscriptionsSource('Selenium: веб-страница (vk-bot), не заменяет OAuth/API-токен')
      setSubscriptionsHint(res.message ?? null)
      setSuccess(
        res.subscriptions && res.subscriptions.length > 0
          ? `Selenium: загружено записей: ${res.subscriptions.length}`
          : 'Selenium: запрос выполнен, список пуст.'
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка vk-bot (Selenium)')
    } finally {
      setLoadingSeleniumVerify(false)
    }
  }

  function addGroupToRead() {
    setGroupsToRead((prev) => [...prev, { id: generateId(), value: '' }])
  }
  function removeGroupToRead(id: string) {
    if (groupsToRead.length > 1) setGroupsToRead((prev) => prev.filter((f) => f.id !== id))
  }
  function updateGroupToRead(id: string, value: string) {
    setGroupsToRead((prev) => prev.map((f) => (f.id === id ? { ...f, value } : f)))
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

  async function handleConnectVk() {
    setError('')
    try {
      const { url } = await vkontakteService.getAuthUrl()
      window.location.href = url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get OAuth URL')
    }
  }

  const showAuthBlock = authStatus != null && !authStatus.connected

  const vkOAuthRedirectUri = `${vkPublicGatewayUrl.replace(/\/$/, '')}/vk/oauth/callback`

  return (
    <PageContainer maxWidth="wide">
      <PageHeader title="VKontakte Integration" description="Configure your VKontakte account settings and post management" />

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

      {/* Tabs */}
      <div className="flex border-b border-[var(--border-color)]">
        {(
          [
            { key: 'create' as const, label: 'Create Post' },
            { key: 'posts' as const, label: 'Posts' },
            { key: 'profile' as const, label: 'Profile Settings' },
            { key: 'processing' as const, label: 'Обработка' },
          ] as const
        ).map(({ key, label }) => (
          <button
            type="button"
            key={key}
            className={`px-6 py-3 text-sm font-medium transition-all relative ${
              activeTab === key ? 'text-primary-400' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
            onClick={() => {
              if (key === 'create') {
                setEditingPostId(null)
                setPostContent('')
              }
              setActiveTab(key)
            }}
          >
            {label}
            {activeTab === key && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />}
          </button>
        ))}
        <button
          type="button"
          className={`px-6 py-3 text-sm font-medium transition-all relative flex items-center gap-1.5 ${
            activeTab === 'auth'
              ? 'text-amber-400'
              : showAuthBlock
                ? 'text-amber-400 animate-pulse'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => setActiveTab('auth')}
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          Авторизация
          {showAuthBlock && <span className="inline-block w-2 h-2 bg-amber-400 rounded-full" />}
          {activeTab === 'auth' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-500" />}
        </button>
      </div>

      {activeTab === 'auth' && (
        <Card className="animate-slide-up border-amber-500/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-400">VK авторизация</CardTitle>
            <CardDescription className="space-y-2">
              <span className="block">
                {authStatus?.message ??
                  'Пользовательский OAuth нужен для загрузки фото на стену сообщества (photos.getWallUploadServer). Токен сообщества (ниже) — для публикации от имени группы и сбора стены.'}
              </span>
              <span className="block text-xs text-[var(--text-muted)]">
                Запрашиваемые scope в Core: <code className="text-[var(--text-secondary)]">wall</code>,{' '}
                <code className="text-[var(--text-secondary)]">photos</code>,{' '}
                <code className="text-[var(--text-secondary)]">groups</code>,{' '}
                <code className="text-[var(--text-secondary)]">offline</code> (классический OAuth VK, не VK ID PKCE).
              </span>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3 p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">Приложение VK (OAuth)</h3>
              <p className="text-xs text-[var(--text-muted)]">
                Параметры из <code className="text-[var(--text-secondary)]">.env</code> перенесены сюда. Укажите данные
                приложения с{' '}
                <a href="https://dev.vk.com" target="_blank" rel="noopener noreferrer" className="text-primary-400 hover:underline">
                  dev.vk.com
                </a>
                . Redirect URI в кабинете VK должен совпадать с вычисленным ниже.
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                <Input
                  label="VK App ID (VK_APP_ID)"
                  value={vkAppId}
                  onChange={(e) => setVkAppId(e.target.value)}
                  placeholder="12345678"
                />
                <Input
                  label="VK App Secret (VK_APP_SECRET)"
                  type="password"
                  value={vkAppSecret === '***' ? '' : vkAppSecret}
                  onChange={(e) => setVkAppSecret(e.target.value)}
                  placeholder={vkAppSecret === '***' ? 'Секрет сохранён (скрыт)' : 'Защищённый ключ приложения'}
                />
                <Input
                  label="URL интерфейса (FRONTEND_URL)"
                  value={vkFrontendUrl}
                  onChange={(e) => setVkFrontendUrl(e.target.value)}
                  placeholder="http://localhost:8100"
                />
                <Input
                  label="Публичный URL gateway (VK_PUBLIC_GATEWAY_URL)"
                  value={vkPublicGatewayUrl}
                  onChange={(e) => setVkPublicGatewayUrl(e.target.value)}
                  placeholder="http://localhost:8000"
                />
              </div>
              <p className="text-xs text-[var(--text-muted)]">
                Redirect URI для VK:{' '}
                <code className="text-[var(--text-secondary)] break-all">{vkOAuthRedirectUri}</code>
              </p>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => void persistFullVkProfile('Настройки OAuth VK сохранены')}
                isLoading={isSavingProfile}
              >
                Сохранить настройки OAuth
              </Button>
            </div>

            <div className="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-tertiary)]">
              <div
                className={`w-3 h-3 rounded-full ${
                  authStatus?.connected ? 'bg-green-400' : 'bg-amber-400 animate-pulse'
                }`}
              />
              <span className="text-sm text-[var(--text-secondary)]">
                {authStatus?.connected ? 'Подключено' : 'Не подключено'}
                {authStatus?.vk_user_id != null && authStatus.connected && (
                  <span className="ml-2 text-[var(--text-muted)]">(VK id: {authStatus.vk_user_id})</span>
                )}
              </span>
              <Button variant="ghost" size="sm" onClick={() => void loadAuthStatus()} className="ml-auto">
                Обновить
              </Button>
            </div>
            {!authStatus?.connected && (
              <div className="p-4 rounded-lg border border-amber-500/30 bg-amber-500/5">
                <p className="text-sm text-[var(--text-muted)] mb-4">
                  Сначала сохраните блок «Приложение VK» выше, затем нажмите кнопку и войдите в VK. После успешного входа
                  токен сохранится в профиле (user_access_token).
                </p>
                <Button onClick={() => void handleConnectVk()}>Подключить VK</Button>
              </div>
            )}
            {authStatus?.connected && (
              <div className="p-4 rounded-lg border border-green-500/30 bg-green-500/5">
                <p className="text-sm text-green-400">Пользовательский токен VK сохранён. Публикация с фото на стену группы доступна.</p>
              </div>
            )}

            <div className="space-y-3 pt-2 border-t border-[var(--border-color)]">
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">Токен сообщества (Access token)</h3>
              <p className="text-xs text-[var(--text-muted)]">
                Обычно это <strong className="text-[var(--text-secondary)]">токен сообщества</strong> для публикации от имени группы и сбора стены (
                <code className="text-[var(--text-muted)]">wall</code>, при необходимости{' '}
                <code className="text-[var(--text-muted)]">groups</code>). Для фото на стене группы дополнительно нужен пользовательский OAuth (блок выше). Подробнее: docs VK_BOT_POSTING.
              </p>
              <input
                type="password"
                value={accessToken === '***' ? '' : accessToken}
                onChange={(e) => setAccessToken(e.target.value)}
                placeholder={accessToken === '***' ? 'Токен сохранён (скрыт)' : 'Оставьте пустым, чтобы не менять'}
                className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
              />
              {accessToken === '***' && (
                <p className="text-xs text-[var(--text-muted)]">Токен сохранён и скрыт. Введите новый токен, чтобы заменить.</p>
              )}
              <Button
                type="button"
                variant="secondary"
                onClick={() => void persistFullVkProfile('Токен и настройки VK сохранены')}
                isLoading={isSavingProfile}
              >
                Сохранить токен и настройки
              </Button>
            </div>

            <div className="space-y-3 pt-2 border-t border-[var(--border-color)]">
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">Проверка авторизации</h3>
              <p className="text-xs text-[var(--text-muted)]">
                С OAuth: запрашивается список подписок на сообщества (VK API{' '}
                <code className="text-[var(--text-muted)]">users.getSubscriptions</code>). Только токен сообщества: по группам из «Group to post» и сбора (
                <code className="text-[var(--text-muted)]">groups.getById</code>).
              </p>
              <Button type="button" onClick={() => void loadSubscriptions()} isLoading={loadingSubscriptions}>
                Запросить список подписок
              </Button>
              {subscriptionsSource && (
                <p className="text-xs text-[var(--text-secondary)]">
                  Источник: {subscriptionsSource}
                </p>
              )}
              {subscriptionsHint && (
                <p className="text-xs text-amber-400/90">{subscriptionsHint}</p>
              )}
              {subscriptions.length > 0 && (
                <ul className="mt-2 space-y-2 max-h-72 overflow-y-auto rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-3">
                  {subscriptions.map((s, i) => (
                    <li
                      key={`${s.id ?? 'x'}-${i}`}
                      className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-[var(--text-primary)] border-b border-[var(--border-color)] border-opacity-50 pb-2 last:border-0 last:pb-0"
                    >
                      {s.screen_name && (
                        <span className="font-mono text-primary-400">{s.screen_name}</span>
                      )}
                      {s.name && <span className="text-[var(--text-secondary)]">{s.name}</span>}
                      {s.id != null && (
                        <span className="text-[var(--text-muted)] text-xs">id: {s.id}</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}

              <div className="pt-3 border-t border-[var(--border-color)] border-dashed">
                <button
                  type="button"
                  className="text-sm text-amber-400/90 hover:text-amber-300 underline-offset-2 hover:underline"
                  onClick={() => setVkSeleniumOpen((v) => !v)}
                >
                  {vkSeleniumOpen ? 'Скрыть' : 'Резервный вход'} (Selenium, логин/пароль)
                </button>
                {vkSeleniumOpen && (
                  <div className="mt-3 space-y-3 rounded-lg border border-amber-500/25 bg-[var(--bg-tertiary)]/50 p-4">
                    <p className="text-xs text-[var(--text-muted)]">
                      Если OAuth или API недоступны: вход через headless-браузер (vk-bot). Пароль не сохраняется в браузере и
                      передаётся только по HTTPS; на сервере не хранится после ответа. Возможны капча и 2FA — тогда
                      используйте обычный OAuth. Результат — веб-список сообществ, не API-токен.
                    </p>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <Input
                        label="Телефон или email VK"
                        type="text"
                        autoComplete="username"
                        value={vkSeleniumLogin}
                        onChange={(e) => setVkSeleniumLogin(e.target.value)}
                        placeholder="Логин"
                      />
                      <Input
                        label="Пароль"
                        type="password"
                        autoComplete="current-password"
                        value={vkSeleniumPassword}
                        onChange={(e) => setVkSeleniumPassword(e.target.value)}
                        placeholder="Одноразово для проверки"
                      />
                    </div>
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => void verifySeleniumFallback()}
                      isLoading={loadingSeleniumVerify}
                      disabled={!vkSeleniumLogin.trim() || !vkSeleniumPassword}
                    >
                      Проверить через Selenium (до ~4 мин)
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Create Post */}
      {activeTab === 'create' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {editingPostId !== null ? 'Edit VKontakte Post' : 'Create VKontakte Post'}
            </CardTitle>
            <CardDescription>Create or edit a post (max {VK_MAX_LENGTH} characters)</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreatePost} className="space-y-6">
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                  Post text (HTML)
                </label>
                <TipTapEditor
                  content={postContent}
                  onChange={setPostContent}
                  placeholder="Enter your post text (HTML supported)"
                  toolbarButtons={[
                    'bold',
                    'italic',
                    'underline',
                    'strike',
                    'heading',
                    'bulletList',
                    'orderedList',
                    'blockquote',
                    'code',
                    'codeBlock',
                    'horizontalRule',
                    'undo',
                    'redo',
                  ]}
                />
                <p className="text-xs text-[var(--text-muted)] mt-2">
                  Plain text length: {htmlToPlainText(postContent).length} / {VK_MAX_LENGTH} characters
                </p>
              </div>

              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                  Изображения
                </label>
                <p className="text-xs text-[var(--text-muted)] mb-2">
                  Загрузите фото с компьютера (JPG, PNG, GIF, WebP). Они будут прикреплены к посту.
                </p>
                <p className="text-xs text-amber-400/90 mb-2 rounded-lg border border-amber-500/25 bg-amber-500/5 px-3 py-2">
                  Публикация <strong>с картинками на стену сообщества</strong> в VK требует пользовательский OAuth (
                  <strong>Авторизация</strong>). Только текст без вложений часто достаточно публиковать с токеном сообщества (вкладка <strong>Авторизация</strong>).
                </p>
                {postImages.some(Boolean) && (
                  <ul className="space-y-2 mb-3">
                    {postImages.map((url, index) =>
                      !url ? null : (
                        <li
                          key={`${url}-${index}`}
                          className="flex items-center gap-3 p-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]"
                        >
                          <img
                            src={imagePreviewUrl(url)}
                            alt=""
                            className="h-14 w-14 shrink-0 object-cover rounded-lg border border-[var(--border-color)] bg-[var(--bg-tertiary)]"
                            onError={(e) => {
                              const el = e.target as HTMLImageElement
                              el.src = ''
                              el.style.display = 'none'
                            }}
                          />
                          <a
                            href={imagePreviewUrl(url)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 min-w-0 text-sm text-primary-400 hover:underline truncate"
                            title={url}
                          >
                            {url}
                          </a>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => setPostImages((prev) => prev.filter((_, i) => i !== index))}
                            className="shrink-0 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                            title="Удалить фото"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            Удалить
                          </Button>
                        </li>
                      )
                    )}
                  </ul>
                )}
                <div className="border-2 border-dashed border-[var(--border-color)] rounded-xl p-6 text-center">
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/gif,image/webp"
                    multiple
                    className="hidden"
                    id="vk-image-upload"
                    disabled={uploadingImage}
                    onChange={async (e) => {
                      const files = e.target.files
                      if (!files?.length) return
                      setError('')
                      setUploadingImage(true)
                      try {
                        for (let i = 0; i < files.length; i++) {
                          const url = await vkontakteService.uploadImage(files[i])
                          setPostImages((prev) => [...prev, url])
                        }
                      } catch (err) {
                        setError(err instanceof Error ? err.message : 'Ошибка загрузки')
                      } finally {
                        setUploadingImage(false)
                        e.target.value = ''
                      }
                    }}
                  />
                  <label htmlFor="vk-image-upload" className="cursor-pointer">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-[var(--text-muted)] mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <p className="text-sm text-[var(--text-secondary)]">
                      {uploadingImage ? 'Загрузка…' : 'Нажмите или перетащите файлы сюда'}
                    </p>
                  </label>
                </div>
              </div>

              {!editingPostId && (
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

      {/* Posts */}
      {activeTab === 'posts' && (
        <Card className="animate-slide-up">
          <CardHeader className="flex flex-row items-center justify-between gap-2">
            <div>
              <CardTitle>Posts</CardTitle>
              <CardDescription>Collected and manual VKontakte posts</CardDescription>
            </div>
            <Button type="button" variant="secondary" size="sm" onClick={loadPosts} disabled={isLoadingPosts}>
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {isLoadingPosts && posts.length === 0 && (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading posts...</div>
            )}
            {!isLoadingPosts && posts.length === 0 && hasLoadedPosts && (
              <div className="text-center py-8 text-[var(--text-muted)]">No posts found.</div>
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
                        <td className="py-2 pr-4 text-[var(--text-primary)] max-w-md truncate">{post.post_text}</td>
                        <td className="py-2 pr-4">
                          <span className="inline-flex items-center rounded-full bg-[var(--bg-secondary)] px-2 py-0.5 text-xs font-medium text-[var(--text-secondary)]">
                            {post.status}
                          </span>
                        </td>
                        <td className="py-2 pr-4 text-[var(--text-secondary)]">
                          {new Date(post.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-2 pr-4 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              type="button"
                              onClick={() => post.id != null && handleEditPost(post.id)}
                              disabled={post.id == null}
                              className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-primary-400 hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-50"
                              title="Edit"
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
                              title="Delete"
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

      {/* Profile Settings (Publishing + Collection) */}
      {activeTab === 'profile' && (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle>Profile Settings</CardTitle>
            <CardDescription>Publishing, connection and collection settings</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingProfile ? (
              <div className="text-center py-8 text-[var(--text-muted)]">Loading profile...</div>
            ) : (
              <form onSubmit={handleSaveProfile} className="space-y-8">
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Publishing</h3>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input type="checkbox" checked={publishEnabled} onChange={(e) => setPublishEnabled(e.target.checked)} className="sr-only peer" />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">Enable publishing</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input type="checkbox" checked={fromGroup} onChange={(e) => setFromGroup(e.target.checked)} className="sr-only peer" />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">From group</span>
                  </label>
                  <Input label="Group to post (ID or short name)" value={groupToPost} onChange={(e) => setGroupToPost(e.target.value)} placeholder="e.g. 123456 or club123456" />
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-[var(--text-secondary)] block">Publish schedule</label>
                    <div className="space-y-3">
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input type="radio" name="schedule" checked={scheduleType === 'immediate'} onChange={() => setScheduleType('immediate')} className="w-4 h-4 text-primary-500" />
                        <span className="text-[var(--text-primary)]">Immediate</span>
                      </label>
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input type="radio" name="schedule" checked={scheduleType === 'intervals'} onChange={() => setScheduleType('intervals')} className="w-4 h-4 text-primary-500" />
                        <span className="text-[var(--text-primary)]">By time intervals</span>
                      </label>
                    </div>
                    {scheduleType === 'intervals' && (
                      <div className="space-y-3 mt-4">
                        {timeIntervals.map((interval, idx) => (
                          <div key={interval.id} className="flex gap-3 items-end">
                            <Input label={`Interval ${idx + 1} start`} type="time" value={interval.start} onChange={(e) => updateTimeInterval(interval.id, 'start', e.target.value)} className="flex-1" />
                            <Input label="End" type="time" value={interval.end} onChange={(e) => updateTimeInterval(interval.id, 'end', e.target.value)} className="flex-1" />
                            {timeIntervals.length > 1 && (
                              <Button type="button" variant="ghost" size="sm" onClick={() => removeTimeInterval(interval.id)} className="text-red-400 hover:text-red-300">
                                Remove
                              </Button>
                            )}
                          </div>
                        ))}
                        {timeIntervals.length < 5 && (
                          <Button type="button" variant="secondary" size="sm" onClick={addTimeInterval}>
                            Add interval
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Collection (Parser)</h3>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input type="checkbox" checked={collectEnabled} onChange={(e) => setCollectEnabled(e.target.checked)} className="sr-only peer" />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">Enable collection</span>
                  </label>
                  {collectEnabled && (
                    <div className="space-y-4 animate-slide-down">
                      <p className="text-sm text-[var(--text-muted)]">
                        Токен сообщества задаётся на вкладке <strong className="text-amber-400/90">Авторизация</strong>. Здесь укажите, с каких групп читать стену.
                      </p>
                      <div className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-4 border border-[var(--border-color)]">
                        <h4 className="text-sm font-semibold text-[var(--text-primary)]">Groups to read (wall.get)</h4>
                        <p className="text-xs text-[var(--text-muted)]">Enter VK group IDs (e.g. 123456 or -123456). One per field.</p>
                        {groupsToRead.map((field) => (
                          <div key={field.id} className="flex gap-3">
                            <Input
                              placeholder="e.g. 123456"
                              value={field.value}
                              onChange={(e) => updateGroupToRead(field.id, e.target.value)}
                              className="flex-1"
                            />
                            {groupsToRead.length > 1 && (
                              <Button type="button" variant="ghost" size="sm" onClick={() => removeGroupToRead(field.id)} className="px-3 text-red-400 hover:text-red-300">
                                Remove
                              </Button>
                            )}
                          </div>
                        ))}
                        <Button type="button" variant="secondary" size="sm" onClick={addGroupToRead}>
                          Add group
                        </Button>
                      </div>
                    </div>
                  )}
                </div>

                <CardFooter className="px-0">
                  <Button type="submit" isLoading={isSavingProfile}>Save Profile Settings</Button>
                </CardFooter>
              </form>
            )}
          </CardContent>
        </Card>
      )}

      {/* Обработка */}
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
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input type="checkbox" checked={processEnabled} onChange={(e) => setProcessEnabled(e.target.checked)} className="sr-only peer" />
                    <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                  </div>
                  <span className="text-[var(--text-primary)]">Обрабатывать перед публикацией</span>
                </label>
                {processEnabled && (
                  <div>
                    <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">Описание обработки</label>
                    <textarea
                      value={processingDescription}
                      onChange={(e) => setProcessingDescription(e.target.value)}
                      rows={4}
                      className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                      placeholder="Опишите, как должны обрабатываться посты..."
                    />
                  </div>
                )}
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input type="checkbox" checked={removeEmojis} onChange={(e) => setRemoveEmojis(e.target.checked)} className="sr-only peer" />
                    <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                  </div>
                  <span className="text-[var(--text-primary)]">Удалить смайлики/эмодзи</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input type="checkbox" checked={removeImages} onChange={(e) => setRemoveImages(e.target.checked)} className="sr-only peer" />
                    <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                  </div>
                  <span className="text-[var(--text-primary)]">Удалить картинки</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input type="checkbox" checked={cleanHtml} onChange={(e) => setCleanHtml(e.target.checked)} className="sr-only peer" />
                    <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                  </div>
                  <span className="text-[var(--text-primary)]">Очистить HTML</span>
                </label>
                <div className="space-y-3">
                  <span className="text-sm font-medium text-[var(--text-secondary)] block">Для каких сервисов подготовить обработку</span>
                  <div className="flex flex-wrap gap-4">
                    {(['wordpress', 'telegram', 'twitter', 'vkontakte'] as const).map((name) => (
                      <label key={name} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={
                            name === 'wordpress' ? processServiceWordpress : name === 'telegram' ? processServiceTelegram : name === 'twitter' ? processServiceTwitter : processServiceVkontakte
                          }
                          onChange={(e) => {
                            if (name === 'wordpress') setProcessServiceWordpress(e.target.checked)
                            else if (name === 'telegram') setProcessServiceTelegram(e.target.checked)
                            else if (name === 'twitter') setProcessServiceTwitter(e.target.checked)
                            else setProcessServiceVkontakte(e.target.checked)
                          }}
                          className="w-4 h-4 text-primary-500 rounded"
                        />
                        <span className="text-[var(--text-primary)]">{name === 'vkontakte' ? 'VKontakte' : name.charAt(0).toUpperCase() + name.slice(1)}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input type="checkbox" checked={statusReviewAfterProcess} onChange={(e) => setStatusReviewAfterProcess(e.target.checked)} className="sr-only peer" />
                    <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                  </div>
                  <span className="text-[var(--text-primary)]">Перевести пост в статус review после обработки</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    <input type="checkbox" checked={addStaticHtml} onChange={(e) => setAddStaticHtml(e.target.checked)} className="sr-only peer" />
                    <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                  </div>
                  <span className="text-[var(--text-primary)]">Добавлять в посты статичный HTML</span>
                </label>
                {addStaticHtml && (
                  <div>
                    <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">Статичный HTML (до 1000 символов)</label>
                    <textarea
                      value={staticHtmlContent}
                      onChange={(e) => setStaticHtmlContent(e.target.value.slice(0, 1000))}
                      rows={4}
                      maxLength={1000}
                      className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                    />
                    <p className="text-xs text-[var(--text-muted)]">{staticHtmlContent.length} / 1000</p>
                  </div>
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
