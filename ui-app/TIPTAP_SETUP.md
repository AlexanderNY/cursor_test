# TipTap Editor Setup

## Установка зависимостей

Для работы TipTap редактора необходимо установить следующие пакеты:

```bash
npm install @tiptap/react @tiptap/starter-kit @tiptap/extension-placeholder @tiptap/extension-underline
```

## Использование

TipTap редактор уже интегрирован в раздел WordPress. Компонент находится в `src/components/ui/tiptap-editor.tsx`.

### Пример использования:

```tsx
import { TipTapEditor } from '@/components/ui/tiptap-editor'

function MyComponent() {
  const [content, setContent] = useState('')

  return (
    <TipTapEditor
      content={content}
      onChange={setContent}
      placeholder="Enter your content..."
      toolbarButtons={['bold', 'italic', 'underline', 'strike', 'heading', 'bulletList', 'orderedList', 'blockquote', 'code', 'codeBlock', 'horizontalRule', 'undo', 'redo']}
    />
  )
}
```

## Настройка кнопок

Вы можете настроить набор кнопок в панели инструментов, передав массив `toolbarButtons`:

- `bold` - Жирный текст
- `italic` - Курсив
- `underline` - Подчеркивание
- `strike` - Зачеркивание
- `heading` - Заголовки (H1, H2, H3)
- `bulletList` - Маркированный список
- `orderedList` - Нумерованный список
- `blockquote` - Цитата
- `code` - Инлайн код
- `codeBlock` - Блок кода
- `horizontalRule` - Горизонтальная линия
- `undo` - Отменить
- `redo` - Повторить

## Формат данных

Редактор возвращает HTML контент через callback `onChange`. Это идеально подходит для WordPress, который использует HTML формат для контента постов.
