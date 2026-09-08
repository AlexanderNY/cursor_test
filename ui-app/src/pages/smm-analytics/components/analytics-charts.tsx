import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type {
  AnalyticsCohort,
  AnalyticsFunnel,
  AnalyticsTrendPoint,
  BestTimeSlot,
} from '@/types/smm'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

const CHART_STROKE = 'var(--color-primary, #3b82f6)'
const CHART_MUTED = 'var(--text-muted, #94a3b8)'

export function TrendsChart({ points }: { points: AnalyticsTrendPoint[] }) {
  if (!points.length) {
    return <p className="text-sm text-[var(--text-muted)] py-6 text-center">Нет snapshot-трендов за период</p>
  }
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis dataKey="date" tick={{ fill: CHART_MUTED, fontSize: 11 }} />
          <YAxis tick={{ fill: CHART_MUTED, fontSize: 11 }} />
          <Tooltip />
          <Area type="monotone" dataKey="views" name="Views" stroke={CHART_STROKE} fill={CHART_STROKE} fillOpacity={0.15} />
          <Area type="monotone" dataKey="er" name="ER %" stroke="#22c55e" fill="#22c55e" fillOpacity={0.08} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function GrowthChart({ points }: { points: { date: string; subscribers: number }[] }) {
  if (!points.length) {
    return <p className="text-sm text-[var(--text-muted)] py-6 text-center">Нет снимков подписчиков</p>
  }
  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis dataKey="date" tick={{ fill: CHART_MUTED, fontSize: 11 }} />
          <YAxis tick={{ fill: CHART_MUTED, fontSize: 11 }} />
          <Tooltip />
          <Line type="monotone" dataKey="subscribers" name="Подписчики" stroke={CHART_STROKE} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function FunnelChart({ funnel }: { funnel: AnalyticsFunnel | null }) {
  const steps = (funnel?.steps || []).filter((s) => s.value != null)
  if (!steps.length) {
    return <p className="text-sm text-[var(--text-muted)] py-6 text-center">Воронка пока пуста</p>
  }
  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={steps} layout="vertical" margin={{ left: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis type="number" tick={{ fill: CHART_MUTED, fontSize: 11 }} />
          <YAxis type="category" dataKey="label" width={110} tick={{ fill: CHART_MUTED, fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="value" name="Значение" fill={CHART_STROKE} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function CohortBars({ cohort }: { cohort: AnalyticsCohort | null }) {
  if (!cohort || cohort.sample_size === 0) {
    return <p className="text-sm text-[var(--text-muted)] py-6 text-center">Недостаточно snapshots для cohort</p>
  }
  const data = [
    { label: '+1ч', value: cohort.retention['1h'] },
    { label: '+24ч', value: cohort.retention['24h'] },
    { label: '+7д', value: cohort.retention['7d'] },
  ]
  return (
    <div className="space-y-3">
      <p className="text-xs text-[var(--text-muted)]">Выборка: {cohort.sample_size} постов · % от финальных views</p>
      {data.map((row) => (
        <div key={row.label}>
          <div className="flex justify-between text-sm mb-1">
            <span>{row.label}</span>
            <span>{row.value}%</span>
          </div>
          <div className="h-2 rounded bg-[var(--bg-tertiary)] overflow-hidden">
            <div className="h-full bg-primary-500" style={{ width: `${Math.min(100, Math.max(0, row.value))}%` }} />
          </div>
        </div>
      ))}
    </div>
  )
}

export function CommentsVolumeChart({ points }: { points: { date: string; count: number }[] }) {
  if (!points.length) {
    return <p className="text-sm text-[var(--text-muted)] py-4 text-center">Нет комментариев за период</p>
  }
  return (
    <div className="h-40 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={points}>
          <XAxis dataKey="date" hide />
          <YAxis tick={{ fill: CHART_MUTED, fontSize: 10 }} width={28} />
          <Tooltip />
          <Bar dataKey="count" name="Комментарии" fill={CHART_STROKE} radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function BestTimesHeatmap({ slots }: { slots: BestTimeSlot[] }) {
  if (!slots.length) {
    return <p className="text-sm text-[var(--text-muted)] py-4 text-center">Нет данных best times</p>
  }
  const max = Math.max(...slots.map((s) => s.score), 1)
  const weekdays = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
  return (
    <div className="overflow-x-auto">
      <div className="min-w-[640px] grid gap-1" style={{ gridTemplateColumns: '36px repeat(24, minmax(0, 1fr))' }}>
        <div />
        {Array.from({ length: 24 }, (_, h) => (
          <div key={`h-${h}`} className="text-[9px] text-center text-[var(--text-muted)]">
            {h}
          </div>
        ))}
        {weekdays.map((label, dow) => (
          <div key={`row-${dow}`} className="contents">
            <div className="text-xs text-[var(--text-muted)] pr-1 self-center">{label}</div>
            {Array.from({ length: 24 }, (_, hour) => {
              const slot = slots.find((s) => s.weekday === dow && s.hour === hour)
              const opacity = slot ? 0.15 + (slot.score / max) * 0.85 : 0.05
              return (
                <div
                  key={`${dow}-${hour}`}
                  title={slot ? `${label} ${hour}:00 · score ${slot.score}` : undefined}
                  className="h-4 rounded-sm bg-primary-500"
                  style={{ opacity }}
                />
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}

export function AnalyticsChartsSection({
  trendPoints,
  growthPoints,
  funnel,
  cohort,
}: {
  trendPoints: AnalyticsTrendPoint[]
  growthPoints: { date: string; subscribers: number }[]
  funnel: AnalyticsFunnel | null
  cohort: AnalyticsCohort | null
}) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Динамика views / ER</CardTitle>
          <CardDescription>По дневным snapshot-ам постов</CardDescription>
        </CardHeader>
        <CardContent>
          <TrendsChart points={trendPoints} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Подписчики</CardTitle>
        </CardHeader>
        <CardContent>
          <GrowthChart points={growthPoints} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Воронка</CardTitle>
          <CardDescription>collected → processed → published → reach → engagement</CardDescription>
        </CardHeader>
        <CardContent>
          <FunnelChart funnel={funnel} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Retention views</CardTitle>
          <CardDescription>% досмотра к финальным просмотрам</CardDescription>
        </CardHeader>
        <CardContent>
          <CohortBars cohort={cohort} />
        </CardContent>
      </Card>
    </div>
  )
}
