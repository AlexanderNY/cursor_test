import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import {
  portfolioCreateCase,
  portfolioDeleteCase,
  portfolioGetMine,
  portfolioReorder,
  portfolioSaveMine,
  portfolioSources,
  portfolioUpdateCase,
  type PortfolioCase,
  type PortfolioCaseInput,
  type PortfolioCertTrack,
  type PortfolioLearnRef,
  type PortfolioProfile,
  type PortfolioResumeOption,
  type PortfolioGithubProject,
} from '@/data/site/portfolio-api'
import { useSiteAuthSession } from '@/data/site/site-auth'

const MAX_CASES = 6

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

function stackText(stack: string[]): string {
  return stack.join(', ')
}

function parseStack(raw: string): string[] {
  return raw
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
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
  const [githubProjects, setGithubProjects] = useState<PortfolioGithubProject[]>([])
  const [learn, setLearn] = useState<PortfolioLearnRef[]>([])
  const [resumes, setResumes] = useState<PortfolioResumeOption[]>([])
  const [certTracks, setCertTracks] = useState<PortfolioCertTrack[]>([])
  const [pending, setPending] = useState<PortfolioCase | null>(null)

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
        setLearn(sources.learn)
        setResumes(sources.resumes)
        setCertTracks(sources.certTracks)
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
      })
      setProfile(saved.portfolio)
      setOk(saved.portfolio?.isPublished ? 'Страница опубликована' : 'Черновик сохранён')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить')
    } finally {
      setBusy(false)
    }
  }

  function startPending(partial: Partial<PortfolioCase>) {
    if (!profile) {
      setError('Сначала сохраните адрес страницы')
      return
    }
    if (cases.length >= MAX_CASES) {
      setError(`Не больше ${MAX_CASES} кейсов`)
      return
    }
    setError('')
    setOk('')
    setPending({
      id: 'pending',
      sortOrder: cases.length,
      title: partial.title || `Кейс ${cases.length + 1}`,
      role: partial.role || '',
      problem: partial.problem || '',
      work: partial.work || '',
      outcome: partial.outcome || '',
      stack: partial.stack || [],
      repoUrl: partial.repoUrl || '',
      demoUrl: partial.demoUrl || '',
      learnSlugs: partial.learnSlugs || [],
      learn: [],
      certTrackId: partial.certTrackId || '',
      certTrackTitle: '',
      updatedAt: null,
    })
  }

  async function onCreatePending(input: PortfolioCaseInput) {
    setBusy(true)
    setError('')
    setOk('')
    try {
      await portfolioCreateCase(input)
      setPending(null)
      await reloadCases()
      setOk('Кейс добавлен')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось добавить кейс')
    } finally {
      setBusy(false)
    }
  }

  async function onSaveCase(item: PortfolioCase, input: PortfolioCaseInput) {
    setBusy(true)
    setError('')
    setOk('')
    try {
      await portfolioUpdateCase(item.id, input)
      await reloadCases()
      setOk(`Кейс «${input.title}» сохранён`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить кейс')
    } finally {
      setBusy(false)
    }
  }

  async function onDeleteCase(item: PortfolioCase) {
    if (!window.confirm(`Удалить кейс «${item.title}»?`)) {
      return
    }
    setBusy(true)
    setError('')
    setOk('')
    try {
      await portfolioDeleteCase(item.id)
      await reloadCases()
      setOk('Кейс удалён')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить кейс')
    } finally {
      setBusy(false)
    }
  }

  async function onMove(index: number, direction: -1 | 1) {
    const next = index + direction
    if (next < 0 || next >= cases.length) {
      return
    }
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
          <h1 className="learn-title">Портфолио кейсов</h1>
          <p className="learn-lead">
            Публичная страница: задача, что сделано, результат, стек и доказательства из Learn.
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
  const earnedTracks = certTracks.filter((track) => track.earned)

  return (
    <PageShell>
      <Link to="/" className="back-link">
        ← На главную
      </Link>
      <header className="learn-header">
        <p className="learn-eyebrow">Сервис · Портфолио</p>
        <h1 className="learn-title">Страница кейсов</h1>
        <p className="learn-lead">
          До 6 кейсов. На опубликованной странице видны имя из анкеты, город, закреплённое резюме
          без контактов и только заполненные истории. Телефон и почта остаются в кабинете.
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
                placeholder="Backend на Python, учусь на 9to18"
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
              <Link to="/game/hh-resume" className="learn-admin-btn">
                Резюме
              </Link>
            </div>
          </form>

          <section className="info-section">
            <h2 className="section-block-title">Откуда взять кейс</h2>
            <p className="learn-section-note">
              Репозитории подтягиваются из резюме. Черновик можно сохранить без текста, публикация
              потребует задачу, что сделано и результат.
            </p>
            {githubProjects.length === 0 ? (
              <p className="learn-section-note">
                В резюме пока нет репозиториев GitHub. Кейс можно создать вручную.
              </p>
            ) : (
              <ul className="portfolio-source-list">
                {githubProjects.map((project) => (
                  <li key={project.url}>
                    <button
                      type="button"
                      className="learn-admin-btn"
                      disabled={busy || cases.length >= MAX_CASES || !profile || pending !== null}
                      onClick={() =>
                        startPending({
                          title: project.name,
                          stack: project.language ? [project.language] : [],
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
            )}
            {!profile ? (
              <p className="learn-section-note">Сначала сохраните адрес страницы.</p>
            ) : null}
          </section>

          <div className="account-actions">
            <button
              type="button"
              className="learn-admin-btn learn-admin-btn-primary"
              disabled={busy || cases.length >= MAX_CASES || !profile || pending !== null}
              onClick={() => startPending({})}
            >
              Добавить кейс ({cases.length}/{MAX_CASES})
            </button>
          </div>

          <div className="portfolio-grid">
            {pending ? (
              <CaseEditor
                key="pending"
                item={pending}
                index={cases.length}
                total={cases.length + 1}
                busy={busy}
                learn={learn}
                earnedTracks={earnedTracks}
                onSave={(input) => onCreatePending(input)}
                onDelete={() => setPending(null)}
                onMove={() => undefined}
                reorder={false}
                deleteLabel="Отмена"
              />
            ) : null}
            {cases.map((item, index) => (
              <CaseEditor
                key={item.id}
                item={item}
                index={index}
                total={cases.length}
                busy={busy}
                learn={learn}
                earnedTracks={earnedTracks}
                onSave={(input) => onSaveCase(item, input)}
                onDelete={() => onDeleteCase(item)}
                onMove={(direction) => onMove(index, direction)}
              />
            ))}
          </div>
        </>
      )}
    </PageShell>
  )
}

function CaseEditor({
  item,
  index,
  total,
  busy,
  learn,
  earnedTracks,
  onSave,
  onDelete,
  onMove,
  reorder = true,
  deleteLabel = 'Удалить',
}: {
  item: PortfolioCase
  index: number
  total: number
  busy: boolean
  learn: PortfolioLearnRef[]
  earnedTracks: PortfolioCertTrack[]
  onSave: (input: PortfolioCaseInput) => void
  onDelete: () => void
  onMove: (direction: -1 | 1) => void
  reorder?: boolean
  deleteLabel?: string
}) {
  const [title, setTitle] = useState(item.title)
  const [role, setRole] = useState(item.role)
  const [problem, setProblem] = useState(item.problem)
  const [work, setWork] = useState(item.work)
  const [outcome, setOutcome] = useState(item.outcome)
  const [stack, setStack] = useState(stackText(item.stack))
  const [repoUrl, setRepoUrl] = useState(item.repoUrl)
  const [demoUrl, setDemoUrl] = useState(item.demoUrl)
  const [learnSlugs, setLearnSlugs] = useState<string[]>(item.learnSlugs)
  const [certTrackId, setCertTrackId] = useState(item.certTrackId)

  useEffect(() => {
    setTitle(item.title)
    setRole(item.role)
    setProblem(item.problem)
    setWork(item.work)
    setOutcome(item.outcome)
    setStack(stackText(item.stack))
    setRepoUrl(item.repoUrl)
    setDemoUrl(item.demoUrl)
    setLearnSlugs(item.learnSlugs)
    setCertTrackId(item.certTrackId)
  }, [item])

  function toggleSlug(slug: string) {
    setLearnSlugs((prev) => {
      if (prev.some((itemSlug) => itemSlug.toLowerCase() === slug.toLowerCase())) {
        return prev.filter((itemSlug) => itemSlug.toLowerCase() !== slug.toLowerCase())
      }
      if (prev.length >= 8) {
        return prev
      }
      return [...prev, slug]
    })
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    void onSave({
      title,
      role,
      problem,
      work,
      outcome,
      stack: parseStack(stack),
      repo_url: repoUrl,
      demo_url: demoUrl,
      learn_slugs: learnSlugs,
      cert_track_id: certTrackId,
    })
  }

  return (
    <form className="portfolio-case" onSubmit={submit}>
      <div className="portfolio-case-toolbar">
        <h2 className="learn-section-title">
          {index + 1}. {title || 'Кейс'}
        </h2>
        {reorder ? (
          <div className="portfolio-actions">
            <button
              type="button"
              className="learn-admin-btn"
              disabled={busy || index === 0}
              onClick={() => onMove(-1)}
            >
              Выше
            </button>
            <button
              type="button"
              className="learn-admin-btn"
              disabled={busy || index === total - 1}
              onClick={() => onMove(1)}
            >
              Ниже
            </button>
          </div>
        ) : null}
      </div>
      <label className="learn-admin-field">
        <span>Название</span>
        <input value={title} onChange={(event) => setTitle(event.target.value)} required maxLength={160} />
      </label>
      <label className="learn-admin-field">
        <span>Роль</span>
        <input
          value={role}
          onChange={(event) => setRole(event.target.value)}
          placeholder="Разработчик, QA, аналитик…"
          maxLength={120}
        />
      </label>
      <label className="learn-admin-field">
        <span>Задача</span>
        <textarea className="learn-admin-textarea" value={problem} onChange={(event) => setProblem(event.target.value)} rows={3} />
      </label>
      <label className="learn-admin-field">
        <span>Что сделано</span>
        <textarea className="learn-admin-textarea" value={work} onChange={(event) => setWork(event.target.value)} rows={3} />
      </label>
      <label className="learn-admin-field">
        <span>Результат</span>
        <textarea className="learn-admin-textarea" value={outcome} onChange={(event) => setOutcome(event.target.value)} rows={3} />
      </label>
      <label className="learn-admin-field">
        <span>Стек через запятую</span>
        <input value={stack} onChange={(event) => setStack(event.target.value)} />
      </label>
      <label className="learn-admin-field">
        <span>Репозиторий</span>
        <input
          value={repoUrl}
          onChange={(event) => setRepoUrl(event.target.value)}
          placeholder="https://"
        />
      </label>
      <label className="learn-admin-field">
        <span>Демо</span>
        <input
          value={demoUrl}
          onChange={(event) => setDemoUrl(event.target.value)}
          placeholder="https://"
        />
      </label>
      <label className="learn-admin-field">
        <span>Сертификат сезона</span>
        <select value={certTrackId} onChange={(event) => setCertTrackId(event.target.value)}>
          <option value="">Не прикреплять</option>
          {earnedTracks.map((track) => (
            <option key={track.id} value={track.id}>
              {track.title}
            </option>
          ))}
          {certTrackId && !earnedTracks.some((track) => track.id === certTrackId) ? (
            <option value={certTrackId}>{item.certTrackTitle || certTrackId}</option>
          ) : null}
        </select>
      </label>
      {learn.length > 0 ? (
        <fieldset className="hh-resume-fieldset">
          <legend>Пройденные выпуски Learn (до 8)</legend>
          <div className="portfolio-learn-box">
            {learn.map((episode) => (
              <label key={episode.slug} className="hh-resume-check">
                <input
                  type="checkbox"
                  checked={learnSlugs.some(
                    (itemSlug) => itemSlug.toLowerCase() === episode.slug.toLowerCase(),
                  )}
                  onChange={() => toggleSlug(episode.slug)}
                />
                {episode.episode ? `${episode.episode} · ` : ''}
                {episode.title}
              </label>
            ))}
          </div>
        </fieldset>
      ) : (
        <p className="learn-section-note">Отметьте выпуски в Tasks, чтобы привязать их к кейсу.</p>
      )}
      <div className="portfolio-actions">
        <button type="submit" className="learn-admin-btn learn-admin-btn-primary" disabled={busy}>
          Сохранить кейс
        </button>
        <button type="button" className="learn-admin-btn" disabled={busy} onClick={() => void onDelete()}>
          {deleteLabel}
        </button>
      </div>
    </form>
  )
}
