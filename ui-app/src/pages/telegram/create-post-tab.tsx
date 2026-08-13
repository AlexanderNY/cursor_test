import { FormEvent, ChangeEvent } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  TargetSocialNetworksWidget,
  type TargetSocialNetworks,
  type SelectedBrandChannels,
} from '@/components/target-social-networks'
import type { TgPostTemplate } from '@/types/telegram'

export interface CreatePostTabProps {
  postText: string
  onPostTextChange: (value: string) => void
  imagePreview: string | null
  onImageChange: (e: ChangeEvent<HTMLInputElement>) => void
  onRemoveImage: () => void
  editingPostId: number | null
  postTargets: TargetSocialNetworks
  onPostTargetsChange: (value: TargetSocialNetworks) => void
  publishAt: string
  onPublishAtChange: (value: string) => void
  selectedChannels: SelectedBrandChannels
  onSelectedChannelsChange: (value: SelectedBrandChannels) => void
  templates: TgPostTemplate[]
  selectedTemplateId: string
  onSelectedTemplateChange: (id: string) => void
  onApplyTemplate: () => void
  onSaveAsTemplate: () => void
  isSavingTemplate: boolean
  isCreatingPost: boolean
  onSubmit: (e: FormEvent) => void
}

export function CreatePostTab({
  postText,
  onPostTextChange,
  imagePreview,
  onImageChange,
  onRemoveImage,
  editingPostId,
  postTargets,
  onPostTargetsChange,
  publishAt,
  onPublishAtChange,
  selectedChannels,
  onSelectedChannelsChange,
  templates,
  selectedTemplateId,
  onSelectedTemplateChange,
  onApplyTemplate,
  onSaveAsTemplate,
  isSavingTemplate,
  isCreatingPost,
  onSubmit,
}: CreatePostTabProps) {
  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          {editingPostId !== null ? 'Edit Telegram Post' : 'Create Telegram Post'}
        </CardTitle>
        <CardDescription>Create a new Telegram post (max 4096 characters)</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-6">
          {templates.length > 0 && editingPostId === null && (
            <div className="p-4 bg-[var(--bg-secondary)] rounded-xl space-y-3 border border-[var(--border-color)]">
              <label className="text-sm font-medium text-[var(--text-secondary)] block">Template</label>
              <div className="flex flex-wrap gap-3 items-end">
                <select
                  value={selectedTemplateId}
                  onChange={(e) => onSelectedTemplateChange(e.target.value)}
                  className="flex-1 min-w-[200px] px-4 py-2.5 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                >
                  <option value="">Select template...</option>
                  {templates.map((t) => (
                    <option key={t.id} value={String(t.id)}>
                      {t.name}
                    </option>
                  ))}
                </select>
                <Button type="button" variant="secondary" size="sm" onClick={onApplyTemplate} disabled={!selectedTemplateId}>
                  Apply
                </Button>
                <Button type="button" variant="secondary" size="sm" onClick={onSaveAsTemplate} isLoading={isSavingTemplate} disabled={!postText.trim()}>
                  Save as template
                </Button>
              </div>
            </div>
          )}

          {templates.length === 0 && editingPostId === null && (
            <div className="flex justify-end">
              <Button type="button" variant="secondary" size="sm" onClick={onSaveAsTemplate} isLoading={isSavingTemplate} disabled={!postText.trim()}>
                Save as template
              </Button>
            </div>
          )}

          <div>
            <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">Post Text</label>
            <textarea
              value={postText}
              onChange={(e) => onPostTextChange(e.target.value)}
              maxLength={4096}
              rows={8}
              className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all"
              placeholder="Enter your post text..."
              required
            />
            <p className="text-xs text-[var(--text-muted)] mt-2">{postText.length} / 4096 characters</p>
          </div>

          <div>
            <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">Image (optional)</label>
            {imagePreview ? (
              <div className="relative">
                <img src={imagePreview} alt="Preview" className="max-w-full h-auto rounded-xl border border-[var(--border-color)]" />
                <Button type="button" variant="ghost" size="sm" onClick={onRemoveImage} className="absolute top-2 right-2 text-red-400 hover:text-red-300">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </Button>
              </div>
            ) : (
              <div className="border-2 border-dashed border-[var(--border-color)] rounded-xl p-6 text-center">
                <input type="file" accept="image/*" onChange={onImageChange} className="hidden" id="image-upload" />
                <label htmlFor="image-upload" className="cursor-pointer">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-[var(--text-muted)] mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p className="text-sm text-[var(--text-secondary)]">Click to upload image</p>
                </label>
              </div>
            )}
          </div>

          {editingPostId === null && (
            <>
              <TargetSocialNetworksWidget
                value={postTargets}
                onChange={onPostTargetsChange}
                selectedChannels={selectedChannels}
                onSelectedChannelsChange={onSelectedChannelsChange}
              />

              <div>
                <label className="text-sm font-medium text-[var(--text-secondary)] block mb-2">
                  Schedule publish (optional)
                </label>
                <input
                  type="datetime-local"
                  value={publishAt}
                  onChange={(e) => onPublishAtChange(e.target.value)}
                  className="w-full max-w-xs px-4 py-2.5 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                />
                <p className="text-xs text-[var(--text-muted)] mt-1">Leave empty to publish immediately when approved</p>
              </div>
            </>
          )}

          <CardFooter className="px-0">
            {editingPostId !== null ? (
              <Button type="submit" isLoading={isCreatingPost} className="w-full sm:w-auto">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Update Post
              </Button>
            ) : (
              <Button type="submit" isLoading={isCreatingPost} className="w-full sm:w-auto">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                Create Post
              </Button>
            )}
          </CardFooter>
        </form>
      </CardContent>
    </Card>
  )
}
