import { FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { wordpressService } from '@/services/wordpress-service'
import type { WordPressPublishProfile } from '@/types/wordpress'
import { useAuth } from '@/contexts/auth-context'
import { useBrand } from '@/contexts/brand-context'
import { canManagePlatformAuth } from '@/types/smm'

const LEGACY_TAB_REDIRECT: Record<string, string> = {
  posts: '/analytics',
  create: '/posts',
  calendar: '/calendar?network=wp',
  profile: '/channels',
  processing: '/channels',
}

function WordPressHubMap() {
  const { selectedBrandId } = useBrand()
  const calendarHref = selectedBrandId
    ? `/calendar?brand=${selectedBrandId}&network=wp`
    : '/calendar?network=wp'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Brand → Channel</CardTitle>
        <CardDescription>
          Здесь только доступ к сайту WordPress. Потоки, очередь и картина по бренду — в общих разделах.
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
              Расписание публикаций всех сетей, фильтр network=wp.
            </p>
          </li>
          <li>
            <Link to="/channels" className="text-primary-400 hover:underline font-medium">
              Profile Settings → Channels
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Collect / Publish и цели — в карточке канала, не в профиле WordPress.
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

export function WordPressPage() {
  const { user } = useAuth()
  const hasTeam = Boolean(user?.group_id || user?.role_in_group)
  const canAuth = canManagePlatformAuth(user?.role_in_group, hasTeam)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [flow, setFlow] = useState<WordPressPublishProfile | null>(null)
  const [siteUrl, setSiteUrl] = useState('')
  const [username, setUsername] = useState('')
  const [appPassword, setAppPassword] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    const legacyTab = searchParams.get('tab')
    if (legacyTab && LEGACY_TAB_REDIRECT[legacyTab]) {
      navigate(LEGACY_TAB_REDIRECT[legacyTab], { replace: true })
    }
  }, [searchParams, navigate])

  useEffect(() => {
    async function loadProfile() {
      setIsLoading(true)
      try {
        const profile = await wordpressService.getPublishProfile()
        setFlow(profile)
        setSiteUrl(profile.site_url || '')
        setUsername(profile.username || '')
        const password = profile.app_password || ''
        setAppPassword(password && password !== '***' ? password : '')
      } catch (err) {
        console.error('Failed to load WordPress profile:', err)
        setFlow(null)
      } finally {
        setIsLoading(false)
      }
    }
    void loadProfile()
  }, [])

  async function handleSave(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSaving(true)
    const base = flow
    try {
      await wordpressService.savePublishProfile({
        publish_enabled: base?.publish_enabled ?? false,
        schedule_type: base?.schedule_type,
        time_intervals: base?.time_intervals,
        site_url: siteUrl || undefined,
        username: username || undefined,
        app_password: appPassword && appPassword !== '***' ? appPassword : undefined,
        publish_all_ready: base?.publish_all_ready ?? true,
        publish_limit: base?.publish_limit,
        publish_interval_minutes: base?.publish_interval_minutes,
        process_before_publish: base?.process_before_publish ?? false,
        process_description: base?.process_description,
        remove_emojis: base?.remove_emojis ?? false,
        remove_images: base?.remove_images ?? false,
        clean_html: base?.clean_html ?? false,
        process_services: base?.process_services,
        status_review_after_process: base?.status_review_after_process ?? false,
        add_static_html: base?.add_static_html ?? false,
        static_html_content: base?.static_html_content,
      })
      setAppPassword('')
      setSuccess('Доступ к сайту сохранён. Потоки настраиваются в Channels.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить доступ')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="WordPress"
        description="Доступ к сайту для Collect / Publish. Потоки настраиваются в Channels."
      />

      {error && <Alert variant="error" className="animate-slide-down">{error}</Alert>}
      {success && <Alert variant="success" className="animate-slide-down">{success}</Alert>}

      <WordPressHubMap />

      {canAuth ? (
        <Card className="animate-slide-up mt-4">
          <CardHeader>
            <CardTitle>Доступ к сайту</CardTitle>
            <CardDescription>
              Адрес сайта, пользователь и application password. Публикация и обработка — в карточке канала.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSave}>
            <CardContent className="space-y-4">
              {isLoading ? (
                <p className="text-sm text-[var(--text-muted)]">Загрузка…</p>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  <Input
                    label="Site URL"
                    type="url"
                    value={siteUrl}
                    onChange={(e) => setSiteUrl(e.target.value)}
                    placeholder="https://example.com"
                  />
                  <Input
                    label="Username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    autoComplete="username"
                  />
                  <Input
                    label="Application password"
                    type="password"
                    value={appPassword}
                    onChange={(e) => setAppPassword(e.target.value)}
                    placeholder="Оставьте пустым, чтобы не менять"
                    autoComplete="current-password"
                  />
                </div>
              )}
            </CardContent>
            <CardFooter>
              <Button type="submit" isLoading={isSaving} disabled={isLoading}>
                Сохранить доступ
              </Button>
            </CardFooter>
          </form>
        </Card>
      ) : (
        <Alert variant="info" className="mt-4">
          Подключать WordPress может владелец или админ команды.{' '}
          <Link to="/channels" className="underline">
            К каналам
          </Link>
        </Alert>
      )}
    </PageContainer>
  )
}
