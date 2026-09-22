# Python Learn series

Оглавление трека Junior → Senior: [`SERIES.md`](SERIES.md).

Шаблон поста: [`../article-template.md`](../article-template.md).

## Выпуски PY01–PY24

Все 24 файла `py*.md` в этой папке — полные статьи в формате шаблона. Они в [`core/data/learn_seed.json`](../../../../../../core/data/learn_seed.json) и [`../episodes.ts`](../episodes.ts).

Импорт / обновление seed:

```bash
python core/scripts/import_python_learn_pilots.py
python core/scripts/generate_learn_episodes_ts.py
```

Скрипт сам находит все `py*.md`.

## Как править выпуск

1. Редактируйте соответствующий `pyNN-….md`.
2. Сохраняйте секции шаблона (≥3 тест, ≥3 Anki, лаба, mermaid, HTML-шпаргалка).
3. Ответы на собеседовании — **своими словами**; источник тем: [DEBAGanov 400 Q&A](https://github.com/DEBAGanov/interview_questions/blob/main/400%20вопросов%20с%20ответами%2C%20которые%20должен%20знать%20Python-разработчик.md).
4. Перегоните seed командами выше.

Конвенции: `episode` PY01–PY24, `order` 301–324, `profiles: [developer]`, `onKnowledgeMap: true`.
