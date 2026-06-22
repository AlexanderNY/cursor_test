import { useState, FormEvent, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { customURLService } from '@/services/custom-url-service'
import type { URLConfig, CustomURLSettings, UrlPostListItem } from '@/types/custom-url'

function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}

const DEFAULT_SCHEDULE_TIME = '09:00'

function defaultUrlConfig(): URLConfig & { id: string } {
  return {
    id: generateId(),
    url: '',
    xpath: '',
    take_screenshot: false,
    screenshot_format: 'base64',
    target_social_networks: { tg: false, tw: false, vk: false, wp: false },
    schedule_time: DEFAULT_SCHEDULE_TIME,
    run_once: false,
  }
}

export function CustomURLPage() {
  const [activeTab, setActiveTab] = useState<'urlSettings' | 'processing' | 'posts'>('urlSettings')
  const [collectEnabled, setCollectEnabled] = useState(false)
  const [urlConfigs, setUrlConfigs] = useState<Array<URLConfig & { id: string }>>([defaultUrlConfig()])

  const [processBeforePublish, setProcessBeforePublish] = useState(false)
  const [processDescription, setProcessDescription] = useState('')
  const [removeEmojis, setRemoveEmojis] = useState(false)
  const [removeImages, setRemoveImages] = useState(false)
  const [cleanHtml, setCleanHtml] = useState(false)
  const [screenshotOnly, setScreenshotOnly] = useState(false)
  const [processServiceWordpress, setProcessServiceWordpress] = useState(false)
  const [processServiceTelegram, setProcessServiceTelegram] = useState(false)
  const [processServiceTwitter, setProcessServiceTwitter] = useState(false)
  const [processServiceVkontakte, setProcessServiceVkontakte] = useState(false)
  const [statusReviewAfterProcess, setStatusReviewAfterProcess] = useState(false)
  const [addStaticHtml, setAddStaticHtml] = useState(false)
  const [staticHtmlContent, setStaticHtmlContent] = useState('')

  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingSettings, setIsLoadingSettings] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [posts, setPosts] = useState<UrlPostListItem[]>([])
  const [isLoadingPosts, setIsLoadingPosts] = useState(false)
  const [hasLoadedPosts, setHasLoadedPosts] = useState(false)

  useEffect(() => {
    async function loadSettings() {
      setIsLoadingSettings(true)
      try {
        const settings = await customURLService.getSettings()
        if (settings) {
          setCollectEnabled(settings.collect_enabled ?? false)
          if (settings.urls && settings.urls.length > 0) {
            setUrlConfigs(
              settings.urls.map((u) => ({
                id: generateId(),
                url: u.url ?? '',
                xpath: u.xpath ?? '',
                take_screenshot: u.take_screenshot ?? false,
                screenshot_format: (u as { screenshot_format?: string }).screenshot_format === 'file' ? 'file' : 'base64',
                target_social_networks: {
                  tg: u.target_social_networks?.tg ?? false,
                  tw: u.target_social_networks?.tw ?? false,
                  vk: u.target_social_networks?.vk ?? false,
                  wp: u.target_social_networks?.wp ?? false,
                },
                schedule_time: u.schedule_time ?? (u as { time_interval?: { start?: string } }).time_interval?.start ?? DEFAULT_SCHEDULE_TIME,
                run_once: (u as { run_once?: boolean }).run_once ?? false,
              }))
            )
          }
          setProcessBeforePublish(settings.process_before_publish ?? false)
          setProcessDescription(settings.process_description ?? '')
          setRemoveEmojis(settings.remove_emojis ?? false)
          setRemoveImages(settings.remove_images ?? false)
          setCleanHtml(settings.clean_html ?? false)
          setScreenshotOnly(settings.screenshot_only ?? false)
          const ps = settings.process_services
          if (Array.isArray(ps)) {
            setProcessServiceWordpress(ps.includes('wordpress'))
            setProcessServiceTelegram(ps.includes('telegram'))
            setProcessServiceTwitter(ps.includes('twitter'))
            setProcessServiceVkontakte(ps.includes('vkontakte'))
          }
          setStatusReviewAfterProcess(settings.status_review_after_process ?? false)
          setAddStaticHtml(settings.add_static_html ?? false)
          setStaticHtmlContent((settings.static_html_content ?? '').slice(0, 1000))
        }
      } catch (err) {
        console.error('Failed to load settings:', err)
      } finally {
        setIsLoadingSettings(false)
      }
    }
    loadSettings()
  }, [])

  useEffect(() => {
    if (activeTab === 'posts' && !hasLoadedPosts) {
      loadPosts()
    }
  }, [activeTab, hasLoadedPosts])

  async function loadPosts() {
    setIsLoadingPosts(true)
    try {
      const data = await customURLService.getPosts()
      setPosts(data)
      setHasLoadedPosts(true)
    } catch (err) {
      console.error('Failed to load url posts:', err)
    } finally {
      setIsLoadingPosts(false)
    }
  }

  function addUrlConfig() {
    setUrlConfigs([...urlConfigs, defaultUrlConfig()])
  }

  function removeUrlConfig(id: string) {
    if (urlConfigs.length > 1) {
      setUrlConfigs(urlConfigs.filter((c) => c.id !== id))
    }
  }

  function updateUrlConfig(id: string, field: keyof URLConfig, value: unknown) {
    setUrlConfigs((prev) =>
      prev.map((config) => {
        if (config.id !== id) return config
        if (field === 'target_social_networks' && value && typeof value === 'object') {
          return { ...config, target_social_networks: { ...config.target_social_networks, ...value as object } }
        }
        if (field === 'schedule_time') {
          return { ...config, schedule_time: value as string }
        }
        if (field === 'run_once') {
          return { ...config, run_once: value as boolean }
        }
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
          url: c.url,
          xpath: c.xpath,
          take_screenshot: c.take_screenshot,
          screenshot_format: c.take_screenshot ? (c.screenshot_format ?? 'base64') : undefined,
          target_social_networks: c.target_social_networks,
          schedule_time: c.schedule_time || DEFAULT_SCHEDULE_TIME,
          run_once: c.run_once ?? false,
        })),
      process_before_publish: processBeforePublish,
      process_description: processDescription || undefined,
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
      static_html_content: addStaticHtml ? staticHtmlContent.slice(0, 1000) : undefined,
      screenshot_only: screenshotOnly,
    }
  }

  async function handleSaveSettings(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsLoading(true)
    try {
      await customURLService.saveSettings(buildFullSettings())
      setSuccess('Settings saved successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <PageContainer>
      <PageHeader title="Custom URL Integration" description="Configure custom URL scraping and content collection" />

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
        <button
          type="button"
          className={`px-6 py-3 text-sm font-medium transition-all relative ${
            activeTab === 'urlSettings' ? 'text-primary-400' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => setActiveTab('urlSettings')}
        >
          Настройки URL
          {activeTab === 'urlSettings' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />}
        </button>
        <button
          type="button"
          className={`px-6 py-3 text-sm font-medium transition-all relative ${
            activeTab === 'processing' ? 'text-primary-400' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => setActiveTab('processing')}
        >
          Обработка
          {activeTab === 'processing' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />}
        </button>
        <button
          type="button"
          className={`px-6 py-3 text-sm font-medium transition-all relative ${
            activeTab === 'posts' ? 'text-primary-400' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
          }`}
          onClick={() => setActiveTab('posts')}
        >
          Posts
          {activeTab === 'posts' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />}
        </button>
      </div>

      {activeTab === 'urlSettings' && (
        <form onSubmit={handleSaveSettings}>
          <Card className="animate-slide-up">
            <CardHeader>
              <CardTitle>Custom URL Settings</CardTitle>
              <CardDescription>Configure URL scraping, time interval per URL, and target social networks</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <label className="flex items-center gap-3 cursor-pointer group">
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={collectEnabled}
                    onChange={(e) => setCollectEnabled(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                  <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                </div>
                <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                  Enable collection
                </span>
              </label>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">URL Configurations</h3>
                  <Button type="button" variant="secondary" size="sm" onClick={addUrlConfig}>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Add URL
                  </Button>
                </div>

                {urlConfigs.map((config, index) => (
                  <Card key={config.id} className="bg-[var(--bg-secondary)]">
                    <CardContent className="pt-6 space-y-4">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="text-sm font-medium text-[var(--text-primary)]">URL Configuration {index + 1}</h4>
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
                        <div className="relative">
                          <input
                            type="checkbox"
                            checked={config.run_once ?? false}
                            onChange={(e) => updateUrlConfig(config.id, 'run_once', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                          <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                        </div>
                        <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                          Выполнить единоразово
                        </span>
                      </label>
                      <label className="flex items-center gap-3 cursor-pointer group">
                        <div className="relative">
                          <input
                            type="checkbox"
                            checked={config.take_screenshot}
                            onChange={(e) => updateUrlConfig(config.id, 'take_screenshot', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                          <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                        </div>
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
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-[var(--text-secondary)] block">Target Social Networks</label>
                        <div className="grid grid-cols-2 gap-3">
                          {(['tg', 'tw', 'vk', 'wp'] as const).map((network) => (
                            <label key={network} className="flex items-center gap-3 cursor-pointer group">
                              <div className="relative">
                                <input
                                  type="checkbox"
                                  checked={config.target_social_networks[network] ?? false}
                                  onChange={(e) => updateUrlConfig(config.id, 'target_social_networks', { [network]: e.target.checked })}
                                  className="sr-only peer"
                                />
                                <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                                <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                              </div>
                              <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors uppercase">
                                {network}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
            <CardFooter>
              <Button type="submit" isLoading={isLoading} className="w-full">
                Save Settings
              </Button>
            </CardFooter>
          </Card>
        </form>
      )}

      {activeTab === 'processing' && (
        <form onSubmit={handleSaveSettings}>
          <Card className="animate-slide-up">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Обработка
              </CardTitle>
              <CardDescription>Настройки обработки постов перед публикацией</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {isLoadingSettings ? (
                <div className="text-center py-8 text-[var(--text-muted)]">Loading...</div>
              ) : (
                <>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={processBeforePublish}
                        onChange={(e) => setProcessBeforePublish(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">
                      Обрабатывать перед публикацией
                    </span>
                  </label>

                  {processBeforePublish && (
                    <div className="space-y-2 animate-slide-down">
                      <label className="text-sm font-medium text-[var(--text-secondary)] block">Описание обработки</label>
                      <textarea
                        value={processDescription}
                        onChange={(e) => setProcessDescription(e.target.value)}
                        rows={4}
                        className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                        placeholder="Опишите, как должны обрабатываться посты перед публикацией..."
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
                      <input
                        type="checkbox"
                        checked={screenshotOnly}
                        onChange={(e) => setScreenshotOnly(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">
                      Сохранять только скриншот (без текста)
                    </span>
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
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={processServiceWordpress} onChange={(e) => setProcessServiceWordpress(e.target.checked)} className="w-4 h-4 text-primary-500 rounded" />
                        <span className="text-[var(--text-primary)]">WordPress</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={processServiceTelegram} onChange={(e) => setProcessServiceTelegram(e.target.checked)} className="w-4 h-4 text-primary-500 rounded" />
                        <span className="text-[var(--text-primary)]">Telegram</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={processServiceTwitter} onChange={(e) => setProcessServiceTwitter(e.target.checked)} className="w-4 h-4 text-primary-500 rounded" />
                        <span className="text-[var(--text-primary)]">Twitter</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={processServiceVkontakte} onChange={(e) => setProcessServiceVkontakte(e.target.checked)} className="w-4 h-4 text-primary-500 rounded" />
                        <span className="text-[var(--text-primary)]">VKontakte</span>
                      </label>
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
                    <div className="space-y-2 animate-slide-down">
                      <label className="text-sm font-medium text-[var(--text-secondary)] block">Статичный HTML (до 1000 символов)</label>
                      <textarea
                        value={staticHtmlContent}
                        onChange={(e) => setStaticHtmlContent(e.target.value.slice(0, 1000))}
                        rows={4}
                        maxLength={1000}
                        className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                        placeholder="Введите статичный HTML для добавления в посты..."
                      />
                      <p className="text-xs text-[var(--text-muted)]">{staticHtmlContent.length} / 1000</p>
                    </div>
                  )}

                  <CardFooter className="px-0">
                    <Button type="submit" isLoading={isLoading} className="w-full sm:w-auto">
                      Сохранить настройки обработки
                    </Button>
                  </CardFooter>
                </>
              )}
            </CardContent>
          </Card>
        </form>
      )}

      {activeTab === 'posts' && (
        <Card className="animate-slide-up">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div>
              <CardTitle className="flex items-center gap-2 text-xl">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 text-primary-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 10h16M4 14h10"
                  />
                </svg>
                Posts
              </CardTitle>
              <CardDescription>Собранные посты из настроенных URL (таблица url_posts)</CardDescription>
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
              <div className="text-center py-8 text-[var(--text-muted)]">No posts collected yet.</div>
            )}
            {!isLoadingPosts && posts.length > 0 && (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                      <th className="py-2 pr-4 font-medium">URL</th>
                      <th className="py-2 pr-4 font-medium">Text</th>
                      <th className="py-2 pr-4 font-medium">Images</th>
                      <th className="py-2 pr-4 font-medium">Status</th>
                      <th className="py-2 pr-4 font-medium">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {posts.map((post, index) => (
                      <tr
                        key={post.id ?? index}
                        className="border-b border-[var(--border-color)] last:border-0"
                      >
                        <td className="py-2 pr-4 text-[var(--text-primary)]">
                          <div className="max-w-xs truncate" title={post.url ?? ''}>
                            {post.url || '—'}
                          </div>
                        </td>
                        <td className="py-2 pr-4 text-[var(--text-primary)]">
                          <div className="max-w-md truncate" title={post.post_text}>
                            {post.post_text || '—'}
                          </div>
                        </td>
                        <td className="py-2 pr-4 text-[var(--text-secondary)]">
                          {Array.isArray(post.images) && post.images.length > 0
                            ? `${post.images.length}`
                            : '—'}
                        </td>
                        <td className="py-2 pr-4">
                          <span className="inline-flex items-center rounded-full bg-[var(--bg-secondary)] px-2 py-0.5 text-xs font-medium text-[var(--text-secondary)]">
                            {post.status}
                          </span>
                        </td>
                        <td className="py-2 pr-4 text-[var(--text-secondary)]">
                          {post.created_at ? new Date(post.created_at).toLocaleString() : '—'}
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
    </PageContainer>
  )
}
