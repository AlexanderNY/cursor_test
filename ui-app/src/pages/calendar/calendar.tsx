import { useEffect, useMemo, useState } from 'react'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import type { BestTimeSlot, PublishJob } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export function CalendarPage() {
  const { selectedBrand, selectedBrandId, brands } = useBrand()
  const [jobs, setJobs] = useState<PublishJob[]>([])
  const [slots, setSlots] = useState<BestTimeSlot[]>([])
  const [cursor, setCursor] = useState(() => {
    const d = new Date()
    return new Date(d.getFullYear(), d.getMonth(), 1)
  })
  const [error, setError] = useState('')
  const [draggingId, setDraggingId] = useState<number | null>(null)

  async function load() {
    setError('')
    try {
      const from = new Date(cursor.getFullYear(), cursor.getMonth(), 1).toISOString()
      const to = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 0, 23, 59, 59).toISOString()
      const list = await smmService.listJobs({
        brand_id: selectedBrandId ?? undefined,
        from,
        to,
      })
      setJobs(list)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  useEffect(() => {
    void load()
  }, [cursor, selectedBrandId])

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

  async function loadBestTimes() {
    try {
      const res = await smmService.bestTimes(selectedBrandId)
      setSlots(res.slots ?? [])
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function reschedule(jobId: number, day: number) {
    const pub = new Date(cursor.getFullYear(), cursor.getMonth(), day, 12, 0, 0)
    try {
      await smmService.updateJob(jobId, { publish_at: pub.toISOString(), status: 'scheduled' })
      await load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Calendar"
        description="Отложенный постинг по всем сетям бренда + ИИ лучшее время"
      />
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
        <Button onClick={() => void loadBestTimes()}>ИИ: лучшее время</Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-4">
        <Card className="lg:col-span-3">
          <CardContent className="p-4">
            <div className="grid grid-cols-7 gap-1 text-center text-xs text-[var(--text-muted)] mb-2">
              {WEEKDAYS.map((w) => (
                <div key={w}>{w}</div>
              ))}
            </div>
            <div className="grid grid-cols-7 gap-1">
              {daysInMonth.map((day, idx) => (
                <div
                  key={idx}
                  className="min-h-[88px] rounded-md border border-[var(--border-color)] p-1"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={() => {
                    if (draggingId != null && day != null) void reschedule(draggingId, day)
                    setDraggingId(null)
                  }}
                >
                  {day != null && (
                    <>
                      <div className="text-xs text-[var(--text-muted)] mb-1">{day}</div>
                      {jobsForDay(day).map((j) => (
                        <div
                          key={j.id}
                          draggable
                          onDragStart={() => setDraggingId(j.id)}
                          className="text-[10px] truncate rounded px-1 py-0.5 mb-0.5 text-white cursor-grab"
                          style={{ backgroundColor: brandColor(j.brand_id) }}
                          title={j.source_text}
                        >
                          {j.source_text.slice(0, 40)}
                        </div>
                      ))}
                    </>
                  )}
                </div>
              ))}
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
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
