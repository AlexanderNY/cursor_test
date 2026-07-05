import { heroStrokeColor } from './hero-colors'

export interface HeroLobeLayout {
  lobeRadius: number
  separation: number
  frontOffsetX: number
  frontOffsetY: number
  backOffsetX: number
  backOffsetY: number
}

export function getHeroLobeLayout(radius: number, facing: number): HeroLobeLayout {
  const lobeRadius = radius * 0.58
  const separation = radius * 0.5
  const frontOffsetX = Math.cos(facing) * separation
  const frontOffsetY = Math.sin(facing) * separation
  return {
    lobeRadius,
    separation,
    frontOffsetX,
    frontOffsetY,
    backOffsetX: -frontOffsetX,
    backOffsetY: -frontOffsetY,
  }
}

export function drawHeroFigureEight(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
  fill: string,
  stroke?: string,
): void {
  const layout = getHeroLobeLayout(radius, facing)
  const strokeColor = stroke ?? heroStrokeColor(fill)

  const lobes: Array<[number, number]> = [
    [layout.backOffsetX, layout.backOffsetY],
    [layout.frontOffsetX, layout.frontOffsetY],
  ]

  for (const [offsetX, offsetY] of lobes) {
    ctx.beginPath()
    ctx.arc(x + offsetX, y + offsetY, layout.lobeRadius, 0, Math.PI * 2)
    ctx.fillStyle = fill
    ctx.fill()
    ctx.strokeStyle = strokeColor
    ctx.lineWidth = 2
    ctx.stroke()
  }
}
