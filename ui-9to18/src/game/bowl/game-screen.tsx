import { useCallback, useEffect, useRef, useState } from 'react'
import { gameBridge } from './game-bridge'
import { GameOverScreen } from './game-over-screen'
import { drawGameFrame, drawHudBars } from './game-renderer'
import { inputManager } from './input-manager'
import { PerkSelectScreen } from './perk-select-screen'
import { writeSave } from './save-storage'
import { getAutosaveIntervalMs } from './game-config'
import type { PerkKind, RenderState } from './types'
import { VirtualJoystick } from './virtual-joystick'

interface GameScreenProps {
  onBackToMenu: () => void
}

export function GameScreen({ onBackToMenu }: GameScreenProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const hudRef = useRef<HTMLCanvasElement>(null)
  const frameRef = useRef<number | null>(null)
  const lastTimeRef = useRef<number | null>(null)
  const autosaveRef = useRef<number>(0)
  const gameOverRef = useRef(false)
  const [showGameOver, setShowGameOver] = useState(false)
  const [showJoystick, setShowJoystick] = useState(false)
  const [renderState, setRenderState] = useState<RenderState | null>(null)
  const [loopError, setLoopError] = useState<string | null>(null)

  const persistSave = useCallback(async () => {
    const stateJson = await gameBridge.exportState()
    writeSave(stateJson)
  }, [])

  const handleBackToMenu = useCallback(async () => {
    await persistSave()
    onBackToMenu()
  }, [onBackToMenu, persistSave])

  const handleSkipPerk = useCallback(async () => {
    await gameBridge.skipPerkSelect()
    await persistSave()
    const canvas = canvasRef.current
    if (canvas) {
      setRenderState(await gameBridge.getRenderState(canvas.width, canvas.height))
    }
  }, [persistSave])

  const handleLevelUpPerk = useCallback(async (perk: PerkKind) => {
    await gameBridge.addPerk(perk)
    await persistSave()
    const canvas = canvasRef.current
    if (canvas) {
      const state = await gameBridge.getRenderState(canvas.width, canvas.height)
      setRenderState(state)
    }
  }, [persistSave])

  useEffect(() => {
    const media = window.matchMedia('(pointer: coarse), (max-width: 767px)')
    const updateJoystickVisibility = () => setShowJoystick(media.matches)
    updateJoystickVisibility()
    media.addEventListener('change', updateJoystickVisibility)
    return () => media.removeEventListener('change', updateJoystickVisibility)
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    const hudCanvas = hudRef.current
    if (!canvas || !hudCanvas) return undefined

    const detachInput = inputManager.attach()
    gameOverRef.current = false
    setShowGameOver(false)
    autosaveRef.current = performance.now()

    const resize = () => {
      const width = window.innerWidth
      const height = window.innerHeight
      canvas.width = width
      canvas.height = height
      hudCanvas.width = width
      hudCanvas.height = height
    }

    resize()
    window.addEventListener('resize', resize)

    const loop = (timestamp: number) => {
      if (lastTimeRef.current === null) {
        lastTimeRef.current = timestamp
      }
      const dt = Math.min((timestamp - lastTimeRef.current) / 1000, 1 / 30)
      lastTimeRef.current = timestamp

      void (async () => {
        try {
          if (gameOverRef.current) {
            frameRef.current = requestAnimationFrame(loop)
            return
          }

          let frameState = await gameBridge.getRenderState(canvas.width, canvas.height)

          if (!frameState.pending_perk_select) {
            const input = inputManager.getVector()
            const action = inputManager.consumeAction()
            await gameBridge.update(dt, input, action)
            frameState = await gameBridge.getRenderState(canvas.width, canvas.height)
          }

          setRenderState(frameState)
          setLoopError(null)

          const gameCtx = canvas.getContext('2d')
          const hudCtx = hudCanvas.getContext('2d')
          if (gameCtx && hudCtx) {
            drawGameFrame(gameCtx, frameState, canvas.width, canvas.height)
            hudCtx.clearRect(0, 0, hudCanvas.width, hudCanvas.height)
            drawHudBars(hudCtx, frameState, hudCanvas.width)
          }

          if (frameState.game_over) {
            gameOverRef.current = true
            setShowGameOver(true)
          }

          if (timestamp - autosaveRef.current >= getAutosaveIntervalMs()) {
            autosaveRef.current = timestamp
            await persistSave()
          }
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Ошибка игрового цикла'
          setLoopError(message)
        }

        frameRef.current = requestAnimationFrame(loop)
      })()
    }

    frameRef.current = requestAnimationFrame(loop)

    return () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current)
      }
      window.removeEventListener('resize', resize)
      detachInput()
      lastTimeRef.current = null
    }
  }, [persistSave])

  return (
    <div className="bowl-game-screen">
      <canvas ref={canvasRef} className="bowl-game-canvas" />
      <canvas ref={hudRef} className="bowl-hud-canvas" />

      <button type="button" className="bowl-back-btn" onClick={handleBackToMenu}>
        ← Меню
      </button>

      <button
        type="button"
        className="bowl-action-btn"
        onClick={() => inputManager.triggerAction()}
        aria-label="Способность"
      >
        ⚡
      </button>

      {showJoystick && (
        <VirtualJoystick
          onChange={(vector) => inputManager.setJoystick(vector)}
        />
      )}

      {renderState?.pending_perk_select && (
        <PerkSelectScreen
          level={renderState.level}
          perkLevels={renderState.player.perk_levels}
          overlay
          onSelect={handleLevelUpPerk}
          onSkip={handleSkipPerk}
        />
      )}

      {loopError && (
        <div className="bowl-overlay">
          <div className="bowl-overlay-card">
            <h2 className="bowl-overlay-title">Ошибка игры</h2>
            <p className="bowl-subtitle">{loopError}</p>
            <button type="button" className="bowl-btn bowl-btn-primary" onClick={handleBackToMenu}>
              В меню
            </button>
          </div>
        </div>
      )}

      {showGameOver && <GameOverScreen onBackToMenu={onBackToMenu} />}
    </div>
  )
}
