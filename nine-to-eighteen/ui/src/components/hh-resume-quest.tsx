const STEPS = [
  { title: 'Роль', blurb: 'Кем выходите на рынок' },
  { title: 'Формат', blurb: 'Как готовы работать' },
  { title: 'Опыт', blurb: 'Где уже что-то делали' },
  { title: 'Учёба', blurb: 'Откуда пришли' },
  { title: 'О себе', blurb: 'Короткий живой текст' },
  { title: 'Навыки', blurb: 'Что подтверждаете делом' },
  { title: 'Бонус', blurb: 'Проекты и тренировка' },
] as const

export const HH_QUEST_COUNT = STEPS.length

export function HhResumeQuestTrack({
  step,
  done,
  onPick,
}: {
  step: number
  done: boolean[]
  onPick: (index: number) => void
}) {
  const cleared = done.filter(Boolean).length
  return (
    <div className="hh-quest">
      <p className="hh-quest-score">
        Уровни <strong>{cleared}</strong> / {STEPS.length}
      </p>
      <div className="hh-quest-track" role="tablist" aria-label="Уровни резюме">
        {STEPS.map((item, index) => {
          const className = [
            'hh-quest-step',
            index === step ? 'is-current' : '',
            done[index] ? 'is-done' : '',
          ]
            .filter(Boolean)
            .join(' ')
          return (
            <button
              key={item.title}
              type="button"
              role="tab"
              aria-selected={index === step}
              className={className}
              onClick={() => onPick(index)}
            >
              <span className="hh-quest-step-index">{done[index] ? '✓' : index + 1}</span>
              <span>
                <strong>{item.title}</strong>
                <small>{item.blurb}</small>
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
