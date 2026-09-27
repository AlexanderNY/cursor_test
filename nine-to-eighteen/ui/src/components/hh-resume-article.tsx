import { Link } from 'react-router-dom'
import { employmentLabel, workFormatLabel } from '@/data/site/resume-options'
import type {
  GithubProject,
  SiteResumePreview,
  SiteResumeSkill,
} from '@/data/site/resume-api'

function fullName(preview: Pick<SiteResumePreview, 'profile' | 'username'>): string {
  const parts = [
    preview.profile.lastName,
    preview.profile.firstName,
    preview.profile.patronymic,
  ].filter(Boolean)
  return parts.join(' ') || preview.username
}

/** Живое превью резюме (редактор / печать). */
export function HhResumeArticle({
  preview,
  skills,
  photoUrl,
  aboutOverride,
  specializationOverride,
  titleOverride,
  salaryOverride,
  employmentOverride,
  workFormatsOverride,
  versionNameOverride,
  badgeLabels,
  projects,
}: {
  preview: SiteResumePreview
  skills: SiteResumeSkill[]
  photoUrl: string | null
  aboutOverride?: string
  specializationOverride?: string
  titleOverride?: string
  salaryOverride?: number | null
  employmentOverride?: string[]
  workFormatsOverride?: string[]
  versionNameOverride?: string
  badgeLabels?: string[]
  projects?: GithubProject[]
}) {
  const about = aboutOverride ?? preview.resume.about
  const specialization =
    specializationOverride ?? preview.resume.specialization
  const title = titleOverride ?? preview.resume.title
  const salaryAmount =
    salaryOverride !== undefined ? salaryOverride : preview.resume.salaryAmount
  const employment = employmentOverride ?? preview.resume.employmentTypes
  const workFormats = workFormatsOverride ?? preview.resume.workFormats
  const versionName = versionNameOverride ?? preview.resume.versionName

  return (
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
            {[preview.profile.city, preview.profile.birthDate].filter(Boolean).join(' · ') ||
              '—'}
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
          {specialization || title || preview.suggestedSpecialization || '—'}
        </p>
        <p>
          Оклад:{' '}
          {salaryAmount != null
            ? `${salaryAmount} ${preview.resume.salaryCurrency}`
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

      {badgeLabels && badgeLabels.length > 0 ? (
        <section className="hh-resume-block">
          <h3>Достижения</h3>
          <ul className="hh-resume-badges">
            {badgeLabels.map((label) => (
              <li key={label} className="hh-resume-badge-chip">
                {label}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {projects && projects.length > 0 ? (
        <section className="hh-resume-block">
          <h3>Проекты</h3>
          <ul>
            {projects.map((project) => (
              <li key={project.url}>
                <a href={project.url} target="_blank" rel="noreferrer">
                  {project.name}
                </a>
                {project.language ? ` · ${project.language}` : ''}
                {project.stars > 0 ? ` · ★${project.stars}` : ''}
                {project.description ? (
                  <p className="hh-resume-meta">{project.description}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <p className="hh-resume-footer">
        {versionName} · Learn · выпусков: {preview.completedCount}
      </p>
    </article>
  )
}

export function HhResumeStrengthBar({
  score,
  maxScore,
  actions,
  expanded,
  onToggle,
}: {
  score: number
  maxScore: number
  actions: Array<{ id: string; title: string; href?: string | null; points: number }>
  expanded: boolean
  onToggle: () => void
}) {
  const pct = Math.max(0, Math.min(100, Math.round((score / Math.max(maxScore, 1)) * 100)))
  return (
    <section className="hh-resume-strength" aria-label="Сила резюме">
      <button type="button" className="hh-resume-strength-toggle" onClick={onToggle}>
        <span>
          Сила резюме: <strong>{pct}%</strong>
        </span>
        <span className="hh-resume-strength-track" aria-hidden>
          <span className="hh-resume-strength-fill" style={{ width: `${pct}%` }} />
        </span>
        <span className="learn-section-note">
          {expanded ? 'Скрыть подсказки' : 'Как усилить'}
        </span>
      </button>
      {expanded && actions.length > 0 ? (
        <ul className="hh-resume-strength-actions">
          {actions.map((action) => (
            <li key={action.id}>
              {action.href ? (
                <Link to={action.href}>{action.title}</Link>
              ) : (
                <span>{action.title}</span>
              )}
            </li>
          ))}
        </ul>
      ) : null}
      {expanded && actions.length === 0 ? (
        <p className="learn-section-note">Отличный результат — резюме хорошо заполнено.</p>
      ) : null}
    </section>
  )
}
