import { useEffect, useMemo, useState } from 'react'
import {
  collectAnkiCards,
  downloadAnkiDeck,
  downloadSingleAnkiCard,
  type AnkiCard,
} from '@/data/learning-map/anki-cards'
import type { LeafNote } from '@/data/learning-map/leaf-notes'
import type { LeafPanelData } from '@/data/learning-map/leaf-panel'
import type { MindNode } from '@/data/learning-map/parse-outline'
import { normalizeTag, resolveTagColor } from '@/data/learning-map/tag-style'
import type { LearnPost } from '@/data/learn/learn-store'
import { Link } from 'react-router-dom'

type LeafDetailPanelProps = {
  data: LeafPanelData
  root: MindNode
  nodeId: string
  learnSlug?: string
  notes: Record<string, LeafNote>
  posts?: LearnPost[]
  tagColors: Record<string, string>
  onSelectRelated: (id: string) => void
  onSaveNote: (description: string, tags: string[]) => void
  onTagClick?: (tag: string) => void
}

export function LeafDetailPanel({
  data,
  root,
  nodeId,
  learnSlug,
  notes,
  posts = [],
  tagColors,
  onSelectRelated,
  onSaveNote,
  onTagClick,
}: LeafDetailPanelProps) {
  const [description, setDescription] = useState(data.customAnswer)
  const [tagsText, setTagsText] = useState(data.tags.join(', '))
  const [savedFlash, setSavedFlash] = useState(false)
  const [ankiIndex, setAnkiIndex] = useState(0)
  const [ankiFlipped, setAnkiFlipped] = useState(false)

  useEffect(() => {
    setDescription(data.customAnswer)
    setTagsText(data.tags.join(', '))
    setSavedFlash(false)
  }, [data.title, data.customAnswer, data.tags])

  useEffect(() => {
    setAnkiIndex(0)
    setAnkiFlipped(false)
  }, [nodeId, learnSlug])

  const draftNotes: Record<string, LeafNote> = useMemo(
    () => ({
      ...notes,
      [nodeId]: {
        description: description.trim(),
        tags: tagsText
          .split(',')
          .map((tag) => tag.trim())
          .filter(Boolean),
      },
    }),
    [notes, nodeId, description, tagsText],
  )

  const ankiDeck: AnkiCard[] = useMemo(
    () =>
      collectAnkiCards(root, {
        notes: draftNotes,
        nodeId,
        onlyLeaves: true,
        posts,
      }),
    [root, draftNotes, nodeId, posts],
  )

  useEffect(() => {
    if (ankiIndex >= ankiDeck.length) {
      setAnkiIndex(0)
    }
  }, [ankiDeck.length, ankiIndex])

  if (!data.isLeaf) {
    return null
  }

  const linkedPost = learnSlug
    ? posts.find((post) => post.slug === learnSlug)
    : undefined

  const activeCard = ankiDeck[ankiIndex] || null

  return (
    <div className="lm-leaf-detail">
      <h3 className="lm-learn-subtitle">Статья Learn</h3>
      {learnSlug ? (
        <p className="lm-leaf-path">
          {linkedPost ? (
            <>
              {linkedPost.episode} · {linkedPost.shortTitle || linkedPost.title}{' '}
              <Link to={`/game/learn/${learnSlug}`} className="lm-btn" style={{ marginLeft: '0.35rem' }}>
                Открыть →
              </Link>
            </>
          ) : (
            <>
              Ожидается статья <code>{learnSlug}</code>{' '}
              <Link to={`/game/learn/${learnSlug}`} className="lm-btn">
                Открыть →
              </Link>
              <span className="lm-detail-empty"> (пока нет в каталоге)</span>
            </>
          )}
        </p>
      ) : (
        <p className="lm-detail-empty">У листа нет привязки learn:slug — добавьте в MD карты.</p>
      )}

      <h3 className="lm-learn-subtitle">Краткий ответ (заметка)</h3>
      <p className="lm-leaf-path">{data.pathTitles.slice(1).join(' → ')}</p>
      {!data.customAnswer && data.description ? (
        <p className="lm-leaf-auto-hint">{data.description}</p>
      ) : null}
      <textarea
        className="lm-leaf-description"
        rows={4}
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        placeholder="Личная заметка (опционально)…"
      />

      <h3 className="lm-learn-subtitle">Теги</h3>
      <div className="lm-tags" aria-label="Теги листа">
        {data.tags.map((tag) => {
          const key = normalizeTag(tag)
          const color = resolveTagColor(key, tagColors)
          return (
            <button
              key={tag}
              type="button"
              className="lm-tag"
              style={{ borderColor: color, color }}
              onClick={() => onTagClick?.(key)}
              title={`Фильтр по #${key}`}
            >
              <span className="lm-tag-dot" style={{ background: color }} />
              #{key}
            </button>
          )
        })}
      </div>
      <input
        className="lm-leaf-tags-input"
        value={tagsText}
        onChange={(event) => setTagsText(event.target.value)}
        placeholder="теги через запятую: sql, indexes, acid"
      />

      <div className="lm-leaf-save-row">
        <button
          type="button"
          className="lm-btn is-active"
          onClick={() => {
            const tags = tagsText
              .split(',')
              .map((tag) => tag.trim())
              .filter(Boolean)
            onSaveNote(description.trim(), tags)
            setSavedFlash(true)
          }}
        >
          Сохранить заметку и теги
        </button>
        {savedFlash ? <span className="lm-leaf-saved">Сохранено в браузере</span> : null}
      </div>

      <h3 className="lm-learn-subtitle">Anki из статьи</h3>
      {activeCard ? (
        <div className="lm-anki-preview">
          <p className="lm-leaf-path">
            Карточка {ankiIndex + 1} / {ankiDeck.length} · колода листа
            {learnSlug ? ` (${learnSlug})` : ''}
          </p>
          <button
            type="button"
            className="lm-anki-preview-face"
            style={{ width: '100%', textAlign: 'left', cursor: 'pointer' }}
            onClick={() => setAnkiFlipped((prev) => !prev)}
          >
            <span className="lm-anki-side-label">{ankiFlipped ? 'Ответ' : 'Вопрос'}</span>
            <p>{ankiFlipped ? activeCard.back : activeCard.front}</p>
          </button>
          {!ankiFlipped ? (
            <p className="lm-detail-empty">Нажмите карточку, чтобы увидеть ответ.</p>
          ) : null}
          {activeCard.learn ? (
            <div className="lm-anki-preview-face">
              <span className="lm-anki-side-label">Learn</span>
              <p className="lm-anki-learn-meta">
                {activeCard.learn.episode} · {activeCard.learn.title}
              </p>
              <Link to={activeCard.learn.href} className="lm-btn" style={{ marginTop: '0.45rem' }}>
                Статья →
              </Link>
            </div>
          ) : null}
          <div className="lm-leaf-save-row" style={{ flexWrap: 'wrap', gap: '0.35rem' }}>
            <button
              type="button"
              className="lm-btn"
              disabled={ankiIndex <= 0}
              onClick={() => {
                setAnkiFlipped(false)
                setAnkiIndex((i) => Math.max(0, i - 1))
              }}
            >
              ← Пред.
            </button>
            <button
              type="button"
              className="lm-btn"
              disabled={ankiIndex >= ankiDeck.length - 1}
              onClick={() => {
                setAnkiFlipped(false)
                setAnkiIndex((i) => Math.min(ankiDeck.length - 1, i + 1))
              }}
            >
              След. →
            </button>
            <button
              type="button"
              className="lm-btn"
              onClick={() => downloadSingleAnkiCard(activeCard)}
            >
              Скачать эту
            </button>
            <button
              type="button"
              className="lm-btn is-active"
              onClick={() =>
                downloadAnkiDeck(
                  ankiDeck,
                  `anki-leaf-${learnSlug || nodeId}.txt`,
                )
              }
            >
              Скачать колоду ({ankiDeck.length})
            </button>
          </div>
        </div>
      ) : (
        <p className="lm-detail-empty">
          Anki появятся после публикации статьи Learn с авторскими карточками (минимум 3).
        </p>
      )}

      <h3 className="lm-learn-subtitle">Связанные листья</h3>
      {data.related.length === 0 ? (
        <p className="lm-detail-empty">
          Пока нет связей. Соседи появятся здесь, а межветочные — через режим «Связь».
        </p>
      ) : (
        <ul className="lm-detail-list lm-detail-list-flat">
          {data.related.map((item) => (
            <li key={`${item.kind}-${item.id}`}>
              <button
                type="button"
                className="lm-detail-link"
                onClick={() => onSelectRelated(item.id)}
              >
                <span>
                  {item.kind === 'cross' ? '↔ ' : '• '}
                  {item.title}
                </span>
                <span className="lm-tree-count">{item.kind === 'cross' ? 'связь' : 'рядом'}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
