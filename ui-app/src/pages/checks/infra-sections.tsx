import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { useChecksInfraContext } from './checks-infra-context'
import {
  platformStatusCell,
  platformTableStatusColumns,
  isCriticalService,
  isCycleStale,
  formatLoopState,
} from './checks-utils'

function HealthBadge({ status }: { status: string }) {
  const isOk = status === 'ok'
  return (
    <span
      className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
        isOk ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
      }`}
    >
      {status}
    </span>
  )
}

function LoopBadge({ loop }: { loop?: { loop_active?: boolean; cycle_in_progress?: boolean } | null }) {
  const state = formatLoopState(loop)
  const className =
    state === 'выполняется'
      ? 'bg-blue-500/20 text-blue-400'
      : state === 'активен'
        ? 'bg-emerald-500/20 text-emerald-400'
        : state === 'остановлен'
          ? 'bg-red-500/20 text-red-400'
          : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)]'
  return <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${className}`}>{state}</span>
}

function StaleBadge() {
  return (
    <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/20 text-amber-400">
      давно не запускался
    </span>
  )
}

function formatDateTime(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleString() : '—'
}

export function ServicesStatusSection() {
  const {
    servicesStatus,
    isLoadingServicesStatus,
    servicesStatusError,
    isRunningProcessor,
    processorRunMessage,
    processorRunError,
    isRunningCollect,
    collectMessage,
    collectError,
    isRunningDistribute,
    distributeMessage,
    distributeError,
    isRunningSchedulerPoll,
    schedulerPollMessage,
    schedulerPollError,
    handleLoadServicesStatus,
    handleRunProcessorCycle,
    handleRunCollectCycle,
    handleRunDistributeCycle,
    handleRunSchedulerPoll,
  } = useChecksInfraContext()

  const collectorHealth = servicesStatus?.healthchecks?.find((h) => h.service_name === 'collector')
  const processorHealth = servicesStatus?.healthchecks?.find((h) => h.service_name === 'processor')
  const schedulerHealth = servicesStatus?.healthchecks?.find((h) => h.service_name === 'scheduler')

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Состояние сервисов
        </CardTitle>
        <CardDescription>Healthcheck всех сервисов и детальный статус критичных процессов</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Button onClick={handleLoadServicesStatus} isLoading={isLoadingServicesStatus} className="w-full sm:w-auto">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Загрузить состояние сервисов
        </Button>

        {servicesStatusError && <Alert variant="error" className="animate-slide-down">{servicesStatusError}</Alert>}

        {servicesStatus && (
          <div className="space-y-8 animate-slide-down">
            <div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Все сервисы</h3>
              <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                <table className="w-full">
                  <thead className="bg-[var(--bg-tertiary)]">
                    <tr>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Сервис</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Статус</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Время сервера</th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Ошибка</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-color)]">
                    {(servicesStatus.healthchecks || []).map((h) => (
                      <tr
                        key={h.service_name}
                        className={`hover:bg-[var(--bg-tertiary)] ${isCriticalService(h.service_name) ? 'bg-primary-500/5' : ''}`}
                      >
                        <td className="py-3 px-4 text-[var(--text-primary)] font-medium">
                          <span className="flex items-center gap-2 flex-wrap">
                            {h.service_name}
                            {isCriticalService(h.service_name) && (
                              <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-primary-500/20 text-primary-400">
                                критичный
                              </span>
                            )}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <HealthBadge status={h.status} />
                        </td>
                        <td className="py-3 px-4 text-[var(--text-secondary)] text-sm">{formatDateTime(h.server_time)}</td>
                        <td className="py-3 px-4 text-[var(--text-secondary)] text-sm">{h.error ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-3">Критичные сервисы</h3>
              <div className="grid gap-4 lg:grid-cols-3">
                {/* Collector */}
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] space-y-3">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <h4 className="font-semibold text-[var(--text-primary)]">Collector</h4>
                    {collectorHealth && <HealthBadge status={collectorHealth.status} />}
                  </div>
                  {servicesStatus.collector?.error ? (
                    <p className="text-red-400 text-sm">{servicesStatus.collector.error}</p>
                  ) : servicesStatus.collector ? (
                    <ul className="text-sm text-[var(--text-secondary)] space-y-2">
                      <li className="flex items-center justify-between gap-2 flex-wrap">
                        <span>Сбор (collect)</span>
                        <LoopBadge loop={servicesStatus.collector.collector} />
                      </li>
                      <li>Последний запуск: {formatDateTime(servicesStatus.collector.collector?.last_run_at)}</li>
                      <li>За цикл: {servicesStatus.collector.collector?.last_cycle_count ?? 0}, всего: {servicesStatus.collector.collector?.total_processed ?? 0}</li>
                      {isCycleStale(
                        servicesStatus.collector.collector?.last_run_at,
                        servicesStatus.collector.collect_interval_sec,
                      ) && (
                        <li><StaleBadge /></li>
                      )}
                      <li className="pt-2 border-t border-[var(--border-color)] flex items-center justify-between gap-2 flex-wrap">
                        <span>Распределение (distribute)</span>
                        <LoopBadge loop={servicesStatus.collector.distributor} />
                      </li>
                      <li>Последний запуск: {formatDateTime(servicesStatus.collector.distributor?.last_run_at)}</li>
                      <li>За цикл: {servicesStatus.collector.distributor?.last_cycle_count ?? 0}, всего: {servicesStatus.collector.distributor?.total_processed ?? 0}</li>
                      {isCycleStale(
                        servicesStatus.collector.distributor?.last_run_at,
                        servicesStatus.collector.distribute_interval_sec,
                      ) && (
                        <li><StaleBadge /></li>
                      )}
                      <li className="text-xs text-[var(--text-muted)]">
                        Интервалы: сбор {servicesStatus.collector.collect_interval_sec ?? '—'} с / распределение {servicesStatus.collector.distribute_interval_sec ?? '—'} с
                      </li>
                    </ul>
                  ) : (
                    <p className="text-[var(--text-muted)] text-sm">Нет данных</p>
                  )}
                  <div className="flex flex-wrap gap-2 pt-2 border-t border-[var(--border-color)]">
                    <Button size="sm" variant="secondary" onClick={handleRunCollectCycle} isLoading={isRunningCollect}>
                      Запустить сбор
                    </Button>
                    <Button size="sm" variant="secondary" onClick={handleRunDistributeCycle} isLoading={isRunningDistribute}>
                      Запустить распределение
                    </Button>
                  </div>
                  {(collectMessage || collectError) && (
                    <Alert variant={collectError ? 'error' : 'success'} className="text-sm">{collectError || collectMessage}</Alert>
                  )}
                  {(distributeMessage || distributeError) && (
                    <Alert variant={distributeError ? 'error' : 'success'} className="text-sm">{distributeError || distributeMessage}</Alert>
                  )}
                </div>

                {/* Processor */}
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] space-y-3">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <h4 className="font-semibold text-[var(--text-primary)]">Processor</h4>
                    {processorHealth && <HealthBadge status={processorHealth.status} />}
                  </div>
                  {servicesStatus.processor?.error ? (
                    <p className="text-red-400 text-sm">{servicesStatus.processor.error}</p>
                  ) : servicesStatus.processor ? (
                    <ul className="text-sm text-[var(--text-secondary)] space-y-2">
                      <li className="flex items-center justify-between gap-2 flex-wrap">
                        <span>Обработка</span>
                        <LoopBadge loop={servicesStatus.processor.processor} />
                      </li>
                      <li>Последний запуск: {formatDateTime(servicesStatus.processor.processor?.last_run_at)}</li>
                      <li>За цикл: {servicesStatus.processor.processor?.last_cycle_count ?? 0}, всего: {servicesStatus.processor.processor?.total_processed ?? 0}</li>
                      {isCycleStale(
                        servicesStatus.processor.processor?.last_run_at,
                        servicesStatus.processor.process_interval_sec,
                      ) && (
                        <li><StaleBadge /></li>
                      )}
                      <li className="text-xs text-[var(--text-muted)]">
                        Интервал: {servicesStatus.processor.process_interval_sec ?? '—'} с, батч: {servicesStatus.processor.process_batch_size ?? '—'}
                      </li>
                    </ul>
                  ) : (
                    <p className="text-[var(--text-muted)] text-sm">Нет данных</p>
                  )}
                  <div className="pt-2 border-t border-[var(--border-color)]">
                    <Button size="sm" variant="secondary" onClick={handleRunProcessorCycle} isLoading={isRunningProcessor}>
                      Запустить обработку
                    </Button>
                    {processorRunMessage && <Alert variant="success" className="mt-2 text-sm">{processorRunMessage}</Alert>}
                    {processorRunError && <Alert variant="error" className="mt-2 text-sm">{processorRunError}</Alert>}
                  </div>
                </div>

                {/* Scheduler */}
                <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] space-y-3">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <h4 className="font-semibold text-[var(--text-primary)]">Scheduler</h4>
                    {schedulerHealth && <HealthBadge status={schedulerHealth.status} />}
                  </div>
                  {servicesStatus.scheduler?.error ? (
                    <p className="text-red-400 text-sm">{servicesStatus.scheduler.error}</p>
                  ) : servicesStatus.scheduler ? (
                    <ul className="text-sm text-[var(--text-secondary)] space-y-2">
                      <li className="flex items-center justify-between gap-2 flex-wrap">
                        <span>Опрос расписаний</span>
                        <LoopBadge
                          loop={{
                            loop_active: servicesStatus.scheduler.poll_loop_active,
                            cycle_in_progress: servicesStatus.scheduler.poll_in_progress,
                          }}
                        />
                      </li>
                      <li>Последний опрос: {formatDateTime(servicesStatus.scheduler.last_poll_at)}</li>
                      {isCycleStale(
                        servicesStatus.scheduler.last_poll_at,
                        servicesStatus.scheduler.poll_interval_sec,
                      ) && (
                        <li><StaleBadge /></li>
                      )}
                      <li className="text-xs text-[var(--text-muted)]">
                        Интервал опроса: {servicesStatus.scheduler.poll_interval_sec ?? '—'} с
                      </li>
                    </ul>
                  ) : (
                    <p className="text-[var(--text-muted)] text-sm">Нет данных</p>
                  )}
                  <div className="pt-2 border-t border-[var(--border-color)]">
                    <Button size="sm" variant="secondary" onClick={handleRunSchedulerPoll} isLoading={isRunningSchedulerPoll}>
                      Запустить опрос расписаний
                    </Button>
                    {schedulerPollMessage && <Alert variant="success" className="mt-2 text-sm">{schedulerPollMessage}</Alert>}
                    {schedulerPollError && <Alert variant="error" className="mt-2 text-sm">{schedulerPollError}</Alert>}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {!servicesStatus && !isLoadingServicesStatus && !servicesStatusError && (
          <p className="text-[var(--text-muted)] text-center py-8">Нажмите «Загрузить состояние сервисов» для получения данных</p>
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
              <h3 className="text-lg font-semibold text-[var(--text-primary)]">Service status</h3>
              {servicesStatus.processor.error ? (
                <p className="text-red-400 text-sm">{servicesStatus.processor.error}</p>
              ) : (
                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                  <li>State: <span className={servicesStatus.healthchecks?.find(h => h.service_name === 'processor')?.status === 'ok' ? 'text-emerald-400' : 'text-red-400'}>{servicesStatus.healthchecks?.find(h => h.service_name === 'processor')?.status ?? '—'}</span></li>
                  <li>Started at: {servicesStatus.processor.started_at ? new Date(servicesStatus.processor.started_at).toLocaleString() : '—'}</li>
                  <li>Last run: {servicesStatus.processor.processor?.last_run_at ? new Date(String(servicesStatus.processor.processor.last_run_at)).toLocaleString() : '—'}</li>
                </ul>
              )}
              <div className="pt-3 border-t border-[var(--border-color)]">
                <Button size="sm" variant="secondary" onClick={handleRunProcessorCycle} isLoading={isRunningProcessor} className="w-full sm:w-auto">
                  Запустить цикл обработки
                </Button>
                {processorRunMessage && <Alert variant="success" className="mt-2">{processorRunMessage}</Alert>}
                {processorRunError && <Alert variant="error" className="mt-2">{processorRunError}</Alert>}
              </div>
            </div>
            {!servicesStatus.processor.error && (
              <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Конфигурация сервиса</h3>
                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                  <li>Периодичность запуска: <strong className="text-[var(--text-primary)]">{servicesStatus.processor.process_interval_sec ?? '—'} с</strong></li>
                  <li>Размер батча за цикл: <strong className="text-[var(--text-primary)]">{servicesStatus.processor.process_batch_size ?? '—'}</strong> постов</li>
                </ul>
              </div>
            )}
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
    handleLoadServicesStatus,
    handleLoadPostsTables,
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
        <CardDescription>Collector service status and platform tables</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Button onClick={handleLoadServicesStatus} isLoading={isLoadingServicesStatus} className="w-full sm:w-auto">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh status
        </Button>
        {servicesStatusError && <Alert variant="error">{servicesStatusError}</Alert>}
        {servicesStatus?.collector && (
          <>
            <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Service status</h3>
              {servicesStatus.collector.error ? (
                <p className="text-red-400 text-sm">{servicesStatus.collector.error}</p>
              ) : (
                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                  <li>State: <span className={servicesStatus.healthchecks?.find(h => h.service_name === 'collector')?.status === 'ok' ? 'text-emerald-400' : 'text-red-400'}>{servicesStatus.healthchecks?.find(h => h.service_name === 'collector')?.status ?? '—'}</span></li>
                  <li>Started at: {servicesStatus.collector.started_at ? new Date(servicesStatus.collector.started_at).toLocaleString() : '—'}</li>
                  <li>Collector last run: {servicesStatus.collector.collector?.last_run_at ? new Date(String(servicesStatus.collector.collector.last_run_at)).toLocaleString() : '—'}</li>
                  <li>Distributor last run: {servicesStatus.collector.distributor?.last_run_at ? new Date(String(servicesStatus.collector.distributor.last_run_at)).toLocaleString() : '—'}</li>
                </ul>
              )}
            </div>
            {!servicesStatus.collector.error && (
              <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Конфигурация сервиса</h3>
                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                  <li>Периодичность сбора постов: <strong className="text-[var(--text-primary)]">{servicesStatus.collector.collect_interval_sec ?? '—'} с</strong></li>
                  <li>Периодичность распределения: <strong className="text-[var(--text-primary)]">{servicesStatus.collector.distribute_interval_sec ?? '—'} с</strong></li>
                  <li>Размер батча сбора: <strong className="text-[var(--text-primary)]">{servicesStatus.collector.collect_batch_size ?? '—'}</strong> постов за цикл</li>
                  <li>Размер батча распределения: <strong className="text-[var(--text-primary)]">{servicesStatus.collector.distribute_batch_size ?? '—'}</strong> постов за цикл</li>
                </ul>
              </div>
            )}
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
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Platform tables</h3>
          <p className="text-sm text-[var(--text-muted)] mb-2">
            Все платформенные таблицы постов из collector (включая threads, cpost и т.д.); по колонкам — статусы строк в каждой *_posts.
          </p>
          <Button onClick={handleLoadPostsTables} isLoading={isLoadingPostsTables} size="sm" variant="secondary" className="mb-2">
            Load posts tables
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

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          Scheduler
        </CardTitle>
        <CardDescription>Статус сервиса scheduler. Просмотр и действия с расписаниями — в Administration → Schedule.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Button onClick={handleLoadServicesStatus} isLoading={isLoadingServicesStatus} className="w-full sm:w-auto">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh status
        </Button>
        {servicesStatusError && <Alert variant="error">{servicesStatusError}</Alert>}
        {servicesStatus?.scheduler && (
          <>
            <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Service status</h3>
              {servicesStatus.scheduler.error ? (
                <p className="text-red-400 text-sm">{servicesStatus.scheduler.error}</p>
              ) : (
                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                  <li>State: <span className={servicesStatus.healthchecks?.find(h => h.service_name === 'scheduler')?.status === 'ok' ? 'text-emerald-400' : 'text-red-400'}>{servicesStatus.healthchecks?.find(h => h.service_name === 'scheduler')?.status ?? '—'}</span></li>
                  <li>Started at: {servicesStatus.scheduler.started_at ? new Date(servicesStatus.scheduler.started_at).toLocaleString() : '—'}</li>
                  <li>Last poll: {servicesStatus.scheduler.last_poll_at ? new Date(servicesStatus.scheduler.last_poll_at).toLocaleString() : '—'}</li>
                </ul>
              )}
            </div>
            {!servicesStatus.scheduler.error && (
              <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Конфигурация сервиса</h3>
                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                  <li>Периодичность опроса (сбор расписаний): <strong className="text-[var(--text-primary)]">{servicesStatus.scheduler.poll_interval_sec ?? '—'} с</strong></li>
                  <li>Оповещать ботов только при изменении: <strong className="text-[var(--text-primary)]">{servicesStatus.scheduler.notify_on_change_only === true ? 'да' : servicesStatus.scheduler.notify_on_change_only === false ? 'нет' : '—'}</strong></li>
                </ul>
              </div>
            )}
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
        <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)]">
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">Расписания и снимки</h3>
          <p className="text-sm text-[var(--text-secondary)] mb-3">
            Таблица <code className="text-xs font-mono">schedule_snapshots</code>, запуск сбора расписаний и принудительный запуск ботов находятся в{' '}
            <strong className="text-[var(--text-primary)]">Administration → Schedule</strong>.
          </p>
          <Link to="/administration?tab=schedule">
            <Button type="button" variant="secondary">Перейти к Schedule Snapshots</Button>
          </Link>
        </div>
      </CardContent>
    </Card>
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

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          Диагностика постинга (Telegram)
        </CardTitle>
        <CardDescription>Сводки по tg_posts и posts по статусам и подсказки при застревании постов в collected</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
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
                Собрано: {new Date(postingDiagnostics.collected_at).toLocaleString()}
              </p>
            )}

            <div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">tg_posts по статусам</h3>
              <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
                <table className="w-full">
                  <thead className="bg-[var(--bg-tertiary)]">
                    <tr>
                      <th className="py-3 px-4 text-left text-sm font-medium text-[var(--text-secondary)]">Статус</th>
                      <th className="py-3 px-4 text-right text-sm font-medium text-[var(--text-secondary)]">Количество</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-color)]">
                    {postingDiagnostics.tg_posts_by_status.length === 0 ? (
                      <tr>
                        <td colSpan={2} className="py-3 px-4 text-[var(--text-muted)] text-sm">Нет данных</td>
                      </tr>
                    ) : (
                      postingDiagnostics.tg_posts_by_status.map((row) => (
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
