import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { smmService } from '@/services/smm-service'
import type { Brand, BrandChannel } from '@/types/smm'
import { useAuth } from './auth-context'

const STORAGE_KEY = 'smm_selected_brand_id'

interface BrandContextValue {
  brands: Brand[]
  selectedBrand: Brand | null
  selectedBrandId: number | null
  channels: BrandChannel[]
  ownChannels: BrandChannel[]
  /** own + publish_enabled (для выбора в Target Social Networks) */
  publishableChannels: BrandChannel[]
  isLoading: boolean
  setSelectedBrandId: (id: number | null) => void
  refreshBrands: () => Promise<void>
  refreshChannels: () => Promise<void>
}

const BrandContext = createContext<BrandContextValue | null>(null)

export function BrandProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  const [brands, setBrands] = useState<Brand[]>([])
  const [channels, setChannels] = useState<BrandChannel[]>([])
  const [selectedBrandId, setSelectedBrandIdState] = useState<number | null>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      return raw ? Number(raw) : null
    } catch {
      return null
    }
  })
  const [isLoading, setIsLoading] = useState(false)

  const setSelectedBrandId = useCallback((id: number | null) => {
    setSelectedBrandIdState(id)
    try {
      if (id == null) localStorage.removeItem(STORAGE_KEY)
      else localStorage.setItem(STORAGE_KEY, String(id))
    } catch {
      /* ignore */
    }
  }, [])

  const refreshBrands = useCallback(async () => {
    if (!isAuthenticated) {
      setBrands([])
      return
    }
    setIsLoading(true)
    try {
      const list = await smmService.listBrands()
      setBrands(list)
      if (selectedBrandId != null && !list.some((b) => b.id === selectedBrandId)) {
        setSelectedBrandId(list[0]?.id ?? null)
      } else if (selectedBrandId == null && list.length === 1) {
        setSelectedBrandId(list[0].id)
      }
    } catch {
      setBrands([])
    } finally {
      setIsLoading(false)
    }
  }, [isAuthenticated, selectedBrandId, setSelectedBrandId])

  const refreshChannels = useCallback(async () => {
    if (!selectedBrandId || !isAuthenticated) {
      setChannels([])
      return
    }
    try {
      const list = await smmService.listChannels(selectedBrandId)
      setChannels(list)
    } catch {
      setChannels([])
    }
  }, [selectedBrandId, isAuthenticated])

  useEffect(() => {
    void refreshBrands()
  }, [isAuthenticated])

  useEffect(() => {
    void refreshChannels()
  }, [refreshChannels])

  const selectedBrand = useMemo(
    () => brands.find((b) => b.id === selectedBrandId) ?? null,
    [brands, selectedBrandId],
  )

  const ownChannels = useMemo(
    () => channels.filter((c) => c.role === 'own'),
    [channels],
  )

  const publishableChannels = useMemo(
    () => ownChannels.filter((c) => c.publish_enabled !== false),
    [ownChannels],
  )

  const value = useMemo(
    () => ({
      brands,
      selectedBrand,
      selectedBrandId,
      channels,
      ownChannels,
      publishableChannels,
      isLoading,
      setSelectedBrandId,
      refreshBrands,
      refreshChannels,
    }),
    [
      brands,
      selectedBrand,
      selectedBrandId,
      channels,
      ownChannels,
      publishableChannels,
      isLoading,
      setSelectedBrandId,
      refreshBrands,
      refreshChannels,
    ],
  )

  return <BrandContext.Provider value={value}>{children}</BrandContext.Provider>
}

export function useBrand() {
  const ctx = useContext(BrandContext)
  if (!ctx) throw new Error('useBrand must be used within BrandProvider')
  return ctx
}
