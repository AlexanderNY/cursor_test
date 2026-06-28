import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { EmptyState } from '@/components/ui/empty-state'
import { TableSkeleton } from '@/components/ui/skeleton'
import { gameService } from '@/services/game-service'
import type { GameMenuNode } from '@/types/game'
import { MediaLibrarySection } from './media-library-section'
import { MenuCsvImportSection } from './menu-csv-import-section'
import {
  formatMenuPrice,
  MENU_PRICE_HINT,
  sanitizeMenuPriceInput,
  validateMenuPrice,
} from '@/utils/menu-price'

interface MenuNodesSectionProps {
  modeId: number | null
  modeTitle?: string
}

function parentLabel(node: GameMenuNode, nodes: GameMenuNode[]): string {
  if (!node.parent_id) return '— корень —'
  const parent = nodes.find((n) => n.id === node.parent_id)
  return parent ? parent.title : `#${node.parent_id}`
}

export function MenuNodesSection({ modeId, modeTitle }: MenuNodesSectionProps) {
  const [nodes, setNodes] = useState<GameMenuNode[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [showForm, setShowForm] = useState(false)
  const [editingNodeId, setEditingNodeId] = useState<number | null>(null)
  const [title, setTitle] = useState('')
  const [bodyText, setBodyText] = useState('')
  const [parentId, setParentId] = useState<string>('')
  const [imageUrl, setImageUrl] = useState('')
  const [price, setPrice] = useState('')
  const [priceError, setPriceError] = useState('')
  const [sortOrder, setSortOrder] = useState('0')
  const [isSaving, setIsSaving] = useState(false)
  const [deletingNodeId, setDeletingNodeId] = useState<number | null>(null)
  const [togglingNodeId, setTogglingNodeId] = useState<number | null>(null)

  const loadNodes = useCallback(async (id: number) => {
    setError('')
    setIsLoading(true)
    try {
      const data = await gameService.listMenuNodes(id)
      setNodes(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить пункты меню')
      setNodes([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (modeId) {
      loadNodes(modeId)
    } else {
      setNodes([])
    }
  }, [modeId, loadNodes])

  function resetForm() {
    setEditingNodeId(null)
    setShowForm(false)
    setTitle('')
    setBodyText('')
    setParentId('')
    setImageUrl('')
    setPrice('')
    setPriceError('')
    setSortOrder('0')
  }

  function openCreateForm() {
    setError('')
    setSuccess('')
    resetForm()
    setShowForm(true)
  }

  function openEditForm(node: GameMenuNode) {
    setError('')
    setSuccess('')
    setEditingNodeId(node.id)
    setTitle(node.title)
    setBodyText(node.body_text ?? '')
    setParentId(node.parent_id ? String(node.parent_id) : '')
    setImageUrl(node.image_url ?? '')
    setPrice(node.price > 0 ? String(node.price) : '')
    setPriceError('')
    setSortOrder(String(node.sort_order))
    setShowForm(true)
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault()
    if (!modeId || !title.trim()) return

    const parsedSort = Number.parseInt(sortOrder, 10)
    const priceResult = validateMenuPrice(price)
    if (priceResult.error) {
      setPriceError(priceResult.error)
      setError(priceResult.error)
      return
    }
    const parsedPrice = priceResult.value
    const parentValue = parentId.trim() ? Number.parseInt(parentId, 10) : null
    if (parentId.trim() && !Number.isFinite(parentValue)) {
      setError('Некорректный родительский пункт')
      return
    }
    if (editingNodeId && parentValue === editingNodeId) {
      setError('Пункт не может быть родителем самого себя')
      return
    }

    setError('')
    setSuccess('')
    setIsSaving(true)
    try {
      const trimmedUrl = imageUrl.trim()
      if (editingNodeId) {
        await gameService.updateMenuNode(editingNodeId, {
          title: title.trim(),
          body_text: bodyText.trim() || null,
          parent_id: parentValue,
          image_url: trimmedUrl || null,
          sort_order: Number.isFinite(parsedSort) ? parsedSort : 0,
          price: parsedPrice,
        })
        setSuccess('Пункт обновлён')
      } else {
        await gameService.createMenuNode({
          mode_id: modeId,
          title: title.trim(),
          body_text: bodyText.trim() || null,
          parent_id: parentValue,
          image_url: trimmedUrl || null,
          sort_order: Number.isFinite(parsedSort) ? parsedSort : 0,
          price: parsedPrice,
          is_active: true,
        })
        setSuccess('Пункт добавлен')
      }
      resetForm()
      await loadNodes(modeId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить пункт')
    } finally {
      setIsSaving(false)
    }
  }

  async function handleToggleActive(node: GameMenuNode) {
    if (!modeId) return
    setTogglingNodeId(node.id)
    setError('')
    try {
      await gameService.updateMenuNode(node.id, { is_active: !node.is_active })
      await loadNodes(modeId)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось обновить пункт')
    } finally {
      setTogglingNodeId(null)
    }
  }

  async function handleDelete(node: GameMenuNode) {
    if (!modeId) return
    if (
      !window.confirm(
        `Удалить пункт «${node.title}»? Дочерние пункты тоже будут удалены.`,
      )
    ) {
      return
    }
    setDeletingNodeId(node.id)
    setError('')
    setSuccess('')
    try {
      await gameService.deleteMenuNode(node.id)
      if (editingNodeId === node.id) resetForm()
      setSuccess('Пункт удалён')
      await loadNodes(modeId)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось удалить пункт')
    } finally {
      setDeletingNodeId(null)
    }
  }

  if (!modeId) {
    return (
      <Card>
        <CardContent className="pt-6">
          <EmptyState title="Выберите режим" description="Слева выберите режим типа «Меню»." />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-lg">
              Пункты меню{modeTitle ? `: ${modeTitle}` : ''}
            </CardTitle>
            <CardDescription>
              Иерархия: выберите родителя для вложенного уровня. Текст на листе показывается при
              выборе пункта без дочерних элементов.
            </CardDescription>
          </div>
          <Button type="button" onClick={openCreateForm} disabled={showForm}>
            Добавить пункт
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && <p className="text-sm text-red-400">{error}</p>}
        {success && <p className="text-sm text-emerald-400">{success}</p>}

        <MediaLibrarySection
          onSelectUrl={(url) => {
            if (!showForm) openCreateForm()
            setImageUrl(url)
            setSuccess('URL изображения подставлен в форму пункта')
          }}
        />

        <MenuCsvImportSection
          modeId={modeId}
          modeTitle={modeTitle}
          existingNodes={nodes}
          onImported={async () => {
            if (modeId) await loadNodes(modeId)
          }}
        />

        {showForm && (
          <form
            onSubmit={handleSave}
            className="space-y-4 rounded-xl border border-[var(--border-color)] p-4"
          >
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">
              {editingNodeId ? 'Редактирование пункта' : 'Новый пункт'}
            </h3>
            <Input
              placeholder="Заголовок кнопки"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <div className="space-y-1">
              <label className="text-xs text-[var(--text-secondary)]">Родитель (пусто = корень)</label>
              <select
                className="w-full rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                value={parentId}
                onChange={(e) => setParentId(e.target.value)}
              >
                <option value="">— корень —</option>
                {nodes
                  .filter((n) => n.id !== editingNodeId)
                  .map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.title} (#{n.id})
                    </option>
                  ))}
              </select>
            </div>
            <textarea
              className="w-full min-h-[80px] rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
              placeholder="Описание (показывается в боте напротив пункта)"
              value={bodyText}
              onChange={(e) => setBodyText(e.target.value)}
            />
            <div className="space-y-1">
              <label htmlFor="menu-node-price" className="text-xs font-medium text-[var(--text-primary)]">
                Цена, ₽
              </label>
              <Input
                id="menu-node-price"
                inputMode="decimal"
                placeholder="0.00"
                value={price}
                onChange={(e) => {
                  setPrice(sanitizeMenuPriceInput(e.target.value))
                  setPriceError('')
                }}
                onBlur={() => {
                  if (!price.trim()) return
                  const result = validateMenuPrice(price)
                  if (result.error) setPriceError(result.error)
                }}
                aria-invalid={Boolean(priceError)}
              />
              <p className="text-xs text-[var(--text-secondary)]">{MENU_PRICE_HINT}</p>
              {priceError && <p className="text-xs text-red-400">{priceError}</p>}
            </div>
            <Input
              placeholder="URL изображения (необязательно)"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
            />
            <Input
              type="number"
              placeholder="Порядок сортировки"
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
            />
            <div className="flex flex-wrap gap-2">
              <Button type="submit" isLoading={isSaving}>
                {editingNodeId ? 'Сохранить' : 'Создать'}
              </Button>
              <Button type="button" variant="secondary" onClick={resetForm}>
                Отмена
              </Button>
            </div>
          </form>
        )}

        {isLoading ? (
          <TableSkeleton rows={5} />
        ) : nodes.length === 0 ? (
          <EmptyState
            title="Нет пунктов"
            description="Добавьте корневые пункты меню — пользователь сможет проваливаться на уровни ниже."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                  <th className="pb-2 pr-3 font-medium">ID</th>
                  <th className="pb-2 pr-3 font-medium">Заголовок</th>
                  <th className="pb-2 pr-3 font-medium">Цена</th>
                  <th className="pb-2 pr-3 font-medium">Родитель</th>
                  <th className="pb-2 pr-3 font-medium">Статус</th>
                  <th className="pb-2 font-medium">Действия</th>
                </tr>
              </thead>
              <tbody>
                {nodes.map((node) => (
                  <tr key={node.id} className="border-b border-[var(--border-color)]/60">
                    <td className="py-3 pr-3 text-[var(--text-secondary)]">{node.id}</td>
                    <td className="py-3 pr-3 max-w-md">
                      <p className="font-medium text-[var(--text-primary)]">{node.title}</p>
                      {node.body_text && (
                        <p className="mt-1 line-clamp-2 text-xs text-[var(--text-secondary)]">
                          {node.body_text}
                        </p>
                      )}
                    </td>
                    <td className="py-3 pr-3 text-[var(--text-secondary)] whitespace-nowrap">
                      {formatMenuPrice(node.price)}
                    </td>
                    <td className="py-3 pr-3 text-[var(--text-secondary)]">
                      {parentLabel(node, nodes)}
                    </td>
                    <td className="py-3 pr-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs ${
                          node.is_active
                            ? 'bg-emerald-500/15 text-emerald-400'
                            : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)]'
                        }`}
                      >
                        {node.is_active ? 'активен' : 'выкл'}
                      </span>
                    </td>
                    <td className="py-3">
                      <div className="flex flex-wrap gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant="secondary"
                          onClick={() => openEditForm(node)}
                        >
                          Изменить
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="secondary"
                          isLoading={togglingNodeId === node.id}
                          onClick={() => handleToggleActive(node)}
                        >
                          {node.is_active ? 'Выключить' : 'Включить'}
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="danger"
                          isLoading={deletingNodeId === node.id}
                          onClick={() => handleDelete(node)}
                        >
                          Удалить
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
