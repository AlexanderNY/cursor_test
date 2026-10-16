import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { coreService } from '@/services/core-service'
import type { PostTraceResponse, ScheduleSnapshot } from '@/types/core'
import { useChecksInfraContext } from './checks-infra-context'
import { platformStatusCell, platformTableStatusColumns } from './checks-utils'
import { formatDateTime } from '@/utils/date'

/** Платформы для «Принудительный запуск ботов» (совпадает с scheduler BOT_PLATFORMS). */
const SCHEDULE_BOT_PLATFORMS = [
  'wp',
  'tg',
  'tw',
  'vk',
  'url',
  'threads',
  'dzen',
  'instagram',
] as const

function formatCpuPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—'
  return `${value}%`
}

function formatMemoryMb(bytes: number): string {
  const mb = bytes / (1024 * 1024)
  return mb >= 100 ? `${Math.round(mb)}` : mb.toFixed(1).replace(/\.0$/, '')
}

function formatMemoryUsage(
  usedBytes: number | null | undefined,
  limitBytes: number | null | undefined,
): string {
  if (usedBytes == null || Number.isNaN(usedBytes)) return '—'
  const used = formatMemoryMb(usedBytes)
  if (limitBytes == null || Number.isNaN(limitBytes) || limitBytes <= 0) {
    return `${used} МБ`
  }
  return `${used} / ${formatMemoryMb(limitBytes)} МБ`
}

export function ServicesStatusSection() {
  const {
    servicesStatus,
    isLoadingServicesStatus,
    servicesStatusError,
    isRunningProcessor,
    processorRunMessage,
    processorRunError,
    handleLoadServicesStatus,
    handleRunProcessorCycle,
  } = useChecksInfraContext()

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Services Status
        </CardTitle>
        <CardDescription>CORE, PROCESSOR, SCHEDULER, COLLECTOR health and status</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Button onClick={handleLoadServicesStatus} isLoading={isLoadingServicesStatus} className="w-full sm:w-auto">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Load Services Status
        </Button>

        {servicesStatusError && <Alert variant="error" className="animate-slide-down">{servicesStatusError}</Alert>}

        {servicesStatus && (
          <div className="space-y-6 animate-slide-down">
            <div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Healthchecks</h3>
              <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                <table className="w-full">
                  <thead className="bg-[var(--bg-tertiary)]">
                    <tr>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Service</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Status</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">CPU</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Memory</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Server time</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Error</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-color)]">
                    {(servicesStatus.healthchecks || []).map((h) => (
                      <tr key={h.service_name} className="hover:bg-[var(--bg-tertiary)]">
                        <td className="py-3 px-4 text-[var(--text-primary)] font-medium">
                          {h.service_name}
                          {h.optional ? (
                            <span className="ml-2 text-xs font-normal text-[var(--text-muted)]">optional</span>
                          ) : null}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
                              h.status === 'ok'
                                ? 'bg-emerald-500/20 text-emerald-400'
                                : h.optional
                                  ? 'bg-amber-500/20 text-amber-400'
                                  : 'bg-red-500/20 text-red-400'
                            }`}
                          >
                            {h.status === 'ok' ? 'ok' : h.optional ? 'down' : 'error'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-[var(--text-secondary)] text-sm tabular-nums">
                          {formatCpuPercent(h.cpu_percent)}
                        </td>
                        <td className="py-3 px-4 text-[var(--text-secondary)] text-sm tabular-nums">
                          {formatMemoryUsage(h.memory_bytes, h.memory_limit_bytes)}
                        </td>
                        <td className="py-3 px-4 text-[var(--text-secondary)] text-sm">{h.server_time ? formatDateTime(h.server_time) : '—'}</td>
                        <td className="py-3 px-4 text-[var(--text-secondary)] text-sm">{h.error ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {servicesStatus.collector && (
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                  <h4 className="font-semibold text-[var(--text-primary)] mb-2">COLLECTOR</h4>
                  {servicesStatus.collector.error ? (
                    <p className="text-red-400 text-sm">{servicesStatus.collector.error}</p>
                  ) : (
                    <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                      <li>Server time: {servicesStatus.collector.current_time ? formatDateTime(servicesStatus.collector.current_time) : '—'}</li>
                      <li>Interval: Dzen RSS {servicesStatus.collector.collect_interval_sec}s</li>
                      {servicesStatus.collector.collector && (
                        <li>Collector: last run {servicesStatus.collector.collector.last_run_at ? formatDateTime(servicesStatus.collector.collector.last_run_at) : '—'}, total {servicesStatus.collector.collector.total_processed}</li>
                      )}
                      {servicesStatus.collector.distributor && (
                        <li>Distributor: last run {servicesStatus.collector.distributor.last_run_at ? formatDateTime(servicesStatus.collector.distributor.last_run_at) : '—'}, total {servicesStatus.collector.distributor.total_processed}</li>
                      )}
                    </ul>
                  )}
                </div>
              )}
              {servicesStatus.processor && (
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                  <h4 className="font-semibold text-[var(--text-primary)] mb-2">PROCESSOR</h4>
                  {servicesStatus.processor.error ? (
                    <p className="text-red-400 text-sm">{servicesStatus.processor.error}</p>
                  ) : (
                    <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                      <li>Server time: {servicesStatus.processor.current_time ? formatDateTime(servicesStatus.processor.current_time) : '—'}</li>
                      <li>Interval: {servicesStatus.processor.process_interval_sec}s</li>
                      {servicesStatus.processor.processor && (
                        <li>Last run: {servicesStatus.processor.processor.last_run_at ? formatDateTime(servicesStatus.processor.processor.last_run_at) : '—'}, total {servicesStatus.processor.processor.total_processed}</li>
                      )}
                    </ul>
                  )}
                  <div className="mt-3 pt-3 border-t border-[var(--border-color)]">
                    <Button size="sm" variant="secondary" onClick={handleRunProcessorCycle} isLoading={isRunningProcessor} className="w-full sm:w-auto">
                      Запустить цикл обработки
                    </Button>
                    {processorRunMessage && <Alert variant="success" className="mt-2 animate-slide-down">{processorRunMessage}</Alert>}
                    {processorRunError && <Alert variant="error" className="mt-2 animate-slide-down">{processorRunError}</Alert>}
                  </div>
                </div>
              )}
              {servicesStatus.scheduler && (
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                  <h4 className="font-semibold text-[var(--text-primary)] mb-2">SCHEDULER</h4>
                  {servicesStatus.scheduler.error ? (
                    <p className="text-red-400 text-sm">{servicesStatus.scheduler.error}</p>
                  ) : (
                    <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                      <li>Server time: {servicesStatus.scheduler.current_time ? formatDateTime(servicesStatus.scheduler.current_time) : '—'}</li>
                      <li>Poll interval: {servicesStatus.scheduler.poll_interval_sec}s</li>
                      <li>Last poll: {servicesStatus.scheduler.last_poll_at ? formatDateTime(servicesStatus.scheduler.last_poll_at) : '—'}</li>
                    </ul>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {!servicesStatus && !isLoadingServicesStatus && !servicesStatusError && (
          <p className="text-[var(--text-muted)] text-center py-8">Click &quot;Load Services Status&quot; to fetch</p>
        )}
      </CardContent>
    </Card>
  )
}

export function ProcessorSection() {
  const {
    servicesStatus,
    postsTables,
    isLoadingServicesStatus,
    isLoadingPostsTables,
    servicesStatusError,
    postsTablesError,
    isRunningProcessor,
    processorRunMessage,
    processorRunError,
    handleLoadServicesStatus,
    handleRunProcessorCycle,
    handleLoadPostsTables,
  } = useChecksInfraContext()

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7" />
          </svg>
          Processor
        </CardTitle>
        <CardDescription>Статус processor и сводка по статусам в таблице posts; полные данные — в Administration → Posts.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Button onClick={handleLoadServicesStatus} isLoading={isLoadingServicesStatus} className="w-full sm:w-auto">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Обновить статус сервисов
        </Button>
        {servicesStatusError && <Alert variant="error" className="animate-slide-down">{servicesStatusError}</Alert>}
        {servicesStatus?.processor && (
          <>
            <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] space-y-2">
              <h3 className="text-lg font-semibold text-[var(--text-primary)]">Статус сервиса</h3>
              {servicesStatus.processor.error ? (
                <p className="text-red-400 text-sm">{servicesStatus.processor.error}</p>
              ) : (
                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                  <li>Состояние: <span className={servicesStatus.healthchecks?.find(h => h.service_name === 'processor')?.status === 'ok' ? 'text-emerald-400' : 'text-red-400'}>{servicesStatus.healthchecks?.find(h => h.service_name === 'processor')?.status ?? '—'}</span></li>
                  <li>Запущен: {servicesStatus.processor.started_at ? formatDateTime(servicesStatus.processor.started_at) : '—'}</li>
                  <li>Последний запуск: {servicesStatus.processor.processor?.last_run_at ? formatDateTime(String(servicesStatus.processor.processor.last_run_at)) : '—'}</li>
                </ul>
              )}
            </div>
            <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Конфигурация сервиса</h3>
              <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                <li>Периодичность запуска: <strong className="text-[var(--text-primary)]">{servicesStatus.processor.process_interval_sec ?? '—'} с</strong></li>
                <li>Размер батча за цикл: <strong className="text-[var(--text-primary)]">{servicesStatus.processor.process_batch_size ?? '—'}</strong> постов</li>
              </ul>
            </div>
            <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] space-y-2">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Принудительный запуск</h3>
              <p className="text-sm text-[var(--text-muted)] mb-2">Один цикл обработки постов из очереди processor.</p>
              <Button size="sm" variant="secondary" onClick={handleRunProcessorCycle} isLoading={isRunningProcessor} className="w-full sm:w-auto">
                Запустить цикл обработки
              </Button>
              {processorRunMessage && <Alert variant="success" className="mt-2">{processorRunMessage}</Alert>}
              {processorRunError && <Alert variant="error" className="mt-2">{processorRunError}</Alert>}
            </div>
            {!servicesStatus.processor.error && servicesStatus.processor.processing_options && servicesStatus.processor.processing_options.length > 0 && (
              <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Функции обработки</h3>
                <p className="text-sm text-[var(--text-muted)] mb-3">
                  Эти опции включаются для каждого пользователя в настройках профиля платформы (Telegram, WordPress, VK, Custom URL). Глобальное изменение по умолчанию здесь не предусмотрено.
                </p>
                <div className="space-y-3">
                  {servicesStatus.processor.processing_options.map((opt) => (
                    <div key={opt.id} className="flex flex-col gap-1 rounded-lg border border-[var(--border-color)] p-3 bg-[var(--bg-tertiary)]">
                      <span className="font-medium text-[var(--text-primary)]">{opt.name_ru}</span>
                      <span className="text-sm text-[var(--text-secondary)]">{opt.description}</span>
                      <span className="text-xs text-[var(--text-muted)] font-mono">{opt.id}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
        <div>
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Таблица posts (сводка processor)</h3>
          <p className="text-sm text-[var(--text-muted)] mb-3">
            Счётчики по статусам в центральной таблице posts (метрики processor). Полная таблица строк и платформенные метрики — в{' '}
            <strong className="text-[var(--text-secondary)]">Administration → Posts</strong>.
          </p>
          <Button onClick={handleLoadPostsTables} isLoading={isLoadingPostsTables} size="sm" variant="secondary" className="mb-2">
            Обновить сводку
          </Button>
          {postsTablesError && <Alert variant="error" className="mb-2">{postsTablesError}</Alert>}
          {postsTables?.posts_table_processor && Object.keys(postsTables.posts_table_processor).length > 0 && (
            <div className="flex flex-wrap gap-4">
              {Object.entries(postsTables.posts_table_processor).map(([status, count]) => (
                <span key={status} className="px-3 py-1 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-sm">
                  {status}: <strong className="text-[var(--text-primary)]">{Number(count).toLocaleString()}</strong>
                </span>
              ))}
            </div>
          )}
          <div className="mt-4">
            <Link to="/administration?tab=posts-tables">
              <Button type="button" variant="secondary">Открыть Administration → Posts</Button>
            </Link>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function CollectorSection() {
  const {
    servicesStatus,
    postsTables,
    isLoadingServicesStatus,
    isLoadingPostsTables,
    servicesStatusError,
    postsTablesError,
    isRunningCollect,
    collectMessage,
    collectError,
    isRunningDistribute,
    distributeMessage,
    distributeError,
    handleLoadServicesStatus,
    handleLoadPostsTables,
    handleRunCollectCycle,
    handleRunDistributeCycle,
  } = useChecksInfraContext()

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 14v6a2 2 0 002 2h14a2 2 0 002-2v-6a2 2 0 00-2-2M5 14V9" />
          </svg>
          Collector
        </CardTitle>
        <CardDescription>Статус collector, периодичность сбора/распределения и платформенные таблицы</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Button onClick={handleLoadServicesStatus} isLoading={isLoadingServicesStatus} className="w-full sm:w-auto">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Обновить статус сервисов
        </Button>
        {servicesStatusError && <Alert variant="error">{servicesStatusError}</Alert>}
        {servicesStatus?.collector && (
          <>
            <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Статус сервиса</h3>
              {servicesStatus.collector.error ? (
                <p className="text-red-400 text-sm">{servicesStatus.collector.error}</p>
              ) : (
                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                  <li>Состояние: <span className={servicesStatus.healthchecks?.find(h => h.service_name === 'collector')?.status === 'ok' ? 'text-emerald-400' : 'text-red-400'}>{servicesStatus.healthchecks?.find(h => h.service_name === 'collector')?.status ?? '—'}</span></li>
                  <li>Запущен: {servicesStatus.collector.started_at ? formatDateTime(servicesStatus.collector.started_at) : '—'}</li>
                  <li>Последний сбор: {servicesStatus.collector.collector?.last_run_at ? formatDateTime(String(servicesStatus.collector.collector.last_run_at)) : '—'}</li>
                  <li>Последнее распределение: {servicesStatus.collector.distributor?.last_run_at ? formatDateTime(String(servicesStatus.collector.distributor.last_run_at)) : '—'}</li>
                </ul>
              )}
            </div>
            <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Конфигурация сервиса</h3>
              <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                <li>Периодичность RSS Дзен: <strong className="text-[var(--text-primary)]">{servicesStatus.collector.collect_interval_sec ?? '—'} с</strong></li>
                <li>Размер батча сбора: <strong className="text-[var(--text-primary)]">{servicesStatus.collector.collect_batch_size ?? '—'}</strong> постов за цикл</li>
                <li>Размер батча распределения: <strong className="text-[var(--text-primary)]">{servicesStatus.collector.distribute_batch_size ?? '—'}</strong> постов за цикл</li>
              </ul>
            </div>
            <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] space-y-3">
              <h3 className="text-lg font-semibold text-[var(--text-primary)]">Принудительный запуск</h3>
              <p className="text-sm text-[var(--text-muted)]">
                Один цикл сбора постов и один цикл распределения готовых постов по платформам.
              </p>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" variant="secondary" onClick={handleRunCollectCycle} isLoading={isRunningCollect}>
                  Запустить сбор (collect)
                </Button>
                <Button size="sm" variant="secondary" onClick={handleRunDistributeCycle} isLoading={isRunningDistribute}>
                  Запустить распределение (distribute)
                </Button>
              </div>
              {collectMessage && <Alert variant="success" className="animate-slide-down">{collectMessage}</Alert>}
              {collectError && <Alert variant="error" className="animate-slide-down">{collectError}</Alert>}
              {distributeMessage && <Alert variant="success" className="animate-slide-down">{distributeMessage}</Alert>}
              {distributeError && <Alert variant="error" className="animate-slide-down">{distributeError}</Alert>}
            </div>
            {!servicesStatus.collector.error && servicesStatus.collector.collect_functions && servicesStatus.collector.collect_functions.length > 0 && (
              <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Функции сервиса</h3>
                <p className="text-sm text-[var(--text-muted)] mb-3">Запуск сбора постов для сервисов и распределение готовых постов по платформам.</p>
                <div className="space-y-3">
                  {servicesStatus.collector.collect_functions.map((fn) => (
                    <div key={fn.id} className="flex flex-col gap-1 rounded-lg border border-[var(--border-color)] p-3 bg-[var(--bg-tertiary)]">
                      <span className="font-medium text-[var(--text-primary)]">{fn.name_ru}</span>
                      <span className="text-sm text-[var(--text-secondary)]">{fn.description}</span>
                      <span className="text-xs text-[var(--text-muted)] font-mono">{fn.id}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
        <div>
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Платформенные таблицы</h3>
          <p className="text-sm text-[var(--text-muted)] mb-2">
            Все платформенные таблицы постов из collector (включая threads, cpost и т.д.); по колонкам — статусы строк в каждой *_posts.
          </p>
          <Button onClick={handleLoadPostsTables} isLoading={isLoadingPostsTables} size="sm" variant="secondary" className="mb-2">
            Обновить таблицы постов
          </Button>
          {postsTablesError && <Alert variant="error" className="mb-2">{postsTablesError}</Alert>}
          {postsTables?.platforms && postsTables.platforms.length > 0 && (() => {
            const statusCols = platformTableStatusColumns(postsTables.platforms)
            return (
              <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                <table className="w-full min-w-max">
                  <thead className="bg-[var(--bg-tertiary)]">
                    <tr>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)] whitespace-nowrap">Platform</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)] whitespace-nowrap">Table</th>
                      {statusCols.map((col) => (
                        <th key={col} className="py-3 px-2 text-right text-xs font-medium text-[var(--text-secondary)] whitespace-nowrap">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-color)]">
                    {postsTables.platforms.map((p) => (
                      <tr key={p.table} className="hover:bg-[var(--bg-tertiary)]">
                        <td className="py-3 px-4 text-[var(--text-primary)] font-medium whitespace-nowrap">{p.platform}</td>
                        <td className="py-3 px-4 text-[var(--text-secondary)] font-mono text-sm whitespace-nowrap">{p.table}</td>
                        {statusCols.map((col) => (
                          <td key={col} className="py-3 px-2 text-right text-sm text-[var(--text-secondary)] tabular-nums">
                            {platformStatusCell(p, col).toLocaleString()}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          })()}
          {postsTables?.posts_table_collector && Object.keys(postsTables.posts_table_collector).length > 0 && (
            <div className="mt-4">
              <h4 className="font-semibold text-[var(--text-primary)] mb-2">Central table posts (collector view)</h4>
              <div className="flex flex-wrap gap-4">
                {Object.entries(postsTables.posts_table_collector).map(([status, count]) => (
                  <span key={status} className="px-3 py-1 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-sm">
                    {status}: <strong className="text-[var(--text-primary)]">{Number(count).toLocaleString()}</strong>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export function SchedulerSection() {
  const {
    servicesStatus,
    isLoadingServicesStatus,
    servicesStatusError,
    handleLoadServicesStatus,
  } = useChecksInfraContext()

  const [schedules, setSchedules] = useState<ScheduleSnapshot[]>([])
  const [isLoadingSchedule, setIsLoadingSchedule] = useState(false)
  const [isStartingDiscovery, setIsStartingDiscovery] = useState(false)
  const [isStartingBot, setIsStartingBot] = useState(false)
  const [scheduleError, setScheduleError] = useState('')
  const [discoveryMessage, setDiscoveryMessage] = useState('')
  const [discoveryError, setDiscoveryError] = useState('')
  const [botMessage, setBotMessage] = useState('')
  const [selectedBots, setSelectedBots] = useState<{ [key: string]: boolean }>(() =>
    Object.fromEntries(SCHEDULE_BOT_PLATFORMS.map((p) => [p, false]))
  )

  async function handleLoadSchedule() {
    setScheduleError('')
    setIsLoadingSchedule(true)
    try {
      const response = await coreService.getSchedule()
      setSchedules(response.schedules || [])
    } catch (error) {
      setScheduleError(error instanceof Error ? error.message : 'Failed to fetch schedule')
      setSchedules([])
    } finally {
      setIsLoadingSchedule(false)
    }
  }

  async function handleStartDiscovery() {
    setDiscoveryMessage('')
    setDiscoveryError('')
    setIsStartingDiscovery(true)
    try {
      const response = await coreService.startDiscovery()
      setDiscoveryMessage(
        response.message + (response.changed ? ' (есть изменения)' : ' (без изменений)')
      )
      await handleLoadServicesStatus()
    } catch (error) {
      setDiscoveryError(error instanceof Error ? error.message : 'Не удалось запустить опрос расписаний')
      setDiscoveryMessage('')
    } finally {
      setIsStartingDiscovery(false)
    }
  }

  async function handleStartBot() {
    const selectedPlatforms = Object.entries(selectedBots)
      .filter(([, selected]) => selected)
      .map(([platform]) => platform)

    if (selectedPlatforms.length === 0) {
      setBotMessage('Выберите хотя бы одного бота')
      return
    }

    setBotMessage('')
    setScheduleError('')
    setIsStartingBot(true)
    try {
      const response = await coreService.startBot(selectedPlatforms)
      const results = Object.entries(response.results || {})
        .map(([platform, result]: [string, { status?: string }]) =>
          `${platform}: ${result.status === 'success' ? 'Success' : 'Error'}`
        )
        .join(', ')
      setBotMessage(`Bots started: ${results}`)
    } catch (error) {
      setScheduleError(error instanceof Error ? error.message : 'Failed to start bots')
      setBotMessage('')
    } finally {
      setIsStartingBot(false)
    }
  }

  function handleBotToggle(platform: string) {
    setSelectedBots((prev) => ({
      ...prev,
      [platform]: !prev[platform],
    }))
  }

  return (
    <div className="space-y-6 animate-slide-up">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Scheduler
          </CardTitle>
          <CardDescription>Статус сервиса scheduler, снимки расписаний и принудительный запуск ботов</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Button onClick={handleLoadServicesStatus} isLoading={isLoadingServicesStatus} className="w-full sm:w-auto">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Обновить статус сервисов
          </Button>
          {servicesStatusError && <Alert variant="error">{servicesStatusError}</Alert>}
          {servicesStatus?.scheduler && (
            <>
              <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Статус сервиса</h3>
                {servicesStatus.scheduler.error ? (
                  <p className="text-red-400 text-sm">{servicesStatus.scheduler.error}</p>
                ) : (
                  <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                    <li>Состояние: <span className={servicesStatus.healthchecks?.find(h => h.service_name === 'scheduler')?.status === 'ok' ? 'text-emerald-400' : 'text-red-400'}>{servicesStatus.healthchecks?.find(h => h.service_name === 'scheduler')?.status ?? '—'}</span></li>
                    <li>Запущен: {servicesStatus.scheduler.started_at ? formatDateTime(servicesStatus.scheduler.started_at) : '—'}</li>
                    <li>Последний опрос: {servicesStatus.scheduler.last_poll_at ? formatDateTime(servicesStatus.scheduler.last_poll_at) : '—'}</li>
                  </ul>
                )}
              </div>
              <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Конфигурация сервиса</h3>
                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                  <li>Периодичность опроса (сбор расписаний): <strong className="text-[var(--text-primary)]">{servicesStatus.scheduler.poll_interval_sec ?? '—'} с</strong></li>
                  <li>Оповещать ботов только при изменении: <strong className="text-[var(--text-primary)]">{servicesStatus.scheduler.notify_on_change_only === true ? 'да' : servicesStatus.scheduler.notify_on_change_only === false ? 'нет' : '—'}</strong></li>
                </ul>
              </div>
              <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] space-y-2">
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Принудительный запуск</h3>
                <p className="text-sm text-[var(--text-muted)] mb-2">
                  Один цикл опроса scheduler’а: сбор снимков расписаний и уведомление ботов (в т.ч. Custom URL / url-bot).
                </p>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={handleStartDiscovery}
                  isLoading={isStartingDiscovery}
                  className="w-full sm:w-auto"
                >
                  Запустить опрос расписаний
                </Button>
                {discoveryMessage && (
                  <Alert variant="success" className="mt-2 animate-slide-down">
                    {discoveryMessage}
                  </Alert>
                )}
                {discoveryError && (
                  <Alert variant="error" className="mt-2 animate-slide-down">
                    {discoveryError}
                  </Alert>
                )}
              </div>
              {!servicesStatus.scheduler.error && servicesStatus.scheduler.schedule_functions && servicesStatus.scheduler.schedule_functions.length > 0 && (
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                  <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Функции сервиса</h3>
                  <p className="text-sm text-[var(--text-muted)] mb-3">Запуск сбора расписаний для сервисов и связанные операции.</p>
                  <div className="space-y-3">
                    {servicesStatus.scheduler.schedule_functions.map((fn) => (
                      <div key={fn.id} className="flex flex-col gap-1 rounded-lg border border-[var(--border-color)] p-3 bg-[var(--bg-tertiary)]">
                        <span className="font-medium text-[var(--text-primary)]">{fn.name_ru}</span>
                        <span className="text-sm text-[var(--text-secondary)]">{fn.description}</span>
                        <span className="text-xs text-[var(--text-muted)] font-mono">{fn.id}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Schedule Snapshots</CardTitle>
          <CardDescription>Таблица schedule_snapshots и принудительный запуск ботов</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Запуск сбора расписаний</h3>
              <p className="text-sm text-[var(--text-secondary)] mb-4">
                Дублирует кнопку выше: один цикл poll scheduler’а
              </p>
              <Button
                onClick={handleStartDiscovery}
                isLoading={isStartingDiscovery}
                className="w-full sm:w-auto"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Запуск сбора расписаний
              </Button>
              {discoveryMessage && (
                <Alert variant="success" className="mt-2 animate-slide-down">
                  {discoveryMessage}
                </Alert>
              )}
              {discoveryError && (
                <Alert variant="error" className="mt-2 animate-slide-down">
                  {discoveryError}
                </Alert>
              )}
            </div>
          </div>

          <div className="space-y-4 border-t border-[var(--border-color)] pt-4">
            <div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Принудительный запуск ботов</h3>
              <p className="text-sm text-[var(--text-secondary)] mb-4">
                Выберите ботов для запуска и нажмите кнопку запуска
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
                {SCHEDULE_BOT_PLATFORMS.map((platform) => (
                  <label
                    key={platform}
                    className="flex items-center space-x-2 cursor-pointer p-3 rounded-lg border border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={selectedBots[platform]}
                      onChange={() => handleBotToggle(platform)}
                      className="w-4 h-4 text-primary-400 rounded focus:ring-primary-400"
                    />
                    <span className="text-[var(--text-secondary)] font-medium uppercase">{platform}</span>
                  </label>
                ))}
              </div>

              <Button
                onClick={handleStartBot}
                isLoading={isStartingBot}
                className="w-full sm:w-auto"
                disabled={Object.values(selectedBots).every((v) => !v)}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Запустить боты
              </Button>
              {botMessage && (
                <Alert variant={botMessage.includes('Error') ? 'error' : 'success'} className="mt-2 animate-slide-down">
                  {botMessage}
                </Alert>
              )}
            </div>
          </div>

          <div className="space-y-4 border-t border-[var(--border-color)] pt-4">
            <div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Просмотр расписаний</h3>
              <p className="text-sm text-[var(--text-secondary)] mb-4">
                Загрузить расписания из таблицы schedule_snapshots
              </p>
              <Button
                onClick={handleLoadSchedule}
                isLoading={isLoadingSchedule}
                className="w-full sm:w-auto"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Получить расписание
              </Button>
            </div>
          </div>

          {scheduleError && (
            <Alert variant="error" className="animate-slide-down">
              {scheduleError}
            </Alert>
          )}

          {schedules.length > 0 && (
            <div className="overflow-x-auto animate-slide-down">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-[var(--border-color)]">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">User ID</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Platform</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Publish Enabled</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Collect Enabled</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Schedule Type</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Time Intervals</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Updated At</th>
                  </tr>
                </thead>
                <tbody>
                  {schedules.map((schedule, index) => (
                    <tr
                      key={`${schedule.user_id}-${schedule.platform}-${index}`}
                      className="border-b border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors"
                    >
                      <td className="py-3 px-4 text-[var(--text-secondary)] font-medium">{schedule.user_id}</td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-blue-500/20 text-blue-400">
                          {schedule.platform}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {schedule.publish_enabled ? (
                          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-emerald-500/20 text-emerald-400">
                            Enabled
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-gray-500/20 text-gray-400">
                            Disabled
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {schedule.collect_enabled ? (
                          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-emerald-500/20 text-emerald-400">
                            Enabled
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-gray-500/20 text-gray-400">
                            Disabled
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-[var(--text-secondary)]">{schedule.schedule_type}</td>
                      <td className="py-3 px-4 text-[var(--text-secondary)]">
                        {schedule.time_intervals && schedule.time_intervals.length > 0 ? (
                          <div className="flex flex-col gap-1">
                            {schedule.time_intervals.map((interval, idx) => (
                              <span key={idx} className="text-xs">
                                {interval.start} - {interval.end}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-[var(--text-muted)]">No intervals</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-[var(--text-secondary)]">
                        {formatDateTime(schedule.updated_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {schedules.length === 0 && !isLoadingSchedule && !scheduleError && (
            <p className="text-[var(--text-muted)] text-center py-8">
              Click &quot;Получить расписание&quot; to fetch schedule snapshots
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export function PostingDiagnosticsSection() {
  const {
    postingDiagnostics,
    isLoadingPostingDiagnostics,
    postingDiagnosticsError,
    isRunningCollect,
    collectMessage,
    collectError,
    isRunningDistribute,
    distributeMessage,
    distributeError,
    handleRunPostingDiagnostics,
    handleRunCollectCycle,
    handleRunDistributeCycle,
  } = useChecksInfraContext()

  const [tracePostId, setTracePostId] = useState('')
  const [postTrace, setPostTrace] = useState<PostTraceResponse | null>(null)
  const [isLoadingTrace, setIsLoadingTrace] = useState(false)
  const [traceError, setTraceError] = useState('')

  async function handleLoadPostTrace() {
    const parsed = Number.parseInt(tracePostId.trim(), 10)
    if (!Number.isFinite(parsed) || parsed <= 0) {
      setTraceError('Укажите корректный post_id')
      setPostTrace(null)
      return
    }
    setTraceError('')
    setPostTrace(null)
    setIsLoadingTrace(true)
    try {
      const data = await coreService.getPostTrace(parsed)
      setPostTrace(data)
    } catch (error) {
      setTraceError(error instanceof Error ? error.message : 'Не удалось загрузить трейс')
      setPostTrace(null)
    } finally {
      setIsLoadingTrace(false)
    }
  }

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          Диагностика постинга (Telegram)
        </CardTitle>
        <CardDescription>Сводки по post_targets (Telegram) и posts по статусам; путь одного сообщения по post_id</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="rounded-xl border border-[var(--border-color)] p-4 space-y-3 bg-[var(--bg-tertiary)]/40">
          <h3 className="text-base font-semibold text-[var(--text-primary)]">Путь сообщения (post_id)</h3>
          <p className="text-sm text-[var(--text-secondary)]">
            Восстанавливает цепочку: сбор → обработка → post_targets → публикация (lifecycle + текущее состояние).
          </p>
          <div className="flex flex-wrap gap-2 items-center">
            <input
              type="number"
              min={1}
              value={tracePostId}
              onChange={(event) => setTracePostId(event.target.value)}
              placeholder="post_id"
              className="px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-primary)] text-sm w-40"
            />
            <Button onClick={handleLoadPostTrace} isLoading={isLoadingTrace} size="sm">
              Показать путь
            </Button>
          </div>
          {traceError && <Alert variant="error">{traceError}</Alert>}
          {postTrace && (
            <div className="space-y-4 animate-slide-down">
              <div className="flex flex-wrap gap-2">
                {postTrace.stages.map((stage) => (
                  <span
                    key={stage.stage}
                    className={`px-3 py-1.5 rounded-lg text-sm ${
                      stage.done
                        ? 'bg-emerald-500/15 text-emerald-300'
                        : 'bg-[var(--bg-secondary)] text-[var(--text-muted)]'
                    }`}
                    title={stage.detail ?? undefined}
                  >
                    {stage.done ? '✓' : '○'} {stage.label}
                    {stage.detail ? ` — ${stage.detail}` : ''}
                  </span>
                ))}
              </div>
              <div className="text-sm text-[var(--text-secondary)] space-y-1">
                <div>
                  Hub #{postTrace.post_id}: status=<strong className="text-[var(--text-primary)]">{String(postTrace.hub.status ?? '—')}</strong>
                  , source=<strong className="text-[var(--text-primary)]">{String(postTrace.hub.source_platform ?? '—')}</strong>
                  , user=<strong className="text-[var(--text-primary)]">{String(postTrace.hub.user_id ?? '—')}</strong>
                </div>
                <div>Targets: {postTrace.targets.length || 0}</div>
              </div>
              {postTrace.targets.length > 0 && (
                <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                  <table className="w-full text-sm">
                    <thead className="bg-[var(--bg-secondary)]">
                      <tr>
                        <th className="py-2 px-3 text-left text-[var(--text-secondary)]">id</th>
                        <th className="py-2 px-3 text-left text-[var(--text-secondary)]">platform</th>
                        <th className="py-2 px-3 text-left text-[var(--text-secondary)]">status</th>
                        <th className="py-2 px-3 text-left text-[var(--text-secondary)]">updated</th>
                        <th className="py-2 px-3 text-left text-[var(--text-secondary)]">result</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--border-color)]">
                      {postTrace.targets.map((target) => (
                        <tr key={String(target.id)}>
                          <td className="py-2 px-3 text-[var(--text-primary)]">{String(target.id)}</td>
                          <td className="py-2 px-3 text-[var(--text-primary)]">{String(target.platform)}</td>
                          <td className="py-2 px-3 text-[var(--text-primary)]">{String(target.status)}</td>
                          <td className="py-2 px-3 text-[var(--text-muted)]">
                            {target.updated_at ? formatDateTime(String(target.updated_at)) : '—'}
                          </td>
                          <td className="py-2 px-3 text-[var(--text-muted)] font-mono text-xs max-w-xs truncate">
                            {target.result ? JSON.stringify(target.result) : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <div>
                <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">
                  Таймлайн ({postTrace.timeline.length}
                  {postTrace.lifecycle_events.length === 0 ? ', inferred — журнал пуст для старых постов' : ''})
                </h4>
                <ol className="space-y-2 border-l border-[var(--border-color)] pl-4">
                  {postTrace.timeline.map((item, idx) => (
                    <li key={`${item.at ?? ''}-${item.to_status ?? ''}-${idx}`} className="text-sm">
                      <div className="text-[var(--text-muted)] text-xs">
                        {item.at ? formatDateTime(item.at) : '—'} · {item.source} · {item.actor ?? '—'}
                      </div>
                      <div className="text-[var(--text-primary)]">
                        [{item.platform ?? '—'}] {item.from_status ?? '∅'} → <strong>{item.to_status ?? '—'}</strong>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
              {postTrace.related_tg_events.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">
                    Связанные tg_events ({postTrace.related_tg_events.length})
                  </h4>
                  <ul className="space-y-1 text-sm text-[var(--text-secondary)]">
                    {postTrace.related_tg_events.map((event) => (
                      <li key={String(event.id)}>
                        {event.created_at ? formatDateTime(String(event.created_at)) : '—'} · {String(event.event_type)}
                        {event.text_preview ? ` — ${String(event.text_preview).slice(0, 80)}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        <Button onClick={handleRunPostingDiagnostics} isLoading={isLoadingPostingDiagnostics} className="w-full sm:w-auto">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Запустить диагностику
        </Button>

        <div className="flex flex-wrap gap-3 items-center">
          <span className="text-sm font-medium text-[var(--text-secondary)]">Быстрые действия:</span>
          <Button variant="secondary" size="sm" onClick={handleRunCollectCycle} isLoading={isRunningCollect}>
            Запустить сбор (collect)
          </Button>
          <Button variant="secondary" size="sm" onClick={handleRunDistributeCycle} isLoading={isRunningDistribute}>
            Запустить распределение (distribute)
          </Button>
          <Link to="/checks/processor" className="text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] underline">
            Цикл обработки — на вкладке Processor
          </Link>
        </div>
        {(collectMessage || collectError) && (
          <Alert variant={collectError ? 'error' : 'success'} className="animate-slide-down">
            {collectError || collectMessage}
          </Alert>
        )}
        {(distributeMessage || distributeError) && (
          <Alert variant={distributeError ? 'error' : 'success'} className="animate-slide-down">
            {distributeError || distributeMessage}
          </Alert>
        )}

        {postingDiagnosticsError && <Alert variant="error" className="animate-slide-down">{postingDiagnosticsError}</Alert>}

        {postingDiagnostics && (
          <div className="space-y-6 animate-slide-down">
            {postingDiagnostics.collected_at && (
              <p className="text-sm text-[var(--text-muted)]">
                Собрано: {formatDateTime(postingDiagnostics.collected_at)}
              </p>
            )}

            <div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Telegram queue (post_targets) по статусам</h3>
              <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                <table className="w-full">
                  <thead className="bg-[var(--bg-tertiary)]">
                    <tr>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Статус</th>
                      <th className="py-3 px-4 text-right text-sm font-medium text-[var(--text-secondary)]">Количество</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-color)]">
                    {(postingDiagnostics.tg_targets_by_status ?? postingDiagnostics.tg_posts_by_status).length === 0 ? (
                      <tr>
                        <td colSpan={2} className="py-3 px-4 text-[var(--text-muted)] text-sm">Нет данных</td>
                      </tr>
                    ) : (
                      (postingDiagnostics.tg_targets_by_status ?? postingDiagnostics.tg_posts_by_status).map((row) => (
                        <tr key={row.status} className="hover:bg-[var(--bg-tertiary)]">
                          <td className="py-3 px-4 text-[var(--text-primary)] font-medium">{row.status}</td>
                          <td className="py-3 px-4 text-right text-[var(--text-secondary)]">{row.count.toLocaleString()}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">posts по статусам и платформе</h3>
              <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                <table className="w-full">
                  <thead className="bg-[var(--bg-tertiary)]">
                    <tr>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Статус</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Платформа</th>
                      <th className="py-3 px-4 text-right text-sm font-medium text-[var(--text-secondary)]">Количество</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-color)]">
                    {postingDiagnostics.posts_by_status.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="py-3 px-4 text-[var(--text-muted)] text-sm">Нет данных</td>
                      </tr>
                    ) : (
                      postingDiagnostics.posts_by_status.map((row, idx) => (
                        <tr key={`${row.status}-${row.source_platform ?? ''}-${idx}`} className="hover:bg-[var(--bg-tertiary)]">
                          <td className="py-3 px-4 text-[var(--text-primary)] font-medium">{row.status}</td>
                          <td className="py-3 px-4 text-[var(--text-secondary)]">{row.source_platform ?? '—'}</td>
                          <td className="py-3 px-4 text-right text-[var(--text-secondary)]">{row.count.toLocaleString()}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex flex-wrap gap-4">
              <span className="px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-sm">
                Готовы к публикации в TG: <strong className="text-[var(--text-primary)]">{postingDiagnostics.ready_for_telegram.toLocaleString()}</strong>
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-sm">
                Профилей с каналом: <strong className="text-[var(--text-primary)]">{postingDiagnostics.profiles_with_channel.toLocaleString()}</strong>
              </span>
            </div>

            {postingDiagnostics.hints.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Рекомендации</h3>
                <ul className="space-y-2">
                  {postingDiagnostics.hints.map((hint, idx) => (
                    <li key={idx} className="flex gap-2 text-sm text-[var(--text-secondary)]">
                      <span className="text-amber-400 shrink-0">•</span>
                      <span>{hint}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {!postingDiagnostics && !isLoadingPostingDiagnostics && !postingDiagnosticsError && (
          <p className="text-[var(--text-muted)] text-center py-8">
            Нажмите «Запустить диагностику», чтобы получить сводки и подсказки по пайплайну постинга.
          </p>
        )}
      </CardContent>
    </Card>
  )
}
