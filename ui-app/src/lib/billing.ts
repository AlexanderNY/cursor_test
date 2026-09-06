export function formatRub(amount: number | null | undefined, currency = 'RUB'): string {
  const n = Number(amount ?? 0)
  const formatted = n.toLocaleString('ru-RU')
  if ((currency || 'RUB').toUpperCase() === 'RUB') return `${formatted} ₽`
  return `${formatted} ${currency}`
}

export const PLAN_REQUEST_STATUS_LABEL: Record<string, string> = {
  pending: 'Новая',
  invoiced: 'Счёт отправлен',
  applied: 'Тариф включён',
  rejected: 'Отклонена',
  cancelled: 'Отменена',
}
