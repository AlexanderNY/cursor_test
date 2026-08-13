import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { coreService } from '@/services/core-service'
import type { PostsTablesResponse, PostingDiagnosticsResponse, ServicesStatusResponse } from '@/types/core'
import { STALE_POSTS_TABLES_MS, STALE_SERVICES_STATUS_MS } from './checks-utils'

export type ChecksInfraSection =
  | 'services-status'
  | 'processor'
  | 'collector'
  | 'scheduler'
  | 'posting-diagnostics'

function sectionFromPath(pathname: string): ChecksInfraSection | null {
  const segment = pathname.split('/').filter(Boolean).pop()
  if (
    segment === 'services-status' ||
    segment === 'processor' ||
    segment === 'collector' ||
    segment === 'scheduler' ||
    segment === 'posting-diagnostics'
  ) {
    return segment
  }
  return null
}

export function useChecksInfra() {
  const location = useLocation()
  const section = sectionFromPath(location.pathname)
  const lastServicesStatusLoadedAt = useRef<number | null>(null)
  const lastPostsTablesLoadedAt = useRef<number | null>(null)

  const [servicesStatus, setServicesStatus] = useState<ServicesStatusResponse | null>(null)
  const [postsTables, setPostsTables] = useState<PostsTablesResponse | null>(null)
  const [isLoadingServicesStatus, setIsLoadingServicesStatus] = useState(false)
  const [isLoadingPostsTables, setIsLoadingPostsTables] = useState(false)
  const [servicesStatusError, setServicesStatusError] = useState('')
  const [postsTablesError, setPostsTablesError] = useState('')
  const [isRunningProcessor, setIsRunningProcessor] = useState(false)
  const [processorRunMessage, setProcessorRunMessage] = useState('')
  const [processorRunError, setProcessorRunError] = useState('')
  const [postingDiagnostics, setPostingDiagnostics] = useState<PostingDiagnosticsResponse | null>(null)
  const [isLoadingPostingDiagnostics, setIsLoadingPostingDiagnostics] = useState(false)
  const [postingDiagnosticsError, setPostingDiagnosticsError] = useState('')
  const [isRunningCollect, setIsRunningCollect] = useState(false)
  const [collectMessage, setCollectMessage] = useState('')
  const [collectError, setCollectError] = useState('')
  const [isRunningDistribute, setIsRunningDistribute] = useState(false)
  const [distributeMessage, setDistributeMessage] = useState('')
  const [distributeError, setDistributeError] = useState('')

  async function handleLoadServicesStatus() {
    setServicesStatusError('')
    setIsLoadingServicesStatus(true)
    try {
      const data = await coreService.getServicesStatus()
      setServicesStatus(data)
      lastServicesStatusLoadedAt.current = Date.now()
    } catch (error) {
      setServicesStatusError(error instanceof Error ? error.message : 'Failed to fetch services status')
      setServicesStatus(null)
    } finally {
      setIsLoadingServicesStatus(false)
    }
  }

  async function handleRunProcessorCycle() {
    setProcessorRunMessage('')
    setProcessorRunError('')
    setIsRunningProcessor(true)
    try {
      const data = await coreService.runProcessorCycle()
      if (data.status === 'success') {
        setProcessorRunMessage(`Обработано постов: ${data.count}. ${data.message}`)
        lastPostsTablesLoadedAt.current = null
        await handleLoadServicesStatus()
      } else {
        setProcessorRunError(data.message || 'Processor cycle failed')
      }
    } catch (error) {
      setProcessorRunError(error instanceof Error ? error.message : 'Failed to run processor cycle')
    } finally {
      setIsRunningProcessor(false)
    }
  }

  async function handleLoadPostsTables() {
    setPostsTablesError('')
    setIsLoadingPostsTables(true)
    try {
      const data = await coreService.getPostsTablesOverview()
      setPostsTables(data)
      lastPostsTablesLoadedAt.current = Date.now()
    } catch (error) {
      setPostsTablesError(error instanceof Error ? error.message : 'Failed to fetch posts tables')
      setPostsTables(null)
    } finally {
      setIsLoadingPostsTables(false)
    }
  }

  async function handleRunPostingDiagnostics() {
    setPostingDiagnosticsError('')
    setPostingDiagnostics(null)
    setIsLoadingPostingDiagnostics(true)
    try {
      const data = await coreService.getPostingDiagnostics()
      setPostingDiagnostics(data)
    } catch (error) {
      setPostingDiagnosticsError(error instanceof Error ? error.message : 'Failed to run posting diagnostics')
      setPostingDiagnostics(null)
    } finally {
      setIsLoadingPostingDiagnostics(false)
    }
  }

  async function handleRunCollectCycle() {
    setCollectError('')
    setCollectMessage('')
    setIsRunningCollect(true)
    try {
      const data = await coreService.runCollectCycle()
      if (data.status === 'success') {
        setCollectMessage(`Собрано постов: ${data.count}. ${data.message}`)
        lastPostsTablesLoadedAt.current = null
        await handleLoadServicesStatus()
        await handleLoadPostsTables()
        if (section === 'posting-diagnostics') {
          await handleRunPostingDiagnostics()
        }
      } else if (data.status === 'partial') {
        setCollectMessage(`Собрано постов: ${data.count}. ${data.message}`)
        if (data.errors?.length) setCollectError(data.errors.join('; '))
        lastPostsTablesLoadedAt.current = null
        await handleLoadServicesStatus()
        await handleLoadPostsTables()
        if (section === 'posting-diagnostics') {
          await handleRunPostingDiagnostics()
        }
      } else {
        setCollectError(data.message || 'Ошибка цикла сбора')
        if (data.errors?.length) setCollectError((prev) => prev + '\n' + data.errors!.join('\n'))
      }
    } catch (error) {
      setCollectError(error instanceof Error ? error.message : 'Ошибка запуска сбора')
    } finally {
      setIsRunningCollect(false)
    }
  }

  async function handleRunDistributeCycle() {
    setDistributeError('')
    setDistributeMessage('')
    setIsRunningDistribute(true)
    try {
      const data = await coreService.runDistributeCycle()
      if (data.status === 'success') {
        setDistributeMessage(`Распределено постов: ${data.count}. ${data.message}`)
        lastPostsTablesLoadedAt.current = null
        await handleLoadServicesStatus()
        await handleLoadPostsTables()
        if (section === 'posting-diagnostics') {
          await handleRunPostingDiagnostics()
        }
      } else {
        setDistributeError(data.message || 'Ошибка цикла распределения')
      }
    } catch (error) {
      setDistributeError(error instanceof Error ? error.message : 'Ошибка запуска распределения')
    } finally {
      setIsRunningDistribute(false)
    }
  }

  useEffect(() => {
    if (!section || section === 'posting-diagnostics') {
      return
    }
    const now = Date.now()
    const servicesStale =
      lastServicesStatusLoadedAt.current === null ||
      now - lastServicesStatusLoadedAt.current > STALE_SERVICES_STATUS_MS
    if (servicesStale) {
      void handleLoadServicesStatus()
    }
    if (section === 'processor' || section === 'collector') {
      const postsStale =
        lastPostsTablesLoadedAt.current === null ||
        now - lastPostsTablesLoadedAt.current > STALE_POSTS_TABLES_MS
      if (postsStale) {
        void handleLoadPostsTables()
      }
    }
  }, [section])

  return {
    servicesStatus,
    postsTables,
    isLoadingServicesStatus,
    isLoadingPostsTables,
    servicesStatusError,
    postsTablesError,
    isRunningProcessor,
    processorRunMessage,
    processorRunError,
    postingDiagnostics,
    isLoadingPostingDiagnostics,
    postingDiagnosticsError,
    isRunningCollect,
    collectMessage,
    collectError,
    isRunningDistribute,
    distributeMessage,
    distributeError,
    handleLoadServicesStatus,
    handleRunProcessorCycle,
    handleLoadPostsTables,
    handleRunPostingDiagnostics,
    handleRunCollectCycle,
    handleRunDistributeCycle,
  }
}

export type ChecksInfra = ReturnType<typeof useChecksInfra>
