import { Fragment, useCallback, useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { EmptyState } from '@/components/ui/empty-state'
import { TableSkeleton } from '@/components/ui/skeleton'
import { gameService } from '@/services/game-service'
import type { GameMenuOrder } from '@/types/game'
import { formatOrderMoney } from '@/utils/menu-price'
import { formatDateTime } from '@/utils/date'

interface OrdersSectionProps {
  modeId: number | null
  modeTitle?: string
  botId: number | null
  filterByMode?: boolean
  className?: string
}

function formatPlayerName(
  username?: string | null,
  firstName?: string | null,
  telegramUserId?: number,
): string {
  if (username) return `@${username}`
  if (firstName) return firstName
  return telegramUserId ? String(telegramUserId) : '—'
}

function formatDate(iso?: string | null): string {
  return formatDateTime(iso)
}

export function OrdersSection({
  modeId,
  modeTitle,
  botId,
  filterByMode = false,
  className = 'mt-6',
}: OrdersSectionProps) {
  const [orders, setOrders] = useState<GameMenuOrder[]>([])
  const [expandedOrderId, setExpandedOrderId] = useState<number | null>(null)
  const [orderDetails, setOrderDetails] = useState<Record<number, GameMenuOrder>>({})
  const [loadingDetailId, setLoadingDetailId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const loadOrders = useCallback(async () => {
    if (!botId) {
      setOrders([])
      setIsLoading(false)
      return
    }
    setIsLoading(true)
    setError('')
    try {
      const data = await gameService.listOrders(
        filterByMode && modeId ? modeId : undefined,
        botId,
        100,
      )
      setOrders(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить заказы')
      setOrders([])
    } finally {
      setIsLoading(false)
    }
  }, [modeId, botId, filterByMode])

  useEffect(() => {
    loadOrders()
  }, [loadOrders])

  async function toggleOrderDetails(orderId: number) {
    if (expandedOrderId === orderId) {
      setExpandedOrderId(null)
      return
    }
    setExpandedOrderId(orderId)
    if (orderDetails[orderId]?.items?.length) {
      return
    }
    setLoadingDetailId(orderId)
    try {
      const detail = await gameService.getOrder(orderId)
      setOrderDetails((prev) => ({ ...prev, [orderId]: detail }))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить состав заказа')
    } finally {
      setLoadingDetailId(null)
    }
  }

  if (!botId) {
    return null
  }

  const description = filterByMode && modeTitle
    ? `Заказы режима «${modeTitle}»`
    : 'Все оформленные заказы бота из режимов «Меню»'

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-lg">Заказы</CardTitle>
            <CardDescription>{description}. Нажмите «Обновить» после оформления в боте.</CardDescription>
          </div>
          <Button type="button" variant="secondary" size="sm" onClick={loadOrders} disabled={isLoading}>
            Обновить
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="error" className="mb-4">
            {error}
          </Alert>
        )}

        {isLoading ? (
          <TableSkeleton rows={5} />
        ) : orders.length === 0 ? (
          <EmptyState
            title="Заказов пока нет"
            description="Когда пользователи оформят заказ через бота, записи появятся здесь."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border-color)] text-left text-[var(--text-secondary)]">
                  <th className="pb-2 pr-3 font-medium">Номер</th>
                  {!filterByMode && <th className="pb-2 pr-3 font-medium">Режим</th>}
                  <th className="pb-2 pr-3 font-medium">Клиент</th>
                  <th className="pb-2 pr-3 font-medium">Позиций</th>
                  <th className="pb-2 pr-3 font-medium">Сумма</th>
                  <th className="pb-2 pr-3 font-medium">Дата</th>
                  <th className="pb-2 font-medium">Состав</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => {
                  const isExpanded = expandedOrderId === order.id
                  const detail = orderDetails[order.id]
                  const colSpan = filterByMode ? 6 : 7
                  return (
                    <Fragment key={order.id}>
                      <tr className="border-b border-[var(--border-color)]/60">
                        <td className="py-3 pr-3 font-mono text-[var(--text-primary)]">
                          {order.order_number}
                        </td>
                        {!filterByMode && (
                          <td className="py-3 pr-3 text-[var(--text-secondary)]">
                            {order.mode_title}
                          </td>
                        )}
                        <td className="py-3 pr-3 text-[var(--text-primary)]">
                          {formatPlayerName(
                            order.username,
                            order.first_name,
                            order.telegram_user_id,
                          )}
                        </td>
                        <td className="py-3 pr-3 text-[var(--text-secondary)]">
                          {order.total_quantity}
                        </td>
                        <td className="py-3 pr-3 font-medium text-[var(--text-primary)] whitespace-nowrap">
                          {formatOrderMoney(order.total_amount)}
                        </td>
                        <td className="py-3 pr-3 text-[var(--text-secondary)] whitespace-nowrap">
                          {formatDate(order.created_at)}
                        </td>
                        <td className="py-3">
                          <Button
                            type="button"
                            size="sm"
                            variant="secondary"
                            isLoading={loadingDetailId === order.id}
                            onClick={() => toggleOrderDetails(order.id)}
                          >
                            {isExpanded ? 'Скрыть' : 'Показать'}
                          </Button>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="border-b border-[var(--border-color)]/40">
                          <td colSpan={colSpan} className="py-3 pl-2">
                            {loadingDetailId === order.id ? (
                              <p className="text-sm text-[var(--text-secondary)]">Загрузка…</p>
                            ) : detail?.items?.length ? (
                              <div className="space-y-2 text-sm">
                                <table className="w-full max-w-xl text-sm">
                                  <thead>
                                    <tr className="text-left text-[var(--text-secondary)]">
                                      <th className="pb-1 pr-3 font-medium">Позиция</th>
                                      <th className="pb-1 pr-3 font-medium">Кол-во</th>
                                      <th className="pb-1 pr-3 font-medium">Цена</th>
                                      <th className="pb-1 font-medium">Сумма</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {detail.items.map((item) => (
                                      <tr key={item.id} className="text-[var(--text-primary)]">
                                        <td className="py-1 pr-3">{item.title}</td>
                                        <td className="py-1 pr-3">{item.quantity}</td>
                                        <td className="py-1 pr-3 whitespace-nowrap">
                                          {formatOrderMoney(item.unit_price)}
                                        </td>
                                        <td className="py-1 whitespace-nowrap">
                                          {formatOrderMoney(
                                            item.line_total ??
                                              (item.unit_price ?? 0) * item.quantity,
                                          )}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                                <p className="pt-1 font-semibold text-[var(--text-primary)]">
                                  Итого: {formatOrderMoney(detail.total_amount)}
                                </p>
                              </div>
                            ) : (
                              <p className="text-sm text-[var(--text-secondary)]">Состав не загружен</p>
                            )}
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
