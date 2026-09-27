import { heroStrokeColor } from './hero-colors'
import { drawComicBody, drawComicFace, drawComicPaws } from './character-visual'

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
  const strokeColor = stroke ?? heroStrokeColor(fill)
  drawComicBody(ctx, x, y, radius, facing, fill, strokeColor, 'hero')
}

export function drawHeroComicFace(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
  lookTarget: { x: number; y: number } | null = null,
  eyeScale = 1,
  beakOpen = 0,
): void {
  const layout = getHeroLobeLayout(radius, facing)
  drawComicFace(
    ctx,
    x + layout.frontOffsetX,
    y + layout.frontOffsetY,
    layout.lobeRadius,
    facing,
    {
      lookTarget,
      eyeScale,
      beakScale: 1.05,
      browAngle: 0.28,
      beakOpen,
    },
  )
}

export function drawHeroPaws(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
  fill: string,
  wag: number,
): void {
  drawComicPaws(ctx, x, y, radius, facing, fill, wag)
}
