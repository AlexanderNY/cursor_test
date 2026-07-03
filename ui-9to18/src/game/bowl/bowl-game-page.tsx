import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { gameBridge } from './game-bridge'
import { DEFAULT_HERO_COLOR } from './hero-colors'
import { HeroColorScreen } from './hero-color-screen'
import { GameScreen } from './game-screen'
import { LoadingScreen } from './loading-screen'
import { MenuScreen } from './menu-screen'
import { PerkSelectScreen } from './perk-select-screen'
import { SettingsScreen } from './settings-screen'
import { loadEffectiveGameConfig } from './settings-storage'
import { applyGameConfig } from './game-bridge'
import { setAutosaveIntervalMs } from './game-config'
import { loadPyodideRuntime } from './pyodide-loader'
import { hasSave, loadSave } from './save-storage'
import type { GameScreen as GameScreenState, PerkKind } from './types'
import '@/styles/bowl-game.css'

export function BowlGamePage() {
  const navigate = useNavigate()
  const [screen, setScreen] = useState<GameScreenState>('loading')
  const [progress, setProgress] = useState(0)
  const [progressLabel, setProgressLabel] = useState('Подготовка…')
  const [canContinue, setCanContinue] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [heroColor, setHeroColor] = useState(DEFAULT_HERO_COLOR)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        await loadPyodideRuntime((value, label) => {
          if (cancelled) return
          setProgress(value)
          setProgressLabel(label)
        })
        if (cancelled) return
        const config = await loadEffectiveGameConfig()
        await applyGameConfig(config)
        setAutosaveIntervalMs(config.autosave_interval_ms)
        if (cancelled) return
        setCanContinue(hasSave())
        setScreen('menu')
      } catch (error) {
        if (cancelled) return
        setLoadError(error instanceof Error ? error.message : 'Не удалось загрузить игру')
      }
    }

    load()

    return () => {
      cancelled = true
    }
  }, [])

  const startWithPerk = useCallback(
    async (perk: PerkKind) => {
      await gameBridge.newGame(window.innerWidth, window.innerHeight, perk, heroColor)
      setScreen('playing')
    },
    [heroColor],
  )

  const continueGame = useCallback(async () => {
    const saved = loadSave()
    if (!saved) return
    const loaded = await gameBridge.loadState(saved)
    if (!loaded) return
    setScreen('playing')
  }, [])

  const exitToHome = useCallback(() => {
    navigate('/')
  }, [navigate])

  const backToMenu = useCallback(() => {
    setCanContinue(hasSave())
    setHeroColor(DEFAULT_HERO_COLOR)
    setScreen('menu')
  }, [])

  if (loadError) {
    return (
      <div className="bowl-screen bowl-menu">
        <div className="bowl-menu-card">
          <h1 className="bowl-title">Ошибка загрузки</h1>
          <p className="bowl-subtitle">{loadError}</p>
          <button type="button" className="bowl-btn bowl-btn-primary" onClick={() => window.location.reload()}>
            Повторить
          </button>
        </div>
      </div>
    )
  }

  if (screen === 'loading') {
    return <LoadingScreen progress={progress} label={progressLabel} />
  }

  if (screen === 'menu') {
    return (
      <MenuScreen
        canContinue={canContinue}
        onNewGame={() => setScreen('colorSelect')}
        onContinue={continueGame}
        onSettings={() => setScreen('settings')}
        onExit={exitToHome}
      />
    )
  }

  if (screen === 'settings') {
    return <SettingsScreen onBack={backToMenu} />
  }

  if (screen === 'colorSelect') {
    return (
      <HeroColorScreen
        onContinue={(color) => {
          setHeroColor(color)
          setScreen('perkSelect')
        }}
        onBack={backToMenu}
      />
    )
  }

  if (screen === 'perkSelect') {
    return (
      <PerkSelectScreen
        level={1}
        onSelect={startWithPerk}
        onBack={() => setScreen('colorSelect')}
      />
    )
  }

  return <GameScreen onBackToMenu={backToMenu} />
}
