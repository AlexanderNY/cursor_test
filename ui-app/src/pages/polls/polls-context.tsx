import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { gameService } from '@/services/game-service'
import type { GameBot, GameMode } from '@/types/game'

export interface PollsContextValue {
  selectedBotId: number | null
  setSelectedBotId: (botId: number) => void
  modes: GameMode[]
  selectedModeId: number | null
  setSelectedModeId: (modeId: number | null) => void
  selectedMode: GameMode | null
  isMenuMode: boolean
  hasMenuModes: boolean
  hasQuizModes: boolean
  isLoadingModes: boolean
  loadModes: (botId?: number | null) => Promise<void>
  handleBotsLoaded: (bots: GameBot[]) => void
}

const PollsContext = createContext<PollsContextValue | null>(null)
const SELECTED_BOT_STORAGE_KEY = 'polls-selected-bot-id'

function readStoredBotId(): number | null {
  const raw = sessionStorage.getItem(SELECTED_BOT_STORAGE_KEY)
  if (!raw) return null
  const parsed = Number.parseInt(raw, 10)
  return Number.isFinite(parsed) ? parsed : null
}

export function PollsProvider({ children }: { children: ReactNode }) {
  const [selectedBotId, setSelectedBotIdState] = useState<number | null>(readStoredBotId)
  const [modes, setModes] = useState<GameMode[]>([])
  const [selectedModeId, setSelectedModeId] = useState<number | null>(null)
  const [isLoadingModes, setIsLoadingModes] = useState(true)

  const selectedMode = modes.find((mode) => mode.id === selectedModeId) ?? null
  const isMenuMode = selectedMode?.mode_type === 'menu'
  const hasMenuModes = modes.some((mode) => mode.mode_type === 'menu')
  const hasQuizModes = modes.some((mode) => mode.mode_type === 'quiz')

  const loadModes = useCallback(async (botId?: number | null) => {
    const effectiveBotId = botId ?? selectedBotId
    if (!effectiveBotId) {
      setModes([])
      setSelectedModeId(null)
      setIsLoadingModes(false)
      return
    }

    setIsLoadingModes(true)
    try {
      const data = await gameService.listModes(true, effectiveBotId)
      setModes(data)
      if (data.length > 0) {
        setSelectedModeId((prev) => (prev && data.some((mode) => mode.id === prev) ? prev : data[0].id))
      } else {
        setSelectedModeId(null)
      }
    } catch {
      setModes([])
      setSelectedModeId(null)
    } finally {
      setIsLoadingModes(false)
    }
  }, [selectedBotId])

  function setSelectedBotId(botId: number | null) {
    setSelectedBotIdState(botId)
    if (botId == null) {
      sessionStorage.removeItem(SELECTED_BOT_STORAGE_KEY)
      return
    }
    sessionStorage.setItem(SELECTED_BOT_STORAGE_KEY, String(botId))
  }

  function handleBotsLoaded(bots: GameBot[]) {
    setSelectedBotIdState((prev) => {
      const preferred = prev ?? readStoredBotId()
      const next = preferred && bots.some((bot) => bot.id === preferred) ? preferred : bots[0]?.id ?? null
      if (next == null) {
        sessionStorage.removeItem(SELECTED_BOT_STORAGE_KEY)
      } else {
        sessionStorage.setItem(SELECTED_BOT_STORAGE_KEY, String(next))
      }
      return next
    })
  }

  useEffect(() => {
    if (selectedBotId) {
      loadModes(selectedBotId)
    }
  }, [selectedBotId, loadModes])

  const value: PollsContextValue = {
    selectedBotId,
    setSelectedBotId,
    modes,
    selectedModeId,
    setSelectedModeId,
    selectedMode,
    isMenuMode,
    hasMenuModes,
    hasQuizModes,
    isLoadingModes,
    loadModes,
    handleBotsLoaded,
  }

  return <PollsContext.Provider value={value}>{children}</PollsContext.Provider>
}

export function usePollsContext(): PollsContextValue {
  const ctx = useContext(PollsContext)
  if (!ctx) {
    throw new Error('usePollsContext must be used within PollsProvider')
  }
  return ctx
}
