import { Link } from 'react-router-dom'
import { safeHref } from '@/data/safe-url'
import {
  educationLevelLabel,
  hhListLabel,
  hhPeriodLabel,
  hhSalaryLabel,
  EMPLOYMENT_HH_LABEL,
  SCHEDULE_HH_LABEL,
} from '@/data/site/resume-options'
import type {
  GithubProject,
  ResumeEducation,
  ResumeExperience,
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
  experience,
  education,
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
  experience?: ResumeExperience[]
  education?: ResumeEducation[]
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
  const jobs = experience ?? preview.resume.experience ?? []
  const schools = education ?? preview.resume.education ?? []
  const salaryText = hhSalaryLabel(salaryAmount)
  const employmentText = hhListLabel(employment, EMPLOYMENT_HH_LABEL)
  const scheduleText = hhListLabel(workFormats, SCHEDULE_HH_LABEL)

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
        <h3>Желаемая должность и зарплата</h3>
        <p>
          {specialization || title || preview.suggestedSpecialization || '—'}
        </p>
        {salaryText ? <p>{salaryText}</p> : null}
        {employmentText ? <p>Занятость: {employmentText}</p> : null}
        {scheduleText ? <p>График работы: {scheduleText}</p> : null}
      </section>

      {jobs.length > 0 ? (
        <section className="hh-resume-block">
          <h3>Опыт работы</h3>
          {jobs.map((job) => (
            <div key={`${job.company}-${job.start}-${job.position}`} className="hh-resume-job">
              <p className="hh-resume-meta">{hhPeriodLabel(job.start, job.end)}</p>
              <p>
                <strong>{job.company}</strong>
                {job.city ? ` · ${job.city}` : ''}
              </p>
              <p>{job.position}</p>
              {job.description ? <p>{job.description}</p> : null}
            </div>
          ))}
        </section>
      ) : null}

      {schools.length > 0 ? (
        <section className="hh-resume-block">
          <h3>Образование</h3>
          {schools.map((school) => (
            <div key={`${school.institution}-${school.year ?? ''}`} className="hh-resume-job">
              {school.level ? <p>{educationLevelLabel(school.level)}</p> : null}
              <p>
                <strong>{school.institution}</strong>
                {school.year ? ` · ${school.year}` : ''}
              </p>
              {[school.faculty, school.specialty].filter(Boolean).length > 0 ? (
                <p>{[school.faculty, school.specialty].filter(Boolean).join(', ')}</p>
              ) : null}
            </div>
          ))}
        </section>
      ) : null}

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

      {(about || preview.branchHints.length > 0) && (
        <section className="hh-resume-block">
          <h3>Обо мне</h3>
          <p>{about || preview.branchHints.join('. ')}</p>
        </section>
      )}

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
                {safeHref(project.url) ? (
                  <a href={safeHref(project.url) || undefined} target="_blank" rel="noreferrer">
                    {project.name}
                  </a>
                ) : (
                  <span>{project.name}</span>
                )}
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
