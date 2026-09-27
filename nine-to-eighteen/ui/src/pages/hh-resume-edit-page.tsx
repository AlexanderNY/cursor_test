import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { HhResumeArticle, HhResumeStrengthBar } from '@/components/hh-resume-article'
import { PageShell } from '@/components/page-shell'
import {
  resumeCoverLetter,
  resumeDownloadExport,
  resumeExport,
  resumeGenerate,
  resumeGetPreview,
  resumeGithubFetch,
  resumeImproveAbout,
  resumeListBadges,
  resumeMatchScore,
  resumeMockChatMessage,
  resumeMockChatStart,
  resumePut,
  resumeSkillGap,
  type GithubProject,
  type MatchScoreResult,
  type MockChatMessage,
  type ResumeBadge,
  type SiteResumePreview,
  type SiteResumeSkill,
  type SkillGapResult,
} from '@/data/site/resume-api'
import { computeStrengthLive } from '@/data/site/resume-strength'
import {
  EMPLOYMENT_OPTIONS,
  WORK_FORMAT_OPTIONS,
  toggleInList,
} from '@/data/site/resume-options'
import { siteFetchPhotoBlob } from '@/data/site/site-api'
import { useSiteAuthSession } from '@/data/site/site-auth'

/** Редактор + live-превью (split) + сила резюме + mock-interview. */
export function HhResumeEditPage() {
  const { resumeId = '' } = useParams()
  const session = useSiteAuthSession()
  const location = useLocation()
  const fromQuiz = Boolean((location.state as { fromQuiz?: boolean } | null)?.fromQuiz)

  const [preview, setPreview] = useState<SiteResumePreview | null>(null)
  const [photoUrl, setPhotoUrl] = useState<string | null>(null)
  const [skills, setSkills] = useState<SiteResumeSkill[]>([])
  const [selectedKeys, setSelectedKeys] = useState<string[]>([])
  const [suggestedSpecialization, setSuggestedSpecialization] = useState<string | null>(null)
  const [branchHints, setBranchHints] = useState<string[]>([])
  const [completedCount, setCompletedCount] = useState(0)
  const [doneRelevant, setDoneRelevant] = useState<string[]>([])
  const [missingRelevant, setMissingRelevant] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [enriching, setEnriching] = useState(false)
  const [aiBusy, setAiBusy] = useState(false)
  const [strengthOpen, setStrengthOpen] = useState(false)
  const [error, setError] = useState('')
  const [ok, setOk] = useState(
    fromQuiz ? 'Шаблон заполнен по опросу — поправьте текст при необходимости.' : '',
  )

  const [versionName, setVersionName] = useState('')
  const [title, setTitle] = useState('')
  const [specialization, setSpecialization] = useState('')
  const [salary, setSalary] = useState('')
  const [employment, setEmployment] = useState<string[]>([])
  const [workFormats, setWorkFormats] = useState<string[]>([])
  const [about, setAbout] = useState('')
  const [gapResult, setGapResult] = useState<SkillGapResult | null>(null)
  const [gapRole, setGapRole] = useState('')
  const [vacancyText, setVacancyText] = useState('')
  const [coverLetter, setCoverLetter] = useState('')
  const [matchResult, setMatchResult] = useState<MatchScoreResult | null>(null)

  const [badges, setBadges] = useState<ResumeBadge[]>([])
  const [selectedBadgeIds, setSelectedBadgeIds] = useState<string[]>([])
  const [githubUsername, setGithubUsername] = useState('')
  const [githubProjects, setGithubProjects] = useState<GithubProject[]>([])

  const [chatSessionId, setChatSessionId] = useState('')
  const [chatMessages, setChatMessages] = useState<MockChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatDone, setChatDone] = useState(false)
  const [chatSummary, setChatSummary] = useState('')
  const [chatTurn, setChatTurn] = useState(0)
  const [chatMaxTurns, setChatMaxTurns] = useState(5)

  const load = useCallback(async () => {
    if (!resumeId) return
    setLoading(true)
    setError('')
    try {
      const data = await resumeGetPreview(resumeId)
      setPreview(data)
      setSkills(data.skills)
      setSelectedKeys(
        data.resume.selectedSkillKeys.length > 0
          ? data.resume.selectedSkillKeys
          : data.skills.map((s) => s.key),
      )
      setVersionName(data.resume.versionName)
      setTitle(data.resume.title)
      setSpecialization(data.resume.specialization)
      setSalary(data.resume.salaryAmount != null ? String(data.resume.salaryAmount) : '')
      setEmployment(data.resume.employmentTypes)
      setWorkFormats(data.resume.workFormats)
      setAbout(data.resume.about)
      setSelectedBadgeIds(data.resume.selectedBadgeIds || [])
      setGithubUsername(data.resume.githubUsername || '')
      setGithubProjects(data.resume.githubProjects || [])
      setSuggestedSpecialization(data.suggestedSpecialization)
      setBranchHints(data.branchHints)
      setCompletedCount(data.completedCount)
      setGapRole(data.resume.specialization || data.suggestedSpecialization || '')
      setDoneRelevant(data.strength?.doneRelevantSlugs || [])
      setMissingRelevant(data.strength?.missingRelevantSlugs || [])
      try {
        const badgeData = await resumeListBadges()
        setBadges(badgeData.badges)
      } catch {
        setBadges([])
      }
      if (data.profile.hasPhoto) {
        const blobUrl = await siteFetchPhotoBlob()
        setPhotoUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev)
          return blobUrl
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить резюме')
    } finally {
      setLoading(false)
    }
  }, [resumeId])

  useEffect(() => {
    if (!session || !resumeId) {
      setLoading(false)
      return
    }
    void load()
    return () => {
      setPhotoUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev)
        return null
      })
    }
  }, [session?.accessToken, resumeId, load])

  const liveSkills = useMemo(
    () => skills.filter((s) => selectedKeys.includes(s.key)),
    [skills, selectedKeys],
  )

  const strength = useMemo(
    () =>
      computeStrengthLive({
        hasPhoto: Boolean(preview?.profile.hasPhoto),
        about,
        doneRelevantSlugs: doneRelevant,
        missingRelevantSlugs: missingRelevant,
      }),
    [preview?.profile.hasPhoto, about, doneRelevant, missingRelevant],
  )

  const salaryNumLive = salary.trim() ? Number(salary.replace(/\s/g, '')) : null

  const badgeLabels = useMemo(() => {
    const byId = new Map(badges.map((b) => [b.id, b.title]))
    return selectedBadgeIds.map((id) => byId.get(id) || id)
  }, [badges, selectedBadgeIds])

  const selectedProjects = useMemo(
    () => githubProjects.filter((p) => p.selected).slice(0, 6),
    [githubProjects],
  )

  async function onSave(event: FormEvent) {
    event.preventDefault()
    if (!resumeId) return
    setSaving(true)
    setError('')
    setOk('')
    try {
      const salaryNum = salary.trim() ? Number(salary.replace(/\s/g, '')) : null
      if (salary.trim() && (salaryNum == null || Number.isNaN(salaryNum))) {
        throw new Error('Оклад должен быть числом')
      }
      await resumePut(resumeId, {
        version_name: versionName.trim() || 'Основное',
        title: title.trim(),
        specialization: specialization.trim(),
        salary_amount: salaryNum,
        salary_currency: 'RUB',
        employment_types: employment,
        work_formats: workFormats,
        about: about.trim(),
        selected_skill_keys: selectedKeys,
        selected_badge_ids: selectedBadgeIds,
        github_username: githubUsername.trim(),
        github_projects: githubProjects,
      })
      setOk('Изменения сохранены')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  async function onEnrichFromLearn() {
    if (!resumeId) return
    setEnriching(true)
    setError('')
    setOk('')
    try {
      const salaryNum = salary.trim() ? Number(salary.replace(/\s/g, '')) : null
      await resumePut(resumeId, {
        version_name: versionName.trim() || 'Основное',
        title: title.trim(),
        specialization: specialization.trim() || undefined,
        salary_amount: salary.trim() && !Number.isNaN(salaryNum as number) ? salaryNum : null,
        employment_types: employment,
        work_formats: workFormats,
        about: about.trim(),
        selected_skill_keys: selectedKeys,
      })
      const result = await resumeGenerate(resumeId, { persist: true })
      setSkills(result.skills)
      setSelectedKeys(result.skills.map((s) => s.key))
      setBranchHints(result.branchHints)
      setCompletedCount(result.completedCount)
      if (result.suggestedSpecialization) {
        setSuggestedSpecialization(result.suggestedSpecialization)
      }
      setOk(
        result.skills.length > 0
          ? `Добавлено навыков из Learn: ${result.skills.length}.`
          : `Пока нет навыков (прогресс: ${result.completedCount}).`,
      )
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось обогатить навыками')
    } finally {
      setEnriching(false)
    }
  }

  async function onExport(format: 'pdf' | 'docx') {
    if (!resumeId) return
    setSaving(true)
    setError('')
    setOk('')
    try {
      const result = await resumeExport(resumeId, format)
      const { objectUrl } = await resumeDownloadExport(result.downloadUrl)
      const a = document.createElement('a')
      a.href = objectUrl
      a.download = result.fileName
      a.click()
      URL.revokeObjectURL(objectUrl)
      setOk(format === 'pdf' ? 'PDF скачан' : 'DOCX скачан')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка экспорта')
    } finally {
      setSaving(false)
    }
  }

  async function onImproveAbout() {
    if (!resumeId || !about.trim()) {
      setError('Сначала заполните «О себе»')
      return
    }
    setAiBusy(true)
    setError('')
    setOk('')
    try {
      await resumePut(resumeId, {
        version_name: versionName.trim() || 'Основное',
        title: title.trim(),
        specialization: specialization.trim() || undefined,
        about: about.trim(),
        selected_skill_keys: selectedKeys,
      })
      const result = await resumeImproveAbout(resumeId, {
        text: about.trim(),
        persist: true,
      })
      setAbout(result.about)
      setOk('«О себе» улучшено и сохранено')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось улучшить текст')
    } finally {
      setAiBusy(false)
    }
  }

  async function onSkillGap() {
    if (!resumeId) return
    setAiBusy(true)
    setError('')
    setOk('')
    try {
      const result = await resumeSkillGap(resumeId, {
        target_role: gapRole.trim() || specialization.trim() || undefined,
      })
      setGapResult(result)
      setOk(
        result.gaps.length > 0
          ? `Рекомендаций: ${result.gaps.length}`
          : 'Явных пробелов нет',
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка skill-gap')
    } finally {
      setAiBusy(false)
    }
  }

  async function onCoverLetter() {
    if (!resumeId || vacancyText.trim().length < 20) {
      setError('Вставьте описание вакансии (≥20 символов)')
      return
    }
    setAiBusy(true)
    setError('')
    setOk('')
    try {
      const result = await resumeCoverLetter(resumeId, vacancyText.trim())
      setCoverLetter(result.letter)
      setOk('Сопроводительное письмо готово')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка генерации письма')
    } finally {
      setAiBusy(false)
    }
  }

  async function onMatchScore() {
    if (!resumeId || vacancyText.trim().length < 20) {
      setError('Вставьте описание вакансии (≥20 символов)')
      return
    }
    setAiBusy(true)
    setError('')
    setOk('')
    try {
      const result = await resumeMatchScore(resumeId, vacancyText.trim())
      setMatchResult(result)
      setOk(`Match Score: ${result.score}%`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка Match Score')
    } finally {
      setAiBusy(false)
    }
  }

  async function onGithubFetch() {
    if (!resumeId || !githubUsername.trim()) {
      setError('Укажите GitHub username')
      return
    }
    setAiBusy(true)
    setError('')
    setOk('')
    try {
      const result = await resumeGithubFetch(resumeId, githubUsername.trim())
      setGithubUsername(result.username)
      setGithubProjects(result.projects)
      setOk(`Загружено репозиториев: ${result.projects.length}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить GitHub')
    } finally {
      setAiBusy(false)
    }
  }

  async function onStartChat() {
    if (!resumeId) return
    setAiBusy(true)
    setError('')
    setOk('')
    setChatInput('')
    setChatSummary('')
    setChatDone(false)
    try {
      const result = await resumeMockChatStart(resumeId, 5)
      setChatSessionId(result.sessionId)
      setChatMessages(result.messages)
      setChatTurn(result.turn)
      setChatMaxTurns(result.maxTurns)
      setOk('Чат-собеседование начато')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось начать чат')
    } finally {
      setAiBusy(false)
    }
  }

  async function onSendChat() {
    if (!resumeId || !chatSessionId || !chatInput.trim()) {
      setError('Введите ответ')
      return
    }
    setAiBusy(true)
    setError('')
    try {
      const result = await resumeMockChatMessage(
        resumeId,
        chatSessionId,
        chatInput.trim(),
      )
      setChatMessages(result.messages)
      setChatTurn(result.turn)
      setChatMaxTurns(result.maxTurns)
      setChatDone(result.done)
      setChatInput('')
      if (result.done) {
        setChatSummary(
          result.summary ||
            (result.overallScore != null
              ? `Средняя оценка ${result.overallScore}/5`
              : 'Собеседование завершено'),
        )
        setOk('Собеседование завершено')
      } else if (result.lastScore != null) {
        setOk(`Оценка хода: ${result.lastScore}/5`)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка чата')
    } finally {
      setAiBusy(false)
    }
  }

  if (!session) {
    return (
      <PageShell>
        <Link to="/game/hh-resume" className="back-link">
          ← К списку
        </Link>
        <p className="learn-section-note">
          <Link to="/login">Войти</Link>
        </p>
      </PageShell>
    )
  }

  if (!resumeId) {
    return (
      <PageShell>
        <Link to="/game/hh-resume" className="back-link">
          ← К списку
        </Link>
        <p className="learn-admin-error">Не указан id резюме</p>
      </PageShell>
    )
  }

  return (
    <PageShell>
      <Link to="/game/hh-resume" className="back-link">
        ← К списку резюме
      </Link>

      <header className="learn-header">
        <p className="learn-eyebrow">HH-резюме · редактор</p>
        <h1 className="learn-title">Доработать резюме</h1>
        <p className="learn-lead">
          Learn: <strong>{completedCount}</strong> выпусков · правки слева, PDF-превью справа.
        </p>
        {error ? <p className="learn-admin-error">{error}</p> : null}
        {ok ? <p className="learn-admin-ok">{ok}</p> : null}
      </header>

      <HhResumeStrengthBar
        score={strength.score}
        maxScore={strength.maxScore}
        actions={strength.actions}
        expanded={strengthOpen}
        onToggle={() => setStrengthOpen((v) => !v)}
      />

      <div className="account-actions" style={{ marginBottom: '1rem' }}>
        <Link
          to={`/game/hh-resume/${resumeId}/quiz`}
          className="learn-admin-btn learn-admin-btn-primary"
        >
          Опросник
        </Link>
        <button
          type="button"
          className="learn-admin-btn learn-admin-btn-primary"
          disabled={enriching || loading}
          onClick={() => void onEnrichFromLearn()}
        >
          {enriching ? 'Обогащаем…' : 'Навыки из Learn'}
        </button>
        <button
          type="button"
          className="learn-admin-btn"
          disabled={saving || enriching}
          onClick={() => void onExport('pdf')}
        >
          PDF
        </button>
        <button
          type="button"
          className="learn-admin-btn"
          disabled={saving || enriching}
          onClick={() => void onExport('docx')}
        >
          DOCX
        </button>
        <Link to={`/game/hh-resume/${resumeId}`} className="learn-admin-btn">
          Полный экран
        </Link>
      </div>

      {loading || !preview ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : (
        <div className="hh-resume-split">
          <div className="hh-resume-split-editor">
            <form className="learn-admin-form hh-resume-form" onSubmit={onSave}>
              <div className="learn-admin-grid">
                <label className="learn-admin-field">
                  <span>Название версии</span>
                  <input
                    value={versionName}
                    onChange={(e) => setVersionName(e.target.value)}
                    maxLength={120}
                  />
                </label>
                <label className="learn-admin-field">
                  <span>Заголовок</span>
                  <input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={255} />
                </label>
                <label className="learn-admin-field">
                  <span>Желаемая должность</span>
                  <input
                    value={specialization}
                    onChange={(e) => setSpecialization(e.target.value)}
                    placeholder={suggestedSpecialization || ''}
                    maxLength={255}
                  />
                </label>
                <label className="learn-admin-field">
                  <span>Оклад, ₽</span>
                  <input
                    value={salary}
                    onChange={(e) => setSalary(e.target.value)}
                    inputMode="numeric"
                  />
                </label>
              </div>

              <fieldset className="hh-resume-fieldset">
                <legend>Тип занятости</legend>
                <div className="hh-resume-checks">
                  {EMPLOYMENT_OPTIONS.map((opt) => (
                    <label key={opt.id} className="hh-resume-check">
                      <input
                        type="checkbox"
                        checked={employment.includes(opt.id)}
                        onChange={() => setEmployment(toggleInList(employment, opt.id))}
                      />
                      {opt.label}
                    </label>
                  ))}
                </div>
              </fieldset>

              <fieldset className="hh-resume-fieldset">
                <legend>Формат работы</legend>
                <div className="hh-resume-checks">
                  {WORK_FORMAT_OPTIONS.map((opt) => (
                    <label key={opt.id} className="hh-resume-check">
                      <input
                        type="checkbox"
                        checked={workFormats.includes(opt.id)}
                        onChange={() => setWorkFormats(toggleInList(workFormats, opt.id))}
                      />
                      {opt.label}
                    </label>
                  ))}
                </div>
              </fieldset>

              <label className="learn-admin-field">
                <span>О себе</span>
                <textarea
                  value={about}
                  onChange={(e) => setAbout(e.target.value)}
                  rows={6}
                  maxLength={8000}
                  placeholder={branchHints.length > 0 ? branchHints.join('. ') : ''}
                />
              </label>
              <div className="account-actions">
                <button
                  type="button"
                  className="learn-admin-btn learn-admin-btn-primary"
                  disabled={aiBusy || !about.trim()}
                  onClick={() => void onImproveAbout()}
                >
                  Улучшить с помощью AI
                </button>
              </div>

              {skills.length > 0 ? (
                <section className="hh-resume-skills-pick" aria-label="Навыки">
                  <h2 className="account-subheading">Навыки из Learn</h2>
                  <ul className="hh-resume-skill-list">
                    {skills.map((skill) => (
                      <li key={skill.key}>
                        <label className="hh-resume-check">
                          <input
                            type="checkbox"
                            checked={selectedKeys.includes(skill.key)}
                            onChange={() =>
                              setSelectedKeys(toggleInList(selectedKeys, skill.key))
                            }
                          />
                          <span>{skill.display}</span>
                        </label>
                      </li>
                    ))}
                  </ul>
                </section>
              ) : (
                <p className="learn-section-note">Навыков пока нет — обогатите из Learn.</p>
              )}

              <section className="hh-resume-ai-block" aria-label="Разрыв навыков">
                <h2 className="account-subheading">Разрыв навыков</h2>
                <label className="learn-admin-field">
                  <span>Целевая должность</span>
                  <input
                    value={gapRole}
                    onChange={(e) => setGapRole(e.target.value)}
                    maxLength={255}
                  />
                </label>
                <button
                  type="button"
                  className="learn-admin-btn learn-admin-btn-primary"
                  disabled={aiBusy}
                  onClick={() => void onSkillGap()}
                >
                  Проанализировать
                </button>
                {gapResult ? (
                  <div className="hh-resume-gap-result">
                    <p className="learn-section-note">{gapResult.summary}</p>
                    <ul className="hh-resume-gap-list">
                      {gapResult.gaps.map((gap) => (
                        <li key={gap.skillKey}>
                          <strong>{gap.skillKey}</strong>
                          {gap.reason ? ` — ${gap.reason}` : ''}
                          <p className="hh-resume-gap-slugs">
                            {gap.learnSlugs.map((slug) => (
                              <Link key={slug} to={`/game/learn/${slug}`}>
                                {slug}
                              </Link>
                            ))}
                          </p>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </section>

              <section className="hh-resume-ai-block" aria-label="Вакансия">
                <h2 className="account-subheading">Вакансия · Match Score и письмо</h2>
                <textarea
                  value={vacancyText}
                  onChange={(e) => setVacancyText(e.target.value)}
                  rows={4}
                  maxLength={8000}
                  placeholder="Текст вакансии"
                />
                <div className="account-actions">
                  <button
                    type="button"
                    className="learn-admin-btn learn-admin-btn-primary"
                    disabled={aiBusy || vacancyText.trim().length < 20}
                    onClick={() => void onMatchScore()}
                  >
                    Match Score
                  </button>
                  <button
                    type="button"
                    className="learn-admin-btn"
                    disabled={aiBusy || vacancyText.trim().length < 20}
                    onClick={() => void onCoverLetter()}
                  >
                    Сопроводительное
                  </button>
                  {coverLetter ? (
                    <button
                      type="button"
                      className="learn-admin-btn"
                      onClick={() => void navigator.clipboard.writeText(coverLetter)}
                    >
                      Копировать письмо
                    </button>
                  ) : null}
                </div>
                {matchResult ? (
                  <div className="hh-match-score" aria-live="polite">
                    <div className="hh-match-score-ring">
                      <strong>{matchResult.score}%</strong>
                      <span>совпадение</span>
                    </div>
                    <p className="learn-section-note">{matchResult.summary}</p>
                    {matchResult.matchedKeys.length > 0 ? (
                      <p className="learn-section-note">
                        Есть: {matchResult.matchedKeys.join(', ')}
                      </p>
                    ) : null}
                    {matchResult.missingKeys.length > 0 ? (
                      <p className="learn-section-note">
                        Не хватает: {matchResult.missingKeys.join(', ')}
                      </p>
                    ) : null}
                  </div>
                ) : null}
                {coverLetter ? <pre className="hh-resume-cover-letter">{coverLetter}</pre> : null}
              </section>

              <section className="hh-resume-ai-block" aria-label="Бейджи">
                <h2 className="account-subheading">Бейджи</h2>
                <p className="learn-section-note">
                  Только заработанные (Learn-сезон или квиз ≥70%). До 8 на резюме.
                </p>
                {badges.filter((b) => b.earned).length === 0 ? (
                  <p className="learn-section-note">Пока нет заработанных бейджей.</p>
                ) : (
                  <ul className="hh-resume-skill-list">
                    {badges
                      .filter((b) => b.earned)
                      .map((badge) => (
                        <li key={badge.id}>
                          <label className="hh-resume-check">
                            <input
                              type="checkbox"
                              checked={selectedBadgeIds.includes(badge.id)}
                              onChange={() =>
                                setSelectedBadgeIds(toggleInList(selectedBadgeIds, badge.id))
                              }
                            />
                            <span>
                              {badge.title}
                              <span className="learn-section-note"> · {badge.kind}</span>
                            </span>
                          </label>
                        </li>
                      ))}
                  </ul>
                )}
              </section>

              <section className="hh-resume-ai-block" aria-label="GitHub">
                <h2 className="account-subheading">GitHub-проекты</h2>
                <label className="learn-admin-field">
                  <span>Публичный username</span>
                  <input
                    value={githubUsername}
                    onChange={(e) => setGithubUsername(e.target.value)}
                    maxLength={39}
                    placeholder="octocat"
                  />
                </label>
                <button
                  type="button"
                  className="learn-admin-btn learn-admin-btn-primary"
                  disabled={aiBusy || !githubUsername.trim()}
                  onClick={() => void onGithubFetch()}
                >
                  Загрузить репозитории
                </button>
                {githubProjects.length > 0 ? (
                  <ul className="hh-resume-skill-list">
                    {githubProjects.map((project) => (
                      <li key={project.url}>
                        <label className="hh-resume-check">
                          <input
                            type="checkbox"
                            checked={project.selected}
                            onChange={() =>
                              setGithubProjects((prev) =>
                                prev.map((p) =>
                                  p.url === project.url
                                    ? { ...p, selected: !p.selected }
                                    : p,
                                ),
                              )
                            }
                          />
                          <span>
                            {project.name}
                            {project.language ? ` · ${project.language}` : ''}
                            {project.stars > 0 ? ` · ★${project.stars}` : ''}
                          </span>
                        </label>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </section>

              <section className="hh-resume-ai-block" aria-label="Mock interview chat">
                <h2 className="account-subheading">Тренировочное собеседование</h2>
                <p className="learn-section-note">
                  Чат с AI по навыкам из резюме (до {chatMaxTurns || 5} ходов).
                </p>
                {!chatSessionId ? (
                  <button
                    type="button"
                    className="learn-admin-btn learn-admin-btn-primary"
                    disabled={aiBusy || skills.length === 0}
                    onClick={() => void onStartChat()}
                  >
                    Начать чат
                  </button>
                ) : (
                  <div className="hh-mock-chat">
                    <p className="learn-section-note">
                      Ход {Math.min(chatTurn, chatMaxTurns)} / {chatMaxTurns}
                      {chatDone ? ' · завершено' : ''}
                    </p>
                    <div className="hh-mock-chat-log" role="log">
                      {chatMessages.map((msg, idx) => (
                        <div
                          key={`${msg.role}-${idx}`}
                          className={
                            msg.role === 'user'
                              ? 'hh-mock-chat-bubble is-user'
                              : 'hh-mock-chat-bubble is-assistant'
                          }
                        >
                          <span className="hh-mock-chat-role">
                            {msg.role === 'user' ? 'Вы' : 'Интервьюер'}
                          </span>
                          <p>{msg.content}</p>
                        </div>
                      ))}
                    </div>
                    {chatSummary ? <p className="learn-admin-ok">{chatSummary}</p> : null}
                    {!chatDone ? (
                      <>
                        <textarea
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          rows={3}
                          placeholder="Ваш ответ"
                        />
                        <div className="account-actions">
                          <button
                            type="button"
                            className="learn-admin-btn learn-admin-btn-primary"
                            disabled={aiBusy || !chatInput.trim()}
                            onClick={() => void onSendChat()}
                          >
                            Отправить
                          </button>
                          <button
                            type="button"
                            className="learn-admin-btn"
                            disabled={aiBusy}
                            onClick={() => {
                              setChatSessionId('')
                              setChatMessages([])
                              setChatSummary('')
                              setChatDone(false)
                            }}
                          >
                            Сбросить
                          </button>
                        </div>
                      </>
                    ) : (
                      <button
                        type="button"
                        className="learn-admin-btn learn-admin-btn-primary"
                        disabled={aiBusy}
                        onClick={() => void onStartChat()}
                      >
                        Ещё раз
                      </button>
                    )}
                  </div>
                )}
              </section>

              <div className="account-actions">
                <button
                  type="submit"
                  className="learn-admin-btn learn-admin-btn-primary"
                  disabled={saving || enriching || aiBusy}
                >
                  Сохранить
                </button>
              </div>
            </form>
          </div>

          <aside className="hh-resume-split-preview" aria-label="Превью PDF">
            <p className="learn-section-note no-print">Живое превью</p>
            <HhResumeArticle
              preview={preview}
              skills={liveSkills}
              photoUrl={photoUrl}
              aboutOverride={about}
              specializationOverride={specialization}
              titleOverride={title}
              salaryOverride={
                salary.trim() && !Number.isNaN(salaryNumLive as number) ? salaryNumLive : null
              }
              employmentOverride={employment}
              workFormatsOverride={workFormats}
              versionNameOverride={versionName}
              badgeLabels={badgeLabels}
              projects={selectedProjects}
            />
          </aside>
        </div>
      )}
    </PageShell>
  )
}
