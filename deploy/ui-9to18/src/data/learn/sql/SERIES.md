# Серия SQL Learn: Junior → Senior

Карта **16 выпусков** по SQL для собеседования. Файлы: `sql-*.md` по slug.

Источник тем (Часть I, Q1–30): [OTUS / Хабр — топ-65 SQL, часть I](https://habr.com/ru/companies/otus/articles/461067/). Ответы в статьях — **оригинальные** (с учётом PostgreSQL 16 и оговорок по диалектам); не копипаст перевода OTUS. Часть II исходной серии на Хабре не найдена — SQL13–14 дополняют типовыми middle/senior темами (CTE, window, EXPLAIN).

## Конвенции

| Поле | Значение |
|------|----------|
| `episode` | `SQL01` … `SQL16` |
| `order` | `601` … `616` |
| `profiles` | `[developer, analyst, tester]` |
| `rubric` | в основном `data` |
| `onKnowledgeMap` | `true` (+ тег `собеседование`) |
| Seed | `import_sql_learn_series.py` → `learn_seed.json` → `episodes.ts` |

Нумерация вопросов: **Q1**…**Q30** = номера из Части I.

---

## Junior · SQL01–SQL06 · order 601–606

| Ep | slug | Тема | Вопросы |
|----|------|------|---------|
| SQL01 | `sql-ddl-dml-dcl` | Подмножества SQL, СУБД, SQL vs MySQL | Q2, Q3, Q9 |
| SQL02 | `sql-tables-keys-constraints` | Таблица/поле, PK/UK/FK, constraints, целостность | Q4, Q7, Q8, Q10–Q12 |
| SQL03 | `sql-delete-truncate-drop` | DELETE vs TRUNCATE vs DROP | Q1, Q21 |
| SQL04 | `sql-joins` | JOIN типы, CROSS vs NATURAL | Q5, Q15, Q27 |
| SQL05 | `sql-types-null` | CHAR vs VARCHAR, NULL | Q6, Q26 |
| SQL06 | `sql-indexes-basics` | Индексы clustered/nonclustered/unique | Q13, Q18, Q19 |

## Middle · SQL07–SQL12 · order 607–612

| Ep | slug | Тема | Вопросы |
|----|------|------|---------|
| SQL07 | `sql-normalization` | Нормализация 1–3НФ, сущности, денормализация | Q16, Q17, Q20, Q22 |
| SQL08 | `sql-acid-transactions` | ACID и транзакции | Q23 |
| SQL09 | `sql-triggers-operators` | Триггеры, операторы SQL | Q24, Q25 |
| SQL10 | `sql-subqueries` | Подзапросы correlated/noncorrelated | Q28, Q29 |
| SQL11 | `sql-agg-dates-count` | COUNT, текущая дата, агрегаты | Q14, Q30 |
| SQL12 | `sql-practice-lab` | Сводная лаба по Q1–30 | практика |

## Senior · SQL13–SQL16 · order 613–616

| Ep | slug | Тема | Вопросы |
|----|------|------|---------|
| SQL13 | `sql-cte-window` | CTE и оконные функции | дополнение сверх Q1–30 |
| SQL14 | `sql-performance-explain` | Планы, индексы на практике | дополнение |
| SQL15 | `sql-interview-drill` | Drill «что ответить» по Q1–30 | кросс |
| SQL16 | `sql-capstone-checklist` | Чеклист + индекс Q→slug | обзор |

## Обслуживание

```bash
python core/scripts/import_sql_learn_series.py
python core/scripts/generate_learn_episodes_ts.py
```
