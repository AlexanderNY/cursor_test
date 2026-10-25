import { useState, FormEvent, useEffect, useCallback, useRef } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import axios from 'axios'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { dzenService } from '@/services/dzen-service'
import { getErrorMessage } from '@/services/api-client'
import { useAuth } from '@/contexts/auth-context'
import { useBrand } from '@/contexts/brand-context'
import { canManagePlatformAuth } from '@/types/smm'
import type {
  DzenProfile,
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

const LEGACY_TAB_REDIRECT: Record<string, string> = {
  posts: '/analytics',
  create: '/posts',
  calendar: '/calendar?network=dzen',
  profile: '/channels',
  processing: '/channels',
}

function DzenHubMap() {
  const { selectedBrandId } = useBrand()
  const calendarHref = selectedBrandId
    ? `/calendar?brand=${selectedBrandId}&network=dzen`
    : '/calendar?network=dzen'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Brand → Channel</CardTitle>
        <CardDescription>
          Здесь только сессия Яндекс ID. Потоки, очередь и картина по бренду — в общих разделах.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="grid gap-3 sm:grid-cols-2 text-sm">
          <li>
            <Link to="/analytics" className="text-primary-400 hover:underline font-medium">
              Posts → Analytics
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">Лента и события по каналам бренда.</p>
          </li>
          <li>
            <Link to={calendarHref} className="text-primary-400 hover:underline font-medium">
              Calendar → общий календарь
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Расписание публикаций всех сетей, фильтр network=dzen.
            </p>
          </li>
          <li>
            <Link to="/channels" className="text-primary-400 hover:underline font-medium">
              Profile Settings → Channels
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Collect / Publish и RSS-источники — в карточке канала.
            </p>
          </li>
          <li>
            <Link to="/channels" className="text-primary-400 hover:underline font-medium">
              Обработка → канал
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">Настроить → Обработка у конкретного канала.</p>
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

export function DzenPage() {
  const { user } = useAuth()
  const hasTeam = Boolean(user?.group_id || user?.role_in_group)
  const canAuth = canManagePlatformAuth(user?.role_in_group, hasTeam)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

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
  const [yandexFirstName, setYandexFirstName] = useState('')
  const [yandexLastName, setYandexLastName] = useState('')
  const [dzenStudioUrl, setDzenStudioUrl] = useState('')
  const [collectSource, setCollectSource] = useState<DzenCollectSource>('rss')
  const [lastAuthError, setLastAuthError] = useState<string | null>(null)
  const [yandexSessionSavedAt, setYandexSessionSavedAt] = useState<string | null>(null)

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
      setYandexSessionSavedAt(null)
      if (profile) {
        setLastAuthError(profile.last_auth_error ?? null)
        setYandexSessionSavedAt(profile.yandex_session_saved_at ?? null)
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
        setYandexFirstName(profile.yandex_first_name ?? '')
        setYandexLastName(profile.yandex_last_name ?? '')
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
    const legacyTab = searchParams.get('tab')
    if (legacyTab && LEGACY_TAB_REDIRECT[legacyTab]) {
      navigate(LEGACY_TAB_REDIRECT[legacyTab], { replace: true })
    }
  }, [searchParams, navigate])

  useEffect(() => {
    const stored = readStoredDiagUrl()
    if (stored) {
      setVerifyDiagImageUrl(stored)
      setDiagImageLoadError(false)
    }
  }, [])

  useEffect(() => {
    return () => {
      liveDiagActiveRef.current = false
      liveDiagGenerationRef.current += 1
    }
  }, [])

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
      yandex_first_name: yandexFirstName || undefined,
      yandex_last_name: yandexLastName || undefined,
      dzen_studio_url: dzenStudioUrl || undefined,
      collect_source: collectSource,
    }
    if (yandexPassword.length > 0) {
      payload.yandex_password = yandexPassword
    }
    return payload
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
          }
          if (diag.message) {
            setVerifyInfoMessage(diag.message)
          } else if (diag.need_push_code) {
            setVerifyInfoMessage('На телефон отправлен код. Введите 6 цифр.')
          }
          if (diag.diag_image_url) {
            setDiagFromResponse(diag.diag_image_url, false)
          }
        } catch {
          /* keep polling */
        }
        await sleep(1500)
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
          await sleep(1500)
        }
        first = false
        try {
          const diag = await dzenService.fetchVerifyPendingDiag()
          if (diag.need_push_code) {
            setNeedPushCode(true)
          }
          if (diag.message) {
            setVerifyInfoMessage(diag.message)
          } else if (diag.need_push_code) {
            setVerifyInfoMessage('На телефон отправлен код. Введите 6 цифр.')
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
    const phone = yandexLogin.trim()
    if (!phone) {
      setError('Укажите телефон Яндекс для входа (может отличаться от Telegram/VK).')
      return
    }
    setError('')
    setSuccess('')
    setVerifyInfoMessage(null)
    setNeedPushCode(false)
    setPushCode('')
    setVerifySubscriptions([])
    setIsVerifyingAuth(true)
    startLiveDiagStream()
    try {
      // Сохраняем телефон/ФИО с формы перед проверкой
      try {
        await dzenService.saveProfile(buildProfilePayload())
      } catch {
        /* start всё равно передаст phone в body */
      }
      const res = await dzenService.verifyYandexStart(phone)
      await loadProfile()
      if (res.ok && res.need_push_code) {
        setNeedPushCode(true)
        setVerifyInfoMessage(res.message ?? 'На телефон отправлен код. Введите 6 цифр.')
        setDiagFromResponse(res.diag_image_url, false)
        // live-стрим продолжает показывать экран SMS-кода ~1.5 с
        return
      }
      stopLiveDiagStream()
      applyVerifyResponse(res)
    } catch (err) {
      setVerifySubscriptions([])
      if (isTimeoutError(err)) {
        setError(
          'Превышен таймаут ожидания ответа. На экране — live-снимок браузера бота (обновление ~1.5 с).'
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
    const code = pushCode.trim().replace(/\D/g, '')
    if (!code) {
      setError('Введите код из SMS.')
      return
    }
    if (code.length !== 6) {
      setError('Код должен содержать ровно 6 цифр.')
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
          'Превышен таймаут после отправки кода. Live-скрин бота продолжает обновляться ~1.5 с.'
        )
      } else {
        setError(getErrorMessage(err) || 'Ошибка отправки кода')
      }
    } finally {
      setIsVerifyingAuth(false)
    }
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="Яндекс Дзен"
        description="Сессия Яндекс ID для публикации. Потоки настраиваются в Channels."
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

      <DzenHubMap />

      {canAuth ? (
        <Card className="animate-slide-up">
          <CardHeader>
            <CardTitle>Авторизация Яндекс</CardTitle>
            <CardDescription>
              Вход через dzen.ru → Яндекс ID по телефону и SMS. Перед проверкой укажите телефон Яндекса
              (он может отличаться от номера в Telegram/VK). Пароль и ФИО — по необходимости.
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
                <Alert variant={yandexSessionSavedAt ? 'success' : 'info'} className="text-sm">
                  {yandexSessionSavedAt
                    ? `Сессия сохранена ${new Date(yandexSessionSavedAt).toLocaleString('ru-RU')}. Публикация новых постов использует эту сессию.`
                    : 'Сессии нет — публикация ждёт проверку авторизации.'}
                </Alert>
                <form onSubmit={handleSaveCredentials} className="space-y-4">
                  <Input
                    label="Телефон Яндекс (для этой проверки)"
                    value={yandexLogin}
                    onChange={(e) => setYandexLogin(e.target.value)}
                    placeholder="79001234567"
                    autoComplete="tel"
                    inputMode="tel"
                    required
                  />
                  <p className="text-xs text-[var(--text-muted)] -mt-2">
                    Введите номер, на который придёт SMS от Яндекса. Не подставляется из Telegram/VK.
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input
                      label="Имя"
                      value={yandexFirstName}
                      onChange={(e) => setYandexFirstName(e.target.value)}
                      placeholder="Имя"
                      autoComplete="given-name"
                    />
                    <Input
                      label="Фамилия"
                      value={yandexLastName}
                      onChange={(e) => setYandexLastName(e.target.value)}
                      placeholder="Фамилия"
                      autoComplete="family-name"
                    />
                  </div>
                  <Input
                    label="Пароль Яндекс (опционально)"
                    type="password"
                    value={yandexPassword}
                    onChange={(e) => setYandexPassword(e.target.value)}
                    placeholder="Оставьте пустым, чтобы не менять сохранённый"
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
                        ? 'Live: экран браузера бота (обновление ~1.5 с, снимок на каждом шаге)'
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
                    <p className="text-sm text-[var(--text-primary)]">
                      На телефон отправлен код. Введите 6 цифр из SMS.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
                      <div className="flex-1">
                        <Input
                          label="Код из SMS"
                          value={pushCode}
                          onChange={(e) =>
                            setPushCode(e.target.value.replace(/\D/g, '').slice(0, 6))
                          }
                          placeholder="123456"
                          inputMode="numeric"
                          autoComplete="one-time-code"
                          maxLength={6}
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
      ) : (
        <Alert variant="info">
          Подключать Дзен может владелец или админ команды.{' '}
          <Link to="/channels" className="underline">
            К каналам
          </Link>
        </Alert>
      )}
    </PageContainer>
  )
}
