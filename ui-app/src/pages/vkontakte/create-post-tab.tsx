import { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { TipTapEditor } from '@/components/ui/tiptap-editor'
import {
  TargetSocialNetworksWidget,
  type TargetSocialNetworks,
  type SelectedBrandChannels,
} from '@/components/target-social-networks'
import { VK_MAX_LENGTH, htmlToPlainText } from './vkontakte-helpers'

export interface CreatePostTabProps {
  postContent: string
  onPostContentChange: (v: string) => void
  postImages: string[]
  onRemoveImage: (index: number) => void
  onUploadImages: (files: FileList) => Promise<void>
  uploadingImage: boolean
  imagePreviewUrl: (url: string) => string
  editingPostId: number | null
  publishAt: string
  onPublishAtChange: (v: string) => void
  targetGroupsText: string
  onTargetGroupsTextChange: (v: string) => void
  postTargets: TargetSocialNetworks
  onPostTargetsChange: (v: TargetSocialNetworks) => void
  selectedChannels: SelectedBrandChannels
  onSelectedChannelsChange: (v: SelectedBrandChannels) => void
  isCreatingPost: boolean
  onSubmit: (e: FormEvent) => void
}

export function CreatePostTab({
  postContent,
  onPostContentChange,
  postImages,
  onRemoveImage,
  onUploadImages,
  uploadingImage,
  imagePreviewUrl,
  editingPostId,
  publishAt,
  onPublishAtChange,
  targetGroupsText,
  onTargetGroupsTextChange,
  postTargets,
  onPostTargetsChange,
  selectedChannels,
  onSelectedChannelsChange,
  isCreatingPost,
  onSubmit,
}: CreatePostTabProps) {
  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {editingPostId !== null ? 'Edit VKontakte Post' : 'Create VKontakte Post'}
        </CardTitle>
        <CardDescription>Create or edit a post (max {VK_MAX_LENGTH} characters)</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-6">
          <div>
            <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
              Post text (HTML)
            </label>
            <TipTapEditor
              content={postContent}
              onChange={onPostContentChange}
              placeholder="Enter your post text (HTML supported)"
              toolbarButtons={[
                'bold',
                'italic',
                'underline',
                'strike',
                'heading',
                'bulletList',
                'orderedList',
                'blockquote',
                'code',
                'codeBlock',
                'horizontalRule',
                'undo',
                'redo',
              ]}
            />
            <p className="text-xs text-[var(--text-muted)] mt-2">
              Plain text length: {htmlToPlainText(postContent).length} / {VK_MAX_LENGTH} characters
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                Publish at (optional)
              </label>
              <input
                type="datetime-local"
                value={publishAt}
                onChange={(e) => onPublishAtChange(e.target.value)}
                className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)]"
              />
              <p className="text-xs text-[var(--text-muted)] mt-1">
                Общий календарь:{' '}
                <Link to="/calendar?network=vk" className="text-primary-400 hover:underline">
                  /calendar
                </Link>
              </p>
            </div>
            <Input
              label="Target groups (optional, comma/newline)"
              value={targetGroupsText}
              onChange={(e) => onTargetGroupsTextChange(e.target.value)}
              placeholder="123456, clubname"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
              Изображения
            </label>
            <p className="text-xs text-[var(--text-muted)] mb-2">
              Загрузите фото с компьютера (JPG, PNG, GIF, WebP). Они будут прикреплены к посту.
            </p>
            <p className="text-xs text-amber-400/90 mb-2 rounded-lg border border-amber-500/25 bg-amber-500/5 px-3 py-2">
              Публикация <strong>с картинками на стену сообщества</strong> в VK требует пользовательский OAuth (
              <strong>Авторизация</strong>). Только текст без вложений часто достаточно публиковать с токеном сообщества
              (вкладка <strong>Авторизация</strong>).
            </p>
            {postImages.some(Boolean) && (
              <ul className="space-y-2 mb-3">
                {postImages.map((url, index) =>
                  !url ? null : (
                    <li
                      key={`${url}-${index}`}
                      className="flex items-center gap-3 p-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]"
                    >
                      <img
                        src={imagePreviewUrl(url)}
                        alt=""
                        className="h-14 w-14 shrink-0 object-cover rounded-lg border border-[var(--border-color)] bg-[var(--bg-tertiary)]"
                        onError={(e) => {
                          const el = e.target as HTMLImageElement
                          el.src = ''
                          el.style.display = 'none'
                        }}
                      />
                      <a
                        href={imagePreviewUrl(url)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 min-w-0 text-sm text-primary-400 hover:underline truncate"
                        title={url}
                      >
                        {url}
                      </a>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => onRemoveImage(index)}
                        className="shrink-0 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                        title="Удалить фото"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                        Удалить
                      </Button>
                    </li>
                  ),
                )}
              </ul>
            )}
            <div className="border-2 border-dashed border-[var(--border-color)] rounded-xl p-6 text-center">
              <input
                type="file"
                accept="image/jpeg,image/png,image/gif,image/webp"
                multiple
                className="hidden"
                id="vk-image-upload"
                disabled={uploadingImage}
                onChange={async (e) => {
                  const files = e.target.files
                  if (!files?.length) return
                  await onUploadImages(files)
                  e.target.value = ''
                }}
              />
              <label htmlFor="vk-image-upload" className="cursor-pointer">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-[var(--text-muted)] mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p className="text-sm text-[var(--text-secondary)]">
                  {uploadingImage ? 'Загрузка…' : 'Нажмите или перетащите файлы сюда'}
                </p>
              </label>
            </div>
          </div>

          {!editingPostId && (
            <TargetSocialNetworksWidget
              value={postTargets}
              onChange={onPostTargetsChange}
              selectedChannels={selectedChannels}
              onSelectedChannelsChange={onSelectedChannelsChange}
            />
          )}
          <CardFooter className="px-0">
            <Button type="submit" isLoading={isCreatingPost} className="w-full sm:w-auto">
              {editingPostId !== null ? 'Update Post' : 'Create Post'}
            </Button>
          </CardFooter>
        </form>
      </CardContent>
    </Card>
  )
}
