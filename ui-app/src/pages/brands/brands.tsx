import { FormEvent, useEffect, useState } from 'react'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import { BRAND_PALETTE, type BrandChannel, type ChannelRole } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'

export function BrandsPage() {
  const { brands, selectedBrandId, setSelectedBrandId, refreshBrands, refreshChannels } = useBrand()
  const [name, setName] = useState('')
  const [color, setColor] = useState<string>(BRAND_PALETTE[0])
  const [error, setError] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [channels, setChannels] = useState<BrandChannel[]>([])
  const [channelNetwork, setChannelNetwork] = useState<'tg' | 'vk'>('tg')
  const [channelId, setChannelId] = useState('')
  const [channelTitle, setChannelTitle] = useState('')
  const [channelRole, setChannelRole] = useState<ChannelRole>('own')
  const [activeBrandId, setActiveBrandId] = useState<number | null>(null)

  useEffect(() => {
    setActiveBrandId(selectedBrandId)
  }, [selectedBrandId])

  useEffect(() => {
    if (!activeBrandId) {
      setChannels([])
      return
    }
    void smmService.listChannels(activeBrandId).then(setChannels).catch(() => setChannels([]))
  }, [activeBrandId])

  async function handleCreateBrand(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    setIsSaving(true)
    setError('')
    try {
      const brand = await smmService.createBrand({ name: name.trim(), color })
      setName('')
      await refreshBrands()
      setSelectedBrandId(brand.id)
      setActiveBrandId(brand.id)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  async function handleDeleteBrand(id: number) {
    if (!confirm('Delete this brand and its channels?')) return
    try {
      await smmService.deleteBrand(id)
      await refreshBrands()
      if (activeBrandId === id) setActiveBrandId(null)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function handleAddChannel(e: FormEvent) {
    e.preventDefault()
    if (!activeBrandId || !channelId.trim()) return
    setIsSaving(true)
    setError('')
    try {
      await smmService.addChannel(activeBrandId, {
        network: channelNetwork,
        external_id: channelId.trim(),
        title: channelTitle.trim() || channelId.trim(),
        role: channelRole,
        kind: channelNetwork === 'vk' ? 'public' : 'channel',
      })
      setChannelId('')
      setChannelTitle('')
      const list = await smmService.listChannels(activeBrandId)
      setChannels(list)
      await refreshChannels()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  async function handleDeleteChannel(channel: BrandChannel) {
    if (!activeBrandId) return
    try {
      await smmService.deleteChannel(activeBrandId, channel.id)
      setChannels((prev) => prev.filter((c) => c.id !== channel.id))
      await refreshChannels()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const ownCount = channels.filter((c) => c.role === 'own').length

  return (
    <PageContainer>
      <PageHeader
        title="Brands"
        description="Цветовые связки каналов TG/VK (до 20 own-каналов)"
      />
      {error && <Alert variant="error">{error}</Alert>}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Создать бренд</CardTitle>
            <CardDescription>Палитра для быстрой идентификации</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateBrand} className="space-y-4">
              <Input label="Название" value={name} onChange={(e) => setName(e.target.value)} />
              <div>
                <p className="text-sm text-[var(--text-secondary)] mb-2">Цвет</p>
                <div className="flex flex-wrap gap-2">
                  {BRAND_PALETTE.map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setColor(c)}
                      className={`h-8 w-8 rounded-full border-2 ${color === c ? 'border-[var(--text-primary)]' : 'border-transparent'}`}
                      style={{ backgroundColor: c }}
                      aria-label={c}
                    />
                  ))}
                </div>
              </div>
              <Button type="submit" disabled={isSaving || !name.trim()}>
                {isSaving ? 'Saving…' : 'Create brand'}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ваши бренды</CardTitle>
            <CardDescription>Выберите бренд для работы в Header switcher</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {brands.length === 0 && (
              <p className="text-sm text-[var(--text-muted)]">Пока нет брендов</p>
            )}
            {brands.map((b) => (
              <div
                key={b.id}
                className={`flex items-center justify-between gap-2 rounded-lg border border-[var(--border-color)] p-3 ${
                  activeBrandId === b.id ? 'bg-[var(--bg-tertiary)]' : ''
                }`}
              >
                <button
                  type="button"
                  className="flex items-center gap-2 flex-1 text-left"
                  onClick={() => {
                    setActiveBrandId(b.id)
                    setSelectedBrandId(b.id)
                  }}
                >
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: b.color }} />
                  <span className="font-medium text-[var(--text-primary)]">{b.name}</span>
                </button>
                <Button variant="ghost" size="sm" onClick={() => handleDeleteBrand(b.id)}>
                  Delete
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {activeBrandId && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Каналы бренда</CardTitle>
            <CardDescription>
              Own-каналы: {ownCount} / 20 · competitor / source тоже можно добавить
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleAddChannel} className="grid gap-3 md:grid-cols-5 items-end">
              <div>
                <label className="text-sm text-[var(--text-secondary)]">Сеть</label>
                <select
                  className="w-full mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2"
                  value={channelNetwork}
                  onChange={(e) => setChannelNetwork(e.target.value as 'tg' | 'vk')}
                >
                  <option value="tg">Telegram</option>
                  <option value="vk">VKontakte</option>
                </select>
              </div>
              <Input
                label="External ID"
                value={channelId}
                onChange={(e) => setChannelId(e.target.value)}
                placeholder="-100… / 123456"
              />
              <Input
                label="Title"
                value={channelTitle}
                onChange={(e) => setChannelTitle(e.target.value)}
              />
              <div>
                <label className="text-sm text-[var(--text-secondary)]">Role</label>
                <select
                  className="w-full mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2"
                  value={channelRole}
                  onChange={(e) => setChannelRole(e.target.value as ChannelRole)}
                >
                  <option value="own">own</option>
                  <option value="source">source</option>
                  <option value="competitor">competitor</option>
                </select>
              </div>
              <Button type="submit" disabled={isSaving}>
                Add
              </Button>
            </form>

            <ul className="space-y-2">
              {channels.map((c) => (
                <li
                  key={c.id}
                  className="flex items-center justify-between rounded-md border border-[var(--border-color)] px-3 py-2 text-sm"
                >
                  <span>
                    <span className="uppercase text-[var(--text-muted)] mr-2">{c.network}</span>
                    {c.title || c.external_id}{' '}
                    <span className="text-[var(--text-muted)]">({c.role})</span>
                  </span>
                  <Button variant="ghost" size="sm" onClick={() => handleDeleteChannel(c)}>
                    Remove
                  </Button>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
