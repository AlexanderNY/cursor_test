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
    const lobe = radius * 0.58
    const sep = radius * 0.5
    drawFilledCircle(ctx, x - fx * sep, y - fy * sep, lobe, fill, stroke, lineWidth)
    drawFilledCircle(ctx, x + fx * sep, y + fy * sep, lobe, fill, stroke, lineWidth)
    drawFilledEllipse(
      ctx,
      x - fx * radius * 0.08,
      y - fy * radius * 0.08,
      radius * 0.42,
      radius * 0.34,
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
  const eyeR = Math.max(3.2, radius * 0.32 * eyeScale)
  const eyeGap = radius * 0.34
  const eyeForward = radius * 0.08

  const leftX = faceX + px * eyeGap * 0.5 + fx * eyeForward
  const leftY = faceY + py * eyeGap * 0.5 + fy * eyeForward
  const rightX = faceX - px * eyeGap * 0.5 + fx * eyeForward
  const rightY = faceY - py * eyeGap * 0.5 + fy * eyeForward

  const lookAngleLeft = lookTarget
    ? Math.atan2(lookTarget.y - leftY, lookTarget.x - leftX)
    : facing
  const lookAngleRight = lookTarget
    ? Math.atan2(lookTarget.y - rightY, lookTarget.x - rightX)
    : facing

  drawOneComicEye(ctx, leftX, leftY, eyeR, lookAngleLeft, eyeWhite, pupilColor)
  drawOneComicEye(ctx, rightX, rightY, eyeR, lookAngleRight, eyeWhite, pupilColor)

  // Brows
  ctx.save()
  ctx.strokeStyle = browColor
  ctx.lineWidth = Math.max(1.8, radius * 0.08)
  ctx.lineCap = 'round'
  for (const [ex, ey, side] of [
    [leftX, leftY, 1],
    [rightX, rightY, -1],
  ] as const) {
    const browBaseX = ex - fy * eyeR * 1.15
    const browBaseY = ey + fx * eyeR * 1.15
    const along = px * side
    const alongY = py * side
    const lift = browAngle * side
    ctx.beginPath()
    ctx.moveTo(
      browBaseX - along * eyeR * 0.85 + fx * lift * eyeR * 0.15,
      browBaseY - alongY * eyeR * 0.85 + fy * lift * eyeR * 0.15,
    )
    ctx.quadraticCurveTo(
      browBaseX + fx * eyeR * 0.12,
      browBaseY + fy * eyeR * 0.12,
      browBaseX + along * eyeR * 0.85 - fx * lift * eyeR * 0.1,
      browBaseY + alongY * eyeR * 0.85 - fy * lift * eyeR * 0.1,
    )
    ctx.stroke()
  }
  ctx.restore()

  const beakTip = radius * (0.55 + 0.2 * beakScale)
  const beakBase = radius * (0.22 + 0.08 * beakScale)
  const beakRootX = faceX + fx * radius * 0.22
  const beakRootY = faceY + fy * radius * 0.22
  const tipX = beakRootX + fx * beakTip
  const tipY = beakRootY + fy * beakTip
  const gap = radius * 0.28 * beakOpen
  const jawStroke = Math.max(1.2, radius * 0.05)

  if (beakOpen > 0.08) {
    ctx.beginPath()
    ctx.moveTo(tipX - fx * gap * 0.35, tipY - fy * gap * 0.35)
    ctx.lineTo(beakRootX + px * beakBase * 0.55, beakRootY + py * beakBase * 0.55)
    ctx.lineTo(beakRootX - px * beakBase * 0.55, beakRootY - py * beakBase * 0.55)
    ctx.closePath()
    ctx.fillStyle = '#7f1d1d'
    ctx.fill()
  }

  const upperTipX = tipX + px * gap * 0.15
  const upperTipY = tipY + py * gap * 0.15
  const lowerTipX = tipX - px * gap * 0.15
  const lowerTipY = tipY - py * gap * 0.15
  const upperLeftX = beakRootX + px * (beakBase + gap)
  const upperLeftY = beakRootY + py * (beakBase + gap)
  const upperRightX = beakRootX - px * beakBase * 0.35 + px * gap * 0.2
  const upperRightY = beakRootY - py * beakBase * 0.35 + py * gap * 0.2
  const lowerLeftX = beakRootX + px * beakBase * 0.35 - px * gap * 0.2
  const lowerLeftY = beakRootY + py * beakBase * 0.35 - py * gap * 0.2
  const lowerRightX = beakRootX - px * (beakBase + gap)
  const lowerRightY = beakRootY - py * (beakBase + gap)

  ctx.beginPath()
  ctx.moveTo(upperTipX, upperTipY)
  ctx.lineTo(upperLeftX, upperLeftY)
  ctx.lineTo(upperRightX, upperRightY)
  ctx.closePath()
  ctx.fillStyle = beakFill
  ctx.fill()
  ctx.strokeStyle = '#b45309'
  ctx.lineWidth = jawStroke
  ctx.stroke()

  ctx.beginPath()
  ctx.moveTo(lowerTipX, lowerTipY)
  ctx.lineTo(lowerLeftX, lowerLeftY)
  ctx.lineTo(lowerRightX, lowerRightY)
  ctx.closePath()
  ctx.fillStyle = beakFill
  ctx.fill()
  ctx.stroke()
}

/** Короткие лапки по бокам. `wag` от -1 до 1 качает их вдоль движения. */
export function drawComicPaws(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
  fill: string,
  wag: number,
): void {
  const fx = Math.cos(facing)
  const fy = Math.sin(facing)
  const px = -fy
  const py = fx
  const pairs = [
    { along: -0.22, reach: 0.62 },
    { along: 0.18, reach: 0.56 },
  ]
  ctx.save()
  for (let index = 0; index < pairs.length; index += 1) {
    const pair = pairs[index]
    const swing = wag * (index % 2 === 0 ? 1 : -1)
    for (const side of [-1, 1]) {
      const rootX = x + fx * radius * pair.along + px * side * radius * 0.36
      const rootY = y + fy * radius * pair.along + py * side * radius * 0.36
      const tipX = rootX + px * side * radius * pair.reach * 0.42 + fx * radius * swing * 0.22
      const tipY = rootY + py * side * radius * pair.reach * 0.42 + fy * radius * swing * 0.22
      ctx.beginPath()
      ctx.moveTo(rootX, rootY)
      ctx.lineTo(tipX, tipY)
      ctx.strokeStyle = fill
      ctx.lineWidth = Math.max(2.2, radius * 0.11)
      ctx.lineCap = 'round'
      ctx.stroke()
      ctx.beginPath()
      ctx.ellipse(tipX, tipY, radius * 0.13, radius * 0.09, facing, 0, Math.PI * 2)
      ctx.fillStyle = fill
      ctx.fill()
      ctx.strokeStyle = 'rgba(15, 23, 42, 0.35)'
      ctx.lineWidth = 1.2
      ctx.stroke()
    }
  }
  ctx.restore()
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
