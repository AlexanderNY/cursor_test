import { createContext, useContext, useReducer, useEffect, useCallback } from 'react'
import type { AuthState, AuthAction, User, TokenResponse, LoginCredentials, RegisterCredentials, ProfileUpdate } from '@/types'
import { authService } from '@/services/auth-service'

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>
  register: (credentials: RegisterCredentials) => Promise<void>
  logout: () => Promise<void>
  logoutAll: () => Promise<void>
  updateProfile: (data: ProfileUpdate) => Promise<void>
  resetPassword: (email: string) => Promise<void>
  clearError: () => void
  refreshUserData: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const initialState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
}

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_START':
      return { ...state, isLoading: true, error: null }
    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        accessToken: action.payload.tokens.access_token,
        refreshToken: action.payload.tokens.refresh_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      }
    case 'AUTH_FAILURE':
      return {
        ...state,
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      }
    case 'LOGOUT':
      return {
        ...initialState,
        isLoading: false,
      }
    case 'UPDATE_USER':
      return { 
        ...state, 
        user: action.payload,
        // Обновляем токены, если они пришли в ответе профиля
        accessToken: action.payload.access_token || state.accessToken,
        refreshToken: action.payload.refresh_token || state.refreshToken,
      }
    case 'UPDATE_TOKENS':
      return {
        ...state,
        accessToken: action.payload.access_token,
        refreshToken: action.payload.refresh_token,
      }
    case 'CLEAR_ERROR':
      return { ...state, error: null }
    default:
      return state
  }
}

function getStoredTokens(): { accessToken: string | null; refreshToken: string | null } {
  return {
    accessToken: localStorage.getItem('access_token'),
    refreshToken: localStorage.getItem('refresh_token'),
  }
}

function storeTokens(tokens: TokenResponse) {
  localStorage.setItem('access_token', tokens.access_token)
  localStorage.setItem('refresh_token', tokens.refresh_token)
}

function clearStoredTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

interface AuthProviderProps {
  children: React.ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState)

  const refreshUserData = useCallback(async () => {
    const { accessToken } = getStoredTokens()
    if (!accessToken) {
      dispatch({ type: 'AUTH_FAILURE', payload: '' })
      return
    }

    try {
      const user = await authService.getProfile()
      // Используем токены из ответа профиля, если они есть, иначе из localStorage
      const tokens = user.access_token && user.refresh_token
        ? {
            access_token: user.access_token,
            refresh_token: user.refresh_token,
            token_type: 'bearer',
          }
        : {
            access_token: getStoredTokens().accessToken!,
            refresh_token: getStoredTokens().refreshToken!,
            token_type: 'bearer',
          }
      
      // Обновляем localStorage, если токены пришли из API
      if (user.access_token && user.refresh_token) {
        storeTokens(tokens)
      }
      
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user,
          tokens,
        },
      })
    } catch {
      clearStoredTokens()
      dispatch({ type: 'LOGOUT' })
    }
  }, [])

  useEffect(() => {
    refreshUserData()
  }, [refreshUserData])

  const login = useCallback(async (credentials: LoginCredentials) => {
    dispatch({ type: 'AUTH_START' })
    try {
      const tokens = await authService.login(credentials)
      storeTokens(tokens)
      const user = await authService.getProfile()
      // Используем токены из ответа профиля, если они есть
      const finalTokens = user.access_token && user.refresh_token
        ? {
            access_token: user.access_token,
            refresh_token: user.refresh_token,
            token_type: 'bearer',
          }
        : tokens
      if (user.access_token && user.refresh_token) {
        storeTokens(finalTokens)
      }
      dispatch({ type: 'AUTH_SUCCESS', payload: { user, tokens: finalTokens } })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed'
      dispatch({ type: 'AUTH_FAILURE', payload: message })
      throw error
    }
  }, [])

  const register = useCallback(async (credentials: RegisterCredentials) => {
    dispatch({ type: 'AUTH_START' })
    try {
      const tokens = await authService.register(credentials)
      storeTokens(tokens)
      const user = await authService.getProfile()
      // Используем токены из ответа профиля, если они есть
      const finalTokens = user.access_token && user.refresh_token
        ? {
            access_token: user.access_token,
            refresh_token: user.refresh_token,
            token_type: 'bearer',
          }
        : tokens
      if (user.access_token && user.refresh_token) {
        storeTokens(finalTokens)
      }
      dispatch({ type: 'AUTH_SUCCESS', payload: { user, tokens: finalTokens } })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Registration failed'
      dispatch({ type: 'AUTH_FAILURE', payload: message })
      throw error
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      const { refreshToken } = getStoredTokens()
      if (refreshToken) {
        await authService.logout(refreshToken)
      }
    } finally {
      clearStoredTokens()
      dispatch({ type: 'LOGOUT' })
    }
  }, [])

  const logoutAll = useCallback(async () => {
    try {
      await authService.logoutAll()
    } finally {
      clearStoredTokens()
      dispatch({ type: 'LOGOUT' })
    }
  }, [])

  const updateProfile = useCallback(async (data: ProfileUpdate) => {
    try {
      const updatedUser = await authService.updateProfile(data)
      // Обновляем токены, если они пришли в ответе
      if (updatedUser.access_token && updatedUser.refresh_token) {
        storeTokens({
          access_token: updatedUser.access_token,
          refresh_token: updatedUser.refresh_token,
          token_type: 'bearer',
        })
      }
      dispatch({ type: 'UPDATE_USER', payload: updatedUser })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Profile update failed'
      throw new Error(message)
    }
  }, [])

  const resetPassword = useCallback(async (email: string) => {
    try {
      await authService.resetPassword(email)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Password reset failed'
      throw new Error(message)
    }
  }, [])

  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' })
  }, [])

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        register,
        logout,
        logoutAll,
        updateProfile,
        resetPassword,
        clearError,
        refreshUserData,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}


