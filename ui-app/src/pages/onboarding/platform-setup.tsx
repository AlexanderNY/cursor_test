import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { smmService } from '@/services/smm-service'
import { useBrand } from '@/contexts/brand-context'
import { usePlatformReadiness } from '@/hooks/use-platform-readiness'
import { getErrorMessage } from '@/services/api-client'

export function PlatformSetupPage() {
  const navigate = useNavigate()
  const { state, loading } = usePlatformReadiness()
  const { brands, refreshBrands, refreshChannels } = useBrand()
  const [error, setError] = useState('')
  const [brandName, setBrandName] = useState('')
  const [network, setNetwork] = useState<'tg' | 'vk'>('tg')
  const [externalId, setExternalId] = useState('')
  const [channelTitle, setChannelTitle] = useState('')
  const [saving, setSaving] = useState(false)

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

  return (
    <PageContainer>
      <PageHeader
        title="Platform setup"
        description="Подключите Telegram/VK и добавьте свой канал перед публикацией"
      />
      {error && <Alert variant="error">{error}</Alert>}

      <div className="mb-4 text-sm text-[var(--text-muted)]">
        Step {Math.min(step, state?.total_steps ?? 5)} / {state?.total_steps ?? 5}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>1–2. Connect platforms</CardTitle>
            <CardDescription>
              TG: {state?.tg_ready ? 'connected' : 'not connected'} · VK:{' '}
              {state?.vk_ready ? 'connected' : 'not connected'}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Link to="/telegram">
              <Button variant={state?.tg_ready ? 'secondary' : 'primary'}>
                {state?.tg_ready ? 'Telegram ✓' : 'Connect Telegram'}
              </Button>
            </Link>
            <Link to="/vkontakte">
              <Button variant={state?.vk_ready ? 'secondary' : 'primary'}>
                {state?.vk_ready ? 'VK ✓' : 'Connect VK'}
              </Button>
            </Link>
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
              Канал можно добавить сразу. Для публикации позже подтвердите собственность
              (Recheck) после подключения TG/VK.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddChannel} className="flex flex-wrap gap-2 items-end">
              <select
                className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                value={network}
                onChange={(e) => setNetwork(e.target.value as 'tg' | 'vk')}
              >
                <option value="tg">Telegram</option>
                <option value="vk">VK</option>
              </select>
              <Input
                value={externalId}
                onChange={(e) => setExternalId(e.target.value)}
                placeholder="Channel / group id"
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
