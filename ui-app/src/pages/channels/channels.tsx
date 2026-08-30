import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { DataTable, type DataTableColumn } from '@/components/ui/data-table'
import { CheckCircleIcon, XCircleIcon } from '@/components/icons'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import type { BrandChannel, BrandNetwork, ChannelRole, PlatformStatusResponse } from '@/types/smm'
import { authStatusLabel, publishReady, collectReady, alertReady, channelReady, reviewEnabled } from '@/hooks/use-platform-readiness'
import { getErrorMessage } from '@/services/api-client'
import { parseQuotaError, type QuotaErrorDetail } from '@/lib/quota'
import { QuotaUpgradeModal } from '@/components/billing/QuotaUpgradeModal'
import { QuotaBanner } from '@/components/billing/QuotaBanner'
import type { UsageSummary } from '@/types/smm'
import {
  BRAND_NETWORKS,
  NETWORK_LABELS,
  networkLabel,
  networkSetupUrl,
} from '@/lib/smm-networks'

type ChannelRow = BrandChannel & { brand_name?: string; brand_color?: string }

function FlagStatusIcon({
  on,
  label,
  title,
  na = false,
  warn = false,
}: {
  on: boolean
  label: string
  title?: string
  na?: boolean
  /** Enabled but misconfigured / incomplete */
  warn?: boolean
}) {
  if (na) {
    return (
      <span
        className="inline-flex items-center justify-center text-[var(--text-muted)]"
        title={title || `${label}: недоступно`}
        aria-label={`${label}: n/a`}
      >
        <span className="text-xs font-medium tracking-wide">—</span>
      </span>
    )
  }
  if (on && warn) {
    return (
      <span
        className="inline-flex text-amber-400"
        title={title || `${label}: включено, но настройка неполная`}
        aria-label={`${label}: warn`}
      >
        <CheckCircleIcon size={20} />
      </span>
    )
  }
  return on ? (
    <span
      className="inline-flex text-emerald-400"
      title={title || `${label}: включено`}
      aria-label={`${label}: on`}
    >
      <CheckCircleIcon size={20} />
    </span>
  ) : (
    <span
      className="inline-flex text-[var(--text-muted)] opacity-60"
      title={title || `${label}: выключено`}
      aria-label={`${label}: off`}
    >
      <XCircleIcon size={20} />
    </span>
  )
}

export function ChannelsPage() {
  const {
    brands,
    selectedBrandId,
    setSelectedBrandId,
    refreshChannels,
    refreshBrands,
    isLoading: isLoadingBrands,
  } = useBrand()
  const [channels, setChannels] = useState<ChannelRow[]>([])
  const [error, setError] = useState('')
  const [limits, setLimits] = useState<{ max_own_channels?: number; tariff?: string }>({})
  const [network, setNetwork] = useState<BrandNetwork>('tg')
  const [externalId, setExternalId] = useState('')
  const [title, setTitle] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [role, setRole] = useState<ChannelRole>('own')
  const [brandId, setBrandId] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)
  const [loadingList, setLoadingList] = useState(false)
  const [filterTitle, setFilterTitle] = useState('')
  const [filterNetwork, setFilterNetwork] = useState<'all' | BrandNetwork>('all')
  const [copiedKey, setCopiedKey] = useState<string | null>(null)
  const [platformStatus, setPlatformStatus] = useState<PlatformStatusResponse | null>(null)
  const [quotaDetail, setQuotaDetail] = useState<QuotaErrorDetail | null>(null)
  const [usage, setUsage] = useState<UsageSummary | null>(null)
  const [success, setSuccess] = useState('')
  const [recheckingId, setRecheckingId] = useState<number | null>(null)
  const [importing, setImporting] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [validating, setValidating] = useState(false)
  const [validationReport, setValidationReport] = useState<
    import('@/services/smm-service').ChannelsValidationResult | null
  >(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const hasBrands = brands.length > 0

  async function load() {
    setError('')
    setLoadingList(true)
    try {
      const [list, palette, platforms, usageSummary] = await Promise.all([
        smmService.listAllChannels(selectedBrandId ?? undefined),
        smmService.getPalette(),
        smmService.platformStatus().catch(() => null),
        smmService.getUsageSummary().catch(() => null),
      ])
      setChannels(list)
      setPlatformStatus(platforms)
      setUsage(usageSummary)
      setLimits({
        max_own_channels: palette.max_own_channels,
        tariff: (palette as { tariff?: string }).tariff,
      })
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoadingList(false)
    }
  }

  useEffect(() => {
    void refreshBrands()
  }, [refreshBrands])

  useEffect(() => {
    if (!hasBrands) {
      setChannels([])
      return
    }
    void load()
  }, [selectedBrandId, hasBrands])

  useEffect(() => {
    if (selectedBrandId) setBrandId(selectedBrandId)
    else if (brands[0]) setBrandId(brands[0].id)
  }, [selectedBrandId, brands])

  const ownCount = channels.filter((c) => c.role === 'own').length
  const hasReadyChannel = channels.some((c) => channelReady(c))
  const readyCount = channels.filter((c) => channelReady(c)).length
  const tgOwnPending = channels.filter(
    (c) => c.network === 'tg' && c.role === 'own' && c.auth_status !== 'connected',
  )
  const tgConnected = Boolean(platformStatus?.tg?.connected)

  const filtered = useMemo(() => {
    const q = filterTitle.trim().toLowerCase()
    return channels.filter((c) => {
      if (filterNetwork !== 'all' && c.network !== filterNetwork) return false
      if (!q) return true
      const hay = `${c.title || ''} ${c.external_id} ${c.brand_name || ''}`.toLowerCase()
      return hay.includes(q)
    })
  }, [channels, filterTitle, filterNetwork])

  async function handleAdd(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (!brandId) {
      setError('Выберите бренд')
      return
    }
    if (network !== 'url' && !externalId.trim()) {
      setError('Укажите ID канала')
      return
    }
    if (network === 'url' && !sourceUrl.trim()) {
      setError('Укажите URL страницы для сбора')
      return
    }
    setSaving(true)
    try {
      await smmService.addChannel(brandId, {
        network,
        external_id: network === 'url' ? undefined : externalId.trim(),
        title:
          network === 'url'
            ? title.trim() || undefined
            : title.trim() || externalId.trim(),
        url: network === 'url' ? sourceUrl.trim() : undefined,
        role: network === 'url' ? 'source' : role,
        kind:
          network === 'vk' ||
          network === 'url' ||
          network === 'instagram' ||
          network === 'threads' ||
          network === 'tw' ||
          network === 'dzen' ||
          network === 'wp'
            ? 'public'
            : 'channel',
      })
      setExternalId('')
      setTitle('')
      setSourceUrl('')
      await load()
      await refreshChannels()
    } catch (err) {
      const q = parseQuotaError(err)
      if (q) setQuotaDetail(q)
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function copyText(text: string, key: string) {
    const value = text.trim()
    if (!value) return
    try {
      await navigator.clipboard.writeText(value)
      setCopiedKey(key)
      window.setTimeout(() => setCopiedKey((prev) => (prev === key ? null : prev)), 1500)
    } catch {
      setError('Не удалось скопировать в буфер обмена')
    }
  }

  function downloadChannelsCsv() {
    const escapeCell = (value: unknown): string => {
      const s = value == null ? '' : String(value)
      if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`
      return s
    }
    const headers = [
      'id',
      'network',
      'external_id',
      'url',
      'title',
      'brand_id',
      'brand_name',
      'role',
      'kind',
      'auth_status',
      'publish_enabled',
      'collect_enabled',
      'review',
      'alert_enabled',
      'ready',
    ]
    const rows = filtered.map((row) => [
      row.id,
      row.network,
      row.external_id,
      row.network === 'url' ? row.url_config?.url || '' : '',
      row.title || '',
      row.brand_id,
      row.brand_name || '',
      row.role,
      row.kind,
      row.auth_status || '',
      row.publish_enabled ? '1' : '0',
      row.collect_enabled ? '1' : '0',
      reviewEnabled(row) ? '1' : '0',
      row.alert_enabled ? '1' : '0',
      channelReady(row) ? '1' : '0',
    ])
    const lines = [headers.join(','), ...rows.map((r) => r.map(escapeCell).join(','))]
    const blob = new Blob([`\uFEFF${lines.join('\n')}`], {
      type: 'text/csv;charset=utf-8',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')
    a.href = url
    a.download = `channels-${stamp}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function downloadChannelsJson() {
    const targetBrand = selectedBrandId ?? brandId
    setExporting(true)
    setError('')
    setSuccess('')
    try {
      const data = await smmService.exportChannels(targetBrand ?? undefined)
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json;charset=utf-8',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')
      const suffix = targetBrand ? `brand-${targetBrand}` : 'all'
      a.href = url
      a.download = `channels-${suffix}-${stamp}.json`
      a.click()
      URL.revokeObjectURL(url)
      setSuccess(
        `Экспорт: ${data.channels?.length ?? 0} канал(ов) с настройками` +
          (targetBrand ? ` (бренд #${targetBrand})` : ' (все бренды)'),
      )
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setExporting(false)
    }
  }

  async function handleImportFile(file: File) {
    const targetBrand = selectedBrandId ?? brandId
    if (!targetBrand) {
      setError('Выберите бренд — импорт идёт в конкретный бренд')
      return
    }
    setImporting(true)
    setError('')
    setSuccess('')
    setValidationReport(null)
    try {
      const result = await smmService.importChannelsFile(targetBrand, file, true)
      await load()
      await refreshChannels()
      const errN = result.errors?.length ?? 0
      const warnN = result.warnings?.length ?? 0
      const v = result.validation
      if (v) setValidationReport(v)
      setSuccess(
        `Импорт в бренд #${targetBrand}: создано ${result.created}, обновлено ${result.updated}` +
          (result.skipped ? `, пропущено ${result.skipped}` : '') +
          (errN ? `, ошибок импорта ${errN}` : '') +
          (warnN ? `, предупреждений ${warnN}` : '') +
          (v
            ? ` · валидация: ${v.accessible}/${v.checked} доступны` +
              (v.errors ? `, ${v.errors} проблем` : '') +
              (v.warnings ? `, ${v.warnings} предупр.` : '') +
              (v.ok ? ', OK' : '')
            : ''),
      )
      if (errN) {
        const first = result.errors[0]
        setError(
          `Часть каналов не импортирована: ${first.error}` +
            (errN > 1 ? ` (+${errN - 1})` : ''),
        )
      } else if (v && !v.ok) {
        setError(
          `После импорта найдены проблемы доступа/настроек (${v.errors}). См. отчёт ниже.`,
        )
      }
    } catch (err) {
      const q = parseQuotaError(err)
      if (q) setQuotaDetail(q)
      setError(getErrorMessage(err))
    } finally {
      setImporting(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  async function runValidation() {
    const targetBrand = selectedBrandId ?? brandId
    if (!targetBrand) {
      setError('Выберите бренд для проверки')
      return
    }
    setValidating(true)
    setError('')
    setSuccess('')
    try {
      const v = await smmService.validateChannels(targetBrand, true)
      setValidationReport(v)
      await load()
      await refreshChannels()
      setSuccess(
        v.ok
          ? `Проверка бренда #${targetBrand}: ${v.accessible}/${v.checked} каналов доступны, настройки OK`
          : `Проверка бренда #${targetBrand}: ${v.errors} ошибок, ${v.warnings} предупреждений`,
      )
      if (!v.ok) {
        setError(`Есть проблемы доступа или настроек — см. отчёт ниже`)
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setValidating(false)
    }
  }

  async function recheckAuth(ch: ChannelRow) {
    if (recheckingId != null) return
    try {
      setError('')
      setSuccess('')
      setRecheckingId(ch.id)
      const updated = await smmService.recheckChannelAuth(ch.id)
      await load()
      await refreshChannels()
      const auth = updated.auth_status || 'unknown'
      const pub =
        updated.role === 'own'
          ? updated.publish_enabled
            ? ', publish включён'
            : ', publish выключен'
          : ''
      setSuccess(
        `Recheck #${ch.id}: ${authStatusLabel(auth)}${pub}` +
          (updated.auth_error ? ` — ${updated.auth_error}` : ''),
      )
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setRecheckingId(null)
    }
  }

  async function remove(ch: ChannelRow) {
    try {
      await smmService.deleteChannel(ch.brand_id, ch.id)
      await load()
      await refreshChannels()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const columns: DataTableColumn<ChannelRow>[] = useMemo(
    () => [
      {
        key: 'network',
        header: 'Сеть',
        render: (_v, row) => (
          <span className="font-semibold uppercase tracking-wide text-[var(--text-primary)]">
            {networkLabel(row.network)}
          </span>
        ),
      },
      {
        key: 'external_id',
        header: 'ID / URL',
        render: (_v, row) => {
          const display =
            row.network === 'url'
              ? row.url_config?.url || row.title || row.external_id
              : row.external_id
          const copyValue =
            row.network === 'url'
              ? row.url_config?.url || row.title || row.external_id
              : row.external_id
          const key = `row-${row.id}`
          return (
            <div className="flex items-start gap-1.5 max-w-[12rem] sm:max-w-[16rem]">
              <code className="text-xs text-[var(--text-primary)] break-all flex-1 min-w-0">{display}</code>
              <button
                type="button"
                className="shrink-0 text-xs text-primary-400 hover:underline"
                title="Скопировать"
                onClick={() => void copyText(String(copyValue || ''), key)}
              >
                {copiedKey === key ? '✓' : 'Copy'}
              </button>
            </div>
          )
        },
      },
      {
        key: 'title',
        header: 'Title',
        render: (_v, row) => (
          <div className="min-w-[140px]">
            <div className="text-[var(--text-primary)] font-medium">
              {row.title || '—'}
            </div>
            {row.brand_name && (
              <div className="text-xs text-[var(--text-muted)] flex items-center gap-1.5 mt-0.5">
                <span
                  className="inline-block h-2 w-2 rounded-full shrink-0"
                  style={{ backgroundColor: row.brand_color || '#64748b' }}
                />
                {row.brand_name}
              </div>
            )}
          </div>
        ),
      },
      {
        key: 'role',
        header: 'Тип',
        render: (_v, row) => (
          <span className="text-xs uppercase tracking-wide text-[var(--text-secondary)]">
            {row.role}
          </span>
        ),
      },
      {
        key: 'auth_status',
        header: 'Auth',
        render: (_v, row) => (
          <div className="flex flex-col gap-1 min-w-[5rem]">
            <span
              className={`text-xs font-medium ${
                row.auth_status === 'connected' || row.auth_status === 'not_required'
                  ? 'text-emerald-400'
                  : 'text-amber-400'
              }`}
              title={row.auth_error || undefined}
            >
              {authStatusLabel(row.auth_status)}
            </span>
            {row.role !== 'competitor' && row.network !== 'url' && (
              <button
                type="button"
                className="text-xs text-primary-400 hover:underline text-left disabled:opacity-50"
                disabled={recheckingId === row.id}
                onClick={(e) => {
                  e.stopPropagation()
                  void recheckAuth(row)
                }}
              >
                {recheckingId === row.id ? 'Recheck…' : 'Recheck'}
              </button>
            )}
          </div>
        ),
      },
      {
        key: 'publish_enabled',
        header: 'Publish',
        render: (_v, row) => {
          const ready = publishReady(row)
          const on = !!row.publish_enabled
          return (
            <FlagStatusIcon
              on={on}
              warn={on && !ready}
              label="Publish"
              na={row.role !== 'own'}
              title={
                row.role !== 'own'
                  ? 'Publish только для own'
                  : ready
                    ? 'Готово: Publish + подтверждённый доступ'
                    : on
                      ? 'Publish включён, но ownership не подтверждён — Recheck'
                      : 'Publish выключен — «Настроить» → Публикация'
              }
            />
          )
        },
      },
      {
        key: 'collect_enabled',
        header: 'Collect',
        render: (_v, row) => {
          const ready = collectReady(row)
          const on = !!row.collect_enabled
          const toReview = reviewEnabled(row)
          const hasTargets = (row.publish_targets || []).length > 0
          return (
            <FlagStatusIcon
              on={on}
              warn={on && !ready}
              label="Collect"
              title={
                ready
                  ? toReview && !hasTargets
                    ? 'Готово: Collect → Review'
                    : toReview
                      ? 'Готово: Collect → targets + Review'
                      : 'Готово: Collect → publish targets'
                  : on
                    ? !hasTargets && !toReview
                      ? 'Collect включён: укажите цели публикации или Review'
                      : 'Collect включён, но нет доступа на чтение — Auth / Recheck'
                    : 'Collect выключен — «Настроить» → Сбор'
              }
            />
          )
        },
      },
      {
        key: 'review',
        header: 'Review',
        render: (_v, row) => {
          const on = reviewEnabled(row)
          return (
            <FlagStatusIcon
              on={on}
              label="Review"
              title={
                on
                  ? 'Собранные посты уходят на ручную проверку (status=review)'
                  : 'Review выключен — «Настроить» → Сбор/Обработка → «На review»'
              }
            />
          )
        },
      },
      {
        key: 'alert_enabled',
        header: 'Alert',
        render: (_v, row) => {
          const ready = alertReady(row)
          const on = !!row.alert_enabled
          return (
            <FlagStatusIcon
              on={on}
              warn={on && !ready}
              label="Alert"
              na={row.network !== 'tg' && row.network !== 'vk'}
              title={
                row.network !== 'tg' && row.network !== 'vk'
                  ? row.network === 'url'
                    ? 'Алерты недоступны для URL-источников'
                    : 'Алерты доступны для Telegram и VKontakte'
                  : ready
                    ? 'Готово: Alert + канал доставки + правила'
                    : on
                      ? 'Alert включён: укажите канал доставки, текст и ключевые слова'
                      : 'Alert выключен — «Настроить» → Алерты'
              }
            />
          )
        },
      },
      {
        key: 'ready',
        header: 'Ready',
        render: (_v, row) => {
          const ready = channelReady(row)
          return (
            <FlagStatusIcon
              on={ready}
              label="Ready"
              title={
                ready
                  ? 'Канал готов: Publish и/или Collect(+targets/Review) и/или Alert настроены'
                  : 'Не готов: нужен Publish (own+auth), либо Collect с targets/Review, либо Alert с доставкой'
              }
            />
          )
        },
      },
      {
        key: 'actions',
        header: '',
        render: (_v, row) => (
          <div className="flex items-center gap-2 justify-end whitespace-nowrap">
            <Link to={`/channels/${row.id}`}>
              <Button size="sm" variant="secondary">
                Настроить
              </Button>
            </Link>
            <Button size="sm" variant="ghost" onClick={() => void remove(row)}>
              Remove
            </Button>
          </div>
        ),
      },
    ],
    [channels, copiedKey, recheckingId],
  )

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="Channels"
        description="Единый хаб каналов · Brand → Channels → поток → Analytics"
      />
      {error && (
        <div className="mb-4" role="alert">
          <Alert variant="error">{error}</Alert>
        </div>
      )}
      {success && (
        <div className="mb-4" role="status">
          <Alert variant="success">{success}</Alert>
        </div>
      )}
      <QuotaBanner metrics={usage?.metrics} focusKey="max_own_channels" className="mb-4" />
      <QuotaUpgradeModal
        open={quotaDetail != null}
        detail={quotaDetail}
        onClose={() => setQuotaDetail(null)}
      />
      {!error && !tgConnected && hasBrands && (
        <Alert variant="info" className="mb-4">
          Для Collect/Publish по Telegram сначала авторизуйтесь:{' '}
          <Link to="/telegram" className="underline font-medium">
            Telegram → Auth
          </Link>
          . После кода вернитесь сюда и нажмите Recheck у канала.
        </Alert>
      )}
      {!error && tgConnected && tgOwnPending.length > 0 && (
        <Alert variant="info" className="mb-4">
          Telegram подключён. Подтвердите собственность: в таблице нажмите{' '}
          <strong>Recheck</strong> у канала
          {tgOwnPending.length === 1
            ? ` «${tgOwnPending[0].title || tgOwnPending[0].external_id}»`
            : ` (${tgOwnPending.length} шт.)`}
          , затем откройте <strong>Настроить</strong> и включите Publish. Collect можно
          настроить уже сейчас.
        </Alert>
      )}
      {!error && tgConnected && tgOwnPending.length === 0 && channels.some((c) => c.network === 'tg' && c.role === 'own') && (
        <Alert variant="success" className="mb-4">
          TG-каналы подтверждены. Флаги Publish / Collect / Alert задаются в{' '}
          <strong>Настроить</strong>. Далее —{' '}
          <Link to="/posts" className="underline">
            Posts
          </Link>
          .
        </Alert>
      )}

      {isLoadingBrands && !hasBrands ? (
        <p className="text-sm text-[var(--text-muted)]">Загрузка брендов…</p>
      ) : !hasBrands ? (
        <Card>
          <CardHeader>
            <CardTitle>Сначала создайте бренд</CardTitle>
            <CardDescription>
              Каналы привязываются к бренду. Без бренда добавлять и управлять каналами нельзя.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link
              to="/brands"
              className="inline-flex items-center text-sm font-medium text-primary-400 hover:underline"
            >
              Перейти в Brands →
            </Link>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card className="mb-4">
            <CardContent className="py-3 flex flex-wrap gap-4 text-sm">
              <span className="text-emerald-400">Brand ✓</span>
              <span className={channels.length ? 'text-emerald-400' : 'text-[var(--text-muted)]'}>
                Channels {channels.length ? '✓' : '· добавьте канал'}
              </span>
              <span className={hasReadyChannel ? 'text-emerald-400' : 'text-[var(--text-muted)]'}>
                Ready {hasReadyChannel ? `✓ ${readyCount}` : '· Publish / Collect+Review / Alert'}
              </span>
              <Link to="/analytics" className="text-primary-400 hover:underline ml-auto">
                Analytics →
              </Link>
            </CardContent>
          </Card>

          <div className="flex flex-wrap gap-3 mb-4 text-sm text-[var(--text-secondary)]">
            <span>
              Own: {ownCount}
              {limits.max_own_channels != null ? ` / ${limits.max_own_channels}` : ''}
            </span>
            {limits.tariff && <span className="uppercase">Plan: {limits.tariff}</span>}
            <Link to="/brands" className="text-primary-400 hover:underline">
              Manage brands →
            </Link>
            <Link to={networkSetupUrl('tg')} className="text-primary-400 hover:underline">
              Telegram auth →
            </Link>
            <Link to={networkSetupUrl('vk')} className="text-primary-400 hover:underline">
              VK auth →
            </Link>
            <Link to={networkSetupUrl('instagram')} className="text-primary-400 hover:underline">
              IG auth →
            </Link>
            <Link to="/custom-url" className="text-primary-400 hover:underline">
              Custom URL / posts →
            </Link>
            <Link to="/inbox" className="text-primary-400 hover:underline">
              Inbox →
            </Link>
          </div>

          <Card className="mb-4">
            <CardHeader>
              <CardTitle>Add channel</CardTitle>
              <CardDescription>
                Любая сеть пайплайна: TG / VK / IG / Threads / TW / Дзен / WP / URL
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={handleAdd}
                className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6 items-end"
              >
                <div>
                  <label className="text-sm text-[var(--text-secondary)]">Brand</label>
                  <select
                    className="w-full mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                    value={brandId ?? ''}
                    onChange={(e) => {
                      const id = e.target.value ? Number(e.target.value) : null
                      setBrandId(id)
                      if (id) setSelectedBrandId(id)
                    }}
                  >
                    {brands.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-[var(--text-secondary)]">Сеть</label>
                  <select
                    className="w-full mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                    value={network}
                    onChange={(e) => {
                      const next = e.target.value as BrandNetwork
                      setNetwork(next)
                      if (next === 'url') setRole('source')
                    }}
                  >
                    {BRAND_NETWORKS.map((net) => (
                      <option key={net} value={net}>
                        {NETWORK_LABELS[net]}
                      </option>
                    ))}
                  </select>
                </div>
                {network !== 'url' ? (
                  <div>
                    <label className="text-sm text-[var(--text-secondary)]">
                      {network === 'tg' || network === 'vk' ? 'ID канала' : 'Handle / ID'}
                    </label>
                    <div className="mt-1 flex gap-2">
                      <input
                        value={externalId}
                        onChange={(e) => setExternalId(e.target.value)}
                        placeholder={
                          network === 'tg'
                            ? '-100…'
                            : network === 'vk'
                              ? '236… / club… / onlinestudies'
                              : '@username / site'
                        }
                        className="flex-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                      />
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        disabled={!externalId.trim()}
                        onClick={() => void copyText(externalId, 'form-id')}
                        title="Скопировать ID"
                      >
                        {copiedKey === 'form-id' ? 'Скопировано' : 'Copy'}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="text-sm text-[var(--text-secondary)]">URL страницы</label>
                    <div className="mt-1 flex gap-2">
                      <input
                        type="url"
                        value={sourceUrl}
                        onChange={(e) => setSourceUrl(e.target.value)}
                        placeholder="https://example.com/news"
                        className="flex-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                      />
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        disabled={!sourceUrl.trim()}
                        onClick={() => void copyText(sourceUrl, 'form-url')}
                        title="Скопировать URL"
                      >
                        {copiedKey === 'form-url' ? 'Скопировано' : 'Copy'}
                      </Button>
                    </div>
                  </div>
                )}
                <Input
                  label={network === 'url' ? 'Название (опционально)' : 'Title'}
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder={network === 'url' ? 'Smart-Lab map' : undefined}
                />
                <div>
                  <label className="text-sm text-[var(--text-secondary)]">Тип</label>
                  <select
                    className="w-full mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                    value={network === 'url' ? 'source' : role}
                    disabled={network === 'url'}
                    onChange={(e) => setRole(e.target.value as ChannelRole)}
                  >
                    <option value="own">own</option>
                    <option value="source">source</option>
                    <option value="competitor">competitor</option>
                  </select>
                </div>
                <Button type="submit" disabled={saving || !brandId}>
                  {saving ? 'Adding…' : 'Add'}
                </Button>
              </form>
              {network !== 'url' && network !== 'tg' && network !== 'vk' && (
                <p className="text-xs text-[var(--text-muted)] mt-3">
                  Auth:{' '}
                  <Link
                    to={networkSetupUrl(network)}
                    className="text-primary-400 hover:underline"
                  >
                    {NETWORK_LABELS[network]}
                  </Link>
                  {' → '}затем Recheck / Bind в карточке канала.
                </p>
              )}
            </CardContent>
          </Card>

          <div className="flex flex-wrap gap-3 mb-3 items-end">
            <div className="min-w-[180px] flex-1">
              <Input
                label="Filter by title"
                value={filterTitle}
                onChange={(e) => setFilterTitle(e.target.value)}
                placeholder="Title / id / brand"
              />
            </div>
            <div>
              <label className="text-sm text-[var(--text-secondary)]">Network</label>
              <select
                className="block mt-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                value={filterNetwork}
                onChange={(e) =>
                  setFilterNetwork(e.target.value as 'all' | BrandNetwork)
                }
              >
                <option value="all">All</option>
                {BRAND_NETWORKS.map((net) => (
                  <option key={net} value={net}>
                    {NETWORK_LABELS[net]}
                  </option>
                ))}
              </select>
            </div>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={filtered.length === 0}
              onClick={downloadChannelsCsv}
              title="Скачать текущую таблицу (с учётом фильтра) в CSV — без вложенных настроек"
            >
              Download CSV
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={exporting || channels.length === 0}
              onClick={() => void downloadChannelsJson()}
              title={
                selectedBrandId || brandId
                  ? 'Скачать JSON выбранного бренда: Collect/Alert/условия/targets'
                  : 'Скачать JSON всех брендов (импорт потом — в выбранный бренд)'
              }
            >
              {exporting ? 'Export…' : 'Download JSON'}
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/json,.json"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) void handleImportFile(f)
              }}
            />
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={importing || !(selectedBrandId ?? brandId)}
              onClick={() => fileInputRef.current?.click()}
              title="Загрузить JSON в выбранный бренд (создаёт / обновляет по network+id), затем проверка доступа"
            >
              {importing ? 'Import…' : 'Upload JSON'}
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={validating || !(selectedBrandId ?? brandId) || channels.length === 0}
              onClick={() => void runValidation()}
              title="Recheck доступа и проверка Collect/Alert/Publish/targets для бренда"
            >
              {validating ? 'Validate…' : 'Validate'}
            </Button>
          </div>

          {validationReport && (
            <Card className="mb-4">
              <CardHeader>
                <CardTitle className="text-base">Отчёт проверки</CardTitle>
                <CardDescription>
                  Бренд #{validationReport.brand_id}: доступны {validationReport.accessible}/
                  {validationReport.checked}
                  {validationReport.errors
                    ? ` · ошибок ${validationReport.errors}`
                    : ''}
                  {validationReport.warnings
                    ? ` · предупреждений ${validationReport.warnings}`
                    : ''}
                  {validationReport.ok ? ' · всё в порядке' : ''}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {validationReport.issues.length === 0 ? (
                  <p className="text-sm text-emerald-400">
                    Все каналы доступны, флаги Collect/Alert/Publish и targets согласованы.
                  </p>
                ) : (
                  <ul className="space-y-2 max-h-64 overflow-y-auto text-sm">
                    {validationReport.issues.map((issue, i) => (
                      <li
                        key={`${issue.channel_id}-${issue.code}-${i}`}
                        className={
                          issue.severity === 'error'
                            ? 'text-red-400'
                            : 'text-amber-400/90'
                        }
                      >
                        <span className="font-medium uppercase text-xs tracking-wide">
                          {issue.severity}
                        </span>
                        {' · '}
                        <Link
                          to={`/channels/${issue.channel_id}`}
                          className="underline text-[var(--text-primary)]"
                        >
                          #{issue.channel_id}
                        </Link>{' '}
                        <span className="text-[var(--text-muted)]">
                          {(issue.network || '').toUpperCase()}
                          {issue.external_id ? ` / ${issue.external_id}` : ''}
                          {issue.title ? ` · ${issue.title}` : ''}
                        </span>
                        <div className="text-[var(--text-secondary)] pl-0 sm:pl-4">
                          {issue.message}
                          <span className="text-[var(--text-muted)] text-xs ml-2">
                            ({issue.code})
                          </span>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          )}

          <DataTable
            columns={columns}
            data={filtered}
            keyExtractor={(row) => row.id}
            isLoading={loadingList}
            rowClassName={(row) =>
              channelReady(row)
                ? 'bg-emerald-500/10 even:bg-emerald-500/15 hover:bg-emerald-500/20'
                : undefined
            }
            emptyMessage={
              channels.length === 0
                ? 'Нет каналов — добавьте выше'
                : 'Нет совпадений по фильтру'
            }
          />
          <p className="mt-2 text-xs text-[var(--text-muted)]">
            Зелёная строка = канал готов: Publish (own+auth), либо Collect с целями/Review, либо
            Alert с доставкой. Жёлтый значок = флаг включён, но настройка неполная.
          </p>
        </>
      )}
    </PageContainer>
  )
}
