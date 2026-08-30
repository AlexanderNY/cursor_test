import { useEffect, useState } from 'react'
import {
  collectAnkiCards,
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

  useEffect(() => {
    setDescription(data.customAnswer)
    setTagsText(data.tags.join(', '))
    setSavedFlash(false)
  }, [data.title, data.customAnswer, data.tags])

  if (!data.isLeaf) {
    return null
  }

  const draftNotes: Record<string, LeafNote> = {
    ...notes,
    [nodeId]: {
      description: description.trim(),
      tags: tagsText
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean),
    },
  }
  const ankiCard: AnkiCard | null = description.trim()
    ? collectAnkiCards(root, {
        notes: draftNotes,
        nodeId,
        onlyLeaves: true,
        posts,
      })[0] || null
    : null

  return (
    <div className="lm-leaf-detail">
      <h3 className="lm-learn-subtitle">Краткий ответ (Anki)</h3>
      <p className="lm-leaf-path">{data.pathTitles.slice(1).join(' → ')}</p>
      {!data.customAnswer && data.description ? (
        <p className="lm-leaf-auto-hint">{data.description}</p>
      ) : null}
      <textarea
        className="lm-leaf-description"
        rows={4}
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        placeholder="Краткий ответ на оборот карты: определение, формула, суть…"
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
          Сохранить ответ и теги
        </button>
        {savedFlash ? <span className="lm-leaf-saved">Сохранено в браузере</span> : null}
      </div>

      <h3 className="lm-learn-subtitle">Anki-карта</h3>
      {ankiCard ? (
        <div className="lm-anki-preview">
          <div className="lm-anki-preview-face">
            <span className="lm-anki-side-label">Тема</span>
            <p>{ankiCard.front}</p>
          </div>
          <div className="lm-anki-preview-face">
            <span className="lm-anki-side-label">Ответ</span>
            <p>{ankiCard.back}</p>
          </div>
          {ankiCard.learn ? (
            <div className="lm-anki-preview-face">
              <span className="lm-anki-side-label">Конспект Learn</span>
              <p className="lm-anki-learn-meta">
                {ankiCard.learn.episode} · {ankiCard.learn.title}
              </p>
              <p>{ankiCard.learn.excerpt}</p>
              <Link to={ankiCard.learn.href} className="lm-btn" style={{ marginTop: '0.45rem' }}>
                Статья →
              </Link>
            </div>
          ) : null}
          <button
            type="button"
            className="lm-btn"
            onClick={() => {
              onSaveNote(
                description.trim(),
                tagsText
                  .split(',')
                  .map((tag) => tag.trim())
                  .filter(Boolean),
              )
              downloadSingleAnkiCard(ankiCard)
            }}
          >
            Скачать карту Anki
          </button>
        </div>
      ) : (
        <p className="lm-detail-empty">
          Введите краткий ответ выше — карта «тема → ответ» сформируется здесь.
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
