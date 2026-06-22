---
name: Time Series Graphs UI
overview: Создание нового раздела "Graphs" с кастомным компонентом временных рядов на чистом React/TypeScript без сторонних библиотек, с поддержкой масштабирования, легендой и обработкой null-значений.
todos:
  - id: create-types
    content: Создать types.ts с интерфейсами TimeSeries, ChartProps, и др.
    status: completed
  - id: create-colors
    content: Создать utils/colors.ts с палитрой 20 цветов
    status: completed
  - id: create-scales
    content: Создать utils/scales.ts с функциями масштабирования
    status: completed
  - id: create-data-generator
    content: Создать utils/data-generator.ts для тестовых данных
    status: completed
  - id: create-dimensions-hook
    content: Создать hooks/useChartDimensions.ts
    status: completed
  - id: create-zoom-hook
    content: Создать hooks/useZoom.ts для zoom/pan
    status: completed
  - id: create-legend
    content: Создать Legend.tsx с toggle visibility
    status: completed
  - id: create-tooltip
    content: Создать Tooltip.tsx для hover
    status: completed
  - id: create-zoom-controls
    content: Создать ZoomControls.tsx
    status: completed
  - id: create-chart-canvas
    content: Создать ChartCanvas.tsx с SVG отрисовкой
    status: completed
  - id: create-main-component
    content: Создать TimeSeriesChart.tsx - основной компонент
    status: completed
  - id: create-index
    content: Создать index.ts с экспортами
    status: completed
  - id: create-page
    content: Создать pages/graphs.tsx
    status: completed
  - id: update-routing
    content: Добавить роут /graphs в App.tsx
    status: completed
  - id: update-nav
    content: Добавить пункт Graphs в навигацию
    status: completed
isProject: false
---

# Time Series Graphs UI Section

## Архитектура компонента

```mermaid
flowchart TB
    subgraph GraphsPage [Graphs Page]
        TimeSeriesChart
    end
    
    subgraph TimeSeriesChart [TimeSeriesChart Component]
        Canvas[SVG Canvas]
        Legend[Legend Panel]
        Controls[Zoom Controls]
        Tooltip[Hover Tooltip]
    end
    
    subgraph DataLayer [Data Layer]
        Generator[Test Data Generator]
        Transform[Data Transformer]
    end
    
    DataLayer --> TimeSeriesChart
    Legend -->|toggle visibility| Canvas
    Controls -->|zoom/pan| Canvas
    Canvas -->|hover| Tooltip
```



## Структура файлов

Новая папка: `[ui-app/src/components/graphs/](ui-app/src/components/graphs/)`

```
graphs/
├── index.ts                    # Экспорты
├── TimeSeriesChart.tsx         # Основной компонент графика
├── types.ts                    # TypeScript типы
├── Legend.tsx                  # Компонент легенды
├── ChartCanvas.tsx             # SVG canvas для отрисовки
├── ZoomControls.tsx            # Контролы масштабирования
├── Tooltip.tsx                 # Тултип при наведении
├── utils/
│   ├── colors.ts               # Палитра из 20 цветов
│   ├── scales.ts               # Функции масштабирования осей
│   └── data-generator.ts       # Генератор тестовых данных
└── hooks/
    ├── useChartDimensions.ts   # Хук для размеров canvas
    └── useZoom.ts              # Хук для zoom/pan
```

## Ключевые решения

### 1. Отрисовка на SVG (не Canvas)

- Лучшая интеграция с React
- Проще обработка событий hover/click
- Поддержка CSS-стилизации
- Достаточная производительность для 20 линий x 120 точек

### 2. Масштабирование

- **Wheel zoom**: колесо мыши для zoom in/out
- **Drag pan**: перетаскивание для смещения
- **Кнопки**: +/- для zoom, Reset для сброса
- **Brush selection**: выделение области для zoom (опционально)

### 3. Обработка null-значений

- Разрыв линии в точках с null
- Визуально: линия прерывается и продолжается после null

```typescript
// Пример: [1, 2, null, 4, 5] -> две отдельные линии
// Линия 1: точки 0-1 (значения 1, 2)
// Линия 2: точки 3-4 (значения 4, 5)
```

### 4. Легенда

- Список всех 20 серий с цветом и названием
- Клик по элементу скрывает/показывает линию
- Визуальная индикация скрытых серий (opacity/strikethrough)

### 5. Палитра цветов

20 различимых цветов с хорошим контрастом для светлой/темной темы.

## Интеграция

### Роутинг

Добавить в `[ui-app/src/App.tsx](ui-app/src/App.tsx)`:

```typescript
import GraphsPage from './pages/graphs';
// ...
<Route path="/graphs" element={<GraphsPage />} />
```

### Навигация

Добавить в `[ui-app/src/config/nav.tsx](ui-app/src/config/nav.tsx)`:

```typescript
{
  name: 'Graphs',
  href: '/graphs',
  icon: ChartBarIcon,
}
```

### Страница

Создать `[ui-app/src/pages/graphs.tsx](ui-app/src/pages/graphs.tsx)` с использованием компонента `TimeSeriesChart`.

## API компонента

```typescript
interface TimeSeriesChartProps {
  data: TimeSeries[];        // Массив временных рядов
  width?: number;            // Ширина (по умолчанию 100%)
  height?: number;           // Высота (по умолчанию 400px)
  showLegend?: boolean;      // Показывать легенду
  enableZoom?: boolean;      // Включить масштабирование
}

interface TimeSeries {
  id: string;
  name: string;
  values: (number | null)[];  // null = отсутствие данных
  color?: string;             // Опциональный цвет
}
```

## Тестовые данные

Генератор создаст 20 временных рядов по 120 значений:

- Базовые синусоиды/косинусоиды с разными фазами и амплитудами
- Случайный шум
- ~10-15% null-значений в случайных позициях

