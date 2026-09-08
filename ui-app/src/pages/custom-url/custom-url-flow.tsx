import { FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import {
  TargetSocialNetworksWidget,
  EMPTY_TARGET_SOCIAL_NETWORKS,
  type SelectedBrandChannels,
  type TargetSocialNetworks,
} from '@/components/target-social-networks'
import { customURLService } from '@/services/custom-url-service'
import type { CustomURLSettings, URLConfig } from '@/types/custom-url'
import { getErrorMessage } from '@/services/api-client'

type FlowTab = 'collect' | 'processing' | 'publish'

const DEFAULT_SCHEDULE_TIME = '09:00'

function emptyItem(id: string): URLConfig {
  return {
    id,
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
    process_description: '',
    remove_emojis: false,
    remove_images: false,
    clean_html: false,
    screenshot_only: false,
    process_services: [],
    status_review_after_process: false,
    add_static_html: false,
    static_html_content: '',
  }
}

function toWidgetTargets(item: URLConfig): TargetSocialNetworks {
  return {
    ...EMPTY_TARGET_SOCIAL_NETWORKS,
    tg: item.target_social_networks?.tg ?? false,
    tw: item.target_social_networks?.tw ?? false,
    vk: item.target_social_networks?.vk ?? false,
    wp: item.target_social_networks?.wp ?? false,
  }
}

function toSelectedChannels(item: URLConfig): SelectedBrandChannels {
  return {
    tg: Array.isArray(item.target_channels) ? item.target_channels.map(String) : [],
    vk: Array.isArray(item.target_groups) ? item.target_groups.map(String) : [],
  }
}

export function CustomUrlFlowPage() {
  const { configId } = useParams()
  const navigate = useNavigate()

  const [tab, setTab] = useState<FlowTab>('collect')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const [settings, setSettings] = useState<CustomURLSettings | null>(null)
  const [item, setItem] = useState<URLConfig | null>(null)

  useEffect(() => {
    if (!configId) {
      setError('Invalid config id')
      setLoading(false)
      return
    }
    void (async () => {
      setLoading(true)
      setError('')
      try {
        const data = await customURLService.getSettings()
        if (!data) {
          setError('Settings not found')
          setLoading(false)
          return
        }
        setSettings(data)
        const found = (data.urls || []).find((u) => u.id === configId)
        if (!found) {
          setError('URL configuration not found')
          setItem(null)
        } else {
          setItem({
            ...emptyItem(configId),
            ...found,
            id: found.id || configId,
            target_social_networks: {
              tg: found.target_social_networks?.tg ?? false,
              tw: found.target_social_networks?.tw ?? false,
              vk: found.target_social_networks?.vk ?? false,
              wp: found.target_social_networks?.wp ?? false,
            },
            target_channels: Array.isArray(found.target_channels)
              ? found.target_channels.map(String)
              : [],
            target_groups: Array.isArray(found.target_groups)
              ? found.target_groups.map(String)
              : [],
            process_services: Array.isArray(found.process_services) ? found.process_services : [],
            process_description: found.process_description ?? '',
            static_html_content: (found.static_html_content ?? '').slice(0, 1000),
            schedule_time: found.schedule_time || DEFAULT_SCHEDULE_TIME,
          })
        }
      } catch (err) {
        setError(getErrorMessage(err))
      } finally {
        setLoading(false)
      }
    })()
  }, [configId])

  function patchItem(partial: Partial<URLConfig>) {
    setItem((prev) => (prev ? { ...prev, ...partial } : prev))
  }

  function processServicesIncludes(name: string): boolean {
    return (item?.process_services || []).includes(name)
  }

  function setProcessService(name: string, enabled: boolean) {
    if (!item) return
    const set = new Set(item.process_services || [])
    if (enabled) set.add(name)
    else set.delete(name)
    patchItem({ process_services: Array.from(set) })
  }

  async function persistItem(e: FormEvent, successMsg: string) {
    e.preventDefault()
    if (!settings || !item || !configId) return
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const urls = (settings.urls || []).map((u) =>
        u.id === configId
          ? {
              ...u,
              ...item,
              id: configId,
              screenshot_format: item.take_screenshot
                ? (item.screenshot_format ?? 'base64')
                : undefined,
              process_description: item.process_description || undefined,
              static_html_content: item.add_static_html
                ? (item.static_html_content ?? '').slice(0, 1000)
                : undefined,
              target_channels: item.target_channels ?? [],
              target_groups: item.target_groups ?? [],
            }
          : u,
      )
      const payload: CustomURLSettings = {
        collect_enabled: settings.collect_enabled,
        urls,
      }
      const saved = await customURLService.saveSettings(payload)
      setSettings(saved)
      const updated = (saved.urls || []).find((u) => u.id === configId)
      if (updated) {
        setItem({
          ...emptyItem(configId),
          ...updated,
          id: configId,
          process_description: updated.process_description ?? '',
          static_html_content: (updated.static_html_content ?? '').slice(0, 1000),
          process_services: Array.isArray(updated.process_services) ? updated.process_services : [],
          target_channels: Array.isArray(updated.target_channels)
            ? updated.target_channels.map(String)
            : [],
          target_groups: Array.isArray(updated.target_groups)
            ? updated.target_groups.map(String)
            : [],
          target_social_networks: {
            tg: updated.target_social_networks?.tg ?? false,
            tw: updated.target_social_networks?.tw ?? false,
            vk: updated.target_social_networks?.vk ?? false,
            wp: updated.target_social_networks?.wp ?? false,
          },
        })
      }
      setSuccess(successMsg)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const tabs: { id: FlowTab; label: string }[] = [
    { id: 'collect', label: 'Сбор' },
    { id: 'processing', label: 'Обработка' },
    { id: 'publish', label: 'Публикация' },
  ]

  return (
    <PageContainer>
      <div className="mb-4">
        <Button type="button" variant="ghost" size="sm" onClick={() => navigate('/custom-url')}>
          ← Назад к списку
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="ml-2"
          onClick={() => navigate('/channels')}
        >
          Channels
        </Button>
      </div>
      <PageHeader
        title="Настройка Custom URL"
        description={item?.url ? item.url : 'Сбор · Обработка · Публикация'}
      />

      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      {loading ? (
        <p className="text-sm text-[var(--text-muted)]">Загрузка…</p>
      ) : !item ? (
        <Card>
          <CardContent className="py-6">
            <p className="text-sm text-[var(--text-secondary)] mb-4">Конфигурация не найдена.</p>
            <Link to="/custom-url" className="text-primary-400 hover:underline text-sm">
              Вернуться к Custom URL
            </Link>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="flex border-b border-[var(--border-color)] mb-4">
            {tabs.map((t) => (
              <button
                key={t.id}
                type="button"
                className={`px-6 py-3 text-sm font-medium transition-all relative ${
                  tab === t.id ? 'text-primary-400' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
                onClick={() => setTab(t.id)}
              >
                {t.label}
                {tab === t.id && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500" />}
              </button>
            ))}
          </div>

          {tab === 'collect' && (
            <form onSubmit={(e) => void persistItem(e, 'Настройки сбора сохранены')}>
              <Card>
                <CardHeader>
                  <CardTitle>Сбор</CardTitle>
                  <CardDescription>URL, XPath, расписание и скриншот</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input
                    label="URL"
                    type="url"
                    value={item.url}
                    onChange={(e) => patchItem({ url: e.target.value })}
                    placeholder="https://example.com"
                  />
                  <Input
                    label="XPath"
                    type="text"
                    value={item.xpath}
                    onChange={(e) => patchItem({ xpath: e.target.value })}
                    placeholder="//div[@class='content']"
                  />
                  <div className="space-y-2 min-w-[8rem]">
                    <label className="text-sm font-medium text-[var(--text-secondary)] block">Время (HH:MM)</label>
                    <Input
                      type="time"
                      value={item.schedule_time ?? ''}
                      onChange={(e) => patchItem({ schedule_time: e.target.value })}
                    />
                  </div>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={item.run_once ?? false}
                        onChange={(e) => patchItem({ run_once: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">Выполнить единоразово</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={item.take_screenshot}
                        onChange={(e) => patchItem({ take_screenshot: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">Take screenshot</span>
                  </label>
                  {item.take_screenshot && (
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          checked={(item.screenshot_format ?? 'base64') === 'base64'}
                          onChange={() => patchItem({ screenshot_format: 'base64' })}
                          className="w-4 h-4 text-primary-500"
                        />
                        <span className="text-[var(--text-primary)]">base64</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          checked={item.screenshot_format === 'file'}
                          onChange={() => patchItem({ screenshot_format: 'file' })}
                          className="w-4 h-4 text-primary-500"
                        />
                        <span className="text-[var(--text-primary)]">файл</span>
                      </label>
                    </div>
                  )}
                </CardContent>
                <CardFooter>
                  <Button type="submit" isLoading={saving}>
                    Сохранить
                  </Button>
                </CardFooter>
              </Card>
            </form>
          )}

          {tab === 'processing' && (
            <form onSubmit={(e) => void persistItem(e, 'Обработка сохранена')}>
              <Card>
                <CardHeader>
                  <CardTitle>Обработка</CardTitle>
                  <CardDescription>Настройки обработки только для этого URL</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={item.process_before_publish ?? false}
                        onChange={(e) => patchItem({ process_before_publish: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">Обрабатывать перед публикацией</span>
                  </label>

                  {item.process_before_publish && (
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-[var(--text-secondary)] block">
                        Описание обработки
                      </label>
                      <textarea
                        value={item.process_description ?? ''}
                        onChange={(e) => patchItem({ process_description: e.target.value })}
                        rows={4}
                        className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                        placeholder="Опишите, как должны обрабатываться посты перед публикацией..."
                      />
                    </div>
                  )}

                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={item.remove_emojis ?? false}
                        onChange={(e) => patchItem({ remove_emojis: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">Удалить смайлики/эмодзи</span>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={item.remove_images ?? false}
                        onChange={(e) => patchItem({ remove_images: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">Удалить картинки</span>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={item.screenshot_only ?? false}
                        onChange={(e) => patchItem({ screenshot_only: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">Сохранять только скриншот (без текста)</span>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={item.clean_html ?? false}
                        onChange={(e) => patchItem({ clean_html: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">Очистить HTML</span>
                  </label>

                  <div className="space-y-3">
                    <span className="text-sm font-medium text-[var(--text-secondary)] block">
                      Для каких сервисов подготовить обработку
                    </span>
                    <div className="flex flex-wrap gap-4">
                      {(
                        [
                          ['wordpress', 'WordPress'],
                          ['telegram', 'Telegram'],
                          ['twitter', 'Twitter'],
                          ['vkontakte', 'VKontakte'],
                        ] as const
                      ).map(([key, label]) => (
                        <label key={key} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={processServicesIncludes(key)}
                            onChange={(e) => setProcessService(key, e.target.checked)}
                            className="w-4 h-4 text-primary-500 rounded"
                          />
                          <span className="text-[var(--text-primary)]">{label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={item.status_review_after_process ?? false}
                        onChange={(e) => patchItem({ status_review_after_process: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">Перевести пост в статус review после обработки</span>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={item.add_static_html ?? false}
                        onChange={(e) => patchItem({ add_static_html: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors" />
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                    </div>
                    <span className="text-[var(--text-primary)]">Добавлять в посты статичный HTML</span>
                  </label>

                  {item.add_static_html && (
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-[var(--text-secondary)] block">
                        Статичный HTML (до 1000 символов)
                      </label>
                      <textarea
                        value={item.static_html_content ?? ''}
                        onChange={(e) => patchItem({ static_html_content: e.target.value.slice(0, 1000) })}
                        rows={4}
                        maxLength={1000}
                        className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
                        placeholder="Введите статичный HTML для добавления в посты..."
                      />
                      <p className="text-xs text-[var(--text-muted)]">
                        {(item.static_html_content ?? '').length} / 1000
                      </p>
                    </div>
                  )}
                </CardContent>
                <CardFooter>
                  <Button type="submit" isLoading={saving}>
                    Сохранить
                  </Button>
                </CardFooter>
              </Card>
            </form>
          )}

          {tab === 'publish' && (
            <form onSubmit={(e) => void persistItem(e, 'Цели публикации сохранены')}>
              <Card>
                <CardHeader>
                  <CardTitle>Публикация</CardTitle>
                  <CardDescription>
                    Выберите сети и доступные own-каналы бренда (publish_enabled), куда уйдёт контент
                    с этого URL.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <TargetSocialNetworksWidget
                    value={toWidgetTargets(item)}
                    onChange={(next) =>
                      patchItem({
                        target_social_networks: {
                          tg: next.tg,
                          tw: next.tw,
                          vk: next.vk,
                          wp: next.wp,
                        },
                        ...(next.tg ? {} : { target_channels: [] }),
                        ...(next.vk ? {} : { target_groups: [] }),
                      })
                    }
                    selectedChannels={toSelectedChannels(item)}
                    onSelectedChannelsChange={(next) =>
                      patchItem({
                        target_channels: next.tg,
                        target_groups: next.vk,
                        target_social_networks: {
                          ...item.target_social_networks,
                          tg: next.tg.length > 0 || Boolean(item.target_social_networks?.tg),
                          vk: next.vk.length > 0 || Boolean(item.target_social_networks?.vk),
                        },
                      })
                    }
                    disabled={{
                      instagram: true,
                      threads: true,
                      dzen: true,
                    }}
                  />
                  {((item.target_channels?.length ?? 0) > 0 || (item.target_groups?.length ?? 0) > 0) && (
                    <p className="text-xs text-[var(--text-muted)]">
                      Выбрано каналов: TG {item.target_channels?.length ?? 0}
                      {item.target_groups && item.target_groups.length > 0
                        ? ` · VK ${item.target_groups.length}`
                        : ''}
                    </p>
                  )}
                </CardContent>
                <CardFooter>
                  <Button type="submit" isLoading={saving}>
                    Сохранить
                  </Button>
                </CardFooter>
              </Card>
            </form>
          )}
        </>
      )}
    </PageContainer>
  )
}
