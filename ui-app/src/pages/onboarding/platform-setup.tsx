import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { LearnModeBanner } from '@/components/smm/learn-mode-banner'
import { smmService } from '@/services/smm-service'
import { useBrand } from '@/contexts/brand-context'
import { usePlatformReadiness } from '@/hooks/use-platform-readiness'
import { getErrorMessage } from '@/services/api-client'
import type { BrandNetwork } from '@/types/smm'
import {
  NETWORK_LABELS,
  NETWORK_SETUP_URLS,
  networkLabel,
} from '@/lib/smm-networks'

const ONBOARDING_NETWORKS: BrandNetwork[] = [
  'tg',
  'vk',
  'instagram',
  'threads',
  'tw',
  'dzen',
  'wp',
]

export function PlatformSetupPage() {
  const navigate = useNavigate()
  const { state, loading, refresh } = usePlatformReadiness()
  const { brands, refreshBrands, refreshChannels } = useBrand()
  const [error, setError] = useState('')
  const [brandName, setBrandName] = useState('')
  const [network, setNetwork] = useState<BrandNetwork>('tg')
  const [externalId, setExternalId] = useState('')
  const [channelTitle, setChannelTitle] = useState('')
  const [saving, setSaving] = useState(false)
  const [seeding, setSeeding] = useState(false)

  useEffect(() => {
    if (!loading && state?.completed) {
      navigate('/channels', { replace: true })
    }
  }, [loading, state, navigate])

  async function handleSkip() {
    try {
      await smmService.skipOnboarding()
      navigate('/channels', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function handleSeedDemo() {
    setSeeding(true)
    setError('')
    try {
      await smmService.seedDemoWorkspace(true)
      await refresh()
      await refreshBrands()
      await refreshChannels()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSeeding(false)
    }
  }

  async function handleCreateBrand(e: React.FormEvent) {
    e.preventDefault()
    if (!brandName.trim()) return
    setSaving(true)
    setError('')
    try {
      await smmService.createBrand({ name: brandName.trim(), color: '#3B82F6' })
      setBrandName('')
      await refreshBrands()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function handleAddChannel(e: React.FormEvent) {
    e.preventDefault()
    const brandId = brands[0]?.id
    if (!brandId || !externalId.trim()) return
    setSaving(true)
    setError('')
    try {
      await smmService.addChannel(brandId, {
        network,
        external_id: externalId.trim(),
        title: channelTitle.trim() || externalId.trim(),
        role: 'own',
        kind: network === 'tg' ? 'channel' : 'public',
      })
      setExternalId('')
      setChannelTitle('')
      await refreshChannels()
      const next = await smmService.onboardingState()
      if (next.completed) navigate('/channels', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const step = state?.step ?? 1
  const platforms = state?.platforms

  function platformReady(net: BrandNetwork): boolean {
    if (net === 'tg') return Boolean(state?.tg_ready)
    if (net === 'vk') return Boolean(state?.vk_ready)
    return Boolean(platforms?.[net]?.connected)
  }

  return (
    <PageContainer>
      <PageHeader
        title="Platform setup"
        description="Подключите любую сеть пайплайна и добавьте own-канал бренда"
      />
      <LearnModeBanner visible={Boolean(state?.learn_mode)} />
      {error && <Alert variant="error">{error}</Alert>}

      {!state?.demo_seeded && (
        <Alert variant="info" className="mb-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm">
              Нужен учебный демо-бренд без реальных credentials? Создайте контур S01 (публикация
              отключена).
            </p>
            <Button size="sm" variant="secondary" isLoading={seeding} onClick={() => void handleSeedDemo()}>
              Создать учебный бренд
            </Button>
          </div>
        </Alert>
      )}

      <div className="mb-4 text-sm text-[var(--text-muted)]">
        Step {Math.min(step, state?.total_steps ?? 5)} / {state?.total_steps ?? 5}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>1–2. Connect platforms</CardTitle>
            <CardDescription>
              Достаточно одной сети. TG/VK и Selenium/OAuth-платформы равноправны.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {ONBOARDING_NETWORKS.map((net) => {
              const ready = platformReady(net)
              return (
                <Link key={net} to={NETWORK_SETUP_URLS[net]}>
                  <Button variant={ready ? 'secondary' : 'primary'} size="sm">
                    {ready ? `${NETWORK_LABELS[net]} ✓` : `Connect ${NETWORK_LABELS[net]}`}
                  </Button>
                </Link>
              )
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>3. Create brand</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateBrand} className="flex gap-2">
              <Input
                value={brandName}
                onChange={(e) => setBrandName(e.target.value)}
                placeholder="Brand name"
                disabled={saving || brands.length > 0}
              />
              <Button type="submit" disabled={saving || brands.length > 0}>
                Create
              </Button>
            </form>
            {brands.length > 0 && (
              <p className="text-sm text-emerald-400 mt-2">Brand ready: {brands[0].name}</p>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>4–5. Add own channel</CardTitle>
            <CardDescription>
              Канал можно добавить сразу (TG/VK/IG/Threads/TW/Дзен/WP). Для публикации позже
              подтвердите собственность (Recheck / Bind) после подключения платформы.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddChannel} className="flex flex-wrap gap-2 items-end">
              <select
                className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                value={network}
                onChange={(e) => setNetwork(e.target.value as BrandNetwork)}
              >
                {ONBOARDING_NETWORKS.map((net) => (
                  <option key={net} value={net}>
                    {NETWORK_LABELS[net]}
                  </option>
                ))}
              </select>
              <Input
                value={externalId}
                onChange={(e) => setExternalId(e.target.value)}
                placeholder={
                  network === 'tg' || network === 'vk'
                    ? 'Channel / group id'
                    : 'Handle / username / site'
                }
                className="min-w-[12rem]"
              />
              <Input
                value={channelTitle}
                onChange={(e) => setChannelTitle(e.target.value)}
                placeholder="Title (optional)"
                className="min-w-[12rem]"
              />
              <Button type="submit" disabled={saving || !brands.length}>
                Add channel
              </Button>
            </form>
            <p className="text-xs text-[var(--text-muted)] mt-3">
              Auth for {networkLabel(network)}:{' '}
              <Link
                to={NETWORK_SETUP_URLS[network]}
                className="text-primary-400 hover:underline"
              >
                open platform page
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 flex gap-2">
        <Button variant="secondary" onClick={() => void handleSkip()}>
          Skip (read-only mode)
        </Button>
        {state?.has_connected_own_channel && (
          <Button onClick={() => navigate('/posts')}>Go to posts</Button>
        )}
      </div>
    </PageContainer>
  )
}
