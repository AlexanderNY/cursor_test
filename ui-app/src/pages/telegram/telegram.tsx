import { useState, useEffect, FormEvent, useCallback } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { telegramService, type TgAuthStatus } from '@/services/telegram-service'
import { useAuth } from '@/contexts/auth-context'
import { useBrand } from '@/contexts/brand-context'
import type { PublishScheduleType, TelegramChatRef } from '@/types/telegram'
import {
  AUTH_STATUS_POLL_INTERVAL_MS,
  TG_CODE_EXPIRED_ERROR,
  TG_CODE_RESEND_INTERVAL_SEC,
  readTgCodeResendCooldownSec,
  rememberTgCodeResendCooldown,
  generateId,
  SCHEDULE_MINUTES,
  createEmptyAlertRuleBlock,
  mapAlertRulesFromProfile,
  serializeAlertRules,
  validateAlertRules,
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

  const [authStatus, setAuthStatus] = useState<TgAuthStatus | null>(null)
  const [authCode, setAuthCode] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [isSubmittingAuth, setIsSubmittingAuth] = useState(false)
  const [codeExpired, setCodeExpired] = useState(false)
  const [resendCooldownSec, setResendCooldownSec] = useState(0)
  const [isResendingCode, setIsResendingCode] = useState(false)

  const [publishEnabled, setPublishEnabled] = useState(false)
  const [collectEnabled, setCollectEnabled] = useState(false)
  const [publishScheduleType, setPublishScheduleType] = useState<PublishScheduleType>('on_new_messages')
  const [publishScheduleHour, setPublishScheduleHour] = useState(9)
  const [publishScheduleMinute, setPublishScheduleMinute] = useState<ScheduleMinute>(0)
  const [apiId, setApiId] = useState('')
  const [apiHash, setApiHash] = useState('')
  const [telegramUsername, setTelegramUsername] = useState('')
  const [authPhoneNumber, setAuthPhoneNumber] = useState('')
  const [proxyUrl, setProxyUrl] = useState('')
  const [channelToPost, setChannelToPost] = useState('')
  const [channelToPostTitle, setChannelToPostTitle] = useState('')
  const [channelsToPost, setChannelsToPost] = useState<TelegramChatRef[]>([])
  const [alertEnabled, setAlertEnabled] = useState(false)
  const [alertRules, setAlertRules] = useState<AlertRuleBlock[]>(() => [createEmptyAlertRuleBlock()])
  const [chatsToRead, setChatsToRead] = useState<DynamicField[]>([{ id: generateId(), value: '', label: '' }])
  const [saveConditions, setSaveConditions] = useState<DynamicField[]>([{ id: generateId(), value: '' }])
  const [processEnabled, setProcessEnabled] = useState(false)
  const [processingDescription, setProcessingDescription] = useState('')
  const [summarizeEnabled, setSummarizeEnabled] = useState(false)
  const [summarizeMinLength, setSummarizeMinLength] = useState(500)
  const [classificationEnabled, setClassificationEnabled] = useState(false)
  const [classificationCategories, setClassificationCategories] = useState('новости, реклама, технологии, финансы, другое')
  const [batchEnrichmentEnabled, setBatchEnrichmentEnabled] = useState(false)
  const [availableChannels, setAvailableChannels] = useState<AvailableChannel[]>([])
  const [isCheckingChannels, setIsCheckingChannels] = useState(false)
  const [channelsError, setChannelsError] = useState('')

  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [isSavingProfile, setIsSavingProfile] = useState(false)
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

  const resendCooldownActive = resendCooldownSec > 0

  useEffect(() => {
    if (!user?.id) return
    setResendCooldownSec(readTgCodeResendCooldownSec(user.id))
  }, [user?.id])

  useEffect(() => {
    const userId = user?.id
    if (!userId || !resendCooldownActive) return
    const timer = window.setInterval(() => {
      setResendCooldownSec(readTgCodeResendCooldownSec(userId))
    }, 1000)
    return () => window.clearInterval(timer)
  }, [user?.id, resendCooldownActive])

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
        // api_hash is masked as "***" when stored — keep input empty so save does not overwrite.
        const hash = profile.api_hash || ''
        setApiHash(hash && hash !== '***' ? hash : '')
        setTelegramUsername(profile.telegram_username || '')
        setAuthPhoneNumber(profile.auth_phone_number || '')
        setProxyUrl(profile.proxy_url || '')
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
        setSummarizeEnabled(profile.summarize_enabled ?? false)
        setSummarizeMinLength(profile.summarize_min_length ?? 500)
        setClassificationEnabled(profile.classification_enabled ?? false)
        setBatchEnrichmentEnabled(profile.batch_enrichment_enabled ?? false)
        if (profile.classification_categories?.length) {
          setClassificationCategories(profile.classification_categories.join(', '))
        }
      }
    } catch (err) {
      console.log('Profile not found, using defaults', err)
    } finally {
      setIsLoadingProfile(false)
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
      api_hash: apiHash && apiHash !== '***' ? apiHash : undefined,
      telegram_username: telegramUsername || undefined,
      auth_phone_number: authPhoneNumber || undefined,
      proxy_url: proxyUrl.trim() || undefined,
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
      classification_enabled: classificationEnabled,
      classification_categories: classificationCategories.split(',').map((s) => s.trim()).filter(Boolean),
      batch_enrichment_enabled: batchEnrichmentEnabled,
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
        const message = res.error || res.message || 'Invalid code'
        setCodeExpired(message === TG_CODE_EXPIRED_ERROR)
        setError(message)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit code')
    } finally {
      setIsSubmittingAuth(false)
    }
  }

  function applyResendCooldown(seconds: number) {
    if (!user?.id || seconds <= 0) return
    rememberTgCodeResendCooldown(user.id, seconds)
    setResendCooldownSec(readTgCodeResendCooldownSec(user.id))
  }

  async function handleResendAuthCode() {
    if (!user?.id || isResendingCode || resendCooldownSec > 0) return
    setIsResendingCode(true)
    setSuccess('')
    try {
      const res = await telegramService.resendAuthCode(user.id)
      if (res.success) {
        applyResendCooldown(TG_CODE_RESEND_INTERVAL_SEC)
        setCodeExpired(false)
        setAuthCode('')
        setError('')
        setSuccess(res.message || 'Новый код отправлен в Telegram. Проверьте приложение.')
        await loadAuthStatus()
        return
      }
      if (res.retry_after_seconds && res.retry_after_seconds > 0) {
        applyResendCooldown(res.retry_after_seconds)
      }
      setError(res.error || res.message || 'Не удалось запросить код')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось запросить код')
    } finally {
      setIsResendingCode(false)
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
          proxyUrl={proxyUrl}
          onProxyUrlChange={setProxyUrl}
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
          showResendCode={codeExpired && authStatus?.auth_state === 'pending_code'}
          resendCooldownSec={resendCooldownSec}
          isResendingCode={isResendingCode}
          onResendAuthCode={handleResendAuthCode}
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
