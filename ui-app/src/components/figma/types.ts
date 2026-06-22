/** Types for Kubernetes Cluster Management Interface (Figma layout) */

export type ClusterStatus = 'running' | 'warning' | 'error' | 'pending'

export interface ClusterSummary {
  id: string
  name: string
  status: ClusterStatus
  nodeCount: number
  podCount: number
  cpuUsage: number
  memoryUsage: number
}

export interface NodeRow {
  name: string
  status: ClusterStatus
  roles: string[]
  cpu: string
  memory: string
  age: string
}

export interface MetricCardProps {
  label: string
  value: string | number
  subValue?: string
  trend?: 'up' | 'down' | 'neutral'
}
