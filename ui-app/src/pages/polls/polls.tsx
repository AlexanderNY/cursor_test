import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { EmptyState } from '@/components/ui/empty-state'
import { TableSkeleton } from '@/components/ui/skeleton'
import { gameService } from '@/services/game-service'
import type { GameMode, GameOptionInput, GameQuestion } from '@/types/game'

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

export function PollsPage() {
  const [modes, setModes] = useState<GameMode[]>([])
  const [selectedModeId, setSelectedModeId] = useState<number | null>(null)
  const [questions, setQuestions] = useState<GameQuestion[]>([])
  const [isLoadingModes, setIsLoadingModes] = useState(true)
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [newModeCode, setNewModeCode] = useState('')
  const [newModeTitle, setNewModeTitle] = useState('')
  const [newModeQuestionsPerGame, setNewModeQuestionsPerGame] = useState('10')
  const [isCreatingMode, setIsCreatingMode] = useState(false)
  const [savingModeId, setSavingModeId] = useState<number | null>(null)

  const [showQuestionForm, setShowQuestionForm] = useState(false)
  const [editingQuestionId, setEditingQuestionId] = useState<number | null>(null)
  const [promptText, setPromptText] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [options, setOptions] = useState<GameOptionInput[]>(emptyOptions())
  const [isSavingQuestion, setIsSavingQuestion] = useState(false)
  const [loadingQuestionId, setLoadingQuestionId] = useState<number | null>(null)
  const [togglingQuestionId, setTogglingQuestionId] = useState<number | null>(null)

  const selectedMode = modes.find((m) => m.id === selectedModeId) ?? null

  const loadModes = useCallback(async () => {
    setError('')
    setIsLoadingModes(true)
    try {
      const data = await gameService.listModes(true)
      setModes(data)
      if (data.length > 0) {
        setSelectedModeId((prev) => (prev && data.some((m) => m.id === prev) ? prev : data[0].id))
      } else {
        setSelectedModeId(null)
        setQuestions([])
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить режимы')
    } finally {
      setIsLoadingModes(false)
    }
  }, [])

  const loadQuestions = useCallback(async (modeId: number) => {
    setError('')
    setIsLoadingQuestions(true)
    try {
      const data = await gameService.listQuestions(modeId)
      setQuestions(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить вопросы')
      setQuestions([])
    } finally {
      setIsLoadingQuestions(false)
    }
  }, [])

  useEffect(() => {
    loadModes()
  }, [loadModes])

  useEffect(() => {
    if (selectedModeId) {
      loadQuestions(selectedModeId)
    }
  }, [selectedModeId, loadQuestions])

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

  async function openEditQuestionForm(questionId: number) {
    setError('')
    setSuccess('')
    setLoadingQuestionId(questionId)
    try {
      const detail = await gameService.getQuestion(questionId)
      setEditingQuestionId(questionId)
      setPromptText(detail.prompt_text)
      setImageUrl(detail.image_url ?? '')
      setOptions(
        detail.options
          .sort((a, b) => a.option_index - b.option_index)
          .map((o) => ({
            option_index: o.option_index,
            option_text: o.option_text,
            is_correct: o.is_correct,
          })),
      )
      setShowQuestionForm(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить вопрос')
    } finally {
      setLoadingQuestionId(null)
    }
  }

  async function handleCreateMode(e: FormEvent) {
    e.preventDefault()
    const questionsPerGame = Number.parseInt(newModeQuestionsPerGame, 10)
    if (!newModeCode.trim() || !newModeTitle.trim() || !Number.isFinite(questionsPerGame)) return

    setError('')
    setSuccess('')
    setIsCreatingMode(true)
    try {
      const created = await gameService.createMode({
        code: newModeCode.trim(),
        title: newModeTitle.trim(),
        questions_per_game: questionsPerGame,
        is_active: true,
      })
      setNewModeCode('')
      setNewModeTitle('')
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
    <PageContainer>
      <PageHeader
        title="Polls"
        description="Управление контентом Telegram-игры: режимы, вопросы и варианты ответов (6 на вопрос, один верный)."
      />

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

      <div className="grid gap-6 lg:grid-cols-[minmax(280px,360px)_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Режимы игры</CardTitle>
            <CardDescription>Например demo — вопросов за партию задаётся здесь.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleCreateMode} className="space-y-3 rounded-xl border border-[var(--border-color)] p-4">
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">Новый режим</h3>
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
              <Input
                type="number"
                min={1}
                max={100}
                placeholder="Вопросов за игру"
                value={newModeQuestionsPerGame}
                onChange={(e) => setNewModeQuestionsPerGame(e.target.value)}
              />
              <Button
                type="submit"
                disabled={!newModeCode.trim() || !newModeTitle.trim() || isCreatingMode}
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
              <ul className="space-y-2">
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
                              {mode.code} · {mode.questions_per_game} вопр./игра
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
                        <div className="mt-2">
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            disabled={savingModeId === mode.id}
                            isLoading={savingModeId === mode.id}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleToggleModeActive(mode)
                            }}
                          >
                            {mode.is_active ? 'Выключить' : 'Включить'}
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

        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle className="text-lg">
                  Вопросы{selectedMode ? `: ${selectedMode.title}` : ''}
                </CardTitle>
                <CardDescription>
                  Каждый вопрос — 6 вариантов, один правильный. Без полного набора вопрос не попадёт в игру.
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
            {!selectedModeId ? (
              <EmptyState title="Выберите режим" description="Слева выберите или создайте режим игры." />
            ) : (
              <>
                {showQuestionForm && (
                  <form
                    onSubmit={handleSaveQuestion}
                    className="space-y-4 rounded-xl border border-[var(--border-color)] p-4"
                  >
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                      {editingQuestionId ? 'Редактирование вопроса' : 'Новый вопрос'}
                    </h3>
                    <textarea
                      className="w-full min-h-[100px] rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                      placeholder="Текст вопроса"
                      value={promptText}
                      onChange={(e) => setPromptText(e.target.value)}
                    />
                    <Input
                      placeholder="URL изображения (необязательно)"
                      value={imageUrl}
                      onChange={(e) => setImageUrl(e.target.value)}
                    />
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-[var(--text-primary)]">Варианты ответа</p>
                      {options
                        .sort((a, b) => a.option_index - b.option_index)
                        .map((option) => (
                          <div key={option.option_index} className="flex items-center gap-2">
                            <input
                              type="radio"
                              name="correct-option"
                              checked={option.is_correct}
                              onChange={() => handleCorrectOptionChange(option.option_index)}
                              title="Правильный ответ"
                            />
                            <span className="w-6 text-sm text-[var(--text-secondary)]">{option.option_index}.</span>
                            <Input
                              className="flex-1"
                              placeholder={`Вариант ${option.option_index}`}
                              value={option.option_text}
                              onChange={(e) =>
                                handleOptionTextChange(option.option_index, e.target.value)
                              }
                            />
                          </div>
                        ))}
                      <p className="text-xs text-[var(--text-secondary)]">
                        Отметьте радиокнопкой один правильный ответ.
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button type="submit" isLoading={isSavingQuestion}>
                        {editingQuestionId ? 'Сохранить' : 'Создать вопрос'}
                      </Button>
                      <Button type="button" variant="secondary" onClick={resetQuestionForm}>
                        Отмена
                      </Button>
                    </div>
                  </form>
                )}

                {isLoadingQuestions ? (
                  <TableSkeleton rows={5} />
                ) : questions.length === 0 ? (
                  <EmptyState
                    title="Нет вопросов"
                    description="Добавьте вопросы с шестью вариантами ответа для выбранного режима."
                  />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                          <th className="pb-2 pr-3 font-medium">ID</th>
                          <th className="pb-2 pr-3 font-medium">Вопрос</th>
                          <th className="pb-2 pr-3 font-medium">Статус</th>
                          <th className="pb-2 font-medium">Действия</th>
                        </tr>
                      </thead>
                      <tbody>
                        {questions.map((q) => (
                          <tr key={q.id} className="border-b border-[var(--border-color)]/60">
                            <td className="py-3 pr-3 text-[var(--text-secondary)]">{q.id}</td>
                            <td className="py-3 pr-3 max-w-md">
                              <p className="line-clamp-2 text-[var(--text-primary)]">{q.prompt_text}</p>
                              {q.image_url && (
                                <p className="mt-1 truncate text-xs text-[var(--text-secondary)]">
                                  {q.image_url}
                                </p>
                              )}
                            </td>
                            <td className="py-3 pr-3">
                              <span
                                className={`rounded-full px-2 py-0.5 text-xs ${
                                  q.is_active
                                    ? 'bg-emerald-500/15 text-emerald-400'
                                    : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)]'
                                }`}
                              >
                                {q.is_active ? 'активен' : 'выкл'}
                              </span>
                            </td>
                            <td className="py-3">
                              <div className="flex flex-wrap gap-2">
                                <Button
                                  type="button"
                                  size="sm"
                                  variant="secondary"
                                  isLoading={loadingQuestionId === q.id}
                                  onClick={() => openEditQuestionForm(q.id)}
                                >
                                  Изменить
                                </Button>
                                <Button
                                  type="button"
                                  size="sm"
                                  variant="secondary"
                                  isLoading={togglingQuestionId === q.id}
                                  onClick={() => handleToggleQuestionActive(q)}
                                >
                                  {q.is_active ? 'Выключить' : 'Включить'}
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
