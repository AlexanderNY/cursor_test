import { useMemo, useState } from 'react'
import type { StructuredMnemonicItem } from '@/data/site/structured-post'
import { techniqueLabel } from '@/data/mnemonics/types'

type MnemonicDrillProps = {
  drill: StructuredMnemonicItem
  onComplete?: () => void
  compact?: boolean
}

function normalizeAnswer(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/ё/g, 'е')
    .replace(/[^\p{L}\p{N}]+/gu, '')
}

function answersMatch(given: string, expected: string): boolean {
  const a = normalizeAnswer(given)
  const b = normalizeAnswer(expected)
  if (!a || !b) {
    return false
  }
  return a === b || b.includes(a) || a.includes(b)
}

function shuffle<T>(items: T[]): T[] {
  const next = [...items]
  for (let i = next.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[next[i], next[j]] = [next[j], next[i]]
  }
  return next
}

const PEG_HOOKS = [
  '1 · кол',
  '2 · лебедь',
  '3 · трезубец',
  '4 · стул',
  '5 · крючок',
  '6 · бублик',
  '7 · коса',
  '8 · снеговик',
  '9 · улитка',
  '10 · тарелка+кол',
]

function AcronymEngine({
  drill,
  onDone,
}: {
  drill: StructuredMnemonicItem
  onDone: () => void
}) {
  const [value, setValue] = useState('')
  const [revealed, setRevealed] = useState(false)
  const expected = drill.answer || drill.items.map((item) => item[0] || '').join('')
  const ok = revealed && answersMatch(value, expected)

  return (
    <div className="mnemonic-engine">
      <p className="learn-section-note">Составьте акроним из первых букв элементов.</p>
      <ul className="account-feature-list">
        {drill.items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <label className="learn-admin-field">
        <span>Ваш акроним</span>
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={revealed}
          placeholder="Например: ACID"
        />
      </label>
      {!revealed ? (
        <button
          type="button"
          className="learn-admin-btn learn-admin-btn-primary"
          onClick={() => {
            setRevealed(true)
            onDone()
          }}
        >
          Проверить
        </button>
      ) : (
        <p className={ok ? 'learn-admin-ok' : 'learn-section-note'}>
          {ok ? 'Верно.' : `Эталон: ${expected}`}
          {drill.hint ? ` · ${drill.hint}` : ''}
        </p>
      )}
    </div>
  )
}

function AcrosticEngine({
  drill,
  onDone,
}: {
  drill: StructuredMnemonicItem
  onDone: () => void
}) {
  const [value, setValue] = useState('')
  const [revealed, setRevealed] = useState(false)
  const letters = drill.items.map((item) => (item[0] || '').toUpperCase()).join(' · ')
  const expected = drill.answer || ''
  const ok = revealed && (!expected || answersMatch(value, expected))

  return (
    <div className="mnemonic-engine">
      <p className="learn-section-note">
        Составьте фразу по первым буквам: <strong>{letters}</strong>
      </p>
      <ul className="account-feature-list">
        {drill.items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <label className="learn-admin-field">
        <span>Ваша фраза</span>
        <textarea
          className="learn-admin-textarea"
          rows={2}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={revealed}
        />
      </label>
      {!revealed ? (
        <button
          type="button"
          className="learn-admin-btn learn-admin-btn-primary"
          onClick={() => {
            setRevealed(true)
            onDone()
          }}
        >
          Сверить
        </button>
      ) : (
        <p className={ok ? 'learn-admin-ok' : 'learn-section-note'}>
          {expected ? `Эталон: ${expected}` : 'Запомните свою фразу — она и есть мнемоника.'}
          {drill.hint ? ` · ${drill.hint}` : ''}
        </p>
      )}
    </div>
  )
}

function ChunkingEngine({
  drill,
  onDone,
}: {
  drill: StructuredMnemonicItem
  onDone: () => void
}) {
  const source = drill.items.join(' ') || drill.answer || ''
  const [value, setValue] = useState('')
  const [revealed, setRevealed] = useState(false)
  const expected = drill.answer || source
  const ok = revealed && answersMatch(value.replace(/[-\s]/g, ''), expected.replace(/[-\s]/g, ''))

  return (
    <div className="mnemonic-engine">
      <p className="learn-section-note">
        Разбейте на группы и восстановите: <code>{source}</code>
      </p>
      {drill.hint ? <p className="learn-section-note">Подсказка: {drill.hint}</p> : null}
      <label className="learn-admin-field">
        <span>Ваши группы (например 54-32)</span>
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={revealed}
        />
      </label>
      {!revealed ? (
        <button
          type="button"
          className="learn-admin-btn learn-admin-btn-primary"
          onClick={() => {
            setRevealed(true)
            onDone()
          }}
        >
          Проверить
        </button>
      ) : (
        <p className={ok ? 'learn-admin-ok' : 'learn-section-note'}>
          {ok ? 'Верно.' : `Эталон: ${expected}`}
        </p>
      )}
    </div>
  )
}

function LinkEngine({
  drill,
  onDone,
}: {
  drill: StructuredMnemonicItem
  onDone: () => void
}) {
  const order = useMemo(() => shuffle(drill.items), [drill.items])
  const [picked, setPicked] = useState<string[]>([])
  const [revealed, setRevealed] = useState(false)
  const remaining = order.filter((item) => !picked.includes(item))
  const expected = drill.answer || drill.items.join(' → ')
  const ok =
    revealed &&
    picked.length === drill.items.length &&
    picked.every((item, index) => item === drill.items[index])

  return (
    <div className="mnemonic-engine">
      <p className="learn-section-note">
        Соберите цепочку в правильном порядке (придумайте историю между шагами).
      </p>
      <div className="mnemonic-chip-row">
        {remaining.map((item) => (
          <button
            key={item}
            type="button"
            className="learn-admin-btn"
            disabled={revealed}
            onClick={() => setPicked((prev) => [...prev, item])}
          >
            {item}
          </button>
        ))}
      </div>
      <p className="learn-panel-heading">Ваша цепочка</p>
      <ol className="account-feature-list">
        {picked.map((item) => (
          <li key={`picked-${item}`}>{item}</li>
        ))}
      </ol>
      <div className="mnemonic-chip-row">
        <button
          type="button"
          className="learn-admin-btn"
          disabled={revealed || picked.length === 0}
          onClick={() => setPicked((prev) => prev.slice(0, -1))}
        >
          Убрать последний
        </button>
        {!revealed ? (
          <button
            type="button"
            className="learn-admin-btn learn-admin-btn-primary"
            disabled={picked.length !== drill.items.length}
            onClick={() => {
              setRevealed(true)
              onDone()
            }}
          >
            Проверить
          </button>
        ) : null}
      </div>
      {revealed ? (
        <p className={ok ? 'learn-admin-ok' : 'learn-section-note'}>
          {ok ? 'Порядок верный.' : `Эталон: ${expected}`}
          {drill.hint ? ` · ${drill.hint}` : ''}
        </p>
      ) : null}
    </div>
  )
}

function PegEngine({
  drill,
  onDone,
}: {
  drill: StructuredMnemonicItem
  onDone: () => void
}) {
  const [slots, setSlots] = useState<Record<number, string>>({})
  const [revealed, setRevealed] = useState(false)
  const pool = useMemo(() => shuffle(drill.items), [drill.items])
  const used = new Set(Object.values(slots))
  const ok =
    revealed &&
    drill.items.every((item, index) => slots[index] === item)

  return (
    <div className="mnemonic-engine">
      <p className="learn-section-note">
        Повесьте каждый элемент на «крючок» (номер → образ → элемент).
      </p>
      <ol className="mnemonic-peg-list">
        {drill.items.map((_, index) => (
          <li key={`peg-${index}`}>
            <span className="mnemonic-peg-hook">{PEG_HOOKS[index] || `${index + 1}`}</span>
            <select
              value={slots[index] || ''}
              disabled={revealed}
              onChange={(e) =>
                setSlots((prev) => ({
                  ...prev,
                  [index]: e.target.value,
                }))
              }
            >
              <option value="">— выбрать —</option>
              {pool.map((item) => (
                <option
                  key={item}
                  value={item}
                  disabled={used.has(item) && slots[index] !== item}
                >
                  {item}
                </option>
              ))}
            </select>
          </li>
        ))}
      </ol>
      {!revealed ? (
        <button
          type="button"
          className="learn-admin-btn learn-admin-btn-primary"
          disabled={Object.keys(slots).length < drill.items.length}
          onClick={() => {
            setRevealed(true)
            onDone()
          }}
        >
          Проверить
        </button>
      ) : (
        <p className={ok ? 'learn-admin-ok' : 'learn-section-note'}>
          {ok ? 'Крючки на месте.' : `Эталон: ${drill.answer || drill.items.join(' · ')}`}
          {drill.hint ? ` · ${drill.hint}` : ''}
        </p>
      )}
    </div>
  )
}

function GenericEngine({
  drill,
  onDone,
}: {
  drill: StructuredMnemonicItem
  onDone: () => void
}) {
  const [value, setValue] = useState('')
  const [revealed, setRevealed] = useState(false)
  const expected = drill.answer || drill.items.join(' · ')
  const ok = revealed && (!expected || answersMatch(value, expected))

  return (
    <div className="mnemonic-engine">
      <p className="learn-section-note">
        {drill.technique === 'loci'
          ? 'Расставьте элементы по «комнатам» дворца и восстановите порядок.'
          : drill.technique === 'major'
            ? 'Переведите число в согласные → образ, затем восстановите.'
            : 'Свяжите звучание термина с ярким образом.'}
      </p>
      <ul className="account-feature-list">
        {drill.items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      {drill.hint ? <p className="learn-section-note">Подсказка: {drill.hint}</p> : null}
      <label className="learn-admin-field">
        <span>Ваш ответ / образ</span>
        <textarea
          className="learn-admin-textarea"
          rows={2}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={revealed}
        />
      </label>
      {!revealed ? (
        <button
          type="button"
          className="learn-admin-btn learn-admin-btn-primary"
          onClick={() => {
            setRevealed(true)
            onDone()
          }}
        >
          Сверить
        </button>
      ) : (
        <p className={ok ? 'learn-admin-ok' : 'learn-section-note'}>
          Эталон: {expected || 'свой устойчивый образ'}
        </p>
      )}
    </div>
  )
}

export function MnemonicDrill({ drill, onComplete, compact = false }: MnemonicDrillProps) {
  function handleDone() {
    onComplete?.()
  }

  let engine = <GenericEngine drill={drill} onDone={handleDone} />
  if (drill.technique === 'acronym') {
    engine = <AcronymEngine drill={drill} onDone={handleDone} />
  } else if (drill.technique === 'acrostic') {
    engine = <AcrosticEngine drill={drill} onDone={handleDone} />
  } else if (drill.technique === 'chunking') {
    engine = <ChunkingEngine drill={drill} onDone={handleDone} />
  } else if (drill.technique === 'link') {
    engine = <LinkEngine drill={drill} onDone={handleDone} />
  } else if (drill.technique === 'peg') {
    engine = <PegEngine drill={drill} onDone={handleDone} />
  }

  return (
    <div className={`mnemonic-drill${compact ? ' is-compact' : ''}`}>
      <div className="mnemonic-drill-head">
        <span className="structured-anki-label">{techniqueLabel(drill.technique)}</span>
        <h3 className="learn-panel-heading">{drill.title}</h3>
      </div>
      {drill.prompt ? <p className="learn-section-note">{drill.prompt}</p> : null}
      {engine}
    </div>
  )
}
