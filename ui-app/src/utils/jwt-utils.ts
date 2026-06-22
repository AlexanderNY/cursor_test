/**
 * Утилиты для работы с JWT токенами на клиенте.
 * Декодирование без проверки подписи - только для отображения информации.
 */

export interface JwtPayload {
  user_id: number
  type: 'access' | 'refresh'
  iat: number
  exp: number
}

/**
 * Декодирует JWT токен без проверки подписи.
 * Используется только для отображения информации о токене.
 * 
 * @param token JWT токен
 * @returns Payload токена или null если декодирование не удалось
 */
export function decodeJwt(token: string): JwtPayload | null {
  try {
    // JWT состоит из 3 частей: header.payload.signature
    const parts = token.split('.')
    if (parts.length !== 3) {
      return null
    }
    
    // Декодируем payload (вторая часть)
    const payload = parts[1]
    // Base64Url -> Base64
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    // Декодируем из Base64
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    
    return JSON.parse(jsonPayload)
  } catch {
    return null
  }
}

/**
 * Форматирует Unix timestamp в читаемую дату.
 * 
 * @param timestamp Unix timestamp в секундах
 * @returns Отформатированная дата и время
 */
export function formatTokenDate(timestamp: number): string {
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

/**
 * Проверяет, истек ли токен.
 * 
 * @param token JWT токен
 * @returns true если токен истек
 */
export function isTokenExpired(token: string): boolean {
  const payload = decodeJwt(token)
  if (!payload) {
    return true
  }
  
  const now = Math.floor(Date.now() / 1000)
  return payload.exp < now
}

/**
 * Получает время до истечения токена.
 * 
 * @param token JWT токен
 * @returns Строка с оставшимся временем или null
 */
export function getTimeUntilExpiry(token: string): string | null {
  const payload = decodeJwt(token)
  if (!payload) {
    return null
  }
  
  const now = Math.floor(Date.now() / 1000)
  const diff = payload.exp - now
  
  if (diff <= 0) {
    return 'Expired'
  }
  
  const days = Math.floor(diff / 86400)
  const hours = Math.floor((diff % 86400) / 3600)
  const minutes = Math.floor((diff % 3600) / 60)
  
  if (days > 0) {
    return `${days}d ${hours}h`
  }
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}
