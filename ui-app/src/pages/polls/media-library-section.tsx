import { useCallback, useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { TableSkeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/ui/empty-state'
import { gameService } from '@/services/game-service'
import type { GameMediaAsset } from '@/types/game'

interface MediaLibrarySectionProps {
  onSelectUrl?: (url: string) => void
}

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

export function MediaLibrarySection({ onSelectUrl }: MediaLibrarySectionProps) {
  const uploadInputRef = useRef<HTMLInputElement>(null)
  const [assets, setAssets] = useState<GameMediaAsset[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [galleryOpen, setGalleryOpen] = useState(false)
  const [uploadTitle, setUploadTitle] = useState('')
  const [uploadDescription, setUploadDescription] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [savingId, setSavingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const loadAssets = useCallback(async () => {
    setError('')
    setIsLoading(true)
    try {
      const data = await gameService.listMedia()
      setAssets(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить медиатеку')
      setAssets([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAssets()
  }, [loadAssets])

  async function handleUploadChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    setError('')
    setSuccess('')
    setIsUploading(true)
    try {
      const created = await gameService.uploadMedia(
        file,
        uploadTitle.trim() || undefined,
        uploadDescription.trim() || undefined,
      )
      setUploadTitle('')
      setUploadDescription('')
      setSuccess(`Загружено: ${created.title || created.filename}`)
      setGalleryOpen(true)
      await loadAssets()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить файл')
    } finally {
      setIsUploading(false)
    }
  }

  function startEdit(asset: GameMediaAsset) {
    setEditingId(asset.id)
    setEditTitle(asset.title)
    setEditDescription(asset.description ?? '')
  }

  async function handleSaveEdit(e: FormEvent) {
    e.preventDefault()
    if (editingId === null) return
    setSavingId(editingId)
    setError('')
    try {
      await gameService.updateMedia(editingId, {
        title: editTitle.trim(),
        description: editDescription.trim() || null,
      })
      setEditingId(null)
      await loadAssets()
      setSuccess('Атрибуты обновлены')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить')
    } finally {
      setSavingId(null)
    }
  }

  async function handleDelete(asset: GameMediaAsset) {
    if (!window.confirm(`Удалить «${asset.title || asset.filename}»?`)) return
    setDeletingId(asset.id)
    setError('')
    try {
      await gameService.deleteMedia(asset.id)
      if (editingId === asset.id) setEditingId(null)
      await loadAssets()
      setSuccess('Файл удалён')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось удалить')
    } finally {
      setDeletingId(null)
    }
  }

  function handleCopyUrl(url: string) {
    void navigator.clipboard.writeText(url)
    setSuccess('URL скопирован в буфер обмена')
  }

  return (
    <div className="space-y-4 rounded-xl border border-[var(--border-color)] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">Медиатека</h3>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">
            JPG, PNG, WebP, GIF до 10 MB. URL публичный — для Telegram и поля image_url.
          </p>
        </div>
        <Button type="button" variant="secondary" size="sm" onClick={() => setGalleryOpen((v) => !v)}>
          {galleryOpen ? 'Скрыть галерею' : 'Галерея'}
        </Button>
      </div>

      <form
        className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
        onSubmit={(e) => e.preventDefault()}
      >
        <Input
          placeholder="Название (необязательно)"
          value={uploadTitle}
          onChange={(e) => setUploadTitle(e.target.value)}
        />
        <Input
          placeholder="Описание / alt (необязательно)"
          value={uploadDescription}
          onChange={(e) => setUploadDescription(e.target.value)}
        />
        <Button
          type="button"
          disabled={isUploading}
          isLoading={isUploading}
          onClick={() => uploadInputRef.current?.click()}
        >
          Загрузить изображение
        </Button>
        <input
          ref={uploadInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          className="hidden"
          onChange={handleUploadChange}
        />
      </form>

      {success && <Alert variant="success">{success}</Alert>}
      {error && <Alert variant="error">{error}</Alert>}

      {galleryOpen && (
        <div className="space-y-4 border-t border-[var(--border-color)] pt-4">
          {isLoading ? (
            <TableSkeleton rows={3} />
          ) : assets.length === 0 ? (
            <EmptyState title="Медиатека пуста" description="Загрузите первое изображение." />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {assets.map((asset) => (
                <div
                  key={asset.id}
                  className="overflow-hidden rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)]"
                >
                  <img
                    src={gameService.mediaPreviewUrl(asset.filename)}
                    alt={asset.title || asset.filename}
                    className="h-40 w-full object-cover bg-[var(--bg-tertiary)]"
                  />
                  <div className="space-y-2 p-3 text-xs">
                    <p className="font-medium text-[var(--text-primary)]">
                      {asset.title || asset.original_filename || asset.filename}
                    </p>
                    {asset.description && (
                      <p className="text-[var(--text-secondary)]">{asset.description}</p>
                    )}
                    <dl className="space-y-1 text-[var(--text-secondary)]">
                      <div className="flex justify-between gap-2">
                        <dt>Файл</dt>
                        <dd className="truncate text-right text-[var(--text-primary)]">{asset.filename}</dd>
                      </div>
                      <div className="flex justify-between gap-2">
                        <dt>Размер</dt>
                        <dd>{formatBytes(asset.size_bytes)}</dd>
                      </div>
                      <div className="flex justify-between gap-2">
                        <dt>MIME</dt>
                        <dd>{asset.content_type || '—'}</dd>
                      </div>
                      <div>
                        <dt className="mb-0.5">public_url</dt>
                        <dd className="break-all text-[var(--text-primary)]">{asset.public_url}</dd>
                      </div>
                    </dl>
                    <div className="flex flex-wrap gap-2 pt-1">
                      {onSelectUrl && (
                        <Button
                          type="button"
                          size="sm"
                          onClick={() => onSelectUrl(asset.public_url)}
                        >
                          Подставить в вопрос
                        </Button>
                      )}
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => handleCopyUrl(asset.public_url)}
                      >
                        Копировать URL
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => startEdit(asset)}
                      >
                        Атрибуты
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        isLoading={deletingId === asset.id}
                        onClick={() => handleDelete(asset)}
                      >
                        Удалить
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {editingId !== null && (
            <form
              onSubmit={handleSaveEdit}
              className="space-y-3 rounded-xl border border-[var(--border-color)] p-4"
            >
              <h4 className="text-sm font-semibold text-[var(--text-primary)]">
                Редактирование атрибутов
              </h4>
              <Input
                placeholder="Название"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
              />
              <Input
                placeholder="Описание"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
              />
              <div className="flex gap-2">
                <Button type="submit" size="sm" isLoading={savingId === editingId}>
                  Сохранить
                </Button>
                <Button type="button" size="sm" variant="secondary" onClick={() => setEditingId(null)}>
                  Отмена
                </Button>
              </div>
            </form>
          )}
        </div>
      )}
    </div>
  )
}
