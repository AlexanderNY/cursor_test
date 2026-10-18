import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { LearnModeBanner } from '@/components/smm/learn-mode-banner'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import { BRAND_PALETTE, type Brand, type BrandChannel } from '@/types/smm'
import { hasBrandVoice } from '@/components/ai/brand-voice-editor'
import { getErrorMessage } from '@/services/api-client'
import { parseQuotaError, type QuotaErrorDetail } from '@/lib/quota'
import { QuotaUpgradeModal } from '@/components/billing/QuotaUpgradeModal'
import { QuotaBanner } from '@/components/billing/QuotaBanner'
import type { UsageSummary } from '@/types/smm'

export function BrandsPage() {
  const { brands, selectedBrandId, setSelectedBrandId, refreshBrands } = useBrand()
  const [name, setName] = useState('')
  const [color, setColor] = useState<string>(BRAND_PALETTE[0])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [channels, setChannels] = useState<BrandChannel[]>([])
  const [activeBrandId, setActiveBrandId] = useState<number | null>(null)

  const [editingBrandId, setEditingBrandId] = useState<number | null>(null)
  const [editBrandName, setEditBrandName] = useState('')
  const [isRenamingBrand, setIsRenamingBrand] = useState(false)
  const [quotaDetail, setQuotaDetail] = useState<QuotaErrorDetail | null>(null)
  const [usage, setUsage] = useState<UsageSummary | null>(null)
  const [learnMode, setLearnMode] = useState(false)

  useEffect(() => {
    void smmService.getUsageSummary().then(setUsage).catch(() => setUsage(null))
  }, [brands.length])

  useEffect(() => {
    void smmService
      .onboardingState()
      .then((s) => setLearnMode(Boolean(s.learn_mode)))
      .catch(() => setLearnMode(false))
  }, [brands.length])

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
    setSuccess('')
    try {
      const brand = await smmService.createBrand({ name: name.trim(), color })
      setName('')
      await refreshBrands()
      setSelectedBrandId(brand.id)
      setActiveBrandId(brand.id)
      setSuccess('Бренд создан')
      void smmService.getUsageSummary().then(setUsage).catch(() => null)
    } catch (err) {
      const q = parseQuotaError(err)
      if (q) setQuotaDetail(q)
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  function startRenameBrand(brand: Brand) {
    setEditingBrandId(brand.id)
    setEditBrandName(brand.name)
    setError('')
    setSuccess('')
  }

  function cancelRenameBrand() {
    setEditingBrandId(null)
    setEditBrandName('')
  }

  async function handleRenameBrand(id: number) {
    const trimmed = editBrandName.trim()
    const brand = brands.find((b) => b.id === id)
    if (!trimmed || !brand || trimmed === brand.name) {
      cancelRenameBrand()
      return
    }
    setIsRenamingBrand(true)
    setError('')
    setSuccess('')
    try {
      await smmService.updateBrand(id, { name: trimmed })
      await refreshBrands()
      setEditingBrandId(null)
      setEditBrandName('')
      setSuccess('Бренд переименован')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsRenamingBrand(false)
    }
  }

  async function handleDeleteBrand(id: number) {
    if (!confirm('Delete this brand and its channels?')) return
    try {
      await smmService.deleteBrand(id)
      await refreshBrands()
      if (activeBrandId === id) setActiveBrandId(null)
      if (editingBrandId === id) cancelRenameBrand()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const activeBrand = brands.find((brand) => brand.id === activeBrandId) ?? null

  return (
    <PageContainer>
      <PageHeader
        title="Brands"
        description="Создайте бренд и подключите каналы. Голос для AI задаётся в помощнике на странице поста."
      />
      <LearnModeBanner visible={learnMode} />
      <p className="mb-4 text-sm flex flex-wrap gap-3">
        <Link to="/channels" className="text-primary-400 hover:underline">
          Далее: Channels →
        </Link>
        <Link to="/analytics" className="text-primary-400 hover:underline">
          Analytics →
        </Link>
      </p>
      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}
      <QuotaBanner metrics={usage?.metrics} focusKey="max_brands" className="mb-4" />
      <QuotaUpgradeModal
        open={quotaDetail != null}
        detail={quotaDetail}
        onClose={() => setQuotaDetail(null)}
      />

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
            <CardDescription>
              Выберите бренд для шапки. Голос для AI — в помощнике при написании поста.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {brands.length === 0 && (
              <p className="text-sm text-[var(--text-muted)]">Пока нет брендов</p>
            )}
            {brands.map((b) => {
              const isRenaming = editingBrandId === b.id
              return (
                <div
                  key={b.id}
                  className={`rounded-lg border border-[var(--border-color)] p-3 ${
                    activeBrandId === b.id ? 'bg-[var(--bg-tertiary)]' : ''
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <button
                      type="button"
                      className="flex items-center gap-2 flex-1 text-left"
                      onClick={() => {
                        setActiveBrandId(b.id)
                        setSelectedBrandId(b.id)
                      }}
                    >
                      <span className="h-3 w-3 rounded-full shrink-0" style={{ backgroundColor: b.color }} />
                      <span className="font-medium text-[var(--text-primary)]">{b.name}</span>
                      {b.is_demo && (
                        <span className="text-[10px] uppercase tracking-wide text-amber-400">
                          Demo S01
                        </span>
                      )}
                      {hasBrandVoice(b) && (
                        <span className="text-[10px] uppercase tracking-wide text-[var(--text-muted)]">
                          Голос
                        </span>
                      )}
                    </button>
                    <div className="flex shrink-0 gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => startRenameBrand(b)}
                        disabled={isRenamingBrand && isRenaming}
                      >
                        Переименовать
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDeleteBrand(b.id)}>
                        Delete
                      </Button>
                    </div>
                  </div>
                  {isRenaming && (
                    <form
                      className="mt-3 flex flex-wrap items-end gap-2"
                      onSubmit={(e) => {
                        e.preventDefault()
                        void handleRenameBrand(b.id)
                      }}
                    >
                      <div className="min-w-[180px] flex-1">
                        <Input
                          label="Название"
                          value={editBrandName}
                          onChange={(e) => setEditBrandName(e.target.value)}
                          autoFocus
                        />
                      </div>
                      <Button
                        type="submit"
                        size="sm"
                        disabled={isRenamingBrand || !editBrandName.trim() || editBrandName.trim() === b.name}
                      >
                        {isRenamingBrand ? 'Saving…' : 'Сохранить'}
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        disabled={isRenamingBrand}
                        onClick={cancelRenameBrand}
                      >
                        Отмена
                      </Button>
                    </form>
                  )}
                </div>
              )
            })}
          </CardContent>
        </Card>
      </div>

      {activeBrand && (
        <p className="mt-6 text-sm text-[var(--text-muted)]">
          Голос «{activeBrand.name}» {hasBrandVoice(activeBrand) ? 'задан' : 'не задан'}.{' '}
          <Link to="/posts" className="text-primary-400 hover:underline">
            Настроить в AI-помощнике на странице поста
          </Link>
          {' · '}
          <Link to="/inbox" className="text-primary-400 hover:underline">
            во входящих
          </Link>
        </p>
      )}

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
