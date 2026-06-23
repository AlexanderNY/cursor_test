import { createContext, useContext, type ReactNode } from 'react'
import { useChecksInfra, type ChecksInfra } from './use-checks-infra'

const ChecksInfraContext = createContext<ChecksInfra | null>(null)

export function ChecksInfraProvider({ children }: { children: ReactNode }) {
  const value = useChecksInfra()
  return <ChecksInfraContext.Provider value={value}>{children}</ChecksInfraContext.Provider>
}

export function useChecksInfraContext(): ChecksInfra {
  const ctx = useContext(ChecksInfraContext)
  if (!ctx) {
    throw new Error('useChecksInfraContext must be used within ChecksInfraProvider')
  }
  return ctx
}
