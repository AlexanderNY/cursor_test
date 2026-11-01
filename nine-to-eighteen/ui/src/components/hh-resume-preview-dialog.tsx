import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { HhResumeArticle } from '@/components/hh-resume-article'
import { siteFetchPhotoBlob } from '@/data/site/site-api'
import {
  resumeDownloadExport,
  resumeExport,
  resumeGetPreview,
  resumeListBadges,
  type ResumeBadge,
  type SiteResumePreview,
} from '@/data/site/resume-api'

export function HhResumePreviewDialog({
  title,
  onClose,
  children,
  extraActions,
}: {
  title: string
  onClose: () => void
  children: ReactNode
  extraActions?: ReactNode
}) {
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onCloseRef.current()
      }
    }
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', onKey)
    }
  }, [])

  return (
    <div
      className="hh-resume-preview-overlay no-print"
      role="dialog"
      aria-modal="true"
      aria-label="Предпросмотр резюме"
      onClick={() => onCloseRef.current()}
    >
      <div
        className="hh-resume-preview-dialog"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="hh-resume-preview-dialog-head">
          <h2>Предпросмотр · {title || 'Резюме'}</h2>
          <div className="hh-resume-preview-dialog-actions">
            {extraActions}
            <button type="button" className="learn-admin-btn" onClick={() => onCloseRef.current()}>
              Закрыть
            </button>
          </div>
        </div>
        <div className="hh-resume-preview-dialog-body">{children}</div>
      </div>
    </div>
  )
}

/** Сохранённое резюме в том же окне, без перехода со списка. */
export function HhResumeSavedPreviewDialog({
  resumeId,
  onClose,
}: {
  resumeId: string
  onClose: () => void
}) {
  const [preview, setPreview] = useState<SiteResumePreview | null>(null)
  const [photoUrl, setPhotoUrl] = useState<string | null>(null)
  const [badges, setBadges] = useState<ResumeBadge[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    let cancelled = false
    let blobUrl = ''
    setLoading(true)
    setError('')
    void (async () => {
      try {
        const data = await resumeGetPreview(resumeId)
        if (cancelled) return
        setPreview(data)
        try {
          const badgeData = await resumeListBadges()
          if (!cancelled) setBadges(badgeData.badges)
        } catch {
          if (!cancelled) setBadges([])
        }
        if (data.profile.hasPhoto) {
          const loaded = await siteFetchPhotoBlob()
          if (!loaded) return
          blobUrl = loaded
          if (cancelled) {
            URL.revokeObjectURL(blobUrl)
            return
          }
          setPhotoUrl(blobUrl)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Не удалось открыть резюме')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
      if (blobUrl) URL.revokeObjectURL(blobUrl)
    }
  }, [resumeId])

  const badgeLabels = useMemo(() => {
    if (!preview) return []
    const byId = new Map(badges.map((badge) => [badge.id, badge.title]))
    return (preview.resume.selectedBadgeIds || []).map((id) => byId.get(id) || id)
  }, [preview, badges])

  const projects = useMemo(
    () => (preview?.resume.githubProjects || []).filter((project) => project.selected).slice(0, 6),
    [preview],
  )

  async function onDownload() {
    setDownloading(true)
    setError('')
    try {
      const result = await resumeExport(resumeId, 'docx')
      const { objectUrl } = await resumeDownloadExport(result.downloadUrl)
      const link = document.createElement('a')
      link.href = objectUrl
      link.download = result.fileName
      link.click()
      URL.revokeObjectURL(objectUrl)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось скачать DOCX')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <HhResumePreviewDialog
      title={preview?.resume.versionName || 'Резюме'}
      onClose={onClose}
      extraActions={
        <>
          <Link to={`/game/hh-resume/${resumeId}`} className="learn-admin-btn">
            На весь экран
          </Link>
          <button
            type="button"
            className="learn-admin-btn learn-admin-btn-primary"
            disabled={loading || downloading || !preview}
            onClick={() => void onDownload()}
          >
            {downloading ? 'Готовим DOCX…' : 'Скачать DOCX'}
          </button>
        </>
      }
    >
      {loading ? <p className="learn-section-note">Загрузка…</p> : null}
      {error ? <p className="learn-admin-error">{error}</p> : null}
      {preview ? (
        <HhResumeArticle
          preview={preview}
          skills={preview.skills}
          photoUrl={photoUrl}
          badgeLabels={badgeLabels}
          projects={projects}
        />
      ) : null}
    </HhResumePreviewDialog>
  )
}
