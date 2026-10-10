import type { TopicDeck } from '@/data/learning-map/decks/types'

export const deckDev: TopicDeck = {
  branchTitle: 'Разработка',
  cards: [
    {
      id: 'pool:dev:layers',
      front: `Что такое слои сервиса?`,
      back: `Разделение HTTP/API, use-case/domain, инфраструктура (БД, очереди). Зависимости внутрь, не из domain в UI-фреймворк.`,
      learnSlug: 's01e01-sloi',
    },
    {
      id: 'pool:dev:system-map',
      front: `Зачем карта системы?`,
      back: `Общий язык компонентов и потоков данных до кодирования. Снижает сюрпризы интеграций.`,
      learnSlug: 's01e02-karta',
    },
    {
      id: 'pool:dev:fastapi-health',
      front: `Зачем /health?`,
      back: `Пробы оркестратора/балансера: процесс жив, опционально зависимости. Не смешивайте с тяжёлой бизнес-логикой.`,
      learnSlug: 'b04-fastapi-health',
    },
    {
      id: 'pool:dev:contract',
      front: `Что такое контракт API?`,
      back: `Схема запросов/ответов, коды ошибок, семантика. OpenAPI/тесты контракта ловят breaking changes.`,
      learnSlug: 's01e05-fastapi',
    },
    {
      id: 'pool:dev:react-list',
      front: `Ключи в списке React?`,
      back: `Стабильный key помогает reconcile. Индекс массива — риск при перестановках. Ключ из id сущности.`,
      learnSlug: 'b08-react-list',
    },
    {
      id: 'pool:dev:react-form',
      front: `Контролируемые поля?`,
      back: `value + onChange → state источник истины. Удобно валидировать и блокировать submit.`,
      learnSlug: 'b09-react-form',
    },
    {
      id: 'pool:dev:compose-stand',
      front: `Склейка стенда?`,
      back: `Один compose/сеть: UI → API → БД. Единый .env и healthcheck ускоряют онбординг.`,
      learnSlug: 'b12-sklejka',
    },
    {
      id: 'pool:dev:notes-api',
      front: `CRUD Notes — что проверить?`,
      back: `Валидация, коды HTTP, идемпотентность PUT, ошибки 404, миграция данных.`,
      learnSlug: 'b07-notes-api',
    },
    {
      id: 'pool:dev:python-api',
      front: `Python для API — минимум?`,
      back: `Типы, async I/O, структура пакета, работа с HTTP-клиентом/БД без блокировок event loop.`,
      learnSlug: 'b03-python',
    },
    {
      id: 'pool:dev:app-map',
      front: `Карта первого приложения?`,
      back: `Границы модулей, вход HTTP, хранилище. Помогает не смешать UI-логику с persistence.`,
      learnSlug: 'b01-karta',
    },
    {
      id: 'pool:dev:react-ui',
      front: `Компонент vs страница?`,
      back: `Переиспользуемые куски UI vs маршрут с данными. Держите сайд-эффекты ближе к краю.`,
      learnSlug: 's01e10-react',
    },
    {
      id: 'pool:dev:dto',
      front: `Зачем DTO/схемы Pydantic?`,
      back: `Валидация на границе, явный контракт, меньше «dict сюрпризов». Ошибки 422 понятны клиенту.`,
      learnSlug: 's01e05-fastapi',
    },
    {
      id: 'pool:dev:stateless',
      front: `Stateless API?`,
      back: `Сервер не хранит сессию в памяти инстанса: auth в токене/внешнем store. Нужно для горизонтального масштаба.`,
      learnSlug: 's01e01-sloi',
    },
    {
      id: 'pool:dev:error-model',
      front: `Единая модель ошибок?`,
      back: `Код, сообщение, details. Клиенты и логи говорят на одном языке. Не отдавайте стек наружу.`,
      learnSlug: 's01e05-fastapi',
    },
    {
      id: 'pool:dev:cors-dev',
      front: `CORS на учебном стенде?`,
      back: `Разрешайте нужные origin в dev; в проде — явно. Прокси Vite часто снимает боль локально.`,
      learnSlug: 'b12-sklejka',
    },
    {
      id: 'pool:dev:id-generation',
      front: `Кто генерирует id?`,
      back: `БД sequence/UUID на сервере предпочтительнее клиентских счётчиков. Документируйте формат.`,
      learnSlug: 'b07-notes-api',
    },
    {
      id: 'pool:dev:pagination',
      front: `Зачем пагинация списка?`,
      back: `Ограничение нагрузки и предсказуемый UX. Cursor/offset — trade-off простоты и стабильности.`,
      learnSlug: 'b08-react-list',
    },
    {
      id: 'pool:dev:env-config',
      front: `Конфиг через env?`,
      back: `Секреты и URL не хардкодить. 12-factor: конфиг среды, одинаковый артефакт.`,
      learnSlug: 'b04-fastapi-health',
    },
    {
      id: 'pool:dev:boundary',
      front: `Граница домена?`,
      back: `Бизнес-правила не зависят от FastAPI/React. Легче тестировать и менять доставку.`,
      learnSlug: 's01e01-sloi',
    },
    {
      id: 'pool:dev:smoke-stand',
      front: `Smoke стенда после compose up?`,
      back: `health API, открытие UI, один CRUD. Автоматизируйте в CI по возможности.`,
      learnSlug: 'b12-sklejka',
    },
  ],
}
