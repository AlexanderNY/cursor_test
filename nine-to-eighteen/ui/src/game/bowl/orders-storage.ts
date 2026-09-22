/** Between-match orders meta (local only). */

export const ORDERS_KEY = 'bowl-orders-v1'

export type BowlOrderId = 'rations' | 'spike_kit' | 'shell_polish' | 'dash_boots'

export type BowlOrderDef = {
  id: BowlOrderId
  title: string
  cost: number
  description: string
  /** Starting perk levels granted for next new game after purchase (one-shot). */
  perkBoost?: Partial<Record<string, number>>
  healHint?: string
}

export const ORDER_CATALOG: BowlOrderDef[] = [
  {
    id: 'rations',
    title: 'Паёк',
    cost: 15,
    description: '+20 стартового red на следующий матч (через буст «глаз» не даём — просто кредит).',
    healHint: 'Кредит на следующий запуск: +1 к любому перку на выбор в начале.',
  },
  {
    id: 'spike_kit',
    title: 'Набор шипов',
    cost: 25,
    description: 'Следующий матч стартует с Шип I.',
    perkBoost: { spike: 1 },
  },
  {
    id: 'shell_polish',
    title: 'Полировка панциря',
    cost: 30,
    description: 'Следующий матч стартует с Панцирь I.',
    perkBoost: { shell: 1 },
  },
  {
    id: 'dash_boots',
    title: 'Сапоги рывка',
    cost: 35,
    description: 'Следующий матч стартует с Рывок+ I.',
    perkBoost: { dash: 1 },
  },
]

export type BowlOrdersState = {
  credits: number
  owned: BowlOrderId[]
  /** One-shot perk levels applied on next newGame, then cleared. */
  pendingPerkBoost: Record<string, number>
  matchesPlayed: number
}

const EMPTY: BowlOrdersState = {
  credits: 0,
  owned: [],
  pendingPerkBoost: {},
  matchesPlayed: 0,
}

export function loadOrders(): BowlOrdersState {
  try {
    const raw = localStorage.getItem(ORDERS_KEY)
    if (!raw) {
      return { ...EMPTY, owned: [], pendingPerkBoost: {} }
    }
    const parsed = JSON.parse(raw) as Partial<BowlOrdersState>
    return {
      credits: Math.max(0, Number(parsed.credits) || 0),
      owned: Array.isArray(parsed.owned)
        ? (parsed.owned.filter((id) =>
            ORDER_CATALOG.some((o) => o.id === id),
          ) as BowlOrderId[])
        : [],
      pendingPerkBoost:
        parsed.pendingPerkBoost && typeof parsed.pendingPerkBoost === 'object'
          ? Object.fromEntries(
              Object.entries(parsed.pendingPerkBoost).map(([k, v]) => [k, Math.max(0, Number(v) || 0)]),
            )
          : {},
      matchesPlayed: Math.max(0, Number(parsed.matchesPlayed) || 0),
    }
  } catch {
    return { ...EMPTY, owned: [], pendingPerkBoost: {} }
  }
}

export function saveOrders(state: BowlOrdersState): void {
  localStorage.setItem(ORDERS_KEY, JSON.stringify(state))
}

export function awardMatchCredits(enemiesEaten: number, survivedBoss: boolean): BowlOrdersState {
  const state = loadOrders()
  const gained = Math.max(5, Math.floor(enemiesEaten / 2) + (survivedBoss ? 20 : 0))
  const next: BowlOrdersState = {
    ...state,
    credits: state.credits + gained,
    matchesPlayed: state.matchesPlayed + 1,
  }
  saveOrders(next)
  return next
}

export function purchaseOrder(orderId: BowlOrderId): { ok: boolean; message: string; state: BowlOrdersState } {
  const state = loadOrders()
  const def = ORDER_CATALOG.find((o) => o.id === orderId)
  if (!def) {
    return { ok: false, message: 'Неизвестный заказ', state }
  }
  if (state.credits < def.cost) {
    return { ok: false, message: 'Недостаточно кредитов', state }
  }
  const pending = { ...state.pendingPerkBoost }
  if (def.perkBoost) {
    for (const [perk, level] of Object.entries(def.perkBoost)) {
      const nextLevel = Number(level) || 0
      pending[perk] = Math.max(pending[perk] || 0, nextLevel)
    }
  }
  const next: BowlOrdersState = {
    ...state,
    credits: state.credits - def.cost,
    owned: state.owned.includes(orderId) ? state.owned : [...state.owned, orderId],
    pendingPerkBoost: pending,
  }
  saveOrders(next)
  return { ok: true, message: 'Заказ оформлен — буст на следующий матч', state: next }
}

export function consumePendingPerkBoost(): Record<string, number> {
  const state = loadOrders()
  const boost = { ...state.pendingPerkBoost }
  if (Object.keys(boost).length === 0) {
    return {}
  }
  saveOrders({ ...state, pendingPerkBoost: {} })
  return boost
}
