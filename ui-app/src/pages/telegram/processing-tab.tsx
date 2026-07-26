import { FormEvent } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

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
  summarizeEnabled: boolean
  onSummarizeEnabledChange: (v: boolean) => void
  summarizeMinLength: number
  onSummarizeMinLengthChange: (v: number) => void
  digestIntervalMin: number
  onDigestIntervalMinChange: (v: number) => void
  digestChannel: string
  onDigestChannelChange: (v: string) => void
  classificationEnabled: boolean
  onClassificationEnabledChange: (v: boolean) => void
  classificationCategories: string
  onClassificationCategoriesChange: (v: string) => void
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
    summarizeEnabled,
    onSummarizeEnabledChange,
    summarizeMinLength,
    onSummarizeMinLengthChange,
    digestIntervalMin,
    onDigestIntervalMinChange,
    digestChannel,
    onDigestChannelChange,
    classificationEnabled,
    onClassificationEnabledChange,
    classificationCategories,
    onClassificationCategoriesChange,
    onSubmit,
  } = props

  return (
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
      <CardContent>
        {isLoadingProfile ? (
          <div className="text-center py-8 text-[var(--text-muted)]">Loading profile...</div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-6">
            <label className="flex items-center gap-3 cursor-pointer group">
              <div className="relative">
                <input type="checkbox" checked={processEnabled} onChange={(e) => onProcessEnabledChange(e.target.checked)} className="sr-only peer" />
                <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
              </div>
              <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">Обрабатывать перед публикацией</span>
            </label>

            {processEnabled && (
              <div className="space-y-2 animate-slide-down">
                <label className="text-sm font-medium text-[var(--text-secondary)] block">Описание обработки</label>
                <textarea value={processingDescription} onChange={(e) => onProcessingDescriptionChange(e.target.value)} rows={4} className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all" placeholder="Опишите, как должны обрабатываться посты перед публикацией..." />
              </div>
            )}

            <label className="flex items-center gap-3 cursor-pointer group">
              <div className="relative">
                <input type="checkbox" checked={removeEmojis} onChange={(e) => onRemoveEmojisChange(e.target.checked)} className="sr-only peer" />
                <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
              </div>
              <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">Удалить смайлики/эмодзи</span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer group">
              <div className="relative">
                <input type="checkbox" checked={removeImages} onChange={(e) => onRemoveImagesChange(e.target.checked)} className="sr-only peer" />
                <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
              </div>
              <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">Удалить картинки</span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer group">
              <div className="relative">
                <input type="checkbox" checked={cleanHtml} onChange={(e) => onCleanHtmlChange(e.target.checked)} className="sr-only peer" />
                <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
              </div>
              <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">Очистить HTML</span>
            </label>

            <div className="space-y-3">
              <span className="text-sm font-medium text-[var(--text-secondary)] block">Для каких сервисов подготовить обработку</span>
              <div className="flex flex-wrap gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={processServiceWordpress} onChange={(e) => onProcessServiceWordpressChange(e.target.checked)} className="w-4 h-4 text-primary-500 rounded" />
                  <span className="text-[var(--text-primary)]">WordPress</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={processServiceTelegram} onChange={(e) => onProcessServiceTelegramChange(e.target.checked)} className="w-4 h-4 text-primary-500 rounded" />
                  <span className="text-[var(--text-primary)]">Telegram</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={processServiceTwitter} onChange={(e) => onProcessServiceTwitterChange(e.target.checked)} className="w-4 h-4 text-primary-500 rounded" />
                  <span className="text-[var(--text-primary)]">Twitter</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={processServiceVkontakte} onChange={(e) => onProcessServiceVkontakteChange(e.target.checked)} className="w-4 h-4 text-primary-500 rounded" />
                  <span className="text-[var(--text-primary)]">VKontakte</span>
                </label>
              </div>
            </div>

            <label className="flex items-center gap-3 cursor-pointer group">
              <div className="relative">
                <input type="checkbox" checked={statusReviewAfterProcess} onChange={(e) => onStatusReviewAfterProcessChange(e.target.checked)} className="sr-only peer" />
                <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
              </div>
              <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">Перевести пост в статус review после обработки</span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer group">
              <div className="relative">
                <input type="checkbox" checked={addStaticHtml} onChange={(e) => onAddStaticHtmlChange(e.target.checked)} className="sr-only peer" />
                <div className="w-11 h-6 bg-[var(--bg-tertiary)] rounded-full peer-checked:bg-primary-500 transition-colors"></div>
                <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
              </div>
              <span className="text-[var(--text-primary)] group-hover:text-primary-400 transition-colors">Добавлять в посты статичный HTML</span>
            </label>

            {addStaticHtml && (
              <div className="space-y-2 animate-slide-down">
                <label className="text-sm font-medium text-[var(--text-secondary)] block">Статичный HTML (до 1000 символов)</label>
                <textarea value={staticHtmlContent} onChange={(e) => onStaticHtmlContentChange(e.target.value.slice(0, 1000))} rows={4} maxLength={1000} className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all" placeholder="Введите статичный HTML для добавления в посты..." />
                <p className="text-xs text-[var(--text-muted)]">{staticHtmlContent.length} / 1000</p>
              </div>
            )}

            <div className="pt-4 border-t border-[var(--border-color)] space-y-4">
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">AI настройки</h3>
              <label className="flex items-center gap-3 cursor-pointer group">
                <input type="checkbox" checked={summarizeEnabled} onChange={(e) => onSummarizeEnabledChange(e.target.checked)} className="w-4 h-4" />
                <span className="text-[var(--text-primary)]">Суммаризация длинных постов</span>
              </label>
              {summarizeEnabled && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Input label="Min length для суммаризации" type="number" value={summarizeMinLength} onChange={(e) => onSummarizeMinLengthChange(Number(e.target.value) || 500)} />
                  <Input label="Digest interval (min)" type="number" value={digestIntervalMin} onChange={(e) => onDigestIntervalMinChange(Number(e.target.value) || 30)} />
                  <Input label="Digest channel" value={digestChannel} onChange={(e) => onDigestChannelChange(e.target.value)} placeholder="-100..." />
                </div>
              )}
              <label className="flex items-center gap-3 cursor-pointer group">
                <input type="checkbox" checked={classificationEnabled} onChange={(e) => onClassificationEnabledChange(e.target.checked)} className="w-4 h-4" />
                <span className="text-[var(--text-primary)]">AI-классификация сообщений</span>
              </label>
              {classificationEnabled && (
                <Input label="Categories (comma-separated)" value={classificationCategories} onChange={(e) => onClassificationCategoriesChange(e.target.value)} />
              )}
            </div>

            <CardFooter className="px-0">
              <Button type="submit" isLoading={isSavingProfile} className="w-full sm:w-auto">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                Сохранить настройки обработки
              </Button>
            </CardFooter>
          </form>
        )}
      </CardContent>
    </Card>
  )
}
