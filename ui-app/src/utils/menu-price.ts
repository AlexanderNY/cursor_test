/** Валидация и форматирование цены пунктов меню (до 2 знаков после запятой). */

export const MENU_PRICE_HINT =
  'Положительное число, не более 2 знаков после запятой. Для разделов без цены укажите 0.'

export interface MenuPriceValidation {
  value: number
  error?: string
}

/** Оставляет в строке только допустимые символы при вводе. */
export function sanitizeMenuPriceInput(raw: string): string {
  const normalized = raw.replace(',', '.')
  if (normalized === '') return ''
  if (!/^\d*(\.\d{0,2})?$/.test(normalized)) {
    return raw.slice(0, -1).replace(',', '.')
  }
  return normalized
}

export function validateMenuPrice(raw: string): MenuPriceValidation {
  const trimmed = raw.trim()
  if (!trimmed) {
    return { value: 0 }
  }

  const normalized = trimmed.replace(',', '.')
  if (!/^\d+(\.\d{1,2})?$/.test(normalized) && !/^\d+$/.test(normalized)) {
    return {
      value: 0,
      error: 'Цена: положительное число, не более 2 знаков после запятой (например 99.90)',
    }
  }

  const value = Number.parseFloat(normalized)
  if (!Number.isFinite(value)) {
    return { value: 0, error: 'Некорректная цена' }
  }
  if (value < 0) {
    return { value: 0, error: 'Цена не может быть отрицательной' }
  }

  const decimalPart = normalized.includes('.') ? normalized.split('.')[1] : ''
  if (decimalPart.length > 2) {
    return { value: 0, error: 'Не более 2 знаков после запятой' }
  }

  const rounded = Math.round(value * 100) / 100
  return { value: rounded }
}

export function formatMenuPrice(value: number | null | undefined): string {
  if (value === null || value === undefined || value <= 0) {
    return '—'
  }
  return `${value.toLocaleString('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ₽`
}

export function formatOrderMoney(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return '—'
  }
  return `${value.toLocaleString('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ₽`
}
