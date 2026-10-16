import type { CertTone } from '@/data/site/cert-shared'

export type CertRenderInput = {
  code: string
  holderName: string
  series: string
  trackName: string
  issuedLabel: string
  episodeCount: number
  done?: number
  percent?: number
  earned?: boolean
  quizLabel: string
  tone: CertTone
  fileStem?: string
}

/** @deprecated Prefer CertRenderInput — kept for call sites that still say PNG. */
export type CertPngInput = CertRenderInput

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
) {
  ctx.beginPath()
  ctx.moveTo(x + radius, y)
  ctx.arcTo(x + width, y, x + width, y + height, radius)
  ctx.arcTo(x + width, y + height, x, y + height, radius)
  ctx.arcTo(x, y + height, x, y, radius)
  ctx.arcTo(x, y, x + width, y, radius)
  ctx.closePath()
}

function fileStemOf(input: CertRenderInput): string {
  const raw = (input.fileStem || input.code || 'cert').trim() || 'cert'
  return raw.replace(/[^\w.-]+/g, '_')
}

function renderCertCanvas(input: CertRenderInput): HTMLCanvasElement | null {
  const canvas = document.createElement('canvas')
  canvas.width = 1400
  canvas.height = 900
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    return null
  }
  const { tone } = input
  const percent = Math.max(0, Math.min(100, Math.round(input.percent ?? (input.earned ? 100 : 0))))
  const done = input.done ?? (input.earned ? input.episodeCount : 0)
  const earned = Boolean(input.earned)

  ctx.fillStyle = '#fffdf8'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  const frame = ctx.createLinearGradient(0, 0, 1400, 900)
  frame.addColorStop(0, tone.a)
  frame.addColorStop(0.5, tone.b)
  frame.addColorStop(1, tone.c)
  ctx.fillStyle = frame
  roundRect(ctx, 36, 36, 1328, 828, 36)
  ctx.fill()
  ctx.fillStyle = '#fffdf8'
  roundRect(ctx, 52, 52, 1296, 796, 28)
  ctx.fill()

  ctx.strokeStyle = tone.b
  ctx.lineWidth = 3
  roundRect(ctx, 78, 78, 1244, 744, 18)
  ctx.stroke()

  const banner = ctx.createLinearGradient(120, 0, 1280, 0)
  banner.addColorStop(0, tone.a)
  banner.addColorStop(0.62, tone.b)
  banner.addColorStop(1, tone.c)
  ctx.fillStyle = banner
  roundRect(ctx, 140, 120, 1120, 64, 32)
  ctx.fill()
  ctx.fillStyle = '#042f2e'
  ctx.font = '700 22px Segoe UI, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('9TO18 · LEARN', 180, 162)
  ctx.textAlign = 'right'
  ctx.fillText(input.code ? input.code : `${percent}%`, 1220, 162)

  ctx.textAlign = 'left'
  ctx.fillStyle = '#5c4a32'
  ctx.font = '700 22px Segoe UI, sans-serif'
  ctx.fillText(input.series.toUpperCase(), 140, 250)

  ctx.fillStyle = '#1c1408'
  ctx.font = '700 72px Segoe UI, sans-serif'
  ctx.fillText(input.holderName, 140, 340)
  ctx.font = '600 36px Segoe UI, sans-serif'
  ctx.fillText(input.trackName, 140, 400)

  ctx.fillStyle = '#3f3428'
  ctx.font = '400 28px Segoe UI, sans-serif'
  const progressLine = earned
    ? `Подтверждается прохождение трека, ${input.episodeCount} вып.`
    : `Прогресс: ${done}/${input.episodeCount} вып. · ${percent}%`
  const lines = [
    progressLine,
    input.quizLabel,
    input.issuedLabel ? `Дата бланка: ${input.issuedLabel}` : 'Черновик — курс ещё не закрыт',
  ]
  lines.forEach((line, index) => {
    ctx.fillText(line, 140, 480 + index * 42)
  })

  ctx.fillStyle = '#e8f5f1'
  roundRect(ctx, 140, 620, 720, 18, 9)
  ctx.fill()
  const bar = ctx.createLinearGradient(140, 0, 860, 0)
  bar.addColorStop(0, tone.a)
  bar.addColorStop(1, tone.b)
  ctx.fillStyle = bar
  roundRect(ctx, 140, 620, Math.max(12, (720 * percent) / 100), 18, 9)
  ctx.fill()
  ctx.fillStyle = '#5c4a32'
  ctx.font = '600 20px Segoe UI, sans-serif'
  ctx.fillText(`${percent}%`, 880, 636)

  ctx.beginPath()
  ctx.arc(1180, 640, 92, 0, Math.PI * 2)
  ctx.fillStyle = frame
  ctx.fill()
  ctx.beginPath()
  ctx.arc(1180, 640, 68, 0, Math.PI * 2)
  ctx.fillStyle = '#fffdf8'
  ctx.fill()
  ctx.strokeStyle = tone.b
  ctx.setLineDash([6, 5])
  ctx.lineWidth = 3
  ctx.stroke()
  ctx.setLineDash([])
  ctx.fillStyle = '#1c1408'
  ctx.textAlign = 'center'
  ctx.font = '700 28px Segoe UI, sans-serif'
  ctx.fillText('9–18', 1180, 636)
  ctx.font = '700 16px Segoe UI, sans-serif'
  ctx.fillStyle = '#5c4a32'
  ctx.fillText(earned ? 'СДАН' : 'ПУТЬ', 1180, 664)

  if (earned) {
    ctx.save()
    ctx.translate(700, 520)
    ctx.rotate((-18 * Math.PI) / 180)
    ctx.strokeStyle = 'rgba(185, 28, 28, 0.72)'
    ctx.fillStyle = 'rgba(185, 28, 28, 0.12)'
    ctx.lineWidth = 6
    roundRect(ctx, -210, -48, 420, 96, 12)
    ctx.fill()
    ctx.stroke()
    ctx.fillStyle = 'rgba(153, 27, 27, 0.88)'
    ctx.font = '800 52px Segoe UI, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('ПРОЙДЕНО', 0, 4)
    ctx.restore()
  }

  return canvas
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function encodePdfString(raw: string): string {
  return raw.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)')
}

function buildJpegPdf(jpeg: Uint8Array, width: number, height: number): Blob {
  const objects: string[] = []
  const offsets: number[] = [0]

  function pushObject(body: string) {
    objects.push(body)
  }

  pushObject('1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
  pushObject('2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n')
  pushObject(
    `3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${width} ${height}] /Contents 4 0 R /Resources << /XObject << /Im0 5 0 R >> >> >>\nendobj\n`,
  )
  const content = `q\n${width} 0 0 ${height} 0 0 cm\n/Im0 Do\nQ\n`
  pushObject(
    `4 0 obj\n<< /Length ${content.length} >>\nstream\n${content}endstream\nendobj\n`,
  )

  const header =
    `5 0 obj\n<< /Type /XObject /Subtype /Image /Width ${width} /Height ${height} ` +
    `/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${jpeg.length} >>\nstream\n`
  const footer = '\nendstream\nendobj\n'

  const encoder = new TextEncoder()
  const parts: Uint8Array[] = []
  let size = 0

  function appendBytes(chunk: Uint8Array) {
    parts.push(chunk)
    size += chunk.length
  }

  function appendText(text: string) {
    appendBytes(encoder.encode(text))
  }

  appendText('%PDF-1.4\n%\xE2\xE3\xCF\xD3\n')
  for (let index = 0; index < objects.length; index += 1) {
    offsets[index + 1] = size
    appendText(objects[index])
  }
  offsets[5] = size
  appendText(header)
  appendBytes(jpeg)
  appendText(footer)

  const xrefStart = size
  let xref = `xref\n0 6\n0000000000 65535 f \n`
  for (let index = 1; index <= 5; index += 1) {
    xref += `${String(offsets[index]).padStart(10, '0')} 00000 n \n`
  }
  xref += `trailer\n<< /Size 6 /Root 1 0 R /Info << /Title (${encodePdfString('9to18 certificate')}) >> >>\n`
  xref += `startxref\n${xrefStart}\n%%EOF\n`
  appendText(xref)

  const out = new Uint8Array(size)
  let offset = 0
  for (const part of parts) {
    out.set(part, offset)
    offset += part.length
  }
  return new Blob([out], { type: 'application/pdf' })
}

function canvasToBlob(canvas: HTMLCanvasElement, type: string, quality?: number): Promise<Blob | null> {
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), type, quality)
  })
}

export function downloadCertPng(input: CertRenderInput): void {
  const canvas = renderCertCanvas(input)
  if (!canvas) {
    return
  }
  void canvasToBlob(canvas, 'image/png').then((blob) => {
    if (!blob) {
      return
    }
    triggerDownload(blob, `${fileStemOf(input)}.png`)
  })
}

export async function downloadCertPdf(input: CertRenderInput): Promise<void> {
  const canvas = renderCertCanvas(input)
  if (!canvas) {
    return
  }
  const jpegBlob = await canvasToBlob(canvas, 'image/jpeg', 0.92)
  if (!jpegBlob) {
    return
  }
  const buffer = new Uint8Array(await jpegBlob.arrayBuffer())
  const pdf = buildJpegPdf(buffer, canvas.width, canvas.height)
  triggerDownload(pdf, `${fileStemOf(input)}.pdf`)
}
