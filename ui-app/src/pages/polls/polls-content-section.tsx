import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { EmptyState } from '@/components/ui/empty-state'
import { TableSkeleton } from '@/components/ui/skeleton'
import { gameService } from '@/services/game-service'
import type {
  GameMode,
  GameModeType,
  GameOption,
  GameOptionInput,
  GameQuestion,
  GameQuestionDetail,
} from '@/types/game'
import { isCountryModeType } from '@/types/game'
import { CountryCatalogSection, QuestionsPerGameEditor } from './country-catalog-section'
import { CsvImportSection } from './csv-import-section'
import { MediaLibrarySection } from './media-library-section'
import { MenuNodesSection } from './menu-nodes-section'
import { usePollsContext } from './polls-context'

function emptyOptions(correctIndex = 1): GameOptionInput[] {
  return [1, 2, 3, 4, 5, 6].map((index) => ({
    option_index: index,
    option_text: '',
    is_correct: index === correctIndex,
  }))
}

function validateOptions(options: GameOptionInput[]): string | null {
  if (options.length !== 6) return 'Нужно ровно 6 вариантов ответа'
  const texts = options.map((o) => o.option_text.trim())
  if (texts.some((t) => !t)) return 'Заполните текст всех вариантов'
  if (options.filter((o) => o.is_correct).length !== 1) return 'Отметьте ровно один правильный ответ'
  return null
}

function questionsCountLabel(count: number): string {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod10 === 1 && mod100 !== 11) return `${count} вопрос`
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${count} вопроса`
  return `${count} вопросов`
}

function optionsForEditor(detail: GameQuestionDetail): GameOptionInput[] {
  const byIndex = new Map(detail.options.map((option) => [option.option_index, option]))
  const hasCorrect = detail.options.some((option) => option.is_correct)
  return emptyOptions().map((slot) => {
    const existing = byIndex.get(slot.option_index)
    return {
      option_index: slot.option_index,
      option_text: existing?.option_text ?? '',
      is_correct: existing ? existing.is_correct : !hasCorrect && slot.option_index === 1,
    }
  })
}

function isCompleteQuestion(question: GameQuestionDetail): boolean {
  return question.options.length === 6 && question.options.filter((option) => option.is_correct).length === 1
}

function QuestionOptionsView({ options }: { options: GameOption[] }) {
  const sorted = [...options].sort((a, b) => a.option_index - b.option_index)
  if (sorted.length === 0) {
    return <p className="text-sm text-amber-400">Вариантов нет — вопрос не попадёт в игру.</p>
  }

  return (
    <ol className="space-y-1.5">
      {sorted.map((option) => (
        <li
          key={option.id}
          className={`rounded-lg px-3 py-1.5 text-sm ${
            option.is_correct
              ? 'bg-emerald-500/15 text-emerald-300'
              : 'bg-[var(--bg-tertiary)] text-[var(--text-primary)]'
          }`}
        >
          <span className="mr-2 tabular-nums text-[var(--text-secondary)]">{option.option_index}.</span>
          {option.option_text}
          {option.is_correct && (
            <span className="ml-2 text-xs font-medium uppercase tracking-wide text-emerald-400">
              правильный
            </span>
          )}
        </li>
      ))}
    </ol>
  )
}

interface QuestionDraftFormProps {
  title: string
  promptText: string
  imageUrl: string
  options: GameOptionInput[]
  isSaving: boolean
  submitLabel: string
  onPromptTextChange: (value: string) => void
  onImageUrlChange: (value: string) => void
  onOptionTextChange: (index: number, text: string) => void
  onCorrectOptionChange: (index: number) => void
  onSubmit: (event: FormEvent) => void
  onCancel: () => void
}

function QuestionDraftForm({
  title,
  promptText,
  imageUrl,
  options,
  isSaving,
  submitLabel,
  onPromptTextChange,
  onImageUrlChange,
  onOptionTextChange,
  onCorrectOptionChange,
  onSubmit,
  onCancel,
}: QuestionDraftFormProps) {
  const sorted = [...options].sort((a, b) => a.option_index - b.option_index)

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <h3 className="text-sm font-semibold text-[var(--text-primary)]">{title}</h3>
      <textarea
        className="w-full min-h-[100px] rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
        placeholder="Текст вопроса"
        value={promptText}
        onChange={(event) => onPromptTextChange(event.target.value)}
      />
      <Input
        placeholder="URL изображения (необязательно, можно из медиатеки)"
        value={imageUrl}
        onChange={(event) => onImageUrlChange(event.target.value)}
      />
      {imageUrl && (
        <img
          src={imageUrl}
          alt="Превью"
          className="max-h-32 rounded-lg border border-[var(--border-color)] object-contain"
          onError={(event) => {
            ;(event.target as HTMLImageElement).style.display = 'none'
          }}
        />
      )}
      <div className="space-y-2">
        <p className="text-sm font-medium text-[var(--text-primary)]">Варианты ответа</p>
        {sorted.map((option) => (
          <div key={option.option_index} className="flex items-center gap-2">
            <input
              type="radio"
              name="correct-option"
              checked={option.is_correct}
              onChange={() => onCorrectOptionChange(option.option_index)}
              title="Правильный ответ"
            />
            <span className="w-6 text-sm text-[var(--text-secondary)]">{option.option_index}.</span>
            <Input
              className="flex-1"
              placeholder={`Вариант ${option.option_index}`}
              value={option.option_text}
              onChange={(event) => onOptionTextChange(option.option_index, event.target.value)}
            />
          </div>
        ))}
        <p className="text-xs text-[var(--text-secondary)]">
          Отметьте радиокнопкой один правильный ответ.
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button type="submit" isLoading={isSaving}>
          {submitLabel}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          Отмена
        </Button>
      </div>
    </form>
  )
}

export function PollsContentSection() {
  const {
    selectedBotId,
    modes,
    selectedModeId,
    setSelectedModeId,
    selectedMode,
    isMenuMode,
    isLoadingModes,
    loadModes,
  } = usePollsContext()

  const isCountryMode = selectedMode ? isCountryModeType(selectedMode.mode_type) : false

  const [questions, setQuestions] = useState<GameQuestionDetail[]>([])
  const [questionQuery, setQuestionQuery] = useState('')
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [newModeCode, setNewModeCode] = useState('')
  const [newModeTitle, setNewModeTitle] = useState('')
  const [newModeType, setNewModeType] = useState<GameModeType>('quiz')
  const [newModeQuestionsPerGame, setNewModeQuestionsPerGame] = useState('10')
  const [isCreatingMode, setIsCreatingMode] = useState(false)
  const [savingModeId, setSavingModeId] = useState<number | null>(null)
  const [deletingModeId, setDeletingModeId] = useState<number | null>(null)

  const [showQuestionForm, setShowQuestionForm] = useState(false)
  const [editingQuestionId, setEditingQuestionId] = useState<number | null>(null)
  const [promptText, setPromptText] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [options, setOptions] = useState<GameOptionInput[]>(emptyOptions())
  const [isSavingQuestion, setIsSavingQuestion] = useState(false)
  const [togglingQuestionId, setTogglingQuestionId] = useState<number | null>(null)
  const [deletingQuestionId, setDeletingQuestionId] = useState<number | null>(null)

  const loadQuestions = useCallback(async (modeId: number) => {
    setError('')
    setIsLoadingQuestions(true)
    try {
      const data = await gameService.listQuestionsWithOptions(modeId)
      setQuestions(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить вопросы')
      setQuestions([])
    } finally {
      setIsLoadingQuestions(false)
    }
  }, [])

  useEffect(() => {
    setQuestionQuery('')
    if (selectedModeId && !isMenuMode && !isCountryMode) {
      loadQuestions(selectedModeId)
    } else {
      setQuestions([])
    }
  }, [selectedModeId, isMenuMode, isCountryMode, loadQuestions])

  const visibleQuestions = useMemo(() => {
    const query = questionQuery.trim().toLowerCase()
    const matched = !query
      ? questions
      : questions.filter((question) => {
          if (String(question.id).includes(query)) return true
          if (question.prompt_text.toLowerCase().includes(query)) return true
          return question.options.some((option) => option.option_text.toLowerCase().includes(query))
        })
    if (!editingQuestionId || matched.some((question) => question.id === editingQuestionId)) {
      return matched
    }
    const editing = questions.find((question) => question.id === editingQuestionId)
    return editing ? [editing, ...matched] : matched
  }, [editingQuestionId, questionQuery, questions])

  function resetQuestionForm() {
    setEditingQuestionId(null)
    setShowQuestionForm(false)
    setPromptText('')
    setImageUrl('')
    setOptions(emptyOptions())
  }

  function openCreateQuestionForm() {
    setError('')
    setSuccess('')
    setEditingQuestionId(null)
    setPromptText('')
    setImageUrl('')
    setOptions(emptyOptions())
    setShowQuestionForm(true)
  }

  function openEditQuestionForm(question: GameQuestionDetail) {
    setError('')
    setSuccess('')
    setEditingQuestionId(question.id)
    setPromptText(question.prompt_text)
    setImageUrl(question.image_url ?? '')
    setOptions(optionsForEditor(question))
    setShowQuestionForm(true)
    requestAnimationFrame(() => {
      document.getElementById(`question-${question.id}`)?.scrollIntoView({ block: 'nearest' })
    })
  }

  async function handleCreateMode(e: FormEvent) {
    e.preventDefault()
    const questionsPerGame = Number.parseInt(newModeQuestionsPerGame, 10)
    if (!newModeCode.trim() || !newModeTitle.trim() || !selectedBotId) return
    if (
      newModeType === 'quiz' &&
      (!Number.isFinite(questionsPerGame) || questionsPerGame < 1)
    ) {
      return
    }

    setError('')
    setSuccess('')
    setIsCreatingMode(true)
    try {
      const created = await gameService.createMode({
        bot_id: selectedBotId,
        code: newModeCode.trim(),
        title: newModeTitle.trim(),
        questions_per_game: newModeType === 'menu' ? 1 : questionsPerGame,
        mode_type: newModeType,
        is_active: true,
      })
      setNewModeCode('')
      setNewModeTitle('')
      setNewModeType('quiz')
      setNewModeQuestionsPerGame('10')
      setSelectedModeId(created.id)
      await loadModes()
      setSuccess(`Режим «${created.title}» создан`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось создать режим')
    } finally {
      setIsCreatingMode(false)
    }
  }

  async function handleToggleModeActive(mode: GameMode) {
    setSavingModeId(mode.id)
    setError('')
    try {
      await gameService.updateMode(mode.id, { is_active: !mode.is_active })
      await loadModes()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось обновить режим')
    } finally {
      setSavingModeId(null)
    }
  }

  async function handleDeleteMode(mode: GameMode) {
    const actionLabel = mode.is_active ? 'удалить активный режим' : 'удалить режим'
    if (
      !window.confirm(
        `Вы уверены, что хотите ${actionLabel} «${mode.title}»? Все вопросы и история игр в этом режиме будут удалены безвозвратно.`,
      )
    ) {
      return
    }

    setDeletingModeId(mode.id)
    setError('')
    setSuccess('')
    try {
      await gameService.deleteMode(mode.id)
      if (selectedModeId === mode.id) {
        resetQuestionForm()
        setQuestions([])
      }
      setSuccess('Режим удалён')
      await loadModes()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось удалить режим')
    } finally {
      setDeletingModeId(null)
    }
  }

  async function handleSaveQuestion(e: FormEvent) {
    e.preventDefault()
    if (!selectedModeId) return

    const optionsError = validateOptions(options)
    if (!promptText.trim()) {
      setError('Введите текст вопроса')
      return
    }
    if (optionsError) {
      setError(optionsError)
      return
    }

    setError('')
    setSuccess('')
    setIsSavingQuestion(true)
    try {
      const trimmedUrl = imageUrl.trim()
      if (editingQuestionId) {
        await gameService.updateQuestion(editingQuestionId, {
          prompt_text: promptText.trim(),
          image_url: trimmedUrl || null,
        })
        await gameService.replaceOptions(editingQuestionId, options)
        setSuccess('Вопрос обновлён')
      } else {
        await gameService.createQuestion({
          mode_id: selectedModeId,
          prompt_text: promptText.trim(),
          image_url: trimmedUrl || null,
          options,
        })
        setSuccess('Вопрос добавлен')
      }
      resetQuestionForm()
      await loadQuestions(selectedModeId)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось сохранить вопрос')
    } finally {
      setIsSavingQuestion(false)
    }
  }

  async function handleToggleQuestionActive(question: GameQuestion) {
    setTogglingQuestionId(question.id)
    setError('')
    try {
      await gameService.updateQuestion(question.id, { is_active: !question.is_active })
      if (selectedModeId) await loadQuestions(selectedModeId)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось обновить вопрос')
    } finally {
      setTogglingQuestionId(null)
    }
  }

  async function handleDeleteQuestion(question: GameQuestion) {
    const actionLabel = question.is_active ? 'удалить активный вопрос' : 'удалить вопрос'
    if (!window.confirm(`Вы уверены, что хотите ${actionLabel} #${question.id}? Это действие необратимо.`)) {
      return
    }

    setDeletingQuestionId(question.id)
    setError('')
    setSuccess('')
    try {
      await gameService.deleteQuestion(question.id)
      if (editingQuestionId === question.id) {
        resetQuestionForm()
      }
      setSuccess('Вопрос удалён')
      if (selectedModeId) await loadQuestions(selectedModeId)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось удалить вопрос')
    } finally {
      setDeletingQuestionId(null)
    }
  }

  function handleOptionTextChange(index: number, text: string) {
    setOptions((prev) =>
      prev.map((o) => (o.option_index === index ? { ...o, option_text: text } : o)),
    )
  }

  function handleCorrectOptionChange(index: number) {
    setOptions((prev) =>
      prev.map((o) => ({ ...o, is_correct: o.option_index === index })),
    )
  }

  return (
    <>
      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}
      {success && (
        <Alert variant="success" className="mb-4">
          {success}
        </Alert>
      )}

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Режимы игры</CardTitle>
            <CardDescription>Например demo — вопросов за партию задаётся здесь.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleCreateMode} className="grid gap-3 rounded-xl border border-[var(--border-color)] p-4 sm:grid-cols-2 xl:grid-cols-4">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] sm:col-span-2 xl:col-span-4">Новый режим</h3>
              <Input
                placeholder="Код (латиница, demo)"
                value={newModeCode}
                onChange={(e) => setNewModeCode(e.target.value)}
              />
              <Input
                placeholder="Название"
                value={newModeTitle}
                onChange={(e) => setNewModeTitle(e.target.value)}
              />
              <div className="space-y-1">
                <label className="text-xs text-[var(--text-secondary)]">Тип режима</label>
                <select
                  className="w-full rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                  value={newModeType}
                  onChange={(e) => setNewModeType(e.target.value as GameModeType)}
                >
                  <option value="quiz">Викторина (вопросы)</option>
                  <option value="menu">Меню (иерархия)</option>
                </select>
              </div>
              {newModeType === 'quiz' && (
                <Input
                  type="number"
                  min={1}
                  max={300}
                  placeholder="Вопросов за игру"
                  value={newModeQuestionsPerGame}
                  onChange={(e) => setNewModeQuestionsPerGame(e.target.value)}
                />
              )}
              <Button
                type="submit"
                className="xl:self-end"
                disabled={!selectedBotId || !newModeCode.trim() || !newModeTitle.trim() || isCreatingMode}
                isLoading={isCreatingMode}
              >
                Создать режим
              </Button>
            </form>

            {isLoadingModes ? (
              <TableSkeleton rows={3} />
            ) : modes.length === 0 ? (
              <EmptyState title="Нет режимов" description="Создайте первый режим игры." />
            ) : (
              <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {modes.map((mode) => {
                  const isSelected = mode.id === selectedModeId
                  return (
                    <li key={mode.id}>
                      <button
                        type="button"
                        onClick={() => setSelectedModeId(mode.id)}
                        className={`w-full rounded-xl border p-3 text-left transition-colors ${
                          isSelected
                            ? 'border-primary-500 bg-primary-500/10'
                            : 'border-[var(--border-color)] hover:bg-[var(--bg-tertiary)]'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="font-medium text-[var(--text-primary)]">{mode.title}</p>
                            <p className="text-xs text-[var(--text-secondary)]">
                              {mode.code} ·{' '}
                              {mode.mode_type === 'menu'
                                ? 'меню'
                                : `${mode.questions_per_game} вопр./игра`}
                            </p>
                          </div>
                          <span
                            className={`shrink-0 rounded-full px-2 py-0.5 text-xs ${
                              mode.is_active
                                ? 'bg-emerald-500/15 text-emerald-400'
                                : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)]'
                            }`}
                          >
                            {mode.is_active ? 'активен' : 'выкл'}
                          </span>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2">
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            disabled={savingModeId === mode.id || deletingModeId === mode.id}
                            isLoading={savingModeId === mode.id}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleToggleModeActive(mode)
                            }}
                          >
                            {mode.is_active ? 'Выключить' : 'Включить'}
                          </Button>
                          <Button
                            type="button"
                            variant="danger"
                            size="sm"
                            disabled={savingModeId === mode.id || deletingModeId === mode.id}
                            isLoading={deletingModeId === mode.id}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteMode(mode)
                            }}
                          >
                            Удалить
                          </Button>
                        </div>
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
          </CardContent>
        </Card>

        <MenuNodesSection
          modes={modes}
          modeId={selectedModeId}
          onSelectMode={setSelectedModeId}
        />

        {isMenuMode ? null : isCountryMode && selectedMode ? (
          <CountryCatalogSection
            key={selectedMode.id}
            mode={selectedMode}
            onModeSaved={() => loadModes()}
          />
        ) : (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle className="text-lg">
                  Вопросы{selectedMode ? `: ${selectedMode.title}` : ''}
                </CardTitle>
                <CardDescription>
                  Состав каждого вопроса виден сразу: текст и шесть вариантов, правильный отмечен.
                  Правка открывается в той же карточке. Без полного набора вопрос не попадёт в игру.
                </CardDescription>
              </div>
              {selectedModeId && (
                <Button type="button" onClick={openCreateQuestionForm} disabled={showQuestionForm}>
                  Добавить вопрос
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {selectedMode && (
              <QuestionsPerGameEditor mode={selectedMode} onSaved={() => loadModes()} />
            )}

            <MediaLibrarySection
              onSelectUrl={(url) => {
                if (!showQuestionForm) {
                  setError('')
                  setEditingQuestionId(null)
                  setPromptText('')
                  setOptions(emptyOptions())
                  setShowQuestionForm(true)
                }
                setImageUrl(url)
                setSuccess('URL изображения подставлен в форму вопроса')
              }}
            />

            <CsvImportSection
              modeId={selectedModeId}
              modeTitle={selectedMode?.title}
              modeCode={selectedMode?.code}
              onImported={async () => {
                if (selectedModeId) await loadQuestions(selectedModeId)
              }}
            />

            {!selectedModeId ? (
              <EmptyState title="Выберите режим" description="Выше выберите или создайте режим игры." />
            ) : (
              <>
                {showQuestionForm && !editingQuestionId && (
                  <div className="rounded-xl border border-[var(--border-color)] p-4">
                    <QuestionDraftForm
                      title="Новый вопрос"
                      promptText={promptText}
                      imageUrl={imageUrl}
                      options={options}
                      isSaving={isSavingQuestion}
                      submitLabel="Создать вопрос"
                      onPromptTextChange={setPromptText}
                      onImageUrlChange={setImageUrl}
                      onOptionTextChange={handleOptionTextChange}
                      onCorrectOptionChange={handleCorrectOptionChange}
                      onSubmit={handleSaveQuestion}
                      onCancel={resetQuestionForm}
                    />
                  </div>
                )}

                {isLoadingQuestions ? (
                  <TableSkeleton rows={5} />
                ) : questions.length === 0 ? (
                  <EmptyState
                    title="Нет вопросов"
                    description="Добавьте вопросы с шестью вариантами ответа для выбранного режима."
                  />
                ) : (
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="text-sm text-[var(--text-secondary)]">
                        {questionsCountLabel(questions.length)}
                        {' · '}
                        активных {questions.filter((question) => question.is_active).length}
                      </p>
                      <Input
                        className="max-w-xs"
                        placeholder="Поиск по тексту или варианту"
                        value={questionQuery}
                        onChange={(event) => setQuestionQuery(event.target.value)}
                      />
                    </div>
                    {visibleQuestions.length === 0 ? (
                      <EmptyState
                        title="Ничего не найдено"
                        description="Измените запрос: ищется номер, текст вопроса и варианты ответа."
                      />
                    ) : (
                      visibleQuestions.map((question) => {
                        const isEditing = editingQuestionId === question.id
                        return (
                          <article
                            key={question.id}
                            id={`question-${question.id}`}
                            className={`space-y-3 rounded-xl border p-4 ${
                              isEditing
                                ? 'border-primary-500 bg-primary-500/5'
                                : 'border-[var(--border-color)]'
                            }`}
                          >
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--text-secondary)]">
                                <span className="font-mono">#{question.id}</span>
                                <span
                                  className={`rounded-full px-2 py-0.5 ${
                                    question.is_active
                                      ? 'bg-emerald-500/15 text-emerald-400'
                                      : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)]'
                                  }`}
                                >
                                  {question.is_active ? 'активен' : 'выкл'}
                                </span>
                                {!isCompleteQuestion(question) && (
                                  <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-amber-400">
                                    неполный набор
                                  </span>
                                )}
                              </div>
                              {!isEditing && (
                                <div className="flex flex-wrap gap-2">
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant="secondary"
                                    onClick={() => openEditQuestionForm(question)}
                                  >
                                    Изменить
                                  </Button>
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant="secondary"
                                    isLoading={togglingQuestionId === question.id}
                                    onClick={() => handleToggleQuestionActive(question)}
                                  >
                                    {question.is_active ? 'Выключить' : 'Включить'}
                                  </Button>
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant="danger"
                                    isLoading={deletingQuestionId === question.id}
                                    onClick={() => handleDeleteQuestion(question)}
                                  >
                                    Удалить
                                  </Button>
                                </div>
                              )}
                            </div>

                            {isEditing ? (
                              <QuestionDraftForm
                                title="Редактирование вопроса"
                                promptText={promptText}
                                imageUrl={imageUrl}
                                options={options}
                                isSaving={isSavingQuestion}
                                submitLabel="Сохранить"
                                onPromptTextChange={setPromptText}
                                onImageUrlChange={setImageUrl}
                                onOptionTextChange={handleOptionTextChange}
                                onCorrectOptionChange={handleCorrectOptionChange}
                                onSubmit={handleSaveQuestion}
                                onCancel={resetQuestionForm}
                              />
                            ) : (
                              <div className="flex gap-4">
                                <div className="min-w-0 flex-1 space-y-3">
                                  <p className="whitespace-pre-wrap text-sm text-[var(--text-primary)]">
                                    {question.prompt_text}
                                  </p>
                                  <QuestionOptionsView options={question.options} />
                                </div>
                                {question.image_url && (
                                  <img
                                    src={question.image_url}
                                    alt=""
                                    className="h-20 w-20 shrink-0 rounded-lg border border-[var(--border-color)] object-contain"
                                    onError={(event) => {
                                      ;(event.target as HTMLImageElement).style.display = 'none'
                                    }}
                                  />
                                )}
                              </div>
                            )}
                          </article>
                        )
                      })
                    )}
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
        )}
      </div>
    </>
  )
}
