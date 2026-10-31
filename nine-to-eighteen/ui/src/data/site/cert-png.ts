import type { CertTone } from '@/data/site/cert-shared'

export type CertTopicRender = {
  code: string
  title: string
}

export type CertRenderInput = {
  code: string
  holderName: string
  series: string
  trackName: string
  courseTitle?: string
  issuedLabel: string
  episodeCount: number
  done?: number
  percent?: number
  earned?: boolean
  quizLabel: string
  tone: CertTone
  fileStem?: string
  durationLabel?: string
  resultLabel?: string
  resultValue?: string
  topics?: CertTopicRender[]
  serialNumber?: string
}

/** @deprecated Prefer CertRenderInput — kept for call sites that still say PNG. */
export type CertPngInput = CertRenderInput

const PAGE_W = 1654
const PAGE_H = 2339
const A4_PT_W = 595.28
const A4_PT_H = 841.89

function fileStemOf(input: CertRenderInput): string {
  const raw = (input.fileStem || input.code || 'cert').trim() || 'cert'
  return raw.replace(/[^\w.-]+/g, '_')
}

function wrapLines(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const words = text.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) {
    return []
  }
  const lines: string[] = []
  let current = ''
  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word
    if (ctx.measureText(candidate).width <= maxWidth) {
      current = candidate
      continue
    }
    if (current) {
      lines.push(current)
    }
    if (ctx.measureText(word).width <= maxWidth) {
      current = word
      continue
    }
    let chunk = ''
    for (const char of word) {
      const next = chunk + char
      if (ctx.measureText(next).width > maxWidth && chunk) {
        lines.push(chunk)
        chunk = char
      } else {
        chunk = next
      }
    }
    current = chunk
  }
  if (current) {
    lines.push(current)
  }
  return lines
}

function fitLine(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string {
  if (ctx.measureText(text).width <= maxWidth) {
    return text
  }
  let cut = text
  while (cut.length > 1 && ctx.measureText(`${cut}…`).width > maxWidth) {
    cut = cut.slice(0, -1)
  }
  return `${cut}…`
}

function renderCertCanvas(input: CertRenderInput): HTMLCanvasElement | null {
  const canvas = document.createElement('canvas')
  canvas.width = PAGE_W
  canvas.height = PAGE_H
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    return null
  }
  const { tone } = input
  const earned = Boolean(input.earned)
  const holder = input.holderName || 'Участник'
  const course = input.courseTitle || input.trackName
  const topics = input.topics || []
  const margin = 100
  const textWidth = PAGE_W - margin * 2 - 24

  ctx.fillStyle = '#fffdf8'
  ctx.fillRect(0, 0, PAGE_W, PAGE_H)
  ctx.textBaseline = 'alphabetic'

  const frame = ctx.createLinearGradient(0, 0, PAGE_W, PAGE_H)
  frame.addColorStop(0, tone.a)
  frame.addColorStop(0.55, tone.b)
  frame.addColorStop(1, tone.c)
  ctx.strokeStyle = frame
  ctx.lineWidth = 16
  ctx.strokeRect(40, 40, PAGE_W - 80, PAGE_H - 80)
  ctx.strokeStyle = '#e7d7b8'
  ctx.lineWidth = 2
  ctx.strokeRect(72, 72, PAGE_W - 144, PAGE_H - 144)

  let y = 148
  ctx.fillStyle = '#5c4a32'
  ctx.font = '700 28px "Segoe UI", sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('СЕРТИФИКАТ', margin, y)
  ctx.textAlign = 'right'
  ctx.fillText(input.serialNumber || '9TO18 · LEARN', PAGE_W - margin, y)

  y += 26
  const bar = ctx.createLinearGradient(margin, 0, PAGE_W - margin, 0)
  bar.addColorStop(0, tone.a)
  bar.addColorStop(0.6, tone.b)
  bar.addColorStop(1, tone.c)
  ctx.fillStyle = bar
  ctx.fillRect(margin, y, textWidth, 6)

  y += 72
  ctx.textAlign = 'left'
  ctx.fillStyle = '#5c4a32'
  ctx.font = '400 32px "Segoe UI", sans-serif'
  ctx.fillText(earned ? 'Настоящим подтверждается, что' : 'Бланк курса для', margin, y)

  y += 74
  ctx.fillStyle = '#1c1408'
  ctx.font = '700 62px "Times New Roman", Palatino, serif'
  for (const line of wrapLines(ctx, holder, textWidth).slice(0, 2)) {
    ctx.fillText(line, margin, y)
    y += 70
  }

  y += 6
  ctx.fillStyle = '#5c4a32'
  ctx.font = '400 32px "Segoe UI", sans-serif'
  ctx.fillText(earned ? 'прошёл(а) курс' : 'проходит курс', margin, y)

  y += 56
  ctx.fillStyle = '#1c1408'
  ctx.font = '700 40px "Times New Roman", Palatino, serif'
  for (const line of wrapLines(ctx, course, textWidth).slice(0, 3)) {
    ctx.fillText(line, margin, y)
    y += 48
  }

  y += 12
  ctx.font = '400 30px "Segoe UI", sans-serif'
  ctx.fillStyle = '#3f3428'
  const dateLine =
    earned && input.issuedLabel
      ? `Дата прохождения: ${input.issuedLabel}`
      : 'Дата выдачи появится после завершения курса'
  ctx.fillText(dateLine, margin, y)

  y += 46
  const facts = [
    input.durationLabel ? `Примерное время курса: ${input.durationLabel}` : '',
    input.resultValue ? `${input.resultLabel || 'Темы'}: ${input.resultValue}` : '',
    input.serialNumber ? `Номер ${input.serialNumber}` : '',
    input.code ? `Код проверки ${input.code}` : '',
  ].filter(Boolean)
  ctx.font = '600 26px "Segoe UI", sans-serif'
  ctx.fillStyle = '#5c4a32'
  for (const fact of facts) {
    ctx.fillText(fact, margin, y)
    y += 36
  }

  y += 28
  ctx.fillStyle = '#7c6448'
  ctx.font = '700 22px "Segoe UI", sans-serif'
  ctx.fillText('ПРОЙДЕННЫЕ ТЕМЫ', margin, y)
  y += 34

  const footerTop = PAGE_H - 230
  if (topics.length === 0) {
    ctx.fillStyle = '#3f3428'
    ctx.font = '400 28px "Segoe UI", sans-serif'
    const note = input.quizLabel || 'Пройденных тем пока нет.'
    for (const line of wrapLines(ctx, note, textWidth).slice(0, 5)) {
      if (y > footerTop - 20) {
        break
      }
      ctx.fillText(line, margin, y)
      y += 36
    }
  } else {
    const twoCols = topics.length > 12
    const topicFont =
      topics.length > 40 ? '400 18px "Segoe UI", sans-serif' : topics.length > 18 ? '400 22px "Segoe UI", sans-serif' : '400 26px "Segoe UI", sans-serif'
    const lineH = topics.length > 40 ? 24 : topics.length > 18 ? 30 : 34
    ctx.font = topicFont
    const rows = Math.max(1, Math.floor((footerTop - y) / lineH))
    const capacity = twoCols ? rows * 2 : rows
    const overflow = topics.length > capacity
    const shown = topics.slice(0, overflow ? Math.max(capacity - 1, 1) : topics.length)
    shown.forEach((topic, index) => {
      const col = twoCols ? index % 2 : 0
      const row = twoCols ? Math.floor(index / 2) : index
      const colW = twoCols ? (textWidth - 28) / 2 : textWidth
      const x = margin + col * (colW + 28)
      const lineY = y + row * lineH
      ctx.fillStyle = '#1c1408'
      ctx.fillText(fitLine(ctx, `${topic.code}  ${topic.title}`, colW), x, lineY)
    })
    if (overflow) {
      ctx.fillStyle = '#5c4a32'
      ctx.fillText(`и ещё ${topics.length - shown.length}`, margin, footerTop - 8)
    }
  }

  const sealX = PAGE_W - margin - 70
  const sealY = PAGE_H - 150
  ctx.beginPath()
  ctx.arc(sealX, sealY, 72, 0, Math.PI * 2)
  ctx.fillStyle = frame
  ctx.fill()
  ctx.beginPath()
  ctx.arc(sealX, sealY, 54, 0, Math.PI * 2)
  ctx.fillStyle = '#fffdf8'
  ctx.fill()
  ctx.strokeStyle = tone.b
  ctx.setLineDash([6, 5])
  ctx.lineWidth = 3
  ctx.stroke()
  ctx.setLineDash([])
  ctx.fillStyle = '#1c1408'
  ctx.textAlign = 'center'
  ctx.font = '700 26px "Segoe UI", sans-serif'
  ctx.fillText('9–18', sealX, sealY - 2)
  ctx.font = '700 15px "Segoe UI", sans-serif'
  ctx.fillStyle = '#5c4a32'
  ctx.fillText(earned ? 'СДАН' : 'ПУТЬ', sealX, sealY + 22)

  if (earned) {
    ctx.save()
    ctx.translate(margin + 210, PAGE_H - 155)
    ctx.rotate((-12 * Math.PI) / 180)
    ctx.strokeStyle = 'rgba(185, 28, 28, 0.78)'
    ctx.lineWidth = 5
    ctx.strokeRect(-150, -34, 300, 68)
    ctx.fillStyle = 'rgba(153, 27, 27, 0.9)'
    ctx.font = '800 36px "Segoe UI", sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('ПРОЙДЕНО', 0, 2)
    ctx.restore()
  }

  ctx.textAlign = 'left'
  ctx.textBaseline = 'alphabetic'
  ctx.fillStyle = '#7c6448'
  ctx.font = '600 22px "Segoe UI", sans-serif'
  ctx.fillText('9to18.ru', margin, PAGE_H - 96)

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

function buildJpegPdf(
  jpeg: Uint8Array,
  imageWidth: number,
  imageHeight: number,
  pageWidth = imageWidth,
  pageHeight = imageHeight,
): Blob {
  const objects: string[] = []
  const offsets: number[] = [0]

  function pushObject(body: string) {
    objects.push(body)
  }

  pushObject('1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
  pushObject('2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n')
  pushObject(
    `3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] /Contents 4 0 R /Resources << /XObject << /Im0 5 0 R >> >> >>\nendobj\n`,
  )
  const content = `q\n${pageWidth} 0 0 ${pageHeight} 0 0 cm\n/Im0 Do\nQ\n`
  pushObject(
    `4 0 obj\n<< /Length ${content.length} >>\nstream\n${content}endstream\nendobj\n`,
  )

  const header =
    `5 0 obj\n<< /Type /XObject /Subtype /Image /Width ${imageWidth} /Height ${imageHeight} ` +
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
  const pdf = buildJpegPdf(buffer, canvas.width, canvas.height, A4_PT_W, A4_PT_H)
  triggerDownload(pdf, `${fileStemOf(input)}.pdf`)
}
