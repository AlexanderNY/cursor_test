import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import { BRAND_PALETTE, type BrandChannel } from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'

export function BrandsPage() {
  const { brands, selectedBrandId, setSelectedBrandId, refreshBrands } = useBrand()
  const [name, setName] = useState('')
  const [color, setColor] = useState<string>(BRAND_PALETTE[0])
  const [error, setError] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [channels, setChannels] = useState<BrandChannel[]>([])
  const [activeBrandId, setActiveBrandId] = useState<number | null>(null)

  useEffect(() => {
    setActiveBrandId(selectedBrandId)
  }, [selectedBrandId])

  useEffect(() => {
    if (!activeBrandId) {
      setChannels([])
      return
    }
    void smmService
      .listChannels(activeBrandId)
      .then(setChannels)
      .catch(() => setChannels([]))
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

  return (
    <PageContainer>
      <PageHeader
        title="Brands"
        description="Шаг 1: создайте бренд → далее Channels → аналитика"
      />
      <p className="mb-4 text-sm flex flex-wrap gap-3">
        <Link to="/channels" className="text-primary-400 hover:underline">
          Далее: Channels →
        </Link>
        <Link to="/analytics" className="text-primary-400 hover:underline">
          Analytics →
        </Link>
      </p>
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
            <CardDescription>Выберите бренд для Header switcher</CardDescription>
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
              Управление каналами, флагами и потоком — в хабе Channels
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link to="/channels">
              <Button variant="secondary">Открыть Channels →</Button>
            </Link>
            {channels.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)]">Пока нет каналов</p>
            ) : (
              <ul className="space-y-2">
                {channels.map((c) => (
                  <li
                    key={c.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-[var(--border-color)] px-3 py-2 text-sm"
                  >
                    <span>
                      <span className="uppercase text-[var(--text-muted)] mr-2">{c.network}</span>
                      {c.title || c.external_id} · {c.role}
                    </span>
                    <Link
                      to={`/channels/${c.id}`}
                      className="text-xs text-primary-400 hover:underline"
                    >
                      Настроить
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
