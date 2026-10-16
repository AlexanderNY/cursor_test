export type ComicBodyStyle = 'round' | 'hunter' | 'lurker' | 'hero' | 'boss'

export interface ComicFaceOptions {
  eyeScale?: number
  browAngle?: number
  beakScale?: number
  /** 0 — клюв закрыт, 1 — широко открыт. */
  beakOpen?: number
  lookTarget?: { x: number; y: number } | null
  pupilColor?: string
  eyeWhite?: string
  beakFill?: string
  browColor?: string
  /** Сколько глаз. Два стоят парой, четыре и шесть — сотами. */
  eyeCount?: number
}

function drawFilledCircle(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  fill: string,
  stroke: string,
  lineWidth = 2,
): void {
  ctx.beginPath()
  ctx.arc(x, y, radius, 0, Math.PI * 2)
  ctx.fillStyle = fill
  ctx.fill()
  ctx.strokeStyle = stroke
  ctx.lineWidth = lineWidth
  ctx.stroke()
}

function drawFilledEllipse(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radiusX: number,
  radiusY: number,
  rotation: number,
  fill: string,
  stroke: string,
  lineWidth = 2,
): void {
  ctx.beginPath()
  ctx.ellipse(x, y, radiusX, radiusY, rotation, 0, Math.PI * 2)
  ctx.fillStyle = fill
  ctx.fill()
  ctx.strokeStyle = stroke
  ctx.lineWidth = lineWidth
  ctx.stroke()
}

/** Составное тело из нескольких простых фигур. Хитбокс снаружи остаётся кругом. */
export function drawComicBody(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
  fill: string,
  stroke: string,
  style: ComicBodyStyle = 'round',
): void {
  const fx = Math.cos(facing)
  const fy = Math.sin(facing)
  const px = -fy
  const py = fx
  const lineWidth = style === 'boss' ? 3.5 : 2.2

  if (style === 'hero') {
    const lobe = radius * 0.42
    const sep = radius * 0.36
    drawFilledCircle(ctx, x - fx * sep, y - fy * sep, lobe, fill, stroke, lineWidth)
    drawFilledCircle(ctx, x + fx * sep, y + fy * sep, lobe, fill, stroke, lineWidth)
    drawFilledEllipse(
      ctx,
      x - fx * radius * 0.08,
      y - fy * radius * 0.08,
      radius * 0.3,
      radius * 0.24,
      facing,
      fill,
      stroke,
      lineWidth,
    )
    return
  }

  if (style === 'boss') {
    drawFilledCircle(ctx, x, y, radius * 0.78, fill, stroke, lineWidth)
    drawFilledCircle(
      ctx,
      x + fx * radius * 0.42,
      y + fy * radius * 0.42,
      radius * 0.55,
      fill,
      stroke,
      lineWidth,
    )
    drawFilledCircle(
      ctx,
      x - fx * radius * 0.38,
      y - fy * radius * 0.38,
      radius * 0.48,
      fill,
      stroke,
      lineWidth,
    )
    drawFilledCircle(
      ctx,
      x + px * radius * 0.4,
      y + py * radius * 0.4,
      radius * 0.36,
      fill,
      stroke,
      lineWidth,
    )
    drawFilledCircle(
      ctx,
      x - px * radius * 0.4,
      y - py * radius * 0.4,
      radius * 0.36,
      fill,
      stroke,
      lineWidth,
    )
    return
  }

  if (style === 'hunter') {
    drawFilledEllipse(
      ctx,
      x,
      y,
      radius * 0.95,
      radius * 0.62,
      facing,
      fill,
      stroke,
      lineWidth,
    )
    drawFilledCircle(
      ctx,
      x + fx * radius * 0.42,
      y + fy * radius * 0.42,
      radius * 0.48,
      fill,
      stroke,
      lineWidth,
    )
    drawFilledEllipse(
      ctx,
      x - fx * radius * 0.72,
      y - fy * radius * 0.72,
      radius * 0.38,
      radius * 0.22,
      facing,
      fill,
      stroke,
      lineWidth,
    )
    return
  }

  if (style === 'lurker') {
    drawFilledEllipse(
      ctx,
      x + fx * radius * 0.12,
      y + fy * radius * 0.12,
      radius * 0.72,
      radius * 0.95,
      facing,
      fill,
      stroke,
      lineWidth,
    )
    drawFilledEllipse(
      ctx,
      x - fx * radius * 0.35,
      y - fy * radius * 0.35,
      radius * 0.7,
      radius * 0.38,
      facing + Math.PI / 2,
      fill,
      stroke,
      lineWidth,
    )
    drawFilledCircle(
      ctx,
      x + fx * radius * 0.35,
      y + fy * radius * 0.35,
      radius * 0.4,
      fill,
      stroke,
      lineWidth,
    )
    return
  }

  // round / grazer family
  drawFilledEllipse(
    ctx,
    x,
    y,
    radius * 0.88,
    radius * 0.72,
    facing,
    fill,
    stroke,
    lineWidth,
  )
  drawFilledCircle(
    ctx,
    x + px * radius * 0.42,
    y + py * radius * 0.42,
    radius * 0.4,
    fill,
    stroke,
    lineWidth,
  )
  drawFilledCircle(
    ctx,
    x - px * radius * 0.42,
    y - py * radius * 0.42,
    radius * 0.4,
    fill,
    stroke,
    lineWidth,
  )
  drawFilledCircle(
    ctx,
    x + fx * radius * 0.28,
    y + fy * radius * 0.28,
    radius * 0.36,
    fill,
    stroke,
    lineWidth,
  )
}

function honeycombRowSizes(count: number): number[] {
  if (count <= 2) return [count]
  if (count === 3) return [2, 1]
  if (count === 4) return [2, 2]
  if (count === 5) return [3, 2]
  if (count === 6) return [3, 3]
  const rows: number[] = []
  let left = count
  while (left > 0) {
    const size = Math.min(3, left)
    rows.push(size)
    left -= size
  }
  return rows
}

/** Крупные глаза, брови и треугольный клюв по facing. */
export function drawComicFace(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
  options: ComicFaceOptions = {},
): void {
  const eyeScale = options.eyeScale ?? 1
  const beakScale = options.beakScale ?? 1
  const beakOpen = Math.max(0, Math.min(1, options.beakOpen ?? 0))
  const browAngle = options.browAngle ?? 0.35
  const eyeWhite = options.eyeWhite ?? '#ffffff'
  const pupilColor = options.pupilColor ?? '#0f172a'
  const beakFill = options.beakFill ?? '#fbbf24'
  const browColor = options.browColor ?? '#0f172a'
  const lookTarget = options.lookTarget ?? null

  const fx = Math.cos(facing)
  const fy = Math.sin(facing)
  const px = -fy
  const py = fx

  const faceX = x + fx * radius * 0.18
  const faceY = y + fy * radius * 0.18
  const eyeCount = Math.max(1, Math.round(options.eyeCount ?? 2))
  const rows = honeycombRowSizes(eyeCount)
  const baseEyeR = Math.max(2, radius * 0.22 * eyeScale)
  const widest = Math.max(...rows)
  let eyeR = baseEyeR
  let eyeStep = eyeR * 2.25
  const maxAcross = radius * 1.45
  if (widest > 1) {
    const span = (widest - 1) * eyeStep + (rows.length > 1 ? eyeStep * 0.5 : 0)
    if (span > maxAcross) {
      eyeStep = maxAcross / (widest - 1 + (rows.length > 1 ? 0.5 : 0))
      eyeR = Math.max(1.4, eyeStep / 2.25)
    }
  }
  const rowGap = eyeR * 2.7
  const frontRow = -radius * 0.04
  const eyes: Array<{ x: number; y: number; across: number }> = []
  rows.forEach((rowSize, rowIndex) => {
    const along = frontRow - rowIndex * rowGap
    const stagger = rows.length > 1 && rowIndex % 2 === 1 ? eyeStep * 0.5 : 0
    const centerBias = rows.length > 1 ? eyeStep * 0.25 : 0
    const rowStart = -((rowSize - 1) * eyeStep) / 2 + stagger - centerBias
    for (let index = 0; index < rowSize; index += 1) {
      const across = rowStart + index * eyeStep
      eyes.push({
        x: faceX + px * across + fx * along,
        y: faceY + py * across + fy * along,
        across,
      })
    }
  })

  for (const eye of eyes) {
    const lookAngle = lookTarget
      ? Math.atan2(lookTarget.y - eye.y, lookTarget.x - eye.x)
      : facing
    drawOneComicEye(ctx, eye.x, eye.y, eyeR, lookAngle, eyeWhite, pupilColor)
  }

  ctx.save()
  ctx.strokeStyle = browColor
  ctx.lineWidth = Math.max(1.4, eyeR * 0.22)
  ctx.lineCap = 'round'
  for (const eye of eyes) {
    const side = eye.across < -eyeStep * 0.2 ? 1 : eye.across > eyeStep * 0.2 ? -1 : 0
    const browBaseX = eye.x - fy * eyeR * 1.15
    const browBaseY = eye.y + fx * eyeR * 1.15
    const alongX = px * side
    const alongY = py * side
    const lift = browAngle * side
    ctx.beginPath()
    ctx.moveTo(
      browBaseX - alongX * eyeR * 0.85 + fx * lift * eyeR * 0.15,
      browBaseY - alongY * eyeR * 0.85 + fy * lift * eyeR * 0.15,
    )
    ctx.quadraticCurveTo(
      browBaseX + fx * eyeR * 0.12,
      browBaseY + fy * eyeR * 0.12,
      browBaseX + alongX * eyeR * 0.85 - fx * lift * eyeR * 0.1,
      browBaseY + alongY * eyeR * 0.85 - fy * lift * eyeR * 0.1,
    )
    ctx.stroke()
  }
  ctx.restore()

  const beakTip = radius * (0.62 + 0.16 * beakScale)
  const beakBase = radius * (0.28 + 0.06 * beakScale)
  const beakRootX = faceX + fx * radius * 0.34
  const beakRootY = faceY + fy * radius * 0.34
  const gap = radius * 0.42 * beakOpen
  const jawStroke = Math.max(1.2, radius * 0.05)

  const upperOuterX = beakRootX + px * (beakBase + gap)
  const upperOuterY = beakRootY + py * (beakBase + gap)
  const upperInnerX = beakRootX + px * gap * 0.35
  const upperInnerY = beakRootY + py * gap * 0.35
  const upperTipX = beakRootX + fx * beakTip + px * gap
  const upperTipY = beakRootY + fy * beakTip + py * gap
  const lowerOuterX = beakRootX - px * (beakBase + gap)
  const lowerOuterY = beakRootY - py * (beakBase + gap)
  const lowerInnerX = beakRootX - px * gap * 0.35
  const lowerInnerY = beakRootY - py * gap * 0.35
  const lowerTipX = beakRootX + fx * beakTip - px * gap
  const lowerTipY = beakRootY + fy * beakTip - py * gap

  if (beakOpen > 0.08) {
    ctx.beginPath()
    ctx.moveTo(upperInnerX, upperInnerY)
    ctx.lineTo(upperTipX, upperTipY)
    ctx.lineTo(lowerTipX, lowerTipY)
    ctx.lineTo(lowerInnerX, lowerInnerY)
    ctx.closePath()
    ctx.fillStyle = '#7f1d1d'
    ctx.fill()
  }

  drawBeakJaw(ctx, upperTipX, upperTipY, upperOuterX, upperOuterY, upperInnerX, upperInnerY, beakFill, jawStroke)
  drawBeakJaw(ctx, lowerTipX, lowerTipY, lowerOuterX, lowerOuterY, lowerInnerX, lowerInnerY, beakFill, jawStroke)

  if (beakOpen > 0.12) {
    const toothLen = radius * (0.14 + 0.1 * beakOpen)
    const toothCount = 3
    drawBeakTeeth(ctx, upperInnerX, upperInnerY, upperTipX, upperTipY, -px, -py, toothLen, toothCount)
    drawBeakTeeth(ctx, lowerInnerX, lowerInnerY, lowerTipX, lowerTipY, px, py, toothLen, toothCount)
  }
}

/**
 * Ноги строго по бокам и зеркально: левая и правая одной длины.
 * Пары равномерно стоят вдоль тела. `wag` от -1 до 1 качает пару вперёд-назад, не ломая зеркало.
 * `reachScale` < 1 — короткие культи перка «нога».
 */
export function drawComicPaws(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
  fill: string,
  wag: number,
  count = 2,
  reachScale = 1,
  bulk = 1,
): void {
  const pairs = Math.floor(count / 2)
  if (pairs <= 0) return

  const fx = Math.cos(facing)
  const fy = Math.sin(facing)
  const px = -fy
  const py = fx
  const span = 0.7
  const lineWidth = Math.max(1.5, radius * (0.12 - Math.min(pairs - 1, 2) * 0.012) * bulk)
  const footR = Math.max(1.5, radius * 0.08 * bulk * Math.min(1, 0.75 + reachScale * 0.25))
  const outward = 0.72 * reachScale * bulk

  ctx.save()
  ctx.lineCap = 'round'
  for (let pair = 0; pair < pairs; pair += 1) {
    const centered = pairs === 1 ? 0 : pair / (pairs - 1) - 0.5
    const along = centered * span
    const swing = wag * (pair % 2 === 0 ? 1 : -1) * 0.14
    for (const side of [-1, 1]) {
      const rootX = x + fx * radius * along + px * side * radius * 0.55
      const rootY = y + fy * radius * along + py * side * radius * 0.55
      const tipX = rootX + px * side * radius * outward + fx * radius * swing
      const tipY = rootY + py * side * radius * outward + fy * radius * swing
      ctx.beginPath()
      ctx.moveTo(rootX, rootY)
      ctx.lineTo(tipX, tipY)
      ctx.strokeStyle = 'rgba(15, 23, 42, 0.55)'
      ctx.lineWidth = lineWidth + 1.4 * bulk
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(rootX, rootY)
      ctx.lineTo(tipX, tipY)
      ctx.strokeStyle = fill
      ctx.lineWidth = lineWidth
      ctx.stroke()
      ctx.beginPath()
      ctx.arc(tipX, tipY, footR, 0, Math.PI * 2)
      ctx.fillStyle = fill
      ctx.fill()
      ctx.strokeStyle = 'rgba(15, 23, 42, 0.45)'
      ctx.lineWidth = 1.2
      ctx.stroke()
    }
  }
  ctx.restore()
}

function drawBeakJaw(
  ctx: CanvasRenderingContext2D,
  tipX: number,
  tipY: number,
  outerX: number,
  outerY: number,
  innerX: number,
  innerY: number,
  fill: string,
  lineWidth: number,
): void {
  ctx.beginPath()
  ctx.moveTo(tipX, tipY)
  ctx.lineTo(outerX, outerY)
  ctx.lineTo(innerX, innerY)
  ctx.closePath()
  ctx.fillStyle = fill
  ctx.fill()
  ctx.strokeStyle = '#b45309'
  ctx.lineWidth = lineWidth
  ctx.stroke()
}

function drawBeakTeeth(
  ctx: CanvasRenderingContext2D,
  fromX: number,
  fromY: number,
  toX: number,
  toY: number,
  inwardX: number,
  inwardY: number,
  toothLen: number,
  count: number,
): void {
  const alongX = toX - fromX
  const alongY = toY - fromY
  const edge = Math.hypot(alongX, alongY)
  if (edge < 1 || count <= 0) return
  const tx = alongX / edge
  const ty = alongY / edge
  const half = toothLen * 0.72
  ctx.fillStyle = '#fff7ed'
  ctx.strokeStyle = '#9a3412'
  ctx.lineWidth = Math.max(0.6, toothLen * 0.18)
  for (let index = 0; index < count; index += 1) {
    const t = (index + 0.5) / count
    const baseX = fromX + alongX * t
    const baseY = fromY + alongY * t
    ctx.beginPath()
    ctx.moveTo(baseX - tx * half, baseY - ty * half)
    ctx.lineTo(baseX + tx * half, baseY + ty * half)
    ctx.lineTo(baseX + inwardX * toothLen, baseY + inwardY * toothLen)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()
  }
}

function drawOneComicEye(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  eyeR: number,
  lookAngle: number,
  eyeWhite: string,
  pupilColor: string,
): void {
  ctx.beginPath()
  ctx.arc(x, y, eyeR, 0, Math.PI * 2)
  ctx.fillStyle = eyeWhite
  ctx.fill()
  ctx.strokeStyle = pupilColor
  ctx.lineWidth = Math.max(1.2, eyeR * 0.12)
  ctx.stroke()

  const pupilR = eyeR * 0.48
  const pupilOffset = eyeR * 0.32
  ctx.beginPath()
  ctx.arc(
    x + Math.cos(lookAngle) * pupilOffset,
    y + Math.sin(lookAngle) * pupilOffset,
    pupilR,
    0,
    Math.PI * 2,
  )
  ctx.fillStyle = pupilColor
  ctx.fill()

  ctx.beginPath()
  ctx.arc(
    x + Math.cos(lookAngle) * pupilOffset - eyeR * 0.18,
    y + Math.sin(lookAngle) * pupilOffset - eyeR * 0.18,
    pupilR * 0.28,
    0,
    Math.PI * 2,
  )
  ctx.fillStyle = '#ffffff'
  ctx.fill()
}

export function comicBodyStyleForEnemyKind(kind: string | undefined): ComicBodyStyle {
  const enemyKind = kind ?? 'grazer'
  if (
    enemyKind === 'hunter' ||
    enemyKind === 'rat' ||
    enemyKind === 'leech_fish' ||
    enemyKind === 'chlorine' ||
    enemyKind === 'crab'
  ) {
    return 'hunter'
  }
  if (
    enemyKind === 'lurker' ||
    enemyKind === 'roach' ||
    enemyKind === 'stoneback' ||
    enemyKind === 'filter' ||
    enemyKind === 'jelly'
  ) {
    return 'lurker'
  }
  return 'round'
}
