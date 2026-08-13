import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

// Используем относительный путь - Vite proxy обработает запрос
const API_BASE_URL = '/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/** FastAPI detail: string | validation[] | { message, ... } */
export function normalizeErrorDetail(detail: unknown): string {
  if (detail == null || detail === '') return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && 'msg' in item) {
          return String((item as { msg: unknown }).msg)
        }
        try {
          return JSON.stringify(item)
        } catch {
          return String(item)
        }
      })
      .filter(Boolean)
      .join('; ')
  }
  if (typeof detail === 'object' && detail !== null && 'message' in detail) {
    const msg = (detail as { message: unknown }).message
    if (typeof msg === 'string' && msg.trim()) return msg
  }
  try {
    return JSON.stringify(detail)
  } catch {
    return String(detail)
  }
}

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // Debug: проверка отправки токена
    console.log('[API] Request:', config.url, 'Token:', token ? 'present' : 'missing')
    return config
  },
  (error) => Promise.reject(error)
)

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    
    // Проверяем что это именно ошибка истечения токена, а не другая 401 ошибка
    const errorDetail = normalizeErrorDetail(error.response?.data?.detail)
    const isTokenExpired = errorDetail.includes('Token has expired')
    
    if (error.response?.status === 401 && isTokenExpired && !originalRequest._retry) {
      originalRequest._retry = true
      
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/sign-in'
        return Promise.reject(error)
      }
      
      try {
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        })
        
        const { access_token, refresh_token } = response.data
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', refresh_token)
        
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`
        }
        
        return apiClient(originalRequest)
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/sign-in'
        return Promise.reject(error)
      }
    }
    
    return Promise.reject(error)
  }
)

export interface ApiError {
  detail?: string | Record<string, unknown> | Array<unknown>
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>
    const detail = normalizeErrorDetail(axiosError.response?.data?.detail)
    if (detail) return detail
    return axiosError.message || 'An error occurred'
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unknown error occurred'
}
