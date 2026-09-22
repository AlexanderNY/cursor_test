import { useEffect, useRef, useState, type ReactNode } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { AdminJumpNav } from '@/components/admin-jump-nav'
import { PageShell } from '@/components/page-shell'
import { StructuredPostEditor } from '@/components/structured-post-editor'
import {
  getSortedRubrics,
  LEARN_LEVELS,
  LEARN_PROFILES,
  hasKnowledgeMapTag,
  withKnowledgeMapTag,
  type LearnLink,
  type LearnLevelId,
  type LearnProfileId,
  type LearnRubricId,
} from '@/data/learn'
import { apiGetArticleTemplate, apiImportPostMd } from '@/data/learn/learn-api'
import {
  downloadLearnArticleFile,
  downloadLearnArticleTemplate,
  parseLearnArticleFile,
  readTextFile,
} from '@/data/learn/learn-article-file'
import {
  createEmptyPost,
  fromDatetimeLocalValue,
  getLearnPostBySlug,
  loadLearnPosts,
  normalizeLearnMeta,
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

function listToText(values: string[]): string {
  return values.join(', ')
}

function textToList(text: string): string[] {
  return text
    .split(/[,;\n]/)
    .map((part) => part.trim())
    .filter(Boolean)
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

function LearnEditFrame({
  embedded,
  children,
}: {
  embedded: boolean
  children: ReactNode
}) {
  if (embedded) {
    return <div className="account-embed">{children}</div>
  }
  return <PageShell variant="admin">{children}</PageShell>
}

export type LearnAdminEditPageProps = {
  embedded?: boolean
  slug?: string
  forceNew?: boolean
  onBack?: () => void
  onSaved?: (slug: string) => void
}

export function LearnAdminEditPage({
  embedded = false,
  slug: slugProp,
  forceNew = false,
  onBack,
  onSaved,
}: LearnAdminEditPageProps = {}) {
  const { slug: slugParam } = useParams()
  const slug = slugProp ?? slugParam
  const navigate = useNavigate()
  const isNew = forceNew || !slug || slug === 'new'
  const rubrics = getSortedRubrics()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [form, setForm] = useState<LearnPostInput | null>(null)
  const [structured, setStructured] = useState<StructuredPost>(EMPTY_LEARN_STRUCTURED_POST)
  const [linksText, setLinksText] = useState('')
  const [tagsText, setTagsText] = useState('')
  const [prerequisitesText, setPrerequisitesText] = useState('')
  const [seoKeywordsText, setSeoKeywordsText] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [isSaved, setIsSaved] = useState(false)
  const [loading, setLoading] = useState(true)
  const [missing, setMissing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [fileBusy, setFileBusy] = useState(false)

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
            setTagsText('')
            setPrerequisitesText('')
            setSeoKeywordsText('')
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
        const meta = normalizeLearnMeta(existing)
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
          ...meta,
        }
        if (!cancelled) {
          setForm(next)
          setStructured(nextStructured)
          setLinksText(linksToText(next.links))
          setTagsText(listToText(meta.tags))
          setPrerequisitesText(listToText(meta.prerequisites))
          setSeoKeywordsText(listToText(meta.seoKeywords))
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
      <LearnEditFrame embedded={embedded}>
        <p className="learn-section-note">Загрузка…</p>
      </LearnEditFrame>
    )
  }

  if (missing || !form) {
    if (embedded) {
      return (
        <LearnEditFrame embedded>
          <p className="learn-section-note">Запись не найдена</p>
          {onBack ? (
            <button type="button" className="back-link" onClick={onBack}>
              ← К списку записей
            </button>
          ) : null}
        </LearnEditFrame>
      )
    }
    return <Navigate to="/game/learn/admin" replace />
  }

  const updateField = <K extends keyof LearnPostInput>(key: K, value: LearnPostInput[K]): void => {
    setForm((current) => (current ? { ...current, [key]: value } : current))
    setIsSaved(false)
  }

  const toggleProfile = (id: LearnProfileId): void => {
    const current = form.profiles || []
    const next = current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    updateField('profiles', next)
  }

  const onKnowledgeMap = hasKnowledgeMapTag(textToList(tagsText))

  const toggleKnowledgeMap = (enabled: boolean): void => {
    const nextTags = withKnowledgeMapTag(textToList(tagsText), enabled)
    setTagsText(listToText(nextTags))
    updateField('tags', nextTags)
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

  const applyImported = (payload: LearnPostInput, warnings: string[]): void => {
    const meta = normalizeLearnMeta(payload)
    const nextStructured = hydrateLearnStructured(payload.structured, {
      lab: payload.lab,
      cheatsheet: payload.cheatsheet,
      cheatsheetFormat: 'html',
      diagram: payload.diagram,
    })
    setForm({
      ...payload,
      ...meta,
      structured: nextStructured,
      theoryFormat: 'markdown',
      labFormat: 'markdown',
      cheatsheetFormat: 'html',
    })
    setStructured(nextStructured)
    setLinksText(linksToText(payload.links || []))
    setTagsText(listToText(meta.tags))
    setPrerequisitesText(listToText(meta.prerequisites))
    setSeoKeywordsText(listToText(meta.seoKeywords))
    setIsSaved(false)
    setError('')
    setNotice(
      warnings.length > 0
        ? `Файл загружен в форму. Предупреждения: ${warnings.join('; ')}`
        : 'Файл загружен в форму. Сохраните, чтобы записать в БД.',
    )
  }

  const exportPostFile = (): void => {
    if (!form) {
      return
    }
    downloadLearnArticleFile({
      ...form,
      links: textToLinks(linksText),
      tags: textToList(tagsText),
      prerequisites: textToList(prerequisitesText),
      seoKeywords: textToList(seoKeywordsText),
      structured,
      theory: theoryFromStructured(structured),
      lab: (structured.lab || '').trim(),
      cheatsheet: (structured.cheatsheetHtml || '').trim(),
      diagram: structured.diagrams.find((d) => d.mermaid.trim())?.mermaid || '',
    })
  }

  const downloadTemplate = (): void => {
    setFileBusy(true)
    setError('')
    void (async () => {
      try {
        const markdown = await apiGetArticleTemplate()
        downloadLearnArticleTemplate(markdown)
        setNotice('Шаблон скачан')
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Не удалось скачать шаблон')
      } finally {
        setFileBusy(false)
      }
    })()
  }

  const importPostFile = (file: File | null, saveToDb: boolean): void => {
    if (!file) {
      return
    }
    setFileBusy(true)
    setError('')
    setNotice('')
    void (async () => {
      try {
        const text = await readTextFile(file)
        if (saveToDb) {
          const result = await apiImportPostMd(text, { save: true })
          applyImported(
            {
              ...result.post,
              theoryFormat: 'markdown',
              labFormat: 'markdown',
              cheatsheetFormat: 'html',
              structured: result.post.structured,
            },
            result.warnings,
          )
          setIsSaved(true)
          setNotice(
            result.warnings.length > 0
              ? `Импортировано и сохранено. Предупреждения: ${result.warnings.join('; ')}`
              : `Импортировано и сохранено: ${result.post.slug}`,
          )
          if (onSaved) {
            onSaved(result.post.slug)
          } else if (isNew || slug !== result.post.slug) {
            navigate(`/game/learn/admin/${result.post.slug}`, { replace: true })
          }
          return
        }
        const parsed = parseLearnArticleFile(text, form || undefined)
        const { warnings, ...payload } = parsed
        applyImported(payload, warnings)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Не удалось загрузить файл')
      } finally {
        setFileBusy(false)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      }
    })()
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
    setNotice('')
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
        const meta = normalizeLearnMeta({
          ...form,
          tags: textToList(tagsText),
          prerequisites: textToList(prerequisitesText),
          seoKeywords: textToList(seoKeywordsText),
        })
        const saved = await saveLearnPost({
          ...form,
          ...meta,
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
        if (onSaved) {
          onSaved(saved.slug)
        } else if (isNew || slug !== saved.slug) {
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
    <LearnEditFrame embedded={embedded}>
      {onBack ? (
        <button type="button" className="back-link" onClick={onBack}>
          ← К списку записей
        </button>
      ) : (
        <Link to="/game/learn/admin" className="back-link">
          ← К списку записей
        </Link>
      )}

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

      <div className="learn-admin-actions" style={{ marginBottom: '1rem' }}>
        <button
          type="button"
          className="learn-admin-btn"
          disabled={fileBusy}
          onClick={downloadTemplate}
        >
          Скачать шаблон
        </button>
        <button type="button" className="learn-admin-btn" disabled={fileBusy} onClick={exportPostFile}>
          Скачать .md
        </button>
        <button
          type="button"
          className="learn-admin-btn"
          disabled={fileBusy}
          onClick={() => {
            fileInputRef.current?.setAttribute('data-save', '0')
            fileInputRef.current?.click()
          }}
        >
          Загрузить .md
        </button>
        <button
          type="button"
          className="learn-admin-btn"
          disabled={fileBusy}
          onClick={() => {
            fileInputRef.current?.setAttribute('data-save', '1')
            fileInputRef.current?.click()
          }}
        >
          Загрузить и сохранить
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".md,.markdown,.txt,text/markdown,text/plain"
          hidden
          onChange={(event) => {
            const saveToDb = fileInputRef.current?.getAttribute('data-save') === '1'
            void importPostFile(event.target.files?.[0] || null, saveToDb)
          }}
        />
      </div>
      <p className="learn-section-note" style={{ marginTop: 0 }}>
        Файл: YAML frontmatter (трек, уровень, теги, автор, обложка, SEO) + разделы ## Введение /
        Раздел / Лаба / Схема / Тест / Шпаргалка / Anki. «Загрузить .md» заполняет форму; запись в
        БД — «Сохранить» или «Загрузить и сохранить».
      </p>

      <AdminJumpNav
        items={[
          { id: 'edit-meta', label: 'Мета' },
          { id: 'edit-labels', label: 'Лейблы' },
          { id: 'edit-seo', label: 'SEO' },
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

          <label className="learn-admin-field">
            <span>Лид (excerpt)</span>
            <input
              value={form.excerpt}
              onChange={(event) => updateField('excerpt', event.target.value)}
              placeholder="1–2 предложения для карточки"
            />
          </label>

          <label className="learn-admin-field">
            <span>Длительность, мин</span>
            <input
              type="number"
              min={0}
              value={form.durationMin || 0}
              onChange={(event) => updateField('durationMin', Number(event.target.value) || 0)}
            />
          </label>
        </div>

        <div id="edit-labels" className="admin-jump-target" style={{ marginTop: '1rem' }}>
          <h3 className="learn-panel-heading">Лейблы</h3>
          <fieldset className="learn-admin-field">
            <legend>Трек (профили карты)</legend>
            <div className="learn-label-checks">
              {LEARN_PROFILES.map((profile) => (
                <label key={profile.id} className="learn-label-check">
                  <input
                    type="checkbox"
                    checked={form.profiles.includes(profile.id)}
                    onChange={() => toggleProfile(profile.id)}
                  />{' '}
                  {profile.label}
                </label>
              ))}
            </div>
          </fieldset>

          <label className="learn-admin-field learn-label-check" style={{ marginTop: '0.75rem' }}>
            <span>
              <input
                type="checkbox"
                checked={onKnowledgeMap}
                onChange={(event) => toggleKnowledgeMap(event.target.checked)}
              />{' '}
              Добавить на карту знаний
            </span>
            <span className="learn-section-note" style={{ margin: 0 }}>
              Ставит лейбл «собеседование» — статья попадает в материалы к карте / собеседованию.
            </span>
          </label>

          <div className="learn-admin-grid">
            <label className="learn-admin-field">
              <span>Уровень</span>
              <select
                value={form.level}
                onChange={(event) =>
                  updateField('level', event.target.value as LearnLevelId | '')
                }
              >
                <option value="">— не указан —</option>
                {LEARN_LEVELS.map((level) => (
                  <option key={level.id} value={level.id}>
                    {level.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="learn-admin-field">
              <span>Теги (через запятую)</span>
              <input
                value={tagsText}
                onChange={(event) => setTagsText(event.target.value)}
                placeholder="jwt, sql, rest"
              />
            </label>

            <label className="learn-admin-field">
              <span>Prerequisites (slug через запятую)</span>
              <input
                value={prerequisitesText}
                onChange={(event) => setPrerequisitesText(event.target.value)}
                placeholder="map-auth-basics"
              />
            </label>

            <label className="learn-admin-field">
              <span>Автор</span>
              <input
                value={form.author}
                onChange={(event) => updateField('author', event.target.value)}
              />
            </label>

            <label className="learn-admin-field">
              <span>URL автора</span>
              <input
                value={form.authorUrl}
                onChange={(event) => updateField('authorUrl', event.target.value)}
                placeholder="https://t.me/…"
              />
            </label>

            <label className="learn-admin-field">
              <span>Обложка (URL)</span>
              <input
                value={form.coverUrl}
                onChange={(event) => updateField('coverUrl', event.target.value)}
                placeholder="https://…"
              />
            </label>
          </div>
          {form.coverUrl.trim() ? (
            <div className="learn-cover-preview">
              <img src={form.coverUrl.trim()} alt="Превью обложки" />
            </div>
          ) : null}
        </div>

        <div id="edit-seo" className="admin-jump-target" style={{ marginTop: '1rem' }}>
          <h3 className="learn-panel-heading">SEO</h3>
          <div className="learn-admin-grid">
            <label className="learn-admin-field">
              <span>seoTitle</span>
              <input
                value={form.seoTitle}
                onChange={(event) => updateField('seoTitle', event.target.value)}
                placeholder="fallback: заголовок"
              />
            </label>
            <label className="learn-admin-field">
              <span>seoDescription</span>
              <input
                value={form.seoDescription}
                onChange={(event) => updateField('seoDescription', event.target.value)}
                placeholder="fallback: excerpt / intro"
              />
            </label>
            <label className="learn-admin-field">
              <span>seoKeywords (через запятую)</span>
              <input
                value={seoKeywordsText}
                onChange={(event) => setSeoKeywordsText(event.target.value)}
              />
            </label>
            <label className="learn-admin-field">
              <span>canonicalUrl</span>
              <input
                value={form.canonicalUrl}
                onChange={(event) => updateField('canonicalUrl', event.target.value)}
                placeholder="https://9to18.ru/game/learn/…"
              />
            </label>
          </div>
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

        {error ? (
          <p className="learn-section-note" style={{ color: '#b91c1c' }}>
            {error}
          </p>
        ) : null}
        {notice ? <p className="learn-admin-ok">{notice}</p> : null}
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
    </LearnEditFrame>
  )
}
