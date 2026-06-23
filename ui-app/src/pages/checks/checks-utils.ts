import type { PlatformMetric } from '@/types/core'

/** Типичные статусы строк в таблицах *_posts; редкие из БД добавляются колонками справа. */
export const PLATFORM_TABLE_STATUS_ORDER: readonly string[] = [
  'collected',
  'created',
  'processing',
  'ready',
  'review',
  'published',
  'failed',
  'skipped',
]

export function platformTableStatusColumns(platforms: PlatformMetric[]): string[] {
  const extra = new Set<string>()
  for (const p of platforms) {
    const sc = p.status_counts
    if (!sc) continue
    for (const k of Object.keys(sc)) {
      if (!PLATFORM_TABLE_STATUS_ORDER.includes(k)) {
        extra.add(k)
      }
    }
  }
  return [...PLATFORM_TABLE_STATUS_ORDER, ...Array.from(extra).sort()]
}

export function platformStatusCell(p: PlatformMetric, col: string): number {
  const sc = p.status_counts
  if (sc && Object.prototype.hasOwnProperty.call(sc, col)) {
    return Number(sc[col] ?? 0)
  }
  if (col === 'collected') return p.collected_count ?? 0
  if (col === 'created') return p.created_count ?? 0
  if (col === 'ready') return p.ready_count ?? 0
  if (col === 'processing') return p.processing_count ?? 0
  return 0
}

/** Не перезапрашивать те же данные при переключении вкладок чаще этого интервала (мс). */
export const STALE_SERVICES_STATUS_MS = 30_000
export const STALE_POSTS_TABLES_MS = 60_000
