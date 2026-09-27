export const BOWL_STAGES = [
  { id: 1, title: 'Унитаз', hazard: 'Смыв' },
  { id: 2, title: 'Канализация', hazard: 'Метан' },
  { id: 3, title: 'Ручей', hazard: 'Течение' },
  { id: 4, title: 'Очистные', hazard: 'Хлор' },
  { id: 5, title: 'Море', hazard: 'Волны' },
] as const

export type BowlStageId = (typeof BOWL_STAGES)[number]['id']

export function clampBowlStage(stage: number): BowlStageId {
  const value = Math.floor(stage)
  if (value <= 1) return 1
  if (value >= 5) return 5
  return value as BowlStageId
}
