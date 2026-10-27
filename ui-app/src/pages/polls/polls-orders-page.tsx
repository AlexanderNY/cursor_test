import { EmptyState } from '@/components/ui/empty-state'
import { OrdersSection } from './orders-section'
import { usePollsContext } from './polls-context'

export function PollsOrdersPage() {
  const { selectedBotId, hasMenuModes } = usePollsContext()

  if (!selectedBotId) {
    return (
      <EmptyState
        title="Выберите бота"
        description="Добавьте или выберите Telegram-бота в настройках выше."
      />
    )
  }

  if (!hasMenuModes) {
    return (
      <EmptyState
        title="Нет режимов меню"
        description="Стол заказов появится в боте после перезапуска: категории, профиль и корзина."
      />
    )
  }

  return (
    <OrdersSection
      modeId={null}
      botId={selectedBotId}
      filterByMode={false}
      className="mt-0"
    />
  )
}
