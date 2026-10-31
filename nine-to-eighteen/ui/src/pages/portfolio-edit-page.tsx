import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { PortfolioTileGrid, type PortfolioTileModel } from '@/components/portfolio-tiles'
import {
  portfolioCreateCase,
  portfolioDeleteCase,
  portfolioDeleteCover,
  portfolioFetchCover,
  portfolioGetMine,
  portfolioReorder,
  portfolioSaveMine,
  portfolioSources,
  portfolioUpdateCase,
  portfolioUploadCover,
  type PortfolioCase,
  type PortfolioCaseInput,
  type PortfolioContacts,
  type PortfolioGithubProject,
  type PortfolioProfile,
  type PortfolioResumeOption,
} from '@/data/site/portfolio-api'
import { useSiteAuthSession } from '@/data/site/site-auth'

const MAX_CASES = 6
const MAX_COVER_BYTES = 1_500_000

type MaterialDraft = {
  id: string | null
  title: string
  blurb: string
  link: string
  repoUrl: string
  hasCover: boolean
  source: PortfolioCase | null
}

function suggestHandle(username: string): string {
  const raw = username
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, '')
    .replace(/^-+|-+$/g, '')
  if (raw.length < 3) {
    return ''
  }
  return raw.slice(0, 32)
}

function caseInput(draft: MaterialDraft, blurb: string, link: string): PortfolioCaseInput {
  const source = draft.source
  return {
    title: draft.title,
    role: source?.role || '',
    problem: source?.problem || '',
    work: source?.work || '',
    outcome: source?.outcome || '',
    stack: source?.stack || [],
    repo_url: source?.repoUrl || draft.repoUrl,
    demo_url: link,
    learn_slugs: source?.learnSlugs || [],
    cert_track_id: source?.certTrackId || '',
    blurb,
  }
}

export function PortfolioEditPage() {
  const session = useSiteAuthSession()
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [profile, setProfile] = useState<PortfolioProfile | null>(null)
  const [cases, setCases] = useState<PortfolioCase[]>([])
  const [handle, setHandle] = useState('')
  const [headline, setHeadline] = useState('')
  const [summary, setSummary] = useState('')
  const [isPublished, setIsPublished] = useState(false)
  const [pinnedResumeId, setPinnedResumeId] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [contactUrl, setContactUrl] = useState('')
  const [githubProjects, setGithubProjects] = useState<PortfolioGithubProject[]>([])
  const [resumes, setResumes] = useState<PortfolioResumeOption[]>([])
  const [draft, setDraft] = useState<MaterialDraft | null>(null)
  const [coverUrls, setCoverUrls] = useState<Record<string, string>>({})

  const accessToken = session?.accessToken ?? ''

  const applyMine = useCallback(
    (nextProfile: PortfolioProfile | null, nextCases: PortfolioCase[], username: string) => {
      setProfile(nextProfile)
      setCases(nextCases)
      setHandle(nextProfile?.handle || suggestHandle(username))
      setHeadline(nextProfile?.headline || '')
      setSummary(nextProfile?.summary || '')
      setIsPublished(Boolean(nextProfile?.isPublished))
      setPinnedResumeId(nextProfile?.pinnedResumeId || '')
      setPhone(nextProfile?.contactPhone || '')
      setEmail(nextProfile?.contactEmail || '')
      setContactUrl(nextProfile?.contactUrl || '')
    },
    [],
  )

  useEffect(() => {
    if (!accessToken) {
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    setError('')
    void (async () => {
      try {
        const [mine, sources] = await Promise.all([portfolioGetMine(), portfolioSources()])
        if (cancelled) return
        applyMine(mine.portfolio, mine.cases, session?.username || '')
        setGithubProjects(sources.githubProjects)
        setResumes(sources.resumes)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Не удалось загрузить портфолио')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [accessToken, applyMine, session?.username])

  useEffect(() => {
    return () => {
      for (const url of Object.values(coverUrls)) URL.revokeObjectURL(url)
    }
  }, [coverUrls])

  useEffect(() => {
    if (!accessToken) return
    let cancelled = false
    void (async () => {
      const next: Record<string, string> = {}
      for (const item of cases) {
        if (!item.hasCover || cancelled) continue
        try {
          const url = await portfolioFetchCover(item.id)
          if (!url) continue
          if (cancelled) {
            URL.revokeObjectURL(url)
            continue
          }
          next[item.id] = url
        } catch {
          /* плитка останется с заглушкой */
        }
      }
      if (cancelled) {
        for (const url of Object.values(next)) URL.revokeObjectURL(url)
        return
      }
      setCoverUrls(next)
    })()
    return () => {
      cancelled = true
    }
  }, [accessToken, cases])

  async function reloadCases() {
    const mine = await portfolioGetMine()
    setProfile(mine.portfolio)
    setCases(mine.cases)
    setIsPublished(Boolean(mine.portfolio?.isPublished))
  }

  async function onSaveProfile(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setOk('')
    try {
      const saved = await portfolioSaveMine({
        handle,
        headline,
        summary,
        is_published: isPublished,
        pinned_resume_id: pinnedResumeId || null,
        contact_phone: phone,
        contact_email: email,
        contact_url: contactUrl,
      })
      setProfile(saved.portfolio)
      setPhone(saved.portfolio?.contactPhone || '')
      setEmail(saved.portfolio?.contactEmail || '')
      setContactUrl(saved.portfolio?.contactUrl || '')
      setOk(saved.portfolio?.isPublished ? 'Страница опубликована' : 'Черновик сохранён')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить')
    } finally {
      setBusy(false)
    }
  }

  function startDraft(partial: Partial<MaterialDraft> = {}) {
    if (!profile) {
      setError('Сначала сохраните адрес страницы')
      return
    }
    if (cases.length >= MAX_CASES) {
      setError(`Не больше ${MAX_CASES} материалов`)
      return
    }
    setError('')
    setOk('')
    setDraft({
      id: null,
      title: partial.title || '',
      blurb: partial.blurb || '',
      link: partial.link || '',
      repoUrl: partial.repoUrl || '',
      hasCover: false,
      source: null,
    })
  }

  function editDraft(item: PortfolioCase) {
    setError('')
    setOk('')
    setDraft({
      id: item.id,
      title: item.title,
      blurb: item.blurb || item.problem,
      link: item.demoUrl || item.repoUrl,
      repoUrl: item.repoUrl,
      hasCover: item.hasCover,
      source: item,
    })
  }

  async function onSaveMaterial(input: {
    title: string
    blurb: string
    link: string
    file: File | null
    removeCover: boolean
  }) {
    if (!draft) return
    setBusy(true)
    setError('')
    setOk('')
    const body = caseInput({ ...draft, title: input.title }, input.blurb, input.link)
    body.title = input.title
    try {
      const saved = draft.id
        ? await portfolioUpdateCase(draft.id, body)
        : await portfolioCreateCase(body)
      if (input.file) {
        try {
          await portfolioUploadCover(saved.id, input.file)
        } catch (err) {
          setDraft(null)
          await reloadCases()
          setError(
            err instanceof Error
              ? `Материал сохранён, картинку загрузить не удалось: ${err.message}`
              : 'Материал сохранён, картинку загрузить не удалось',
          )
          return
        }
      } else if (input.removeCover && draft.hasCover) {
        await portfolioDeleteCover(saved.id)
      }
      setDraft(null)
      await reloadCases()
      setOk(draft.id ? 'Материал сохранён' : 'Материал добавлен')
      document.getElementById('portfolio-board')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить материал')
    } finally {
      setBusy(false)
    }
  }

  async function onDeleteCase(item: PortfolioCase) {
    if (!window.confirm(`Удалить материал «${item.title}»?`)) {
      return
    }
    setBusy(true)
    setError('')
    setOk('')
    try {
      await portfolioDeleteCase(item.id)
      if (draft?.id === item.id) setDraft(null)
      await reloadCases()
      setOk('Материал удалён')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить материал')
    } finally {
      setBusy(false)
    }
  }

  async function onMove(index: number, direction: -1 | 1) {
    const next = index + direction
    if (next < 0 || next >= cases.length) return
    const ids = cases.map((item) => item.id)
    const swap = ids[index]
    ids[index] = ids[next]
    ids[next] = swap
    setBusy(true)
    setError('')
    try {
      await portfolioReorder(ids)
      await reloadCases()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось изменить порядок')
    } finally {
      setBusy(false)
    }
  }

  if (!session) {
    return (
      <PageShell>
        <Link to="/" className="back-link">
          ← На главную
        </Link>
        <header className="learn-header">
          <p className="learn-eyebrow">Сервис · Портфолио</p>
          <h1 className="learn-title">Портфолио</h1>
          <p className="learn-lead">
            Загрузите материалы с картинкой и описанием — после сохранения откроется страница
            с плитками, ссылкой и контактами.
          </p>
          <p className="learn-section-note">
            <Link to="/login">Войти</Link>
            {' · '}
            <Link to="/register">Регистрация</Link>
          </p>
        </header>
      </PageShell>
    )
  }

  const publicUrl = profile?.handle ? `${window.location.origin}/p/${profile.handle}` : ''
  const contacts: PortfolioContacts = { phone, email, url: contactUrl }
  const tiles: PortfolioTileModel[] = cases.map((item, index) => ({
    id: item.id,
    title: item.title,
    blurb: item.blurb || item.problem,
    link: item.demoUrl || item.repoUrl,
    imageUrl: coverUrls[item.id] || '',
    tags: item.stack,
    actions: (
      <div className="portfolio-actions">
        <button type="button" className="learn-admin-btn" disabled={busy} onClick={() => editDraft(item)}>
          Изменить
        </button>
        <button
          type="button"
          className="learn-admin-btn"
          disabled={busy || index === 0}
          onClick={() => void onMove(index, -1)}
        >
          Выше
        </button>
        <button
          type="button"
          className="learn-admin-btn"
          disabled={busy || index === cases.length - 1}
          onClick={() => void onMove(index, 1)}
        >
          Ниже
        </button>
        <button
          type="button"
          className="learn-admin-btn"
          disabled={busy}
          onClick={() => void onDeleteCase(item)}
        >
          Удалить
        </button>
      </div>
    ),
  }))

  return (
    <PageShell>
      <Link to="/" className="back-link">
        ← На главную
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Сервис · Портфолио</p>
        <h1 className="learn-title">Материалы портфолио</h1>
        <p className="learn-lead">
          У каждого материала — картинка, краткое описание и ссылка. После сохранения они
          собираются в плитки, на каждой видны ваши контакты.
        </p>
        {error ? <p className="learn-admin-error">{error}</p> : null}
        {ok ? <p className="learn-admin-ok">{ok}</p> : null}
      </header>

      {loading ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : (
        <>
          <form className="hh-resume-form" onSubmit={(event) => void onSaveProfile(event)}>
            <label className="learn-admin-field">
              <span>Адрес страницы</span>
              <input
                value={handle}
                onChange={(event) => setHandle(event.target.value)}
                placeholder="ivan-dev"
                autoComplete="off"
                required
              />
            </label>
            <p className="learn-section-note">
              Публичная ссылка: {publicUrl || 'появится после сохранения адреса'}
              {profile?.isPublished && publicUrl ? (
                <>
                  {' · '}
                  <Link to={`/p/${profile.handle}`}>Открыть</Link>
                </>
              ) : null}
            </p>
            <label className="learn-admin-field">
              <span>Заголовок</span>
              <input
                value={headline}
                onChange={(event) => setHeadline(event.target.value)}
                placeholder="Дизайн и вёрстка интерфейсов"
                maxLength={160}
              />
            </label>
            <label className="learn-admin-field">
              <span>Коротко о себе</span>
              <textarea
                className="learn-admin-textarea"
                value={summary}
                onChange={(event) => setSummary(event.target.value)}
                rows={4}
                maxLength={2000}
              />
            </label>
            <label className="learn-admin-field">
              <span>Телефон</span>
              <input
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                placeholder="+7 900 000-00-00"
                autoComplete="tel"
                maxLength={64}
              />
            </label>
            <label className="learn-admin-field">
              <span>Email</span>
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                maxLength={255}
              />
            </label>
            <label className="learn-admin-field">
              <span>Ссылка для связи</span>
              <input
                value={contactUrl}
                onChange={(event) => setContactUrl(event.target.value)}
                placeholder="https://t.me/username"
                maxLength={500}
              />
            </label>
            <p className="learn-section-note">
              Телефон, почта и ссылка для связи показываются на каждой плитке опубликованной
              страницы.
            </p>
            <label className="learn-admin-field">
              <span>Закрепить резюме</span>
              <select
                value={pinnedResumeId}
                onChange={(event) => setPinnedResumeId(event.target.value)}
              >
                <option value="">Не закреплять</option>
                {resumes.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.versionName || 'Резюме'}
                    {item.specialization ? ` · ${item.specialization}` : ''}
                    {item.title ? ` · ${item.title}` : ''}
                  </option>
                ))}
              </select>
            </label>
            <label className="hh-resume-check">
              <input
                type="checkbox"
                checked={isPublished}
                onChange={(event) => setIsPublished(event.target.checked)}
              />
              Опубликовать страницу
            </label>
            <div className="account-actions">
              <button
                type="submit"
                className="learn-admin-btn learn-admin-btn-primary"
                disabled={busy}
              >
                Сохранить страницу
              </button>
              <Link to="/account" className="learn-admin-btn">
                Анкета
              </Link>
            </div>
          </form>

          <section className="info-section">
            <h2 className="section-block-title">Новый материал</h2>
            <p className="learn-section-note">
              Картинка JPEG, PNG, WebP или GIF до 1.5 МБ, краткое описание и ссылка на работу.
              До {MAX_CASES} материалов.
            </p>
            {githubProjects.length > 0 ? (
              <ul className="portfolio-source-list">
                {githubProjects.map((project) => (
                  <li key={project.url}>
                    <button
                      type="button"
                      className="learn-admin-btn"
                      disabled={busy || cases.length >= MAX_CASES || !profile || draft !== null}
                      onClick={() =>
                        startDraft({
                          title: project.name,
                          link: project.url,
                          repoUrl: project.url,
                        })
                      }
                    >
                      Добавить {project.name}
                    </button>
                    {project.language ? <span className="portfolio-chip">{project.language}</span> : null}
                  </li>
                ))}
              </ul>
            ) : null}
            {!profile ? <p className="learn-section-note">Сначала сохраните адрес страницы.</p> : null}
            {draft ? (
              <MaterialForm
                key={draft.id || 'new'}
                draft={draft}
                existingCover={draft.id ? coverUrls[draft.id] || '' : ''}
                busy={busy}
                onCancel={() => setDraft(null)}
                onSubmit={(input) => void onSaveMaterial(input)}
              />
            ) : (
              <div className="account-actions">
                <button
                  type="button"
                  className="learn-admin-btn learn-admin-btn-primary"
                  disabled={busy || cases.length >= MAX_CASES || !profile}
                  onClick={() => startDraft()}
                >
                  Добавить материал ({cases.length}/{MAX_CASES})
                </button>
              </div>
            )}
          </section>

          <section id="portfolio-board" className="info-section">
            <h2 className="section-block-title">Страница с плитками</h2>
            {cases.length === 0 ? (
              <p className="learn-section-note">
                Сохраните материал — здесь появятся плитки: картинка, краткое описание, ссылка и
                контактная информация.
              </p>
            ) : (
              <>
                <p className="learn-section-note">
                  Так страница выглядит после сохранения.
                  {profile?.isPublished && profile.handle ? (
                    <>
                      {' '}
                      <Link to={`/p/${profile.handle}`}>Открыть публичную</Link>
                    </>
                  ) : (
                    ' Опубликуйте её, чтобы ссылку можно было отправить.'
                  )}
                </p>
                <PortfolioTileGrid tiles={tiles} contacts={contacts} />
              </>
            )}
          </section>
        </>
      )}
    </PageShell>
  )
}

function MaterialForm({
  draft,
  existingCover,
  busy,
  onCancel,
  onSubmit,
}: {
  draft: MaterialDraft
  existingCover: string
  busy: boolean
  onCancel: () => void
  onSubmit: (input: {
    title: string
    blurb: string
    link: string
    file: File | null
    removeCover: boolean
  }) => void
}) {
  const [title, setTitle] = useState(draft.title)
  const [blurb, setBlurb] = useState(draft.blurb)
  const [link, setLink] = useState(draft.link)
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState('')
  const [removeCover, setRemoveCover] = useState(false)
  const [localError, setLocalError] = useState('')

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview)
    }
  }, [preview])

  function onPickFile(next: File | null) {
    if (preview) URL.revokeObjectURL(preview)
    setPreview('')
    setFile(null)
    setRemoveCover(false)
    if (!next) return
    const allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    const byName = /\.(jpe?g|png|webp|gif)$/i.test(next.name)
    if (next.type && !allowed.includes(next.type) && !byName) {
      setLocalError('Нужна картинка JPEG, PNG, WebP или GIF')
      return
    }
    if (next.size > MAX_COVER_BYTES) {
      setLocalError('Картинка больше 1.5 МБ')
      return
    }
    setLocalError('')
    setFile(next)
    setPreview(URL.createObjectURL(next))
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!title.trim() || !blurb.trim()) {
      setLocalError('Нужны название и краткое описание')
      return
    }
    setLocalError('')
    onSubmit({ title: title.trim(), blurb: blurb.trim(), link: link.trim(), file, removeCover })
  }

  const shownCover = preview || (!removeCover ? existingCover : '')

  return (
    <form id="portfolio-material-form" className="portfolio-material" onSubmit={submit}>
      {localError ? <p className="learn-admin-error">{localError}</p> : null}
      <label className="learn-admin-field">
        <span>Картинка</span>
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          onChange={(event) => {
            onPickFile(event.target.files?.[0] || null)
            event.target.value = ''
          }}
        />
      </label>
      {shownCover ? <img src={shownCover} alt="" className="portfolio-form-preview" /> : null}
      {draft.hasCover && !file ? (
        <label className="hh-resume-check">
          <input
            type="checkbox"
            checked={removeCover}
            onChange={(event) => setRemoveCover(event.target.checked)}
          />
          Убрать картинку
        </label>
      ) : null}
      <label className="learn-admin-field">
        <span>Название</span>
        <input value={title} onChange={(event) => setTitle(event.target.value)} required maxLength={160} />
      </label>
      <label className="learn-admin-field">
        <span>Краткое описание</span>
        <textarea
          className="learn-admin-textarea"
          value={blurb}
          onChange={(event) => setBlurb(event.target.value)}
          rows={3}
          maxLength={400}
          required
        />
      </label>
      <label className="learn-admin-field">
        <span>Ссылка</span>
        <input
          value={link}
          onChange={(event) => setLink(event.target.value)}
          placeholder="https://"
          maxLength={500}
        />
      </label>
      <div className="portfolio-actions">
        <button type="submit" className="learn-admin-btn learn-admin-btn-primary" disabled={busy}>
          Сохранить материал
        </button>
        <button type="button" className="learn-admin-btn" disabled={busy} onClick={onCancel}>
          Отмена
        </button>
      </div>
    </form>
  )
}
