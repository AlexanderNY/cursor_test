import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { HtmlEditor } from '@/components/html-editor'
import { PageShell } from '@/components/page-shell'
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
import { plainTextToHtml } from '@/data/learn/sanitize-html'

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

export function LearnAdminEditPage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const isNew = !slug || slug === 'new'
  const rubrics = getSortedRubrics()

  const initial = useMemo((): LearnPostInput | null => {
    if (isNew) {
      const posts = loadLearnPosts()
      const nextOrder = posts.reduce((max, post) => Math.max(max, post.order), 0) + 1
      return createEmptyPost(nextOrder)
    }
    const existing = getLearnPostBySlug(slug)
    if (!existing) {
      return null
    }
    return {
      slug: existing.slug,
      episode: existing.episode,
      title: existing.title,
      shortTitle: existing.shortTitle,
      rubricId: existing.rubricId,
      order: existing.order,
      theory:
        existing.theoryFormat === 'html' ? existing.theory : plainTextToHtml(existing.theory),
      lab: existing.labFormat === 'html' ? existing.lab : plainTextToHtml(existing.lab),
      cheatsheet:
        existing.cheatsheetFormat === 'html'
          ? existing.cheatsheet
          : plainTextToHtml(existing.cheatsheet),
      diagram: existing.diagram,
      links: existing.links,
      theoryFormat: 'html',
      labFormat: 'html',
      cheatsheetFormat: 'html',
      publishedAt: existing.publishedAt,
    }
  }, [isNew, slug])

  const [form, setForm] = useState<LearnPostInput | null>(initial)
  const [linksText, setLinksText] = useState(initial ? linksToText(initial.links) : '')
  const [error, setError] = useState('')
  const [isSaved, setIsSaved] = useState(false)

  useEffect(() => {
    setForm(initial)
    setLinksText(initial ? linksToText(initial.links) : '')
    setError('')
    setIsSaved(false)
  }, [initial])

  if (!form) {
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

    const hasConflict = loadLearnPosts().some(
      (post) => post.slug === normalizedSlug && (isNew || post.slug !== slug),
    )
    if (hasConflict) {
      setError('Такой slug уже занят')
      return
    }

    const saved = saveLearnPost({
      ...form,
      slug: normalizedSlug,
      title: form.title.trim(),
      shortTitle: form.shortTitle.trim() || form.title.trim().slice(0, 24),
      episode: form.episode.trim() || 'S01',
      links: textToLinks(linksText),
      theoryFormat: 'html',
      labFormat: 'html',
      cheatsheetFormat: 'html',
    })

    setIsSaved(true)
    setError('')
    if (isNew || slug !== saved.slug) {
      navigate(`/game/learn/admin/${saved.slug}`, { replace: true })
    }
  }

  return (
    <PageShell>
      <Link to="/game/learn/admin" className="back-link">
        ← К списку записей
      </Link>

      <header className="learn-header">
        <p className="learn-eyebrow">Learn · Админка</p>
        <h1 className="learn-title">{isNew ? 'Новая запись' : 'Редактирование'}</h1>
      </header>

      <form className="learn-admin-form" onSubmit={handleSubmit}>
        <div className="learn-admin-grid">
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
              required
            />
          </label>
        </div>

        <HtmlEditor
          label="Теория"
          value={form.theory}
          onChange={(html) => updateField('theory', html)}
        />
        <HtmlEditor label="Лаба" value={form.lab} onChange={(html) => updateField('lab', html)} />
        <HtmlEditor
          label="Шпаргалка"
          value={form.cheatsheet}
          onChange={(html) => updateField('cheatsheet', html)}
        />

        <label className="learn-admin-field">
          <span>Mermaid-схема</span>
          <textarea
            className="learn-admin-textarea"
            rows={6}
            value={form.diagram}
            onChange={(event) => updateField('diagram', event.target.value)}
          />
        </label>

        <label className="learn-admin-field">
          <span>Ссылки (строка: подпись | url)</span>
          <textarea
            className="learn-admin-textarea"
            rows={4}
            value={linksText}
            onChange={(event) => {
              setLinksText(event.target.value)
              setIsSaved(false)
            }}
          />
        </label>

        {error ? <p className="learn-admin-error">{error}</p> : null}
        {isSaved ? <p className="learn-admin-ok">Сохранено</p> : null}

        <div className="learn-admin-actions">
          <button type="submit" className="learn-admin-btn learn-admin-btn-primary">
            Сохранить
          </button>
          <Link to={`/game/learn/${form.slug}?preview=1`} className="learn-admin-btn">
            Открыть на сайте
          </Link>
        </div>
      </form>
    </PageShell>
  )
}
