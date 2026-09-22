import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { MnemonicDrill } from '@/components/mnemonic-drill'
import {
  deleteCustomMnemonicDrill,
  loadCustomMnemonicDrills,
  upsertCustomMnemonicDrill,
  type CustomMnemonicDrill,
} from '@/data/mnemonics/custom-drills'
import {
  examplesForTechnique,
  toStructuredExample,
  type SeedMnemonicDrill,
} from '@/data/mnemonics/seed-drills'
import {
  getTechniqueMeta,
  parseItemsText,
  type MnemonicTechniqueId,
  type StructuredMnemonicItem,
} from '@/data/mnemonics/types'
import { markMnemonicDone } from '@/data/mnemonics/collect'

type MnemonicTrainerWorkspaceProps = {
  technique: MnemonicTechniqueId
}

type Phase = 'edit' | 'practice'

function emptyForm() {
  return { title: '', prompt: '', itemsText: '', hint: '', answer: '' }
}

export function MnemonicTrainerWorkspace({ technique }: MnemonicTrainerWorkspaceProps) {
  const meta = getTechniqueMeta(technique)
  const catalog = useMemo(() => examplesForTechnique(technique), [technique])
  const [phase, setPhase] = useState<Phase>('edit')
  const [saved, setSaved] = useState<CustomMnemonicDrill[]>(() =>
    loadCustomMnemonicDrills(technique),
  )
  const [title, setTitle] = useState('')
  const [prompt, setPrompt] = useState('')
  const [itemsText, setItemsText] = useState('')
  const [hint, setHint] = useState('')
  const [answer, setAnswer] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [active, setActive] = useState<StructuredMnemonicItem | null>(null)
  const [message, setMessage] = useState('')
  const [practiceKey, setPracticeKey] = useState(0)

  useEffect(() => {
    setSaved(loadCustomMnemonicDrills(technique))
    setPhase('edit')
    setActive(null)
    setEditingId(null)
    const blank = emptyForm()
    setTitle(blank.title)
    setPrompt(blank.prompt)
    setItemsText(blank.itemsText)
    setHint(blank.hint)
    setAnswer(blank.answer)
    setMessage('')
  }, [technique])

  const draftItems = useMemo(
    () => parseItemsText(itemsText, technique),
    [itemsText, technique],
  )

  const canStart =
    draftItems.length > 0 || Boolean(answer.trim()) || Boolean(prompt.trim())

  if (!meta) {
    return <p className="learn-section-note">Неизвестная техника.</p>
  }

  const metaTitle = meta.title
  const metaExampleTitle = meta.exampleTitle
  const metaHowTo = meta.howTo
  const metaItemsLabel = meta.itemsLabel
  const metaInputHint = meta.inputHint
  const metaAnswerLabel = meta.answerLabel
  const metaAnswerPlaceholder = meta.answerPlaceholder

  function applyExample(example: SeedMnemonicDrill | StructuredMnemonicItem) {
    setEditingId(null)
    setTitle(example.title)
    setPrompt(example.prompt)
    setItemsText(example.items.join('\n'))
    setHint(example.hint || '')
    setAnswer(example.answer || '')
    setPhase('edit')
    setMessage(`В форме: «${example.title}» — правьте и сохраните как свой пример.`)
  }

  function loadIntoForm(drill: CustomMnemonicDrill) {
    setEditingId(drill.id)
    setTitle(drill.title)
    setPrompt(drill.prompt)
    setItemsText(drill.items.join('\n'))
    setHint(drill.hint || '')
    setAnswer(drill.answer || '')
    setPhase('edit')
    setMessage('Редактирование вашего примера.')
  }

  function startPractice(drill: StructuredMnemonicItem) {
    setActive(drill)
    setPracticeKey((prev) => prev + 1)
    setPhase('practice')
    setMessage('')
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    const items = parseItemsText(itemsText, technique)
    if (items.length === 0 && !answer.trim()) {
      setMessage('Добавьте элементы или эталонный ответ.')
      return
    }
    const savedDrill = upsertCustomMnemonicDrill({
      id: editingId || undefined,
      technique,
      title: title.trim() || metaTitle,
      prompt: prompt.trim() || `Запомните материал техникой «${metaTitle}».`,
      items,
      hint: hint.trim() || undefined,
      answer: answer.trim() || undefined,
    })
    setSaved(loadCustomMnemonicDrills(technique))
    setEditingId(savedDrill.id)
    setMessage('Пример сохранён в браузере.')
    startPractice(savedDrill)
  }

  function onDelete(id: string) {
    deleteCustomMnemonicDrill(id)
    setSaved(loadCustomMnemonicDrills(technique))
    if (editingId === id) {
      setEditingId(null)
    }
    setMessage('Пример удалён.')
  }

  function practiceWithoutSave() {
    const items = parseItemsText(itemsText, technique)
    if (items.length === 0 && !answer.trim()) {
      setMessage('Добавьте элементы или эталонный ответ.')
      return
    }
    startPractice({
      technique,
      title: title.trim() || 'Черновик',
      prompt: prompt.trim() || `Запомните материал техникой «${metaTitle}».`,
      items,
      hint: hint.trim() || undefined,
      answer: answer.trim() || undefined,
    })
  }

  function resetForm() {
    setEditingId(null)
    const blank = emptyForm()
    setTitle(blank.title)
    setPrompt(blank.prompt)
    setItemsText(blank.itemsText)
    setHint(blank.hint)
    setAnswer(blank.answer)
    setMessage('Новый пример.')
  }

  if (phase === 'practice' && active) {
    return (
      <section className="mnemonic-workspace" aria-labelledby="mnemonic-practice">
        <div className="mnemonic-workspace-toolbar">
          <button type="button" className="learn-admin-btn" onClick={() => setPhase('edit')}>
            ← К примерам
          </button>
          <button
            type="button"
            className="learn-admin-btn"
            onClick={() => startPractice(active)}
          >
            Заново
          </button>
        </div>
        <h2 id="mnemonic-practice" className="learn-section-title">
          Тренировка · {metaTitle}
        </h2>
        <MnemonicDrill
          key={`${practiceKey}-${active.title}`}
          drill={active}
          onComplete={() =>
            markMnemonicDone(`custom/${technique}/${active.title}`)
          }
        />
      </section>
    )
  }

  return (
    <section className="mnemonic-workspace" aria-labelledby="mnemonic-edit">
      <h2 id="mnemonic-edit" className="learn-section-title">
        {metaTitle}: примеры
      </h2>
      <p className="learn-lead">{metaHowTo}</p>

      <div className="mnemonic-examples-block" id="mnemonic-catalog">
        <h3 className="learn-panel-heading">
          Готовые примеры ({catalog.length})
        </h3>
        {catalog.length === 0 ? (
          <p className="learn-section-note">Пока нет каталога — добавьте свой ниже.</p>
        ) : (
          <ul className="mnemonic-saved-list">
            {catalog.map((example) => (
              <li key={`${example.technique}-${example.title}`} className="mnemonic-saved-item">
                <div>
                  <strong>{example.title}</strong>
                  <p className="learn-section-note">
                    {example.items.slice(0, 6).join(' · ')}
                    {example.items.length > 6 ? '…' : ''}
                    {example.answer ? ` → ${example.answer}` : ''}
                  </p>
                </div>
                <div className="mnemonic-chip-row">
                  <button
                    type="button"
                    className="learn-admin-btn learn-admin-btn-primary"
                    onClick={() => startPractice(toStructuredExample(example))}
                  >
                    Тренировать
                  </button>
                  <button
                    type="button"
                    className="learn-admin-btn"
                    onClick={() => applyExample(example)}
                  >
                    В форму
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="mnemonic-saved-block">
        <h3 className="learn-panel-heading">Ваши примеры ({saved.length})</h3>
        {saved.length === 0 ? (
          <p className="learn-section-note">
            Пока пусто — заполните форму ниже. Хранится только в этом браузере.
          </p>
        ) : (
          <ul className="mnemonic-saved-list">
            {saved.map((drill) => (
              <li key={drill.id} className="mnemonic-saved-item">
                <div>
                  <strong>{drill.title}</strong>
                  <p className="learn-section-note">
                    {drill.items.slice(0, 5).join(' · ')}
                    {drill.items.length > 5 ? '…' : ''}
                  </p>
                </div>
                <div className="mnemonic-chip-row">
                  <button
                    type="button"
                    className="learn-admin-btn learn-admin-btn-primary"
                    onClick={() => startPractice(drill)}
                  >
                    Тренировать
                  </button>
                  <button
                    type="button"
                    className="learn-admin-btn"
                    onClick={() => loadIntoForm(drill)}
                  >
                    Изменить
                  </button>
                  <button
                    type="button"
                    className="learn-admin-link learn-admin-danger"
                    onClick={() => onDelete(drill.id)}
                  >
                    Удалить
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <form className="learn-admin-form mnemonic-custom-form" onSubmit={onSubmit}>
        <h3 className="learn-panel-heading">
          {editingId ? 'Изменить пример' : 'Добавить свой пример'}
        </h3>
        <label className="learn-admin-field">
          <span>Название</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={metaExampleTitle}
          />
        </label>
        <label className="learn-admin-field">
          <span>Задание для себя</span>
          <textarea
            className="learn-admin-textarea"
            rows={2}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Что именно нужно запомнить и зачем"
          />
        </label>
        <label className="learn-admin-field">
          <span>{metaItemsLabel}</span>
          <textarea
            className="learn-admin-textarea"
            rows={technique === 'chunking' || technique === 'major' ? 2 : 6}
            value={itemsText}
            onChange={(e) => setItemsText(e.target.value)}
            placeholder={metaInputHint}
          />
        </label>
        <p className="learn-section-note">
          Распознано элементов: {draftItems.length}
          {draftItems.length > 0 ? ` · ${draftItems.slice(0, 4).join(' · ')}` : ''}
        </p>
        <label className="learn-admin-field">
          <span>Подсказка (необязательно)</span>
          <input
            value={hint}
            onChange={(e) => setHint(e.target.value)}
            placeholder="Как кодировать"
          />
        </label>
        <label className="learn-admin-field">
          <span>{metaAnswerLabel}</span>
          <input
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder={metaAnswerPlaceholder}
          />
        </label>

        <div className="mnemonic-chip-row">
          <button
            type="submit"
            className="learn-admin-btn learn-admin-btn-primary"
            disabled={!canStart}
          >
            Сохранить и тренировать
          </button>
          <button
            type="button"
            className="learn-admin-btn"
            disabled={!canStart}
            onClick={practiceWithoutSave}
          >
            Только потренировать
          </button>
          {catalog[0] ? (
            <button
              type="button"
              className="learn-admin-btn"
              onClick={() => applyExample(catalog[0])}
            >
              Первый из каталога
            </button>
          ) : null}
          {editingId || title || prompt || itemsText ? (
            <button type="button" className="learn-admin-btn" onClick={resetForm}>
              Сбросить форму
            </button>
          ) : null}
        </div>
        {message ? <p className="learn-section-note">{message}</p> : null}
      </form>

      <p className="learn-section-note">
        Дриллы из Learn по этой технике — в{' '}
        <Link to={`/game/mnemonics?tab=learn&tech=${technique}`}>общей сессии</Link>.
      </p>
    </section>
  )
}
