#!/usr/bin/env python3
"""Generate Redis / Java / Product / JS Learn series markdown into deploy + nine-to-eighteen."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "ui-9to18" / "src" / "data" / "learn"
NINE = ROOT / "nine-to-eighteen" / "ui" / "src" / "data" / "learn"


def article(
    *,
    slug: str,
    title: str,
    short: str,
    episode: str,
    rubric: str,
    order: int,
    published: str,
    profiles: list[str],
    level: str,
    tags: list[str],
    duration: int,
    excerpt: str,
    prerequisites: list[str],
    seo_title: str,
    seo_desc: str,
    seo_kw: list[str],
    intro: str,
    sections: list[tuple[str, str]],
    lab_goal: str,
    lab_steps: list[str],
    lab_group: str,
    lab_done: list[str],
    diagram_title: str,
    diagram: str,
    quiz: list[tuple[str, str, str]],
    cheat_html: str,
    anki: list[tuple[str, str]],
    summary: list[str],
    links: list[tuple[str, str]],
    next_link: tuple[str, str] | None = None,
) -> str:
    tags_yaml = "[" + ", ".join(tags) + "]"
    profiles_yaml = "[" + ", ".join(profiles) + "]"
    prereq_yaml = "[" + ", ".join(prerequisites) + "]" if prerequisites else "[]"
    kw_yaml = "[" + ", ".join(seo_kw) + "]"
    lines = [
        "---",
        f"slug: {slug}",
        f"title: {title}",
        f"shortTitle: {short}",
        f"episode: {episode}",
        f"rubric: {rubric}",
        f"order: {order}",
        f"publishedAt: {published}",
        f"profiles: {profiles_yaml}",
        f"level: {level}",
        f"tags: {tags_yaml}",
        "onKnowledgeMap: true",
        f"durationMin: {duration}",
        f"excerpt: {excerpt}",
        f"prerequisites: {prereq_yaml}",
        f"seoTitle: {seo_title}",
        f"seoDescription: {seo_desc}",
        f"seoKeywords: {kw_yaml}",
        f"canonicalUrl: https://9to18.ru/game/learn/{slug}",
        "---",
        "",
        "## Введение",
        "",
        intro,
        "",
    ]
    for heading, body in sections:
        lines.extend([f"## Раздел: {heading}", "", body, ""])
    lines.extend(
        [
            "## Лаба",
            "",
            f"**Цель.** {lab_goal}",
            "",
            "**Шаги.**",
        ]
    )
    for i, step in enumerate(lab_steps, 1):
        lines.append(f"{i}. {step}")
    lines.extend(
        [
            "",
            f"**В группу:** {lab_group}",
            "",
            "**Готово, если…**",
        ]
    )
    for item in lab_done:
        lines.append(f"- [ ] {item}")
    lines.extend(
        [
            "",
            f"## Схема: {diagram_title}",
            "",
            "```mermaid",
            diagram.strip(),
            "```",
            "",
            "## Тест",
            "",
        ]
    )
    for q, a, explain in quiz:
        lines.extend(
            [
                f"### {q}",
                "",
                f"**Ответ:** {a}",
                "",
                f"**Пояснение:** {explain}",
                "",
            ]
        )
    lines.extend(["## Шпаргалка", "", cheat_html.strip(), "", "## Anki", ""])
    for front, back in anki:
        lines.extend([f"### Front: {front}", "", f"Back: {back}", ""])
    lines.extend(["## Итоги", ""])
    for s in summary:
        lines.append(f"- {s}")
    lines.extend(["", "## Ссылки", ""])
    for label, href in links:
        if href.startswith("http"):
            lines.append(f"- [{label}]({href})")
        else:
            lines.append(f"- Learn | [{label}]({href})")
    if next_link:
        lines.append(f"- Далее: [{next_link[0]}]({next_link[1]})")
    lines.append("")
    return "\n".join(lines)


def write_series(subdir: str, files: dict[str, str], series_md: str, readme: str) -> None:
    for base in (DEPLOY, NINE):
        target = base / subdir
        target.mkdir(parents=True, exist_ok=True)
        (target / "SERIES.md").write_text(series_md, encoding="utf-8")
        (target / "README.md").write_text(readme, encoding="utf-8")
        for name, content in files.items():
            (target / name).write_text(content, encoding="utf-8")
        print(f"wrote {len(files)} articles + SERIES to {target}")


# ── Redis ────────────────────────────────────────────────────────────────────

RD_SERIES = """# Серия Redis Learn: Junior → Senior

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
"""

RD_README = """# Redis Learn series

Оглавление: [`SERIES.md`](SERIES.md). Шаблон: [`../article-template.md`](../article-template.md).

```bash
python core/scripts/import_redis_learn_series.py
```
"""


def build_redis() -> dict[str, str]:
    articles: dict[str, str] = {}
    articles["rd01-kv-model.md"] = article(
        slug="rd-kv-model",
        title="Redis на собесе — модель ключ–значение",
        short="KV модель",
        episode="RD01",
        rubric="data",
        order=701,
        published="2027-05-01T10:00:00+03:00",
        profiles=["developer", "analyst"],
        level="junior",
        tags=["redis", "kv", "cache", "собеседование"],
        duration=25,
        excerpt="Что такое Redis, чем KV отличается от таблицы и почему Redis не source of truth.",
        prerequisites=[],
        seo_title="Redis KV модель — junior собеседование",
        seo_desc="Redis как in-memory key-value: когда уместен, чем не заменяет PostgreSQL.",
        seo_kw=["redis", "key-value", "кэш", "собеседование"],
        intro=(
            "Redis часто звучит на собесе как «кэш» — и этого мало. Junior должен объяснить модель "
            "ключ–значение, отличие от реляционной таблицы и риск хранить единственную правду в памяти."
        ),
        sections=[
            (
                "Что такое Redis",
                "Redis — in-memory хранилище структур данных с сетевым протоколом. Типичные роли: "
                "кэш ответов API, сессии, rate limit, лёгкие счётчики и pub/sub-сигналы.\n\n"
                "Сильные стороны: низкая задержка чтения/записи, богатые типы (не только string), TTL. "
                "Слабые: данные живут в RAM (если нет persistence / реплики), операционная цена памяти, "
                "сложность инвалидации кэша.",
            ),
            (
                "KV vs таблица",
                "В PostgreSQL вы думаете строками, связями и JOIN. В Redis — **ключом** и значением "
                "(или структурой вокруг ключа). Нет нормализации «из коробки»: вы сами проектируете "
                "пространство имён (`user:42:profile`).\n\n"
                "См. также: [SQL DDL/DML и виды СУБД](/game/learn/sql-ddl-dml-dcl) — где Redis "
                "упомянут как key-value рядом с RDBMS.",
            ),
            (
                "Не source of truth",
                "Если Redis — единственное место заказа/баланса без записи в БД, рестарт или eviction "
                "могут стереть бизнес-факт. Правило собеса: **система записи** (часто PostgreSQL) + "
                "кэш/ускоритель (Redis). Persistence (RDB/AOF) снижает риск, но не делает Redis "
                "полноценной транзакционной СУБД для сложной аналитики.",
            ),
        ],
        lab_goal="Спроектировать ключи для кэша профиля пользователя без дублирования «правды» только в Redis.",
        lab_steps=[
            "Опишите сущность `User(id, email, name)` в PostgreSQL одной фразой.",
            "Придумайте ключ Redis для кэша профиля (например `user:{id}:profile`).",
            "Запишите сценарий miss: нет ключа → SELECT из БД → SET с TTL.",
            "Назовите 2 причины не хранить баланс счёта только в Redis.",
            "Сверьте ответ с формулировкой «кэш vs source of truth».",
        ],
        lab_group="партнёр предлагает хранить заказы только в Redis — вы аргументируете против.",
        lab_done=[
            "Отличаете KV от таблицы",
            "Называете 2 типичных сценария Redis",
            "Объясняете, почему Redis не единственная правда",
        ],
        diagram_title="Кэш поверх БД",
        diagram="""flowchart LR
  Client --> API
  API --> Redis[(Redis)]
  API --> PG[(PostgreSQL)]
  Redis -.->|miss| API""",
        quiz=[
            (
                "Чем Redis принципиально отличается от PostgreSQL?",
                "in-memory KV/структуры vs реляционные таблицы и SQL",
                "Разный класс задач: ускорение lookup vs схема, JOIN, ACID-отчёты.",
            ),
            (
                "Почему Redis обычно не source of truth?",
                "данные в памяти могут пропасть при рестарте/eviction без надёжной записи в БД",
                "Persistence помогает, но не заменяет модель бизнес-транзакций в СУБД.",
            ),
            (
                "Назовите два типичных сценария Redis",
                "кэш API и сессии (или rate limit / счётчики)",
                "Любые два из: cache, session, rate limit, pub/sub, leaderboard.",
            ),
        ],
        cheat_html="""<h3>Суть</h3>
<ul>
<li>Redis = in-memory структуры + сеть</li>
<li>Ключ → значение / структура</li>
<li>Кэш ускоряет, БД хранит правду</li>
</ul>
<h3>Антипаттерн</h3>
<pre><code>единственный source of truth в Redis без БД</code></pre>""",
        anki=[
            ("Что такое Redis одной фразой?", "In-memory хранилище структур данных с сетевым доступом"),
            ("Почему не класть единственную правду в Redis?", "Рестарт/eviction могут стереть данные; нет зрелой реляционной модели"),
            ("Типичный ключ кэша профиля?", "user:{id}:profile или hash запроса"),
        ],
        summary=[
            "KV ≠ таблица: проектируете ключи сами",
            "Redis ускоряет, PostgreSQL часто пишет правду",
            "На собесе отделяйте кэш от системы записи",
        ],
        links=[
            ("Redis docs — Data types", "https://redis.io/docs/data-types/"),
            ("SQL DDL / NoSQL обзор", "/game/learn/sql-ddl-dml-dcl"),
            ("Python БД и кеш", "/game/learn/py-db-cache-memcached"),
        ],
        next_link=("Типы данных Redis", "/game/learn/rd-data-types"),
    )
    articles["rd02-data-types.md"] = article(
        slug="rd-data-types",
        title="Типы данных Redis — string, hash, list, set, zset",
        short="Типы Redis",
        episode="RD02",
        rubric="data",
        order=702,
        published="2027-05-03T10:00:00+03:00",
        profiles=["developer", "analyst"],
        level="junior",
        tags=["redis", "data-types", "собеседование"],
        duration=30,
        excerpt="Какой тип Redis выбрать: string, hash, list, set, sorted set.",
        prerequisites=["rd-kv-model"],
        seo_title="Типы данных Redis — junior",
        seo_desc="string/hash/list/set/zset: когда какой тип на собеседовании.",
        seo_kw=["redis", "hash", "zset", "list", "собеседование"],
        intro="После модели KV спрашивают: «какие типы знаете?». Нужно не перечисление, а выбор типа под задачу.",
        sections=[
            (
                "string и hash",
                "**string** — байтовая строка: JSON-blob, счётчик (`INCR`), битовые флаги. Просто и универсально.\n\n"
                "**hash** — поле→значение внутри ключа: удобно для объекта профиля (`HSET user:1 name …`). "
                "Частичное обновление полей без перезаписи всего JSON.",
            ),
            (
                "list, set, zset",
                "**list** — упорядоченный список: очереди задач (с оговорками), ленты, recent items.\n\n"
                "**set** — уникальные элементы: теги, уникальные посетители (в пределах памяти).\n\n"
                "**zset (sorted set)** — элемент + score: рейтинги, time-ordered ленты, sliding window rate limit.",
            ),
            (
                "Выбор типа",
                "Правило: сначала сценарий доступа (целиком / по полю / топ-N / уникальность), потом тип. "
                "Не кладите огромный JSON в string, если часто меняете одно поле — берите hash.",
            ),
        ],
        lab_goal="Подобрать тип Redis под три сценария продукта.",
        lab_steps=[
            "Сессия пользователя (token → userId) — какой тип и ключ?",
            "Топ-10 игроков по очкам — какой тип?",
            "Список последних 20 действий — какой тип?",
            "Профиль с email/name — hash или string? Обоснуйте.",
            "Запишите одну ошибку выбора типа (например list для уникальных id).",
        ],
        lab_group="партнёр называет сценарий — вы называете тип за 15 секунд.",
        lab_done=["Называете 5 базовых типов", "Связываете zset с рейтингом", "Отличаете hash от string-JSON"],
        diagram_title="Типы и сценарии",
        diagram="""flowchart TB
  S[string] --> Cache[JSON blob / counter]
  H[hash] --> Profile[поля объекта]
  L[list] --> Feed[recent / queue-like]
  SET[set] --> Tags[уникальные]
  Z[zset] --> Rank[рейтинг / score]""",
        quiz=[
            ("Какой тип для рейтинга с очками?", "zset (sorted set)", "Score задаёт порядок; ZRANGE/ZREVRANGE отдают топ."),
            ("Чем hash удобнее string с JSON?", "частичное обновление полей", "HSET одного поля без сериализации всего объекта."),
            ("Для чего set?", "уникальные элементы без дублей", "Теги, множества id, пересечения/разности."),
        ],
        cheat_html="""<h3>Типы</h3>
<ul>
<li>string — blob / INCR</li>
<li>hash — поля объекта</li>
<li>list — порядок</li>
<li>set — уникальность</li>
<li>zset — score + порядок</li>
</ul>""",
        anki=[
            ("zset — зачем?", "элементы с score: рейтинги, окна по времени"),
            ("hash vs JSON string", "hash — точечные поля; string — целиком сериализованный объект"),
            ("list в Redis", "упорядоченная последовательность; LPUSH/RPOP и т.п."),
        ],
        summary=["Пять базовых типов закрывают большинство junior-вопросов", "Сначала сценарий, потом тип", "hash ≠ set"],
        links=[
            ("Redis data types", "https://redis.io/docs/data-types/"),
            ("KV модель", "/game/learn/rd-kv-model"),
        ],
        next_link=("TTL и persistence", "/game/learn/rd-ttl-persistence"),
    )
    articles["rd03-ttl-persistence.md"] = article(
        slug="rd-ttl-persistence",
        title="TTL и persistence Redis — EXPIRE, RDB, AOF",
        short="TTL persistence",
        episode="RD03",
        rubric="data",
        order=703,
        published="2027-05-05T10:00:00+03:00",
        profiles=["developer", "analyst"],
        level="junior",
        tags=["redis", "ttl", "rdb", "aof", "собеседование"],
        duration=28,
        excerpt="TTL ключей, зачем EXPIRE; RDB vs AOF и риск потери данных.",
        prerequisites=["rd-data-types"],
        seo_title="Redis TTL RDB AOF — junior",
        seo_desc="Срок жизни ключей и режимы persistence Redis для собеседования.",
        seo_kw=["redis", "TTL", "RDB", "AOF", "собеседование"],
        intro="TTL и persistence — частая пара вопросов: «протухнет ли ключ» и «что будет после рестарта».",
        sections=[
            (
                "TTL",
                "`EXPIRE` / `SETEX` / TTL в командах задают время жизни ключа. По истечении ключ удаляется "
                "(лениво/активно — детали реализации). Зачем: автоинвалидация кэша, сессии, лимиты.\n\n"
                "`TTL key` показывает оставшиеся секунды; `-1` — без TTL; `-2` — ключа нет.",
            ),
            (
                "RDB vs AOF",
                "**RDB** — снимки на диск по расписанию: компактно, но окно потери данных между снимками.\n\n"
                "**AOF** — журнал операций: можно настроить fsync; обычно лучше для меньшей потери, ценой объёма/IO.\n\n"
                "На собесе: «persistence снижает риск, но не делает Redis заменой OLTP-СУБД».",
            ),
            (
                "Рестарт",
                "Без persistence данные в RAM после kill процесса пропадут. С репликацией и sentinel/cluster "
                "картина сложнее — это middle/senior (RD07). Junior должен честно сказать: уточню конфиг "
                "`save` / `appendonly` на стенде.",
            ),
        ],
        lab_goal="Смоделировать TTL и описать риск потери при RDB-only.",
        lab_steps=[
            "В redis-cli (или описать): SET session:1 alice EX 60.",
            "Проверьте TTL session:1.",
            "Объясните, что будет через 61 секунду.",
            "Сравните RDB и AOF в таблице «потеря / размер / IO».",
            "Напишите фразу для собеса про рестарт без AOF.",
        ],
        lab_group="партнёр выбирает RDB или AOF — вы называете главный компромисс.",
        lab_done=["Ставите TTL осознанно", "Отличаете RDB от AOF", "Связываете persistence с риском потери"],
        diagram_title="Жизнь ключа",
        diagram="""sequenceDiagram
  App->>Redis: SET key val EX 60
  Note over Redis: TTL тикает
  Redis-->>App: miss после истечения""",
        quiz=[
            ("Зачем TTL на кэше?", "автоматически протухать устаревшие данные", "Снижает риск вечного stale без ручной очистки."),
            ("Главный минус RDB?", "окно потери данных между снимками", "После краша теряются изменения после последнего dump."),
            ("AOF хранит что?", "журнал команд/операций", "Позволяет восстановить состояние ближе к моменту сбоя."),
        ],
        cheat_html="""<h3>TTL</h3>
<pre><code>SET k v EX 60
TTL k</code></pre>
<h3>Persistence</h3>
<ul>
<li>RDB — snapshot</li>
<li>AOF — journal</li>
</ul>""",
        anki=[
            ("TTL -1 значит?", "ключ есть, срока жизни нет"),
            ("RDB vs AOF", "снимок vs журнал операций"),
            ("Почему TTL на сессии?", "сессия сама истечёт без ручного DELETE"),
        ],
        summary=["TTL — базовая гигиена кэша", "RDB/AOF — компромисс потери vs IO", "Persistence ≠ замена БД"],
        links=[
            ("Redis persistence", "https://redis.io/docs/management/persistence/"),
            ("Типы данных", "/game/learn/rd-data-types"),
        ],
        next_link=("cache-aside", "/game/learn/rd-cache-aside"),
    )
    articles["rd04-cache-aside.md"] = article(
        slug="rd-cache-aside",
        title="Паттерн cache-aside в Redis",
        short="cache-aside",
        episode="RD04",
        rubric="data",
        order=704,
        published="2027-05-07T10:00:00+03:00",
        profiles=["developer", "analyst"],
        level="middle",
        tags=["redis", "cache-aside", "invalidation", "собеседование"],
        duration=30,
        excerpt="Чтение через кэш, miss → БД → запись; ключи и инвалидация.",
        prerequisites=["rd-ttl-persistence"],
        seo_title="Redis cache-aside — middle",
        seo_desc="Паттерн cache-aside: miss, hit, инвалидация ключей.",
        seo_kw=["redis", "cache-aside", "инвалидация", "собеседование"],
        intro="Middle ждут не «поставим Redis», а паттерн чтения/записи и историю про устаревший кэш.",
        sections=[
            (
                "cache-aside",
                "1) читаем ключ в Redis; 2) hit → отдать; 3) miss → читать БД; 4) записать в Redis с TTL; 5) отдать клиенту.\n\n"
                "Запись в БД: обновить БД, затем удалить/обновить ключ кэша (чтобы не отдать stale).",
            ),
            (
                "Ключ",
                "Ключ часто = сущность + id или hash параметров запроса. Стабильность ключа важнее «красоты». "
                "Версионирование ключа (`v2:`) помогает при смене формата значения.",
            ),
            (
                "Инвалидация",
                "Сложнее записи: кто и когда сбрасывает кэш? Варианты: TTL, явный DEL при UPDATE, "
                "событие из очереди. Антипаттерн — вечный ключ без политики обновления.\n\n"
                "См. также: [Python БД и Memcached](/game/learn/py-db-cache-memcached).",
            ),
        ],
        lab_goal="Описать cache-aside для GET /users/{id}.",
        lab_steps=[
            "Псевдокод hit/miss.",
            "Ключ `user:{id}`.",
            "Сценарий UPDATE name — что с ключом?",
            "Выберите TTL (и почему не «навсегда»).",
            "Назовите риск stale после записи.",
        ],
        lab_group="один пишет hit-path, второй — invalidation path.",
        lab_done=["Рисуете hit/miss", "Связываете UPDATE с DEL", "Не путаете write-through с cache-aside"],
        diagram_title="cache-aside",
        diagram="""sequenceDiagram
  C->>API: GET user
  API->>Redis: GET
  alt miss
    API->>PG: SELECT
    API->>Redis: SET TTL
  end
  API-->>C: 200""",
        quiz=[
            ("Что делает приложение при miss?", "читает БД и кладёт результат в Redis", "Кэш заполняется по требованию (lazy)."),
            ("Что сделать с ключом после UPDATE в БД?", "удалить или обновить ключ", "Иначе клиент может читать stale."),
            ("Зачем TTL при cache-aside?", "ограничить жизнь устаревших данных", "Страховка, если забыли инвалидировать."),
        ],
        cheat_html="""<h3>cache-aside</h3>
<pre><code>get(k):
  v = redis.get(k)
  if v: return v
  v = db.get()
  redis.set(k, v, ttl)
  return v</code></pre>""",
        anki=[
            ("cache-aside hit", "значение берём из Redis без похода в БД"),
            ("После UPDATE", "инвалидировать ключ кэша"),
            ("Ключ кэша", "стабильный id или hash параметров"),
        ],
        summary=["Hit/miss — база middle", "Инвалидация = половина дизайна", "TTL — страховка"],
        links=[
            ("PY20 кеш", "/game/learn/py-db-cache-memcached"),
            ("TTL", "/game/learn/rd-ttl-persistence"),
        ],
        next_link=("Stampede и locks", "/game/learn/rd-stampede-locks"),
    )
    articles["rd05-stampede-locks.md"] = article(
        slug="rd-stampede-locks",
        title="Cache stampede и блокировки ключа",
        short="Stampede",
        episode="RD05",
        rubric="data",
        order=705,
        published="2027-05-09T10:00:00+03:00",
        profiles=["developer", "analyst"],
        level="middle",
        tags=["redis", "stampede", "dogpile", "собеседование"],
        duration=30,
        excerpt="Dogpile при истечении TTL: singleflight и lock на ключ.",
        prerequisites=["rd-cache-aside"],
        seo_title="Redis stampede dogpile — middle",
        seo_desc="Что такое cache stampede и как защититься singleflight/lock.",
        seo_kw=["stampede", "dogpile", "redis", "собеседование"],
        intro="Когда TTL истекает одновременно у многих воркеров, все бегут в БД — stampede (dogpile).",
        sections=[
            (
                "Проблема",
                "Популярный ключ протух → N параллельных запросов делают один и тот же тяжёлый SELECT. "
                "БД перегружается ровно в момент «промаха».",
            ),
            (
                "Защита",
                "**Singleflight / lock на ключ**: первый воркер берёт блокировку (SET NX EX), грузит БД, "
                "пишет кэш, отпускает; остальные ждут или отдают stale. Soft TTL / early refresh — другой приём.",
            ),
            (
                "Связь с Memcached",
                "Та же идея в PY20 про dogpile. См. [py-db-cache-memcached](/game/learn/py-db-cache-memcached).",
            ),
        ],
        lab_goal="Смоделировать stampede на бумаге и добавить lock.",
        lab_steps=[
            "Нарисуйте 5 клиентов на один miss без защиты.",
            "Добавьте SET key:lock NX EX 5.",
            "Опишите поведение второго клиента.",
            "Назовите риск долгого lock.",
            "Сравните с просто увеличенным TTL.",
        ],
        lab_group="кто держит lock — кто ждёт; обсудите timeout.",
        lab_done=["Объясняете stampede", "Знаете SET NX как lock", "Связываете с hot key"],
        diagram_title="Stampede",
        diagram="""flowchart TB
  Miss[TTL expired] --> Many[N workers]
  Many --> DB[(DB overload)]
  Miss --> Lock[one holder]
  Lock --> DB2[(one SELECT)]
  DB2 --> Cache[SET cache]""",
        quiz=[
            ("Что такое cache stampede?", "много одновременных загрузок одного ключа из БД после miss", "Ещё называют dogpile."),
            ("Как SET NX помогает?", "только один ставит lock и грузит БД", "Остальные не дублируют тяжёлый запрос."),
            ("Риск lock без TTL?", "вечная блокировка при падении держателя", "Поэтому EX на lock обязателен."),
        ],
        cheat_html="""<h3>Lock</h3>
<pre><code>SET lock:user:1 1 NX EX 5</code></pre>
<ul><li>один грузит БД</li><li>остальные ждут / stale</li></ul>""",
        anki=[
            ("dogpile", "штампede при массовом miss одного ключа"),
            ("SET NX EX", "взять lock с автоснятием"),
            ("soft TTL", "обновлять кэш до жёсткого протухания"),
        ],
        summary=["Stampede = дружный miss", "Lock/singleflight лечит hot key", "TTL на lock обязателен"],
        links=[
            ("cache-aside", "/game/learn/rd-cache-aside"),
            ("PY20", "/game/learn/py-db-cache-memcached"),
        ],
        next_link=("pub/sub vs очередь", "/game/learn/rd-pubsub-vs-queue"),
    )
    articles["rd06-pubsub-vs-queue.md"] = article(
        slug="rd-pubsub-vs-queue",
        title="Redis pub/sub vs брокер сообщений",
        short="pub/sub vs queue",
        episode="RD06",
        rubric="data",
        order=706,
        published="2027-05-11T10:00:00+03:00",
        profiles=["developer", "analyst"],
        level="middle",
        tags=["redis", "pubsub", "kafka", "собеседование"],
        duration=28,
        excerpt="Когда Redis pub/sub уместен и чем не заменяет Kafka/RabbitMQ.",
        prerequisites=["rd-stampede-locks"],
        seo_title="Redis pub/sub vs Kafka — middle",
        seo_desc="Отличие pub/sub Redis от брокера с персистентностью и consumer group.",
        seo_kw=["redis", "pubsub", "kafka", "rabbitmq", "собеседование"],
        intro="Redis умеет PUBLISH/SUBSCRIBE, но это не замена Kafka. Middle должен провести границу.",
        sections=[
            (
                "Redis pub/sub",
                "Сообщения доставляются подписчикам online. Если клиента не было — сообщение не «подождёт» "
                "в журнале (в классическом pub/sub). Подходит для сигналов, инвалидации кэша, live-уведомлений.",
            ),
            (
                "Брокер",
                "Kafka/Rabbit хранят сообщения, дают ack, retry, DLQ, consumer groups. См. канон: "
                "[sa-sync-async-queues](/game/learn/sa-sync-async-queues).",
            ),
            (
                "Выбор",
                "Нужен replay и гарантии доставки → брокер. Нужен лёгкий fan-out сигнала → Redis pub/sub "
                "(или Streams — отдельная тема; на junior/middle достаточно честно разделить).",
            ),
        ],
        lab_goal="Выбрать механизм для двух сценариев.",
        lab_steps=[
            "Инвалидация кэша на 3 инстанса API — pub/sub или Kafka?",
            "Очередь писем с retry — ?",
            "Обоснуйте каждый выбор в 2 предложениях.",
            "Назовите риск pub/sub при рестарте подписчика.",
            "Ссылку на SA10 добавьте в конспект.",
        ],
        lab_group="поменяйтесь сценариями и проверьте аргументы.",
        lab_done=["Не путаете pub/sub с очередью", "Ссылаетесь на SA10", "Знаете про потерю offline-сообщений"],
        diagram_title="Fan-out сигнала",
        diagram="""flowchart LR
  Pub[PUBLISH invalidate] --> S1[API1]
  Pub --> S2[API2]
  Pub --> S3[API3]""",
        quiz=[
            ("Сохраняет ли классический Redis pub/sub сообщения для offline?", "нет", "Нужен брокер или Streams с иной семантикой."),
            ("Когда брать Kafka вместо pub/sub?", "нужны replay, consumer group, долгая доставка", "Событийный журнал и развязка продюсера."),
            ("Хороший кейс pub/sub?", "сигнал сбросить кэш на всех нодах", "Лёгкий fan-out без жёстких гарантий."),
        ],
        cheat_html="""<h3>Граница</h3>
<ul>
<li>pub/sub — сигнал online</li>
<li>брокер — хранение + retry</li>
</ul>
<p>См. SA10 sync/async</p>""",
        anki=[
            ("Redis PUBLISH", "отправить сообщение каналу подписчикам online"),
            ("Почему не замена Kafka", "нет того же журнала/replay/гарантий из коробки"),
            ("Кейс pub/sub", "invalidate cache / live signal"),
        ],
        summary=["pub/sub ≠ очередь", "Канон брокеров — SA10", "Сигналы vs бизнес-события"],
        links=[
            ("SA sync/async queues", "/game/learn/sa-sync-async-queues"),
            ("Stampede", "/game/learn/rd-stampede-locks"),
        ],
        next_link=("Eviction и cluster", "/game/learn/rd-eviction-cluster"),
    )
    articles["rd07-eviction-cluster.md"] = article(
        slug="rd-eviction-cluster",
        title="Eviction, Sentinel и Cluster — обзор",
        short="Eviction cluster",
        episode="RD07",
        rubric="data",
        order=707,
        published="2027-05-13T10:00:00+03:00",
        profiles=["developer", "analyst"],
        level="senior",
        tags=["redis", "eviction", "cluster", "sentinel", "собеседование"],
        duration=35,
        excerpt="maxmemory-policy, Sentinel и Redis Cluster на уровне обзора для собеса.",
        prerequisites=["rd-pubsub-vs-queue"],
        seo_title="Redis eviction Sentinel Cluster — senior",
        seo_desc="Политики вытеснения памяти и обзор HA: Sentinel vs Cluster.",
        seo_kw=["eviction", "sentinel", "redis cluster", "собеседование"],
        intro="Senior-вопросы: что будет, когда память кончилась, и чем Sentinel отличается от Cluster.",
        sections=[
            (
                "Eviction",
                "При `maxmemory` Redis вытесняет ключи по политике: `noeviction` (ошибка записи), "
                "`allkeys-lru`, `volatile-lru`, `allkeys-lfu` и др. Для кэша обычно LRU/LFU; "
                "для «важных» ключей без TTL `noeviction` + мониторинг.",
            ),
            (
                "Sentinel",
                "Мониторинг master/replica и автоматический failover. Клиенты узнают нового master. "
                "Это HA для одного логического шарда, не шардирование данных.",
            ),
            (
                "Cluster",
                "Данные делятся по hash slots между нодами. Масштаб по данным/нагрузке. Сложность операций "
                "multi-key. На собесе: «Cluster — шарды; Sentinel — failover одного набора».",
            ),
        ],
        lab_goal="Составить таблицу выбора eviction и HA.",
        lab_steps=[
            "Кэш сессий — какая policy?",
            "Критичный счётчик без TTL — риск allkeys-lru?",
            "Нужен failover без шардов — Sentinel или Cluster?",
            "Нужно 100GB данных — ?",
            "Запишите один operational risk Cluster (reshard / multi-key).",
        ],
        lab_group="один предлагает Cluster «на всякий случай» — второй возражает.",
        lab_done=["Называете 2 policy", "Отличаете Sentinel от Cluster", "Связываете eviction с типом данных"],
        diagram_title="HA варианты",
        diagram="""flowchart TB
  App --> Sentinel
  Sentinel --> Master
  Master --> Replica
  App2 --> Cluster
  Cluster --> N1
  Cluster --> N2
  Cluster --> N3""",
        quiz=[
            ("allkeys-lru делает что?", "вытесняет наименее недавно использованные среди всех ключей", "Когда память на пределе."),
            ("Sentinel vs Cluster?", "failover репликации vs шардирование слотов", "Разные задачи HA/scale."),
            ("noeviction при полной памяти?", "ошибка на запись, ключи не вытесняются", "Подходит не для чистого кэша."),
        ],
        cheat_html="""<h3>Eviction</h3>
<ul><li>lru/lfu — для кэша</li><li>noeviction — строгий режим</li></ul>
<h3>HA</h3>
<ul><li>Sentinel — failover</li><li>Cluster — slots</li></ul>""",
        anki=[
            ("maxmemory-policy", "что делать при нехватке RAM"),
            ("Sentinel", "автоfailover master/replica"),
            ("Cluster hash slot", "ключ → слот → нода"),
        ],
        summary=["Eviction — политика выживания кэша", "Sentinel ≠ Cluster", "Senior связывает конфиг с риском"],
        links=[
            ("Redis Cluster spec", "https://redis.io/docs/reference/cluster-spec/"),
            ("pub/sub", "/game/learn/rd-pubsub-vs-queue"),
        ],
        next_link=("Capstone Redis", "/game/learn/rd-capstone"),
    )
    articles["rd08-capstone.md"] = article(
        slug="rd-capstone",
        title="Capstone Redis — drill и чеклист",
        short="Capstone Redis",
        episode="RD08",
        rubric="data",
        order=708,
        published="2027-05-15T10:00:00+03:00",
        profiles=["developer", "analyst"],
        level="senior",
        tags=["redis", "capstone", "собеседование"],
        duration=35,
        excerpt="Итоговый drill Redis vs PostgreSQL и чеклист RD01–RD07.",
        prerequisites=["rd-eviction-cluster"],
        seo_title="Redis capstone checklist — senior",
        seo_desc="Чеклист серии Redis и drill сравнения с PostgreSQL.",
        seo_kw=["redis", "capstone", "чеклист", "собеседование"],
        intro="Финальный выпуск: собрать ответы серии и проверить пробелы перед собесом.",
        sections=[
            (
                "Чеклист уровней",
                "**Junior:** KV, типы, TTL/persistence, не source of truth.\n\n"
                "**Middle:** cache-aside, stampede, pub/sub vs брокер.\n\n"
                "**Senior:** eviction, Sentinel/Cluster обзор.",
            ),
            (
                "Redis vs PostgreSQL",
                "PostgreSQL — схема, JOIN, транзакции, отчёты. Redis — низкая задержка, кэш, счётчики, "
                "сигналы. Гибрид нормален. См. [sql-ddl-dml-dcl](/game/learn/sql-ddl-dml-dcl).",
            ),
            (
                "Индекс slug",
                "| Ep | slug |\n|----|------|\n| RD01 | rd-kv-model |\n| RD02 | rd-data-types |\n"
                "| RD03 | rd-ttl-persistence |\n| RD04 | rd-cache-aside |\n| RD05 | rd-stampede-locks |\n"
                "| RD06 | rd-pubsub-vs-queue |\n| RD07 | rd-eviction-cluster |\n| RD08 | rd-capstone |",
            ),
        ],
        lab_goal="Пройти drill из 8 вопросов по одному на выпуск.",
        lab_steps=[
            "Закройте SERIES и ответьте на 8 вопросов вслух по таймеру 60с.",
            "Отметьте ❌ и откройте соответствующий slug.",
            "Повторите Anki слабых выпусков.",
            "Сформулируйте гибрид PG+Redis для своего pet-проекта.",
            "Добавьте ссылку на map-redis / PY20 в конспект.",
        ],
        lab_group="парный drill: вопрос → ответ → правка.",
        lab_done=["Есть персональный gap-list", "Умеете сравнить Redis и PG", "Знаете индекс slug"],
        diagram_title="Трек RD",
        diagram="""flowchart LR
  RD01 --> RD02 --> RD03 --> RD04 --> RD05 --> RD06 --> RD07 --> RD08""",
        quiz=[
            ("Когда Redis, когда PostgreSQL?", "кэш/lookup/сигналы vs схема/JOIN/OLTP-правда", "Гибрид частый."),
            ("Главный риск stampede?", " thrashing БД на hot key miss", "Лечится lock/singleflight."),
            ("Sentinel решает какую задачу?", "failover репликации", "Не шардирование."),
        ],
        cheat_html="""<h3>Чеклист</h3>
<ul>
<li>KV + типы + TTL</li>
<li>cache-aside + stampede</li>
<li>pub/sub ≠ Kafka</li>
<li>eviction + HA обзор</li>
</ul>""",
        anki=[
            ("Индекс RD01", "rd-kv-model"),
            ("Индекс RD04", "rd-cache-aside"),
            ("Гибрид", "PG пишет правду, Redis ускоряет"),
        ],
        summary=["Capstone = чеклист + drill", "Не зубрите команды — сценарии", "Связки с SQL/SA/PY обязательны"],
        links=[
            ("SERIES", "/game/learn"),
            ("SQL01", "/game/learn/sql-ddl-dml-dcl"),
            ("PY20", "/game/learn/py-db-cache-memcached"),
            ("SA10", "/game/learn/sa-sync-async-queues"),
        ],
    )
    return articles


if __name__ == "__main__":
    # Placeholder: full builder continues in same file via exec of remaining builders
    print("module loaded; use generate_all()")
