import { useEffect, useId, useRef, useState } from 'react'

interface MermaidBlockProps {
  chart: string
}

export function MermaidBlock({ chart }: MermaidBlockProps) {
  const reactId = useId().replace(/:/g, '')
  const containerRef = useRef<HTMLDivElement>(null)
  const [hasError, setHasError] = useState(false)

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
          theme: 'dark',
          securityLevel: 'loose',
          fontFamily: 'Segoe UI, system-ui, sans-serif',
        })
        const { svg } = await mermaid.render(`learn-mermaid-${reactId}`, chart.trim())
        if (!isCancelled && containerRef.current) {
          containerRef.current.innerHTML = svg
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
  }, [chart, reactId])

  if (hasError) {
    return (
      <pre className="learn-mermaid-fallback">
        <code>{chart.trim()}</code>
      </pre>
    )
  }

  return <div ref={containerRef} className="learn-mermaid" role="img" aria-label="Схема" />
}
