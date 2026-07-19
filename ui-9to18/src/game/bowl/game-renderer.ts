import {
  formatPerkLevels,
  getPerkLevel,
  getPerkLimbCount,
  getSpikeDrawStats,
  isPerkDotsOnly,
  isPerkStub,
  isPerkWaves,
} from './perks'
import { drawHeroFigureEight, getHeroLobeLayout } from './hero-visual'
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

  for (const nutrient of state.nutrients ?? []) {
    drawNutrient(ctx, nutrient)
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

  if (state.exit_open && state.exit) {
    drawExitPortal(ctx, state.exit)
  }

  drawPlayer(ctx, state.player, state.pickups)
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
  bowl: { cx: number; cy: number; rx: number; ry: number; outer_rx?: number; outer_ry?: number; rim_margin?: number },
): void {
  const { cx, cy, rx, ry } = bowl
  const outerRx = bowl.outer_rx ?? rx + (bowl.rim_margin ?? 48)
  const outerRy = bowl.outer_ry ?? ry + (bowl.rim_margin ?? 48)

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
    drawPaperObstacle(ctx, width, height)
  } else {
    drawToothbrushObstacle(ctx, width, height)
  }

  ctx.restore()
}

function drawPaperObstacle(ctx: CanvasRenderingContext2D, width: number, height: number): void {
  const hw = width / 2
  const hh = height / 2
  const corner = Math.min(width, height) * 0.14

  ctx.save()
  ctx.translate(1.5, 2.5)
  ctx.globalAlpha = 0.22
  ctx.fillStyle = '#0f172a'
  ctx.beginPath()
  ctx.roundRect(-hw + 2, -hh + 2, width - 1, height - 1, corner)
  ctx.fill()
  ctx.restore()

  const bodyGrad = ctx.createLinearGradient(-hw, -hh, hw, hh)
  bodyGrad.addColorStop(0, '#ffffff')
  bodyGrad.addColorStop(0.45, '#f8fafc')
  bodyGrad.addColorStop(1, '#e2e8f0')

  ctx.fillStyle = bodyGrad
  ctx.strokeStyle = '#94a3b8'
  ctx.lineWidth = 1.25
  ctx.beginPath()
  ctx.roundRect(-hw, -hh, width, height, corner)
  ctx.fill()
  ctx.stroke()

  const fold = Math.min(width, height) * 0.28
  ctx.fillStyle = 'rgba(148, 163, 184, 0.35)'
  ctx.strokeStyle = 'rgba(100, 116, 139, 0.55)'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(hw - fold, -hh)
  ctx.lineTo(hw, -hh + fold)
  ctx.lineTo(hw - fold, -hh + fold)
  ctx.closePath()
  ctx.fill()
  ctx.stroke()

  ctx.strokeStyle = 'rgba(148, 163, 184, 0.45)'
  ctx.lineWidth = 1
  ctx.lineCap = 'round'
  const creases: Array<[number, number, number, number]> = [
    [-hw * 0.55, -hh * 0.15, hw * 0.05, hh * 0.2],
    [-hw * 0.35, hh * 0.05, hw * 0.35, hh * 0.35],
    [-hw * 0.1, -hh * 0.45, hw * 0.45, -hh * 0.05],
  ]
  for (const [x1, y1, x2, y2] of creases) {
    ctx.beginPath()
    ctx.moveTo(x1, y1)
    ctx.quadraticCurveTo((x1 + x2) / 2, (y1 + y2) / 2 + 2, x2, y2)
    ctx.stroke()
  }

  ctx.fillStyle = 'rgba(148, 163, 184, 0.18)'
  for (let row = 0; row < 3; row += 1) {
    const lineY = -hh * 0.15 + row * height * 0.18
    ctx.fillRect(-hw * 0.55, lineY, width * 0.42, 1.2)
  }
}

function drawToothbrushObstacle(ctx: CanvasRenderingContext2D, width: number, height: number): void {
  const hw = width / 2
  const hh = height / 2
  const handleW = width * 0.62
  const headW = width * 0.95
  const headLen = height * 0.24
  const neckLen = height * 0.1

  ctx.save()
  ctx.translate(1, 2)
  ctx.globalAlpha = 0.2
  ctx.fillStyle = '#0f172a'
  ctx.beginPath()
  ctx.roundRect(-handleW / 2 + 1, -hh + 3, handleW, height - 2, handleW / 2)
  ctx.fill()
  ctx.restore()

  const handleGrad = ctx.createLinearGradient(-handleW / 2, 0, handleW / 2, 0)
  handleGrad.addColorStop(0, '#0d9488')
  handleGrad.addColorStop(0.35, '#14b8a6')
  handleGrad.addColorStop(0.7, '#5eead4')
  handleGrad.addColorStop(1, '#0f766e')

  ctx.fillStyle = handleGrad
  ctx.strokeStyle = '#115e59'
  ctx.lineWidth = 1.2
  ctx.beginPath()
  ctx.roundRect(-handleW / 2, -hh + headLen + neckLen, handleW, height - headLen - neckLen, handleW / 2)
  ctx.fill()
  ctx.stroke()

  ctx.fillStyle = '#99f6e4'
  ctx.beginPath()
  ctx.ellipse(0, hh * 0.62, handleW * 0.16, handleW * 0.16, 0, 0, Math.PI * 2)
  ctx.fill()

  ctx.fillStyle = '#2dd4bf'
  ctx.strokeStyle = '#0f766e'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(-handleW * 0.34, -hh + headLen + neckLen)
  ctx.lineTo(-headW * 0.42, -hh + headLen)
  ctx.lineTo(headW * 0.42, -hh + headLen)
  ctx.lineTo(handleW * 0.34, -hh + headLen + neckLen)
  ctx.closePath()
  ctx.fill()
  ctx.stroke()

  const headGrad = ctx.createLinearGradient(0, -hh, 0, -hh + headLen)
  headGrad.addColorStop(0, '#f8fafc')
  headGrad.addColorStop(0.55, '#e2e8f0')
  headGrad.addColorStop(1, '#cbd5e1')

  ctx.fillStyle = headGrad
  ctx.strokeStyle = '#64748b'
  ctx.lineWidth = 1.1
  ctx.beginPath()
  ctx.roundRect(-headW / 2, -hh, headW, headLen, headW * 0.22)
  ctx.fill()
  ctx.stroke()

  ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)'
  ctx.lineWidth = 1.15
  ctx.lineCap = 'round'
  const bristleRows = 4
  const bristleCols = 5
  const bristleStartX = -headW * 0.36
  const bristleStartY = -hh + headLen * 0.22
  const bristleGapX = (headW * 0.72) / (bristleCols - 1)
  const bristleGapY = (headLen * 0.55) / (bristleRows - 1)
  for (let row = 0; row < bristleRows; row += 1) {
    for (let col = 0; col < bristleCols; col += 1) {
      const bx = bristleStartX + col * bristleGapX
      const by = bristleStartY + row * bristleGapY
      ctx.beginPath()
      ctx.moveTo(bx, by)
      ctx.lineTo(bx, by - headLen * 0.16)
      ctx.stroke()
    }
  }

  ctx.strokeStyle = 'rgba(15, 118, 110, 0.35)'
  ctx.lineWidth = 0.9
  ctx.beginPath()
  ctx.moveTo(-handleW * 0.18, -hh + headLen + neckLen * 0.35)
  ctx.lineTo(handleW * 0.18, -hh + headLen + neckLen * 0.35)
  ctx.stroke()
}

function drawNutrient(
  ctx: CanvasRenderingContext2D,
  nutrient: NonNullable<RenderState['nutrients']>[number],
): void {
  const { x, y, radius_x: radiusX, radius_y: radiusY, angle } = nutrient
  ctx.save()
  ctx.translate(x, y)
  ctx.rotate(angle)
  ctx.beginPath()
  ctx.ellipse(0, 0, radiusX, radiusY, 0, 0, Math.PI * 2)
  const grad = ctx.createRadialGradient(0, 0, Math.min(radiusX, radiusY) * 0.15, 0, 0, radiusX)
  grad.addColorStop(0, 'rgba(180, 120, 60, 0.55)')
  grad.addColorStop(0.55, 'rgba(120, 72, 32, 0.72)')
  grad.addColorStop(1, 'rgba(78, 48, 22, 0.85)')
  ctx.fillStyle = grad
  ctx.fill()
  ctx.strokeStyle = 'rgba(62, 38, 18, 0.55)'
  ctx.lineWidth = 2
  ctx.stroke()
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
    drawPickupLegs(ctx, x, y, radius, 6)
    drawSimpleDots(ctx, x, y, radius, 2, '#ecfdf5', '#065f46')
  } else {
    drawRedPickupSpikes(ctx, x, y, radius, spikeAngle)
    drawSimpleDots(ctx, x, y, radius, 2, '#fff1f2', '#7f1d1d')
  }
}

function drawSimpleDots(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  count: number,
  fill: string,
  stroke: string,
): void {
  const spacing = Math.min(radius * 0.45, 5)
  const startX = x - ((count - 1) * spacing) / 2
  for (let i = 0; i < count; i += 1) {
    const dotX = startX + i * spacing
    const dotY = y - radius * 0.12
    ctx.beginPath()
    ctx.arc(dotX, dotY, Math.max(1.6, radius * 0.16), 0, Math.PI * 2)
    ctx.fillStyle = fill
    ctx.fill()
    ctx.strokeStyle = stroke
    ctx.lineWidth = 1
    ctx.stroke()
  }
}

function drawPickupLegs(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  count: number,
): void {
  ctx.strokeStyle = '#6ee7b7'
  ctx.lineWidth = Math.max(1.5, radius * 0.14)
  ctx.lineCap = 'round'
  const pairs = Math.ceil(count / 2)
  for (let pair = 0; pair < pairs; pair += 1) {
    for (const side of [-1, 1]) {
      const index = pair * 2 + (side === 1 ? 1 : 0)
      if (index >= count) continue
      const along = -0.2 + (pair / Math.max(pairs - 1, 1)) * 0.45
      const spread = 0.45 + pair * 0.06
      ctx.beginPath()
      ctx.moveTo(x + side * radius * (0.22 + pair * 0.04), y + radius * along)
      ctx.lineTo(x + side * radius * spread, y + radius * (along + 0.42))
      ctx.stroke()
    }
  }
}

function drawRedPickupSpikes(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  angle: number,
): void {
  const spread = 0.28
  for (const offset of [-spread, spread]) {
    drawPickupSpike(ctx, x, y, radius, angle + offset)
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

function drawExitPortal(
  ctx: CanvasRenderingContext2D,
  exit: { x: number; y: number; radius: number },
): void {
  const { x, y, radius } = exit
  ctx.save()

  ctx.beginPath()
  ctx.arc(x, y, radius * 1.35, 0, Math.PI * 2)
  ctx.fillStyle = 'rgba(0, 0, 0, 0.22)'
  ctx.fill()

  const ring = ctx.createRadialGradient(x, y, radius * 0.2, x, y, radius)
  ring.addColorStop(0, '#000000')
  ring.addColorStop(0.55, '#0a0a0a')
  ring.addColorStop(0.85, '#1a1a1a')
  ring.addColorStop(1, 'rgba(30, 30, 30, 0.15)')
  ctx.beginPath()
  ctx.arc(x, y, radius, 0, Math.PI * 2)
  ctx.fillStyle = ring
  ctx.fill()

  ctx.strokeStyle = 'rgba(248, 250, 252, 0.55)'
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.arc(x, y, radius, 0, Math.PI * 2)
  ctx.stroke()

  ctx.strokeStyle = 'rgba(148, 163, 184, 0.35)'
  ctx.lineWidth = 1.5
  ctx.beginPath()
  ctx.arc(x, y, radius * 0.72, 0, Math.PI * 2)
  ctx.stroke()

  ctx.fillStyle = 'rgba(248, 250, 252, 0.85)'
  ctx.font = '700 13px Segoe UI, system-ui, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('ВЫХОД', x, y + 4)
  ctx.textAlign = 'start'

  ctx.restore()
}

function drawBoss(
  ctx: CanvasRenderingContext2D,
  enemy: RenderState['enemies'][number],
  playerX: number,
  playerY: number,
): void {
  const { x, y, radius, health, max_health: maxHealth, state, burst_left: burstLeft = 0 } = enemy
  const bossKind = enemy.boss_kind ?? 'titan'
  const palette = BOSS_KIND_PALETTE[bossKind] ?? BOSS_KIND_PALETTE.titan
  const facing = Math.atan2(playerY - y, playerX - x)
  const isDashing = bossKind === 'stalker' && burstLeft > 0

  if (bossKind === 'titan' || bossKind === 'swarm') {
    drawLegs(ctx, x, y, radius, facing, 2)
  }
  if (bossKind === 'stalker' || bossKind === 'vortex') {
    drawTentacles(ctx, x, y, radius, facing, 2, false)
  }
  if (bossKind === 'leech' || bossKind === 'titan') {
    drawPlayerSpike(ctx, x, y, radius, facing)
  }
  if (bossKind === 'vortex') {
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(facing + Math.PI / 2)
    ctx.strokeStyle = 'rgba(191, 219, 254, 0.55)'
    ctx.lineWidth = 2
    for (let ring = 0.35; ring <= 1.0; ring += 0.22) {
      ctx.beginPath()
      ctx.arc(0, 0, radius * ring, 0, Math.PI * 2)
      ctx.stroke()
    }
    ctx.restore()
  }

  ctx.beginPath()
  ctx.arc(x, y, radius, 0, Math.PI * 2)
  ctx.fillStyle = isDashing ? palette.dash : palette.fill
  ctx.fill()
  ctx.strokeStyle = state === 'chase' || isDashing ? palette.chaseStroke : palette.stroke
  ctx.lineWidth = isDashing ? 5 : 4
  ctx.stroke()

  if (bossKind === 'leech') {
    drawEyes(ctx, x, y, facing)
  }
  if (bossKind === 'swarm') {
    ctx.fillStyle = '#431407'
    for (let i = 0; i < 4; i += 1) {
      const dotAngle = facing + (Math.PI / 2) * i * 0.5
      ctx.beginPath()
      ctx.arc(x + Math.cos(dotAngle) * radius * 0.55, y + Math.sin(dotAngle) * radius * 0.55, 3, 0, Math.PI * 2)
      ctx.fill()
    }
  }

  const hpRatio = maxHealth > 0 ? Math.max(0, health / maxHealth) : 1
  const barW = radius * 2.0
  ctx.fillStyle = 'rgba(0,0,0,0.5)'
  ctx.fillRect(x - barW / 2, y - radius - 14, barW, 6)
  ctx.fillStyle = hpRatio > 0.35 ? palette.hp : '#f87171'
  ctx.fillRect(x - barW / 2, y - radius - 14, barW * hpRatio, 6)

  ctx.fillStyle = palette.label
  ctx.font = 'bold 13px Segoe UI, system-ui, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(BOSS_KIND_LABELS[bossKind], x, y - radius - 20)
  ctx.textAlign = 'start'
}

const BOSS_KIND_LABELS: Record<NonNullable<RenderState['enemies'][number]['boss_kind']>, string> = {
  titan: 'ТИТАН',
  stalker: 'СТАЛКЕР',
  swarm: 'РОЕВИК',
  leech: 'КРОВОСОС',
  vortex: 'ВИХРЬ',
}

const BOSS_KIND_PALETTE: Record<
  NonNullable<RenderState['enemies'][number]['boss_kind']>,
  { fill: string; dash: string; stroke: string; chaseStroke: string; hp: string; label: string }
> = {
  titan: {
    fill: '#991b1b',
    dash: '#991b1b',
    stroke: '#fecaca',
    chaseStroke: '#fca5a5',
    hp: '#ef4444',
    label: '#fee2e2',
  },
  stalker: {
    fill: '#6d28d9',
    dash: '#a855f7',
    stroke: '#ddd6fe',
    chaseStroke: '#f0abfc',
    hp: '#c084fc',
    label: '#ede9fe',
  },
  swarm: {
    fill: '#c2410c',
    dash: '#ea580c',
    stroke: '#fed7aa',
    chaseStroke: '#fdba74',
    hp: '#fb923c',
    label: '#ffedd5',
  },
  leech: {
    fill: '#9f1239',
    dash: '#be123c',
    stroke: '#fecdd3',
    chaseStroke: '#fda4af',
    hp: '#f43f5e',
    label: '#ffe4e6',
  },
  vortex: {
    fill: '#1d4ed8',
    dash: '#2563eb',
    stroke: '#bfdbfe',
    chaseStroke: '#93c5fd',
    hp: '#60a5fa',
    label: '#dbeafe',
  },
}

function drawEnemy(
  ctx: CanvasRenderingContext2D,
  enemy: RenderState['enemies'][number],
): void {
  const { x, y, radius, state, health, max_health: maxHealth, burst_left: burstLeft = 0 } = enemy
  const kind = enemy.kind ?? 'grazer'
  const palette = ENEMY_KIND_PALETTE[kind] ?? ENEMY_KIND_PALETTE.grazer
  const isBursting = kind === 'lurker' && burstLeft > 0

  ctx.beginPath()
  ctx.arc(x, y, radius, 0, Math.PI * 2)
  const fill =
    state === 'cooldown'
      ? '#64748b'
      : state === 'flee'
        ? '#fbbf24'
        : isBursting
          ? palette.burst
          : palette.fill
  ctx.fillStyle = fill
  ctx.fill()

  ctx.strokeStyle = state === 'chase' || isBursting ? palette.chaseStroke : palette.stroke
  ctx.lineWidth = state === 'chase' || isBursting ? 3 : 2
  if (kind === 'lurker' && state === 'patrol' && burstLeft <= 0) {
    ctx.setLineDash([4, 5])
  }
  ctx.stroke()
  ctx.setLineDash([])

  drawEnemyKindMark(ctx, x, y, radius, kind, state)

  const hpRatio = maxHealth > 0 ? Math.max(0, health / maxHealth) : 1
  const barW = radius * 1.6
  ctx.fillStyle = 'rgba(0,0,0,0.45)'
  ctx.fillRect(x - barW / 2, y - radius - 8, barW, 4)
  ctx.fillStyle = hpRatio > 0.35 ? '#34d399' : '#f87171'
  ctx.fillRect(x - barW / 2, y - radius - 8, barW * hpRatio, 4)
}

const ENEMY_KIND_PALETTE: Record<
  RenderState['enemies'][number]['kind'],
  { fill: string; burst: string; stroke: string; chaseStroke: string }
> = {
  grazer: {
    fill: '#22c55e',
    burst: '#22c55e',
    stroke: '#86efac',
    chaseStroke: '#86efac',
  },
  hunter: {
    fill: '#ef4444',
    burst: '#ef4444',
    stroke: '#fca5a5',
    chaseStroke: '#f472b6',
  },
  lurker: {
    fill: '#f59e0b',
    burst: '#fb923c',
    stroke: '#fcd34d',
    chaseStroke: '#fdba74',
  },
}

function drawEnemyKindMark(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  kind: RenderState['enemies'][number]['kind'] | undefined,
  state: RenderState['enemies'][number]['state'],
): void {
  const enemyKind = kind ?? 'grazer'
  ctx.save()
  if (enemyKind === 'grazer') {
    ctx.fillStyle = '#14532d'
    ctx.beginPath()
    ctx.arc(x - radius * 0.22, y - radius * 0.18, radius * 0.14, 0, Math.PI * 2)
    ctx.arc(x + radius * 0.22, y - radius * 0.18, radius * 0.14, 0, Math.PI * 2)
    ctx.fill()
  } else if (enemyKind === 'hunter') {
    ctx.strokeStyle = state === 'chase' ? '#fff1f2' : '#7f1d1d'
    ctx.lineWidth = 2
    ctx.lineCap = 'round'
    for (const side of [-1, 1]) {
      ctx.beginPath()
      ctx.moveTo(x + side * radius * 0.18, y - radius * 0.12)
      ctx.lineTo(x + side * radius * 0.42, y + radius * 0.08)
      ctx.stroke()
    }
  } else {
    ctx.fillStyle = '#78350f'
    ctx.beginPath()
    ctx.arc(x, y, radius * 0.18, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.restore()
}

function drawPlayer(
  ctx: CanvasRenderingContext2D,
  player: RenderState['player'],
  pickups: RenderState['pickups'],
): void {
  const {
    x,
    y,
    radius,
    perk_levels: perkLevels = {},
    facing_angle: facing,
    color,
    move_angle: moveAngle,
    grab_kind: grabKind = 'none',
    grab_time_left: grabTimeLeft = 0,
  } = player
  const fill = color ?? '#60a5fa'
  const stroke = heroStrokeColor(fill)
  const direction = moveAngle ?? facing

  const legLevel = getPerkLevel(perkLevels, 'leg')
  const eyeLevel = getPerkLevel(perkLevels, 'eye')
  const tentacleLevel = getPerkLevel(perkLevels, 'tentacle')
  const spikeStats = getSpikeDrawStats(perkLevels)

  if (isPerkWaves(perkLevels, 'tentacle')) {
    drawTentacleWaves(ctx, x, y, radius, facing)
  } else if (tentacleLevel > 0) {
    drawTentacles(ctx, x, y, radius, facing, getPerkLimbCount(perkLevels, 'tentacle'), grabKind !== 'none')
  }

  if (isPerkStub(perkLevels, 'leg')) {
    drawLegStubs(ctx, x, y, radius, facing)
  } else if (legLevel > 0) {
    drawLegs(ctx, x, y, radius, facing, getPerkLimbCount(perkLevels, 'leg'))
  }

  if (spikeStats.forehead) {
    drawForeheadSpike(ctx, x, y, radius, facing, spikeStats.length)
  } else if (spikeStats.count > 0) {
    drawPlayerSpikes(ctx, x, y, radius, direction, spikeStats.count, spikeStats.length)
  }

  drawHeroFigureEight(ctx, x, y, radius, facing, fill, stroke)

  const lobes = getHeroLobeLayout(radius, facing)
  const eyeCenterX = x + lobes.frontOffsetX
  const eyeCenterY = y + lobes.frontOffsetY
  const lookTarget = nearestLookTarget(eyeCenterX, eyeCenterY, pickups)
  if (isPerkDotsOnly(perkLevels, 'eye')) {
    drawLookingDots(ctx, eyeCenterX, eyeCenterY, radius * 0.55, 2, lookTarget, '#ffffff', '#0f172a')
  } else if (eyeLevel > 0) {
    drawEyes(
      ctx,
      eyeCenterX,
      eyeCenterY,
      facing,
      getPerkLimbCount(perkLevels, 'eye'),
      lookTarget,
    )
  }

  if (grabKind !== 'none' && grabTimeLeft > 0) {
    drawGrabLink(ctx, x, y, radius, facing)
  }
}

function nearestLookTarget(
  fromX: number,
  fromY: number,
  pickups: RenderState['pickups'],
): { x: number; y: number } | null {
  let best: { x: number; y: number } | null = null
  let bestDist = Number.POSITIVE_INFINITY
  for (const pickup of pickups) {
    const dx = pickup.x - fromX
    const dy = pickup.y - fromY
    const dist = Math.hypot(dx, dy)
    if (dist < bestDist) {
      bestDist = dist
      best = { x: pickup.x, y: pickup.y }
    }
  }
  return best
}

function drawLookingDots(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  count: number,
  lookTarget: { x: number; y: number } | null,
  fill: string,
  stroke: string,
): void {
  const spacing = Math.min(radius * 0.55, 7)
  const startX = x - ((count - 1) * spacing) / 2
  const lookAngle = lookTarget ? Math.atan2(lookTarget.y - y, lookTarget.x - x) : -Math.PI / 2
  for (let i = 0; i < count; i += 1) {
    const dotX = startX + i * spacing
    const dotY = y - radius * 0.08
    const eyeR = Math.max(2.4, radius * 0.22)
    ctx.beginPath()
    ctx.arc(dotX, dotY, eyeR, 0, Math.PI * 2)
    ctx.fillStyle = fill
    ctx.fill()
    ctx.strokeStyle = stroke
    ctx.lineWidth = 1
    ctx.stroke()
    const pupilOffset = eyeR * 0.4
    ctx.beginPath()
    ctx.arc(
      dotX + Math.cos(lookAngle) * pupilOffset,
      dotY + Math.sin(lookAngle) * pupilOffset,
      eyeR * 0.42,
      0,
      Math.PI * 2,
    )
    ctx.fillStyle = stroke
    ctx.fill()
  }
}

function drawGrabLink(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
): void {
  const endX = x + Math.cos(facing) * (radius + 28)
  const endY = y + Math.sin(facing) * (radius + 28)
  ctx.save()
  ctx.strokeStyle = 'rgba(192, 132, 252, 0.75)'
  ctx.lineWidth = 2
  ctx.setLineDash([5, 4])
  ctx.beginPath()
  ctx.moveTo(x + Math.cos(facing) * radius * 0.4, y + Math.sin(facing) * radius * 0.4)
  ctx.lineTo(endX, endY)
  ctx.stroke()
  ctx.restore()
}

function drawLegStubs(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
): void {
  ctx.save()
  ctx.translate(x, y)
  ctx.rotate(facing)
  ctx.strokeStyle = '#93c5fd'
  ctx.lineWidth = 2.5
  ctx.lineCap = 'round'
  for (const side of [-1, 1]) {
    ctx.beginPath()
    ctx.moveTo(side * radius * 0.42, radius * 0.08)
    ctx.lineTo(side * radius * 0.58, radius * 0.28)
    ctx.stroke()
  }
  ctx.restore()
}

function drawTentacleWaves(
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
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  for (const side of [-1, 1]) {
    ctx.beginPath()
    for (let step = 0; step <= 8; step += 1) {
      const t = step / 8
      const waveX = side * radius * (0.55 + t * 0.35)
      const waveY = -radius * 0.15 + Math.sin(t * Math.PI * 2) * radius * 0.12
      if (step === 0) ctx.moveTo(waveX, waveY)
      else ctx.lineTo(waveX, waveY)
    }
    ctx.stroke()
  }
  ctx.restore()
}

function drawForeheadSpike(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
  length: number,
): void {
  const lobes = getHeroLobeLayout(radius, facing)
  const baseX = x + lobes.frontOffsetX
  const baseY = y + lobes.frontOffsetY
  const tipX = baseX + Math.cos(facing - Math.PI / 2) * length
  const tipY = baseY + Math.sin(facing - Math.PI / 2) * length
  const leftX = baseX + Math.cos(facing - Math.PI / 2 + 2.5) * length * 0.35
  const leftY = baseY + Math.sin(facing - Math.PI / 2 + 2.5) * length * 0.35
  const rightX = baseX + Math.cos(facing - Math.PI / 2 - 2.5) * length * 0.35
  const rightY = baseY + Math.sin(facing - Math.PI / 2 - 2.5) * length * 0.35
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

function drawLegs(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
  count: number,
): void {
  ctx.save()
  ctx.translate(x, y)
  ctx.rotate(facing)
  ctx.strokeStyle = '#93c5fd'
  ctx.lineWidth = 3
  ctx.lineCap = 'round'
  const pairs = Math.ceil(count / 2)
  for (let pair = 0; pair < pairs; pair += 1) {
    for (const side of [-1, 1]) {
      const index = pair * 2 + (side === 1 ? 1 : 0)
      if (index >= count) continue
      const along = -0.35 + (pair / Math.max(pairs - 1, 1)) * 0.55
      const spread = 0.55 + pair * 0.08
      ctx.beginPath()
      ctx.moveTo(side * radius * (0.35 + pair * 0.06), radius * along)
      ctx.lineTo(side * radius * spread, radius * (along + 0.55))
      ctx.stroke()
    }
  }
  ctx.restore()
}

function drawEyes(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  facing: number,
  count: number,
  lookTarget: { x: number; y: number } | null,
): void {
  ctx.save()
  ctx.translate(x, y)
  ctx.rotate(facing)
  const lookWorldAngle = lookTarget ? Math.atan2(lookTarget.y - y, lookTarget.x - x) : facing
  const lookLocal = lookWorldAngle - facing
  const cols = Math.min(count, 3)
  const rows = Math.ceil(count / cols)
  const eyeRadius = 5.2
  const pupilRadius = 2.2
  const pupilTravel = eyeRadius * 0.42
  let drawn = 0
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      if (drawn >= count) break
      const offsetX = (col - (cols - 1) / 2) * 11
      const offsetY = (row - (rows - 1) / 2) * 10 - 1
      ctx.fillStyle = '#ffffff'
      ctx.beginPath()
      ctx.arc(offsetX, offsetY, eyeRadius, 0, Math.PI * 2)
      ctx.fill()
      ctx.strokeStyle = 'rgba(15, 23, 42, 0.35)'
      ctx.lineWidth = 1.1
      ctx.stroke()
      ctx.fillStyle = '#0f172a'
      ctx.beginPath()
      ctx.arc(
        offsetX + Math.cos(lookLocal) * pupilTravel,
        offsetY + Math.sin(lookLocal) * pupilTravel,
        pupilRadius,
        0,
        Math.PI * 2,
      )
      ctx.fill()
      drawn += 1
    }
  }
  ctx.restore()
}

function drawTentacles(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
  count: number,
  isGrabbing: boolean,
): void {
  ctx.save()
  ctx.translate(x, y)
  ctx.rotate(facing)
  ctx.strokeStyle = isGrabbing ? '#e879f9' : '#c084fc'
  ctx.lineWidth = isGrabbing ? 3 : 2.5
  ctx.lineCap = 'round'
  const pairs = Math.ceil(count / 2)
  for (let pair = 0; pair < pairs; pair += 1) {
    for (const side of [-1, 1]) {
      const index = pair * 2 + (side === 1 ? 1 : 0)
      if (index >= count) continue
      const reach = isGrabbing ? 1.35 : 1.05
      const along = -0.2 + pair * 0.18
      ctx.beginPath()
      ctx.moveTo(side * radius * (0.42 + pair * 0.05), radius * along)
      ctx.quadraticCurveTo(
        side * radius * 1.15,
        -radius * (0.35 + pair * 0.08),
        side * radius * reach,
        -radius * (0.65 + pair * 0.05),
      )
      ctx.stroke()
    }
  }
  ctx.restore()
}

function spikeSpreadAngles(baseAngle: number, spikeCount: number): number[] {
  if (spikeCount <= 1) return [baseAngle]
  if (spikeCount === 2) {
    const spread = 0.22
    return [baseAngle - spread, baseAngle + spread]
  }
  const spread = 0.38
  const step = spread / 1.5
  return [baseAngle - spread, baseAngle - step, baseAngle + step, baseAngle + spread]
}

function drawPlayerSpike(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  facing: number,
): void {
  drawPlayerSpikes(ctx, x, y, radius, facing, 1, 12)
}

function drawPlayerSpikes(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number,
  direction: number,
  spikeCount: number,
  spikeLength: number,
): void {
  const startOffset = radius * 0.55
  for (const angle of spikeSpreadAngles(direction, spikeCount)) {
    const baseX = x + Math.cos(angle) * startOffset
    const baseY = y + Math.sin(angle) * startOffset
    const tipX = x + Math.cos(angle) * (startOffset + spikeLength)
    const tipY = y + Math.sin(angle) * (startOffset + spikeLength)
    const leftAngle = angle + Math.PI / 2
    const rightAngle = angle - Math.PI / 2
    const baseWidth = Math.max(3, spikeLength * 0.22)
    const leftX = baseX + Math.cos(leftAngle) * baseWidth
    const leftY = baseY + Math.sin(leftAngle) * baseWidth
    const rightX = baseX + Math.cos(rightAngle) * baseWidth
    const rightY = baseY + Math.sin(rightAngle) * baseWidth

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
  const { red, green, weight, perks = [], radius, stamina = 100, stamina_max = 100, is_sprinting: isSprinting } =
    state.player
  const barWidth = Math.min(240, viewportWidth - 32)
  const x = 16
  const top = 16
  const height = 14
  const gap = 10
  const maxStat = Math.max(50, red, green, 1)

  drawBar(ctx, x, top, barWidth, height, red / maxStat, '#f87171', 'Красная')
  drawBar(ctx, x, top + height + gap, barWidth, height, green / maxStat, '#34d399', 'Зелёная')
  drawBar(
    ctx,
    x,
    top + (height + gap) * 2,
    barWidth,
    height,
    stamina / Math.max(stamina_max, 1),
    isSprinting ? '#fbbf24' : '#60a5fa',
    'Выносливость',
  )

  ctx.fillStyle = '#ffffff'
  ctx.font = '600 14px Segoe UI, system-ui, sans-serif'
  ctx.fillText(`Вес: ${Math.round(weight)} · R ${Math.round(radius)}px`, x, top + (height + gap) * 3 + 18)
  ctx.fillStyle = '#e2e8f0'
  ctx.font = '12px Segoe UI, system-ui, sans-serif'
  const perkText = formatPerkLevels(state.player.perk_levels ?? {})
  ctx.fillText(`Уровень ${state.level} · ${perkText}`, x, top + (height + gap) * 3 + 36)
  ctx.fillText(
    `Врагов съедено: ${state.enemies_eaten_mod}/${state.enemies_per_perk} (всего ${state.enemies_eaten})`,
    x,
    top + (height + gap) * 3 + 52,
  )
  ctx.fillStyle = '#cbd5e1'
  ctx.fillText(
    `Обзор: ${Math.round(state.visibility_radius)}px`,
    x,
    top + (height + gap) * 3 + 68,
  )

  drawMatchTimer(ctx, state, viewportWidth, x, top + (height + gap) * 3 + 88)

  ctx.fillText('Space — щупальце / шип · Shift — рывок', x, top + (height + gap) * 3 + 112)
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
  const activeBoss = state.active_boss
  const escapeSec = state.boss_escape_sec ?? 60
  const fightTimer = state.boss_fight_timer ?? 0
  const escapeLeft = Math.max(0, escapeSec - fightTimer)
  const exitOpen = Boolean(state.exit_open)

  let label = `До водоворота: ${formatTimer(remaining)}`
  if (phase === 'whirlpool') {
    label = `Водоворот: ${formatTimer(whirlpoolLeft)}`
  } else if (exitOpen) {
    label = 'ВЫХОД ОТКРЫТ'
  } else if (phase === 'boss') {
    const title = activeBoss?.title?.toUpperCase() ?? 'БОСС'
    label = `${title} · ${formatTimer(escapeLeft)}`
  }

  ctx.font = '700 16px Segoe UI, system-ui, sans-serif'
  const textWidth = ctx.measureText(label).width + 24
  const boxX = (viewportWidth - textWidth) / 2
  const boxY = 12

  ctx.fillStyle =
    phase === 'whirlpool'
      ? 'rgba(37, 99, 235, 0.92)'
      : exitOpen
        ? 'rgba(15, 23, 42, 0.95)'
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
    ctx.fillText('Всё стягивается в центр водоворота', statusX, statusY)
  } else if (exitOpen) {
    ctx.fillStyle = '#e2e8f0'
    ctx.font = '12px Segoe UI, system-ui, sans-serif'
    ctx.fillText('Чёрный круг в центре — войдите, чтобы перейти на следующий уровень', statusX, statusY)
  } else {
    ctx.fillStyle = '#fca5a5'
    ctx.font = '12px Segoe UI, system-ui, sans-serif'
    const bossHint = activeBoss
      ? `${activeBoss.title}: HP ${Math.ceil(activeBoss.health)}/${Math.ceil(activeBoss.max_health)} · убегите ${formatTimer(escapeLeft)} или убейте`
      : `Убейте босса или проживите ${formatTimer(escapeLeft)} — откроется выход`
    ctx.fillText(bossHint, statusX, statusY)
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
