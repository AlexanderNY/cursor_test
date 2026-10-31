import { EDUCATION_LEVEL_OPTIONS } from '@/data/site/resume-options'

export type ExperienceDraft = {
  company: string
  position: string
  city: string
  start: string
  end: string
  description: string
}

export type EducationDraft = {
  level: string
  institution: string
  faculty: string
  specialty: string
  year: string
}

export function emptyExperience(): ExperienceDraft {
  return { company: '', position: '', city: '', start: '', end: '', description: '' }
}

export function emptyEducation(): EducationDraft {
  return { level: 'higher', institution: '', faculty: '', specialty: '', year: '' }
}

const MAX_JOBS = 12
const MAX_SCHOOLS = 6

export function HhResumeHistoryFields({
  experience,
  education,
  onExperience,
  onEducation,
}: {
  experience: ExperienceDraft[]
  education: EducationDraft[]
  onExperience: (next: ExperienceDraft[]) => void
  onEducation: (next: EducationDraft[]) => void
}) {
  return (
    <>
      <fieldset className="hh-resume-fieldset">
        <legend>Опыт работы</legend>
        <p className="learn-section-note">
          Компания, должность и месяц начала. Пустая дата окончания — «по настоящее время».
          Эти строки hh.ru переносит в блок опыта.
        </p>
        {experience.map((job, index) => (
          <div key={index} className="hh-resume-entry">
            <div className="learn-admin-grid">
              <label className="learn-admin-field">
                <span>Компания</span>
                <input
                  value={job.company}
                  maxLength={160}
                  onChange={(event) =>
                    patchJob(experience, index, { company: event.target.value }, onExperience)
                  }
                />
              </label>
              <label className="learn-admin-field">
                <span>Должность</span>
                <input
                  value={job.position}
                  maxLength={160}
                  onChange={(event) =>
                    patchJob(experience, index, { position: event.target.value }, onExperience)
                  }
                />
              </label>
              <label className="learn-admin-field">
                <span>Город</span>
                <input
                  value={job.city}
                  maxLength={120}
                  onChange={(event) =>
                    patchJob(experience, index, { city: event.target.value }, onExperience)
                  }
                />
              </label>
              <label className="learn-admin-field">
                <span>Начало</span>
                <input
                  type="month"
                  value={job.start}
                  onChange={(event) =>
                    patchJob(experience, index, { start: event.target.value }, onExperience)
                  }
                />
              </label>
              <label className="learn-admin-field">
                <span>Окончание</span>
                <input
                  type="month"
                  value={job.end}
                  onChange={(event) =>
                    patchJob(experience, index, { end: event.target.value }, onExperience)
                  }
                />
              </label>
            </div>
            <label className="learn-admin-field">
              <span>Обязанности и результаты</span>
              <textarea
                value={job.description}
                rows={3}
                maxLength={4000}
                onChange={(event) =>
                  patchJob(experience, index, { description: event.target.value }, onExperience)
                }
              />
            </label>
            <button
              type="button"
              className="learn-admin-btn"
              onClick={() => onExperience(experience.filter((_, itemIndex) => itemIndex !== index))}
            >
              Убрать место работы
            </button>
          </div>
        ))}
        <button
          type="button"
          className="learn-admin-btn"
          disabled={experience.length >= MAX_JOBS}
          onClick={() => onExperience([...experience, emptyExperience()])}
        >
          Добавить место работы
        </button>
      </fieldset>

      <fieldset className="hh-resume-fieldset">
        <legend>Образование</legend>
        {education.map((school, index) => (
          <div key={index} className="hh-resume-entry">
            <div className="learn-admin-grid">
              <label className="learn-admin-field">
                <span>Уровень</span>
                <select
                  value={school.level}
                  onChange={(event) =>
                    patchSchool(education, index, { level: event.target.value }, onEducation)
                  }
                >
                  {EDUCATION_LEVEL_OPTIONS.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="learn-admin-field">
                <span>Учебное заведение</span>
                <input
                  value={school.institution}
                  maxLength={200}
                  onChange={(event) =>
                    patchSchool(
                      education,
                      index,
                      { institution: event.target.value },
                      onEducation,
                    )
                  }
                />
              </label>
              <label className="learn-admin-field">
                <span>Факультет</span>
                <input
                  value={school.faculty}
                  maxLength={160}
                  onChange={(event) =>
                    patchSchool(education, index, { faculty: event.target.value }, onEducation)
                  }
                />
              </label>
              <label className="learn-admin-field">
                <span>Специальность</span>
                <input
                  value={school.specialty}
                  maxLength={160}
                  onChange={(event) =>
                    patchSchool(education, index, { specialty: event.target.value }, onEducation)
                  }
                />
              </label>
              <label className="learn-admin-field">
                <span>Год окончания</span>
                <input
                  value={school.year}
                  inputMode="numeric"
                  maxLength={4}
                  onChange={(event) =>
                    patchSchool(education, index, { year: event.target.value }, onEducation)
                  }
                />
              </label>
            </div>
            <button
              type="button"
              className="learn-admin-btn"
              onClick={() => onEducation(education.filter((_, itemIndex) => itemIndex !== index))}
            >
              Убрать образование
            </button>
          </div>
        ))}
        <button
          type="button"
          className="learn-admin-btn"
          disabled={education.length >= MAX_SCHOOLS}
          onClick={() => onEducation([...education, emptyEducation()])}
        >
          Добавить образование
        </button>
      </fieldset>
    </>
  )
}

function patchJob(
  list: ExperienceDraft[],
  index: number,
  patch: Partial<ExperienceDraft>,
  onChange: (next: ExperienceDraft[]) => void,
) {
  onChange(list.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item)))
}

function patchSchool(
  list: EducationDraft[],
  index: number,
  patch: Partial<EducationDraft>,
  onChange: (next: EducationDraft[]) => void,
) {
  onChange(list.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item)))
}
