import { K8sHeader } from './K8sHeader'
import { K8sSidebar } from './K8sSidebar'
import { ClusterCard } from './ClusterCard'
import { MetricCard } from './MetricCard'
import { NodeTable } from './NodeTable'
import type { ClusterSummary, NodeRow } from './types'

const mockClusters: ClusterSummary[] = [
  {
    id: '1',
    name: 'production-cluster',
    status: 'running',
    nodeCount: 12,
    podCount: 84,
    cpuUsage: 42,
    memoryUsage: 68,
  },
  {
    id: '2',
    name: 'staging-cluster',
    status: 'warning',
    nodeCount: 4,
    podCount: 32,
    cpuUsage: 78,
    memoryUsage: 82,
  },
  {
    id: '3',
    name: 'dev-cluster',
    status: 'running',
    nodeCount: 3,
    podCount: 18,
    cpuUsage: 24,
    memoryUsage: 45,
  },
]

const mockNodes: NodeRow[] = [
  { name: 'node-1.prod', status: 'running', roles: ['master', 'worker'], cpu: '1200m', memory: '4Gi', age: '45d' },
  { name: 'node-2.prod', status: 'running', roles: ['worker'], cpu: '800m', memory: '3Gi', age: '45d' },
  { name: 'node-3.prod', status: 'running', roles: ['worker'], cpu: '950m', memory: '3.5Gi', age: '30d' },
]

export function K8sDashboard() {
  return (
    <div className="flex min-h-screen bg-[var(--bg-primary)]">
      <K8sSidebar />
      <div className="flex flex-1 flex-col min-w-0">
        <K8sHeader />
        <main className="flex-1 overflow-auto p-6">
          <div className="mx-auto max-w-7xl space-y-8">
            <section>
              <h2 className="mb-4 text-xl font-semibold text-[var(--text-primary)]">Overview</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <MetricCard label="Total clusters" value={3} subValue="2 running" trend="neutral" />
                <MetricCard label="Total nodes" value={19} subValue="18 ready" trend="up" />
                <MetricCard label="Total pods" value={134} subValue="128 running" trend="neutral" />
                <MetricCard label="Avg. CPU" value="48%" subValue="Last 24h" trend="down" />
              </div>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-[var(--text-primary)]">Clusters</h2>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                {mockClusters.map((cluster) => (
                  <ClusterCard key={cluster.id} cluster={cluster} />
                ))}
              </div>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-[var(--text-primary)]">Nodes (production-cluster)</h2>
              <NodeTable nodes={mockNodes} />
            </section>
          </div>
        </main>
      </div>
    </div>
  )
}
