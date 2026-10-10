import type { TopicDeck } from '@/data/learning-map/decks/types'

export const deckTools: TopicDeck = {
  branchTitle: 'Инструменты',
  cards: [
    {
      id: 'pool:tools:git-basic',
      front: `git status/add/commit — зачем ритуал?`,
      back: `Понятный history и безопасные точки отката. Мелкие осмысленные коммиты легче ревьюить.`,
      learnSlug: 's01e03-git',
    },
    {
      id: 'pool:tools:branch-pr',
      front: `Ветка и PR?`,
      back: `Изоляция изменения, ревью, CI на PR. Защита main — базовая гигиена.`,
      learnSlug: 'b06-git-branch',
    },
    {
      id: 'pool:tools:rebase-merge',
      front: `merge vs rebase?`,
      back: `merge сохраняет факт слияния; rebase линеаризует. Не rebaseйте публичную историю без договорённости.`,
      learnSlug: 'b06-git-branch',
    },
    {
      id: 'pool:tools:regex',
      front: `Зачем regex на собесе?`,
      back: `Валидации, парсинг логов, поиск. Знайте классы символов, квантификаторы, жадность, границы.`,
      learnSlug: 's01e09-regex',
    },
    {
      id: 'pool:tools:insomnia',
      front: `Проверка API в Insomnia/Postman?`,
      back: `Коллекции запросов, env,断言. Быстрый ручной/полуавтоматический контракт.`,
      learnSlug: 's01e06-insomnia',
    },
    {
      id: 'pool:tools:curl',
      front: `curl для API?`,
      back: `Скриптуемые запросы в CI/терминале: методы, заголовки, тело. Основа отладки без GUI.`,
      learnSlug: 'b05-api-check',
    },
    {
      id: 'pool:tools:git-zero',
      front: `Git с нуля — ключевые объекты?`,
      back: `blob/tree/commit, ссылки веток. Понимание модели спасает от «магии» reset/revert.`,
      learnSlug: 'b02-git',
    },
    {
      id: 'pool:tools:conflict',
      front: `Конфликт слияния?`,
      back: `Обе стороны меняли одни строки. Разрешите осознанно, протестируйте, не коммитьте маркеры.`,
      learnSlug: 'b06-git-branch',
    },
    {
      id: 'pool:tools:gitignore',
      front: `.gitignore?`,
      back: `Не коммитить секреты, билды, venv. Секреты — в менеджере/env, не в истории.`,
      learnSlug: 's01e03-git',
    },
    {
      id: 'pool:tools:regex-groups',
      front: `Группы в regex?`,
      back: `() захват, (?:) non-capturing. Нужны для замены и извлечения полей.`,
      learnSlug: 's01e09-regex',
    },
    {
      id: 'pool:tools:http-methods',
      front: `GET vs POST на проверке API?`,
      back: `GET — чтение/идемпотентность; POST — создание/действие. Не кладите секреты в query без нужды.`,
      learnSlug: 'b05-api-check',
    },
    {
      id: 'pool:tools:collections',
      front: `Зачем коллекции запросов?`,
      back: `Онбординг, регрессия ручная, единые env для стендов. Версионируйте рядом с кодом.`,
      learnSlug: 's01e06-insomnia',
    },
    {
      id: 'pool:tools:cherry-pick',
      front: `cherry-pick?`,
      back: `Перенос одного коммита. Осторожно с зависимостями и дублями при позднем merge.`,
      learnSlug: 'b06-git-branch',
    },
    {
      id: 'pool:tools:tag',
      front: `Теги релизов?`,
      back: `Неизменяемые метки версий для деплоя/changelog. Annotated tags предпочтительны.`,
      learnSlug: 's01e03-git',
    },
    {
      id: 'pool:tools:verbose-curl',
      front: `Как дебажить HTTP curl?`,
      back: `-v смотрит заголовки; -i включает статус в вывод. Сертификаты/прокси — частые блокеры.`,
      learnSlug: 'b05-api-check',
    },
    {
      id: 'pool:tools:stash',
      front: `git stash?`,
      back: `Временно убрать локальные изменения. Не используйте как долговременное хранилище фич.`,
      learnSlug: 'b02-git',
    },
    {
      id: 'pool:tools:regex-anchor',
      front: `^ и $ ?`,
      back: `Якоря начала/конца строки. Без них паттерн матчит подстроку — частая ошибка валидации.`,
      learnSlug: 's01e09-regex',
    },
    {
      id: 'pool:tools:pr-review',
      front: `Что просят в PR?`,
      back: `Зачем изменение, как проверить, риски. Маленький diff > огромный «всё сразу».`,
      learnSlug: 'b06-git-branch',
    },
    {
      id: 'pool:tools:reset-revert',
      front: `reset vs revert?`,
      back: `reset двигает ветку (опасно на shared); revert создаёт новый коммит-отмену — безопасно для main.`,
      learnSlug: 'b02-git',
    },
    {
      id: 'pool:tools:auth-header',
      front: `Authorization header в проверках?`,
      back: `Bearer/токен в env коллекции, не в скриншотах. Ротация секретов стенда.`,
      learnSlug: 's01e06-insomnia',
    },
  ],
}
