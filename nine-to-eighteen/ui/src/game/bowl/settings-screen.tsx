import { useEffect, useMemo, useState } from 'react'
import type { GameConfig } from './game-config'
import { setAutosaveIntervalMs } from './game-config'
import { gameBridge } from './game-bridge'
import {
  clearSettingsOverrides,
  fetchBaseGameConfig,
  loadEffectiveGameConfig,
  mergeGameConfig,
  saveSettingsOverrides,
} from './settings-storage'
import { EDITABLE_SETTINGS, groupSettings, SETTING_GROUPS } from './settings-schema'

interface SettingsScreenProps {
  onBack: () => void
}

export function SettingsScreen({ onBack }: SettingsScreenProps) {
  const [baseConfig, setBaseConfig] = useState<GameConfig | null>(null)
  const [values, setValues] = useState<Partial<GameConfig>>({})
  const [status, setStatus] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  const grouped = useMemo(() => groupSettings(EDITABLE_SETTINGS), [])

  useEffect(() => {
    let cancelled = false
    void loadEffectiveGameConfig().then((config) => {
      if (cancelled) return
      setBaseConfig(config)
      setValues(config)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const updateNumber = (key: keyof GameConfig, raw: string) => {
    const field = EDITABLE_SETTINGS.find((item) => item.key === key)
    const parsed = Number(raw)
    if (Number.isNaN(parsed)) return
    let next = parsed
    if (field?.min !== undefined) next = Math.max(field.min, next)
    if (field?.max !== undefined) next = Math.min(field.max, next)
    setValues((prev) => ({ ...prev, [key]: next }))
  }

  const updateBoolean = (key: keyof GameConfig, checked: boolean) => {
    setValues((prev) => ({ ...prev, [key]: checked }))
  }

  const handleSave = async () => {
    if (!baseConfig) return
    setIsSaving(true)
    setStatus('')
    try {
      const freshBase = await fetchBaseGameConfig()
      const overrides: Partial<GameConfig> = {}
      for (const field of EDITABLE_SETTINGS) {
        const key = field.key
        if (values[key] !== freshBase[key]) {
          overrides[key] = values[key] as never
        }
      }
      saveSettingsOverrides(overrides)
      const merged = mergeGameConfig(freshBase, overrides)
      await gameBridge.applyConfig(merged)
      setAutosaveIntervalMs(merged.autosave_interval_ms)
      setBaseConfig(merged)
      setStatus('Сохранено. Параметры с пометкой «новая игра» — только при старте матча.')
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Не удалось сохранить')
    } finally {
      setIsSaving(false)
    }
  }

  const handleReset = async () => {
    clearSettingsOverrides()
    setStatus('')
    try {
      const fresh = await fetchBaseGameConfig()
      setBaseConfig(fresh)
      setValues(fresh)
      await gameBridge.applyConfig(fresh)
      setAutosaveIntervalMs(fresh.autosave_interval_ms)
      setStatus('Сброшено к значениям из game-config.json')
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Не удалось сбросить')
    }
  }

  if (!baseConfig) {
    return (
      <div className="bowl-screen bowl-menu">
        <div className="bowl-menu-card">
          <p className="bowl-subtitle">Загрузка настроек…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bowl-screen bowl-menu">
      <div className="bowl-settings-card">
        <div className="bowl-brand">
          <span className="bowl-brand-mark">Bowl</span>
          <span className="bowl-brand-domain">Настройки</span>
        </div>
        <h1 className="bowl-title">Быстрая настройка</h1>
        <p className="bowl-subtitle">
          Изменения сохраняются локально и сразу применяются к движку.
        </p>

        <div className="bowl-settings-scroll">
          {SETTING_GROUPS.map((group) => {
            const fields = grouped.get(group)
            if (!fields?.length) return null
            return (
              <section key={group} className="bowl-settings-group">
                <h2 className="bowl-settings-group-title">{group}</h2>
                {fields.map((field) => (
                  <label key={field.key} className="bowl-settings-row">
                    <span className="bowl-settings-label">
                      {field.label}
                      {field.newGameOnly && (
                        <span className="bowl-settings-tag">новая игра</span>
                      )}
                    </span>
                    {field.kind === 'boolean' ? (
                      <input
                        type="checkbox"
                        className="bowl-settings-checkbox"
                        checked={Boolean(values[field.key])}
                        onChange={(event) => updateBoolean(field.key, event.target.checked)}
                      />
                    ) : (
                      <input
                        type="number"
                        className="bowl-settings-input"
                        value={Number(values[field.key] ?? 0)}
                        min={field.min}
                        max={field.max}
                        step={field.step ?? 1}
                        onChange={(event) => updateNumber(field.key, event.target.value)}
                      />
                    )}
                  </label>
                ))}
              </section>
            )
          })}
        </div>

        {status && <p className="bowl-settings-status">{status}</p>}

        <div className="bowl-settings-actions">
          <button
            type="button"
            className="bowl-btn bowl-btn-primary"
            disabled={isSaving}
            onClick={handleSave}
          >
            {isSaving ? 'Сохранение…' : 'Сохранить'}
          </button>
          <button type="button" className="bowl-btn" onClick={handleReset}>
            Сбросить
          </button>
          <button type="button" className="bowl-btn bowl-btn-ghost" onClick={onBack}>
            ← Назад
          </button>
        </div>
      </div>
    </div>
  )
}
