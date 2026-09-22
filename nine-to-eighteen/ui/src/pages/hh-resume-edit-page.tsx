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
  resumeImproveAbout,
  resumeMockInterviewEvaluate,
  resumeMockInterviewStart,
  resumePut,
  resumeSkillGap,
  type MockInterviewQuestion,
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
import { getSiteAuthSession } from '@/data/site/site-auth'

/** Редактор + live-превью (split) + сила резюме + mock-interview. */
export function HhResumeEditPage() {
  const { resumeId = '' } = useParams()
  const session = getSiteAuthSession()
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

  const [mockQuestions, setMockQuestions] = useState<MockInterviewQuestion[]>([])
  const [mockIndex, setMockIndex] = useState(0)
  const [mockAnswer, setMockAnswer] = useState('')
  const [mockFeedback, setMockFeedback] = useState('')
  const [mockScores, setMockScores] = useState<number[]>([])

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
      setSuggestedSpecialization(data.suggestedSpecialization)
      setBranchHints(data.branchHints)
      setCompletedCount(data.completedCount)
      setGapRole(data.resume.specialization || data.suggestedSpecialization || '')
      setDoneRelevant(data.strength?.doneRelevantSlugs || [])
      setMissingRelevant(data.strength?.missingRelevantSlugs || [])
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
  }, [session, resumeId, load])

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

  async function onStartMock() {
    if (!resumeId) return
    setAiBusy(true)
    setError('')
    setOk('')
    setMockFeedback('')
    setMockAnswer('')
    setMockScores([])
    setMockIndex(0)
    try {
      const result = await resumeMockInterviewStart(resumeId, 5)
      setMockQuestions(result.questions)
      setOk(`Вопросов: ${result.questions.length}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось начать собеседование')
    } finally {
      setAiBusy(false)
    }
  }

  async function onSubmitMockAnswer() {
    if (!resumeId || !mockQuestions[mockIndex]) return
    const q = mockQuestions[mockIndex]
    if (!mockAnswer.trim()) {
      setError('Введите ответ')
      return
    }
    setAiBusy(true)
    setError('')
    try {
      const result = await resumeMockInterviewEvaluate(resumeId, {
        question: q.question,
        answer: mockAnswer.trim(),
        skill_key: q.skillKey,
      })
      setMockFeedback(`${result.score}/5 — ${result.feedback}`)
      setMockScores((prev) => [...prev, result.score])
      setOk(result.passed ? 'Ответ принят' : 'Есть над чем поработать')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка оценки')
    } finally {
      setAiBusy(false)
    }
  }

  function onNextMock() {
    setMockFeedback('')
    setMockAnswer('')
    if (mockIndex + 1 < mockQuestions.length) {
      setMockIndex((i) => i + 1)
    } else {
      const avg =
        mockScores.length > 0
          ? (mockScores.reduce((a, b) => a + b, 0) / mockScores.length).toFixed(1)
          : '—'
      setOk(`Собеседование завершено. Средний балл: ${avg}/5`)
      setMockQuestions([])
      setMockIndex(0)
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

              <section className="hh-resume-ai-block" aria-label="Сопроводительное">
                <h2 className="account-subheading">Сопроводительное письмо</h2>
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
                    onClick={() => void onCoverLetter()}
                  >
                    Сгенерировать
                  </button>
                  {coverLetter ? (
                    <button
                      type="button"
                      className="learn-admin-btn"
                      onClick={() => void navigator.clipboard.writeText(coverLetter)}
                    >
                      Копировать
                    </button>
                  ) : null}
                </div>
                {coverLetter ? <pre className="hh-resume-cover-letter">{coverLetter}</pre> : null}
              </section>

              <section className="hh-resume-ai-block" aria-label="Mock interview">
                <h2 className="account-subheading">Тренировочное собеседование</h2>
                <p className="learn-section-note">
                  AI задаст 3–5 вопросов по навыкам из резюме.
                </p>
                {mockQuestions.length === 0 ? (
                  <button
                    type="button"
                    className="learn-admin-btn learn-admin-btn-primary"
                    disabled={aiBusy || skills.length === 0}
                    onClick={() => void onStartMock()}
                  >
                    Начать собеседование
                  </button>
                ) : (
                  <div className="hh-mock-interview">
                    <p className="learn-section-note">
                      Вопрос {mockIndex + 1} из {mockQuestions.length}
                      {mockQuestions[mockIndex]?.skillKey
                        ? ` · ${mockQuestions[mockIndex].skillKey}`
                        : ''}
                    </p>
                    <p className="account-subheading">{mockQuestions[mockIndex]?.question}</p>
                    {mockQuestions[mockIndex]?.hint ? (
                      <p className="learn-section-note">Подсказка: {mockQuestions[mockIndex].hint}</p>
                    ) : null}
                    <textarea
                      value={mockAnswer}
                      onChange={(e) => setMockAnswer(e.target.value)}
                      rows={4}
                      placeholder="Ваш ответ"
                    />
                    {mockFeedback ? <p className="learn-admin-ok">{mockFeedback}</p> : null}
                    <div className="account-actions">
                      <button
                        type="button"
                        className="learn-admin-btn learn-admin-btn-primary"
                        disabled={aiBusy || !mockAnswer.trim()}
                        onClick={() => void onSubmitMockAnswer()}
                      >
                        Оценить ответ
                      </button>
                      <button
                        type="button"
                        className="learn-admin-btn"
                        disabled={aiBusy}
                        onClick={onNextMock}
                      >
                        {mockIndex + 1 < mockQuestions.length ? 'Далее' : 'Завершить'}
                      </button>
                    </div>
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
            />
          </aside>
        </div>
      )}
    </PageShell>
  )
}
