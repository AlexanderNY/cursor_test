import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { AdminJumpNav } from '@/components/admin-jump-nav'
import { PageShell } from '@/components/page-shell'
import {
  resumeAdminGetSettings,
  resumeAdminPutSettings,
  type ResumeAdminSettings,
} from '@/data/site/resume-api'
import { isSuperAdmin, useSiteAuthSession } from '@/data/site/site-auth'

function emptySettings(): ResumeAdminSettings {
  return {
    rateLimits: {
      ai: { requests: 8, windowSec: 60 },
      generate: { requests: 20, windowSec: 60 },
      preview: { requests: 60, windowSec: 60 },
      export: { requests: 10, windowSec: 60 },
    },
    ai: { enabled: true, serviceUrl: '', model: '', timeoutSec: 60 },
    strength: {
      photoPoints: 10,
      aboutPoints: 15,
      aboutMinLen: 40,
      learnPointsPerModule: 20,
      maxScore: 100,
    },
    features: {
      exportEnabled: true,
      aiImproveAbout: true,
      aiSkillGap: true,
      aiCoverLetter: true,
      aiMatchScore: true,
      aiMockInterview: true,
    },
  }
}

/** Админка настроек resume-api (только site_admin). */
export function HhResumeAdminPage() {
  const session = useSiteAuthSession()
  const [settings, setSettings] = useState<ResumeAdminSettings>(emptySettings)
  const [envOnly, setEnvOnly] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await resumeAdminGetSettings()
      setSettings(data.settings)
      setEnvOnly(data.envOnly || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить настройки')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!session || !isSuperAdmin()) return
    void load()
  }, [session?.accessToken, load])

  if (!session) {
    return <Navigate to="/login" replace />
  }
  if (!isSuperAdmin()) {
    return (
      <PageShell variant="admin">
        <p className="learn-admin-error">Нужна роль site_admin</p>
        <Link to="/game/hh-resume">← К резюме</Link>
      </PageShell>
    )
  }

  async function onSave(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setOk('')
    try {
      const data = await resumeAdminPutSettings(settings)
      setSettings(data.settings)
      setOk('Настройки сохранены (применяются сразу в этом процессе resume-api)')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  function patchRate(
    bucket: keyof ResumeAdminSettings['rateLimits'],
    field: 'requests' | 'windowSec',
    value: number,
  ) {
    setSettings((prev) => ({
      ...prev,
      rateLimits: {
        ...prev.rateLimits,
        [bucket]: { ...prev.rateLimits[bucket], [field]: value },
      },
    }))
  }

  return (
    <PageShell variant="admin">
      <AdminJumpNav
        items={[
          { id: 'admin-resume-rate', label: 'Rate limits' },
          { id: 'admin-resume-ai', label: 'AI / Ollama' },
          { id: 'admin-resume-strength', label: 'Сила резюме' },
          { id: 'admin-resume-features', label: 'Фичи' },
        ]}
        serviceItems={[{ id: 'nav-hh-resume', label: 'Резюме', href: '/game/hh-resume' }]}
      />

      <header className="learn-header">
        <p className="learn-eyebrow">Админ · Резюме</p>
        <h1 className="learn-title">Настройки resume-api</h1>
        <p className="learn-lead">
          Rate limits, AI, баллы «силы резюме» и флаги фич. Секреты БД/JWT/S3 — только в env:{' '}
          {envOnly.join(', ') || 'DATABASE_URL, JWT_SECRET_KEY, S3_*'}.
        </p>
        {error ? <p className="learn-admin-error">{error}</p> : null}
        {ok ? <p className="learn-admin-ok">{ok}</p> : null}
      </header>

      {loading ? (
        <p className="learn-section-note">Загрузка…</p>
      ) : (
        <form className="learn-admin-form" onSubmit={(e) => void onSave(e)}>
          <section id="admin-resume-rate" className="hh-resume-ai-block">
            <h2 className="account-subheading">Rate limits (на пользователя / окно)</h2>
            <div className="learn-admin-grid">
              {(
                [
                  ['ai', 'AI'],
                  ['generate', 'Generate'],
                  ['preview', 'Preview'],
                  ['export', 'Export'],
                ] as const
              ).map(([key, label]) => (
                <div key={key} className="learn-admin-field">
                  <span>{label}</span>
                  <div className="hh-resume-checks">
                    <label className="hh-resume-check">
                      req
                      <input
                        type="number"
                        min={1}
                        max={10000}
                        value={settings.rateLimits[key].requests}
                        onChange={(e) =>
                          patchRate(key, 'requests', Number(e.target.value) || 1)
                        }
                      />
                    </label>
                    <label className="hh-resume-check">
                      sec
                      <input
                        type="number"
                        min={1}
                        max={3600}
                        value={settings.rateLimits[key].windowSec}
                        onChange={(e) =>
                          patchRate(key, 'windowSec', Number(e.target.value) || 1)
                        }
                      />
                    </label>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section id="admin-resume-ai" className="hh-resume-ai-block">
            <h2 className="account-subheading">AI / Ollama</h2>
            <label className="hh-resume-check">
              <input
                type="checkbox"
                checked={settings.ai.enabled}
                onChange={(e) =>
                  setSettings((prev) => ({
                    ...prev,
                    ai: { ...prev.ai, enabled: e.target.checked },
                  }))
                }
              />
              AI включён
            </label>
            <div className="learn-admin-grid">
              <label className="learn-admin-field">
                <span>AI_SERVICE_URL</span>
                <input
                  value={settings.ai.serviceUrl}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      ai: { ...prev.ai, serviceUrl: e.target.value },
                    }))
                  }
                  placeholder="http://host.docker.internal:11434"
                />
              </label>
              <label className="learn-admin-field">
                <span>Модель</span>
                <input
                  value={settings.ai.model}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      ai: { ...prev.ai, model: e.target.value },
                    }))
                  }
                  placeholder="qwen2.5:1.5b"
                />
              </label>
              <label className="learn-admin-field">
                <span>Timeout, сек</span>
                <input
                  type="number"
                  min={5}
                  max={300}
                  value={settings.ai.timeoutSec}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      ai: { ...prev.ai, timeoutSec: Number(e.target.value) || 60 },
                    }))
                  }
                />
              </label>
            </div>
          </section>

          <section id="admin-resume-strength" className="hh-resume-ai-block">
            <h2 className="account-subheading">Сила резюме (баллы)</h2>
            <div className="learn-admin-grid">
              {(
                [
                  ['photoPoints', 'Фото'],
                  ['aboutPoints', 'О себе'],
                  ['aboutMinLen', 'Мин. длина «О себе»'],
                  ['learnPointsPerModule', 'За модуль Learn'],
                  ['maxScore', 'Макс. score'],
                ] as const
              ).map(([key, label]) => (
                <label key={key} className="learn-admin-field">
                  <span>{label}</span>
                  <input
                    type="number"
                    value={settings.strength[key]}
                    onChange={(e) =>
                      setSettings((prev) => ({
                        ...prev,
                        strength: {
                          ...prev.strength,
                          [key]: Number(e.target.value) || 0,
                        },
                      }))
                    }
                  />
                </label>
              ))}
            </div>
          </section>

          <section id="admin-resume-features" className="hh-resume-ai-block">
            <h2 className="account-subheading">Фичи</h2>
            <div className="hh-resume-checks">
              {(
                [
                  ['exportEnabled', 'PDF/DOCX export'],
                  ['aiImproveAbout', 'AI «О себе»'],
                  ['aiSkillGap', 'Skill gap'],
                  ['aiCoverLetter', 'Cover letter'],
                  ['aiMatchScore', 'Match Score'],
                  ['aiMockInterview', 'Mock interview'],
                ] as const
              ).map(([key, label]) => (
                <label key={key} className="hh-resume-check">
                  <input
                    type="checkbox"
                    checked={settings.features[key]}
                    onChange={(e) =>
                      setSettings((prev) => ({
                        ...prev,
                        features: { ...prev.features, [key]: e.target.checked },
                      }))
                    }
                  />
                  {label}
                </label>
              ))}
            </div>
          </section>

          <div className="account-actions">
            <button
              type="submit"
              className="learn-admin-btn learn-admin-btn-primary"
              disabled={saving}
            >
              {saving ? 'Сохраняем…' : 'Сохранить'}
            </button>
            <button
              type="button"
              className="learn-admin-btn"
              disabled={saving}
              onClick={() => void load()}
            >
              Сбросить с сервера
            </button>
            <Link to="/game/hh-resume" className="learn-admin-btn">
              К резюме
            </Link>
          </div>
        </form>
      )}
    </PageShell>
  )
}
