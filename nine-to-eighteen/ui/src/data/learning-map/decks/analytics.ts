import type { TopicDeck } from '@/data/learning-map/decks/types'

export const deckAnalytics: TopicDeck = {
  branchTitle: 'Аналитика и продукт',
  cards: [
    {
      id: 'pool:analytics:sa-intro',
      front: `Системный анализ на карте — фокус?`,
      back: `Требования, границы системы, интеграции. Связка с серией СА глубже — здесь вход для смешанных профилей.`,
      learnSlug: 's01e03-git',
    },
    {
      id: 'pool:analytics:requirements',
      front: `Как дробить требования?`,
      back: `Эпики → истории → критерии приёмки. Трассировка к тестам и дизайну.`,
      learnSlug: 'sa-requirements-basics',
    },
    {
      id: 'pool:analytics:backlog-prio',
      front: `Приоритизация бэклога?`,
      back: `Ценность/риск/effort, прозрачные правила (RICE/WSJF). Регулярный refinement.`,
      learnSlug: 'pm-product-management',
    },
    {
      id: 'pool:analytics:acceptance',
      front: `Критерии приёмки?`,
      back: `Проверяемые условия Done для истории. Given/When/Then или чеклист — главное измеримость.`,
      learnSlug: 'sa-requirements-basics',
    },
    {
      id: 'pool:analytics:stakeholder-map',
      front: `Карта стейкхолдеров?`,
      back: `Кто влияет/интересуется; каналы коммуникации. Снижает сюрпризы на демо.`,
      learnSlug: 'pm-product-management',
    },
    {
      id: 'pool:analytics:as-is-to-be',
      front: `AS-IS / TO-BE?`,
      back: `Текущий и целевой процесс. Разрыв = объём изменений и риски.`,
      learnSlug: 's01e03-git',
    },
    {
      id: 'pool:analytics:nonfunctional',
      front: `NFR в лёгком анализе?`,
      back: `Зафиксируйте измеримо хотя бы perf/security/доступность для критичных сценариев.`,
      learnSlug: 'sa-requirements-basics',
    },
    {
      id: 'pool:analytics:mvp-scope',
      front: `Scope MVP с аналитиком?`,
      back: `Отрезаем must для обучения/ценности, явный out-of-scope. Защита от расползания.`,
      learnSlug: 'pm-product-management',
    },
    {
      id: 'pool:analytics:traceability',
      front: `Трассировка требований?`,
      back: `Связь требование→дизайн→тест→релиз. Нужна при аудите и сложных доменах.`,
      learnSlug: 'sa-requirements-basics',
    },
    {
      id: 'pool:analytics:workshop',
      front: `Зачем discovery-сессия?`,
      back: `Синхронизировать язык домена и цели до детальной спецификации.`,
      learnSlug: 's01e03-git',
    },
    {
      id: 'pool:analytics:risk-req',
      front: `Риски в требованиях?`,
      back: `Неясные термины, скрытые NFR, зависимости вендоров. Явно в реестре рисков.`,
      learnSlug: 'sa-requirements-basics',
    },
    {
      id: 'pool:analytics:demo',
      front: `Демо как обратная связь?`,
      back: `Показать инкремент стейкхолдерам, собрать правки в backlog — не «отчёт о статусе».`,
      learnSlug: 'pm-product-management',
    },
    {
      id: 'pool:analytics:invariants',
      front: `Бизнес-инварианты?`,
      back: `Правила, которые всегда истинны (баланс, статусы). Их тестируют и кодируют явно.`,
      learnSlug: 's01e03-git',
    },
    {
      id: 'pool:analytics:change-request',
      front: `CR vs новый scope?`,
      back: `Оценка влияния на срок/бюджет/риски, приоритизация. Прозрачность важнее скорости «да».`,
      learnSlug: 'pm-product-management',
    },
    {
      id: 'pool:analytics:glossary',
      front: `Глоссарий домена?`,
      back: `Одинаковые термины у бизнеса и команды. Дешёвый способ снизить дефекты недопонимания.`,
      learnSlug: 'sa-requirements-basics',
    },
  ],
}
