# Серия Redis Learn: Junior → Senior

Карта **8 выпусков** по Redis для собеседования. Файлы: `rd-*.md` по slug.

## Конвенции

| Поле | Значение |
|------|----------|
| `episode` | `RD01` … `RD08` |
| `order` | `701` … `708` |
| `profiles` | `[developer, analyst]` |
| `rubric` | `data` |
| `onKnowledgeMap` | `true` (+ тег `собеседование`) |
| Seed | `import_redis_learn_series.py` → `learn_seed.json` → `episodes.ts` |

## Junior · RD01–RD03 · order 701–703

| Ep | slug | Тема |
|----|------|------|
| RD01 | `rd-kv-model` | KV-модель, не source of truth |
| RD02 | `rd-data-types` | string, hash, list, set, zset |
| RD03 | `rd-ttl-persistence` | TTL, RDB vs AOF |

## Middle · RD04–RD06 · order 704–706

| Ep | slug | Тема |
|----|------|------|
| RD04 | `rd-cache-aside` | cache-aside и инвалидация |
| RD05 | `rd-stampede-locks` | dogpile / singleflight |
| RD06 | `rd-pubsub-vs-queue` | pub/sub vs брокер |

## Senior · RD07–RD08 · order 707–708

| Ep | slug | Тема |
|----|------|------|
| RD07 | `rd-eviction-cluster` | eviction, sentinel/cluster |
| RD08 | `rd-capstone` | drill vs PostgreSQL, чеклист |

## Обслуживание

```bash
python core/scripts/import_redis_learn_series.py
python core/scripts/generate_learn_episodes_ts.py
```
