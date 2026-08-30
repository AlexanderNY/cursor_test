import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { LearnModeBanner } from '@/components/smm/learn-mode-banner'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import type { BestTimeSlot, PublishJob } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

const STATUS_FILTERS = [
  { value: '', label: 'All statuses' },
  { value: 'draft', label: 'Draft' },
  { value: 'pending_approval', label: 'Pending approval' },
  { value: 'ready', label: 'Ready' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'published', label: 'Published' },
  { value: 'failed', label: 'Failed' },
  { value: 'rejected', label: 'Rejected' },
] as const

function toDatetimeLocal(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function CalendarPage() {
  const { selectedBrand, selectedBrandId, brands, ownChannels, setSelectedBrandId } = useBrand()
  const [searchParams, setSearchParams] = useSearchParams()
  const [jobs, setJobs] = useState<PublishJob[]>([])
  const [slots, setSlots] = useState<BestTimeSlot[]>([])
  const [planFeatures, setPlanFeatures] = useState<Record<string, boolean>>({})
  const [horizonDays, setHorizonDays] = useState(7)
  const [cursor, setCursor] = useState(() => {
    const d = new Date()
    return new Date(d.getFullYear(), d.getMonth(), 1)
  })
  const [error, setError] = useState('')
  const [draggingId, setDraggingId] = useState<number | null>(null)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [rejectComment, setRejectComment] = useState('')
  const [rejectingId, setRejectingId] = useState<number | null>(null)
  const [assignId, setAssignId] = useState<number | null>(null)
  const [assignUserId, setAssignUserId] = useState('')
  const [mineOnly, setMineOnly] = useState(false)
  const [bulkPublishAt, setBulkPublishAt] = useState('')
  const [learnMode, setLearnMode] = useState(false)

  const statusFilter = searchParams.get('status') || ''
  const channelFilter = searchParams.get('channel')
    ? Number(searchParams.get('channel'))
    : undefined
  const networkFilter = searchParams.get('network') || undefined
  const brandFromUrl = searchParams.get('brand')
    ? Number(searchParams.get('brand'))
    : undefined

  useEffect(() => {
    if (brandFromUrl && brandFromUrl !== selectedBrandId) {
      setSelectedBrandId(brandFromUrl)
    }
  }, [brandFromUrl, selectedBrandId, setSelectedBrandId])

  useEffect(() => {
    void smmService
      .onboardingState()
      .then((s) => setLearnMode(Boolean(s.learn_mode)))
      .catch(() => setLearnMode(false))
  }, [selectedBrandId])

  const brandChannels = useMemo(
    () => ownChannels.filter((c) => !selectedBrandId || c.brand_id === selectedBrandId),
    [ownChannels, selectedBrandId],
  )

  async function load() {
    setError('')
    try {
      const from = new Date(cursor.getFullYear(), cursor.getMonth(), 1).toISOString()
      const to = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 0, 23, 59, 59).toISOString()
      const [list, plan] = await Promise.all([
        smmService.listJobs({
          brand_id: selectedBrandId ?? undefined,
          from,
          to,
          status: statusFilter || undefined,
          channel_id: channelFilter,
          network: networkFilter,
          assigned_to_me: mineOnly || undefined,
        }),
        smmService.getPlan().catch(() => null),
      ])
      setJobs(list)
      if (plan?.limits?.features) setPlanFeatures(plan.limits.features as Record<string, boolean>)
      if (plan?.limits?.schedule_horizon_days != null) {
        setHorizonDays(Number(plan.limits.schedule_horizon_days))
      }
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  useEffect(() => {
    void load()
  }, [cursor, selectedBrandId, statusFilter, channelFilter, networkFilter, mineOnly])

  const pendingApproval = useMemo(
    () => jobs.filter((j) => j.status === 'pending_approval'),
    [jobs],
  )

  const assignedToMe = useMemo(
    () => pendingApproval.filter((j) => j.assigned_to != null),
    [pendingApproval],
  )

  const daysInMonth = useMemo(() => {
    const y = cursor.getFullYear()
    const m = cursor.getMonth()
    const count = new Date(y, m + 1, 0).getDate()
    const startDow = new Date(y, m, 1).getDay()
    const cells: (number | null)[] = []
    for (let i = 0; i < startDow; i++) cells.push(null)
    for (let d = 1; d <= count; d++) cells.push(d)
    return cells
  }, [cursor])

  const maxScheduleDate = useMemo(() => {
    const d = new Date()
    d.setDate(d.getDate() + horizonDays)
    return d
  }, [horizonDays])

  function jobsForDay(day: number): PublishJob[] {
    return jobs.filter((j) => {
      const iso = j.publish_at || j.created_at
      if (!iso) return false
      const d = new Date(iso)
      return (
        d.getFullYear() === cursor.getFullYear() &&
        d.getMonth() === cursor.getMonth() &&
        d.getDate() === day
      )
    })
  }

  function brandColor(brandId?: number | null) {
    return brands.find((b) => b.id === brandId)?.color ?? selectedBrand?.color ?? '#3B82F6'
  }

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(searchParams)
    if (!value) next.delete(key)
    else next.set(key, value)
    setSearchParams(next, { replace: true })
  }

  function toggleSelect(id: number) {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  async function loadBestTimes() {
    if (!planFeatures.best_times) {
      setError('Best times requires Standard or Full — see Pricing')
      return
    }
    try {
      const res = await smmService.bestTimes(selectedBrandId, channelFilter ?? null)
      setSlots(res.slots ?? [])
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function reschedule(jobId: number, day: number) {
    const pub = new Date(cursor.getFullYear(), cursor.getMonth(), day, 12, 0, 0)
    if (pub > maxScheduleDate) {
      setError(`Slot outside plan horizon (${horizonDays} days). Upgrade or pick an earlier date.`)
      return
    }
    try {
      await smmService.updateJob(jobId, { publish_at: pub.toISOString(), status: 'scheduled' })
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function approve(jobId: number) {
    try {
      await smmService.approveJob(jobId)
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function reject(jobId: number) {
    try {
      await smmService.rejectJob(jobId, rejectComment || undefined)
      setRejectingId(null)
      setRejectComment('')
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function assign(jobId: number) {
    const uid = assignUserId.trim() ? Number(assignUserId) : null
    if (assignUserId.trim() && Number.isNaN(uid)) {
      setError('assigned_to must be a user id')
      return
    }
    try {
      await smmService.assignJob(jobId, uid)
      setAssignId(null)
      setAssignUserId('')
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function bulkApprove() {
    if (!selectedIds.length) return
    try {
      await smmService.bulkApproveJobs(selectedIds)
      setSelectedIds([])
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function bulkReschedule() {
    if (!selectedIds.length || !bulkPublishAt) return
    const pub = new Date(bulkPublishAt)
    if (Number.isNaN(pub.getTime())) {
      setError('Invalid bulk schedule datetime')
      return
    }
    if (pub > maxScheduleDate) {
      setError(`Bulk slot outside plan horizon (${horizonDays} days)`)
      return
    }
    try {
      await smmService.bulkRescheduleJobs(selectedIds, pub.toISOString())
      setSelectedIds([])
      setBulkPublishAt('')
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const statusBadge = (status: string) => {
    if (status === 'pending_approval') return '⏳ '
    if (status === 'rejected') return '✕ '
    if (status === 'failed') return '! '
    if (status === 'published') return '✓ '
    return ''
  }

  return (
    <PageContainer>
      <PageHeader
        title="Calendar"
        description="Единый календарь SMM jobs: approve → слот → публикация"
      />
      <LearnModeBanner visible={learnMode} />
      {error && <Alert variant="error">{error}</Alert>}

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <Button
          variant="secondary"
          onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() - 1, 1))}
        >
          Prev
        </Button>
        <span className="font-medium min-w-[160px] text-center">
          {cursor.toLocaleString(undefined, { month: 'long', year: 'numeric' })}
        </span>
        <Button
          variant="secondary"
          onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1))}
        >
          Next
        </Button>
        <select
          className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1.5 text-sm"
          value={statusFilter}
          onChange={(e) => setFilter('status', e.target.value)}
        >
          {STATUS_FILTERS.map((s) => (
            <option key={s.value || 'all'} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
        <select
          className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1.5 text-sm"
          value={channelFilter ?? ''}
          onChange={(e) => setFilter('channel', e.target.value)}
        >
          <option value="">All channels</option>
          {brandChannels.map((c) => (
            <option key={c.id} value={c.id}>
              {c.network.toUpperCase()} · {c.title || c.external_id}
            </option>
          ))}
        </select>
        <select
          className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1.5 text-sm"
          value={networkFilter ?? ''}
          onChange={(e) => setFilter('network', e.target.value)}
        >
          <option value="">All networks</option>
          <option value="tg">Telegram</option>
          <option value="vk">VK</option>
        </select>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={mineOnly}
            onChange={(e) => setMineOnly(e.target.checked)}
          />
          На мне
          {assignedToMe.length > 0 && (
            <span className="rounded-full bg-amber-500/20 text-amber-600 px-1.5 text-xs">
              {assignedToMe.length}
            </span>
          )}
        </label>
        <Button
          onClick={() => void loadBestTimes()}
          disabled={!planFeatures.best_times}
          title={!planFeatures.best_times ? 'Upgrade to Standard+' : undefined}
        >
          ИИ: лучшее время
        </Button>
        {!planFeatures.best_times && (
          <Link to="/pricing" className="text-sm text-primary-400 hover:underline">
            Upgrade
          </Link>
        )}
        <span className="text-xs text-[var(--text-muted)]">
          Horizon: {horizonDays}d (until {maxScheduleDate.toLocaleDateString()})
        </span>
      </div>

      {selectedIds.length > 0 && planFeatures.approval_workflow && (
        <Card className="mb-4">
          <CardContent className="flex flex-wrap items-center gap-2 py-3">
            <span className="text-sm">{selectedIds.length} selected</span>
            <Button size="sm" onClick={() => void bulkApprove()}>
              Bulk approve
            </Button>
            <input
              type="datetime-local"
              value={bulkPublishAt}
              max={toDatetimeLocal(maxScheduleDate)}
              onChange={(e) => setBulkPublishAt(e.target.value)}
              className="px-2 py-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] text-sm"
            />
            <Button size="sm" variant="secondary" onClick={() => void bulkReschedule()}>
              Bulk reschedule
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setSelectedIds([])}>
              Clear
            </Button>
          </CardContent>
        </Card>
      )}

      {pendingApproval.length > 0 && planFeatures.approval_workflow && (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle className="text-base">
              {mineOnly ? 'На мне' : 'Pending approval'} ({pendingApproval.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {pendingApproval.map((j) => (
              <div
                key={j.id}
                className="flex flex-wrap items-center justify-between gap-2 text-sm border-b border-[var(--border-color)] py-2"
              >
                <label className="flex items-center gap-2 min-w-0 flex-1">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(j.id)}
                    onChange={() => toggleSelect(j.id)}
                  />
                  <span className="truncate">{j.source_text.slice(0, 80)}</span>
                  {j.assigned_to != null && (
                    <span className="text-xs text-[var(--text-muted)] shrink-0">
                      → user {j.assigned_to}
                    </span>
                  )}
                </label>
                <div className="flex flex-wrap gap-1">
                  <Button size="sm" onClick={() => void approve(j.id)}>
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => {
                      setRejectingId(j.id)
                      setRejectComment('')
                    }}
                  >
                    Reject
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setAssignId(j.id)
                      setAssignUserId(j.assigned_to != null ? String(j.assigned_to) : '')
                    }}
                  >
                    Assign
                  </Button>
                </div>
                {rejectingId === j.id && (
                  <div className="w-full flex flex-wrap gap-2 mt-1">
                    <input
                      className="flex-1 px-2 py-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] text-sm"
                      placeholder="Rejection comment"
                      value={rejectComment}
                      onChange={(e) => setRejectComment(e.target.value)}
                    />
                    <Button size="sm" onClick={() => void reject(j.id)}>
                      Confirm reject
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setRejectingId(null)}>
                      Cancel
                    </Button>
                  </div>
                )}
                {assignId === j.id && (
                  <div className="w-full flex flex-wrap gap-2 mt-1">
                    <input
                      className="w-40 px-2 py-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] text-sm"
                      placeholder="Reviewer user id"
                      value={assignUserId}
                      onChange={(e) => setAssignUserId(e.target.value)}
                    />
                    <Button size="sm" onClick={() => void assign(j.id)}>
                      Save
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setAssignId(null)}>
                      Cancel
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-4">
        <Card className="lg:col-span-3">
          <CardContent className="p-4">
            <div className="grid grid-cols-7 gap-1 text-center text-xs text-[var(--text-muted)] mb-2">
              {WEEKDAYS.map((w) => (
                <div key={w}>{w}</div>
              ))}
            </div>
            <div className="grid grid-cols-7 gap-1">
              {daysInMonth.map((day, idx) => {
                const dayDate =
                  day != null
                    ? new Date(cursor.getFullYear(), cursor.getMonth(), day, 12)
                    : null
                const isBeyondHorizon = dayDate != null && dayDate > maxScheduleDate
                return (
                  <div
                    key={idx}
                    className={`min-h-[88px] rounded-md border border-[var(--border-color)] p-1 ${
                      isBeyondHorizon ? 'opacity-40 bg-[var(--bg-secondary)]' : ''
                    }`}
                    title={
                      isBeyondHorizon
                        ? `Outside schedule horizon (${horizonDays} days)`
                        : undefined
                    }
                    onDragOver={(e) => {
                      if (!isBeyondHorizon) e.preventDefault()
                    }}
                    onDrop={() => {
                      if (draggingId != null && day != null && !isBeyondHorizon) {
                        void reschedule(draggingId, day)
                      }
                      setDraggingId(null)
                    }}
                  >
                    {day != null && (
                      <>
                        <div className="text-xs text-[var(--text-muted)] mb-1">{day}</div>
                        {jobsForDay(day).map((j) => (
                          <div
                            key={j.id}
                            draggable={!isBeyondHorizon}
                            onDragStart={() => setDraggingId(j.id)}
                            className="text-[10px] truncate rounded px-1 py-0.5 mb-0.5 text-white cursor-grab"
                            style={{ backgroundColor: brandColor(j.brand_id) }}
                            title={`${j.status}: ${j.source_text}`}
                          >
                            {statusBadge(j.status)}
                            {j.source_text.slice(0, 40)}
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Best times</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {slots.length === 0 && (
              <p className="text-[var(--text-muted)]">Нажмите «ИИ: лучшее время»</p>
            )}
            {slots.map((s, i) => (
              <div key={i} className="flex justify-between border-b border-[var(--border-color)] py-1">
                <span>
                  {WEEKDAYS[s.weekday]} {String(s.hour).padStart(2, '0')}:00
                </span>
                <span className="text-[var(--text-muted)]">{s.score}</span>
              </div>
            ))}
            <p className="text-xs text-[var(--text-muted)] pt-2">
              TG/VK week calendars deep-link here — SMM jobs are the source of truth.
            </p>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
