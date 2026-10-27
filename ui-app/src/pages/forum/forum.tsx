import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  Alert,
  Button,
  Card,
  CardContent,
  EmptyState,
  Input,
  PageContainer,
  PageHeader,
} from '@/components/ui'
import { useAuth } from '@/contexts/auth-context'
import { useToast } from '@/contexts/toast-context'
import { getErrorMessage } from '@/services/api-client'
import { forumService } from '@/services/forum-service'
import type { ForumKind, ForumListResponse, ForumScope, ForumThreadDetail } from '@/types/core'
import { FORUM_KIND_LABELS } from '@/types/core'
import { avatarPublicSrc } from '@/utils/avatar'
import { formatDateTime } from '@/utils/date'

const KINDS: ForumKind[] = ['discussion', 'bug_report', 'suggestion', 'contact_author']
const POLL_MS = 20000

function excerpt(text: string, max = 140): string {
  const flat = text.replace(/\s+/g, ' ').trim()
  if (flat.length <= max) return flat
  return `${flat.slice(0, max - 1)}…`
}

function AuthorFace({
  name,
  avatar,
  className = 'h-7 w-7 text-[10px]',
}: {
  name: string
  avatar?: string | null
  className?: string
}) {
  const src = avatarPublicSrc(avatar)
  const initial = (name || '?').slice(0, 1).toUpperCase()
  if (src) {
    return (
      <img
        src={src}
        alt=""
        className={`${className} rounded-full object-cover shrink-0 bg-[var(--bg-tertiary)]`}
      />
    )
  }
  return (
    <span
      className={`${className} rounded-full shrink-0 inline-flex items-center justify-center bg-gradient-to-br from-primary-500 to-accent-500 font-semibold text-white`}
      aria-hidden
    >
      {initial}
    </span>
  )
}

function parseKind(raw: string | null): ForumKind | '' {
  if (raw && KINDS.includes(raw as ForumKind)) return raw as ForumKind
  return ''
}

export function ForumPage() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const [searchParams, setSearchParams] = useSearchParams()
  const hasTeam = Boolean(user?.group_id || user?.role_in_group)
  const workspaceKey = user?.active_group_id ?? user?.group_id ?? null

  const scopeParam = searchParams.get('scope')
  const scope: ForumScope =
    scopeParam === 'workspace' || scopeParam === 'platform'
      ? scopeParam
      : hasTeam
        ? 'workspace'
        : 'platform'
  const kind = parseKind(searchParams.get('kind'))
  const threadParam = searchParams.get('thread')
  const threadId = threadParam && /^\d+$/.test(threadParam) ? Number(threadParam) : null

  const [list, setList] = useState<ForumListResponse | null>(null)
  const [thread, setThread] = useState<ForumThreadDetail | null>(null)
  const [listError, setListError] = useState('')
  const [threadError, setThreadError] = useState('')
  const [isLoadingList, setIsLoadingList] = useState(true)
  const [isLoadingThread, setIsLoadingThread] = useState(false)
  const [showComposer, setShowComposer] = useState(false)
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [createKind, setCreateKind] = useState<ForumKind>(kind || 'discussion')
  const [isCreating, setIsCreating] = useState(false)
  const [reply, setReply] = useState('')
  const [isReplying, setIsReplying] = useState(false)
  const [isVoting, setIsVoting] = useState(false)
  const [busyId, setBusyId] = useState<number | null>(null)

  const patchParams = useCallback(
    (next: Record<string, string | null>) => {
      const params = new URLSearchParams(searchParams)
      for (const [key, value] of Object.entries(next)) {
        if (value == null || value === '') params.delete(key)
        else params.set(key, value)
      }
      setSearchParams(params, { replace: true })
    },
    [searchParams, setSearchParams],
  )

  const loadList = useCallback(
    async (silent: boolean) => {
      if (!silent) {
        setIsLoadingList(true)
        setListError('')
      }
      try {
        const response = await forumService.listThreads({
          scope,
          ...(kind ? { kind } : {}),
        })
        setList(response)
      } catch (err) {
        if (!silent) setListError(getErrorMessage(err))
      } finally {
        if (!silent) setIsLoadingList(false)
      }
    },
    [scope, kind],
  )

  const loadThread = useCallback(
    async (id: number, silent: boolean) => {
      if (!silent) {
        setIsLoadingThread(true)
        setThreadError('')
      }
      try {
        const detail = await forumService.getThread(id)
        if (detail.scope !== scope) {
          setThread(null)
          setThreadError('Эта ветка из другой области')
          return
        }
        setThread(detail)
        setThreadError('')
      } catch (err) {
        if (!silent) {
          setThread(null)
          setThreadError(getErrorMessage(err))
        }
      } finally {
        if (!silent) setIsLoadingThread(false)
      }
    },
    [scope],
  )

  useEffect(() => {
    void loadList(false)
  }, [loadList, workspaceKey])

  useEffect(() => {
    if (threadId == null) {
      setThread(null)
      setThreadError('')
      return
    }
    void loadThread(threadId, false)
  }, [threadId, loadThread])

  useEffect(() => {
    setCreateKind(kind || 'discussion')
  }, [kind])

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (document.visibilityState !== 'visible') return
      void loadList(true)
      if (threadId != null) void loadThread(threadId, true)
    }, POLL_MS)
    return () => window.clearInterval(timer)
  }, [loadList, loadThread, threadId])

  function selectScope(next: ForumScope) {
    patchParams({ scope: next, thread: null })
    setShowComposer(false)
  }

  function selectKind(next: ForumKind | '') {
    patchParams({ kind: next || null })
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    const trimmedTitle = title.trim()
    const trimmedBody = body.trim()
    if (!trimmedTitle || !trimmedBody) {
      addToast('Введите название и текст', 'error')
      return
    }
    setIsCreating(true)
    try {
      const created = await forumService.createThread({
        scope,
        kind: createKind,
        title: trimmedTitle,
        body: trimmedBody,
      })
      setTitle('')
      setBody('')
      setShowComposer(false)
      patchParams({
        scope,
        kind: createKind,
        thread: String(created.id),
      })
      addToast('Ветка открыта', 'success')
    } catch (err) {
      addToast(getErrorMessage(err), 'error')
    } finally {
      setIsCreating(false)
    }
  }

  async function handleReply(event: FormEvent) {
    event.preventDefault()
    if (threadId == null) return
    const trimmed = reply.trim()
    if (!trimmed) {
      addToast('Введите сообщение', 'error')
      return
    }
    setIsReplying(true)
    try {
      await forumService.addPost(threadId, trimmed)
      setReply('')
      await loadThread(threadId, true)
      await loadList(true)
    } catch (err) {
      addToast(getErrorMessage(err), 'error')
    } finally {
      setIsReplying(false)
    }
  }

  async function handleVote() {
    if (thread == null) return
    setIsVoting(true)
    try {
      const result = await forumService.toggleVote(thread.id)
      setThread((prev) =>
        prev && prev.id === thread.id
          ? { ...prev, voted: result.voted, vote_count: result.vote_count }
          : prev,
      )
      setList((prev) =>
        prev
          ? {
              ...prev,
              threads: prev.threads.map((item) =>
                item.id === thread.id
                  ? { ...item, voted: result.voted, vote_count: result.vote_count }
                  : item,
              ),
            }
          : prev,
      )
      await loadList(true)
    } catch (err) {
      addToast(getErrorMessage(err), 'error')
    } finally {
      setIsVoting(false)
    }
  }

  async function handleClose() {
    if (thread == null) return
    setBusyId(thread.id)
    try {
      const updated = await forumService.setClosed(thread.id, !thread.is_closed)
      setThread(updated)
      await loadList(true)
    } catch (err) {
      addToast(getErrorMessage(err), 'error')
    } finally {
      setBusyId(null)
    }
  }

  async function handleDeleteThread() {
    if (thread == null) return
    if (!window.confirm(`Удалить ветку «${thread.title}» вместе с ответами?`)) return
    setBusyId(thread.id)
    try {
      await forumService.deleteThread(thread.id)
      setThread(null)
      patchParams({ thread: null })
      await loadList(true)
      addToast('Ветка удалена', 'success')
    } catch (err) {
      addToast(getErrorMessage(err), 'error')
    } finally {
      setBusyId(null)
    }
  }

  async function handleDeletePost(postId: number) {
    if (threadId == null) return
    if (!window.confirm('Удалить это сообщение?')) return
    setBusyId(postId)
    try {
      await forumService.deletePost(postId)
      await loadThread(threadId, true)
      await loadList(true)
    } catch (err) {
      addToast(getErrorMessage(err), 'error')
    } finally {
      setBusyId(null)
    }
  }

  const threads = list?.threads ?? []
  const noWorkspace = scope === 'workspace' && list != null && list.group_id == null
  const description =
    scope === 'workspace'
      ? list?.group_name
        ? `Беседа команды «${list.group_name}». Её видят только участники Workspace.`
        : 'Беседа внутри Workspace. Её видят только участники команды.'
      : kind === 'suggestion'
        ? 'Общие идеи платформы. Голос поднимает ветку в списке.'
        : 'Общие ветки: ошибки, идеи и вопросы автору. Их видят все пользователи.'

  return (
    <PageContainer maxWidth="wide">
      <PageHeader title="Беседы" description={description} />

      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Область бесед">
        <Button
          type="button"
          size="sm"
          variant={scope === 'workspace' ? 'primary' : 'secondary'}
          onClick={() => selectScope('workspace')}
          aria-pressed={scope === 'workspace'}
        >
          Команда
        </Button>
        <Button
          type="button"
          size="sm"
          variant={scope === 'platform' ? 'primary' : 'secondary'}
          onClick={() => selectScope('platform')}
          aria-pressed={scope === 'platform'}
        >
          Платформа
        </Button>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          variant={kind === '' ? 'primary' : 'ghost'}
          onClick={() => selectKind('')}
        >
          Все
        </Button>
        {KINDS.map((item) => (
          <Button
            key={item}
            type="button"
            size="sm"
            variant={kind === item ? 'primary' : 'ghost'}
            onClick={() => selectKind(item)}
          >
            {FORUM_KIND_LABELS[item]}
          </Button>
        ))}
      </div>

      {listError && <Alert variant="error">{listError}</Alert>}

      <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
        <Card className={threadId != null ? 'hidden lg:flex lg:flex-col' : ''}>
          <CardContent className="space-y-3 pt-5">
            {!noWorkspace && (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="w-full"
                onClick={() => setShowComposer((open) => !open)}
              >
                {showComposer ? 'Скрыть форму' : 'Новая ветка'}
              </Button>
            )}

            {showComposer && !noWorkspace && (
              <form onSubmit={handleCreate} className="space-y-3">
                <label className="block text-sm font-medium text-[var(--text-secondary)]" htmlFor="forum-kind">
                  Тип
                </label>
                <select
                  id="forum-kind"
                  value={createKind}
                  onChange={(event) => setCreateKind(event.target.value as ForumKind)}
                  className="w-full rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                >
                  {KINDS.map((item) => (
                    <option key={item} value={item}>
                      {FORUM_KIND_LABELS[item]}
                    </option>
                  ))}
                </select>
                <Input
                  label="Название"
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  maxLength={255}
                />
                <label className="block text-sm font-medium text-[var(--text-secondary)]" htmlFor="forum-body">
                  Сообщение
                </label>
                <textarea
                  id="forum-body"
                  value={body}
                  onChange={(event) => setBody(event.target.value)}
                  rows={5}
                  maxLength={8000}
                  className="w-full rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                />
                <Button type="submit" size="sm" isLoading={isCreating}>
                  Открыть
                </Button>
              </form>
            )}

            {isLoadingList && <p className="text-sm text-[var(--text-muted)]">Загрузка…</p>}

            {noWorkspace && (
              <EmptyState
                title="Нет Workspace"
                description="Создайте команду, чтобы вести беседу внутри неё. Общие ветки доступны на платформе."
                action={
                  <Link to="/team" className="text-sm text-primary-400 hover:underline">
                    Открыть Workspace
                  </Link>
                }
              />
            )}

            {!isLoadingList && !noWorkspace && threads.length === 0 && (
              <EmptyState
                title="Пока пусто"
                description="Откройте первую ветку — её увидят участники этой области."
              />
            )}

            <ul className="space-y-2">
              {threads.map((item) => {
                const selected = item.id === threadId
                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => patchParams({ scope, thread: String(item.id) })}
                      className={`w-full rounded-xl border px-3 py-2 text-left transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 ${
                        selected
                          ? 'border-primary-500/60 bg-primary-500/10'
                          : 'border-[var(--border-color)] hover:border-primary-500/40'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs text-[var(--text-muted)]">
                          {FORUM_KIND_LABELS[item.kind]}
                          {item.is_closed ? ' · закрыта' : ''}
                        </span>
                        {item.kind === 'suggestion' && (
                          <span className="text-xs text-[var(--text-secondary)]">▲ {item.vote_count}</span>
                        )}
                      </div>
                      <p className="mt-1 text-sm font-medium text-[var(--text-primary)] line-clamp-2">
                        {item.title}
                      </p>
                      <p className="mt-1 text-xs text-[var(--text-muted)] line-clamp-2">{excerpt(item.body)}</p>
                      <p className="mt-1 flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
                        <AuthorFace name={item.author_name} avatar={item.author_avatar} className="h-4 w-4 text-[8px]" />
                        <span>
                          {item.author_name} · {item.reply_count} отв.
                        </span>
                      </p>
                    </button>
                  </li>
                )
              })}
            </ul>
          </CardContent>
        </Card>

        <Card className={threadId == null ? 'hidden lg:block' : ''}>
          <CardContent className="space-y-4 pt-5">
            {threadId != null && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="lg:hidden"
                onClick={() => patchParams({ thread: null })}
              >
                К списку
              </Button>
            )}

            {threadError && <Alert variant="error">{threadError}</Alert>}
            {isLoadingThread && <p className="text-sm text-[var(--text-muted)]">Загрузка ветки…</p>}

            {thread == null && !isLoadingThread && !threadError && (
              <EmptyState
                title="Выберите ветку"
                description="Слева список бесед. Новая ветка останется в выбранной области: команда или платформа."
              />
            )}

            {thread != null && (
              <>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex min-w-0 items-start gap-3">
                    <AuthorFace name={thread.author_name} avatar={thread.author_avatar} className="h-9 w-9 text-sm" />
                    <div className="min-w-0">
                      <p className="text-xs text-[var(--text-muted)]">
                        {FORUM_KIND_LABELS[thread.kind]}
                        {thread.is_closed ? ' · закрыта' : ''} · {formatDateTime(thread.created_at)}
                      </p>
                      <h2 className="mt-1 text-xl font-semibold text-[var(--text-primary)]">{thread.title}</h2>
                      <p className="text-sm text-[var(--text-secondary)]">{thread.author_name}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {thread.can_vote && (
                      <Button
                        type="button"
                        size="sm"
                        variant={thread.voted ? 'primary' : 'secondary'}
                        isLoading={isVoting}
                        onClick={() => void handleVote()}
                      >
                        {thread.voted ? 'Голос есть' : 'Голосовать'} · {thread.vote_count}
                      </Button>
                    )}
                    {!thread.can_vote && thread.kind === 'suggestion' && (
                      <span className="text-sm text-[var(--text-muted)] self-center">▲ {thread.vote_count}</span>
                    )}
                    {thread.can_close && (
                      <Button type="button" size="sm" variant="secondary" onClick={() => void handleClose()}>
                        {thread.is_closed ? 'Открыть' : 'Закрыть'}
                      </Button>
                    )}
                    {thread.can_delete && (
                      <Button type="button" size="sm" variant="danger" onClick={() => void handleDeleteThread()}>
                        Удалить
                      </Button>
                    )}
                  </div>
                </div>

                <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] px-3 py-3">
                  <p className="whitespace-pre-wrap text-sm text-[var(--text-primary)]">{thread.body}</p>
                </div>

                <div className="space-y-3 max-h-[50vh] overflow-y-auto pr-1">
                  {thread.posts.map((post) => (
                    <div
                      key={post.id}
                      className="flex gap-2 rounded-xl border border-[var(--border-color)] px-3 py-2"
                    >
                      <AuthorFace name={post.author_name} avatar={post.author_avatar} />
                      <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-xs text-[var(--text-muted)]">
                          {post.author_name} · {formatDateTime(post.created_at)}
                        </p>
                        {post.can_delete && (
                          <Button
                            type="button"
                            size="sm"
                            variant="ghost"
                            onClick={() => void handleDeletePost(post.id)}
                            isLoading={busyId === post.id}
                          >
                            Удалить
                          </Button>
                        )}
                      </div>
                      <p className="mt-1 whitespace-pre-wrap text-sm text-[var(--text-primary)]">{post.body}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {thread.can_reply ? (
                  <form onSubmit={handleReply} className="space-y-2">
                    <label className="block text-sm font-medium text-[var(--text-secondary)]" htmlFor="forum-reply">
                      Ответ
                    </label>
                    <textarea
                      id="forum-reply"
                      value={reply}
                      onChange={(event) => setReply(event.target.value)}
                      rows={3}
                      maxLength={8000}
                      placeholder="Напишите ответ. Ctrl+Enter отправит."
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
                          event.preventDefault()
                          event.currentTarget.form?.requestSubmit()
                        }
                      }}
                      className="w-full rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                    />
                    <Button type="submit" size="sm" isLoading={isReplying}>
                      Отправить
                    </Button>
                  </form>
                ) : (
                  <p className="text-sm text-[var(--text-muted)]">Ветка закрыта, новые ответы не принимаются.</p>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
