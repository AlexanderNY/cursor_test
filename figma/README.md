# Kubernetes Cluster Management Interface (Figma)

Макет: **Kubernetes Cluster Management Interface**  
Источник: [Figma](https://www.figma.com/make/JSZZXeysdTnr77yLob13qY/Kubernetes-Cluster-Management-Interface) (доступ к файлу требует авторизации в Figma).

Вёрстка выполнена по названию макета и типичной структуре K8s-дашбордов. После открытия макета в Figma можно уточнить отступы, цвета и состав экранов по скриншотам или Dev Mode.

## Структура

```
figma/
  assets/           # картинки, иконки из Figma (при экспорте)
  components/       # React-компоненты макета
    index.ts        # реэкспорт
    K8sDashboard.tsx   # корневой экран
    K8sHeader.tsx
    K8sSidebar.tsx
    ClusterCard.tsx
    MetricCard.tsx
    NodeTable.tsx
    StatusBadge.tsx
  types.ts          # типы для пропсов (ClusterSummary, NodeRow, ClusterStatus и т.д.)
  README.md         # этот файл
```

## Стек

- React 18, TypeScript, Tailwind CSS (те же классы и переменные, что в ui-app: `--bg-primary`, `--text-primary`, `primary-*`, `accent-*`). Отдельного конфига Tailwind в figma нет — при сборке превью используются настройки ui-app.

## Подключение в ui-app

1. **Превью:** в ui-app добавлен роут `/figma-preview`, который рендерит `K8sDashboard` из `figma/components`.

2. **Перенос в приложение:** скопировать нужные файлы из `figma/components/` и `figma/assets/` в ui-app (например, `src/components/figma/` или по фичам). Классы Tailwind уже совместимы с ui-app.

## Компоненты

| Компонент     | Назначение |
|---------------|------------|
| K8sDashboard  | Корневой экран: сайдбар + хедер + блоки Overview, Clusters, Nodes. |
| K8sHeader     | Шапка с заголовком и кнопками «Add cluster», Refresh. |
| K8sSidebar    | Боковое меню (Overview, Clusters, Nodes, Pods, Deployments, Settings). |
| ClusterCard   | Карточка кластера (имя, статус, nodes/pods, CPU/Memory). |
| MetricCard    | Карточка метрики (label, value, опционально trend). |
| NodeTable     | Таблица нод (Name, Status, Roles, CPU, Memory, Age). |
| StatusBadge   | Бейдж статуса (Running, Warning, Error, Pending). |

Иконки в сайдбаре и хедере реализованы inline SVG в компонентах. При необходимости их можно вынести в `figma/assets/` и подключать по путям.
