import type { TopicDeck } from '@/data/learning-map/decks/types'

export const deckDevops: TopicDeck = {
  branchTitle: 'DevOps',
  cards: [
    {
      id: 'pool:devops:image',
      front: `Что такое Docker-образ?`,
      back: `Слоистая неизменяемая сборка ФС+метаданные для контейнера. Теги и multi-stage уменьшают размер/секреты.`,
      learnSlug: 'b10-docker',
    },
    {
      id: 'pool:devops:compose',
      front: `Docker Compose?`,
      back: `Описание многоконтейнерного стенда: сети, volumes, depends_on. Для локалки и простых деплоев.`,
      learnSlug: 'b11-compose',
    },
    {
      id: 'pool:devops:cicd',
      front: `CI vs CD?`,
      back: `CI — сборка/тесты на изменение; CD — доставка артефакта на среды. Пайплайн как код.`,
      learnSlug: 'map-cicd',
    },
    {
      id: 'pool:devops:k8s',
      front: `Kubernetes обзорно?`,
      back: `Оркестрация контейнеров: Pod/Deployment/Service. Декларативное желаемое состояние.`,
      learnSlug: 'map-k8s',
    },
    {
      id: 'pool:devops:networking',
      front: `Путь HTTP-запроса?`,
      back: `DNS → LB/ingress → сервис → под → app. Таймауты и TLS на каждом hops.`,
      learnSlug: 'map-networking',
    },
    {
      id: 'pool:devops:healthcheck',
      front: `HEALTHCHECK/пробы?`,
      back: `liveness/readiness отделяют «процесс жив» и «готов принимать трафик». Ложные пробы = флапы.`,
      learnSlug: 'b10-docker',
    },
    {
      id: 'pool:devops:layers-cache',
      front: `Кэш слоёв Docker?`,
      back: `Порядок Dockerfile: редко меняемое сверху. Иначе каждый билд тянет зависимости заново.`,
      learnSlug: 'b10-docker',
    },
    {
      id: 'pool:devops:secrets',
      front: `Секреты в контейнерах?`,
      back: `Не в образе/ENV в git. Runtime mount/secret store. Ротация и least privilege.`,
      learnSlug: 'b11-compose',
    },
    {
      id: 'pool:devops:blue-green',
      front: `Blue/green или canary?`,
      back: `Стратегии выката с быстрым откатом/постепенным трафиком. Нужны метрики и совместимость схемы.`,
      learnSlug: 'map-cicd',
    },
    {
      id: 'pool:devops:ingress',
      front: `Ingress?`,
      back: `HTTP(S) вход в кластер: маршрутизация host/path, TLS. Связка с Service.`,
      learnSlug: 'map-k8s',
    },
    {
      id: 'pool:devops:observability',
      front: `Логи, метрики, трейсы?`,
      back: `Три столпа: что случилось, насколько плохо, где в графе вызовов. Без них инциденты дольше.`,
      learnSlug: 'map-networking',
    },
    {
      id: 'pool:devops:immutable',
      front: `Immutable infrastructure?`,
      back: `Не патчим живые серверы — выкатываем новый артефакт. Воспроизводимость и откат.`,
      learnSlug: 'map-cicd',
    },
    {
      id: 'pool:devops:volume',
      front: `Volume vs слой контейнера?`,
      back: `Данные в контейнере эфемерны. Volume переживает recreate — для БД/загрузок.`,
      learnSlug: 'b11-compose',
    },
    {
      id: 'pool:devops:resource',
      front: `requests/limits?`,
      back: `Гарантии и потолки CPU/RAM в k8s. Без них noisy neighbor и OOMKill сюрпризы.`,
      learnSlug: 'map-k8s',
    },
    {
      id: 'pool:devops:dns',
      front: `DNS в отладке?`,
      back: `Неверный hostname/TTL кэша — частый «сеть сломалась». Проверяйте resolve с нужного сегмента.`,
      learnSlug: 'map-networking',
    },
    {
      id: 'pool:devops:artifact',
      front: `Артефакт пайплайна?`,
      back: `Образ/пакет с версией и SBOM по возможности. Один артефакт на все среды, разный конфиг.`,
      learnSlug: 'map-cicd',
    },
    {
      id: 'pool:devops:rootless',
      front: `Почему не root в контейнере?`,
      back: `Меньшая поверхность при побеге. USER non-root + read-only FS где можно.`,
      learnSlug: 'b10-docker',
    },
    {
      id: 'pool:devops:service-mesh',
      front: `Service mesh идея?`,
      back: `Sidecar для mTLS/retries/метрик между сервисами. Цена сложности — не для каждого масштаба.`,
      learnSlug: 'map-k8s',
    },
    {
      id: 'pool:devops:tls',
      front: `TLS termination где?`,
      back: `На edge/ingress или end-to-end. Понимание, где шифрование заканчивается, важно для угроз.`,
      learnSlug: 'map-networking',
    },
    {
      id: 'pool:devops:rollback',
      front: `Откат деплоя?`,
      back: `Предыдущий образ/ревизия Deployment плюс совместимость миграций. Репетируйте заранее.`,
      learnSlug: 'map-cicd',
    },
  ],
}
