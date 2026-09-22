import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import {
  resumeGenerate,
  resumeGetPreview,
  resumePut,
  type SiteResumeSkill,
} from '@/data/site/resume-api'
import {
  EMPLOYMENT_OPTIONS,
  WORK_FORMAT_OPTIONS,
  toggleInList,
} from '@/data/site/resume-options'
import { getSiteAuthSession } from '@/data/site/site-auth'

/** Раздел доработки: текст из опросника можно править; навыки — из Learn. */
export function HhResumeEditPage() {
  const session = getSiteAuthSession()
  const location = useLocation()
  const fromQuiz = Boolean((location.state as { fromQuiz?: boolean } | null)?.fromQuiz)

  const [skills, setSkills] = useState<SiteResumeSkill[]>([])
  const [selectedKeys, setSelectedKeys] = useState<string[]>([])
  const [suggestedSpecialization, setSuggestedSpecialization] = useState<string | null>(null)
  const [branchHints, setBranchHints] = useState<string[]>([])
  const [completedCount, setCompletedCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [enriching, setEnriching] = useState(false)
  const [error, setError] = useState('')
  const [ok, setOk] = useState(fromQuiz ? 'Шаблон заполнен по опросу — поправьте текст при необходимости.' : '')

  const [title, setTitle] = useState('')
  const [specialization, setSpecialization] = useState('')
  const [salary, setSalary] = useState('')
  const [employment, setEmployment] = useState<string[]>([])
  const [workFormats, setWorkFormats] = useState<string[]>([])
  const [about, setAbout] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await resumeGetPreview()
      setSkills(data.skills)
      setSelectedKeys(
        data.resume.selectedSkillKeys.length > 0
          ? data.resume.selectedSkillKeys
          : data.skills.map((s) => s.key),
      )
      setTitle(data.resume.title)
      setSpecialization(data.resume.specialization)
      setSalary(data.resume.salaryAmount != null ? String(data.resume.salaryAmount) : '')
      setEmployment(data.resume.employmentTypes)
      setWorkFormats(data.resume.workFormats)
      setAbout(data.resume.about)
      setSuggestedSpecialization(data.suggestedSpecialization)
      setBranchHints(data.branchHints)
      setCompletedCount(data.completedCount)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить резюме')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!session) {
      setLoading(false)
      return
    }
    void load()
  }, [session, load])

  async function onSave(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setOk('')
    try {
      const salaryNum = salary.trim() ? Number(salary.replace(/\s/g, '')) : null
      if (salary.trim() && (salaryNum == null || Number.isNaN(salaryNum))) {
        throw new Error('Оклад должен быть числом')
      }
      await resumePut({
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
    setEnriching(true)
    setError('')
    setOk('')
    try {
      // Сохраняем текущий текст, чтобы навыки не затёрли правки пользователя
      const salaryNum = salary.trim() ? Number(salary.replace(/\s/g, '')) : null
      await resumePut({
        title: title.trim(),
        specialization: specialization.trim() || undefined,
        salary_amount: salary.trim() && !Number.isNaN(salaryNum as number) ? salaryNum : null,
        employment_types: employment,
        work_formats: workFormats,
        about: about.trim(),
        selected_skill_keys: selectedKeys,
      })
      const result = await resumeGenerate({
        selected_skill_keys: undefined,
        persist: true,
      })
      setSkills(result.skills)
      setSelectedKeys(result.skills.map((s) => s.key))
      setBranchHints(result.branchHints)
      setCompletedCount(result.completedCount)
      if (result.suggestedSpecialization) {
        setSuggestedSpecialization(result.suggestedSpecialization)
      }
      setOk(
        result.skills.length > 0
          ? `Добавлено навыков из Learn: ${result.skills.length} (пройдено выпусков: ${result.completedCount}). Текст «о себе» не менялся — при необходимости поправьте вручную.`
          : `Пока нет навыков — отметьте выпуски в Learn (прогресс: ${result.completedCount}).`,
      )
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось обогатить навыками')
    } finally {
      setEnriching(false)
    }
  }

  if (!session) {
    return (
      <PageShell>
        <Link to="/game/hh-resume" className="back-link">
          ← К превью
        </Link>
        <header className="learn-header">
          <p className="learn-eyebrow">Доработка резюме</p>
          <h1 className="learn-title">Нужен вход</h1>
          <p className="learn-section-note">
            <Link to="/login">Войти</Link>
            {' · '}
            <Link to="/register">Регистрация</Link>
          </p>
        </header>
      </PageShell>
    )
  }

  return (
    <PageShell>
      <Link to="/game/hh-resume" className="back-link">
        ← К превью резюме
      </Link>

      <header className="learn-header">
        <p className="learn-eyebrow">HH-резюме · доработка</p>
        <h1 className="learn-title">Доработать резюме</h1>
        <p className="learn-lead">
          Текст из опросника можно править. Навыки подтягиваются отдельно из пройденных выпусков
          Learn. Анкета (ФИО, фото) — в <Link to="/account">кабинете</Link>. Пройдено выпусков:{' '}
          <strong>{completedCount}</strong>.
        </p>
        {error ? <p className="learn-admin-error">{error}</p> : null}
        {ok ? <p className="learn-admin-ok">{ok}</p> : null}
      </header>

      <div className="account-actions" style={{ marginBottom: '1.25rem' }}>
        <Link to="/game/hh-resume/quiz" className="learn-admin-btn learn-admin-btn-primary">
          Пройти опросник заново
        </Link>
        <button
          type="button"
          className="learn-admin-btn learn-admin-btn-primary"
          disabled={enriching || loading}
          onClick={() => void onEnrichFromLearn()}
        >
          {enriching ? 'Обогащаем…' : 'Обогатить навыками из Learn'}
        </button>
        <Link to="/game/learn" className="learn-admin-btn">
          Learn
        </Link>
        <Link to="/game/learning-map" className="learn-admin-btn">
          Карта
        </Link>
      </div>

      {loading ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : (
        <form className="learn-admin-form hh-resume-form" onSubmit={onSave}>
          <div className="learn-admin-grid">
            <label className="learn-admin-field">
              <span>Заголовок резюме</span>
              <input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={255} />
            </label>
            <label className="learn-admin-field">
              <span>Желаемая должность / специализация</span>
              <input
                value={specialization}
                onChange={(e) => setSpecialization(e.target.value)}
                placeholder={suggestedSpecialization || 'например DevOps-инженер'}
                maxLength={255}
              />
            </label>
            <label className="learn-admin-field">
              <span>Желаемый оклад, ₽</span>
              <input
                value={salary}
                onChange={(e) => setSalary(e.target.value)}
                inputMode="numeric"
                placeholder="например 180000"
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
            <span>О себе — можно скорректировать текст из опросника</span>
            <textarea
              value={about}
              onChange={(e) => setAbout(e.target.value)}
              rows={7}
              maxLength={8000}
              placeholder={
                branchHints.length > 0
                  ? branchHints.join('. ')
                  : 'Кратко о опыте и целях'
              }
            />
          </label>

          {skills.length > 0 ? (
            <section className="hh-resume-skills-pick" aria-label="Навыки">
              <h2 className="account-subheading">Навыки из Learn</h2>
              <p className="learn-section-note">
                Снимите галочки с лишнего. Чтобы поднять уровень — дойдите связанные выпуски и снова
                нажмите «Обогатить навыками из Learn».
              </p>
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
                    {skill.sourceSlugs?.length ? (
                      <span className="hh-resume-skill-sources">
                        {skill.sourceSlugs.map((slug) => (
                          <Link key={slug} to={`/game/learn/${slug}`}>
                            {slug}
                          </Link>
                        ))}
                      </span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </section>
          ) : (
            <p className="learn-section-note">
              Навыков пока нет. Отметьте выпуски в <Link to="/game/learn">Learn</Link>, затем
              нажмите «Обогатить навыками из Learn».
            </p>
          )}

          <div className="account-actions">
            <button
              type="submit"
              className="learn-admin-btn learn-admin-btn-primary"
              disabled={saving || enriching}
            >
              Сохранить правки
            </button>
            <Link to="/game/hh-resume" className="learn-admin-btn">
              К превью
            </Link>
          </div>
        </form>
      )}
    </PageShell>
  )
}
