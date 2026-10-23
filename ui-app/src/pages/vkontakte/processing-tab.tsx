import { FormEvent } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'

export interface ProcessingTabProps {
  isLoadingProfile: boolean
  isSavingProfile: boolean
  processEnabled: boolean
  onProcessEnabledChange: (v: boolean) => void
  processingDescription: string
  onProcessingDescriptionChange: (v: string) => void
  removeEmojis: boolean
  onRemoveEmojisChange: (v: boolean) => void
  removeImages: boolean
  onRemoveImagesChange: (v: boolean) => void
  cleanHtml: boolean
  onCleanHtmlChange: (v: boolean) => void
  processServiceWordpress: boolean
  onProcessServiceWordpressChange: (v: boolean) => void
  processServiceTelegram: boolean
  onProcessServiceTelegramChange: (v: boolean) => void
  processServiceTwitter: boolean
  onProcessServiceTwitterChange: (v: boolean) => void
  processServiceVkontakte: boolean
  onProcessServiceVkontakteChange: (v: boolean) => void
  statusReviewAfterProcess: boolean
  onStatusReviewAfterProcessChange: (v: boolean) => void
  addStaticHtml: boolean
  onAddStaticHtmlChange: (v: boolean) => void
  staticHtmlContent: string
  onStaticHtmlContentChange: (v: string) => void
  onSubmit: (e: FormEvent) => void
}

export function ProcessingTab(props: ProcessingTabProps) {
  const {
    isLoadingProfile,
    isSavingProfile,
    processEnabled,
    onProcessEnabledChange,
    processingDescription,
    onProcessingDescriptionChange,
    removeEmojis,
    onRemoveEmojisChange,
    removeImages,
    onRemoveImagesChange,
    cleanHtml,
    onCleanHtmlChange,
    processServiceWordpress,
    onProcessServiceWordpressChange,
    processServiceTelegram,
    onProcessServiceTelegramChange,
    processServiceTwitter,
    onProcessServiceTwitterChange,
    processServiceVkontakte,
    onProcessServiceVkontakteChange,
    statusReviewAfterProcess,
    onStatusReviewAfterProcessChange,
    addStaticHtml,
    onAddStaticHtmlChange,
    staticHtmlContent,
    onStaticHtmlContentChange,
    onSubmit,
  } = props

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle>Обработка</CardTitle>
        <CardDescription>Настройки обработки постов перед публикацией</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoadingProfile ? (
          <div className="text-center py-8 text-[var(--text-muted)]">Loading profile...</div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-6">
            <label className="flex items-center gap-3 cursor-pointer group">
              <Switch
                  checked={processEnabled}
                  onChange={(e) => onProcessEnabledChange(e.target.checked)}
                />
              <span className="text-[var(--text-primary)]">Обрабатывать перед публикацией</span>
            </label>
            {processEnabled && (
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                  Описание обработки
                </label>
                <textarea
                  value={processingDescription}
                  onChange={(e) => onProcessingDescriptionChange(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                  placeholder="Опишите, как должны обрабатываться посты..."
                />
              </div>
            )}
            <label className="flex items-center gap-3 cursor-pointer group">
              <Switch
                  checked={removeEmojis}
                  onChange={(e) => onRemoveEmojisChange(e.target.checked)}
                />
              <span className="text-[var(--text-primary)]">Удалить смайлики/эмодзи</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer group">
              <Switch
                  checked={removeImages}
                  onChange={(e) => onRemoveImagesChange(e.target.checked)}
                />
              <span className="text-[var(--text-primary)]">Удалить картинки</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer group">
              <Switch
                  checked={cleanHtml}
                  onChange={(e) => onCleanHtmlChange(e.target.checked)}
                />
              <span className="text-[var(--text-primary)]">Очистить HTML</span>
            </label>
            <div className="space-y-3">
              <span className="text-sm font-medium text-[var(--text-secondary)] block">
                Для каких сервисов подготовить обработку
              </span>
              <div className="flex flex-wrap gap-4">
                {(['wordpress', 'telegram', 'twitter', 'vkontakte'] as const).map((name) => (
                  <label key={name} className="flex items-center gap-2 cursor-pointer">
                    <Switch
                      checked={
                        name === 'wordpress'
                          ? processServiceWordpress
                          : name === 'telegram'
                            ? processServiceTelegram
                            : name === 'twitter'
                              ? processServiceTwitter
                              : processServiceVkontakte
                      }
                      onChange={(e) => {
                        if (name === 'wordpress') onProcessServiceWordpressChange(e.target.checked)
                        else if (name === 'telegram') onProcessServiceTelegramChange(e.target.checked)
                        else if (name === 'twitter') onProcessServiceTwitterChange(e.target.checked)
                        else onProcessServiceVkontakteChange(e.target.checked)
                      }}
                    />
                    <span className="text-[var(--text-primary)]">
                      {name === 'vkontakte' ? 'VKontakte' : name.charAt(0).toUpperCase() + name.slice(1)}
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <label className="flex items-center gap-3 cursor-pointer group">
              <Switch
                  checked={statusReviewAfterProcess}
                  onChange={(e) => onStatusReviewAfterProcessChange(e.target.checked)}
                />
              <span className="text-[var(--text-primary)]">Перевести пост в статус review после обработки</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer group">
              <Switch
                  checked={addStaticHtml}
                  onChange={(e) => onAddStaticHtmlChange(e.target.checked)}
                />
              <span className="text-[var(--text-primary)]">Добавлять в посты статичный HTML</span>
            </label>
            {addStaticHtml && (
              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                  Статичный HTML (до 1000 символов)
                </label>
                <textarea
                  value={staticHtmlContent}
                  onChange={(e) => onStaticHtmlContentChange(e.target.value.slice(0, 1000))}
                  rows={4}
                  maxLength={1000}
                  className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                />
                <p className="text-xs text-[var(--text-muted)]">{staticHtmlContent.length} / 1000</p>
              </div>
            )}
            <CardFooter className="px-0">
              <Button type="submit" isLoading={isSavingProfile}>
                Сохранить настройки обработки
              </Button>
            </CardFooter>
          </form>
        )}
      </CardContent>
    </Card>
  )
}
