import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { smmService } from '@/services/smm-service'
import type { JobComment, JobRevision, PublishJob } from '@/types/smm'
import { canPublish } from '@/types/smm'
import { useAuth } from '@/contexts/auth-context'
import { getErrorMessage } from '@/services/api-client'

interface JobCollabPanelProps {
  job: PublishJob
  onJobRestored?: (job: PublishJob) => void
}

export function JobCollabPanel({ job, onJobRestored }: JobCollabPanelProps) {
  const { user } = useAuth()
  const canEdit = canPublish(user?.role_in_group, user?.role)
  const [tab, setTab] = useState<'comments' | 'history'>('comments')
  const [comments, setComments] = useState<JobComment[]>([])
  const [revisions, setRevisions] = useState<JobRevision[]>([])
  const [body, setBody] = useState('')
  const [anchorStart, setAnchorStart] = useState('')
  const [anchorEnd, setAnchorEnd] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setError('')
    try {
      const [c, r] = await Promise.all([
        smmService.listJobComments(job.id),
        smmService.listJobRevisions(job.id),
      ])
      setComments(c)
      setRevisions(r)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }, [job.id])

  useEffect(() => {
    void load()
  }, [load])

  async function handleComment(e: FormEvent) {
    e.preventDefault()
    if (!body.trim()) return
    setBusy(true)
    setError('')
    try {
      const start = anchorStart.trim() === '' ? undefined : Number(anchorStart)
      const end = anchorEnd.trim() === '' ? undefined : Number(anchorEnd)
      const anchor =
        start != null && end != null && !Number.isNaN(start) && !Number.isNaN(end)
          ? { kind: 'text' as const, start, end }
          : undefined
      await smmService.addJobComment(job.id, { body: body.trim(), anchor })
      setBody('')
      setAnchorStart('')
      setAnchorEnd('')
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function handleResolve(commentId: number, resolved: boolean) {
    try {
      await smmService.resolveJobComment(job.id, commentId, resolved)
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function handleRestore(revisionId: number) {
    if (!canEdit) return
    setBusy(true)
    setError('')
    try {
      const restored = await smmService.restoreJobRevision(job.id, revisionId)
      onJobRestored?.(restored)
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] p-3 space-y-3">
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant={tab === 'comments' ? 'default' : 'ghost'}
          onClick={() => setTab('comments')}
        >
          Comments
        </Button>
        <Button
          size="sm"
          variant={tab === 'history' ? 'default' : 'ghost'}
          onClick={() => setTab('history')}
        >
          History
        </Button>
        <span className="text-xs text-[var(--text-muted)] ml-auto">Job #{job.id}</span>
      </div>
      {error && <Alert variant="error">{error}</Alert>}

      {tab === 'comments' && (
        <div className="space-y-3">
          <ul className="space-y-2 max-h-48 overflow-y-auto text-sm">
            {comments.length === 0 && (
              <li className="text-[var(--text-muted)]">No comments yet</li>
            )}
            {comments.map((c) => (
              <li
                key={c.id}
                className={`rounded border border-[var(--border-color)] p-2 ${
                  c.resolved_at ? 'opacity-60' : ''
                }`}
              >
                <p className="whitespace-pre-wrap">{c.body}</p>
                {c.anchor?.kind === 'text' && (
                  <p className="text-[10px] text-[var(--text-muted)] mt-1">
                    Anchor: chars {c.anchor.start}–{c.anchor.end}
                  </p>
                )}
                <div className="flex items-center gap-2 mt-1 text-[10px] text-[var(--text-muted)]">
                  <span>user {c.user_id}</span>
                  <span>{c.created_at ? new Date(c.created_at).toLocaleString() : ''}</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 px-1 text-[10px]"
                    onClick={() => void handleResolve(c.id, !c.resolved_at)}
                  >
                    {c.resolved_at ? 'Reopen' : 'Resolve'}
                  </Button>
                </div>
              </li>
            ))}
          </ul>
          <form onSubmit={handleComment} className="space-y-2">
            <textarea
              className="w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1.5 text-sm min-h-[64px]"
              placeholder="Comment on this draft…"
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
            <div className="flex flex-wrap gap-2 items-end">
              <input
                className="w-20 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1 text-xs"
                placeholder="start"
                value={anchorStart}
                onChange={(e) => setAnchorStart(e.target.value)}
                title="Optional text selection start"
              />
              <input
                className="w-20 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1 text-xs"
                placeholder="end"
                value={anchorEnd}
                onChange={(e) => setAnchorEnd(e.target.value)}
                title="Optional text selection end"
              />
              <Button type="submit" size="sm" disabled={busy || !body.trim()}>
                Add comment
              </Button>
            </div>
          </form>
        </div>
      )}

      {tab === 'history' && (
        <ul className="space-y-2 max-h-64 overflow-y-auto text-sm">
          {revisions.length === 0 && (
            <li className="text-[var(--text-muted)]">No revisions yet</li>
          )}
          {revisions.map((rev, idx) => {
            const prev = revisions[idx + 1]
            const before = (prev?.source_text || '').slice(0, 120)
            const after = (rev.source_text || '').slice(0, 120)
            return (
              <li
                key={rev.id}
                className="rounded border border-[var(--border-color)] p-2 space-y-1"
              >
                <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--text-muted)]">
                  <span>{rev.change_summary || 'update'}</span>
                  <span>·</span>
                  <span>{rev.status}</span>
                  <span>·</span>
                  <span>
                    {rev.created_at ? new Date(rev.created_at).toLocaleString() : ''}
                  </span>
                  {canEdit && (
                    <Button
                      size="sm"
                      variant="secondary"
                      className="h-6 ml-auto"
                      disabled={busy}
                      onClick={() => void handleRestore(rev.id)}
                    >
                      Restore
                    </Button>
                  )}
                </div>
                {prev && before !== after && (
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="rounded bg-red-500/10 p-1.5 text-[var(--text-muted)]">
                      <span className="font-medium text-red-400">Before</span>
                      <p className="mt-0.5 whitespace-pre-wrap line-clamp-3">{before || '—'}</p>
                    </div>
                    <div className="rounded bg-emerald-500/10 p-1.5 text-[var(--text-muted)]">
                      <span className="font-medium text-emerald-400">After</span>
                      <p className="mt-0.5 whitespace-pre-wrap line-clamp-3">{after || '—'}</p>
                    </div>
                  </div>
                )}
                {!prev && (
                  <p className="text-[11px] text-[var(--text-muted)] line-clamp-2">
                    {(rev.source_text || '').slice(0, 160)}
                  </p>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
