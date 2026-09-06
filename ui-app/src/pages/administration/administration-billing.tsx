import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { authService } from '@/services/auth-service'
import type { BillingPlanRequest, PromoCode } from '@/types/auth'
import { getErrorMessage } from '@/services/api-client'
import { formatDateTime } from '@/utils/date'
import { formatRub, PLAN_REQUEST_STATUS_LABEL } from '@/lib/billing'

export function AdministrationBillingPanel() {
  const [requests, setRequests] = useState<BillingPlanRequest[]>([])
  const [promos, setPromos] = useState<PromoCode[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [invoiceNote, setInvoiceNote] = useState('')
  const [invoicePreview, setInvoicePreview] = useState('')
  const [promoCode, setPromoCode] = useState('')
  const [promoPercent, setPromoPercent] = useState('20')
  const [promoAmount, setPromoAmount] = useState('')
  const [promoMode, setPromoMode] = useState<'percent' | 'amount'>('percent')
  const [promoPlan, setPromoPlan] = useState('')
  const [promoDesc, setPromoDesc] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      const [req, codes] = await Promise.all([
        authService.adminListPlanRequests(),
        authService.adminListPromoCodes(),
      ])
      setRequests(req)
      setPromos(codes)
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function sendInvoice(id: number) {
    setBusyId(id)
    setError('')
    try {
      const updated = await authService.adminSendInvoice(id, invoiceNote.trim() || undefined)
      setRequests((prev) => prev.map((r) => (r.id === id ? updated : r)))
      setInvoicePreview(updated.invoice_body || '')
      if (updated.smtp_configured === false || updated.invoice_smtp_sent === false) {
        setError('SMTP не настроен: счёт сохранён, письмо не ушло. Скопируйте текст ниже или задайте SMTP_HOST/SMTP_FROM.')
      }
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setBusyId(null)
    }
  }

  async function applyRequest(id: number) {
    setBusyId(id)
    setError('')
    try {
      const updated = await authService.adminApplyPlanRequest(id)
      setRequests((prev) => prev.map((r) => (r.id === id ? updated : r)))
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setBusyId(null)
    }
  }

  async function rejectRequest(id: number) {
    setBusyId(id)
    setError('')
    try {
      const updated = await authService.adminRejectPlanRequest(id)
      setRequests((prev) => prev.map((r) => (r.id === id ? updated : r)))
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setBusyId(null)
    }
  }

  async function createPromo() {
    setError('')
    try {
      const created = await authService.adminCreatePromoCode({
        code: promoCode.trim().toUpperCase(),
        description: promoDesc.trim() || undefined,
        discount_percent: promoMode === 'percent' ? Number(promoPercent) : undefined,
        discount_amount: promoMode === 'amount' ? Number(promoAmount) : undefined,
        applies_to_tariff: promoPlan || undefined,
      })
      setPromos((prev) => [created, ...prev])
      setPromoCode('')
      setPromoDesc('')
    } catch (e) {
      setError(getErrorMessage(e))
    }
  }

  async function togglePromo(p: PromoCode) {
    try {
      const updated = await authService.adminUpdatePromoCode(p.id, { is_active: !p.is_active })
      setPromos((prev) => prev.map((x) => (x.id === p.id ? updated : x)))
    } catch (e) {
      setError(getErrorMessage(e))
    }
  }

  const openRequests = requests.filter((r) => r.status === 'pending' || r.status === 'invoiced')

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Заявки на тариф</CardTitle>
          <CardDescription>
            Заявка с Pricing или кнопка Save в Users. Дальше: счёт на почту или ручное включение тарифа.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="secondary" onClick={() => void load()} isLoading={loading}>
              Обновить
            </Button>
            <Input
              value={invoiceNote}
              onChange={(e) => setInvoiceNote(e.target.value)}
              placeholder="Комментарий в счёте (реквизиты)"
              className="max-w-md"
            />
          </div>
          {error && <Alert variant="error">{error}</Alert>}
          {openRequests.length === 0 && !loading && (
            <p className="text-sm text-[var(--text-muted)]">Открытых заявок нет</p>
          )}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[var(--text-muted)] border-b border-[var(--border-color)]">
                  <th className="py-2 pr-2">#</th>
                  <th className="py-2 pr-2">Пользователь</th>
                  <th className="py-2 pr-2">Тариф</th>
                  <th className="py-2 pr-2">Сумма</th>
                  <th className="py-2 pr-2">Статус</th>
                  <th className="py-2">Действия</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((r) => (
                  <tr key={r.id} className="border-b border-[var(--border-color)] align-top">
                    <td className="py-2 pr-2">{r.id}</td>
                    <td className="py-2 pr-2">
                      <div>{r.username || r.user_id}</div>
                      <div className="text-xs text-[var(--text-muted)]">{r.email}</div>
                      <div className="text-xs text-[var(--text-muted)]">{formatDateTime(r.created_at)}</div>
                    </td>
                    <td className="py-2 pr-2">
                      {r.current_tariff} → {r.requested_tariff}
                      {r.promo_code ? <div className="text-xs">промо {r.promo_code}</div> : null}
                    </td>
                    <td className="py-2 pr-2">
                      {formatRub(r.final_price, r.currency)}
                      {r.discount_amount > 0 && (
                        <div className="text-xs text-[var(--text-muted)]">
                          было {formatRub(r.list_price, r.currency)}
                        </div>
                      )}
                    </td>
                    <td className="py-2 pr-2">{PLAN_REQUEST_STATUS_LABEL[r.status] ?? r.status}</td>
                    <td className="py-2">
                      {(r.status === 'pending' || r.status === 'invoiced') && (
                        <div className="flex flex-wrap gap-2">
                          <Button
                            size="sm"
                            variant="secondary"
                            disabled={busyId === r.id}
                            onClick={() => void sendInvoice(r.id)}
                          >
                            Счёт на почту
                          </Button>
                          <Button
                            size="sm"
                            disabled={busyId === r.id}
                            onClick={() => void applyRequest(r.id)}
                          >
                            Включить тариф
                          </Button>
                          <Button
                            size="sm"
                            variant="danger"
                            disabled={busyId === r.id}
                            onClick={() => void rejectRequest(r.id)}
                          >
                            Отклонить
                          </Button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {invoicePreview && (
            <pre className="text-xs whitespace-pre-wrap rounded-xl border border-[var(--border-color)] p-3 bg-[var(--bg-tertiary)]">
              {invoicePreview}
            </pre>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Промокоды</CardTitle>
          <CardDescription>Процент или фиксированная скидка в рублях. Один код — один раз на пользователя.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            <Input label="Код" value={promoCode} onChange={(e) => setPromoCode(e.target.value.toUpperCase())} />
            <Input label="Описание" value={promoDesc} onChange={(e) => setPromoDesc(e.target.value)} />
            <select
              className="h-11 mt-auto rounded-xl border border-[var(--border-color)] bg-[var(--bg-tertiary)] px-3 text-sm"
              value={promoMode}
              onChange={(e) => setPromoMode(e.target.value as 'percent' | 'amount')}
            >
              <option value="percent">Скидка %</option>
              <option value="amount">Скидка ₽</option>
            </select>
            {promoMode === 'percent' ? (
              <Input label="Процент" type="number" value={promoPercent} onChange={(e) => setPromoPercent(e.target.value)} />
            ) : (
              <Input label="Сумма ₽" type="number" value={promoAmount} onChange={(e) => setPromoAmount(e.target.value)} />
            )}
            <select
              className="h-11 mt-auto rounded-xl border border-[var(--border-color)] bg-[var(--bg-tertiary)] px-3 text-sm"
              value={promoPlan}
              onChange={(e) => setPromoPlan(e.target.value)}
            >
              <option value="">Все платные тарифы</option>
              <option value="standard">Только Standard</option>
              <option value="full">Только Full</option>
            </select>
            <Button type="button" onClick={() => void createPromo()} className="mt-auto">
              Создать
            </Button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[var(--text-muted)] border-b border-[var(--border-color)]">
                  <th className="py-2 pr-2">Код</th>
                  <th className="py-2 pr-2">Скидка</th>
                  <th className="py-2 pr-2">Тариф</th>
                  <th className="py-2 pr-2">Использовано</th>
                  <th className="py-2">Статус</th>
                </tr>
              </thead>
              <tbody>
                {promos.map((p) => (
                  <tr key={p.id} className="border-b border-[var(--border-color)]">
                    <td className="py-2 pr-2 font-medium">{p.code}</td>
                    <td className="py-2 pr-2">
                      {p.discount_percent ? `${p.discount_percent}%` : formatRub(p.discount_amount ?? 0)}
                    </td>
                    <td className="py-2 pr-2">{p.applies_to_tariff || 'все'}</td>
                    <td className="py-2 pr-2">
                      {p.redeemed_count}
                      {p.max_redemptions != null ? ` / ${p.max_redemptions}` : ''}
                    </td>
                    <td className="py-2">
                      <Button size="sm" variant="secondary" onClick={() => void togglePromo(p)}>
                        {p.is_active ? 'Выключить' : 'Включить'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {promos.length === 0 && <p className="text-sm text-[var(--text-muted)] py-3">Пока нет промокодов</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
