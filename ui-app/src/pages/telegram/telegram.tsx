import { useState, useEffect, FormEvent, useCallback } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/services/api-client'
import { telegramService, type TgAuthStatus } from '@/services/telegram-service'
import {
  createDefaultTargets,
  EMPTY_SELECTED_BRAND_CHANNELS,
  type SelectedBrandChannels,
  type TargetSocialNetworks,
} from '@/components/target-social-networks'
import { useAuth } from '@/contexts/auth-context'
import { useBrand } from '@/contexts/brand-context'
import type {
  PublishScheduleType,
  TelegramChatRef,
  TelegramPostListItem,
  TgAnalyticsAlertItem,
  TgPostTemplate,
  TelegramTab,
} from '@/types/telegram'
import {
  AUTH_STATUS_POLL_INTERVAL_MS,
  MAX_ALERT_RULES,
  MAX_ALERT_LIST_ITEMS,
  generateId,
  SCHEDULE_MINUTES,
  createEmptyAlertRuleBlock,
  mapAlertRulesFromProfile,
  serializeAlertRules,
  validateAlertRules,
  fromDatetimeLocalValue,
  getWeekStart,
  getWeekRange,
  chatRefsFromInputs,
  chatRefsFromDynamicFields,
  dynamicFieldsFromChatRefs,
  type ScheduleMinute,
  type DynamicField,
  type AlertRuleBlock,
  type AvailableChannel,
} from './telegram-helpers'
import { AuthTab } from './auth-tab'
import { canManagePlatformAuth } from '@/types/smm'

const LEGACY_TAB_REDIRECT: Record<string, string> = {
  posts: '/analytics',
  create: '/posts',
  calendar: '/calendar?network=tg',
  profile: '/channels',
  processing: '/channels',
}

function TelegramHubMap() {
  const { selectedBrandId } = useBrand()
  const calendarHref = selectedBrandId
    ? `/calendar?brand=${selectedBrandId}&network=tg`
    : '/calendar?network=tg'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Brand → Channel</CardTitle>
        <CardDescription>
          Здесь только сессия Telegram. Потоки, очередь и картина по бренду — в общих разделах.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="grid gap-3 sm:grid-cols-2 text-sm">
          <li>
            <Link to="/analytics" className="text-primary-400 hover:underline font-medium">
              Posts → Analytics
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Лента и события по каналам бренда, вкладка Telegram в Analytics.
            </p>
          </li>
          <li>
            <Link to={calendarHref} className="text-primary-400 hover:underline font-medium">
              Calendar → общий календарь
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Расписание публикаций всех сетей, фильтр network=tg.
            </p>
          </li>
          <li>
            <Link to="/channels" className="text-primary-400 hover:underline font-medium">
              Profile Settings → Channels
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Collect / Publish / Alert и цели — в карточке канала, не в профиле TG.
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

export function TelegramPage() {
  const { user } = useAuth()
  const hasTeam = Boolean(user?.group_id || user?.role_in_group)
  const canAuth = canManagePlatformAuth(user?.role_in_group, hasTeam)
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const [activeTab, setActiveTab] = useState<TelegramTab>('auth')

  const [authStatus, setAuthStatus] = useState<TgAuthStatus | null>(null)
  const [authCode, setAuthCode] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [isSubmittingAuth, setIsSubmittingAuth] = useState(false)

  const [publishEnabled, setPublishEnabled] = useState(false)
  const [collectEnabled, setCollectEnabled] = useState(false)
  const [publishScheduleType, setPublishScheduleType] = useState<PublishScheduleType>('on_new_messages')
  const [publishScheduleHour, setPublishScheduleHour] = useState(9)
  const [publishScheduleMinute, setPublishScheduleMinute] = useState<ScheduleMinute>(0)
  const [apiId, setApiId] = useState('')
  const [apiHash, setApiHash] = useState('')
  const [telegramUsername, setTelegramUsername] = useState('')
  const [authPhoneNumber, setAuthPhoneNumber] = useState('')
  const [channelToPost, setChannelToPost] = useState('')
  const [channelToPostTitle, setChannelToPostTitle] = useState('')
  const [channelsToPost, setChannelsToPost] = useState<TelegramChatRef[]>([])
  const [alertEnabled, setAlertEnabled] = useState(false)
  const [alertRules, setAlertRules] = useState<AlertRuleBlock[]>(() => [createEmptyAlertRuleBlock()])
  const [chatsToRead, setChatsToRead] = useState<DynamicField[]>([{ id: generateId(), value: '', label: '' }])
  const [saveConditions, setSaveConditions] = useState<DynamicField[]>([{ id: generateId(), value: '' }])
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
  const [summarizeEnabled, setSummarizeEnabled] = useState(false)
  const [summarizeMinLength, setSummarizeMinLength] = useState(500)
  const [digestIntervalMin, setDigestIntervalMin] = useState(30)
  const [digestChannel, setDigestChannel] = useState('')
  const [classificationEnabled, setClassificationEnabled] = useState(false)
  const [classificationCategories, setClassificationCategories] = useState('новости, реклама, технологии, финансы, другое')
  const [batchEnrichmentEnabled, setBatchEnrichmentEnabled] = useState(false)
  const [recentAlerts, setRecentAlerts] = useState<TgAnalyticsAlertItem[]>([])

  const [postText, setPostText] = useState('')
  const [postTargets, setPostTargets] = useState<TargetSocialNetworks>(() => createDefaultTargets('tg'))
  const [publishAt, setPublishAt] = useState('')
  const [selectedChannels, setSelectedChannels] = useState<SelectedBrandChannels>(
    () => ({ ...EMPTY_SELECTED_BRAND_CHANNELS }),
  )
  const [templates, setTemplates] = useState<TgPostTemplate[]>([])
  const [selectedTemplateId, setSelectedTemplateId] = useState('')
  const [isSavingTemplate, setIsSavingTemplate] = useState(false)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)

  const [posts, setPosts] = useState<TelegramPostListItem[]>([])
  const [isLoadingPosts, setIsLoadingPosts] = useState(false)
  const [hasLoadedPosts, setHasLoadedPosts] = useState(false)
  const [calendarPosts, setCalendarPosts] = useState<TelegramPostListItem[]>([])
  const [isLoadingCalendar, setIsLoadingCalendar] = useState(false)
  const [calendarWeekStart, setCalendarWeekStart] = useState(() => getWeekStart(new Date()))

  const [editingPostId, setEditingPostId] = useState<number | null>(null)
  const [deletingPostId, setDeletingPostId] = useState<number | null>(null)
  const [approvingPostId, setApprovingPostId] = useState<number | null>(null)
  const [deletingPublishedId, setDeletingPublishedId] = useState<number | null>(null)

  const [availableChannels, setAvailableChannels] = useState<AvailableChannel[]>([])
  const [isCheckingChannels, setIsCheckingChannels] = useState(false)
  const [channelsError, setChannelsError] = useState('')

  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [isCreatingPost, setIsCreatingPost] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    loadProfile()
  }, [])

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

  const loadAuthStatus = useCallback(async () => {
    if (!user?.id) return
    try {
      const status = await telegramService.getAuthStatus(user.id)
      setAuthStatus(status)
    } catch (err) {
      console.error('[TelegramPage] Failed to load auth status:', err)
    }
  }, [user?.id])

  useEffect(() => {
    if (!user?.id) return
    loadAuthStatus()
    const interval = setInterval(loadAuthStatus, AUTH_STATUS_POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [user?.id, loadAuthStatus])

  useEffect(() => {
    if (activeTab === 'posts' && !hasLoadedPosts) {
      loadPosts()
    }
  }, [activeTab, hasLoadedPosts])

  useEffect(() => {
    if (activeTab === 'create') {
      loadTemplates()
    }
  }, [activeTab])

  useEffect(() => {
    if (activeTab === 'calendar') {
      loadCalendarPosts(calendarWeekStart)
    }
  }, [activeTab, calendarWeekStart])

  async function loadTemplates() {
    try {
      const data = await telegramService.getTemplates()
      setTemplates(data)
    } catch (err) {
      console.warn('Templates load failed', err)
    }
  }

  async function loadCalendarPosts(weekStart: Date) {
    setIsLoadingCalendar(true)
    const { dateFrom, dateTo } = getWeekRange(weekStart)
    try {
      const data = await telegramService.getPosts({ dateFrom, dateTo, limit: 200 })
      setCalendarPosts(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load calendar posts')
    } finally {
      setIsLoadingCalendar(false)
    }
  }

  async function loadProfile() {
    setIsLoadingProfile(true)
    setError('')
    try {
      const profile = await telegramService.getProfile()
      if (profile) {
        setPublishEnabled(profile.publish_enabled ?? false)
        setCollectEnabled(profile.collect_enabled ?? false)
        setPublishScheduleType((profile.schedule_type as PublishScheduleType) || 'on_new_messages')
        const ti = profile.time_intervals
        if (Array.isArray(ti) && ti.length > 0 && ti[0]?.start) {
          const [h, m] = ti[0].start.split(':').map(Number)
          const hour = Number.isFinite(h) ? Math.max(0, Math.min(23, h)) : 9
          const rawMin = Number.isFinite(m) ? m : 0
          const minute = SCHEDULE_MINUTES.reduce((prev, curr) =>
            Math.abs(curr - rawMin) < Math.abs(prev - rawMin) ? curr : prev,
          ) as ScheduleMinute
          setPublishScheduleHour(hour)
          setPublishScheduleMinute(minute)
        }
        setApiId(profile.api_id || '')
        setApiHash(profile.api_hash || '')
        setTelegramUsername(profile.telegram_username || '')
        setAuthPhoneNumber(profile.auth_phone_number || '')
        setChannelToPost(profile.channel_to_post || '')
        {
          const channelRefs = chatRefsFromInputs(
            profile.channels_to_post?.length
              ? profile.channels_to_post
              : profile.channel_to_post
                ? [profile.channel_to_post]
                : [],
          )
          setChannelsToPost(channelRefs)
          setChannelToPostTitle(channelRefs[0]?.title || '')
        }
        setAlertEnabled(profile.alert_enabled ?? false)
        setAlertRules(mapAlertRulesFromProfile(profile.alert_rules))
        if (profile.chats_to_read && profile.chats_to_read.length > 0) {
          setChatsToRead(dynamicFieldsFromChatRefs(profile.chats_to_read))
        }
        if (profile.save_conditions && profile.save_conditions.length > 0) {
          setSaveConditions(profile.save_conditions.map((condition) => ({ id: generateId(), value: condition })))
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
        }
        setStatusReviewAfterProcess(profile.status_review_after_process ?? false)
        setAddStaticHtml(profile.add_static_html ?? false)
        setStaticHtmlContent((profile.static_html_content ?? '').slice(0, 1000))
        setSummarizeEnabled(profile.summarize_enabled ?? false)
        setSummarizeMinLength(profile.summarize_min_length ?? 500)
        setDigestIntervalMin(profile.digest_interval_min ?? 30)
        setDigestChannel(profile.digest_channel || '')
        setClassificationEnabled(profile.classification_enabled ?? false)
        setBatchEnrichmentEnabled(profile.batch_enrichment_enabled ?? false)
        if (profile.classification_categories?.length) {
          setClassificationCategories(profile.classification_categories.join(', '))
        }
        if (profile.alert_enabled) {
          telegramService.getAnalyticsAlerts('7d', 10).then(setRecentAlerts).catch(() => {})
        }
      }
    } catch (err) {
      console.log('Profile not found, using defaults', err)
    } finally {
      setIsLoadingProfile(false)
    }
  }

  async function loadPosts() {
    setIsLoadingPosts(true)
    setError('')
    try {
      const data = await telegramService.getPosts()
      setPosts(data)
      setHasLoadedPosts(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load posts')
    } finally {
      setIsLoadingPosts(false)
    }
  }

  function buildProfileConfig() {
    const timeIntervals =
      publishScheduleType === 'by_intervals'
        ? [{ start: `${String(publishScheduleHour).padStart(2, '0')}:${String(publishScheduleMinute).padStart(2, '0')}` }]
        : []
    return {
      publish_enabled: publishEnabled,
      collect_enabled: collectEnabled,
      schedule_type: publishScheduleType,
      time_intervals: timeIntervals,
      api_id: apiId || undefined,
      api_hash: apiHash || undefined,
      telegram_username: telegramUsername || undefined,
      auth_phone_number: authPhoneNumber || undefined,
      chats_to_read: chatRefsFromDynamicFields(chatsToRead),
      save_conditions: saveConditions.map((f) => f.value).filter(Boolean),
      channel_to_post: channelsToPost[0]?.id || channelToPost || undefined,
      channels_to_post: (() => {
        if (channelsToPost.length) return channelsToPost
        const id = channelToPost.trim()
        if (!id) return undefined
        const title = channelToPostTitle.trim()
        return [title ? { id, title } : { id }]
      })(),
      alert_enabled: alertEnabled,
      alert_rules: serializeAlertRules(alertRules),
      process_enabled: processEnabled,
      processing_description: processEnabled ? processingDescription || undefined : undefined,
      summarize_enabled: summarizeEnabled,
      summarize_min_length: summarizeMinLength,
      digest_interval_min: digestIntervalMin,
      digest_channel: digestChannel || undefined,
      classification_enabled: classificationEnabled,
      classification_categories: classificationCategories.split(',').map((s) => s.trim()).filter(Boolean),
      batch_enrichment_enabled: batchEnrichmentEnabled,
    }
  }

  async function handleDeletePost(postId: number) {
    if (deletingPostId !== null) return
    setDeletingPostId(postId)
    setError('')
    try {
      await telegramService.deletePost(postId)
      setPosts((prev) => prev.filter((p) => p.id !== postId))
      setSuccess('Post deleted successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete post')
    } finally {
      setDeletingPostId(null)
    }
  }

  async function handleApprovePost(postId: number) {
    if (approvingPostId !== null) return
    setApprovingPostId(postId)
    setError('')
    try {
      await telegramService.approvePost(postId)
      setPosts((prev) => prev.map((p) => (p.id === postId ? { ...p, status: 'approved' } : p)))
      setSuccess('Post approved')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve post')
    } finally {
      setApprovingPostId(null)
    }
  }

  async function handleDeletePublished(postId: number) {
    if (!user?.id || deletingPublishedId !== null) return
    setDeletingPublishedId(postId)
    setError('')
    try {
      await telegramService.deletePublishedPost(user.id, postId)
      setSuccess('Post deleted from Telegram')
      loadPosts()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete from Telegram')
    } finally {
      setDeletingPublishedId(null)
    }
  }

  async function handleReschedule(postId: number, newIsoDatetime: string) {
    setError('')
    try {
      await telegramService.updatePost(postId, undefined, undefined, { publishAt: newIsoDatetime })
      setSuccess('Post rescheduled')
      if (activeTab === 'calendar') {
        loadCalendarPosts(calendarWeekStart)
      }
      if (hasLoadedPosts) {
        loadPosts()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reschedule post')
      throw err
    }
  }

  async function handleEditPost(postId: number) {
    setError('')
    if (imagePreview?.startsWith('blob:')) {
      URL.revokeObjectURL(imagePreview)
    }
    try {
      const post = await telegramService.getPost(postId)
      setPostText(post.post_text ?? '')
      setEditingPostId(postId)
      setPublishAt('')
      setTargetChannels(post.target_channels ?? [])
      setImageFile(null)
      const firstImage = post.images?.[0]
      if (firstImage) {
        if (typeof firstImage === 'string' && (firstImage.startsWith('/uploads/tg/') || firstImage.startsWith('uploads/tg/'))) {
          const filename = firstImage.split('/').pop() ?? firstImage
          const res = await apiClient.get<Blob>(`/tg/uploads/${encodeURIComponent(filename)}`, { responseType: 'blob' })
          setImagePreview(URL.createObjectURL(res.data))
        } else {
          setImagePreview(typeof firstImage === 'string' ? firstImage : null)
        }
      } else {
        setImagePreview(null)
      }
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

    if (postText.length > 4096) {
      setError('Post text cannot exceed 4096 characters')
      setIsCreatingPost(false)
      return
    }

    const publishAtIso = fromDatetimeLocalValue(publishAt)

    try {
      if (editingPostId !== null) {
        await telegramService.updatePost(editingPostId, postText, imageFile || undefined, {
          publishAt: publishAtIso,
          clearPublishAt: !publishAtIso,
          targetChannels: selectedChannels.tg.length ? selectedChannels.tg : undefined,
        })
        setSuccess('Post updated successfully')
        setEditingPostId(null)
        resetPostForm()
        loadPosts()
      } else {
        await telegramService.createPost(postText, imageFile || undefined, postTargets, {
          publishAt: publishAtIso,
          targetChannels: selectedChannels.tg.length ? selectedChannels.tg : undefined,
          targetGroups: selectedChannels.vk.length ? selectedChannels.vk : undefined,
        })
        setSuccess('Post created successfully')
        resetPostForm()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : (editingPostId !== null ? 'Failed to update post' : 'Failed to create post'))
    } finally {
      setIsCreatingPost(false)
    }
  }

  function resetPostForm() {
    setPostText('')
    setPublishAt('')
    setSelectedChannels({ ...EMPTY_SELECTED_BRAND_CHANNELS })
    setImageFile(null)
    if (imagePreview?.startsWith('blob:')) {
      URL.revokeObjectURL(imagePreview)
    }
    setImagePreview(null)
  }

  async function handleApplyTemplate() {
    const template = templates.find((t) => String(t.id) === selectedTemplateId)
    if (!template) return
    const hashtags = template.hashtags.trim()
    const combined = hashtags ? `${template.text}\n\n${hashtags}` : template.text
    setPostText(combined)
  }

  async function handleSaveAsTemplate() {
    const name = window.prompt('Template name:')
    if (!name?.trim()) return
    setIsSavingTemplate(true)
    setError('')
    try {
      const created = await telegramService.createTemplate(name.trim(), postText)
      setTemplates((prev) => [...prev, created])
      setSelectedTemplateId(String(created.id))
      setSuccess('Template saved')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save template')
    } finally {
      setIsSavingTemplate(false)
    }
  }

  async function handleSaveProfile(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    const alertValidationError = validateAlertRules(alertEnabled, alertRules)
    if (alertValidationError) {
      setError(alertValidationError)
      return
    }
    setIsSavingProfile(true)
    try {
      await telegramService.saveConfig(buildProfileConfig())
      await telegramService.reloadBot()
      setSuccess('Profile settings saved successfully')
      setTimeout(loadAuthStatus, 5000)
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
    const alertValidationError = validateAlertRules(alertEnabled, alertRules)
    if (alertValidationError) {
      setError(alertValidationError)
      return
    }
    setIsSavingProfile(true)
    try {
      await telegramService.saveConfig({
        ...buildProfileConfig(),
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
        static_html_content: addStaticHtml ? (staticHtmlContent || undefined)?.slice(0, 1000) : undefined,
      })
      await telegramService.reloadBot()
      setSuccess('Processing settings saved successfully')
      setTimeout(loadAuthStatus, 5000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save processing settings')
    } finally {
      setIsSavingProfile(false)
    }
  }

  function addField(setter: React.Dispatch<React.SetStateAction<DynamicField[]>>) {
    setter((prev) => [...prev, { id: generateId(), value: '', label: '' }])
  }

  function removeField(setter: React.Dispatch<React.SetStateAction<DynamicField[]>>, id: string) {
    setter((prev) => prev.filter((field) => field.id !== id))
  }

  function updateField(
    setter: React.Dispatch<React.SetStateAction<DynamicField[]>>,
    id: string,
    patch: Partial<Pick<DynamicField, 'value' | 'label'>>,
  ) {
    setter((prev) => prev.map((field) => (field.id === id ? { ...field, ...patch } : field)))
  }

  function addAlertRule() {
    setAlertRules((prev) => (prev.length >= MAX_ALERT_RULES ? prev : [...prev, createEmptyAlertRuleBlock()]))
  }

  function removeAlertRule(ruleId: string) {
    setAlertRules((prev) => (prev.length <= 1 ? prev : prev.filter((rule) => rule.id !== ruleId)))
  }

  function updateAlertRule(ruleId: string, patch: Partial<Omit<AlertRuleBlock, 'id' | 'chatsToRead' | 'saveConditions'>>) {
    setAlertRules((prev) => prev.map((rule) => (rule.id === ruleId ? { ...rule, ...patch } : rule)))
  }

  function addAlertRuleField(ruleId: string, field: 'chatsToRead' | 'saveConditions') {
    setAlertRules((prev) =>
      prev.map((rule) => {
        if (rule.id !== ruleId || rule[field].length >= MAX_ALERT_LIST_ITEMS) return rule
        const empty =
          field === 'chatsToRead'
            ? { id: generateId(), value: '', label: '' }
            : { id: generateId(), value: '' }
        return { ...rule, [field]: [...rule[field], empty] }
      }),
    )
  }

  function removeAlertRuleField(ruleId: string, field: 'chatsToRead' | 'saveConditions', fieldId: string) {
    setAlertRules((prev) =>
      prev.map((rule) => {
        if (rule.id !== ruleId || rule[field].length <= 1) return rule
        return { ...rule, [field]: rule[field].filter((item) => item.id !== fieldId) }
      }),
    )
  }

  function updateAlertRuleField(
    ruleId: string,
    field: 'chatsToRead' | 'saveConditions',
    fieldId: string,
    patch: Partial<Pick<DynamicField, 'value' | 'label'>>,
  ) {
    setAlertRules((prev) =>
      prev.map((rule) => {
        if (rule.id !== ruleId) return rule
        return {
          ...rule,
          [field]: rule[field].map((item) => (item.id === fieldId ? { ...item, ...patch } : item)),
        }
      }),
    )
  }

  function handleImageChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) {
      if (imagePreview?.startsWith('blob:')) {
        URL.revokeObjectURL(imagePreview)
      }
      setImageFile(file)
      const reader = new FileReader()
      reader.onloadend = () => setImagePreview(reader.result as string)
      reader.readAsDataURL(file)
    }
  }

  function removeImage() {
    if (imagePreview?.startsWith('blob:')) {
      URL.revokeObjectURL(imagePreview)
    }
    setImageFile(null)
    setImagePreview(null)
  }

  async function handleSubmitAuthCode(e: FormEvent) {
    e.preventDefault()
    if (!user?.id || !authCode.trim()) return
    setIsSubmittingAuth(true)
    setError('')
    try {
      const res = await telegramService.submitAuthCode(user.id, authCode.trim())
      if (res.success) {
        setAuthCode('')
        setSuccess(
          'Telegram авторизован. Дальше: Channels → Recheck у канала → включите Publish / Collect.',
        )
        await loadAuthStatus()
        try {
          const { smmService } = await import('@/services/smm-service')
          // Refresh channel ownership after TG session is live
          const list = await smmService.listAllChannels()
          await Promise.allSettled(
            list
              .filter((c) => c.network === 'tg' && c.role === 'own')
              .map((c) => smmService.recheckChannelAuth(c.id)),
          )
        } catch {
          /* non-blocking */
        }
      } else {
        setError(res.error || res.message || 'Invalid code')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit code')
    } finally {
      setIsSubmittingAuth(false)
    }
  }

  async function handleSubmitAuthPassword(e: FormEvent) {
    e.preventDefault()
    if (!user?.id || !authPassword.trim()) return
    setIsSubmittingAuth(true)
    setError('')
    try {
      const res = await telegramService.submitAuthPassword(user.id, authPassword.trim())
      if (res.success) {
        setAuthPassword('')
        setSuccess(
          'Telegram авторизован (2FA). Дальше: Channels → Recheck у канала → включите Publish / Collect.',
        )
        await loadAuthStatus()
        try {
          const { smmService } = await import('@/services/smm-service')
          const list = await smmService.listAllChannels()
          await Promise.allSettled(
            list
              .filter((c) => c.network === 'tg' && c.role === 'own')
              .map((c) => smmService.recheckChannelAuth(c.id)),
          )
        } catch {
          /* non-blocking */
        }
      } else {
        setError(res.error || res.message || 'Invalid password')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit password')
    } finally {
      setIsSubmittingAuth(false)
    }
  }

  async function handleCheckChannels() {
    if (!user?.id) return
    setChannelsError('')
    setAvailableChannels([])
    setIsCheckingChannels(true)
    try {
      const list = await telegramService.getAvailableChannels(user.id)
      setAvailableChannels(list)
    } catch (err) {
      setChannelsError(err instanceof Error ? err.message : 'Ошибка проверки каналов')
    } finally {
      setIsCheckingChannels(false)
    }
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="Telegram"
        description="Сессия аккаунта для Collect / Publish / Alert. Потоки настраиваются в Channels."
      />

      {error && <Alert variant="error" className="animate-slide-down">{error}</Alert>}
      {success && <Alert variant="success" className="animate-slide-down">{success}</Alert>}

      <TelegramHubMap />

      {canAuth ? (
        <AuthTab
          authStatus={authStatus}
          isLoadingProfile={isLoadingProfile}
          isSavingProfile={isSavingProfile}
          isSubmittingAuth={isSubmittingAuth}
          isCheckingChannels={isCheckingChannels}
          apiId={apiId}
          onApiIdChange={setApiId}
          apiHash={apiHash}
          onApiHashChange={setApiHash}
          telegramUsername={telegramUsername}
          onTelegramUsernameChange={setTelegramUsername}
          authPhoneNumber={authPhoneNumber}
          onAuthPhoneNumberChange={setAuthPhoneNumber}
          authCode={authCode}
          onAuthCodeChange={setAuthCode}
          authPassword={authPassword}
          onAuthPasswordChange={setAuthPassword}
          availableChannels={availableChannels}
          channelsError={channelsError}
          onSaveProfile={handleSaveProfile}
          onLoadAuthStatus={loadAuthStatus}
          onSubmitAuthCode={handleSubmitAuthCode}
          onSubmitAuthPassword={handleSubmitAuthPassword}
          onCheckChannels={handleCheckChannels}
        />
      ) : (
        <Alert variant="info">
          Подключать Telegram-сессию может владелец или админ команды.{' '}
          <Link to="/channels" className="underline">
            К каналам
          </Link>
        </Alert>
      )}
    </PageContainer>
  )
}
