import { FormEvent, useCallback, useEffect, useState } from 'react'
import { MarkdownField } from '@/components/markdown-field'
import {
  siteCreateNote,
  siteDeleteNote,
  siteDeleteNoteFile,
  siteFetchNoteFileBlob,
  siteListNotes,
  siteUpdateNote,
  siteUploadNoteFile,
  type SiteUserNote,
} from '@/data/site/site-api'

export function NotesPanel() {
  const [items, setItems] = useState<SiteUserNote[]>([])
  const [ready, setReady] = useState(false)
  const [error, setError] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [tag, setTag] = useState('')
  const [busy, setBusy] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const next = await siteListNotes()
      setItems(next)
      setError('')
      if (selectedId == null && next[0]) {
        setSelectedId(next[0].id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить заметки')
      setItems([])
    } finally {
      setReady(true)
    }
  }, [selectedId])

  useEffect(() => {
    void refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps -- initial load only
  }, [])

  const selected = items.find((item) => item.id === selectedId) || null

  useEffect(() => {
    if (!selected) {
      setTitle('')
      setBody('')
      setTag('')
      return
    }
    setTitle(selected.title)
    setBody(selected.body)
    setTag(selected.tag)
  }, [selected])

  async function handleCreate() {
    setBusy(true)
    try {
      const note = await siteCreateNote({ title: 'Новая заметка', body: '' })
      await refresh()
      setSelectedId(note.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать')
    } finally {
      setBusy(false)
    }
  }

  async function handleSave(event: FormEvent) {
    event.preventDefault()
    if (!selected || busy) {
      return
    }
    setBusy(true)
    try {
      const updated = await siteUpdateNote(selected.id, {
        title: title.trim() || 'Без названия',
        body,
        tag: tag.trim(),
      })
      setItems((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить')
    } finally {
      setBusy(false)
    }
  }

  async function handleUpload(file: File | null) {
    if (!selected || !file) {
      return
    }
    setBusy(true)
    try {
      await siteUploadNoteFile(selected.id, file)
      await refresh()
      setSelectedId(selected.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить файл')
    } finally {
      setBusy(false)
    }
  }

  if (!ready) {
    return <p className="learn-section-note">Загрузка заметок…</p>
  }

  return (
    <section className="tasks-notes" aria-labelledby="tasks-notes-title">
      <header className="tasks-panel-head">
        <h2 id="tasks-notes-title" className="learn-section-title">
          База знаний
        </h2>
        <p className="learn-section-note">
          Заметки в markdown и вложения (изображения, pdf, txt, md).
        </p>
      </header>

      <div className="tasks-notes-layout">
        <aside className="tasks-notes-list">
          <button
            type="button"
            className="learn-admin-btn learn-admin-btn-primary"
            disabled={busy}
            onClick={() => void handleCreate()}
          >
            Новая заметка
          </button>
          <ul>
            {items.map((note) => (
              <li key={note.id}>
                <button
                  type="button"
                  className={
                    note.id === selectedId
                      ? 'tasks-notes-item is-active'
                      : 'tasks-notes-item'
                  }
                  onClick={() => setSelectedId(note.id)}
                >
                  <strong>{note.title || 'Без названия'}</strong>
                  {note.tag ? <span>{note.tag}</span> : null}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <div className="tasks-notes-editor">
          {error ? <p className="tasks-personal-error">{error}</p> : null}
          {!selected ? (
            <p className="learn-section-note">Выберите или создайте заметку.</p>
          ) : (
            <form onSubmit={(event) => void handleSave(event)}>
              <label className="learn-admin-field">
                <span>Заголовок</span>
                <input
                  type="text"
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  maxLength={512}
                />
              </label>
              <label className="learn-admin-field">
                <span>Метка</span>
                <input
                  type="text"
                  value={tag}
                  onChange={(event) => setTag(event.target.value)}
                  maxLength={64}
                />
              </label>
              <MarkdownField
                label="Текст"
                value={body}
                onChange={setBody}
                rows={12}
                placeholder="Инструкции, ссылки, черновики…"
              />
              <div className="tasks-notes-files">
                <h3>Файлы</h3>
                <ul>
                  {(selected.files || []).map((file) => (
                    <li key={file.id}>
                      <button
                        type="button"
                        className="learn-admin-link"
                        onClick={() => {
                          void siteFetchNoteFileBlob(selected.id, file.id).then((blob) => {
                            const url = URL.createObjectURL(blob)
                            const a = document.createElement('a')
                            a.href = url
                            a.download = file.filename
                            a.click()
                            URL.revokeObjectURL(url)
                          })
                        }}
                      >
                        {file.filename}
                      </button>
                      <span className="learn-section-note">
                        {Math.round(file.sizeBytes / 1024)} КБ
                      </span>
                      <button
                        type="button"
                        className="learn-admin-link"
                        onClick={() => {
                          void siteDeleteNoteFile(selected.id, file.id).then(async () => {
                            await refresh()
                            setSelectedId(selected.id)
                          })
                        }}
                      >
                        Удалить
                      </button>
                    </li>
                  ))}
                </ul>
                <label className="learn-admin-field">
                  <span>Прикрепить файл</span>
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png,.webp,.gif,.pdf,.txt,.md"
                    disabled={busy}
                    onChange={(event) => {
                      const file = event.target.files?.[0] || null
                      event.target.value = ''
                      void handleUpload(file)
                    }}
                  />
                </label>
              </div>
              <div className="tasks-editor-actions">
                <button
                  type="submit"
                  className="learn-admin-btn learn-admin-btn-primary"
                  disabled={busy}
                >
                  Сохранить
                </button>
                <button
                  type="button"
                  className="learn-admin-link"
                  disabled={busy}
                  onClick={() => {
                    if (!window.confirm(`Удалить «${selected.title}»?`)) {
                      return
                    }
                    void siteDeleteNote(selected.id).then(async () => {
                      setSelectedId(null)
                      await refresh()
                    })
                  }}
                >
                  Удалить заметку
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </section>
  )
}
