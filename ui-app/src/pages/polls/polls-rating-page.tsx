import { useState } from 'react'
import { EmptyState } from '@/components/ui/empty-state'
import { RatingSection } from './rating-section'
import { usePollsContext } from './polls-context'

export function PollsRatingPage() {
  const { selectedBotId, modes, hasQuizModes } = usePollsContext()
  const quizModes = modes.filter((mode) => mode.mode_type === 'quiz')
  const [filterModeId, setFilterModeId] = useState<number | null>(null)

  if (!selectedBotId) {
    return (
      <EmptyState
        title="Выберите бота"
        description="Добавьте или выберите Telegram-бота в настройках выше."
      />
    )
  }

  if (!hasQuizModes) {
    return (
      <EmptyState
        title="Нет режимов викторины"
        description="Рейтинг и история прохождений доступны для режимов типа «Викторина»."
      />
    )
  }

  const filteredMode = filterModeId
    ? quizModes.find((mode) => mode.id === filterModeId) ?? null
    : null

  return (
    <RatingSection
      modeId={filterModeId}
      modeTitle={filteredMode?.title}
      showModeFilter
      quizModes={quizModes}
      filterModeId={filterModeId}
      onFilterModeIdChange={setFilterModeId}
      className="mt-0"
    />
  )
}
