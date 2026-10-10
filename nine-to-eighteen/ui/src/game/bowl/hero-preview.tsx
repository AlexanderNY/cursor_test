import { useEffect, useRef } from 'react'
import { drawHeroComicFace, drawHeroFigureEight, drawHeroPaws } from './hero-visual'

interface HeroPreviewProps {
  color: string
  size?: number
  eyeCount?: number
  legCount?: number
  legReach?: number
  beakOpen?: number
}

export function HeroPreview({
  color,
  size = 96,
  eyeCount = 2,
  legCount = 2,
  legReach = 1,
  beakOpen = 0.72,
}: HeroPreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const facing = -Math.PI / 2
    const radius = size / 2 - 10
    ctx.clearRect(0, 0, size, size)
    drawHeroFigureEight(ctx, size / 2, size / 2 + 2, radius, facing, color)
    drawHeroPaws(ctx, size / 2, size / 2 + 2, radius, facing, color, 0, legCount, legReach)
    drawHeroComicFace(ctx, size / 2, size / 2 + 2, radius, facing, null, 1, beakOpen, eyeCount)
  }, [beakOpen, color, eyeCount, legCount, legReach, size])

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
