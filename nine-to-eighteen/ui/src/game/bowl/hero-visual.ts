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
  const lobeRadius = radius * 0.42
  const separation = radius * 0.36
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
  eyeCount = 2,
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
      eyeScale: eyeScale * 0.9,
      beakScale: 0.72,
      browAngle: 0.28,
      beakOpen,
      eyeCount,
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
  count = 2,
  reachScale = 1,
): void {
  drawComicPaws(ctx, x, y, radius, facing, fill, wag, count, reachScale * 0.62, 0.7)
}
