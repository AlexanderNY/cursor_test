import { useState, FormEvent, useEffect, useCallback } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  createDefaultTargets,
  EMPTY_SELECTED_BRAND_CHANNELS,
  type TargetSocialNetworks,
  type SelectedBrandChannels,
} from '@/components/target-social-networks'
import { apiClient } from '@/services/api-client'
import { vkontakteService } from '@/services/vkontakte-service'
import { useAuth } from '@/contexts/auth-context'
import { useBrand } from '@/contexts/brand-context'
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
import { AuthTab } from './auth-tab'
import { canManagePlatformAuth } from '@/types/smm'
import { buildVkCallbackApiUrl, buildVkOAuthRedirectUri } from '@/lib/vk-public-urls'

const LEGACY_TAB_REDIRECT: Record<string, string> = {
  posts: '/analytics',
  create: '/posts',
  calendar: '/calendar?network=vk',
  profile: '/channels',
  processing: '/channels',
}

function VkontakteHubMap() {
  const { selectedBrandId } = useBrand()
  const calendarHref = selectedBrandId
    ? `/calendar?brand=${selectedBrandId}&network=vk`
    : '/calendar?network=vk'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Brand → Channel</CardTitle>
        <CardDescription>
          Здесь только OAuth и токены VK. Потоки, очередь и картина по бренду — в общих разделах.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="grid gap-3 sm:grid-cols-2 text-sm">
          <li>
            <Link to="/analytics" className="text-primary-400 hover:underline font-medium">
              Posts → Analytics
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Лента и события по каналам бренда.
            </p>
          </li>
          <li>
            <Link to={calendarHref} className="text-primary-400 hover:underline font-medium">
              Calendar → общий календарь
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Расписание публикаций всех сетей, фильтр network=vk.
            </p>
          </li>
          <li>
            <Link to="/channels" className="text-primary-400 hover:underline font-medium">
              Profile Settings → Channels
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Collect / Publish / Alert и цели — в карточке канала, не в профиле VK.
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

export function VKontaktePage() {
  const { user } = useAuth()
  const hasTeam = Boolean(user?.group_id || user?.role_in_group)
  const canAuth = canManagePlatformAuth(user?.role_in_group, hasTeam)
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState<VKontakteTab>('auth')

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
  const [userAccessToken, setUserAccessToken] = useState('')
  const [vkAppId, setVkAppId] = useState('')
  const [vkAppSecret, setVkAppSecret] = useState('')
  const [vkAppServiceKey, setVkAppServiceKey] = useState('')
  const [vkCallbackConfirmation, setVkCallbackConfirmation] = useState('')
  const [vkCallbackSecret, setVkCallbackSecret] = useState('')
  const [vkFrontendUrl, setVkFrontendUrl] = useState('http://localhost:8100')
  const [vkPublicGatewayUrl, setVkPublicGatewayUrl] = useState('http://localhost:8000')
  const [verifyResults, setVerifyResults] = useState<
    Partial<Record<'community' | 'callback' | 'app' | 'oauth', import('@/types/vkontakte').VKAuthVerifyResult | null>>
  >({})
  const [verifyingBlock, setVerifyingBlock] = useState<
    'community' | 'callback' | 'app' | 'oauth' | null
  >(null)
  const [testingCommunityWall, setTestingCommunityWall] = useState(false)
  const [communityTestPostUrl, setCommunityTestPostUrl] = useState<string | null>(null)
  const [loadingAdminGroups, setLoadingAdminGroups] = useState(false)
  const [adminGroups, setAdminGroups] = useState<VKSubscriptionItem[]>([])
  const [testingOwnWall, setTestingOwnWall] = useState(false)
  const [ownWallTestPostUrl, setOwnWallTestPostUrl] = useState<string | null>(null)
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
        setAccessToken(
          profile.access_token === '***' || profile.has_access_token ? '***' : '',
        )
        setUserAccessToken(
          profile.user_access_token === '***' || profile.has_user_access_token ? '***' : '',
        )
        setVkAppId(profile.vk_app_id ?? '')
        setVkAppSecret(
          profile.vk_app_secret === '***' || profile.has_vk_app_secret ? '***' : '',
        )
        setVkAppServiceKey(
          profile.vk_app_service_key === '***' || profile.has_vk_app_service_key ? '***' : '',
        )
        setVkCallbackConfirmation(profile.vk_callback_confirmation ?? '')
        setVkCallbackSecret(
          profile.vk_callback_secret === '***' || profile.has_vk_callback_secret ? '***' : '',
        )
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
    navigate('/posts')
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
          // After failed publish posts land in review; saving re-queues them.
          status: 'ready',
        })
        setSuccess('Post updated and set to ready for publishing')
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
      collect_enabled: Boolean(collectEnabled && authStatus?.connected),
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
      user_access_token:
        userAccessToken && userAccessToken !== '***' ? userAccessToken : undefined,
      vk_app_id: vkAppId.trim() || undefined,
      vk_app_secret: vkAppSecret && vkAppSecret !== '***' ? vkAppSecret : undefined,
      vk_app_service_key: vkAppServiceKey && vkAppServiceKey !== '***' ? vkAppServiceKey : undefined,
      vk_callback_confirmation: vkCallbackConfirmation.trim() || undefined,
      vk_callback_secret: vkCallbackSecret && vkCallbackSecret !== '***' ? vkCallbackSecret : undefined,
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
      await loadProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile settings')
    } finally {
      setIsSavingProfile(false)
    }
  }

  async function persistCommunityAuth() {
    setError('')
    setSuccess('')
    setIsSavingProfile(true)
    try {
      await vkontakteService.saveProfile({
        ...buildProfilePayload(),
        group_to_post: groupToPost.trim() || undefined,
        access_token:
          accessToken && accessToken !== '***' ? accessToken.trim() : undefined,
      })
      setSuccess('Токен сообщества сохранён')
      await loadProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save community token')
    } finally {
      setIsSavingProfile(false)
    }
  }

  async function persistUserToken() {
    setError('')
    setSuccess('')
    setIsSavingProfile(true)
    try {
      await vkontakteService.saveProfile({
        ...buildProfilePayload(),
        user_access_token:
          userAccessToken && userAccessToken !== '***' ? userAccessToken.trim() : undefined,
      })
      setSuccess('User token сохранён')
      await loadProfile()
      await loadAuthStatus()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save user token')
    } finally {
      setIsSavingProfile(false)
    }
  }

  async function persistAppKeys() {
    setError('')
    setSuccess('')
    setIsSavingProfile(true)
    try {
      await vkontakteService.saveProfile({
        ...buildProfilePayload(),
        vk_app_id: vkAppId.trim() || undefined,
        vk_app_secret: vkAppSecret && vkAppSecret !== '***' ? vkAppSecret.trim() : undefined,
        vk_app_service_key:
          vkAppServiceKey && vkAppServiceKey !== '***' ? vkAppServiceKey.trim() : undefined,
        vk_frontend_url: vkFrontendUrl.trim() || undefined,
        vk_public_gateway_url: vkPublicGatewayUrl.trim() || undefined,
      })
      setSuccess('Ключи приложения сохранены')
      await loadProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save app keys')
    } finally {
      setIsSavingProfile(false)
    }
  }

  async function persistCallbackAuth() {
    setError('')
    setSuccess('')
    setIsSavingProfile(true)
    try {
      await vkontakteService.saveProfile({
        ...buildProfilePayload(),
        vk_callback_confirmation: vkCallbackConfirmation.trim() || undefined,
        vk_callback_secret:
          vkCallbackSecret && vkCallbackSecret !== '***' ? vkCallbackSecret.trim() : undefined,
      })
      setSuccess('Callback API настройки сохранены')
      await loadProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save callback settings')
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
    if (collectEnabled && !(authStatus?.connected)) {
      setError(
        'Сбор (Collect) требует user OAuth. Откройте Авторизация → «Подключить пользователя».',
      )
      return
    }
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

  const vkOAuthRedirectUri =
    authStatus?.redirect_uri?.trim() || buildVkOAuthRedirectUri(vkPublicGatewayUrl)
  const vkCallbackApiUrl = buildVkCallbackApiUrl(vkPublicGatewayUrl)

  const startVkOAuth = (flow: 'user' | 'group') => {
    setError('')
    void vkontakteService
      .getAuthUrl(flow)
      .then(({ url }) => {
        window.location.href = url
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to get OAuth URL')
      })
  }

  async function runVerify(block: 'community' | 'callback' | 'app' | 'oauth') {
    setVerifyingBlock(block)
    setError('')
    try {
      const res = await vkontakteService.verifyAuthBlock(block)
      setVerifyResults((prev) => ({ ...prev, [block]: res }))
      if (res.ok) setSuccess(res.message)
      else setError(res.message)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Verify failed'
      setVerifyResults((prev) => ({
        ...prev,
        [block]: { ok: false, block, message },
      }))
      setError(message)
    } finally {
      setVerifyingBlock(null)
    }
  }

  async function runTestCommunityWall() {
    setTestingCommunityWall(true)
    setError('')
    setCommunityTestPostUrl(null)
    try {
      const res = await vkontakteService.testCommunityWall()
      setVerifyResults((prev) => ({ ...prev, community: res }))
      const url =
        res.details && typeof res.details.post_url === 'string' ? res.details.post_url : null
      setCommunityTestPostUrl(url)
      if (res.ok) setSuccess(res.message)
      else setError(res.message)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Тестовый пост не удался')
    } finally {
      setTestingCommunityWall(false)
    }
  }

  async function runLoadAdminGroups() {
    setLoadingAdminGroups(true)
    setError('')
    try {
      const res = await vkontakteService.getAdminGroups()
      setAdminGroups(res.subscriptions ?? [])
      setSuccess(
        res.count > 0
          ? `Админ-сообществ: ${res.count}. Кликните, чтобы выбрать Group to post.`
          : 'Список пуст — подключите user OAuth с доступом к группам.',
      )
    } catch (err) {
      setAdminGroups([])
      setError(err instanceof Error ? err.message : 'Не удалось загрузить admin-группы')
    } finally {
      setLoadingAdminGroups(false)
    }
  }

  function selectAdminGroup(groupId: number) {
    setGroupToPost(String(groupId))
    setSuccess(`Group to post = ${groupId}. Сохраните блок «Сообщество».`)
  }

  async function runTestOwnWall() {
    setTestingOwnWall(true)
    setError('')
    setOwnWallTestPostUrl(null)
    try {
      const res = await vkontakteService.testOwnWall()
      setVerifyResults((prev) => ({ ...prev, oauth: res }))
      const url =
        res.details && typeof res.details.post_url === 'string' ? res.details.post_url : null
      setOwnWallTestPostUrl(url)
      if (res.ok) setSuccess(res.message)
      else setError(res.message)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Тест на личную стену не удался')
    } finally {
      setTestingOwnWall(false)
    }
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="VKontakte"
        description="OAuth и токены для Collect / Publish / Alert. Потоки настраиваются в Channels."
      />

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

      <VkontakteHubMap />

      {canAuth ? (
        <AuthTab
          authStatus={authStatus}
          groupToPost={groupToPost}
          onGroupToPostChange={setGroupToPost}
          accessToken={accessToken}
          onAccessTokenChange={setAccessToken}
          userAccessToken={userAccessToken}
          onUserAccessTokenChange={setUserAccessToken}
          onSaveUserToken={() => void persistUserToken()}
          vkCallbackConfirmation={vkCallbackConfirmation}
          onVkCallbackConfirmationChange={setVkCallbackConfirmation}
          vkCallbackSecret={vkCallbackSecret}
          onVkCallbackSecretChange={setVkCallbackSecret}
          vkCallbackApiUrl={vkCallbackApiUrl}
          vkAppId={vkAppId}
          onVkAppIdChange={setVkAppId}
          vkAppSecret={vkAppSecret}
          onVkAppSecretChange={setVkAppSecret}
          vkAppServiceKey={vkAppServiceKey}
          onVkAppServiceKeyChange={setVkAppServiceKey}
          vkFrontendUrl={vkFrontendUrl}
          onVkFrontendUrlChange={setVkFrontendUrl}
          vkPublicGatewayUrl={vkPublicGatewayUrl}
          onVkPublicGatewayUrlChange={setVkPublicGatewayUrl}
          vkOAuthRedirectUri={vkOAuthRedirectUri}
          isSavingProfile={isSavingProfile}
          verifyResults={verifyResults}
          verifyingBlock={verifyingBlock}
          onSaveCommunity={() => void persistCommunityAuth()}
          onSaveCallback={() => void persistCallbackAuth()}
          onSaveApp={() => void persistAppKeys()}
          onVerify={(block) => void runVerify(block)}
          onTestCommunityWall={() => void runTestCommunityWall()}
          testingCommunityWall={testingCommunityWall}
          communityTestPostUrl={communityTestPostUrl}
          onLoadAdminGroups={() => void runLoadAdminGroups()}
          loadingAdminGroups={loadingAdminGroups}
          adminGroups={adminGroups}
          onSelectAdminGroup={selectAdminGroup}
          onTestOwnWall={() => void runTestOwnWall()}
          testingOwnWall={testingOwnWall}
          ownWallTestPostUrl={ownWallTestPostUrl}
          onRefreshAuthStatus={() => void loadAuthStatus()}
          onConnectVkUser={() => startVkOAuth('user')}
          onConnectVkCommunity={() => startVkOAuth('group')}
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
      ) : (
        <Alert variant="info">
          Подключать VK может владелец или админ команды.{' '}
          <Link to="/channels" className="underline">
            К каналам
          </Link>
        </Alert>
      )}
    </PageContainer>
  )
}
