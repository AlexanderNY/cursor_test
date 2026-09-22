import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageShell } from '@/components/page-shell'
import { siteFetchPhotoBlob } from '@/data/site/site-api'
import {
  resumeGenerate,
  resumeGetPreview,
  type SiteResumePreview,
  type SiteResumeSkill,
} from '@/data/site/resume-api'
import {
  employmentLabel,
  workFormatLabel,
} from '@/data/site/resume-options'
import { getSiteAuthSession } from '@/data/site/site-auth'

function fullName(preview: SiteResumePreview): string {
  const parts = [
    preview.profile.lastName,
    preview.profile.firstName,
    preview.profile.patronymic,
  ].filter(Boolean)
  return parts.join(' ') || preview.username
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function buildDocHtml(preview: SiteResumePreview, skills: SiteResumeSkill[]): string {
  const name = fullName(preview)
  const skillLines = skills.map((s) => `<li>${escapeHtml(s.display)}</li>`).join('')
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

export function HhResumePage() {
  const session = getSiteAuthSession()
  const [preview, setPreview] = useState<SiteResumePreview | null>(null)
  const [photoUrl, setPhotoUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await resumeGetPreview()
      setPreview(data)
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

  const skills = useMemo(() => preview?.skills || [], [preview])

  async function onGenerate() {
    setBusy(true)
    setError('')
    setOk('')
    try {
      const result = await resumeGenerate({
        selected_skill_keys:
          preview?.resume.selectedSkillKeys.length
            ? preview.resume.selectedSkillKeys
            : undefined,
        persist: true,
      })
      setOk(
        result.skills.length > 0
          ? `Собрано навыков: ${result.skills.length} (пройдено: ${result.completedCount})`
          : `Пока нет навыков — отметьте выпуски в Learn (прогресс: ${result.completedCount})`,
      )
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка генерации')
    } finally {
      setBusy(false)
    }
  }

  function onPrint() {
    window.print()
  }

  function onDownloadDoc() {
    if (!preview) return
    const html = buildDocHtml(preview, skills)
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
        <p className="learn-eyebrow">Сервис · Резюме</p>
        <h1 className="learn-title">Резюме</h1>
        <p className="learn-lead">
          Анкета — в <Link to="/account">кабинете</Link>. Сначала{' '}
          <Link to="/game/hh-resume/quiz">опросник</Link>, затем правка в{' '}
          <Link to="/game/hh-resume/edit">доработке</Link> и навыки из Learn.
        </p>
        {error ? <p className="learn-admin-error">{error}</p> : null}
        {ok ? <p className="learn-admin-ok">{ok}</p> : null}
      </header>

      {loading ? (
        <p className="learn-section-note no-print">Загрузка…</p>
      ) : (
        <>
          <div className="account-actions no-print" style={{ marginBottom: '1.5rem' }}>
            <Link to="/game/hh-resume/quiz" className="learn-admin-btn learn-admin-btn-primary">
              Создать через опросник
            </Link>
            <Link to="/game/hh-resume/edit" className="learn-admin-btn learn-admin-btn-primary">
              Доработать резюме
            </Link>
            <button
              type="button"
              className="learn-admin-btn learn-admin-btn-primary"
              disabled={busy}
              onClick={() => void onGenerate()}
            >
              Обогатить навыками из Learn
            </button>
            <button type="button" className="learn-admin-btn" onClick={onPrint}>
              Печать / PDF
            </button>
            <button type="button" className="learn-admin-btn" onClick={onDownloadDoc}>
              Сохранить как DOC
            </button>
            <Link to="/account" className="learn-admin-btn">
              Анкета
            </Link>
            <Link to="/game/learn" className="learn-admin-btn">
              Learn
            </Link>
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
                <p>
                  {preview.resume.specialization ||
                    preview.resume.title ||
                    preview.suggestedSpecialization ||
                    '—'}
                </p>
                <p>
                  Оклад:{' '}
                  {preview.resume.salaryAmount != null
                    ? `${preview.resume.salaryAmount} ${preview.resume.salaryCurrency}`
                    : 'не указан'}
                </p>
                <p>Занятость: {employmentLabel(preview.resume.employmentTypes) || '—'}</p>
                <p>Формат работы: {workFormatLabel(preview.resume.workFormats) || '—'}</p>
              </section>

              {(preview.resume.about || preview.branchHints.length > 0) && (
                <section className="hh-resume-block">
                  <h3>О себе</h3>
                  <p>{preview.resume.about || preview.branchHints.join('. ')}</p>
                </section>
              )}

              <section className="hh-resume-block">
                <h3>Ключевые навыки</h3>
                {skills.length === 0 ? (
                  <p>—</p>
                ) : (
                  <ul>
                    {skills.map((skill) => (
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
