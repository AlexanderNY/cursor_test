import type { TopicDeck } from '@/data/learning-map/decks/types'

export const deckTesting: TopicDeck = {
  branchTitle: 'Тестирование',
  cards: [
    {
      id: 'pool:testing:qa-map',
      front: `QA на карте тестирования?`,
      back: `Стратегия и тест-дизайн для смешанных ролей; глубокая серия — в ветке QA.`,
      learnSlug: 'qa-intro-testing',
    },
    {
      id: 'pool:testing:e2e-local',
      front: `E2E локально?`,
      back: `Сквозной сценарий на стенде: UI+API+БД. Дорогой, но ловит склейку. Держите тонкий набор.`,
      learnSlug: 'qa-aqa-principles',
    },
    {
      id: 'pool:testing:pyramid-map',
      front: `Пирамида на практике?`,
      back: `Много unit, меньше integration, ещё меньше e2e. Инверсия пирамиды замедляет CI.`,
      learnSlug: 'qa-intro-testing',
    },
    {
      id: 'pool:testing:fixture',
      front: `Фикстуры данных?`,
      back: `Предсказуемое начальное состояние. Изоляция тестов друг от друга обязательна.`,
      learnSlug: 'qa-aqa-principles',
    },
    {
      id: 'pool:testing:assert',
      front: `Хороший assert?`,
      back: `Одна проверка смысла, понятное сообщение. Не проверяйте всё подряд в одном кейсе без нужды.`,
      learnSlug: 'qa-intro-testing',
    },
    {
      id: 'pool:testing:env-parity',
      front: `Паритет окружений?`,
      back: `Чем ближе staging к prod (данные/конфиг), тем меньше «у нас работает». Контейнеры помогают.`,
      learnSlug: 'qa-aqa-principles',
    },
    {
      id: 'pool:testing:smoke-ci',
      front: `Smoke в CI?`,
      back: `Быстрый набор после деплоя/PR. Падение — стоп-кран релиза.`,
      learnSlug: 'qa-intro-testing',
    },
    {
      id: 'pool:testing:test-double',
      front: `Test double?`,
      back: `Stub/mock/fake/spy — подмены зависимостей. Цель — стабильность и скорость unit-слоя.`,
      learnSlug: 'qa-intro-testing',
    },
    {
      id: 'pool:testing:flaky-e2e',
      front: `Почему e2e flaky?`,
      back: `Тайминги UI, общие данные, внешние сервисы. Явные ожидания и изоляция.`,
      learnSlug: 'qa-aqa-principles',
    },
    {
      id: 'pool:testing:coverage',
      front: `Покрытие кода?`,
      back: `Индикатор пробелов, не цель 100%. Важнее покрытие рисков и критичных путей.`,
      learnSlug: 'qa-intro-testing',
    },
    {
      id: 'pool:testing:contract-map',
      front: `Контракт API в тестах?`,
      back: `Схема ответа/статусы как тест. Ломающие изменения видны до полного UI e2e.`,
      learnSlug: 'qa-aqa-principles',
    },
    {
      id: 'pool:testing:manual',
      front: `Когда ручной тест незаменим?`,
      back: `UX-эвристики, исследовательские сессии, одноразовые риски. Дополняет автоматизацию.`,
      learnSlug: 'qa-intro-testing',
    },
    {
      id: 'pool:testing:data-cleanup',
      front: `Очистка после теста?`,
      back: `finally/fixtures teardown, транзакции rollback, уникальные префиксы данных.`,
      learnSlug: 'qa-aqa-principles',
    },
    {
      id: 'pool:testing:shift-left-map',
      front: `Shift-left на карте?`,
      back: `Ревью требований и unit раньше дорогих e2e. QA влияет на дизайн.`,
      learnSlug: 'qa-intro-testing',
    },
    {
      id: 'pool:testing:report',
      front: `Отчёт о прогоне?`,
      back: `Что бежало, что упало, артефакты (логи/скрины), воспроизведение. Без этого CI бесполезен людям.`,
      learnSlug: 'qa-aqa-principles',
    },
  ],
}
