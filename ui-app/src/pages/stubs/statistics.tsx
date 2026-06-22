import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { EmptyState, DataTable } from '@/components/ui'
import { coreService } from '@/services/core-service'
import type { HealthcheckItem, StatisticsItem } from '@/types/core'

export function StatisticsTabContent() {
  const [healthcheckData, setHealthcheckData] = useState<HealthcheckItem[]>([])
  const [statisticsData, setStatisticsData] = useState<StatisticsItem[]>([])
  const [isLoadingHealthcheck, setIsLoadingHealthcheck] = useState(false)
  const [isLoadingStatistics, setIsLoadingStatistics] = useState(false)
  const [healthcheckError, setHealthcheckError] = useState('')
  const [statisticsError, setStatisticsError] = useState('')

  async function handleHealthcheck() {
    setHealthcheckError('')
    setIsLoadingHealthcheck(true)
    try {
      const response = await coreService.getHealthcheck()
      setHealthcheckData(response.services || [])
    } catch (error) {
      setHealthcheckError(error instanceof Error ? error.message : 'Failed to fetch healthcheck')
      setHealthcheckData([])
    } finally {
      setIsLoadingHealthcheck(false)
    }
  }

  async function handleStatistics() {
    setStatisticsError('')
    setIsLoadingStatistics(true)
    try {
      const response = await coreService.getStatistics()
      setStatisticsData(response.services || [])
    } catch (error) {
      setStatisticsError(error instanceof Error ? error.message : 'Failed to fetch statistics')
      setStatisticsData([])
    } finally {
      setIsLoadingStatistics(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card className="animate-slide-up">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Service Healthcheck
          </CardTitle>
          <CardDescription>Check the status of all services</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            onClick={handleHealthcheck}
            isLoading={isLoadingHealthcheck}
            className="w-full sm:w-auto"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Request Healthcheck
          </Button>

          {healthcheckError && (
            <Alert variant="error" className="animate-slide-down">
              {healthcheckError}
            </Alert>
          )}

          {healthcheckData.length > 0 && (
            <div className="overflow-x-auto animate-slide-down">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-[var(--border-color)]">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Service Name</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {healthcheckData.map((item, index) => (
                    <tr
                      key={index}
                      className="border-b border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors"
                    >
                      <td className="py-3 px-4 text-[var(--text-secondary)]">{item.service_name}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                          item.status === 'ok'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-red-500/20 text-red-400'
                        }`}>
                          {item.status === 'ok' ? (
                            <>
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              OK
                            </>
                          ) : (
                            <>
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                              Error
                            </>
                          )}
                        </span>
                        {item.error && (
                          <div className="mt-1 text-xs text-red-400">{item.error}</div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {healthcheckData.length === 0 && !isLoadingHealthcheck && !healthcheckError && (
            <EmptyState
              title="No healthcheck data"
              description='Click "Request Healthcheck" to check service status.'
            />
          )}
        </CardContent>
      </Card>

      <Card className="animate-slide-up animate-stagger-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Service Statistics
          </CardTitle>
          <CardDescription>View statistics for collected, processed, and published posts</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            onClick={handleStatistics}
            isLoading={isLoadingStatistics}
            className="w-full sm:w-auto"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Request Statistics
          </Button>

          {statisticsError && (
            <Alert variant="error" className="animate-slide-down">
              {statisticsError}
            </Alert>
          )}

          {statisticsData.length > 0 && (
            <div className="animate-slide-down">
              <DataTable<StatisticsItem>
                columns={[
                  { key: 'service_name', header: 'Service Name', render: (v) => <span className="font-medium">{String(v)}</span> },
                  { key: 'collected_posts', header: 'Collected Posts', render: (v) => Number(v).toLocaleString() },
                  { key: 'processed_posts', header: 'Processed Posts', render: (v) => Number(v).toLocaleString() },
                  { key: 'published_posts', header: 'Published Posts', render: (v) => Number(v).toLocaleString() },
                ]}
                data={statisticsData}
                keyExtractor={(row) => row.service_name}
                striped
              />
            </div>
          )}

          {statisticsData.length === 0 && !isLoadingStatistics && !statisticsError && (
            <EmptyState
              title="No statistics data"
              description='Click "Request Statistics" to view service statistics.'
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
