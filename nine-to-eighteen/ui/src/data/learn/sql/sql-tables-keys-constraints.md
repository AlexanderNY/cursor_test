---
slug: sql-tables-keys-constraints
title: Таблицы, ключи и ограничения целостности
shortTitle: Ключи и constraints
episode: SQL02
rubric: data
order: 602
publishedAt: 2027-04-03T10:00:00+03:00
profiles: [developer, analyst, tester]
level: junior
tags: [sql, primary-key, foreign-key, constraints, целостность, собеседование]
onKnowledgeMap: true
durationMin: 30
excerpt: Таблица и поле, PRIMARY KEY, UNIQUE, FOREIGN KEY, CHECK/NOT NULL и виды целостности данных в реляционной модели.
prerequisites: [sql-ddl-dml-dcl]
seoTitle: PK UK FK и constraints SQL — junior собеседование
seoDescription: Что такое таблица и поле, первичный и уникальный ключ, внешний ключ, ограничения и целостность данных. Примеры PostgreSQL.
seoKeywords: [SQL, PRIMARY KEY, FOREIGN KEY, UNIQUE, constraints, целостность, PostgreSQL, собеседование]
canonicalUrl: https://9to18.ru/game/learn/sql-tables-keys-constraints
---

## Введение

После семейств команд переходим к каркасу реляционной модели: таблица и поле, ключи и ограничения. На собесе часто сыплют подряд: что такое PK, чем UNIQUE отличается от PK, зачем FK и что такое целостность. Ответы ниже — с примерами под PostgreSQL.

## Раздел: Таблица, поле и ключи

**Таблица** — именованная структура из строк (кортежей) и столбцов (атрибутов). На уровне хранения в PostgreSQL таблица обычно лежит в heap; строки адресуются через `ctid`, но в прикладном SQL вы работаете с логическими ключами.

**Поле (столбец)** — именованный атрибут с типом (`integer`, `text`, `timestamptz`, …), допустимостью NULL и ограничениями.

**PRIMARY KEY (PK)** — ограничение, которое:
1. однозначно идентифицирует строку;
2. запрещает NULL во всех столбцах ключа;
3. подразумевает уникальный индекс (в PostgreSQL создаётся автоматически).

На таблицу — один PRIMARY KEY (может быть составным):

```sql
CREATE TABLE orders (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id    bigint NOT NULL,
  status     text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- составной PK
CREATE TABLE order_items (
  order_id bigint NOT NULL,
  line_no  int NOT NULL,
  product_id bigint NOT NULL,
  qty      int NOT NULL CHECK (qty > 0),
  PRIMARY KEY (order_id, line_no)
);
```

**UNIQUE KEY / UNIQUE** — уникальность значений (или набора столбцов), но в отличие от PK:
- на таблицу может быть несколько UNIQUE;
- в PostgreSQL в UNIQUE-столбце допускается несколько NULL (NULL не считается равным NULL при проверке уникальности) — это частый подвох на собесе;
- UNIQUE не объявляет «главный» идентификатор строки для FK по умолчанию, хотя на UNIQUE можно ссылаться из FK.

Практически: PK — «кто я»; UNIQUE — «это значение/комбинация не должна повторяться» (email, внешний код заказа).

## Раздел: Ограничения и внешние ключи

**Constraints** — правила, которые СУБД проверяет при записи. Основные виды:

| Ограничение | Смысл |
|-------------|--------|
| `NOT NULL` | значение обязательно |
| `UNIQUE` | уникальность |
| `PRIMARY KEY` | уникальность + NOT NULL + идентификатор |
| `FOREIGN KEY` | ссылка на существующую строку (или NULL, если допускается) |
| `CHECK` | произвольный предикат по строке |
| `EXCLUDE` (PG) | запрет пересечений (диапазоны, геометрия) |

**FOREIGN KEY (FK)** связывает дочернюю таблицу с родительской:

```sql
CREATE TABLE users (
  id    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email text NOT NULL UNIQUE
);

CREATE TABLE orders (
  id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id bigint NOT NULL REFERENCES users (id) ON DELETE RESTRICT,
  status  text NOT NULL CHECK (status IN ('new', 'paid', 'canceled'))
);
```

Поведение при удалении/обновлении родителя задаётся действиями: `RESTRICT` / `NO ACTION`, `CASCADE`, `SET NULL`, `SET DEFAULT`. На собесе полезно привести пример: удаление пользователя с заказами — либо запрет, либо каскад (осознанно).

## Раздел: Целостность данных

**Целостность** — данные соответствуют правилам предметной области и модели.

Классы, которые обычно ждут в ответе:
1. **Доменная** — значения в допустимом домене типа и CHECK (`qty > 0`, статус из списка).
2. **Сущностная** — каждая сущность идентифицируема (PK), нет «безымянных» дубликатов строк с точки зрения ключа.
3. **Ссылочная** — FK не указывает на несуществующего родителя; нет «осиротевших» ссылок после некорректного удаления.
4. **Пользовательская / бизнес** — правила, которые не всегда укладываются в один CHECK (уникальность активного тарифа на пользователя, непересечение интервалов) — триггеры, EXCLUDE, приложение + транзакции.

Целостность обеспечивается ограничениями схемы + транзакциями + (иногда) приложением. Хороший ответ: «сначала декларативные constraints, императив — только если декларативно нельзя».

## Лаба

**Цель.** Спроектировать мини-схему users → orders → order_items с PK/UK/FK/CHECK и поймать нарушения целостности.

**Шаги.**
1. Создайте `users(id PK, email UNIQUE NOT NULL)`, `orders(id PK, user_id FK, status CHECK)`, `order_items(order_id, line_no, qty CHECK, PK составной)`.
2. Вставьте пользователя и заказ; попробуйте вставить заказ с несуществующим `user_id` — зафиксируйте текст ошибки FK.
3. Попробуйте два пользователя с одним email — ошибка UNIQUE.
4. Попробуйте `qty = 0` — ошибка CHECK.
5. Сформулируйте вслух: чем UNIQUE(email) отличается от PRIMARY KEY(id).

**В группу:** партнёр предлагает действие `ON DELETE CASCADE` vs `RESTRICT` для users→orders — обсудите риск для продакшена.

**Готово, если…**
- [ ] Объясняете таблицу/поле без круговых определений
- [ ] Отличаете PK от UNIQUE, в том числе поведение NULL в PostgreSQL
- [ ] Называете 3+ вида constraints и 3 вида целостности

## Схема: Связи users–orders–items

```mermaid
erDiagram
  USERS ||--o{ ORDERS : places
  ORDERS ||--|{ ORDER_ITEMS : contains
  USERS {
    bigint id PK
    text email UK
  }
  ORDERS {
    bigint id PK
    bigint user_id FK
    text status
  }
  ORDER_ITEMS {
    bigint order_id PK_FK
    int line_no PK
    int qty
  }
```

## Тест

### Чем PRIMARY KEY отличается от UNIQUE?

**Ответ:** PK один на таблицу, запрещает NULL и задаёт идентификатор строки; UNIQUE может быть несколько и в PostgreSQL допускает несколько NULL

**Пояснение:** оба дают уникальность, но роль и правила NULL/количества ограничений разные.

### Что проверяет FOREIGN KEY?

**Ответ:** ссылочную целостность — значение ссылки существует в родительской таблице (или NULL, если разрешён)

**Пояснение:** FK не заменяет бизнес-проверки, но защищает от «битых» связей.

### Что такое доменная целостность?

**Ответ:** значения соответствуют типу и ограничениям домена (NOT NULL, CHECK, допустимый диапазон)

**Пояснение:** отдельно от ссылочной (FK) и сущностной (PK) целостности.

## Шпаргалка

<h3>Ключи</h3>
<ul>
<li><b>PK</b> — идентификатор, UNIQUE + NOT NULL, один на таблицу</li>
<li><b>UNIQUE</b> — уникальность кандидата; NULL-семантика зависит от СУБД</li>
<li><b>FK</b> — ссылка на PK/UNIQUE родителя + действие ON DELETE/UPDATE</li>
</ul>
<h3>Constraints</h3>
<ul>
<li>NOT NULL, CHECK, UNIQUE, PK, FK</li>
<li>Сначала декларативно, потом триггеры/приложение</li>
</ul>
<h3>Целостность</h3>
<ul>
<li>Доменная · сущностная · ссылочная · бизнес-правила</li>
</ul>

## Anki

### Front: Можно ли иметь несколько PRIMARY KEY на одной таблице?

Back: Нет, PRIMARY KEY один (столбец или набор столбцов). Несколько UNIQUE — можно.

### Front: Можно ли в PostgreSQL вставить две строки с NULL в UNIQUE-столбец?

Back: Да, обычно можно: NULL при сравнении уникальности не считается равным другому NULL.

### Front: Что обеспечивает ссылочную целостность?

Back: FOREIGN KEY и политика ON DELETE/UPDATE относительно родительской строки

## Итоги

- Таблица + типизированные поля — базовая единица реляционной модели
- PK/UK/FK и CHECK — главный способ защитить данные без кода приложения
- Целостность — не одно слово, а набор уровней; умейте привести пример на каждый

## Ссылки

- [OTUS / Хабр — топ вопросов по SQL, часть I](https://habr.com/ru/companies/otus/articles/461067/)
- [PostgreSQL: Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- Learn | /game/learn
- Далее: [DELETE, TRUNCATE и DROP](/game/learn/sql-delete-truncate-drop)
