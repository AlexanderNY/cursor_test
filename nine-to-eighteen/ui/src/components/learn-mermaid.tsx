import { useEffect, useId, useRef, useState } from 'react'
import { sanitizeSvg } from '@/data/safe-url'
import { getTheme, subscribeTheme, type ThemeMode } from '@/data/theme'

interface MermaidBlockProps {
  chart: string
}

function mermaidTheme(theme: ThemeMode): 'dark' | 'neutral' {
  return theme === 'light' ? 'neutral' : 'dark'
}

function mermaidThemeVariables(): Record<string, string> {
  const css = getComputedStyle(document.documentElement)
  const read = (name: string, fallback: string): string => {
    const value = css.getPropertyValue(name).trim()
    return value || fallback
  }
  const fg = read('--color-fg', '#f4f7fb')
  const panel = read('--color-panel', '#0a0e14')
  const accent = read('--color-accent', '#5eead4')
  const surface = read('--color-surface-2', 'rgba(255,255,255,0.1)')
  return {
    background: panel,
    primaryColor: surface,
    primaryTextColor: fg,
    primaryBorderColor: accent,
    lineColor: fg,
    secondaryColor: surface,
    tertiaryColor: panel,
    mainBkg: surface,
    nodeBorder: accent,
    clusterBkg: panel,
    titleColor: fg,
    edgeLabelBackground: panel,
    textColor: fg,
  }
}

export function MermaidBlock({ chart }: MermaidBlockProps) {
  const reactId = useId().replace(/:/g, '')
  const containerRef = useRef<HTMLDivElement>(null)
  const [hasError, setHasError] = useState(false)
  const [theme, setTheme] = useState<ThemeMode>(() =>
    typeof document === 'undefined' ? 'dark' : getTheme(),
  )

  useEffect(() => subscribeTheme(setTheme), [])

  useEffect(() => {
    let isCancelled = false

    async function renderDiagram(): Promise<void> {
      if (!containerRef.current) {
        return
      }

      setHasError(false)
      try {
        const mermaid = (await import('mermaid')).default
        mermaid.initialize({
          startOnLoad: false,
          theme: mermaidTheme(theme),
          themeVariables: mermaidThemeVariables(),
          securityLevel: 'strict',
          fontFamily: 'Segoe UI, system-ui, sans-serif',
          htmlLabels: false,
          flowchart: {
            htmlLabels: false,
            useMaxWidth: true,
          },
        })
        const { svg } = await mermaid.render(`learn-mermaid-${reactId}`, chart.trim())
        const safeSvg = sanitizeSvg(svg)
        if (!isCancelled && containerRef.current) {
          containerRef.current.innerHTML = safeSvg
        }
      } catch {
        if (!isCancelled) {
          setHasError(true)
        }
      }
    }

    void renderDiagram()

    return () => {
      isCancelled = true
    }
  }, [chart, reactId, theme])

  if (hasError) {
    return (
      <pre className="learn-mermaid-fallback">
        <code>{chart.trim()}</code>
      </pre>
    )
  }

  return <div ref={containerRef} className="learn-mermaid" role="img" aria-label="Схема" />
}
