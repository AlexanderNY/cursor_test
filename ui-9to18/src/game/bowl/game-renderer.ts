import { formatPerkLevels } from './perks'
import { heroStrokeColor } from './hero-colors'
import type { RenderState } from './types'

export function drawGameFrame(
  ctx: CanvasRenderingContext2D,
  state: RenderState,
  viewportWidth: number,
  viewportHeight: number,
): void {
  ctx.clearRect(0, 0, viewportWidth, viewportHeight)
  ctx.fillStyle = '#dce4ef'
  ctx.fillRect(0, 0, viewportWidth, viewportHeight)

  ctx.save()
  ctx.translate(-state.camera.x, -state.camera.y)

  drawWorldFloor(ctx, state.world.width, state.world.height)

  if (state.level >= 1) {
    drawToiletBowl(ctx, state.bowl)
  }

  for (const obstacle of state.obstacles) {
    drawObstacle(ctx, obstacle)
  }

  for (const pickup of state.pickups) {
    drawPickup(ctx, pickup)
  }

  for (const enemy of state.enemies) {
    if (enemy.is_boss) {
      drawBoss(ctx, enemy, state.player.x, state.player.y)
    } else {
      drawEnemy(ctx, enemy)
    }
  }

  if (state.phase === 'whirlpool') {
    drawWhirlpool(ctx, state)
  }

  drawPlayer(ctx, state.player)
  ctx.restore()

  drawFogOfWar(ctx, state, viewportWidth, viewportHeight)
}

function drawWorldFloor(
  ctx: CanvasRenderingContext2D,
  worldWidth: number,
  worldHeight: number,
): void {
  ctx.fillStyle = '#e8eef5'
  ctx.fillRect(0, 0, worldWidth, worldHeight)

  ctx.strokeStyle = 'rgba(148, 163, 184, 0.22)'
  ctx.lineWidth = 1
  const gridStep = 80
  for (let x = 0; x <= worldWidth; x += gridStep) {
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, worldHeight)
    ctx.stroke()
  }
  for (let y = 0; y <= worldHeight; y += gridStep) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(worldWidth, y)
    ctx.stroke()
  }
}

function drawToiletBowl(
  ctx: CanvasRenderingContext2D,
  bowl: { cx: number; cy: number; rx: number; ry: number },
): void {
  const { cx, cy, rx, ry } = bowl
  const outerRx = rx + 48
  const outerRy = ry + 48

  ctx.save()
  ctx.beginPath()
  ctx.ellipse(cx, cy, outerRx, outerRy, 0, 0, Math.PI * 2)
  ctx.fillStyle = '#cbd5e1'
  ctx.fill()
  ctx.strokeStyle = '#94a3b8'
  ctx.lineWidth = 8
  ctx.stroke()

  ctx.beginPath()
  ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2)
  ctx.fillStyle = '#1e4d7a'
  ctx.fill()

  const waterGrad = ctx.createRadialGradient(cx, cy - ry * 0.15, rx * 0.1, cx, cy, rx)
  waterGrad.addColorStop(0, 'rgba(96, 165, 250, 0.55)')
  waterGrad.addColorStop(0.55, 'rgba(37, 99, 168, 0.75)')
  waterGrad.addColorStop(1, 'rgba(15, 45, 82, 0.95)')
  ctx.fillStyle = waterGrad
  ctx.fill()

  ctx.strokeStyle = 'rgba(191, 219, 254, 0.25)'
  ctx.lineWidth = 2
  ctx.stroke()

  ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)'
  ctx.lineWidth = 1
  for (let ring = 0.25; ring <= 0.85; ring += 0.15) {
    ctx.beginPath()
    ctx.ellipse(cx, cy, rx * ring, ry * ring, 0, 0, Math.PI * 2)
    ctx.stroke()
  }

  ctx.restore()
}

function drawObstacle(
  ctx: CanvasRenderingContext2D,
  obstacle: RenderState['obstacles'][number],
): void {
  const { x, y, kind, angle, width, height } = obstacle

  ctx.save()
  ctx.translate(x, y)
  ctx.rotate(angle)

  if (kind === 'paper') {
    ctx.fillStyle = '#f8fafc'
    ctx.strokeStyle = '#cbd5e1'
    ctx.lineWidth = 1.5
    ctx.fillRect(-width / 2, -height / 2, width, height)
    ctx.strokeRect(-width / 2, -height / 2, width, height)
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.5)'
    ctx.beginPath()
    ctx.moveTo(-width * 0.15, -height * 0.3)
    ctx.lineTo(width * 0.2, -height * 0.1)
    ctx.stroke()
  } else {
    ctx.fillStyle = '#e2e8f0'
    ctx.fillRect(-width * 0.35, -height * 0.15, width * 0.7, height * 0.3)
    ctx.fillStyle = '#38bdf8'
    for (let i = 0; i < 5; i += 1) {
      ctx.fillRect(-width * 0.45 + i * 5, -height * 0.35, 3, height * 0.25)
    }
    ctx.fillStyle = '#94a3b8'
    ctx.beginPath()
    ctx.arc(width * 0.28, 0, height * 0.22, 0, Math.PI * 2)
    ctx.fill()
  }

  ctx.restore()
}

function drawPickup(
  ctx: CanvasRenderingContext2D,
  pickup: RenderState['pickups'][number],
): void {
  const { x, y, radius, kind, spike_angle: spikeAngle } = pickup
  const color = kind === 'green' ? '#34d399' : '#f87171'

  ctx.beginPath()
  ctx.arc(x, y, radius, 0, Math.PI * 2)
  ctx.fillStyle = color
  ctx.fill()
  ctx.strokeStyle = kind === 'green' ? '#86efac' : '#fca5a5'
  ctx.lineWidth = 2
  ctx.stroke()

  if (kind === 'green') {
    drawTinyLegs(ctx, x, y, radius + 2)
  } else {
    drawPickupSpike(ctx, x, y, radius, spikeAngle)
  }
}

function drawTinyLegs(ctx: CanvasRenderingContext2D, x: number, y: number, offset: number): void {
  ctx.strokeStyle = '#6ee7b7'
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  for (const side of [-1, 1]) {
    ctx.beginPath()
    ctx.moveTo(x + side * 3, y + 2)
    ctx.lineTo(x + side * offset * 0.55, y + offset * 0.85)
    ctx.stroke()
  }
}

function drawPickupSpike(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  angle: number,
): void {
  const tipX = x + Math.cos(angle) * (radius + 7)
  const tipY = y + Math.sin(angle) * (radius + 7)
  const baseAngle1 = angle + Math.PI * 0.75
  const baseAngle2 = angle - Math.PI * 0.75
  const base1X = x + Math.cos(baseAngle1) * radius * 0.55
  const base1Y = y + Math.sin(baseAngle1) * radius * 0.55
  const base2X = x + Math.cos(baseAngle2) * radius * 0.55
  const base2Y = y + Math.sin(baseAngle2) * radius * 0.55

  ctx.beginPath()
  ctx.moveTo(tipX, tipY)
  ctx.lineTo(base1X, base1Y)
  ctx.lineTo(base2X, base2Y)
  ctx.closePath()
  ctx.fillStyle = '#ef4444'
  ctx.fill()
}

function drawWhirlpool(
  ctx: CanvasRenderingContext2D,
  state: RenderState,
): void {
  const { cx, cy } = state.bowl
  const radius = state.whirlpool_radius
  const angle = state.whirlpool_angle
  const progress = 1 - state.whirlpool_time_left / Math.max(state.whirlpool_duration, 0.001)

  ctx.save()
  ctx.translate(cx, cy)
  ctx.rotate(angle)

  const grad = ctx.createRadialGradient(0, 0, radius * 0.1, 0, 0, radius)
  grad.addColorStop(0, 'rgba(15, 23, 42, 0.95)')
  grad.addColorStop(0.45, 'rgba(30, 64, 175, 0.75)')
  grad.addColorStop(1, 'rgba(96, 165, 250, 0.15)')
  ctx.beginPath()
  ctx.arc(0, 0, radius, 0, Math.PI * 2)
  ctx.fillStyle = grad
  ctx.fill()

  ctx.strokeStyle = 'rgba(191, 219, 254, 0.55)'
  ctx.lineWidth = 3
  for (let arm = 0; arm < 5; arm += 1) {
    ctx.beginPath()
    const startAngle = (Math.PI * 2 * arm) / 5
    for (let step = 0; step <= 24; step += 1) {
      const t = step / 24
      const spiralAngle = startAngle + t * Math.PI * 3.5
      const spiralRadius = radius * (1 - t * 0.85)
      const px = Math.cos(spiralAngle) * spiralRadius
      const py = Math.sin(spiralAngle) * spiralRadius
      if (step === 0) ctx.moveTo(px, py)
      else ctx.lineTo(px, py)
    }
    ctx.stroke()
  }

  ctx.fillStyle = '#0f172a'
  ctx.beginPath()
  ctx.arc(0, 0, radius * (0.12 + progress * 0.08), 0, Math.PI * 2)
  ctx.fill()

  ctx.restore()
}

function drawBoss(
  ctx: CanvasRenderingContext2D,
  enemy: RenderState['enemies'][number],
  playerX: number,
  playerY: number,
): void {
  const { x, y, radius } = enemy
  const facing = Math.atan2(playerY - y, playerX - x)

  drawTentacles(ctx, x, y, radius, facing)
  drawLegs(ctx, x, y, radius, facing)
  drawPlayerSpike(ctx, x, y, radius, facing)

  ctx.beginPath()
  ctx.arc(x, y, radius, 0, Math.PI * 2)
  ctx.fillStyle = '#dc2626'
  ctx.fill()
  ctx.strokeStyle = '#fca5a5'
  ctx.lineWidth = 4
  ctx.stroke()

  drawEyes(ctx, x, y, facing)

  ctx.fillStyle = '#fee2e2'
  ctx.font = 'bold 14px Segoe UI, system-ui, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('BOSS', x, y - radius - 10)
  ctx.textAlign = 'start'
}

function drawEnemy(
  ctx: CanvasRenderingContext2D,
  enemy: RenderState['enemies'][number],
): void {
  const { x, y, radius, state, health, max_health: maxHealth } = enemy
  ctx.beginPath()
  ctx.arc(x, y, radius, 0, Math.PI * 2)
  const fill =
    state === 'cooldown' ? '#64748b' : state === 'flee' ? '#fbbf24' : state === 'chase' ? '#c084fc' : '#a78bfa'
  ctx.fillStyle = fill
  ctx.fill()
  if (state === 'chase' || enemy.is_boss) {
    ctx.strokeStyle = '#f472b6'
    ctx.lineWidth = 3
    ctx.stroke()
  }

  const hpRatio = maxHealth > 0 ? Math.max(0, health / maxHealth) : 1
  const barW = radius * 1.6
  ctx.fillStyle = 'rgba(0,0,0,0.45)'
  ctx.fillRect(x - barW / 2, y - radius - 8, barW, 4)
  ctx.fillStyle = hpRatio > 0.35 ? '#34d399' : '#f87171'
  ctx.fillRect(x - barW / 2, y - radius - 8, barW * hpRatio, 4)
}

function drawPlayer(
  ctx: CanvasRenderingContext2D,
  player: RenderState['player'],
): void {
  const { x, y, radius, perks = [], facing_angle: facing, color } = player
  const fill = color ?? '#60a5fa'
  const stroke = heroStrokeColor(fill)

  if (perks.includes('tentacle')) {
    drawTentacles(ctx, x, y, radius, facing)
  }
  if (perks.includes('leg')) {
    drawLegs(ctx, x, y, radius, facing)
  }
  if (perks.includes('spike')) {
    drawPlayerSpike(ctx, x, y, radius, facing)
  }

  ctx.beginPath()
  ctx.arc(x, y, radius, 0, Math.PI * 2)
  ctx.fillStyle = fill
  ctx.fill()
  ctx.strokeStyle = stroke
  ctx.lineWidth = 2
  ctx.stroke()

  if (perks.includes('eye')) {
    drawEyes(ctx, x, y, facing)
  }
}

function drawLegs(ctx: CanvasRenderingContext2D, x: number, y: number, radius: number, facing: number): void {
  ctx.save()
  ctx.translate(x, y)
  ctx.rotate(facing)
  ctx.strokeStyle = '#93c5fd'
  ctx.lineWidth = 3
  ctx.lineCap = 'round'
  for (const side of [-1, 1]) {
    ctx.beginPath()
    ctx.moveTo(side * radius * 0.55, radius * 0.15)
    ctx.lineTo(side * radius * 0.95, radius * 0.75)
    ctx.stroke()
  }
  ctx.restore()
}

function drawEyes(ctx: CanvasRenderingContext2D, x: number, y: number, facing: number): void {
  ctx.save()
  ctx.translate(x, y)
  ctx.rotate(facing)
  ctx.fillStyle = '#ffffff'
  for (const side of [-1, 1]) {
    ctx.beginPath()
    ctx.arc(side * 5, -2, 3.2, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = '#0f172a'
    ctx.beginPath()
    ctx.arc(side * 5 + 1, -2, 1.4, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = '#ffffff'
  }
  ctx.restore()
}

function drawTentacles(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
): void {
  ctx.save()
  ctx.translate(x, y)
  ctx.rotate(facing)
  ctx.strokeStyle = '#c084fc'
  ctx.lineWidth = 2.5
  ctx.lineCap = 'round'
  for (const side of [-1, 1]) {
    ctx.beginPath()
    ctx.moveTo(side * radius * 0.5, -radius * 0.1)
    ctx.quadraticCurveTo(side * radius * 1.2, -radius * 0.45, side * radius * 0.85, -radius * 0.75)
    ctx.stroke()
  }
  ctx.restore()
}

function drawPlayerSpike(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
): void {
  const tipX = x + Math.cos(facing) * (radius + 12)
  const tipY = y + Math.sin(facing) * (radius + 12)
  const leftX = x + Math.cos(facing + 2.4) * radius * 0.5
  const leftY = y + Math.sin(facing + 2.4) * radius * 0.5
  const rightX = x + Math.cos(facing - 2.4) * radius * 0.5
  const rightY = y + Math.sin(facing - 2.4) * radius * 0.5

  ctx.beginPath()
  ctx.moveTo(tipX, tipY)
  ctx.lineTo(leftX, leftY)
  ctx.lineTo(rightX, rightY)
  ctx.closePath()
  ctx.fillStyle = '#fbbf24'
  ctx.fill()
  ctx.strokeStyle = '#fde68a'
  ctx.lineWidth = 1
  ctx.stroke()
}

function drawFogOfWar(
  ctx: CanvasRenderingContext2D,
  state: RenderState,
  viewportWidth: number,
  viewportHeight: number,
): void {
  const screenX = state.player.x - state.camera.x
  const screenY = state.player.y - state.camera.y
  const radius = state.visibility_radius
  const fogAlpha = 0.55
  const softEdge = 32

  ctx.save()

  // Туман поверх мира, «дыра» через even-odd — мир под кругом не затрагивается
  ctx.fillStyle = `rgba(15, 23, 42, ${fogAlpha})`
  ctx.beginPath()
  ctx.rect(0, 0, viewportWidth, viewportHeight)
  ctx.arc(screenX, screenY, radius, 0, Math.PI * 2, true)
  ctx.fill('evenodd')

  // Мягкий переход на границе круга (только кольцо снаружи)
  const edgeGradient = ctx.createRadialGradient(
    screenX,
    screenY,
    radius,
    screenX,
    screenY,
    radius + softEdge,
  )
  edgeGradient.addColorStop(0, 'rgba(15, 23, 42, 0)')
  edgeGradient.addColorStop(0.65, `rgba(15, 23, 42, ${fogAlpha * 0.35})`)
  edgeGradient.addColorStop(1, `rgba(15, 23, 42, ${fogAlpha})`)
  ctx.fillStyle = edgeGradient
  ctx.beginPath()
  ctx.arc(screenX, screenY, radius + softEdge, 0, Math.PI * 2)
  ctx.arc(screenX, screenY, radius, 0, Math.PI * 2, true)
  ctx.fill('evenodd')

  ctx.strokeStyle = 'rgba(100, 116, 139, 0.28)'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.arc(screenX, screenY, radius, 0, Math.PI * 2)
  ctx.stroke()

  ctx.restore()
}

export function drawHudBars(
  ctx: CanvasRenderingContext2D,
  state: RenderState,
  viewportWidth: number,
): void {
  const { red, green, weight, perks = [], radius } = state.player
  const barWidth = Math.min(240, viewportWidth - 32)
  const x = 16
  const top = 16
  const height = 14
  const gap = 10
  const maxStat = Math.max(50, red, green, 1)

  drawBar(ctx, x, top, barWidth, height, red / maxStat, '#f87171', 'Красная')
  drawBar(ctx, x, top + height + gap, barWidth, height, green / maxStat, '#34d399', 'Зелёная')

  ctx.fillStyle = '#ffffff'
  ctx.font = '600 14px Segoe UI, system-ui, sans-serif'
  ctx.fillText(`Вес: ${Math.round(weight)} · R ${Math.round(radius)}px`, x, top + (height + gap) * 2 + 18)
  ctx.fillStyle = '#e2e8f0'
  ctx.font = '12px Segoe UI, system-ui, sans-serif'
  const perkText = formatPerkLevels(state.player.perk_levels ?? {})
  ctx.fillText(`Уровень ${state.level} · ${perkText}`, x, top + (height + gap) * 2 + 36)
  ctx.fillText(
    `Врагов съедено: ${state.enemies_eaten_mod}/${state.enemies_per_perk} (всего ${state.enemies_eaten})`,
    x,
    top + (height + gap) * 2 + 52,
  )
  ctx.fillStyle = '#cbd5e1'
  ctx.fillText(
    `Обзор: ${Math.round(state.visibility_radius)}px`,
    x,
    top + (height + gap) * 2 + 68,
  )

  drawMatchTimer(ctx, state, viewportWidth, x, top + (height + gap) * 2 + 88)

  if (perks.includes('tentacle') || perks.includes('spike')) {
    ctx.fillText('Space — способность', x, top + (height + gap) * 2 + 112)
  }
}

function formatTimer(seconds: number): string {
  const total = Math.max(0, Math.ceil(seconds))
  const minutes = Math.floor(total / 60)
  const secs = total % 60
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

function drawMatchTimer(
  ctx: CanvasRenderingContext2D,
  state: RenderState,
  viewportWidth: number,
  statusX: number,
  statusY: number,
): void {
  const phase = state.phase ?? 'normal'
  const matchTotal = state.match_timer_total ?? 120
  const matchElapsed = state.match_timer ?? 0
  const whirlpoolLeft = state.whirlpool_time_left ?? 0
  const remaining = Math.max(0, matchTotal - matchElapsed)
  const label =
    phase === 'whirlpool'
      ? `Водоворот: ${formatTimer(whirlpoolLeft)}`
      : phase === 'boss'
        ? 'БОСС!'
        : `До водоворота: ${formatTimer(remaining)}`

  ctx.font = '700 16px Segoe UI, system-ui, sans-serif'
  const textWidth = ctx.measureText(label).width + 24
  const boxX = (viewportWidth - textWidth) / 2
  const boxY = 12

  ctx.fillStyle =
    phase === 'whirlpool'
      ? 'rgba(37, 99, 235, 0.92)'
      : phase === 'boss'
        ? 'rgba(220, 38, 38, 0.92)'
        : 'rgba(15, 23, 42, 0.92)'
  ctx.fillRect(boxX, boxY, textWidth, 34)
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)'
  ctx.strokeRect(boxX, boxY, textWidth, 34)

  ctx.fillStyle = '#f8fafc'
  ctx.textAlign = 'center'
  ctx.fillText(label, boxX + textWidth / 2, boxY + 22)
  ctx.textAlign = 'start'

  if (phase === 'normal') {
    ctx.fillStyle = '#dbe4ef'
    ctx.font = '12px Segoe UI, system-ui, sans-serif'
    ctx.fillText('Обратный отсчёт до водоворота', statusX, statusY)
  } else if (phase === 'whirlpool') {
    ctx.fillStyle = '#93c5fd'
    ctx.font = '12px Segoe UI, system-ui, sans-serif'
    ctx.fillText('Предметы в центр · живое — от центра', statusX, statusY)
  } else {
    ctx.fillStyle = '#fca5a5'
    ctx.font = '12px Segoe UI, system-ui, sans-serif'
    ctx.fillText('Босс со всеми перками преследует героя', statusX, statusY)
  }
}

function drawBar(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  ratio: number,
  color: string,
  label: string,
): void {
  ctx.fillStyle = 'rgba(255, 255, 255, 0.16)'
  ctx.fillRect(x, y, width, height)

  ctx.fillStyle = color
  ctx.fillRect(x, y, width * Math.min(Math.max(ratio, 0), 1), height)

  ctx.strokeStyle = 'rgba(255, 255, 255, 0.35)'
  ctx.strokeRect(x, y, width, height)

  ctx.fillStyle = '#e2e8f0'
  ctx.font = '12px Segoe UI, system-ui, sans-serif'
  ctx.fillText(label, x, y - 4)
}
