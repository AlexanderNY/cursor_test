import { useState, FormEvent, useEffect, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import {
  createDefaultTargets,
  EMPTY_SELECTED_BRAND_CHANNELS,
  type TargetSocialNetworks,
  type SelectedBrandChannels,
} from '@/components/target-social-networks'
import { apiClient } from '@/services/api-client'
import { vkontakteService } from '@/services/vkontakte-service'
import { useAuth } from '@/contexts/auth-context'
import type {
  VKontakteProfile,
  VKontaktePostListItem,
  ScheduleType,
  VKAuthStatus,
  VKSubscriptionItem,
  VKontakteTab,
} from '@/types/vkontakte'
import {
  VK_MAX_LENGTH,
  AUTH_STATUS_POLL_INTERVAL_MS,
  generateId,
  htmlToPlainText,
  imagePreviewUrl,
  getWeekStart,
  getWeekRange,
  type DynamicField,
} from './vkontakte-helpers'
import { CreatePostTab } from './create-post-tab'
import { PostsTab } from './posts-tab'
import { CalendarTab } from './calendar-tab'
import { ProfileSettingsTab } from './profile-settings-tab'
import { ProcessingTab } from './processing-tab'
import { AuthTab } from './auth-tab'

const TAB_ORDER: { id: VKontakteTab; label: string; accent?: boolean }[] = [
  { id: 'create', label: 'Create Post' },
  { id: 'posts', label: 'Posts' },
  { id: 'calendar', label: 'Calendar' },
  { id: 'profile', label: 'Profile Settings' },
  { id: 'processing', label: 'Обработка' },
  { id: 'auth', label: 'Авторизация', accent: true },
]

export function VKontaktePage() {
  const { user } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState<VKontakteTab>(() =>
    searchParams.get('auth') === '1' ? 'auth' : 'create',
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

  const [postContent, setPostContent] = useState('')
  const [postImages, setPostImages] = useState<string[]>([])
  const [publishAt, setPublishAt] = useState('')
  const [targetGroupsText, setTargetGroupsText] = useState('')
  const [postTargets, setPostTargets] = useState<TargetSocialNetworks>(() => createDefaultTargets('vk'))
  const [selectedChannels, setSelectedChannels] = useState<SelectedBrandChannels>({
    ...EMPTY_SELECTED_BRAND_CHANNELS,
  })
  const [editingPostId, setEditingPostId] = useState<number | null>(null)

  const [posts, setPosts] = useState<VKontaktePostListItem[]>([])
  const [isLoadingPosts, setIsLoadingPosts] = useState(false)
  const [hasLoadedPosts, setHasLoadedPosts] = useState(false)
  const [deletingPostId, setDeletingPostId] = useState<number | null>(null)

  const [calendarWeekStart, setCalendarWeekStart] = useState(() => getWeekStart(new Date()))
  const [calendarPosts, setCalendarPosts] = useState<VKontaktePostListItem[]>([])
  const [isLoadingCalendar, setIsLoadingCalendar] = useState(false)

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
            })),
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
      const oauthMessage =
        searchParams.get('message') ||
        (searchParams.get('oauth') === 'success' ? 'Connected successfully' : 'Connection failed')
      setSuccess(searchParams.get('oauth') === 'success' ? oauthMessage : '')
      setError(searchParams.get('oauth') === 'error' ? oauthMessage : '')
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

  useEffect(() => {
    if (activeTab === 'calendar') {
      loadCalendarPosts(calendarWeekStart)
    }
  }, [activeTab, calendarWeekStart])

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

  async function loadCalendarPosts(weekStart: Date) {
    setIsLoadingCalendar(true)
    const { dateFrom, dateTo } = getWeekRange(weekStart)
    try {
      const data = await vkontakteService.getPosts({ dateFrom, dateTo, limit: 200 })
      setCalendarPosts(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load calendar posts')
    } finally {
      setIsLoadingCalendar(false)
    }
  }

  function switchToCreateTab() {
    setEditingPostId(null)
    setPostContent('')
    setPostImages([])
    setActiveTab('create')
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
          publish_at: publishAt ? new Date(publishAt).toISOString() : undefined,
          target_groups: [
            ...selectedChannels.vk,
            ...targetGroupsText
              .split(/[\n,]+/)
              .map((s) => s.trim())
              .filter(Boolean),
          ].filter((v, i, a) => a.indexOf(v) === i),
          target_channels: selectedChannels.tg.length ? selectedChannels.tg : undefined,
        })
        setSuccess('Post created successfully')
        setPostContent('')
        setPostImages([])
        setPublishAt('')
        setTargetGroupsText('')
        setSelectedChannels({ ...EMPTY_SELECTED_BRAND_CHANNELS })
        if (hasLoadedPosts) loadPosts()
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
      if (activeTab === 'calendar') loadCalendarPosts(calendarWeekStart)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete post')
    } finally {
      setDeletingPostId(null)
    }
  }

  async function handleReschedule(postId: number, newIsoDatetime: string) {
    setError('')
    try {
      await vkontakteService.updatePost(postId, { publish_at: newIsoDatetime })
      setSuccess('Post rescheduled')
      if (activeTab === 'calendar') loadCalendarPosts(calendarWeekStart)
      if (hasLoadedPosts) loadPosts()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reschedule post')
    }
  }

  async function handleUploadImages(files: FileList) {
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
      .map((v) => parseInt(v, 10))
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
    await persistFullVkProfile('Processing settings saved successfully')
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
      setSubscriptionsSource(
        res.source === 'user_oauth'
          ? 'Пользовательский OAuth (users.getSubscriptions)'
          : 'Токен сообщества (groups.getById)',
      )
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
            : base,
        )
        return
      }
      setSubscriptions(res.subscriptions ?? [])
      setSubscriptionsSource('Selenium: веб-страница (vk-bot), не заменяет OAuth/API-токен')
      setSubscriptionsHint(res.message ?? null)
      setSuccess(
        res.subscriptions && res.subscriptions.length > 0
          ? `Selenium: загружено записей: ${res.subscriptions.length}`
          : 'Selenium: запрос выполнен, список пуст.',
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка vk-bot (Selenium)')
    } finally {
      setLoadingSeleniumVerify(false)
    }
  }

  function resolveImagePreview(url: string): string {
    const base = apiClient.defaults.baseURL ?? '/api'
    const origin = typeof window !== 'undefined' ? window.location.origin : ''
    return imagePreviewUrl(url, base, origin)
  }

  const showAuthBlock = authStatus != null && !authStatus.connected
  const vkOAuthRedirectUri = `${vkPublicGatewayUrl.replace(/\/$/, '')}/vk/oauth/callback`

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="VKontakte Integration"
        description="Configure your VKontakte account settings and post management"
      />
      <p className="mb-4 text-sm">
        <Link to="/channels" className="text-primary-400 hover:underline">
          Управлять каналами → /channels
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

      <div className="flex border-b border-[var(--border-color)] overflow-x-auto">
        {TAB_ORDER.map((tab) => {
          const isActive = activeTab === tab.id
          const isAuth = tab.id === 'auth'
          const textClass = isAuth
            ? isActive || showAuthBlock
              ? 'text-amber-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            : isActive
              ? 'text-primary-400'
              : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          return (
            <button
              key={tab.id}
              type="button"
              className={`px-6 py-3 text-sm font-medium transition-all relative whitespace-nowrap flex items-center gap-1.5 ${textClass} ${isAuth && showAuthBlock && !isActive ? 'animate-pulse' : ''}`}
              onClick={() => (tab.id === 'create' ? switchToCreateTab() : setActiveTab(tab.id))}
            >
              {isAuth && (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              )}
              {tab.label}
              {isAuth && showAuthBlock && <span className="inline-block w-2 h-2 bg-amber-400 rounded-full" />}
              {isActive && (
                <div className={`absolute bottom-0 left-0 right-0 h-0.5 ${isAuth ? 'bg-amber-500' : 'bg-primary-500'}`} />
              )}
            </button>
          )
        })}
      </div>

      {activeTab === 'create' && (
        <CreatePostTab
          postContent={postContent}
          onPostContentChange={setPostContent}
          postImages={postImages}
          onRemoveImage={(index) => setPostImages((prev) => prev.filter((_, i) => i !== index))}
          onUploadImages={handleUploadImages}
          uploadingImage={uploadingImage}
          imagePreviewUrl={resolveImagePreview}
          editingPostId={editingPostId}
          publishAt={publishAt}
          onPublishAtChange={setPublishAt}
          targetGroupsText={targetGroupsText}
          onTargetGroupsTextChange={setTargetGroupsText}
          postTargets={postTargets}
          onPostTargetsChange={setPostTargets}
          selectedChannels={selectedChannels}
          onSelectedChannelsChange={setSelectedChannels}
          isCreatingPost={isCreatingPost}
          onSubmit={handleCreatePost}
        />
      )}

      {activeTab === 'posts' && (
        <PostsTab
          posts={posts}
          isLoadingPosts={isLoadingPosts}
          hasLoadedPosts={hasLoadedPosts}
          deletingPostId={deletingPostId}
          onRefresh={loadPosts}
          onEdit={handleEditPost}
          onDelete={handleDeletePost}
        />
      )}

      {activeTab === 'calendar' && (
        <CalendarTab
          posts={calendarPosts}
          weekStart={calendarWeekStart}
          isLoading={isLoadingCalendar}
          onWeekChange={setCalendarWeekStart}
          onReschedule={handleReschedule}
        />
      )}

      {activeTab === 'profile' && (
        <ProfileSettingsTab
          isLoadingProfile={isLoadingProfile}
          isSavingProfile={isSavingProfile}
          publishEnabled={publishEnabled}
          onPublishEnabledChange={setPublishEnabled}
          fromGroup={fromGroup}
          onFromGroupChange={setFromGroup}
          groupToPost={groupToPost}
          onGroupToPostChange={setGroupToPost}
          scheduleType={scheduleType}
          onScheduleTypeChange={setScheduleType}
          timeIntervals={timeIntervals}
          onAddTimeInterval={() => {
            if (timeIntervals.length < 5) {
              setTimeIntervals((prev) => [...prev, { id: generateId(), start: '', end: '' }])
            }
          }}
          onRemoveTimeInterval={(id) => {
            if (timeIntervals.length > 1) {
              setTimeIntervals((prev) => prev.filter((i) => i.id !== id))
            }
          }}
          onUpdateTimeInterval={(id, field, value) => {
            setTimeIntervals((prev) => prev.map((i) => (i.id === id ? { ...i, [field]: value } : i)))
          }}
          collectEnabled={collectEnabled}
          onCollectEnabledChange={setCollectEnabled}
          groupsToRead={groupsToRead}
          onAddGroupToRead={() => setGroupsToRead((prev) => [...prev, { id: generateId(), value: '' }])}
          onRemoveGroupToRead={(id) => {
            if (groupsToRead.length > 1) setGroupsToRead((prev) => prev.filter((f) => f.id !== id))
          }}
          onUpdateGroupToRead={(id, value) => {
            setGroupsToRead((prev) => prev.map((f) => (f.id === id ? { ...f, value } : f)))
          }}
          onSubmit={handleSaveProfile}
        />
      )}

      {activeTab === 'processing' && (
        <ProcessingTab
          isLoadingProfile={isLoadingProfile}
          isSavingProfile={isSavingProfile}
          processEnabled={processEnabled}
          onProcessEnabledChange={setProcessEnabled}
          processingDescription={processingDescription}
          onProcessingDescriptionChange={setProcessingDescription}
          removeEmojis={removeEmojis}
          onRemoveEmojisChange={setRemoveEmojis}
          removeImages={removeImages}
          onRemoveImagesChange={setRemoveImages}
          cleanHtml={cleanHtml}
          onCleanHtmlChange={setCleanHtml}
          processServiceWordpress={processServiceWordpress}
          onProcessServiceWordpressChange={setProcessServiceWordpress}
          processServiceTelegram={processServiceTelegram}
          onProcessServiceTelegramChange={setProcessServiceTelegram}
          processServiceTwitter={processServiceTwitter}
          onProcessServiceTwitterChange={setProcessServiceTwitter}
          processServiceVkontakte={processServiceVkontakte}
          onProcessServiceVkontakteChange={setProcessServiceVkontakte}
          statusReviewAfterProcess={statusReviewAfterProcess}
          onStatusReviewAfterProcessChange={setStatusReviewAfterProcess}
          addStaticHtml={addStaticHtml}
          onAddStaticHtmlChange={setAddStaticHtml}
          staticHtmlContent={staticHtmlContent}
          onStaticHtmlContentChange={setStaticHtmlContent}
          onSubmit={handleSaveProcessing}
        />
      )}

      {activeTab === 'auth' && (
        <AuthTab
          authStatus={authStatus}
          vkAppId={vkAppId}
          onVkAppIdChange={setVkAppId}
          vkAppSecret={vkAppSecret}
          onVkAppSecretChange={setVkAppSecret}
          vkFrontendUrl={vkFrontendUrl}
          onVkFrontendUrlChange={setVkFrontendUrl}
          vkPublicGatewayUrl={vkPublicGatewayUrl}
          onVkPublicGatewayUrlChange={setVkPublicGatewayUrl}
          vkOAuthRedirectUri={vkOAuthRedirectUri}
          accessToken={accessToken}
          onAccessTokenChange={setAccessToken}
          isSavingProfile={isSavingProfile}
          onSaveOAuthSettings={() => void persistFullVkProfile('Настройки OAuth VK сохранены')}
          onSaveTokenSettings={() => void persistFullVkProfile('Токен и настройки VK сохранены')}
          onRefreshAuthStatus={() => void loadAuthStatus()}
          onConnectVk={() => {
            setError('')
            void vkontakteService
              .getAuthUrl()
              .then(({ url }) => {
                window.location.href = url
              })
              .catch((err) => {
                setError(err instanceof Error ? err.message : 'Failed to get OAuth URL')
              })
          }}
          loadingSubscriptions={loadingSubscriptions}
          onLoadSubscriptions={() => void loadSubscriptions()}
          subscriptions={subscriptions}
          subscriptionsSource={subscriptionsSource}
          subscriptionsHint={subscriptionsHint}
          vkSeleniumOpen={vkSeleniumOpen}
          onToggleSelenium={() => setVkSeleniumOpen((v) => !v)}
          vkSeleniumLogin={vkSeleniumLogin}
          onVkSeleniumLoginChange={setVkSeleniumLogin}
          vkSeleniumPassword={vkSeleniumPassword}
          onVkSeleniumPasswordChange={setVkSeleniumPassword}
          loadingSeleniumVerify={loadingSeleniumVerify}
          onVerifySelenium={() => void verifySeleniumFallback()}
        />
      )}
    </PageContainer>
  )
}
