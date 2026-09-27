import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { HhResumeArticle, HhResumeStrengthBar } from '@/components/hh-resume-article'
import { PageShell } from '@/components/page-shell'
import { siteFetchPhotoBlob } from '@/data/site/site-api'
import {
  resumeDownloadExport,
  resumeExport,
  resumeGenerate,
  resumeGetPreview,
  resumeListBadges,
  resumeSkillGap,
  type ResumeBadge,
  type SiteResumePreview,
  type SkillGapResult,
} from '@/data/site/resume-api'
import { useSiteAuthSession } from '@/data/site/site-auth'

async function triggerDownload(resumeId: string, format: 'pdf' | 'docx') {
  const result = await resumeExport(resumeId, format)
  const { objectUrl } = await resumeDownloadExport(result.downloadUrl)
  const a = document.createElement('a')
  a.href = objectUrl
  a.download = result.fileName
  a.click()
  URL.revokeObjectURL(objectUrl)
}

/** Полноэкранное превью + экспорт (редактирование — split на /edit). */
export function HhResumePreviewPage() {
  const { resumeId = '' } = useParams()
  const session = useSiteAuthSession()
  const [preview, setPreview] = useState<SiteResumePreview | null>(null)
  const [photoUrl, setPhotoUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [ok, setOk] = useState('')
  const [gapResult, setGapResult] = useState<SkillGapResult | null>(null)
  const [strengthOpen, setStrengthOpen] = useState(false)
  const [badges, setBadges] = useState<ResumeBadge[]>([])

  const load = useCallback(async () => {
    if (!resumeId) return
    setLoading(true)
    setError('')
    try {
      const data = await resumeGetPreview(resumeId)
      setPreview(data)
      try {
        const badgeData = await resumeListBadges()
        setBadges(badgeData.badges)
      } catch {
        setBadges([])
      }
      if (data.profile.hasPhoto) {
        const blobUrl = await siteFetchPhotoBlob()
        setPhotoUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev)
          return blobUrl
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить резюме')
    } finally {
      setLoading(false)
    }
  }, [resumeId])

  useEffect(() => {
    if (!session || !resumeId) {
      setLoading(false)
      return
    }
    void load()
    return () => {
      setPhotoUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev)
        return null
      })
    }
  }, [session?.accessToken, resumeId, load])

  const skills = useMemo(() => preview?.skills || [], [preview])

  const badgeLabels = useMemo(() => {
    if (!preview) return []
    const byId = new Map(badges.map((b) => [b.id, b.title]))
    return (preview.resume.selectedBadgeIds || []).map((id) => byId.get(id) || id)
  }, [preview, badges])

  const selectedProjects = useMemo(
    () => (preview?.resume.githubProjects || []).filter((p) => p.selected).slice(0, 6),
    [preview],
  )

  async function onEnrich() {
    if (!resumeId) return
    setBusy(true)
    setError('')
    setOk('')
    try {
      const result = await resumeGenerate(resumeId, { persist: true })
      setOk(
        result.skills.length > 0
          ? `Навыков из Learn: ${result.skills.length}`
          : `Пока нет навыков (прогресс: ${result.completedCount})`,
      )
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка обогащения')
    } finally {
      setBusy(false)
    }
  }

  async function onExport(format: 'pdf' | 'docx') {
    if (!resumeId) return
    setBusy(true)
    setError('')
    setOk('')
    try {
      await triggerDownload(resumeId, format)
      setOk(format === 'pdf' ? 'PDF скачан' : 'DOCX скачан')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка экспорта')
    } finally {
      setBusy(false)
    }
  }

  async function onSkillGap() {
    if (!resumeId) return
    setBusy(true)
    setError('')
    setOk('')
    try {
      const result = await resumeSkillGap(resumeId, {
        target_role: preview?.resume.specialization || undefined,
      })
      setGapResult(result)
      setOk(
        result.gaps.length > 0
          ? `Рекомендаций по Learn: ${result.gaps.length}`
          : 'Явных пробелов нет',
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка анализа навыков')
    } finally {
      setBusy(false)
    }
  }

  if (!session) {
    return (
      <PageShell>
        <Link to="/game/hh-resume" className="back-link">
          ← К списку
        </Link>
        <p className="learn-section-note">
          <Link to="/login">Войти</Link>
        </p>
      </PageShell>
    )
  }

  if (!resumeId) {
    return (
      <PageShell>
        <Link to="/game/hh-resume" className="back-link">
          ← К списку
        </Link>
        <p className="learn-admin-error">Не указан id резюме</p>
      </PageShell>
    )
  }

  return (
    <PageShell>
      <Link to="/game/hh-resume" className="back-link no-print">
        ← К списку резюме
      </Link>

      <header className="learn-header no-print">
        <p className="learn-eyebrow">Сервис · Резюме · превью</p>
        <h1 className="learn-title">{preview?.resume.versionName || 'Резюме'}</h1>
        <p className="learn-lead">
          <Link to={`/game/hh-resume/${resumeId}/edit`}>Редактор (split)</Link>
          {' · '}
          <Link to={`/game/hh-resume/${resumeId}/quiz`}>Опросник</Link>
        </p>
        {error ? <p className="learn-admin-error">{error}</p> : null}
        {ok ? <p className="learn-admin-ok">{ok}</p> : null}
      </header>

      {preview?.strength ? (
        <div className="no-print">
          <HhResumeStrengthBar
            score={preview.strength.score}
            maxScore={preview.strength.maxScore}
            actions={preview.strength.actions}
            expanded={strengthOpen}
            onToggle={() => setStrengthOpen((v) => !v)}
          />
        </div>
      ) : null}

      {loading ? (
        <p className="learn-section-note no-print">Загрузка…</p>
      ) : (
        <>
          <div className="account-actions no-print" style={{ marginBottom: '1.5rem' }}>
            <Link
              to={`/game/hh-resume/${resumeId}/edit`}
              className="learn-admin-btn learn-admin-btn-primary"
            >
              Редактор
            </Link>
            <button
              type="button"
              className="learn-admin-btn learn-admin-btn-primary"
              disabled={busy}
              onClick={() => void onEnrich()}
            >
              Обогатить навыками из Learn
            </button>
            <button
              type="button"
              className="learn-admin-btn"
              disabled={busy}
              onClick={() => void onSkillGap()}
            >
              Разрыв навыков
            </button>
            <button
              type="button"
              className="learn-admin-btn"
              disabled={busy}
              onClick={() => void onExport('pdf')}
            >
              Скачать PDF
            </button>
            <button
              type="button"
              className="learn-admin-btn"
              disabled={busy}
              onClick={() => void onExport('docx')}
            >
              Скачать DOCX
            </button>
            <button type="button" className="learn-admin-btn" onClick={() => window.print()}>
              Печать
            </button>
          </div>

          {gapResult ? (
            <section className="hh-resume-ai-block no-print" aria-label="Разрыв навыков">
              <h2 className="account-subheading">Рекомендации Learn</h2>
              <p className="learn-section-note">{gapResult.summary}</p>
              {gapResult.gaps.length > 0 ? (
                <ul className="hh-resume-gap-list">
                  {gapResult.gaps.map((gap) => (
                    <li key={gap.skillKey}>
                      <strong>{gap.skillKey}</strong>
                      {gap.reason ? <span> — {gap.reason}</span> : null}
                      {gap.learnSlugs.length > 0 ? (
                        <p className="hh-resume-gap-slugs">
                          {gap.learnSlugs.map((slug) => (
                            <Link key={slug} to={`/game/learn/${slug}`}>
                              {slug}
                            </Link>
                          ))}
                        </p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              ) : null}
            </section>
          ) : null}

          {preview ? (
            <HhResumeArticle
              preview={preview}
              skills={skills}
              photoUrl={photoUrl}
              badgeLabels={badgeLabels}
              projects={selectedProjects}
            />
          ) : null}
        </>
      )}
    </PageShell>
  )
}
