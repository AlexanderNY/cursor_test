import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import {
  siteFetchPhotoBlob,
  siteGenerateResume,
  siteGetResumePreview,
  sitePutResume,
  type SiteResumePreview,
  type SiteResumeSkill,
} from '@/data/site/site-api'
import { getSiteAuthSession } from '@/data/site/site-auth'

const EMPLOYMENT_OPTIONS: Array<{ id: string; label: string }> = [
  { id: 'full', label: 'Полная занятость' },
  { id: 'part', label: 'Частичная занятость' },
  { id: 'project', label: 'Проектная работа' },
  { id: 'volunteer', label: 'Волонтёрство' },
  { id: 'internship', label: 'Стажировка' },
]

const WORK_FORMAT_OPTIONS: Array<{ id: string; label: string }> = [
  { id: 'office', label: 'Офис' },
  { id: 'remote', label: 'Удалённо' },
  { id: 'hybrid', label: 'Гибрид' },
  { id: 'travel', label: 'Разъездная' },
]

function toggleInList(list: string[], id: string): string[] {
  return list.includes(id) ? list.filter((x) => x !== id) : [...list, id]
}

function fullName(preview: SiteResumePreview): string {
  const parts = [
    preview.profile.lastName,
    preview.profile.firstName,
    preview.profile.patronymic,
  ].filter(Boolean)
  return parts.join(' ') || preview.username
}

function employmentLabel(ids: string[]): string {
  return ids
    .map((id) => EMPLOYMENT_OPTIONS.find((o) => o.id === id)?.label || id)
    .join(', ')
}

function workFormatLabel(ids: string[]): string {
  return ids
    .map((id) => WORK_FORMAT_OPTIONS.find((o) => o.id === id)?.label || id)
    .join(', ')
}

function buildDocHtml(preview: SiteResumePreview, skills: SiteResumeSkill[]): string {
  const name = fullName(preview)
  const skillLines = skills
    .map((s) => `<li>${escapeHtml(s.display)}</li>`)
    .join('')
  const about = preview.resume.about || preview.branchHints.join('. ')
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${escapeHtml(name)}</title></head><body>
<h1>${escapeHtml(name)}</h1>
<p>${escapeHtml(preview.profile.city || '')}${preview.profile.birthDate ? ` · ${escapeHtml(preview.profile.birthDate)}` : ''}</p>
<p>Тел.: ${escapeHtml(preview.profile.phone || '—')} · Email: ${escapeHtml(preview.profile.email || '—')}</p>
<p>Гражданство: ${escapeHtml(preview.profile.citizenship || '—')}. Командировки: ${preview.profile.readyForTrips ? 'готов' : 'не готов'}.</p>
<h2>Желаемая должность</h2>
<p>${escapeHtml(preview.resume.specialization || preview.resume.title || '—')}</p>
<p>Оклад: ${preview.resume.salaryAmount != null ? `${preview.resume.salaryAmount} ${escapeHtml(preview.resume.salaryCurrency)}` : 'не указан'}</p>
<p>Занятость: ${escapeHtml(employmentLabel(preview.resume.employmentTypes) || '—')}</p>
<p>Формат: ${escapeHtml(workFormatLabel(preview.resume.workFormats) || '—')}</p>
${about ? `<h2>О себе</h2><p>${escapeHtml(about)}</p>` : ''}
<h2>Ключевые навыки</h2>
<ul>${skillLines || '<li>—</li>'}</ul>
<p><em>Собрано на 9to18.ru из прогресса Learn</em></p>
</body></html>`
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

export function HhResumePage() {
  const session = getSiteAuthSession()
  const [preview, setPreview] = useState<SiteResumePreview | null>(null)
  const [skills, setSkills] = useState<SiteResumeSkill[]>([])
  const [selectedKeys, setSelectedKeys] = useState<string[]>([])
  const [photoUrl, setPhotoUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')

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
      const data = await siteGetResumePreview()
      setPreview(data)
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
  }, [])

  useEffect(() => {
    if (!session) {
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
  }, [session, load])

  const visibleSkills = useMemo(
    () => skills.filter((s) => selectedKeys.includes(s.key)),
    [skills, selectedKeys],
  )

  async function onSavePrefs(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setOk('')
    try {
      const salaryNum = salary.trim() ? Number(salary.replace(/\s/g, '')) : null
      if (salary.trim() && (salaryNum == null || Number.isNaN(salaryNum))) {
        throw new Error('Оклад должен быть числом')
      }
      await sitePutResume({
        title: title.trim(),
        specialization: specialization.trim(),
        salary_amount: salaryNum,
        salary_currency: 'RUB',
        employment_types: employment,
        work_formats: workFormats,
        about: about.trim(),
        selected_skill_keys: selectedKeys,
      })
      setOk('Предпочтения сохранены')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  async function onGenerate() {
    setSaving(true)
    setError('')
    setOk('')
    try {
      await sitePutResume({
        title: title.trim(),
        specialization: specialization.trim() || undefined,
        salary_amount: salary.trim() ? Number(salary.replace(/\s/g, '')) : null,
        employment_types: employment,
        work_formats: workFormats,
        about: about.trim(),
        selected_skill_keys: selectedKeys,
      })
      const result = await siteGenerateResume({
        selected_skill_keys: selectedKeys.length > 0 ? selectedKeys : undefined,
        persist: true,
      })
      setSkills(result.skills)
      if (selectedKeys.length === 0) {
        setSelectedKeys(result.skills.map((s) => s.key))
      }
      if (!specialization.trim() && result.suggestedSpecialization) {
        setSpecialization(result.suggestedSpecialization)
      }
      if (!about.trim() && result.branchHints.length > 0) {
        setAbout(result.branchHints.join('. ') + '.')
      }
      setOk(
        result.skills.length > 0
          ? `Собрано навыков: ${result.skills.length} (пройдено выпусков: ${result.completedCount})`
          : `Пока нет навыков — отметьте выпуски в Learn (прогресс: ${result.completedCount})`,
      )
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка генерации')
    } finally {
      setSaving(false)
    }
  }

  function onPrint() {
    window.print()
  }

  function onDownloadDoc() {
    if (!preview) return
    const html = buildDocHtml(
      {
        ...preview,
        resume: {
          ...preview.resume,
          title,
          specialization,
          salaryAmount: salary.trim() ? Number(salary.replace(/\s/g, '')) : null,
          employmentTypes: employment,
          workFormats: workFormats,
          about,
        },
      },
      visibleSkills,
    )
    const blob = new Blob(['\ufeff', html], { type: 'application/msword' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `resume-${fullName(preview).replace(/\s+/g, '_') || 'hh'}.doc`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (!session) {
    return (
      <PageShell>
        <Link to="/" className="back-link">
          ← На главную
        </Link>
        <header className="learn-header">
          <p className="learn-eyebrow">HH-резюме</p>
          <h1 className="learn-title">Резюме из Learn</h1>
          <p className="learn-lead">
            Нужен аккаунт 9to18: заполните анкету в кабинете и соберите навыки из пройденных
            выпусков.
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

  return (
    <PageShell>
      <Link to="/" className="back-link no-print">
        ← На главную
      </Link>

      <header className="learn-header no-print">
        <p className="learn-eyebrow">HH-резюме · 9to18</p>
        <h1 className="learn-title">Резюме</h1>
        <p className="learn-lead">
          Анкета — в{' '}
          <Link to="/account">личном кабинете</Link>. Здесь: оклад, должность и навыки из Learn /
          карты обучения.
        </p>
        {error ? <p className="learn-admin-error">{error}</p> : null}
        {ok ? <p className="learn-admin-ok">{ok}</p> : null}
      </header>

      {loading ? (
        <p className="learn-section-note no-print">Загрузка…</p>
      ) : (
        <>
          <form className="learn-admin-form hh-resume-form no-print" onSubmit={onSavePrefs}>
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
                  placeholder={preview?.suggestedSpecialization || 'например DevOps-инженер'}
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
              <span>О себе (опционально)</span>
              <textarea
                value={about}
                onChange={(e) => setAbout(e.target.value)}
                rows={4}
                maxLength={8000}
              />
            </label>

            <div className="account-actions">
              <button
                type="submit"
                className="learn-admin-btn learn-admin-btn-primary"
                disabled={saving}
              >
                Сохранить
              </button>
              <button
                type="button"
                className="learn-admin-btn learn-admin-btn-primary"
                disabled={saving}
                onClick={() => void onGenerate()}
              >
                Собрать из Learn
              </button>
              <Link to="/game/learn" className="learn-admin-btn">
                Learn
              </Link>
              <Link to="/game/learning-map" className="learn-admin-btn">
                Карта
              </Link>
              <Link to="/account" className="learn-admin-btn">
                Анкета
              </Link>
            </div>
          </form>

          {skills.length > 0 ? (
            <section className="hh-resume-skills-pick no-print" aria-label="Навыки">
              <h2 className="account-subheading">Навыки из Learn</h2>
              <p className="learn-section-note">
                Снимите галочки с лишнего перед печатью. Чтобы поднять уровень — дойдите связанные
                выпуски.
              </p>
              <ul className="hh-resume-skill-list">
                {skills.map((skill) => (
                  <li key={skill.key}>
                    <label className="hh-resume-check">
                      <input
                        type="checkbox"
                        checked={selectedKeys.includes(skill.key)}
                        onChange={() => setSelectedKeys(toggleInList(selectedKeys, skill.key))}
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
            <p className="learn-section-note no-print">
              Пока нет навыков. Отметьте выпуски в{' '}
              <Link to="/game/learn">Learn</Link> или на{' '}
              <Link to="/game/learning-map">карте</Link>, затем нажмите «Собрать из Learn».
            </p>
          )}

          <div className="account-actions no-print" style={{ marginBottom: '1.5rem' }}>
            <button type="button" className="learn-admin-btn" onClick={onPrint}>
              Печать / PDF
            </button>
            <button type="button" className="learn-admin-btn" onClick={onDownloadDoc}>
              Сохранить как DOC
            </button>
          </div>

          {preview ? (
            <article className="hh-resume-preview" id="hh-resume-print">
              <div className="hh-resume-preview-head">
                {photoUrl ? (
                  <img src={photoUrl} alt="" className="hh-resume-photo" />
                ) : (
                  <div className="hh-resume-photo hh-resume-photo-placeholder" aria-hidden>
                    фото
                  </div>
                )}
                <div>
                  <h2 className="hh-resume-name">{fullName(preview)}</h2>
                  <p className="hh-resume-meta">
                    {[preview.profile.city, preview.profile.birthDate]
                      .filter(Boolean)
                      .join(' · ') || '—'}
                  </p>
                  <p className="hh-resume-meta">
                    {preview.profile.phone || '—'} · {preview.profile.email || '—'}
                  </p>
                  <p className="hh-resume-meta">
                    Гражданство: {preview.profile.citizenship || '—'}
                    {' · '}
                    Командировки: {preview.profile.readyForTrips ? 'готов' : 'не готов'}
                  </p>
                </div>
              </div>

              <section className="hh-resume-block">
                <h3>Желаемая должность</h3>
                <p>{specialization || title || preview.suggestedSpecialization || '—'}</p>
                <p>
                  Оклад:{' '}
                  {salary.trim()
                    ? `${salary.trim()} ₽`
                    : preview.resume.salaryAmount != null
                      ? `${preview.resume.salaryAmount} ${preview.resume.salaryCurrency}`
                      : 'не указан'}
                </p>
                <p>Занятость: {employmentLabel(employment) || '—'}</p>
                <p>Формат работы: {workFormatLabel(workFormats) || '—'}</p>
              </section>

              {(about || preview.branchHints.length > 0) && (
                <section className="hh-resume-block">
                  <h3>О себе</h3>
                  <p>{about || preview.branchHints.join('. ')}</p>
                </section>
              )}

              <section className="hh-resume-block">
                <h3>Ключевые навыки</h3>
                {visibleSkills.length === 0 ? (
                  <p>—</p>
                ) : (
                  <ul>
                    {visibleSkills.map((skill) => (
                      <li key={skill.key}>{skill.display}</li>
                    ))}
                  </ul>
                )}
              </section>

              <p className="hh-resume-footer">
                Источник навыков: Learn · 9to18.ru · выпусков пройдено:{' '}
                {preview.completedCount}
              </p>
            </article>
          ) : null}
        </>
      )}
    </PageShell>
  )
}
