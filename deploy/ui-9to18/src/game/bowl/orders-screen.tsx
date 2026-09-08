import { useState } from 'react'
import {
  ORDER_CATALOG,
  loadOrders,
  purchaseOrder,
  type BowlOrdersState,
} from './orders-storage'

interface OrdersScreenProps {
  onBack: () => void
}

export function OrdersScreen({ onBack }: OrdersScreenProps) {
  const [state, setState] = useState<BowlOrdersState>(() => loadOrders())
  const [message, setMessage] = useState('')

  return (
    <div className="bowl-screen bowl-menu">
      <div className="bowl-menu-card" style={{ maxWidth: 520 }}>
        <div className="bowl-brand">
          <span className="bowl-brand-mark">Bowl</span>
          <span className="bowl-brand-domain">заказы</span>
        </div>
        <h1 className="bowl-title">Внутриигровые заказы</h1>
        <p className="bowl-subtitle">
          Кредиты копятся после матчей (локально). Покупка даёт буст перка на следующий запуск.
        </p>
        <p className="bowl-subtitle">
          Баланс: <strong>{state.credits}</strong> · матчей: {state.matchesPlayed}
          {Object.keys(state.pendingPerkBoost).length > 0
            ? ` · ожидает буст: ${Object.entries(state.pendingPerkBoost)
                .map(([k, v]) => `${k} ${v}`)
                .join(', ')}`
            : ''}
        </p>

        <div className="bowl-menu-actions" style={{ gap: '0.65rem' }}>
          {ORDER_CATALOG.map((order) => (
            <button
              key={order.id}
              type="button"
              className="bowl-btn"
              onClick={() => {
                const result = purchaseOrder(order.id)
                setState(result.state)
                setMessage(result.message)
              }}
            >
              {order.title} · {order.cost} кр.
              <span style={{ display: 'block', fontSize: '0.8em', opacity: 0.8, marginTop: 4 }}>
                {order.description}
              </span>
            </button>
          ))}
        </div>

        {message ? <p className="bowl-subtitle">{message}</p> : null}

        <button type="button" className="bowl-btn bowl-btn-primary" onClick={onBack} style={{ marginTop: 12 }}>
          Назад
        </button>
      </div>
    </div>
  )
}
