import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

// Используем относительный путь - Vite proxy обработает запрос
const API_BASE_URL = '/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

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
    const errorDetail = error.response?.data?.detail || ''
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
  detail: string
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>
    return axiosError.response?.data?.detail || axiosError.message || 'An error occurred'
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unknown error occurred'
}


