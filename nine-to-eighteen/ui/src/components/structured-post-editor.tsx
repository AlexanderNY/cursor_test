import { HtmlEditor } from '@/components/html-editor'
import { LearnContent } from '@/components/learn-content'
import { MarkdownField } from '@/components/markdown-field'
import type { MnemonicTechniqueId, StructuredPost } from '@/data/site/structured-post'
import {
  EMPTY_LEARN_STRUCTURED_POST,
  EMPTY_STRUCTURED_POST,
  MNEMONIC_TECHNIQUE_IDS,
  validateLearnStructuredPost,
  validateStructuredPost,
} from '@/data/site/structured-post'

const EMPTY_MNEMONIC = {
  technique: 'acronym' as MnemonicTechniqueId,
  title: '',
  prompt: '',
  items: [''],
  hint: '',
  answer: '',
}

type StructuredPostEditorProps = {
  value: StructuredPost
  onChange: (next: StructuredPost) => void
  /** Learn course: lab + HTML cheatsheet + stricter validation; hide blog-only summary. */
  mode?: 'blog' | 'learn'
}

function clone(post: StructuredPost): StructuredPost {
  return JSON.parse(JSON.stringify(post)) as StructuredPost
}

export function StructuredPostEditor({
  value,
  onChange,
  mode = 'blog',
}: StructuredPostEditorProps) {
  const isLearn = mode === 'learn'
  const errors = isLearn ? validateLearnStructuredPost(value) : validateStructuredPost(value)
  const emptyTemplate = isLearn ? EMPTY_LEARN_STRUCTURED_POST : EMPTY_STRUCTURED_POST

  function patch(mutator: (draft: StructuredPost) => void) {
    const draft = clone(value)
    mutator(draft)
    onChange(draft)
  }

  return (
    <div className="structured-editor">
      <p className="learn-section-note">
        {isLearn
          ? 'Шаблон Learn: теория → лаба → схемы → тест → шпаргалка → Anki → мнемоника (опционально).'
          : 'Единый формат: введение → основная часть → схемы → тест → итог/anki / мнемоника.'}
      </p>
      {errors.length > 0 ? (
        <ul className="structured-editor-errors">
          {errors.map((err) => (
            <li key={err}>{err}</li>
          ))}
        </ul>
      ) : (
        <p className="learn-admin-ok">Формат готов к публикации</p>
      )}

      <div id="edit-theory" className="structured-editor-block admin-jump-target">
        <MarkdownField
          label="Введение (теория, markdown)"
          rows={4}
          value={value.intro}
          onChange={(next) =>
            patch((d) => {
              d.intro = next
            })
          }
          placeholder="Зачем эта тема, контекст, что получит читатель…"
        />

        <div className="structured-editor-block-head">
          <h4 className="learn-panel-heading">Основная часть (теория)</h4>
          <button
            type="button"
            className="learn-admin-btn"
            onClick={() =>
              patch((d) => {
                d.sections.push({ heading: '', body: '' })
              })
            }
          >
            + Раздел
          </button>
        </div>
        {value.sections.map((section, index) => (
          <div key={`sec-${index}`} className="structured-editor-card">
            <label className="learn-admin-field">
              <span>Заголовок раздела</span>
              <input
                value={section.heading}
                onChange={(e) =>
                  patch((d) => {
                    d.sections[index].heading = e.target.value
                  })
                }
              />
            </label>
            <MarkdownField
              label="Текст (markdown)"
              rows={5}
              value={section.body}
              onChange={(next) =>
                patch((d) => {
                  d.sections[index].body = next
                })
              }
            />
            {value.sections.length > 1 ? (
              <button
                type="button"
                className="learn-admin-link learn-admin-danger"
                onClick={() =>
                  patch((d) => {
                    d.sections.splice(index, 1)
                  })
                }
              >
                Удалить раздел
              </button>
            ) : null}
          </div>
        ))}
      </div>

      {isLearn ? (
        <div id="edit-lab" className="structured-editor-block admin-jump-target">
          <div className="structured-editor-block-head">
            <h4 className="learn-panel-heading">Лабораторная работа</h4>
          </div>
          <p className="learn-section-note">
            Что сделать на ПК: цель, шаги, что сдать в группу, чеклист «готово если».
          </p>
          <MarkdownField
            label="Лаба (markdown)"
            rows={8}
            value={value.lab || ''}
            onChange={(next) =>
              patch((d) => {
                d.lab = next
              })
            }
            placeholder={'**Цель.** …\n\n**Шаги.**\n1. …'}
          />
        </div>
      ) : null}

      <div id="edit-diagrams" className="structured-editor-block admin-jump-target">
        <div className="structured-editor-block-head">
          <h4 className="learn-panel-heading">Схемы (Mermaid)</h4>
          <button
            type="button"
            className="learn-admin-btn"
            onClick={() =>
              patch((d) => {
                d.diagrams.push({ caption: '', mermaid: 'flowchart LR\n  A --> B' })
              })
            }
          >
            + Схема
          </button>
        </div>
        {value.diagrams.length === 0 ? (
          <p className="learn-section-note">
            {isLearn
              ? 'Нужна хотя бы одна схема.'
              : 'Необязательно. Добавьте схему, если помогает понять тему.'}
          </p>
        ) : null}
        {value.diagrams.map((diagram, index) => (
          <div key={`diag-${index}`} className="structured-editor-card">
            <label className="learn-admin-field">
              <span>Подпись</span>
              <input
                value={diagram.caption}
                onChange={(e) =>
                  patch((d) => {
                    d.diagrams[index].caption = e.target.value
                  })
                }
              />
            </label>
            <label className="learn-admin-field">
              <span>Mermaid</span>
              <textarea
                className="learn-admin-textarea"
                rows={4}
                value={diagram.mermaid}
                onChange={(e) =>
                  patch((d) => {
                    d.diagrams[index].mermaid = e.target.value
                  })
                }
              />
            </label>
            <button
              type="button"
              className="learn-admin-link learn-admin-danger"
              onClick={() =>
                patch((d) => {
                  d.diagrams.splice(index, 1)
                })
              }
            >
              Удалить схему
            </button>
          </div>
        ))}
      </div>

      <div id="edit-quiz" className="structured-editor-block admin-jump-target">
        <div className="structured-editor-block-head">
          <h4 className="learn-panel-heading">Тест (вопрос → ответ)</h4>
          <button
            type="button"
            className="learn-admin-btn"
            onClick={() =>
              patch((d) => {
                d.quiz.push({ question: '', answer: '', explain: '' })
              })
            }
          >
            + Вопрос
          </button>
        </div>
        {isLearn ? (
          <p className="learn-section-note">Краткий тест на запоминание: минимум 3 вопроса.</p>
        ) : null}
        {value.quiz.map((item, index) => (
          <div key={`quiz-${index}`} className="structured-editor-card">
            <label className="learn-admin-field">
              <span>Вопрос</span>
              <input
                value={item.question}
                onChange={(e) =>
                  patch((d) => {
                    d.quiz[index].question = e.target.value
                  })
                }
              />
            </label>
            <label className="learn-admin-field">
              <span>Ответ</span>
              <input
                value={item.answer}
                onChange={(e) =>
                  patch((d) => {
                    d.quiz[index].answer = e.target.value
                  })
                }
              />
            </label>
            <label className="learn-admin-field">
              <span>Пояснение</span>
              <textarea
                className="learn-admin-textarea"
                rows={2}
                value={item.explain}
                onChange={(e) =>
                  patch((d) => {
                    d.quiz[index].explain = e.target.value
                  })
                }
              />
            </label>
            <button
              type="button"
              className="learn-admin-link learn-admin-danger"
              onClick={() =>
                patch((d) => {
                  d.quiz.splice(index, 1)
                  if (d.quiz.length === 0) {
                    d.quiz.push({ question: '', answer: '', explain: '' })
                  }
                })
              }
            >
              Удалить вопрос
            </button>
          </div>
        ))}
      </div>

      {isLearn ? (
        <div id="edit-cheatsheet" className="structured-editor-block admin-jump-target">
          <div className="structured-editor-block-head">
            <h4 className="learn-panel-heading">Шпаргалка (HTML)</h4>
          </div>
          <p className="learn-section-note">
            Формулы, команды, таблицы, суть урока. Разрешены h1–h4, списки, table, pre/code. В
            `.md` уходит как HTML под секцией «Шпаргалка».
          </p>
          <HtmlEditor
            label="Шпаргалка (HTML)"
            value={value.cheatsheetHtml || ''}
            onChange={(html) =>
              patch((d) => {
                d.cheatsheetHtml = html
              })
            }
          />
          {(value.cheatsheetHtml || '').trim() ? (
            <div className="structured-editor-card">
              <p className="learn-section-note">Превью как на странице урока</p>
              <LearnContent content={value.cheatsheetHtml || ''} format="html" />
            </div>
          ) : null}
        </div>
      ) : null}

      <div id="edit-anki" className="structured-editor-block admin-jump-target">
        <div className="structured-editor-block-head">
          <h4 className="learn-panel-heading">Anki-карточки</h4>
          <button
            type="button"
            className="learn-admin-btn"
            onClick={() =>
              patch((d) => {
                d.anki.push({ front: '', back: '' })
              })
            }
          >
            + Карточка
          </button>
        </div>
        <p className="learn-section-note">
          {isLearn
            ? 'Колода листа карты: 3–8 авторских пар. Не подставляются из summary автоматически.'
            : 'Если пусто — при чтении карточки соберутся из теста и итогов.'}
        </p>
        {value.anki.map((item, index) => (
          <div key={`anki-${index}`} className="structured-editor-card">
            <label className="learn-admin-field">
              <span>Лицо (вопрос)</span>
              <input
                value={item.front}
                onChange={(e) =>
                  patch((d) => {
                    d.anki[index].front = e.target.value
                  })
                }
              />
            </label>
            <label className="learn-admin-field">
              <span>Оборот (ответ)</span>
              <textarea
                className="learn-admin-textarea"
                rows={2}
                value={item.back}
                onChange={(e) =>
                  patch((d) => {
                    d.anki[index].back = e.target.value
                  })
                }
              />
            </label>
            <button
              type="button"
              className="learn-admin-link learn-admin-danger"
              onClick={() =>
                patch((d) => {
                  d.anki.splice(index, 1)
                  if (d.anki.length === 0) {
                    d.anki.push({ front: '', back: '' })
                  }
                })
              }
            >
              Удалить карточку
            </button>
          </div>
        ))}
      </div>

      <div id="edit-mnemonics" className="structured-editor-block admin-jump-target">
        <div className="structured-editor-block-head">
          <h4 className="learn-panel-heading">Мнемоника (опционально)</h4>
          <button
            type="button"
            className="learn-admin-btn"
            onClick={() =>
              patch((d) => {
                if (!d.mnemonics) {
                  d.mnemonics = []
                }
                d.mnemonics.push({ ...EMPTY_MNEMONIC, items: [''] })
              })
            }
          >
            + Дрилл
          </button>
        </div>
        <p className="learn-section-note">
          Тренировка кодирования (акроним, цепочка, крючки…), не дублирует Anki. Пустой блок можно
          не заполнять.
        </p>
        {(value.mnemonics || []).map((item, index) => (
          <div key={`mnemonic-${index}`} className="structured-editor-card">
            <label className="learn-admin-field">
              <span>Техника</span>
              <select
                value={item.technique}
                onChange={(e) =>
                  patch((d) => {
                    if (!d.mnemonics) {
                      return
                    }
                    d.mnemonics[index].technique = e.target.value as MnemonicTechniqueId
                  })
                }
              >
                {MNEMONIC_TECHNIQUE_IDS.map((id) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </select>
            </label>
            <label className="learn-admin-field">
              <span>Заголовок</span>
              <input
                value={item.title}
                onChange={(e) =>
                  patch((d) => {
                    if (!d.mnemonics) {
                      return
                    }
                    d.mnemonics[index].title = e.target.value
                  })
                }
              />
            </label>
            <label className="learn-admin-field">
              <span>Задание</span>
              <textarea
                className="learn-admin-textarea"
                rows={2}
                value={item.prompt}
                onChange={(e) =>
                  patch((d) => {
                    if (!d.mnemonics) {
                      return
                    }
                    d.mnemonics[index].prompt = e.target.value
                  })
                }
              />
            </label>
            <label className="learn-admin-field">
              <span>Элементы (по строке)</span>
              <textarea
                className="learn-admin-textarea"
                rows={3}
                value={item.items.join('\n')}
                onChange={(e) =>
                  patch((d) => {
                    if (!d.mnemonics) {
                      return
                    }
                    d.mnemonics[index].items = e.target.value.split(/\r?\n/)
                  })
                }
              />
            </label>
            <label className="learn-admin-field">
              <span>Подсказка</span>
              <input
                value={item.hint || ''}
                onChange={(e) =>
                  patch((d) => {
                    if (!d.mnemonics) {
                      return
                    }
                    d.mnemonics[index].hint = e.target.value
                  })
                }
              />
            </label>
            <label className="learn-admin-field">
              <span>Ответ / эталон</span>
              <input
                value={item.answer || ''}
                onChange={(e) =>
                  patch((d) => {
                    if (!d.mnemonics) {
                      return
                    }
                    d.mnemonics[index].answer = e.target.value
                  })
                }
              />
            </label>
            <button
              type="button"
              className="learn-admin-link learn-admin-danger"
              onClick={() =>
                patch((d) => {
                  if (!d.mnemonics) {
                    return
                  }
                  d.mnemonics.splice(index, 1)
                })
              }
            >
              Удалить дрилл
            </button>
          </div>
        ))}
      </div>

      {!isLearn ? (
        <div className="structured-editor-block">
          <div className="structured-editor-block-head">
            <h4 className="learn-panel-heading">Итог (чеклист)</h4>
            <button
              type="button"
              className="learn-admin-btn"
              onClick={() =>
                patch((d) => {
                  d.summary.push('')
                })
              }
            >
              + Пункт
            </button>
          </div>
          {value.summary.map((line, index) => (
            <label key={`sum-${index}`} className="learn-admin-field">
              <span>Пункт {index + 1}</span>
              <input
                value={line}
                onChange={(e) =>
                  patch((d) => {
                    d.summary[index] = e.target.value
                  })
                }
              />
            </label>
          ))}
        </div>
      ) : (
        <div className="structured-editor-block">
          <div className="structured-editor-block-head">
            <h4 className="learn-panel-heading">Итог (опционально, 3 строки)</h4>
            <button
              type="button"
              className="learn-admin-btn"
              onClick={() =>
                patch((d) => {
                  d.summary.push('')
                })
              }
            >
              + Пункт
            </button>
          </div>
          <p className="learn-section-note">Не превращается в Anki автоматически.</p>
          {value.summary.map((line, index) => (
            <label key={`sum-${index}`} className="learn-admin-field">
              <span>Пункт {index + 1}</span>
              <input
                value={line}
                onChange={(e) =>
                  patch((d) => {
                    d.summary[index] = e.target.value
                  })
                }
              />
            </label>
          ))}
        </div>
      )}

      <MarkdownField
        label="Дополнительно (необязательный markdown)"
        rows={3}
        value={value.appendix || ''}
        onChange={(next) =>
          patch((d) => {
            d.appendix = next
          })
        }
      />

      <button
        type="button"
        className="learn-admin-btn"
        onClick={() => onChange(clone(emptyTemplate))}
      >
        Сбросить шаблон
      </button>
    </div>
  )
}
