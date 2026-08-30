import type { ReactNode } from 'react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { PageHeader, PageContainer } from '@/components/ui'
import { guideService, type GuideBlock } from '@/services/guide-service'
import {
  bodyStyle,
  renderGuideMarkdown,
  styleToCss,
  subtitleStyle,
  titleStyle,
} from '@/lib/guide-render'

const APP_VERSION = '0.1.0'

const linkBtn =
  'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 px-3 py-1.5 text-sm'
const linkBtnPrimary = `${linkBtn} bg-gradient-to-r from-primary-500 to-primary-600 text-white hover:from-primary-600 hover:to-primary-700 shadow-lg shadow-primary-500/25`
const linkBtnSecondary = `${linkBtn} bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-primary)] hover:border-primary-500/50`

function BlockCard({
  block,
  footer,
}: {
  block: GuideBlock
  footer?: ReactNode
}) {
  const cardCss = styleToCss(block.style)
  const isIntro = block.slug === 'intro'

  if (isIntro) {
    return (
      <div id={block.slug} className="scroll-mt-6 mb-6" style={cardCss}>
        {block.body ? (
          <div className="text-sm text-[var(--text-secondary)]" style={bodyStyle(block.style)}>
            {renderGuideMarkdown(block.body, block.style?.textColor)}
          </div>
        ) : null}
      </div>
    )
  }

  return (
    <section id={block.slug} className="scroll-mt-6 mb-6">
      <Card style={cardCss}>
        <CardHeader>
          <CardTitle style={titleStyle(block.style)}>{block.title}</CardTitle>
          {block.subtitle ? (
            <CardDescription style={subtitleStyle(block.style)}>{block.subtitle}</CardDescription>
          ) : null}
        </CardHeader>
        <CardContent>
          <div className="text-sm text-[var(--text-secondary)]" style={bodyStyle(block.style)}>
            {renderGuideMarkdown(block.body, block.style?.textColor)}
          </div>
          {footer}
        </CardContent>
      </Card>
    </section>
  )
}

export function AboutPage() {
  const [blocks, setBlocks] = useState<GuideBlock[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError('')
      try {
        const list = await guideService.listPublic()
        if (!cancelled) setBlocks(list)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Не удалось загрузить справку')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const intro = blocks.find((b) => b.slug === 'intro')
  const toc = useMemo(
    () =>
      blocks
        .filter((b) => b.slug !== 'intro' && (b.toc_label || b.title))
        .map((b) => ({ id: b.slug, label: b.toc_label || b.title })),
    [blocks],
  )

  const howtoFooter = blocks.some((b) => b.slug === 'howto') ? (
    <div className="mt-6 flex flex-wrap gap-2">
      <Link to="/channels" className={linkBtnPrimary}>
        Channels
      </Link>
      <Link to="/posts" className={linkBtnSecondary}>
        Posts
      </Link>
      <Link to="/inbox" className={linkBtnSecondary}>
        Inbox
      </Link>
      <Link to="/team" className={linkBtnSecondary}>
        Team
      </Link>
      <Link to="/pricing" className={linkBtnSecondary}>
        Pricing
      </Link>
    </div>
  ) : null

  return (
    <PageContainer>
      <PageHeader
        title={intro?.title || 'Справка'}
        description={
          intro?.subtitle || `Документация Control Panel · v${APP_VERSION}`
        }
      />

      {toc.length > 0 && (
        <nav className="mb-6 flex flex-wrap gap-2 text-sm">
          {toc.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              className="rounded-lg border border-[var(--border-color)] px-3 py-1.5 text-[var(--text-secondary)] hover:border-primary-500/50 hover:text-[var(--text-primary)] transition-colors"
            >
              {item.label}
            </a>
          ))}
        </nav>
      )}

      {loading && <p className="text-sm text-[var(--text-muted)]">Загрузка…</p>}
      {error && <p className="text-sm text-red-400 mb-4">{error}</p>}
      {!loading &&
        blocks.map((block) => (
          <BlockCard
            key={block.id}
            block={block}
            footer={block.slug === 'howto' ? howtoFooter : undefined}
          />
        ))}

      <Card className="mt-6" id="releases">
        <CardHeader>
          <CardTitle>Релизы продукта (трек C)</CardTitle>
          <CardDescription>
            Отдельно от учебного сезона S01E… — шаблон в docs/RELEASES.md
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-[var(--text-secondary)] space-y-2">
          <p>
            Короткие анонсы изменений CopyParse без лекций. CTA только на продукт, без склейки с
            9to18.
          </p>
          <pre className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-3 text-xs overflow-x-auto whitespace-pre-wrap">{`CopyParse · Release YYYY-MM-DD

Что изменилось:
• …

Попробовать: https://www.copyparse.ru/?utm_source=tg&utm_campaign=release_YYYYMMDD`}</pre>
          <p>
            Текущая версия UI: <strong>v{APP_VERSION}</strong>
          </p>
        </CardContent>
      </Card>
    </PageContainer>
  )
}
