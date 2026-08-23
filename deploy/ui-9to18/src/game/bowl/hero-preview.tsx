import { useEffect, useRef } from 'react'
import { drawHeroFigureEight } from './hero-visual'

interface HeroPreviewProps {
  color: string
  size?: number
}

export function HeroPreview({ color, size = 72 }: HeroPreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.clearRect(0, 0, size, size)
    drawHeroFigureEight(ctx, size / 2, size / 2, size / 2 - 8, -Math.PI / 2, color)
  }, [color, size])

  return (
    <canvas
      ref={canvasRef}
      width={size}
      height={size}
      className="bowl-hero-preview-canvas"
      aria-hidden
    />
  )
}
