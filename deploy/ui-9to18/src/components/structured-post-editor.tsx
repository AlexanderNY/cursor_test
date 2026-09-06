import type { StructuredPost } from '@/data/site/structured-post'
import { EMPTY_STRUCTURED_POST, validateStructuredPost } from '@/data/site/structured-post'

type StructuredPostEditorProps = {
  value: StructuredPost
  onChange: (next: StructuredPost) => void
}

function clone(post: StructuredPost): StructuredPost {
  return JSON.parse(JSON.stringify(post)) as StructuredPost
}

export function StructuredPostEditor({ value, onChange }: StructuredPostEditorProps) {
  const errors = validateStructuredPost(value)

  function patch(mutator: (draft: StructuredPost) => void) {
    const draft = clone(value)
    mutator(draft)
    onChange(draft)
  }

  return (
    <div className="structured-editor">
      <p className="learn-section-note">
        Единый формат: введение → основная часть → схемы → тест → итог/anki. Подходит и для
        проверки знаний, и для карточек повторения.
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

      <label className="learn-admin-field">
        <span>Введение</span>
        <textarea
          className="learn-admin-textarea"
          rows={4}
          value={value.intro}
          onChange={(e) => patch((d) => {
            d.intro = e.target.value
          })}
          placeholder="Зачем эта тема, контекст, что получит читатель…"
        />
      </label>

      <div className="structured-editor-block">
        <div className="structured-editor-block-head">
          <h4 className="learn-panel-heading">Основная часть</h4>
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
            <label className="learn-admin-field">
              <span>Текст (markdown)</span>
              <textarea
                className="learn-admin-textarea"
                rows={5}
                value={section.body}
                onChange={(e) =>
                  patch((d) => {
                    d.sections[index].body = e.target.value
                  })
                }
              />
            </label>
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

      <div className="structured-editor-block">
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
          <p className="learn-section-note">Необязательно. Добавьте схему, если помогает понять тему.</p>
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

      <div className="structured-editor-block">
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

      <div className="structured-editor-block">
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
          Если пусто — при чтении карточки соберутся из теста и итогов.
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

      <label className="learn-admin-field">
        <span>Дополнительно (необязательный markdown)</span>
        <textarea
          className="learn-admin-textarea"
          rows={3}
          value={value.appendix || ''}
          onChange={(e) =>
            patch((d) => {
              d.appendix = e.target.value
            })
          }
        />
      </label>

      <button
        type="button"
        className="learn-admin-btn"
        onClick={() => onChange(clone(EMPTY_STRUCTURED_POST))}
      >
        Сбросить шаблон
      </button>
    </div>
  )
}
