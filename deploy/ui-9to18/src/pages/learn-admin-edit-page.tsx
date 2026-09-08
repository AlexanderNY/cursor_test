import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { AdminJumpNav } from '@/components/admin-jump-nav'
import { PageShell } from '@/components/page-shell'
import { StructuredPostEditor } from '@/components/structured-post-editor'
import { getSortedRubrics, type LearnLink, type LearnRubricId } from '@/data/learn'
import {
  createEmptyPost,
  fromDatetimeLocalValue,
  getLearnPostBySlug,
  loadLearnPosts,
  saveLearnPost,
  slugifyTitle,
  toDatetimeLocalValue,
  type LearnPostInput,
} from '@/data/learn/learn-store'
import {
  EMPTY_LEARN_STRUCTURED_POST,
  hydrateLearnStructured,
  serializeStructuredPost,
  type StructuredPost,
  validateLearnStructuredPost,
} from '@/data/site/structured-post'

function linksToText(links: LearnLink[]): string {
  return links.map((link) => `${link.label} | ${link.href}`).join('\n')
}

function textToLinks(text: string): LearnLink[] {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [label, ...rest] = line.split('|')
      const href = rest.join('|').trim() || '#'
      return { label: label.trim(), href }
    })
}

function theoryFromStructured(post: StructuredPost): string {
  const parts = [post.intro.trim()]
  for (const section of post.sections) {
    if (section.heading.trim()) {
      parts.push(`## ${section.heading.trim()}`)
    }
    if (section.body.trim()) {
      parts.push(section.body.trim())
    }
  }
  return parts.filter(Boolean).join('\n\n')
}

export function LearnAdminEditPage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const isNew = !slug || slug === 'new'
  const rubrics = getSortedRubrics()

  const [form, setForm] = useState<LearnPostInput | null>(null)
  const [structured, setStructured] = useState<StructuredPost>(EMPTY_LEARN_STRUCTURED_POST)
  const [linksText, setLinksText] = useState('')
  const [error, setError] = useState('')
  const [isSaved, setIsSaved] = useState(false)
  const [loading, setLoading] = useState(true)
  const [missing, setMissing] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setMissing(false)
    void (async () => {
      try {
        if (isNew) {
          const posts = await loadLearnPosts({ admin: true })
          const nextOrder = posts.reduce((max, post) => Math.max(max, post.order), 0) + 1
          const empty = createEmptyPost(nextOrder)
          if (!cancelled) {
            setForm(empty)
            setStructured(empty.structured ?? EMPTY_LEARN_STRUCTURED_POST)
            setLinksText('')
          }
          return
        }
        const existing = await getLearnPostBySlug(slug!, { admin: true })
        if (!existing) {
          if (!cancelled) setMissing(true)
          return
        }
        const nextStructured = hydrateLearnStructured(existing.structured, {
          lab: existing.lab,
          cheatsheet: existing.cheatsheet,
          cheatsheetFormat: existing.cheatsheetFormat,
          diagram: existing.diagram,
        })
        const next: LearnPostInput = {
          slug: existing.slug,
          episode: existing.episode,
          title: existing.title,
          shortTitle: existing.shortTitle,
          rubricId: existing.rubricId,
          order: existing.order,
          theory: existing.theory,
          lab: existing.lab,
          cheatsheet: existing.cheatsheet,
          diagram: existing.diagram,
          links: existing.links,
          structured: nextStructured,
          theoryFormat: 'markdown',
          labFormat: existing.labFormat === 'html' ? 'html' : 'markdown',
          cheatsheetFormat: existing.cheatsheetFormat === 'html' ? 'html' : 'markdown',
          publishedAt: existing.publishedAt,
        }
        if (!cancelled) {
          setForm(next)
          setStructured(nextStructured)
          setLinksText(linksToText(next.links))
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Ошибка загрузки')
          setMissing(true)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [isNew, slug])

  if (loading) {
    return (
      <PageShell>
        <p className="learn-section-note">Загрузка…</p>
      </PageShell>
    )
  }

  if (missing || !form) {
    return <Navigate to="/game/learn/admin" replace />
  }

  const updateField = <K extends keyof LearnPostInput>(key: K, value: LearnPostInput[K]): void => {
    setForm((current) => (current ? { ...current, [key]: value } : current))
    setIsSaved(false)
  }

  const handleTitleBlur = (): void => {
    if (!isNew || !form) {
      return
    }
    if (form.slug.startsWith('post-')) {
      const nextSlug = slugifyTitle(form.title) || form.slug
      updateField('slug', nextSlug)
    }
  }

  const handleSubmit = (event: FormEvent): void => {
    event.preventDefault()
    if (!form) {
      return
    }

    const normalizedSlug = form.slug.trim().toLowerCase()
    if (!normalizedSlug || !/^[a-z0-9-]+$/.test(normalizedSlug)) {
      setError('Slug: только латиница, цифры и дефис')
      return
    }
    if (!form.title.trim()) {
      setError('Укажите заголовок')
      return
    }
    const validation = validateLearnStructuredPost(structured)
    if (validation.length > 0) {
      setError(validation.join('; '))
      return
    }

    setSaving(true)
    setError('')
    void (async () => {
      try {
        const posts = await loadLearnPosts({ admin: true })
        const hasConflict = posts.some(
          (post) => post.slug === normalizedSlug && (isNew || post.slug !== slug),
        )
        if (hasConflict) {
          setError('Такой slug уже занят')
          return
        }
        const firstDiagram = structured.diagrams.find((d) => d.mermaid.trim())?.mermaid || ''
        const labText = (structured.lab || '').trim()
        const cheatsheetHtml = (structured.cheatsheetHtml || '').trim()
        const saved = await saveLearnPost({
          ...form,
          slug: normalizedSlug,
          title: form.title.trim(),
          shortTitle: form.shortTitle.trim() || form.title.trim().slice(0, 24),
          episode: form.episode.trim() || 'S01',
          links: textToLinks(linksText),
          structured,
          theory: theoryFromStructured(structured),
          lab: labText,
          cheatsheet: cheatsheetHtml,
          diagram: firstDiagram,
          theoryFormat: 'markdown',
          labFormat: 'markdown',
          cheatsheetFormat: 'html',
        })
        setIsSaved(true)
        if (isNew || slug !== saved.slug) {
          navigate(`/game/learn/admin/${saved.slug}`, { replace: true })
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Не удалось сохранить')
      } finally {
        setSaving(false)
      }
    })()
  }

  return (
    <PageShell>
      <Link to="/game/learn/admin" className="back-link">
        ← К списку записей
      </Link>

      <header className="learn-header">
        <p className="learn-eyebrow">Learn · Админка</p>
        <h1 className="learn-title">{isNew ? 'Новая запись' : 'Редактирование'}</h1>
        <p className="learn-section-note">
          Пять блоков: теория, лаба, Mermaid, тест, HTML-шпаргалка + колода Anki. Одна статья =
          один лист карты.
        </p>
        <p className="learn-section-note">
          Лист карты:{' '}
          <code>{`{learn:${form.slug || 'slug'}}`}</code>
          {' · '}
          <Link to="/game/learning-map" className="learn-admin-link">
            Открыть карту обучения
          </Link>
        </p>
      </header>

      <AdminJumpNav
        items={[
          { id: 'edit-meta', label: 'Мета' },
          { id: 'edit-theory', label: 'Теория' },
          { id: 'edit-lab', label: 'Лаба' },
          { id: 'edit-diagrams', label: 'Схемы' },
          { id: 'edit-quiz', label: 'Тест' },
          { id: 'edit-cheatsheet', label: 'Шпаргалка' },
          { id: 'edit-anki', label: 'Anki' },
          { id: 'edit-links', label: 'Ссылки' },
          { id: 'edit-save', label: 'Сохранить' },
        ]}
      />

      <form className="learn-admin-form" onSubmit={handleSubmit}>
        <div id="edit-meta" className="learn-admin-grid admin-jump-target">
          <label className="learn-admin-field">
            <span>Заголовок</span>
            <input
              value={form.title}
              onChange={(event) => updateField('title', event.target.value)}
              onBlur={handleTitleBlur}
              required
            />
          </label>

          <label className="learn-admin-field">
            <span>Короткое имя</span>
            <input
              value={form.shortTitle}
              onChange={(event) => updateField('shortTitle', event.target.value)}
            />
          </label>

          <label className="learn-admin-field">
            <span>Код выпуска</span>
            <input
              value={form.episode}
              onChange={(event) => updateField('episode', event.target.value)}
              placeholder="S01E11"
            />
          </label>

          <label className="learn-admin-field">
            <span>Slug</span>
            <input
              value={form.slug}
              onChange={(event) => updateField('slug', event.target.value)}
              disabled={!isNew}
              required
            />
          </label>

          <label className="learn-admin-field">
            <span>Рубрика</span>
            <select
              value={form.rubricId}
              onChange={(event) => updateField('rubricId', event.target.value as LearnRubricId)}
            >
              {rubrics.map((rubric) => (
                <option key={rubric.id} value={rubric.id}>
                  {rubric.title}
                </option>
              ))}
            </select>
          </label>

          <label className="learn-admin-field">
            <span>Порядок</span>
            <input
              type="number"
              value={form.order}
              onChange={(event) => updateField('order', Number(event.target.value) || 0)}
            />
          </label>

          <label className="learn-admin-field">
            <span>Дата публикации</span>
            <input
              type="datetime-local"
              value={toDatetimeLocalValue(form.publishedAt)}
              onChange={(event) =>
                updateField('publishedAt', fromDatetimeLocalValue(event.target.value))
              }
            />
          </label>
        </div>

        <StructuredPostEditor
          mode="learn"
          value={structured}
          onChange={(next) => {
            setStructured(next)
            setIsSaved(false)
          }}
        />

        <label id="edit-links" className="learn-admin-field admin-jump-target">
          <span>Ссылки (строка: подпись | url)</span>
          <textarea rows={4} value={linksText} onChange={(event) => setLinksText(event.target.value)} />
        </label>

        {error ? <p className="learn-section-note" style={{ color: '#b91c1c' }}>{error}</p> : null}
        {isSaved ? <p className="learn-admin-ok">Сохранено</p> : null}

        <div id="edit-save" className="admin-jump-target">
          <button type="submit" className="learn-admin-btn learn-admin-btn-primary" disabled={saving}>
            {saving ? 'Сохранение…' : 'Сохранить'}
          </button>
          <p className="learn-section-note" style={{ marginTop: '0.5rem' }}>
            Превью JSON: {serializeStructuredPost(structured).length} символов
          </p>
        </div>
      </form>
    </PageShell>
  )
}
