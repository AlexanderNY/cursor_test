# Серия System Analyst Learn: Junior → Senior

Карта **24 выпуска** для трека системного аналитика. Полные тексты: `sa-*.md` по slug (например `sa-requirements-basics.md`).

Источник тем: [Топ-150 вопросов СА на Хабре](https://habr.com/ru/articles/963708/). В статьях — **оригинальные** ответы (в источнике ответов нет). Нумерация: **T1**…**T7** (тема.вопрос).

## Конвенции

| Поле | Значение |
|------|----------|
| `episode` | `SA01` … `SA24` |
| `order` | `501` … `524` |
| `profiles` | `[analyst]` |
| `onKnowledgeMap` | `true` (+ тег `собеседование`) |
| Seed | `import_sa_learn_series.py` → `learn_seed.json` → `episodes.ts` |

---

## Junior · SA01–SA08 · order 501–508

| Ep | slug | Тема | Вопросы |
|----|------|------|---------|
| SA01 | `sa-requirements-basics` | Сбор требований, FR/NFR | T1.1–1.6 |
| SA02 | `sa-user-stories-use-cases` | User story, USM, Use case | T1.7–1.12 |
| SA03 | `sa-gost-srs-artifacts` | ГОСТ, SRS, постановка | T1.13–1.22 |
| SA04 | `sa-notations-bpmn-uml` | BPMN, UML | T2.1–2.8 |
| SA05 | `sa-db-basics` | БД, нормализация, связи | T3.1.1–3.1.12 |
| SA06 | `sa-sql-basics` | SQL, JOIN, HAVING | T3.2.1–3.2.7 |
| SA07 | `sa-rest-basics` | REST API основы | T4.2.1–4.2.14 |
| SA08 | `sa-methods-scrum-kanban` | Методологии, DoR/DoD | T6.1.1–6.1.14 |

## Middle · SA09–SA16 · order 509–516

| Ep | slug | Тема | Вопросы |
|----|------|------|---------|
| SA09 | `sa-db-advanced` | ACID, индексы, шард/реплика | T3.1.13–3.1.24 |
| SA10 | `sa-sync-async-queues` | Sync/async, Kafka/Rabbit | T4.1; T4.4.1–4.4.5 |
| SA11 | `sa-rest-advanced` | Идемпотентность, версии, JSON Schema | T4.2.5–6, T4.2.15–20 |
| SA12 | `sa-soap-xml` | SOAP, XML, WSDL | T4.3 |
| SA13 | `sa-esb-integrations` | ESB, GraphQL, gRPC, webhook | T4.4.6–9; T4.5 |
| SA14 | `sa-architecture-styles` | SOA, микросервисы, монолит | T5.1–5.6 |
| SA15 | `sa-orchestration-cap-gateway` | Оркестрация, CAP, Gateway | T5.7–5.15 |
| SA16 | `sa-http-security-basics` | HTTP/S, auth, шифрование | T7.1–7.5 |

## Senior · SA17–SA24 · order 517–524

| Ep | slug | Тема | Вопросы |
|----|------|------|---------|
| SA17 | `sa-requirements-senior-craft` | Постановка senior, QA | углубление T1 |
| SA18 | `sa-modeling-workshop` | BPMN+Sequence+ER лаба | T2+T3 практика |
| SA19 | `sa-integration-design` | Выбор интеграции | синтез T4 |
| SA20 | `sa-architecture-decisions` | ADR монолит/микро | синтез T5 |
| SA21 | `sa-estimation-delivery` | Оценка и поставка | T6.1 углубление |
| SA22 | `sa-profession-levels` | Junior vs Senior СА | T6.2 |
| SA23 | `sa-interview-drill` | Drill по 7 темам | кросс T1–T7 |
| SA24 | `sa-capstone-checklist` | Чеклист + индекс | обзор |

## Обслуживание

```bash
python core/scripts/import_sa_learn_series.py
python core/scripts/generate_learn_episodes_ts.py
```
