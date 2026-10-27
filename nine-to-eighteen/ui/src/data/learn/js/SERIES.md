> Короткие выпуски этой серии объединены в сводные статьи. Живой файл — первый выпуск группы, его текст включает соседние темы. Старые slug в таблицах ниже отдельно больше не открываются и заново их заводить не нужно. Ссылки из таблиц ведут на сводный выпуск.

# Серия JavaScript Learn (язык)

Карта **6 выпусков** языковой базы перед React. React — сезон B (`b08-react-list` и далее), не в этой папке.

Пишите и правьте тела по [`../article-template.md`](../article-template.md).

## Источники (reading list, не копипаст)

Канон формулировок и ссылок в постах:

| Источник | Зачем |
|----------|--------|
| [MDN Web Docs — JavaScript Guide / Reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript) | typeof, функции, `this`, Promise, `fetch`, DOM, JSON |
| [ECMAScript® Language Specification (ECMA-262)](https://tc39.es/ecma262/) | правила `==` / Abstract Equality, семантика `this` |
| [javascript.info](https://javascript.info/) | дополнительное чтение тем же порядком (типы → функции → промисы → DOM → JSON) |

В текстах выпусков — **оригинальные** русские разборы и примеры; MDN / ECMA / javascript.info — в блоке «Ссылки» как список для углубления, не как абзацы для копирования.

## Конвенции

| Поле | Значение |
|------|----------|
| Файлы | `js01-….md` … `js06-….md` рядом с этим файлом |
| `episode` | `JS01` … `JS06` |
| `order` | `850` … `855` |
| `profiles` | `[developer, tester]` |
| `rubric` | `frontend` |
| `onKnowledgeMap` | `true` (+ тег `собеседование`) |
| `prerequisites` | предыдущий slug (линейный трек) |
| Seed | `import_js_learn_series.py` |

---

## Эпизоды

| Ep | slug | Файл | Фокус |
|----|------|------|--------|
| JS01 | `js-types-coerce` | [`js01-types-coerce.md`](js01-types-coerce.md) | Примитивы, typeof, `==`/`===`, falsy |
| JS02 | `js-functions-this` | [`js02-functions-this.md`](js02-functions-this.md) | Function vs arrow, this, bind |
| JS03 | `js-async-fetch` | [`js03-async-fetch.md`](js03-async-fetch.md) | Promise, async/await, fetch + `ok` |
| JS04 | `js-dom-events` | [`js04-dom-events.md`](js04-dom-events.md) | DOM, listeners, делегирование, XSS |
| JS05 | `js-json-xml` | [`js05-json-xml.md`](js05-json-xml.md) | JSON.parse/stringify, DOMParser |
| JS06 | `js-capstone` | [`js06-capstone.md`](js06-capstone.md) | Drill JS01–JS05 → мост к React B08 |

**После серии:** [b08-react-list](/game/learn/b05-api-check).
