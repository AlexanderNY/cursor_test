export interface HeroColorOption {
  id: string
  label: string
  fill: string
  stroke: string
}

export const HERO_COLORS: HeroColorOption[] = [
  { id: 'blue', label: 'Голубой', fill: '#60a5fa', stroke: '#bfdbfe' },
  { id: 'emerald', label: 'Изумрудный', fill: '#34d399', stroke: '#a7f3d0' },
  { id: 'violet', label: 'Фиолетовый', fill: '#a78bfa', stroke: '#ddd6fe' },
  { id: 'rose', label: 'Розовый', fill: '#fb7185', stroke: '#fecdd3' },
  { id: 'amber', label: 'Янтарный', fill: '#fbbf24', stroke: '#fde68a' },
  { id: 'cyan', label: 'Бирюзовый', fill: '#22d3ee', stroke: '#a5f3fc' },
  { id: 'lime', label: 'Лайм', fill: '#a3e635', stroke: '#d9f99d' },
  { id: 'orange', label: 'Оранжевый', fill: '#fb923c', stroke: '#fed7aa' },
]

export const DEFAULT_HERO_COLOR = HERO_COLORS[0].fill

export function heroStrokeColor(fill: string): string {
  return HERO_COLORS.find((item) => item.fill === fill)?.stroke ?? '#bfdbfe'
}

export function isAllowedHeroColor(color: string): boolean {
  return HERO_COLORS.some((item) => item.fill === color)
}
