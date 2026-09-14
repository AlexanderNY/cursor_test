import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type PointerEvent as ReactPointerEvent,
  type WheelEvent as ReactWheelEvent,
} from 'react'
import { AnkiStudy } from '@/components/anki-study'
import { LearningMapLearnPanel } from '@/components/learning-map-learn-panel'
import { LeafDetailPanel } from '@/components/leaf-detail-panel'
import {
  collectAnkiCards,
  downloadAnkiDeck,
  type AnkiCard,
} from '@/data/learning-map/anki-cards'
import { siteReviewAnkiCard } from '@/data/site/site-api'
import { getSiteAuthSession } from '@/data/site/site-auth'
import {
  loadHiddenBranchIds,
  saveHiddenBranchIds,
} from '@/data/learning-map/branch-visibility'
import {
  addCrossLink,
  crossLinkGeometry,
  loadCrossLinks,
  removeCrossLink,
  saveCrossLinks,
  type MapCrossLink,
} from '@/data/learning-map/cross-links'
import {
  buildLearningMapMarkdown,
  downloadMarkdownFile,
  suggestExportFilename,
} from '@/data/learning-map/export-markdown'
import {
  loadLeafNotes,
  saveLeafNotes,
  upsertLeafNote,
  type LeafNote,
} from '@/data/learning-map/leaf-notes'
import { buildLeafPanelData } from '@/data/learning-map/leaf-panel'
import { layoutMindmap } from '@/data/learning-map/layout-mindmap'
import {
  findL1Ancestor,
  getMapLearnLink,
} from '@/data/learning-map/map-learn-links'
import type { MindNode } from '@/data/learning-map/parse-outline'
import {
  filterTree,
  filterTreeByProfile,
  filterTreeByTags,
  LEARN_MAP_PROFILES,
  type LearnMapProfileId,
} from '@/data/learning-map/parse-outline'
import {
  collectAllTags,
  getNodeTags,
  loadTagColors,
  normalizeTag,
  pickPrimaryTag,
  resolveTagColor,
  saveTagColors,
  setTagColor,
} from '@/data/learning-map/tag-style'
import { getPublishedPosts, useLearnPosts } from '@/data/learn/use-learn-posts'
import { useSiteLearnProgress } from '@/data/site/use-learn-progress'

interface LearningMindmapProps {
  root: MindNode
  branchCount: number
  nodeCount: number
}

const DEPTH_OPTIONS = [1, 2, 3, 4, 5] as const
const MIN_ZOOM = 0.25
const MAX_ZOOM = 2.5

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function findNode(root: MindNode, id: string): MindNode | null {
  if (root.id === id) {
    return root
  }
  for (const child of root.children) {
    const found = findNode(child, id)
    if (found) {
      return found
    }
  }
  return null
}

function collectPath(root: MindNode, targetId: string): MindNode[] | null {
  if (root.id === targetId) {
    return [root]
  }
  for (const child of root.children) {
    const path = collectPath(child, targetId)
    if (path) {
      return [root, ...path]
    }
  }
  return null
}

function isLeafNode(node: MindNode | null | undefined): boolean {
  return Boolean(node && node.children.length === 0)
}

export function LearningMindmap({ root, branchCount, nodeCount }: LearningMindmapProps) {
  const shellRef = useRef<HTMLDivElement>(null)
  const viewportRef = useRef<HTMLDivElement>(null)
  const [query, setQuery] = useState('')
  const [depth, setDepth] = useState<number>(2)
  const [selectedId, setSelectedId] = useState(root.id)
  const [zoom, setZoom] = useState(0.85)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [hiddenBranchIds, setHiddenBranchIds] = useState<string[]>(() => loadHiddenBranchIds())
  const [crossLinks, setCrossLinks] = useState<MapCrossLink[]>(() => loadCrossLinks())
  const [linkMode, setLinkMode] = useState(false)
  const [linkFromId, setLinkFromId] = useState<string | null>(null)
  const [linkMessage, setLinkMessage] = useState('')
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [leafNotes, setLeafNotes] = useState<Record<string, LeafNote>>(() => loadLeafNotes())
  const [ankiOpen, setAnkiOpen] = useState(false)
  const [activeTags, setActiveTags] = useState<string[]>([])
  const [tagColors, setTagColors] = useState<Record<string, string>>(() => loadTagColors())
  const [profileId, setProfileId] = useState<LearnMapProfileId | null>('developer')
  const { posts, isReady: learnReady } = useLearnPosts()
  const publishedPosts = useMemo(() => getPublishedPosts(posts), [posts])
  const { completedSlugs } = useSiteLearnProgress()
  const dragRef = useRef<{
    pointerId: number
    startX: number
    startY: number
    originX: number
    originY: number
    moved: boolean
  } | null>(null)

  const branches = root.children
  const hiddenSet = useMemo(() => new Set(hiddenBranchIds), [hiddenBranchIds])

  const visibleRoot = useMemo((): MindNode => {
    if (hiddenSet.size === 0) {
      return root
    }
    return {
      ...root,
      children: root.children.filter((branch) => !hiddenSet.has(branch.id)),
    }
  }, [root, hiddenSet])

  const filtered = useMemo(() => {
    const byProfile = filterTreeByProfile(visibleRoot, profileId) ?? {
      ...visibleRoot,
      children: [],
    }
    const byQuery = filterTree(byProfile, query) ?? byProfile
    if (activeTags.length === 0) {
      return byQuery
    }
    return (
      filterTreeByTags(byQuery, activeTags, (node) => getNodeTags(node, leafNotes)) ?? {
        ...byQuery,
        children: [],
      }
    )
  }, [visibleRoot, query, activeTags, leafNotes, profileId])
  const layout = useMemo(() => layoutMindmap(filtered, depth), [filtered, depth])

  const allTags = useMemo(
    () => collectAllTags(visibleRoot, leafNotes),
    [visibleRoot, leafNotes],
  )

  const tagsByNodeId = useMemo(() => {
    const map = new Map<string, string[]>()
    const walk = (node: MindNode): void => {
      map.set(node.id, getNodeTags(node, leafNotes))
      for (const child of node.children) {
        walk(child)
      }
    }
    walk(root)
    return map
  }, [root, leafNotes])

  const toggleTagFilter = useCallback((tag: string) => {
    setActiveTags((prev) =>
      prev.includes(tag) ? prev.filter((item) => item !== tag) : [...prev, tag],
    )
  }, [])

  const selectedNode = useMemo(
    () => findNode(root, selectedId) ?? root,
    [root, selectedId],
  )
  const selectedPath = useMemo(
    () => collectPath(root, selectedId) ?? [root],
    [root, selectedId],
  )
  const l1Branch = useMemo(
    () => findL1Ancestor(root, selectedId),
    [root, selectedId],
  )
  const learnLink = useMemo(
    () => (l1Branch ? getMapLearnLink(l1Branch.title) : undefined),
    [l1Branch],
  )

  const persistHidden = useCallback((ids: string[]) => {
    setHiddenBranchIds(ids)
    saveHiddenBranchIds(ids)
  }, [])

  const hideBranch = useCallback(
    (branchId: string) => {
      if (!branchId || branchId === root.id) {
        return
      }
      const next = [...new Set([...hiddenBranchIds, branchId])]
      persistHidden(next)
      if (selectedId === branchId || collectPath(root, selectedId)?.some((n) => n.id === branchId)) {
        setSelectedId(root.id)
      }
    },
    [hiddenBranchIds, persistHidden, root, selectedId],
  )

  const showBranch = useCallback(
    (branchId: string) => {
      persistHidden(hiddenBranchIds.filter((id) => id !== branchId))
    },
    [hiddenBranchIds, persistHidden],
  )

  const showAllBranches = useCallback(() => {
    persistHidden([])
  }, [persistHidden])

  const persistCrossLinks = useCallback((next: MapCrossLink[]) => {
    setCrossLinks(next)
    saveCrossLinks(next)
  }, [])

  const onRemoveCrossLink = useCallback(
    (a: string, b: string) => {
      persistCrossLinks(removeCrossLink(crossLinks, a, b))
      setLinkMessage('Связь удалена')
    },
    [crossLinks, persistCrossLinks],
  )

  const exportMarkdown = useCallback(() => {
    const visibleBranchIds =
      hiddenSet.size > 0
        ? root.children.filter((branch) => !hiddenSet.has(branch.id)).map((branch) => branch.id)
        : null
    const markdown = buildLearningMapMarkdown(root, {
      notes: leafNotes,
      crossLinks,
      includeBranchIds: visibleBranchIds,
    })
    downloadMarkdownFile(suggestExportFilename(root), markdown)
    setLinkMessage('Markdown скачан — можно открыть в Obsidian')
  }, [crossLinks, hiddenSet, leafNotes, root])

  const ankiCards = useMemo(() => {
    const visibleRoot =
      hiddenSet.size === 0
        ? root
        : {
            ...root,
            children: root.children.filter((branch) => !hiddenSet.has(branch.id)),
          }
    const branchId =
      l1Branch && !hiddenSet.has(l1Branch.id) && selectedId !== root.id ? l1Branch.id : null
    return collectAnkiCards(visibleRoot, {
      notes: leafNotes,
      branchId: branchId && selectedId !== root.id ? branchId : null,
      onlyLeaves: true,
      posts: publishedPosts,
    })
  }, [hiddenSet, l1Branch, leafNotes, publishedPosts, root, selectedId])

  const ankiCardsAll = useMemo(() => {
    const visibleRoot =
      hiddenSet.size === 0
        ? root
        : {
            ...root,
            children: root.children.filter((branch) => !hiddenSet.has(branch.id)),
          }
    return collectAnkiCards(visibleRoot, {
      notes: leafNotes,
      onlyLeaves: true,
      posts: publishedPosts,
    })
  }, [hiddenSet, leafNotes, publishedPosts, root])

  const ankiTopics = useMemo(() => {
    const counts = new Map<string, { title: string; count: number }>()
    for (const card of ankiCardsAll) {
      if (!card.branchId) {
        continue
      }
      const prev = counts.get(card.branchId)
      if (prev) {
        prev.count += 1
      } else {
        counts.set(card.branchId, { title: card.branch, count: 1 })
      }
    }
    return root.children
      .filter((branch) => !hiddenSet.has(branch.id))
      .map((branch) => ({
        id: branch.id,
        title: branch.title,
        count: counts.get(branch.id)?.count || 0,
      }))
      .filter((topic) => topic.count > 0)
  }, [ankiCardsAll, hiddenSet, root.children])

  const ankiTagOptions = useMemo(() => {
    const set = new Set<string>()
    for (const card of ankiCardsAll) {
      for (const tag of card.tags) {
        set.add(normalizeTag(tag))
      }
    }
    return [...set].sort((a, b) => a.localeCompare(b, 'ru'))
  }, [ankiCardsAll])

  const exportAnki = useCallback(() => {
    const cards = ankiCards.length > 0 ? ankiCards : ankiCardsAll
    if (cards.length === 0) {
      setLinkMessage('Нет Anki-карт: сохраните краткий ответ у листьев')
      return
    }
    downloadAnkiDeck(cards)
    setLinkMessage(
      `Anki: ${cards.length} карт${ankiCards.length > 0 && l1Branch ? ` (ветка «${l1Branch.title}»)` : ''} — File → Import в Anki`,
    )
  }, [ankiCards, ankiCardsAll, l1Branch])

  const selectedLeafLinks = useMemo(() => {
    return crossLinks.filter((link) => link.a === selectedId || link.b === selectedId)
  }, [crossLinks, selectedId])

  const leafPanel = useMemo(
    () => buildLeafPanelData(root, selectedId, crossLinks, leafNotes),
    [root, selectedId, crossLinks, leafNotes],
  )

  const drawnCrossLinks = useMemo(() => {
    const byId = new Map(layout.nodes.map((node) => [node.id, node]))
    return crossLinks
      .map((link) => {
        const left = byId.get(link.a)
        const right = byId.get(link.b)
        if (!left || !right) {
          return null
        }
        const geometry = crossLinkGeometry(left.x, left.y, right.x, right.y)
        return {
          key: `${link.a}|${link.b}`,
          a: link.a,
          b: link.b,
          titleA: left.title,
          titleB: right.title,
          d: geometry.d,
          midX: geometry.midX,
          midY: geometry.midY,
        }
      })
      .filter((item): item is NonNullable<typeof item> => item != null)
  }, [crossLinks, layout.nodes])

  const selectNode = (id: string, expandNextLevel = false) => {
    setSelectedId(id)
    const path = collectPath(root, id)
    const nodeDepth = Math.max(0, (path?.length ?? 1) - 1)
    const node = path?.[path.length - 1]
    let needed = Math.max(1, nodeDepth)
    if (expandNextLevel && node && node.children.length > 0) {
      needed = Math.max(needed, nodeDepth + 1)
    }
    if (needed > depth) {
      setDepth(Math.min(5, needed))
    }
  }

  const onNodeClick = (nodeId: string) => {
    if (!linkMode) {
      selectNode(nodeId, true)
      return
    }
    const node = findNode(root, nodeId)
    if (!isLeafNode(node)) {
      setLinkMessage('Связь только между листьями (узлы без дочерних)')
      return
    }
    if (!linkFromId) {
      setLinkFromId(nodeId)
      setLinkMessage('Теперь выберите листок другой ветки')
      selectNode(nodeId)
      return
    }
    if (linkFromId === nodeId) {
      setLinkFromId(null)
      setLinkMessage('Выбор сброшен — кликните первый листок')
      return
    }
    const branchA = findL1Ancestor(root, linkFromId)
    const branchB = findL1Ancestor(root, nodeId)
    if (!branchA || !branchB || branchA.id === branchB.id) {
      setLinkMessage('Нужны листья из разных веток')
      return
    }
    const next = addCrossLink(crossLinks, linkFromId, nodeId)
    persistCrossLinks(next)
    setLinkFromId(null)
    setLinkMessage('Пунктирная связь добавлена')
    selectNode(nodeId)
  }

  const fitToView = useCallback(() => {
    const viewport = viewportRef.current
    if (!viewport) {
      return
    }
    const rect = viewport.getBoundingClientRect()
    const nextZoom = clamp(
      Math.min((rect.width - 24) / layout.width, (rect.height - 24) / layout.height),
      MIN_ZOOM,
      1.15,
    )
    setZoom(nextZoom)
    setPan({
      x: (rect.width - layout.width * nextZoom) / 2,
      y: (rect.height - layout.height * nextZoom) / 2,
    })
  }, [layout.height, layout.width])

  const fitToViewRef = useRef(fitToView)
  fitToViewRef.current = fitToView

  // Автовписать только при старте / поиске / скрытии веток / fullscreen — не при раскрытии глубины.
  useEffect(() => {
    fitToViewRef.current()
  }, [query, hiddenBranchIds, isFullscreen])

  useEffect(() => {
    fitToViewRef.current()
    // initial fit once
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mount only
  }, [])

  useEffect(() => {
    const syncFs = () => {
      const native = Boolean(document.fullscreenElement)
      const css = Boolean(shellRef.current?.classList.contains('is-fullscreen-css'))
      setIsFullscreen(native || css)
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') {
        return
      }
      const shell = shellRef.current
      if (shell?.classList.contains('is-fullscreen-css')) {
        shell.classList.remove('is-fullscreen-css')
        setIsFullscreen(false)
      }
    }
    document.addEventListener('fullscreenchange', syncFs)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('fullscreenchange', syncFs)
      document.removeEventListener('keydown', onKey)
    }
  }, [])

  const toggleFullscreen = async () => {
    const shell = shellRef.current
    if (!shell) {
      return
    }
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen()
        shell.classList.remove('is-fullscreen-css')
        setIsFullscreen(false)
        return
      }
      if (shell.classList.contains('is-fullscreen-css')) {
        shell.classList.remove('is-fullscreen-css')
        setIsFullscreen(false)
        return
      }
      if (typeof shell.requestFullscreen === 'function') {
        await shell.requestFullscreen()
        setIsFullscreen(true)
        return
      }
      shell.classList.add('is-fullscreen-css')
      setIsFullscreen(true)
    } catch {
      shell.classList.toggle('is-fullscreen-css')
      setIsFullscreen(shell.classList.contains('is-fullscreen-css'))
    }
  }

  const onWheel = (event: ReactWheelEvent<HTMLDivElement>) => {
    event.preventDefault()
    const viewport = viewportRef.current
    if (!viewport) {
      return
    }
    const rect = viewport.getBoundingClientRect()
    const mouseX = event.clientX - rect.left
    const mouseY = event.clientY - rect.top
    const delta = event.deltaY > 0 ? 0.9 : 1.1
    const nextZoom = clamp(zoom * delta, MIN_ZOOM, MAX_ZOOM)
    const scale = nextZoom / zoom
    setPan({
      x: mouseX - (mouseX - pan.x) * scale,
      y: mouseY - (mouseY - pan.y) * scale,
    })
    setZoom(nextZoom)
  }

  const onPointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.button !== 0) {
      return
    }
    const target = event.target as HTMLElement
    if (target.closest('.lm-node, .lm-cross-link')) {
      return
    }
    dragRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      originX: pan.x,
      originY: pan.y,
      moved: false,
    }
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  const onPointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current
    if (!drag || drag.pointerId !== event.pointerId) {
      return
    }
    const dx = event.clientX - drag.startX
    const dy = event.clientY - drag.startY
    if (Math.abs(dx) + Math.abs(dy) > 3) {
      drag.moved = true
    }
    setPan({ x: drag.originX + dx, y: drag.originY + dy })
  }

  const onPointerUp = (event: ReactPointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current
    if (!drag || drag.pointerId !== event.pointerId) {
      return
    }
    dragRef.current = null
    try {
      event.currentTarget.releasePointerCapture(event.pointerId)
    } catch {
      // ignore
    }
  }

  const visibleCount = layout.nodes.length

  return (
    <div
      ref={shellRef}
      className={`lm${isFullscreen ? ' is-fullscreen' : ''}`}
    >
      <div className="lm-menu" aria-label="Управление картой">
        <section className="lm-menu-block">
          <p className="lm-menu-block-label">Фильтры</p>
          <div className="lm-menu-block-body">
            <label className="lm-search">
              <span className="lm-search-label">Поиск</span>
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="ACID, docker, soft skills…"
                autoComplete="off"
              />
            </label>

            <div className="lm-depth" role="group" aria-label="Профиль обучения">
              <span className="lm-search-label">Профиль</span>
              <div className="lm-profile-btns">
                <button
                  type="button"
                  className={`lm-profile-btn${profileId === null ? ' is-active' : ''}`}
                  onClick={() => setProfileId(null)}
                  aria-pressed={profileId === null}
                  title="Все листья"
                >
                  Все
                </button>
                {LEARN_MAP_PROFILES.map((profile) => (
                  <button
                    key={profile.id}
                    type="button"
                    className={`lm-profile-btn${profileId === profile.id ? ' is-active' : ''}`}
                    onClick={() => setProfileId(profile.id)}
                    aria-pressed={profileId === profile.id}
                    title={profile.label}
                  >
                    {profile.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="lm-depth" role="group" aria-label="Глубина карты">
              <span className="lm-search-label">Уровни</span>
              <div className="lm-depth-btns">
                {DEPTH_OPTIONS.map((value) => (
                  <button
                    key={value}
                    type="button"
                    className={`lm-depth-btn${depth === value ? ' is-active' : ''}`}
                    onClick={() => setDepth(value)}
                    aria-pressed={depth === value}
                  >
                    {value}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="lm-menu-block">
          <p className="lm-menu-block-label">Карта</p>
          <div className="lm-menu-block-body lm-menu-block-body-actions">
            <div className="lm-zoom-controls" role="group" aria-label="Масштаб">
              <button type="button" className="lm-btn" onClick={() => setZoom((z) => clamp(z / 1.15, MIN_ZOOM, MAX_ZOOM))}>
                −
              </button>
              <button type="button" className="lm-btn lm-zoom-label" onClick={fitToView}>
                {Math.round(zoom * 100)}%
              </button>
              <button type="button" className="lm-btn" onClick={() => setZoom((z) => clamp(z * 1.15, MIN_ZOOM, MAX_ZOOM))}>
                +
              </button>
              <button type="button" className="lm-btn" onClick={fitToView}>
                Вписать
              </button>
              <button
                type="button"
                className={`lm-btn${linkMode ? ' is-active' : ''}`}
                aria-pressed={linkMode}
                onClick={() => {
                  setLinkMode((prev) => !prev)
                  setLinkFromId(null)
                  setLinkMessage(
                    !linkMode
                      ? 'Режим связи: кликните два листа из разных веток'
                      : '',
                  )
                }}
              >
                Связь
              </button>
              <button
                type="button"
                className={`lm-btn${isFullscreen ? ' is-active' : ''}`}
                aria-pressed={isFullscreen}
                onClick={() => void toggleFullscreen()}
                title={isFullscreen ? 'Выйти из полного экрана (Esc)' : 'На весь экран'}
              >
                {isFullscreen ? 'Свернуть' : 'На весь экран'}
              </button>
              <button
                type="button"
                className="lm-btn"
                onClick={exportMarkdown}
                title="Скачать карту в Markdown (Obsidian)"
              >
                Выгрузить MD
              </button>
              <button
                type="button"
                className="lm-btn"
                onClick={exportAnki}
                title="Скачать колоду Anki (тема → ответ) для импорта"
              >
                Anki ↓
              </button>
              <button
                type="button"
                className={`lm-btn${ankiOpen ? ' is-active' : ''}`}
                onClick={() => setAnkiOpen(true)}
                title="Повторение карточек в браузере"
              >
                Anki ▶
              </button>
            </div>

            <p className="lm-stats">
              {branches.length - hiddenSet.size}/{branchCount} веток · показано {visibleCount} /{' '}
              {nodeCount} · глубина {depth}
              {hiddenSet.size > 0 ? ` · скрыто ${hiddenSet.size}` : ''}
              {crossLinks.length > 0 ? ` · связей ${crossLinks.length}` : ''}
              {activeTags.length > 0 ? ` · теги: ${activeTags.map((t) => `#${t}`).join(' ')}` : ''}
            </p>
            {linkMessage ? <p className="lm-link-hint">{linkMessage}</p> : null}
          </div>
        </section>
      </div>

      {allTags.length > 0 ? (
        <div className="lm-tags-bar" role="group" aria-label="Фильтр по тегам">
          <div className="lm-branches-head">
            <span className="lm-search-label">Теги</span>
            {activeTags.length > 0 ? (
              <button type="button" className="lm-btn" onClick={() => setActiveTags([])}>
                Сбросить фильтр
              </button>
            ) : null}
          </div>
          <ul className="lm-tag-filter-list">
            {allTags.map((tag) => {
              const color = resolveTagColor(tag, tagColors)
              const isActive = activeTags.includes(tag)
              return (
                <li key={tag} className="lm-tag-filter-item">
                  <label className="lm-tag-color" title={`Цвет «${tag}»`}>
                    <span className="lm-tag-color-swatch" style={{ background: color }} />
                    <input
                      type="color"
                      value={color}
                      aria-label={`Цвет тега ${tag}`}
                      onChange={(event) => {
                        const hex = event.target.value
                        setTagColors((prev) => {
                          const next = setTagColor(prev, tag, hex)
                          saveTagColors(next)
                          return next
                        })
                      }}
                    />
                  </label>
                  <button
                    type="button"
                    className={`lm-tag-filter-chip${isActive ? ' is-active' : ''}`}
                    style={{
                      borderColor: color,
                      background: isActive ? `${color}33` : undefined,
                      color: isActive ? color : undefined,
                    }}
                    aria-pressed={isActive}
                    onClick={() => toggleTagFilter(tag)}
                    title={isActive ? `Убрать фильтр «${tag}»` : `Фильтр по «${tag}»`}
                  >
                    #{tag}
                  </button>
                </li>
              )
            })}
          </ul>
          <p className="lm-viewport-hint">
            Клик по тегу — фильтр · цветной кружок — назначить цвет узлам с этим тегом
          </p>
        </div>
      ) : null}

      <div className="lm-branches" role="group" aria-label="Ветки карты">
        <div className="lm-branches-head">
          <span className="lm-search-label">Ветки</span>
          {hiddenSet.size > 0 ? (
            <button type="button" className="lm-btn" onClick={showAllBranches}>
              Показать все
            </button>
          ) : null}
        </div>
        <ul className="lm-branch-chips">
          {branches.map((branch) => {
            const isHidden = hiddenSet.has(branch.id)
            const isCurrent = selectedId === branch.id || l1Branch?.id === branch.id
            return (
              <li key={branch.id} className={`lm-branch-chip-wrap${isHidden ? ' is-hidden' : ''}`}>
                <button
                  type="button"
                  className={`lm-branch-chip${isHidden ? ' is-hidden' : ''}${isCurrent ? ' is-current' : ''}`}
                  title={isHidden ? `Показать «${branch.title}»` : `Открыть «${branch.title}»`}
                  onClick={() => {
                    if (isHidden) {
                      showBranch(branch.id)
                    }
                    selectNode(branch.id)
                  }}
                >
                  {branch.title}
                </button>
                {!isHidden ? (
                  <button
                    type="button"
                    className="lm-branch-hide"
                    aria-label={`Скрыть ветку ${branch.title}`}
                    title="Скрыть ветку"
                    onClick={() => hideBranch(branch.id)}
                  >
                    ×
                  </button>
                ) : null}
              </li>
            )
          })}
        </ul>
      </div>

      <div
        ref={viewportRef}
        className="lm-viewport"
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        role="application"
        aria-label="Интерактивная mind map"
      >
        <div
          className="lm-canvas"
          style={{
            width: layout.width,
            height: layout.height,
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          }}
        >
          <svg
            className="lm-svg"
            width={layout.width}
            height={layout.height}
            viewBox={`0 0 ${layout.width} ${layout.height}`}
          >
            <defs>
              <marker
                id="lm-arrow"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="7"
                markerHeight="7"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" className="lm-arrow-head" />
              </marker>
            </defs>
            <g transform={`translate(${layout.originX} ${layout.originY})`}>
              {layout.edges.map((edge) => (
                <path
                  key={edge.id}
                  d={edge.d}
                  className="lm-edge"
                  markerEnd="url(#lm-arrow)"
                  fill="none"
                />
              ))}
              {layout.nodes.map((node) => {
                const isSelected = node.id === selectedId
                const isRoot = node.depth === 0
                const isLinkFrom = linkMode && linkFromId === node.id
                const leaf = findNode(root, node.id)
                const canLink = linkMode && isLeafNode(leaf)
                const nodeTags = tagsByNodeId.get(node.id) || []
                const primaryTag = pickPrimaryTag(nodeTags, activeTags)
                const tagColor = primaryTag ? resolveTagColor(primaryTag, tagColors) : null
                return (
                  <g
                    key={node.id}
                    className={`lm-node lm-node-d${Math.min(node.depth, 5)}${isSelected ? ' is-selected' : ''}${isRoot ? ' is-root' : ''}${isLinkFrom ? ' is-link-from' : ''}${linkMode && canLink ? ' is-linkable' : ''}${linkMode && !canLink && !isRoot ? ' is-link-disabled' : ''}${tagColor ? ' has-tag-color' : ''}`}
                    transform={`translate(${node.x - node.width / 2} ${node.y - node.height / 2})`}
                    onClick={(event) => {
                      event.stopPropagation()
                      onNodeClick(node.id)
                    }}
                    style={{ cursor: linkMode ? (canLink ? 'crosshair' : 'not-allowed') : 'pointer' }}
                  >
                    <title>
                      {node.fullTitle}
                      {node.description ? `\n\n${node.description}` : ''}
                      {nodeTags.length ? `\n\n#${nodeTags.join(' #')}` : ''}
                      {node.hasHiddenChildren ? '\n\nКлик — показать следующий уровень' : ''}
                    </title>
                    <rect
                      width={node.width}
                      height={node.height}
                      rx={isRoot ? 28 : 10}
                      ry={isRoot ? 28 : 10}
                      className="lm-node-shape"
                      style={
                        tagColor
                          ? { stroke: tagColor, strokeWidth: isSelected ? 2.6 : 2 }
                          : undefined
                      }
                    />
                    {tagColor ? (
                      <circle
                        cx={isRoot ? 14 : 8}
                        cy={isRoot ? 14 : 8}
                        r={isRoot ? 5 : 3.5}
                        fill={tagColor}
                        className="lm-node-tag-dot"
                      />
                    ) : null}
                    <text
                      x={node.width / 2}
                      y={node.height / 2}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      className="lm-node-text"
                    >
                      {(node.titleLines?.length ? node.titleLines : [node.title]).map(
                        (line, lineIndex, lines) => (
                          <tspan
                            key={`${node.id}-l${lineIndex}`}
                            x={node.width / 2}
                            dy={
                              lineIndex === 0
                                ? lines.length > 1
                                  ? '-0.55em'
                                  : '0.35em'
                                : '1.2em'
                            }
                          >
                            {line}
                          </tspan>
                        ),
                      )}
                    </text>
                    {node.hasHiddenChildren ? (
                      <circle
                        cx={node.side >= 0 ? node.width - 6 : 6}
                        cy={node.height - 6}
                        r={4}
                        className="lm-node-more"
                      />
                    ) : null}
                  </g>
                )
              })}
              {drawnCrossLinks.map((link) => {
                const removeScale = 1 / zoom
                const hitWidth = Math.max(16, 18 / zoom)
                const removeLink = (event: { stopPropagation: () => void }) => {
                  event.stopPropagation()
                  onRemoveCrossLink(link.a, link.b)
                }
                const onRemoveKeyDown = (event: ReactKeyboardEvent<SVGGElement>) => {
                  if (event.key !== 'Enter' && event.key !== ' ') {
                    return
                  }
                  event.preventDefault()
                  removeLink(event)
                }
                return (
                  <g
                    key={link.key}
                    className="lm-cross-link"
                    role="button"
                    tabIndex={0}
                    aria-label={`Удалить связь «${link.titleA}» — «${link.titleB}»`}
                    onPointerDown={(event) => event.stopPropagation()}
                    onClick={removeLink}
                    onKeyDown={onRemoveKeyDown}
                  >
                    <title>
                      Удалить связь «{link.titleA}» — «{link.titleB}»
                    </title>
                    <path
                      d={link.d}
                      className="lm-cross-edge-hit"
                      fill="none"
                      strokeWidth={hitWidth}
                    />
                    <path d={link.d} className="lm-cross-edge" fill="none" />
                    <g
                      className="lm-cross-remove"
                      transform={`translate(${link.midX} ${link.midY}) scale(${removeScale})`}
                    >
                      <circle r="11" className="lm-cross-remove-bg" />
                      <path
                        d="M -4.2 -4.2 L 4.2 4.2 M 4.2 -4.2 L -4.2 4.2"
                        className="lm-cross-remove-x"
                      />
                    </g>
                  </g>
                )
              })}
            </g>
          </svg>
        </div>
        <p className="lm-viewport-hint">
          Колёсико — масштаб · перетаскивание — панорама · клик по узлу с детьми — следующий уровень
          {linkMode ? ' · режим связи: два листа разных веток' : ' · «Связь» — пунктир между ветками'}
          {drawnCrossLinks.length > 0 ? ' · × на пунктире удаляет связь' : ''}
          {isFullscreen ? ' · Esc — выйти из полного экрана' : ''}
        </p>
      </div>

      <section className="lm-panel" aria-labelledby="lm-panel-title">
        <header className="lm-panel-header">
          <div>
            <p className="lm-panel-eyebrow">Выбранный узел</p>
            <h2 id="lm-panel-title" className="lm-panel-title">
              {selectedNode.title}
            </h2>
          </div>
        </header>

        <nav className="lm-breadcrumb" aria-label="Путь">
          {selectedPath.map((node, index) => (
            <button
              key={node.id}
              type="button"
              className="lm-crumb"
              onClick={() => selectNode(node.id)}
            >
              {index > 0 ? <span className="lm-crumb-sep">/</span> : null}
              {node.title}
            </button>
          ))}
        </nav>

        {leafPanel?.isLeaf ? (
          <LeafDetailPanel
            data={leafPanel}
            root={root}
            nodeId={selectedId}
            learnSlug={selectedNode.learnSlug}
            notes={leafNotes}
            posts={publishedPosts}
            tagColors={tagColors}
            onSelectRelated={(id) => selectNode(id)}
            onSaveNote={(description, tags) => {
              const next = upsertLeafNote(leafNotes, selectedId, { description, tags })
              setLeafNotes(next)
              saveLeafNotes(next)
            }}
            onTagClick={(tag) => toggleTagFilter(normalizeTag(tag))}
          />
        ) : null}

        {l1Branch && learnLink && !leafPanel?.isLeaf ? (
          <LearningMapLearnPanel
            branchTitle={l1Branch.title}
            link={learnLink}
            posts={publishedPosts}
            isReady={learnReady}
            completedSlugs={completedSlugs}
          />
        ) : null}

        {l1Branch && !hiddenSet.has(l1Branch.id) ? (
          <p className="lm-branch-actions">
            <button
              type="button"
              className="lm-btn"
              onClick={() => hideBranch(l1Branch.id)}
            >
              Скрыть ветку «{l1Branch.title}»
            </button>
          </p>
        ) : null}

        {!leafPanel?.isLeaf && selectedLeafLinks.length > 0 ? (
          <div className="lm-cross-links">
            <h3 className="lm-learn-subtitle">Пунктирные связи</h3>
            <ul className="lm-detail-list">
              {selectedLeafLinks.map((link) => {
                const otherId = link.a === selectedId ? link.b : link.a
                const other = findNode(root, otherId)
                return (
                  <li key={`${link.a}|${link.b}`} className="lm-cross-link-row">
                    <button
                      type="button"
                      className="lm-detail-link"
                      onClick={() => selectNode(otherId)}
                    >
                      ↔ {other?.title || otherId}
                    </button>
                    <button
                      type="button"
                      className="lm-btn"
                      onClick={() => onRemoveCrossLink(link.a, link.b)}
                    >
                      Удалить
                    </button>
                  </li>
                )
              })}
            </ul>
          </div>
        ) : null}

        {selectedNode.children.length === 0 ? (
          leafPanel?.isLeaf ? null : (
            <p className="lm-detail-empty">Листовой узел — тема для повторения.</p>
          )
        ) : (
          <ul className="lm-detail-list lm-detail-list-flat">
            {selectedNode.children.map((child) => (
              <li key={child.id}>
                <button
                  type="button"
                  className="lm-detail-link"
                  onClick={() => selectNode(child.id, true)}
                >
                  {child.title}
                  {child.children.length > 0 ? (
                    <span className="lm-tree-count">{child.children.length}</span>
                  ) : null}
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {ankiOpen ? (
        <AnkiStudy
          cards={ankiCardsAll}
          topics={ankiTopics}
          allTags={ankiTagOptions}
          tagColors={tagColors}
          initialBranchIds={
            l1Branch && !hiddenSet.has(l1Branch.id) && selectedId !== root.id
              ? [l1Branch.id]
              : []
          }
          initialTags={activeTags}
          onClose={() => setAnkiOpen(false)}
          onReview={(card: AnkiCard, ease) => {
            if (!getSiteAuthSession()?.accessToken) {
              return
            }
            void siteReviewAnkiCard({
              card_id: card.id,
              front: card.front,
              back: card.back,
              source_key: card.learn?.slug
                ? `learn/${card.learn.slug}`
                : `map/${card.branchId || 'root'}`,
              ease,
            }).catch(() => undefined)
          }}
        />
      ) : null}
    </div>
  )
}
