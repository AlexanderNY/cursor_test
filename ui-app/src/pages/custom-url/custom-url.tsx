import { useState, FormEvent, useEffect, useMemo } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { customURLService } from '@/services/custom-url-service'
import { smmService } from '@/services/smm-service'
import type { URLConfig, CustomURLSettings } from '@/types/custom-url'
import { Switch } from '@/components/ui/switch'
import { useBrand } from '@/contexts/brand-context'

function generateId(): string {
  return crypto.randomUUID?.() || Math.random().toString(36).substring(2, 9)
}

const DEFAULT_SCHEDULE_TIME = '09:00'

function defaultUrlConfig(): URLConfig {
  return {
    id: generateId(),
    url: '',
    xpath: '',
    take_screenshot: false,
    screenshot_format: 'base64',
    target_social_networks: { tg: false, tw: false, vk: false, wp: false },
    target_channels: [],
    target_groups: [],
    schedule_time: DEFAULT_SCHEDULE_TIME,
    run_once: false,
    process_before_publish: false,
    remove_emojis: false,
    remove_images: false,
    clean_html: false,
    screenshot_only: false,
    process_services: [],
    status_review_after_process: false,
    add_static_html: false,
  }
}

function mapUrlFromApi(u: URLConfig): URLConfig {
  return {
    id: u.id || generateId(),
    url: u.url ?? '',
    xpath: u.xpath ?? '',
    take_screenshot: u.take_screenshot ?? false,
    screenshot_format: u.screenshot_format === 'file' ? 'file' : 'base64',
    target_social_networks: {
      tg: u.target_social_networks?.tg ?? false,
      tw: u.target_social_networks?.tw ?? false,
      vk: u.target_social_networks?.vk ?? false,
      wp: u.target_social_networks?.wp ?? false,
    },
    target_channels: Array.isArray(u.target_channels) ? u.target_channels.map(String) : [],
    target_groups: Array.isArray(u.target_groups) ? u.target_groups.map(String) : [],
    schedule_time:
      u.schedule_time ??
      (u as { time_interval?: { start?: string } }).time_interval?.start ??
      DEFAULT_SCHEDULE_TIME,
    run_once: u.run_once ?? false,
    process_before_publish: u.process_before_publish ?? false,
    process_description: u.process_description ?? '',
    remove_emojis: u.remove_emojis ?? false,
    remove_images: u.remove_images ?? false,
    clean_html: u.clean_html ?? false,
    screenshot_only: u.screenshot_only ?? false,
    process_services: Array.isArray(u.process_services) ? u.process_services : [],
    status_review_after_process: u.status_review_after_process ?? false,
    add_static_html: u.add_static_html ?? false,
    static_html_content: (u.static_html_content ?? '').slice(0, 1000),
  }
}

const LEGACY_TAB_REDIRECT: Record<string, string> = {
  posts: '/analytics',
  create: '/posts',
  calendar: '/calendar?network=url',
  profile: '/channels',
  processing: '/channels',
}

function CustomUrlHubMap() {
  const { selectedBrandId } = useBrand()
  const calendarHref = selectedBrandId
    ? `/calendar?brand=${selectedBrandId}&network=url`
    : '/calendar?network=url'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Brand → Channel</CardTitle>
        <CardDescription>
          Здесь список URL-источников. Потоки, очередь и картина по бренду — в общих разделах.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="grid gap-3 sm:grid-cols-2 text-sm">
          <li>
            <Link to="/analytics" className="text-primary-400 hover:underline font-medium">
              Posts → Analytics
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">Собранные материалы смотрите в общей ленте.</p>
          </li>
          <li>
            <Link to={calendarHref} className="text-primary-400 hover:underline font-medium">
              Calendar → общий календарь
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">Расписание публикаций, фильтр network=url.</p>
          </li>
          <li>
            <Link to="/channels" className="text-primary-400 hover:underline font-medium">
              Profile Settings → Channels
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">
              Канал network=URL и цели публикации — в карточке канала.
            </p>
          </li>
          <li>
            <Link to="/channels" className="text-primary-400 hover:underline font-medium">
              Обработка → канал
            </Link>
            <p className="text-[var(--text-muted)] mt-0.5">Настроить → Обработка у конкретного источника.</p>
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

export function CustomURLPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [collectEnabled, setCollectEnabled] = useState(false)
  const [urlConfigs, setUrlConfigs] = useState<URLConfig[]>([defaultUrlConfig()])

  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingSettings, setIsLoadingSettings] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [urlChannelByExternalId, setUrlChannelByExternalId] = useState<Record<string, number>>({})

  useEffect(() => {
    async function loadSettings() {
      setIsLoadingSettings(true)
      try {
        const [settings, allChannels] = await Promise.all([
          customURLService.getSettings(),
          smmService.listAllChannels().catch(() => []),
        ])
        if (settings) {
          setCollectEnabled(settings.collect_enabled ?? false)
          if (settings.urls && settings.urls.length > 0) {
            setUrlConfigs(settings.urls.map(mapUrlFromApi))
          }
        }
        const map: Record<string, number> = {}
        for (const ch of allChannels) {
          if (ch.network === 'url' && ch.external_id) {
            map[String(ch.external_id)] = ch.id
          }
        }
        setUrlChannelByExternalId(map)
      } catch (err) {
        console.error('Failed to load settings:', err)
      } finally {
        setIsLoadingSettings(false)
      }
    }
    loadSettings()
  }, [])

  const linkedChannelCount = useMemo(
    () => Object.keys(urlChannelByExternalId).length,
    [urlChannelByExternalId],
  )

  useEffect(() => {
    const legacyTab = searchParams.get('tab')
    if (legacyTab && LEGACY_TAB_REDIRECT[legacyTab]) {
      navigate(LEGACY_TAB_REDIRECT[legacyTab], { replace: true })
    }
  }, [searchParams, navigate])

  function addUrlConfig() {
    setUrlConfigs([...urlConfigs, defaultUrlConfig()])
  }

  function removeUrlConfig(id: string | undefined) {
    if (!id || urlConfigs.length <= 1) return
    setUrlConfigs(urlConfigs.filter((c) => c.id !== id))
  }

  function updateUrlConfig(id: string | undefined, field: keyof URLConfig, value: unknown) {
    if (!id) return
    setUrlConfigs((prev) =>
      prev.map((config) => {
        if (config.id !== id) return config
        return { ...config, [field]: value }
      })
    )
  }

  function buildFullSettings(): CustomURLSettings {
    return {
      collect_enabled: collectEnabled,
      urls: urlConfigs
        .filter((c) => c.url && c.xpath)
        .map((c) => ({
          id: c.id,
          url: c.url,
          xpath: c.xpath,
          take_screenshot: c.take_screenshot,
          screenshot_format: c.take_screenshot ? (c.screenshot_format ?? 'base64') : undefined,
          target_social_networks: c.target_social_networks,
          target_channels: c.target_channels ?? [],
          target_groups: c.target_groups ?? [],
          schedule_time: c.schedule_time || DEFAULT_SCHEDULE_TIME,
          run_once: c.run_once ?? false,
          process_before_publish: c.process_before_publish ?? false,
          process_description: c.process_description || undefined,
          remove_emojis: c.remove_emojis ?? false,
          remove_images: c.remove_images ?? false,
          clean_html: c.clean_html ?? false,
          process_services: c.process_services ?? [],
          status_review_after_process: c.status_review_after_process ?? false,
          add_static_html: c.add_static_html ?? false,
          static_html_content: c.add_static_html
            ? (c.static_html_content ?? '').slice(0, 1000)
            : undefined,
          screenshot_only: c.screenshot_only ?? false,
        })),
    }
  }

  async function handleSaveSettings(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsLoading(true)
    try {
      const saved = await customURLService.saveSettings(buildFullSettings())
      if (saved?.urls?.length) {
        setUrlConfigs(saved.urls.map(mapUrlFromApi))
      }
      setSuccess('Settings saved successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Custom URL"
        description="Список URL-источников. Потоки настраиваются в Channels."
      />
      {linkedChannelCount > 0 && (
        <p className="mb-4 text-sm text-[var(--text-muted)]">
          Связано с каналами бренда: {linkedChannelCount}
        </p>
      )}

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

      <CustomUrlHubMap />

      <form onSubmit={handleSaveSettings} className="mt-4">
          <Card className="animate-slide-up">
            <CardHeader>
              <CardTitle>Custom URL Settings</CardTitle>
              <CardDescription>
                Список URL для сбора. Для публикации в own-каналы бренда по расписанию используйте
                Channels → URL source → Настроить.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {isLoadingSettings ? (
                <div className="text-center py-8 text-[var(--text-muted)]">Loading...</div>
              ) : (
                <>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <Switch
                        checked={collectEnabled}
                        onChange={(e) => setCollectEnabled(e.target.checked)}
                      />
                    <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                      Enable collection
                    </span>
                  </label>

                  <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">URL Configurations</h3>

                    {urlConfigs.map((config, index) => (
                      <Card key={config.id} className="bg-[var(--bg-secondary)]">
                        <CardContent className="pt-6 space-y-4">
                          <div className="flex items-center justify-between mb-2 gap-2 flex-wrap">
                            <h4 className="text-sm font-medium text-[var(--text-primary)]">
                              URL Configuration {index + 1}
                            </h4>
                            <div className="flex items-center gap-2">
                              {config.id && urlChannelByExternalId[config.id] != null && (
                                <Link to={`/channels/${urlChannelByExternalId[config.id]}`}>
                                  <Button type="button" size="sm" variant="primary">
                                    Настроить в Channels
                                  </Button>
                                </Link>
                              )}
                              {config.id && (
                                <Link to={`/custom-url/${config.id}`}>
                                  <Button type="button" size="sm" variant="secondary">
                                    Legacy flow
                                  </Button>
                                </Link>
                              )}
                              {urlConfigs.length > 1 && (
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => removeUrlConfig(config.id)}
                                  className="px-3 text-red-400 hover:text-red-300"
                                >
                                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                  </svg>
                                </Button>
                              )}
                            </div>
                          </div>
                          <Input
                            label="URL"
                            type="url"
                            value={config.url}
                            onChange={(e) => updateUrlConfig(config.id, 'url', e.target.value)}
                            placeholder="https://example.com"
                          />
                          <Input
                            label="XPath"
                            type="text"
                            value={config.xpath}
                            onChange={(e) => updateUrlConfig(config.id, 'xpath', e.target.value)}
                            placeholder="//div[@class='content']"
                          />
                          <div className="space-y-2 min-w-[8rem]">
                            <label className="text-sm font-medium text-[var(--text-secondary)] block">Время (HH:MM)</label>
                            <Input
                              type="time"
                              value={config.schedule_time ?? ''}
                              onChange={(e) => updateUrlConfig(config.id, 'schedule_time', e.target.value)}
                            />
                          </div>
                          <label className="flex items-center gap-3 cursor-pointer group">
                            <Switch
                                checked={config.run_once ?? false}
                                onChange={(e) => updateUrlConfig(config.id, 'run_once', e.target.checked)}
                              />
                            <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                              Выполнить единоразово
                            </span>
                          </label>
                          <label className="flex items-center gap-3 cursor-pointer group">
                            <Switch
                                checked={config.take_screenshot}
                                onChange={(e) => updateUrlConfig(config.id, 'take_screenshot', e.target.checked)}
                              />
                            <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                              Take screenshot
                            </span>
                          </label>
                          {config.take_screenshot && (
                            <div className="space-y-2 animate-slide-down">
                              <label className="text-sm font-medium text-[var(--text-secondary)] block">Формат картинки</label>
                              <div className="flex gap-4">
                                <label className="flex items-center gap-2 cursor-pointer">
                                  <input
                                    type="radio"
                                    name={`screenshot-format-${config.id}`}
                                    checked={(config.screenshot_format ?? 'base64') === 'base64'}
                                    onChange={() => updateUrlConfig(config.id, 'screenshot_format', 'base64')}
                                    className="w-4 h-4 text-primary-500"
                                  />
                                  <span className="text-[var(--text-primary)]">base64</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer">
                                  <input
                                    type="radio"
                                    name={`screenshot-format-${config.id}`}
                                    checked={config.screenshot_format === 'file'}
                                    onChange={() => updateUrlConfig(config.id, 'screenshot_format', 'file')}
                                    className="w-4 h-4 text-primary-500"
                                  />
                                  <span className="text-[var(--text-primary)]">файл</span>
                                </label>
                              </div>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}

                    <Button type="button" variant="secondary" size="sm" onClick={addUrlConfig} className="w-full sm:w-auto">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      Add URL
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
            <CardFooter>
              <Button type="submit" isLoading={isLoading} className="w-full" disabled={isLoadingSettings}>
                Save Settings
              </Button>
            </CardFooter>
          </Card>
        </form>
    </PageContainer>
  )
}
