import { getPyodide } from './pyodide-loader'
import { ENGINE_BOOTSTRAP } from './python-bootstrap'
import { loadEffectiveGameConfig } from './settings-storage'
import { PERKS_CONFIG_PATH } from './types'
import type { GameConfig } from './game-config'
import type { InputVector, PerkKind, RenderState } from './types'
import { isAllowedHeroColor, DEFAULT_HERO_COLOR } from './hero-colors'

async function runPython(code: string): Promise<unknown> {
  const pyodide = getPyodide()
  return pyodide.runPythonAsync(`${ENGINE_BOOTSTRAP}\n${code}`)
}

let configLoaded = false

async function ensureConfigLoaded(): Promise<void> {
  if (configLoaded) return
  const [config, perksRes] = await Promise.all([
    loadEffectiveGameConfig(),
    fetch(PERKS_CONFIG_PATH),
  ])
  if (!perksRes.ok) {
    throw new Error(`Failed to load perks.json: ${perksRes.status}`)
  }
  const configJson = JSON.stringify(config)
  const perksJson = await perksRes.text()
  const pyodide = getPyodide()
  pyodide.globals.set('_bowl_config_json', configJson)
  pyodide.globals.set('_bowl_perks_json', perksJson)
  await runPython(`
engine.load_config(_bowl_config_json)
engine.load_perks(_bowl_perks_json)
`)
  configLoaded = true
}

export async function applyGameConfig(config: GameConfig): Promise<void> {
  const pyodide = getPyodide()
  pyodide.globals.set('_bowl_config_json', JSON.stringify(config))
  await runPython('engine.load_config(_bowl_config_json)')
  configLoaded = true
}

export class GameBridge {
  async applyConfig(config: GameConfig): Promise<void> {
    await applyGameConfig(config)
  }

  async newGame(
    viewportWidth: number,
    viewportHeight: number,
    perk: PerkKind,
    color: string = DEFAULT_HERO_COLOR,
  ): Promise<void> {
    await ensureConfigLoaded()
    const safeColor = isAllowedHeroColor(color) ? color : DEFAULT_HERO_COLOR
    await runPython(
      `engine.new_game(${viewportWidth}, ${viewportHeight}, "${perk}", "${safeColor}")`,
    )
  }

  async addPerk(perk: PerkKind): Promise<void> {
    await runPython(`engine.add_perk("${perk}")`)
  }

  async skipPerkSelect(): Promise<void> {
    await runPython('engine.skip_perk_select()')
  }

  async loadState(stateJson: string): Promise<boolean> {
    const pyodide = getPyodide()
    pyodide.globals.set('_bowl_state_json', stateJson)
    const result = await runPython('engine.load_state(_bowl_state_json)')
    return Boolean(result)
  }

  async exportState(): Promise<string> {
    const result = await runPython('engine.export_state_json()')
    return String(result)
  }

  async update(dt: number, input: InputVector, action: boolean): Promise<void> {
    await runPython(`engine.update(${dt}, ${input.x}, ${input.y}, ${action ? 'True' : 'False'})`)
  }

  async getRenderState(viewportWidth: number, viewportHeight: number): Promise<RenderState> {
    const result = await runPython(`
import json
json.dumps(engine.get_render_state(${viewportWidth}, ${viewportHeight}))
`)
    return JSON.parse(String(result)) as RenderState
  }
}

export const gameBridge = new GameBridge()
