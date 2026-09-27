import { useEffect, useRef } from 'react'
import { drawHeroComicFace, drawHeroFigureEight, drawHeroPaws } from './hero-visual'

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
    const facing = -Math.PI / 2
    const radius = size / 2 - 8
    ctx.clearRect(0, 0, size, size)
    drawHeroFigureEight(ctx, size / 2, size / 2, radius, facing, color)
    drawHeroPaws(ctx, size / 2, size / 2, radius, facing, color, 0.35)
    drawHeroComicFace(ctx, size / 2, size / 2, radius, facing, null, 1, 0.15)
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
