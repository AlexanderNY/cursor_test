---
slug: sql-indexes-basics
title: Индексы в SQL — зачем, виды, clustered vs nonclustered
shortTitle: Индексы basics
episode: SQL06
rubric: data
order: 606
publishedAt: 2027-04-11T10:00:00+03:00
profiles: [developer, analyst, tester]
level: junior
tags: [sql, index, btree, clustered, postgresql, собеседование]
onKnowledgeMap: true
durationMin: 30
excerpt: Что такое индекс, clustered и nonclustered, типы индексов. Акцент на B-tree в PostgreSQL и отличия модели SQL Server.
prerequisites: [sql-types-null]
seoTitle: Индексы SQL — clustered, B-tree, PostgreSQL собеседование
seoDescription: Основы индексов для собеседования: назначение, clustered/nonclustered, типы. PostgreSQL vs SQL Server, оригинальный разбор.
seoKeywords: [SQL, индекс, B-tree, clustered, nonclustered, PostgreSQL, SQL Server, собеседование]
canonicalUrl: https://9to18.ru/game/learn/sql-indexes-basics
---

## Введение

Индекс ускоряет поиск ценой дополнительных структур на запись и места на диске. На junior-собесе ждут определение, разницу clustered/nonclustered и перечень типов. Важно не переносить термины SQL Server на PostgreSQL один в один — модели хранения отличаются.

## Раздел: Что такое индекс

**Индекс** — вспомогательная структура (чаще всего сбалансированное дерево), которая хранит упорядоченные ключи и указатели на строки таблицы (или включает нужные поля целиком).

Зачем:
- быстро находить строки по равенству и диапазону (`WHERE id =`, `WHERE created_at BETWEEN`);
- поддерживать уникальность (`UNIQUE INDEX` / ограничения PK/UK);
- иногда отдавать результат без обращения к heap (covering / index-only scan в PG при видимости по visibility map).

Цена:
- замедление `INSERT`/`UPDATE`/`DELETE` — нужно обновлять индекс;
- место на диске;
- риск «лишних» индексов, которые не используются планировщиком.

```sql
CREATE INDEX idx_orders_user_id ON orders (user_id);
CREATE UNIQUE INDEX idx_users_email ON users (email);
-- частичный индекс (PostgreSQL)
CREATE INDEX idx_orders_open ON orders (created_at) WHERE status = 'new';
```

Планировщик решает, читать индекс или seq scan: при малой таблице полный скан часто дешевле.

## Раздел: Clustered и nonclustered

Термины классически из **SQL Server / ряд учебных курсов**:

**Clustered index** задаёт физический порядок строк в структуре таблицы: данные «лежат в индексе». На таблицу обычно один clustered (часто на PK). Поиск по ключу кластера быстро находит страницу данных.

**Nonclustered index** — отдельная структура: ключ индекса + указатель на строку (RID или ключ кластера). Таких индексов много. Чтобы получить остальные столбцы, движок делает lookup в основную структуру.

**Как это выглядит в PostgreSQL:**
- таблицы по умолчанию — **heap** (неупорядоченное хранилище строк);
- вторичные индексы (по умолчанию **B-tree**) хранят ключ + `tid` (указатель на версию строки в heap);
- отдельного «clustered index» как обязательной организации таблицы, как в SQL Server, **нет**;
- команда `CLUSTER` один раз переписывает heap в порядке индекса, но порядок **не поддерживается** автоматически при дальнейших записях;
- `INDEX … INCLUDE` и index-only scan частично закрывают сценарии covering.

На собесе хороший ответ: «В SQL Server кластерный индекс часто определяет физический layout; в PostgreSQL индекс — отдельная структура над heap, а CLUSTER — разовое упорядочивание».

## Раздел: Типы индексов

Обзор с привязкой к PostgreSQL:

| Тип | Когда полезен |
|-----|----------------|
| **B-tree** | Равенство и диапазоны, сортировка, PK/UK — основной тип по умолчанию |
| **Hash** | В PG ограниченные сценарии равенства; реже нужен вручную |
| **GiST / SP-GiST** | Геометрия, диапазоны, полнотекстные/нестандартные ключи |
| **GIN** | Массивы, jsonb, полнотекст — много значений на строку |
| **BRIN** | Очень большие таблицы с физически коррелированными значениями (время) |

В **SQL Server** в разговоре про типы часто звучат clustered/nonclustered, unique/nonunique, filtered, columnstore — другая таксономия поверх storage engine.

Практические правила junior-уровня:
1. индекс под реальные `WHERE`/`JOIN`/`ORDER BY`, не «на все столбцы»;
2. селективность важна: индекс по `boolean is_active` часто бесполезен без условия/частичности;
3. составной индекс: порядок столбцов = порядок отбора (`(user_id, created_at)` ≠ `(created_at, user_id)` для разных запросов);
4. смотреть план (`EXPLAIN` / `EXPLAIN ANALYZE`) — тема следующих выпусков серии.

## Лаба

**Цель.** Создать индекс под JOIN/фильтр и сравнить план до/после на учебной таблице.

**Шаги.**
1. Создайте `sql06_events(id bigserial, user_id bigint, created_at timestamptz, payload text)` и вставьте заметный объём (тысячи строк скриптом).
2. Выполните `EXPLAIN ANALYZE SELECT * FROM sql06_events WHERE user_id = 42;` без индекса — зафиксируйте Seq Scan.
3. Создайте `CREATE INDEX ON sql06_events (user_id);` и повторите план — ожидайте Index Scan / Bitmap Index Scan.
4. Добавьте составной `(user_id, created_at)` и запрос с диапазоном дат для одного user_id.
5. Кратко запишите 3 пункта: выгода, цена на INSERT, отличие PG heap от clustered в SQL Server.

**В группу:** один предлагает «давайте clustered index на email как в SQL Server» — второй объясняет, как сказать это корректно для PostgreSQL.

**Готово, если…**
- [ ] Определяете индекс и его trade-off за 30 секунд
- [ ] Не путаете clustered SQL Server с индексами PostgreSQL
- [ ] Называете B-tree как основной тип и по одному примеру GiST/GIN

## Схема: Поиск через индекс

```mermaid
flowchart LR
  Q["WHERE user_id = 42"] --> I[B-tree индекс]
  I --> T[tid / ключ строки]
  T --> H[Heap таблица PG]
  H --> R[Строки результата]
```

## Тест

### Зачем нужен индекс, если можно Seq Scan?

**Ответ:** на больших таблицах индекс сильно сокращает объём чтения для селективных условий; на маленьких Seq Scan может быть дешевле

**Пояснение:** решение принимает планировщик, исходя из статистики и стоимости.

### Есть ли в PostgreSQL clustered index как в SQL Server?

**Ответ:** нет прямой аналогии; по умолчанию heap + вторичные индексы, CLUSTER лишь разово упорядочивает

**Пояснение:** путать термины диалектов — частая ошибка на собесе.

### Какой тип индекса в PostgreSQL основной для WHERE id = и диапазонов?

**Ответ:** B-tree

**Пояснение:** именно B-tree создаётся по умолчанию для обычных скалярных ключей.

## Шпаргалка

<h3>Суть</h3>
<ul>
<li>Индекс ускоряет чтение, замедляет запись, занимает место</li>
<li>PG: heap + B-tree (и другие access methods)</li>
<li>SQL Server: clustered часто = организация данных таблицы</li>
</ul>
<h3>Команды PG</h3>
<pre><code>CREATE INDEX idx_name ON table (col);
CREATE INDEX ON table (a, b);
CREATE INDEX ON table (created_at) WHERE status = 'new';
EXPLAIN ANALYZE SELECT ...;
</code></pre>
<h3>Типы PG</h3>
<ul>
<li>B-tree · Hash · GiST · SP-GiST · GIN · BRIN</li>
</ul>

## Anki

### Front: Что такое индекс в СУБД?

Back: Вспомогательная структура для ускорения поиска по ключу ценой накладных расходов на изменение данных

### Front: Clustered vs nonclustered в классическом смысле?

Back: Clustered определяет порядок/организацию данных таблицы (обычно один); nonclustered — отдельная структура с указателями на строки

### Front: Чем PostgreSQL отличается в теме «кластерный индекс»?

Back: Таблица — heap; индексы вторичные; CLUSTER не поддерживает порядок автоматически как clustered index в SQL Server

## Итоги

- Индекс — инструмент под конкретные запросы, не серебряная пуля
- B-tree закрывает большинство junior-сценариев в PostgreSQL
- Clustered/nonclustered рассказывайте с пометкой диалекта — иначе ответ засчитывают как путаницу

## Ссылки

- [OTUS / Хабр — топ вопросов по SQL, часть I](https://habr.com/ru/companies/otus/articles/461067/)
- [PostgreSQL: Indexes](https://www.postgresql.org/docs/current/indexes.html)
- Learn | /game/learn
- Далее: [Нормализация и денормализация](/game/learn/sql-normalization)
