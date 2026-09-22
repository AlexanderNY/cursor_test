# Серия QA Learn: Junior → Senior

Карта **24 выпуска** для трека тестировщика. Полные тексты: `qa-*.md` по slug (например `qa-intro-testing.md`).

Источник тем: [QA-interview-250](https://github.com/Konstantine23/QA-interview-250). В статьях — **оригинальные** ответы по вопросам (не копипаст). Нумерация: **J**unior, **M**iddle, **S**enior.

AQA-лабы и сниппеты — **Python** (pytest, requests/httpx, Selenium/Playwright Python). Java/TestNG — кратко, если вопрос явно про Java.

## Конвенции

| Поле | Значение |
|------|----------|
| `episode` | `QA01` … `QA24` |
| `order` | `401` … `424` |
| `profiles` | `[tester]` |
| `onKnowledgeMap` | `true` (+ тег `собеседование`) |
| Seed | `import_qa_learn_series.py` → `learn_seed.json` → `episodes.ts` |

---

## Junior · QA01–QA08 · order 401–408

| Ep | slug | Тема | Вопросы |
|----|------|------|---------|
| QA01 | `qa-intro-testing` | Тестирование, STLC, Entry/Exit | J1–3, J25, J30 |
| QA02 | `qa-types-levels` | Типы и уровни, smoke/sanity, boxes | J4–5, J9–10, J12–13, J15–17, J19–23, J100 |
| QA03 | `qa-test-design` | Эквивалентность, границы, pesticide | J6–8, J24, J123, J137–140 |
| QA04 | `qa-bugs-reports` | Bug report, severity/priority | J26–29, J131–133 |
| QA05 | `qa-docs-plan-cases` | План, кейсы, RTM, чеклисты | J18, J31–35, J119, J121 |
| QA06 | `qa-web-http-api-basics` | HTTP, REST, cookies, DevTools | J76–103 |
| QA07 | `qa-sql-db-basics` | БД и SQL-лабы | J87, J134–136 |
| QA08 | `qa-junior-practice-lab` | Сводная практика junior | J119–130, J132, J135 |

## AQA bridge · QA09–QA12 · order 409–412

| Ep | slug | Тема | Вопросы |
|----|------|------|---------|
| QA09 | `qa-aqa-principles` | OOP/SOLID/PO; Java-блок кратко | J36–45 |
| QA10 | `qa-selenium-webdriver` | Selenium на Python | J46–62; M35–38, M41–42 |
| QA11 | `qa-pytest-ci-git` | pytest, Git, CI, отчёты | J63–75; M16 |
| QA12 | `qa-mobile-basics` | Mobile + Appium-концепт | J109–118; M72–84 обзор |

## Middle · QA13–QA18 · order 413–418

| Ep | slug | Тема | Вопросы |
|----|------|------|---------|
| QA13 | `qa-middle-process` | Процесс, coverage, leakage | M1, M4, M14, M17–22 |
| QA14 | `qa-test-design-advanced` | Decision table, pairwise, RBT | M3, M11, M23–25, M93, M101 |
| QA15 | `qa-api-contract-perf` | API, contract, perf tools | M10, M26–29, M96–97; S9, S29 |
| QA16 | `qa-agile-scrum-kanban` | Scrum/Kanban, DoD | M30–33; S3–4 |
| QA17 | `qa-infra-linux-containers` | VM, Docker, SSH, shell | M43–52 |
| QA18 | `qa-middle-web-mobile-sql` | Auth, OWASP intro, SQL mid, mobile | M53–71, M72–84 |

## Senior · QA19–QA24 · order 419–424

| Ep | slug | Тема | Вопросы |
|----|------|------|---------|
| QA19 | `qa-strategy-metrics` | Стратегия, метрики, estimate | S1–2, S5–13, S15–18 |
| QA20 | `qa-shift-left-automation-roi` | Shift-left, ROI, BDD, CI/CD | S19–25, S27; M34 |
| QA21 | `qa-security-perf-senior` | OWASP, sockets, stress | S26, S28–29 |
| QA22 | `qa-leadership-conflicts` | Конфликты, дедлайны, RCA | M85–87; S6, S8, S31–33 |
| QA23 | `qa-senior-practice-drill` | Drill senior-практики | S30, S34–38; M88–103 |
| QA24 | `qa-capstone-checklist` | Чеклист + appendix | обзор |

## Appendix вне цепочки

J104–108 (NIC/RTP/SIP), M40 (Electron), M69 (SQL Server replication) — footnote в QA24.

## Обслуживание

```bash
python core/scripts/import_qa_learn_series.py
python core/scripts/generate_learn_episodes_ts.py
# опционально: reset Learn seed в админке или перезапуск core после обновления learn_seed.json
```
