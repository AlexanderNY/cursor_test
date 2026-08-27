import type { LearnEpisode } from './types'

export const learnEpisodes: LearnEpisode[] = [
  {
    slug: 's01e01-sloi',
    episode: 'S01E01',
    title: 'Зачем собирать сервис слоями',
    shortTitle: 'Слои',
    rubricId: 'architecture',
    order: 1,
    theory: `S01E01 · Слои · UI / API / БД / деплой

Сервис — это не «один файл Python, который рисует HTML». Как только появляются второй пользователь, обновление кода и падение базы, слои начинают окупаться.

Четыре слоя, которые вы соберёте за сезон:

1. UI — то, что видит человек (у нас позже React).
2. API — контракт: HTTP, JSON, ошибки. Без экранов.
3. БД — факты, которые переживают перезапуск процесса (PostgreSQL).
4. Деплой — как это запускают одинаково у вас и на стенде (сначала Compose, потом Minikube).

Зачем это в живом сервисе. У CopyParse браузер не ходит в базу: он говорит с UI и с \`/api\`, дальше шлюз, сервисы, Postgres. Если смешать всё в одном процессе, нельзя заменить только бота или только фронт.

Граница. Слой «оркестратор / Kafka / микросервисы на каждый чих» в первую неделю — лишняя фича. Сначала четыре коробки и понятные стрелки.

Следующий выпуск: карта CopyParse — кто кому звонит, без клонирования всего монорепо.`,
    lab: `**20 минут.** На бумаге или в любом редакторе нарисуйте свой учебный сервис «Заявки» четырьмя прямоугольниками: UI, API, БД, деплой. Подпишите одну стрелку: кто кого вызывает при «создать заявку».

**В группу:** фото схемы. Не код.

**Проверка:** на схеме база не торчит в браузер напрямую.`,
    links: [
      {
        label: 'Двенадцать факторов: процессы, конфиг, подключённые сервисы',
        href: 'https://12factor.net/ru/',
      },
      {
        label: 'HTTP как транспорт API (методы, статус-коды)',
        href: 'https://developer.mozilla.org/ru/docs/Web/HTTP/Overview',
      },
      {
        label: 'Как устроен стенд курса: docs/ARCHITECTURE.md в репозитории CopyParse',
        href: '#',
      },
    ],
    diagram: `flowchart LR
  User[Человек] --> UI[UI]
  UI --> API[API]
  API --> DB[(БД)]
  Deploy[Деплой] -.-> UI
  Deploy -.-> API
  Deploy -.-> DB`,
    cheatsheet: `### Слои (запомнить)

| Слой | Отвечает за | Не делает |
|------|-------------|-----------|
| UI | Экраны, формы | Прямой доступ к БД |
| API | HTTP, JSON, коды ошибок | Вёрстку |
| БД | Факты после рестарта | Бизнес-логику UI |
| Деплой | Одинаковый запуск | «У меня локально ок» |

### Стрелка «создать заявку»

\`Человек → UI → API → БД\`

### Не делать

- Браузер → Postgres
- Один файл «и HTML, и SQL, и деплой»
- Kafka / оркестратор в первую неделю

### Готово, если…

- [ ] На схеме 4 коробки
- [ ] Одна подписанная стрелка вызова
- [ ] БД не торчит в браузер`,
  },
  {
    slug: 's01e02-karta',
    episode: 'S01E02',
    title: 'Карта CopyParse за 10 минут',
    shortTitle: 'Карта',
    rubricId: 'architecture',
    order: 2,
    theory: `S01E02 · Карта · кто кому звонит

Сегодня не поднимаем стенд. Учимся читать чужую систему по коробкам, а не по файлам.

Упрощённо CopyParse:

- Край: nginx принимает HTTPS и режет по Host.
- UI — React. Браузер ходит на UI и на \`/api\`.
- Шлюз (gateway) — JWT, CORS, прокси во внутренние сервисы.
- Платформа: auth, core, scheduler, collector, processor.
- Боты площадок: Telegram, VK и остальные.
- Данные: PostgreSQL и объектное хранилище S3 (MinIO).

Путь «опубликовать пост»: UI или бот → данные в Postgres → collector/processor гоняют статусы → бот площадки публикует. Это конвейер со статусами, не один скрипт \`send()\`.

Зачем это вам. Ваш сервис заявок в миниатюре повторит ту же идею: UI не пишет в БД в обход API, деплой не равен «у меня на ноутбуке завелось».

Граница. Не клонируйте весь монорепо на первой неделе и не пытайтесь понять каждый бот. Пять коробок достаточно.

Следующий выпуск: Git и GitHub — чтобы лабы жили в ветке, а не в архиве на Рабочем столе.`,
    lab: `**20 минут.** Перерисуйте схему своими словами (можно 6–7 блоков, не 20). Подпишите красным путь одного действия: «пользователь нажал Опубликовать».

**В группу:** фото/скрин схемы.

**Проверка:** на пути есть API или шлюз; UI не подключён к Postgres напрямую.`,
    links: [
      {
        label: 'Высокоуровневая схема стенда — docs/ARCHITECTURE.md',
        href: '#',
      },
      {
        label: 'Что делает UI после входа — docs/USER_GUIDE.md',
        href: '#',
      },
      {
        label: 'Паттерн BFF / gateway (Microsoft)',
        href: 'https://learn.microsoft.com/ru-ru/azure/architecture/microservices/design/gateway',
      },
    ],
    diagram: `flowchart LR
  User[Браузер] --> Edge[nginx]
  Edge --> UI[UI]
  Edge --> GW[gateway]
  UI --> GW
  GW --> Auth[auth]
  GW --> Core[core]
  GW --> Bots[боты]
  Core --> PG[(PostgreSQL)]
  Bots --> PG`,
    cheatsheet: `### Коробки CopyParse

1. **nginx** — HTTPS, Host
2. **UI** — React
3. **gateway** — JWT, CORS, прокси
4. **Сервисы** — auth, core, боты…
5. **Данные** — Postgres + S3/MinIO

### Путь «Опубликовать»

\`UI → gateway → core/боты → Postgres → статусы → публикация\`

Не: \`UI → send() в бот напрямую\`.

### Не делать

- Клонировать весь монорепо в первую неделю
- Рисовать 20 микросервисов «как в проде»
- UI → Postgres

### Готово, если…

- [ ] 5–7 блоков своими словами
- [ ] Красный путь «Опубликовать»
- [ ] На пути есть API/шлюз`,
  },
  {
    slug: 's01e03-git',
    episode: 'S01E03',
    title: 'Git / GitHub',
    shortTitle: 'Git',
    rubricId: 'tools',
    order: 3,
    theory: `S01E03 · Git · commit, ветка, PR — на примерах

Код без истории — черновик на Рабочем столе. Git фиксирует *что* изменилось. GitHub — *где это обсудить*, не кидая zip в мессенджер.

Сквозной пример сезона: репозиторий учебного сервиса **«Заявки»** (\`tickets\`).

### 1. Репозиторий

Один учебный проект — один repo. На GitHub: New repository → имя \`tickets\` (private нормально) → **без** README, если будете \`git init\` локально.

\`\`\`bash
mkdir tickets
cd tickets
git init
git branch -M main
\`\`\`

### 2. .gitignore сразу, до первого commit

Иначе \`.env\` и \`venv/\` уедут в историю навсегда.

\`\`\`
.env
venv/
.venv/
__pycache__/
*.pyc
node_modules/
.idea/
.vscode/
*.pem
\`\`\`

Плохо: закоммитить \`.env\` с \`DATABASE_URL=...\` и потом «удалить файл» — секрет уже в истории.

### 3. Commit — снимок с понятным сообщением

\`\`\`bash
git add .gitignore README.md
git status
git commit -m "init: учебный сервис заявок, gitignore"
\`\`\`

| Плохо | Хорошо |
|-------|--------|
| \`fix\` | \`init: учебный сервис заявок, gitignore\` |
| \`asdf\` | \`docs: схема слоёв UI/API/БД\` |
| \`update\` | \`feat: черновик статусов заявки\` |

### 4. Ветка: \`main\` бережём

\`\`\`bash
git switch -c s01-e03
# правите docs/layers.md (схема из E01 текстом)
git add docs/layers.md
git commit -m "docs: схема слоёв для сервиса заявок"
\`\`\`

Имена веток: \`s01-e03\`, \`feature/tickets-api\` — коротко и по делу.

### 5. Push и Pull Request

\`\`\`bash
git remote add origin https://github.com/<you>/tickets.git
git push -u origin main
git push -u origin s01-e03
\`\`\`

На GitHub: Compare & pull request → \`s01-e03\` → \`main\`. В PR смотрите **Files changed** (дифф), не кнопку Merge.

Зачем это в живом сервисе. В CopyParse секреты не кладут в git (\`secret.yaml\` собирают из example). Один пароль БД в истории = ротация у всех.

Граница. Теги, rebase «как в банке» и монорепо-тулинг подождут. В сезон 1: ветка + понятный commit + PR.

Следующий выпуск: системный анализ — контракт API до первой строчки FastAPI.`,
    lab: `**30–40 минут.** Цель: один PR без секретов.

1. Создайте пустой репозиторий \`tickets\` на GitHub (private ок). **Не** ставьте галку «Add a README», если идёте путём ниже.
2. Локально:

\`\`\`bash
mkdir tickets && cd tickets
git init
git branch -M main
\`\`\`

Создайте \`.gitignore\` (блок из теории) и \`README.md\` на 3 строки: что за сервис, для кого, стек позже.

3. Первый commit в \`main\`, push:

\`\`\`bash
git add .gitignore README.md
git commit -m "init: учебный сервис заявок, gitignore"
git remote add origin https://github.com/<you>/tickets.git
git push -u origin main
\`\`\`

4. Ветка и второй commit:

\`\`\`bash
git switch -c s01-e03
# файл docs/layers.md — четыре слоя + стрелка «создать заявку» (из E01)
git add docs/layers.md
git commit -m "docs: схема слоёв для сервиса заявок"
git push -u origin s01-e03
\`\`\`

5. Откройте Pull Request \`s01-e03\` → \`main\`. Просмотрите Files changed.

**В группу:** ссылка на PR.

**Проверка:**
- в диффе нет \`.env\`, \`venv/\`, \`__pycache__/\`
- у обоих commit сообщения читаются (не \`fix\`)
- PR идёт не из \`main\` в \`main\`, а из ветки лабы`,
    links: [
      { label: 'Pro Git, главы 2–3', href: 'https://git-scm.com/book/ru/v2' },
      {
        label: 'GitHub Flow',
        href: 'https://docs.github.com/ru/get-started/using-github/github-flow',
      },
      { label: 'Шаблоны .gitignore', href: 'https://github.com/github/gitignore' },
    ],
    diagram: `flowchart LR
  Main[main] --> Branch[s01_e03]
  Branch --> Commit[commit_docs]
  Commit --> Push[push]
  Push --> PR[Pull_Request]
  PR --> Review[ревью_диффа]
  Review --> Main`,
    cheatsheet: `### Команды подряд (happy path)

\`\`\`bash
git init
git branch -M main
git status
git add .gitignore README.md
git commit -m "init: учебный сервис заявок, gitignore"
git remote add origin https://github.com/<you>/tickets.git
git push -u origin main

git switch -c s01-e03
git add docs/layers.md
git commit -m "docs: схема слоёв для сервиса заявок"
git push -u origin s01-e03
# дальше PR на GitHub: s01-e03 → main
\`\`\`

### Смотреть, что происходит

\`\`\`bash
git status          # что изменено / в индексе
git log --oneline   # короткая история
git diff            # незакоммиченный дифф
git diff --staged   # то, что уже в add
\`\`\`

### .gitignore (минимум)

\`\`\`
.env
venv/
.venv/
__pycache__/
*.pyc
node_modules/
*.pem
\`\`\`

### Не делать

- Commit \`fix\` / \`asdf\` / \`update\`
- Класть \`.env\` и \`venv/\` в репозиторий
- Писать лабу прямо в \`main\` без ветки и PR
- «Починить» секрет удалением файла без ротации — история помнит

### Готово, если…

- [ ] Есть PR со ссылкой
- [ ] В Files changed нет секретов и venv
- [ ] Два осмысленных commit message
- [ ] Ветка лабы ≠ \`main\``,
  },
  {
    slug: 's01e04-sa',
    episode: 'S01E04',
    title: 'SA: от боли к контракту API',
    shortTitle: 'SA / контракт',
    rubricId: 'api',
    order: 4,
    theory: `S01E04 · SA · контракт до экранов

Системный анализ — не «нарисовать макет». Это ответить: какая боль, какой факт в системе меняется, какой HTTP-контракт это фиксирует.

Порядок, который экономит переписывание React:

1. Боль. «Куратор не видит, какие заявки зависли».
2. Факт. Заявка имеет статус: \`new\` → \`in_progress\` → \`done\` (отказ — отдельный статус, не удаление строки «чтобы не потерять историю»).
3. Контракт. \`POST /tickets\`, \`GET /tickets\`, \`PATCH /tickets/{id}\` — поля, коды 400/404/409.
4. Экран. Список и форма появляются после пунктов 1–3.

Так устроен CopyParse: пост живёт статусами (\`collected\` → \`review\`/\`ready\` → \`published\`), а не кнопкой «отправить во все сети сразу».

Граница. Не пишите ТЗ на 40 страниц и не тащите Kafka «на вырост». Одна страница: цель, 3–5 операций, статусы, что *не* делаем в MVP.

Следующий выпуск: FastAPI — первый роутер под этот контракт.`,
    lab: `**40 минут.** Одна страница (Google Doc, Markdown в репо — как удобно).

Заголовок: «Заявки, MVP». Блоки:

- Кто пользователь и какая боль (2–3 предложения).
- Статусы заявки (3–4 значения, переходы).
- Таблица операций: метод, путь, тело, успешный код, ошибка.
- Одна убитая фича: что сознательно не делаем (комментарии, файлы, роли админа — выберите одно и напишите почему).

**В группу:** ссылка или файл \`docs/tz-mvp.md\` в PR.

**Проверка:** в таблице есть хотя бы один 409/404; нет пункта «красивый UI».`,
    links: [
      {
        label: 'Методы HTTP',
        href: 'https://developer.mozilla.org/ru/docs/Web/HTTP/Reference/Methods',
      },
      {
        label: 'Семантика статус-кодов',
        href: 'https://developer.mozilla.org/ru/docs/Web/HTTP/Reference/Status',
      },
      {
        label: 'Ресурсная модель REST (Microsoft)',
        href: 'https://learn.microsoft.com/ru-ru/azure/architecture/best-practices/api-design',
      },
    ],
    diagram: `flowchart LR
  Pain[Боль] --> Fact[Факт_и_статусы]
  Fact --> Contract[Контракт_HTTP]
  Contract --> UI[Экраны]`,
    cheatsheet: `### Порядок SA

\`Боль → Факт/статусы → Контракт HTTP → Экраны\`

### Таблица операций (шаблон)

| Метод | Путь | Тело | OK | Ошибка |
|-------|------|------|-----|--------|
| POST | /tickets | title | 201 | 400 |
| GET | /tickets | — | 200 | — |
| PATCH | /tickets/{id} | status | 200 | 404 / 409 |

### Статусы заявки (пример)

\`new → in_progress → done\` (+ \`rejected\`, не DELETE)

### Не делать

- ТЗ на 40 страниц
- Kafka «на вырост»
- Начинать с макета React

### Готово, если…

- [ ] Есть 409 или 404 в таблице
- [ ] Есть убитая фича
- [ ] Нет пункта «красивый UI»`,
  },
  {
    slug: 's01e05-fastapi',
    episode: 'S01E05',
    title: 'FastAPI: первый роутер и Pydantic',
    shortTitle: 'FastAPI',
    rubricId: 'api',
    order: 5,
    theory: `S01E05 · FastAPI · роутер и Pydantic

API начинается не с базы, а с контракта: путь, вход, выход, ошибка. FastAPI как раз заставляет это написать типами.

Три понятия:

- Роутер — набор путей (\`GET /health\`, \`GET /tickets\`). Позже разрежете по модулям, сейчас хватит одного файла.
- Pydantic-модель — JSON, который вы обещаете. Лишнее поле клиента не должно молча ломать сервер; недостающее — 422, не 500.
- Обработчик — функция. Пока можно вернуть список из памяти. База будет в E07.

Зачем это в живом сервисе. В CopyParse сервисы на FastAPI: шлюз и core говорят JSON-контрактами, а не «как получилось в print».

Граница. Не подключайте ORM, JWT и Docker в этом выпуске. Один процесс, \`uvicorn\`, две ручки. Swagger сам появится на \`/docs\` — это нормально, не отдельный микросервис.

Следующий выпуск: Insomnia — те же ручки без браузера и без React.`,
    lab: `**40 минут.** В ветке репозитория заявок:

1. Минимальный FastAPI: \`GET /health\` → \`{"status": "ok"}\`.
2. Модель \`Ticket\` (id, title, status) и \`GET /tickets\` — верните 2–3 объекта из списка в коде.
3. Запуск: \`uvicorn\`. Откройте \`/docs\`.

**В группу:** скрин \`/docs\` и URL локально (localhost достаточно).

**Проверка:** OpenAPI в \`/docs\` совпадает с таблицей из вашего ТЗ хотя бы по \`GET /tickets\`. Если нет — поправьте либо код, либо ТЗ, не оба «на потом».`,
    links: [
      {
        label: 'First Steps',
        href: 'https://fastapi.tiangolo.com/tutorial/first-steps/',
      },
      {
        label: 'Pydantic-модели в FastAPI',
        href: 'https://fastapi.tiangolo.com/tutorial/body/',
      },
      {
        label: 'Автодокументация OpenAPI',
        href: 'https://fastapi.tiangolo.com/tutorial/metadata/',
      },
    ],
    diagram: `flowchart LR
  Client[Клиент] --> Route["GET /tickets"]
  Route --> Model[Pydantic]
  Model --> Handler[Обработчик]
  Handler --> JSON[JSON]`,
    cheatsheet: `### Скелет

\`\`\`python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Ticket(BaseModel):
    id: int
    title: str
    status: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tickets", response_model=list[Ticket])
def list_tickets():
    return [...]
\`\`\`

### Запуск

\`\`\`bash
uvicorn main:app --reload
# docs → http://127.0.0.1:8000/docs
\`\`\`

### Коды

| Ситуация | Код |
|----------|-----|
| OK | 200 |
| Создано | 201 |
| Плохое тело / валидация | 422 |
| Не найдено | 404 |
| Сервер упал | 500 — чинить, не маскировать |

### Не делать

- ORM + JWT + Docker в этом выпуске
- Ответ «как print» без модели

### Готово, если…

- [ ] \`/health\` и \`/tickets\` в \`/docs\`
- [ ] Совпадает с ТЗ хотя бы по GET /tickets`,
  },
  {
    slug: 's01e06-insomnia',
    episode: 'S01E06',
    title: 'Insomnia: коллекция до UI',
    shortTitle: 'Insomnia',
    rubricId: 'tools',
    order: 6,
    theory: `S01E06 · Insomnia · API проверяем до React

UI ещё нет — и это хорошо. Если ручка жива только «когда открыта страница», вы не отличите баг фронта от бага сервера.

Insomnia (или аналог) нужна как **клиент контракта**:

- Коллекция — набор запросов, который живёт рядом с кодом, а не в голове.
- Environment — \`base_url\` для local (\`http://127.0.0.1:8000\`). Позже добавите minikube, не плодя копии запросов.
- Заголовки. Пока без JWT; привыкайте видеть \`Content-Type: application/json\`. Authorization появится позже.

Зачем это в живом сервисе. Шлюз CopyParse отдаёт JSON; отладка «пост не ушёл» начинается с запроса к API, не с кликов в UI.

Граница. Не превращайте Insomnia в CI. Сначала руками, коллекцию — в git. Прогоны в Jenkins — сезон 2.

Следующий выпуск: PostgreSQL — факты заявок переживут перезапуск uvicorn.`,
    lab: `**30 минут.**

1. Установите Insomnia: https://insomnia.rest/download
2. Создайте коллекцию «Заявки», env \`local\` с \`base_url\`.
3. Запросы: \`GET {{ base_url }}/health\` и \`GET {{ base_url }}/tickets\`. Сохраните успешные ответы.
4. Экспорт коллекции (JSON) в репозиторий, например \`insomnia/tickets.json\`. Commit в ветке.

**В группу:** скрин двух зелёных запросов + путь к файлу коллекции в PR.

**Проверка:** одногруппник может импортировать JSON и попасть в ваши ручки, сменив только \`base_url\`.`,
    links: [
      { label: 'Скачать Insomnia', href: 'https://insomnia.rest/download' },
      {
        label: 'Коллекции и окружения',
        href: 'https://docs.insomnia.rest/insomnia/environments',
      },
      {
        label: 'Импорт / экспорт',
        href: 'https://docs.insomnia.rest/insomnia/import-export-data',
      },
    ],
    diagram: `flowchart LR
  Insomnia[Insomnia] --> Health["GET /health"]
  Insomnia --> Tickets["GET /tickets"]
  Health --> API[FastAPI]
  Tickets --> API`,
    cheatsheet: `### Environment

\`\`\`
base_url = http://127.0.0.1:8000
\`\`\`

Запросы: \`{{ base_url }}/health\`, \`{{ base_url }}/tickets\`

### Чеклист запроса

- Method + URL
- \`Content-Type: application/json\` (для тела)
- Сохранённый успешный ответ в коллекции
- JSON коллекции в git

### Не делать

- Копии одних и тех же запросов под каждый стенд (используйте env)
- «Проверил только в браузере на UI»
- Jenkins вместо ручной коллекции в сезон 1

### Готово, если…

- [ ] Два зелёных запроса
- [ ] \`insomnia/*.json\` в PR
- [ ] Меняется только \`base_url\``,
  },
  {
    slug: 's01e07-postgres',
    episode: 'S01E07',
    title: 'PostgreSQL: таблица и SELECT',
    shortTitle: 'PostgreSQL',
    rubricId: 'data',
    order: 7,
    theory: `S01E07 · PostgreSQL · таблица, PK, SELECT

Пока заявки живут в списке Python, перезапуск сервера стирает учебный стенд. База — это факты: строка либо есть, либо её нет.

Минимум:

- Таблица \`tickets\`: столбцы с типами, не «одна JSON-простыня на всё».
- Первичный ключ (\`id\`). Без него вы не скажете PATCH/DELETE «вот эта заявка».
- \`SELECT\` — чтение. Сначала без JOIN.
- Подключение с API. Один пул / одно соединение на запрос в учебном коде допустимо; соединение в глобальном цикле без закрытия — нет.

Зачем это в живом сервисе. CopyParse хранит посты и статусы в PostgreSQL: конвейер переживает рестарт бота.

Граница. Не настраивайте репликацию, партиции и Kafka «чтобы было как в банке». Одна база, одна таблица, три строки.

Следующий выпуск: JOIN и индекс — когда таблиц станет две.`,
    lab: `**40 минут.**

1. Поднимите Postgres (локально или контейнер). Создайте БД \`tickets\`.
2. SQL:

\`\`\`sql
CREATE TABLE tickets (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title      text NOT NULL,
  status     text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
\`\`\`

3. Вставьте 3 заявки. \`SELECT id, title, status FROM tickets;\`
4. Подключите FastAPI к БД: \`GET /tickets\` читает таблицу, не список в памяти.

**В группу:** скрин SELECT из клиента (psql, DBeaver, DataGrip) и зелёный \`GET /tickets\` в Insomnia после рестарта uvicorn.

**Проверка:** после рестарта API список тот же.`,
    links: [
      {
        label: 'Учебник PostgreSQL: старт',
        href: 'https://www.postgresql.org/docs/current/tutorial-start.html',
      },
      {
        label: 'Создание таблиц (Postgres Pro)',
        href: 'https://postgrespro.ru/docs/postgresql/current/ddl-basics',
      },
      {
        label: 'Docker image postgres',
        href: 'https://hub.docker.com/_/postgres',
      },
    ],
    diagram: `flowchart LR
  API[FastAPI] --> PG[(tickets)]
  Insomnia[Insomnia] --> API`,
    cheatsheet: `### DDL

\`\`\`sql
CREATE TABLE tickets (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title      text NOT NULL,
  status     text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO tickets (title, status) VALUES
  ('Первая', 'new'),
  ('Вторая', 'in_progress'),
  ('Третья', 'done');

SELECT id, title, status FROM tickets;
\`\`\`

### Правило

Список в Python → **пропадает** после рестарта.  
Строки в Postgres → **остаются**.

### Не делать

- Одна JSON-простыня «на всё»
- Соединение без закрытия в бесконечном цикле
- Репликация / партиции в этот выпуск

### Готово, если…

- [ ] SELECT в клиенте БД
- [ ] GET /tickets после рестарта uvicorn тот же`,
  },
  {
    slug: 's01e08-sql',
    episode: 'S01E08',
    title: 'SQL: JOIN и индекс',
    shortTitle: 'SQL JOIN',
    rubricId: 'data',
    order: 8,
    theory: `S01E08 · SQL · JOIN и зачем индекс

Одна таблица врёт, как только появляется «чей это». Автор заявки — не строка, повторённая в каждом title, а другая сущность.

JOIN склеивает факты по ключу: \`tickets.author_id = users.id\`. Это не «цикл в Python по двум спискам», это работа СУБД.

Индекс — структура, которая ускоряет поиск по условию (\`WHERE status = ...\`, \`WHERE author_id = ...\`). Цена: INSERT/UPDATE становятся чуть дороже, место на диске тоже. Индекс «на всякий случай по всем колонкам» — лишняя фича.

\`EXPLAIN\` (и \`EXPLAIN ANALYZE\`) показывает, пошла ли база seq scan по всей таблице или index scan. На трёх строках разницы не видно — и это нормально. Смотрите план, привыкайте к словам.

Зачем это в живом сервисе. В аналитике и в ядре CopyParse без JOIN и индексов под реальные выборки вы не отладите «почему тормозит список».

Граница. Не учите оконные функции и CTE в этом выпуске, если JOIN ещё не уверенный. Партиции и шардинг — не сюда.

Следующий выпуск: регулярные выражения — валидация на входе, не парсинг всего HTML.`,
    lab: `**40 минут.**

1. Таблица \`users (id, name)\`. 2–3 пользователя. В \`tickets\` добавьте \`author_id\` (FK).
2. Запрос: все заявки с именем автора — \`INNER JOIN\`.
3. Индекс: \`CREATE INDEX tickets_author_id_idx ON tickets (author_id);\`
4. \`EXPLAIN SELECT ... JOIN ... WHERE tickets.author_id = 1;\`

**В группу:** текст JOIN-запроса и скрин \`EXPLAIN\` (не обязательно ANALYZE).

**Проверка:** без JOIN в Python. Имена авторов приходят из SQL.`,
    links: [
      {
        label: 'JOIN в учебнике Postgres Pro',
        href: 'https://postgrespro.ru/docs/postgresql/current/tutorial-join',
      },
      {
        label: 'Индексы',
        href: 'https://postgrespro.ru/docs/postgresql/current/indexes-intro',
      },
      {
        label: 'Как читать EXPLAIN',
        href: 'https://postgrespro.ru/docs/postgresql/current/using-explain',
      },
    ],
    diagram: `flowchart LR
  Users[users] --> Join[JOIN]
  Tickets[tickets] --> Join
  Join --> Result[заявка_плюс_автор]`,
    cheatsheet: `### JOIN

\`\`\`sql
SELECT t.id, t.title, u.name AS author
FROM tickets t
INNER JOIN users u ON u.id = t.author_id
WHERE t.author_id = 1;
\`\`\`

### Индекс

\`\`\`sql
CREATE INDEX tickets_author_id_idx ON tickets (author_id);
EXPLAIN SELECT ... WHERE tickets.author_id = 1;
\`\`\`

### Когда индекс

- Часто фильтруете / джойните по колонке
- Не «на все колонки сразу»

### Не делать

- JOIN в цикле Python по двум спискам
- Оконные функции, пока JOIN не уверенный
- Индекс «на всякий случай»

### Готово, если…

- [ ] Имя автора из SQL, не из Python
- [ ] Есть скрин EXPLAIN`,
  },
  {
    slug: 's01e09-regex',
    episode: 'S01E09',
    title: 'Регулярные выражения',
    shortTitle: 'Regex',
    rubricId: 'tools',
    order: 9,
    theory: `S01E09 · Regex · валидация и где уже вредно

Регулярное выражение — это формальный язык для поиска по строке, не «искусственный интеллект» и не парсер HTML.

Где уместно в сервисе заявок:

- Грубый формат: код заявки \`TCK-\\d+\`, e-mail «есть @ и точка», slug из латиницы.
- Вырезать кусок из лога: номер запроса, статус.
- Серверная проверка плюс та же идея на клиенте — но источником правды остаётся API.

Где вредно:

- Разбор HTML/XML regex’ом («достать все ссылки из страницы») — ломается на вложенности. Для этого парсер.
- «Умная» валидация ФИО, адресов, телефона всех стран одним выражением — ложные отказы.
- Секреты и SQL: regex не заменяет параметризованные запросы.

В Python — модуль \`re\`. Отлаживать удобно на regex101: видны группы и расхождения Python vs JS.

Зачем это в живом сервисе. В пайплайне контента (чистка текста, URL, лимиты) без дисциплины regex легко сломать валидные данные.

Граница. Не пишите комбайн на 80 групп. Если выражение нельзя прочитать вслух — упростите или откажитесь.

Следующий выпуск: React — список заявок из того API, которое вы уже проверили Insomnia.`,
    lab: `**30 минут.**

1. На https://regex101.com/ (Flavor: Python) напишите выражение для кода заявки: \`TCK-\` и цифры. Прогоните 5 положительных и 3 отрицательных примера.
2. В FastAPI: поле \`code\` (или валидация \`title\`) через \`pattern\` в Pydantic либо \`re\` в хендлере. Невалидное тело → 422, не 500.
3. Insomnia: один запрос, который должен упасть, один — пройти.

**В группу:** ссылка на сохранённый regex101 (или скрин тестов) + скрин 422.

**Проверка:** вы не парсите HTML. Есть хотя бы один сознательно отвергнутый ввод.`,
    links: [
      { label: 're в Python', href: 'https://docs.python.org/3/library/re.html' },
      { label: 'Песочница regex101', href: 'https://regex101.com/' },
      {
        label: 'MDN: регулярные выражения (диалект JS)',
        href: 'https://developer.mozilla.org/ru/docs/Web/JavaScript/Guide/Regular_expressions',
      },
    ],
    diagram: `flowchart LR
  Input[Ввод] --> Re[re_pattern]
  Re -->|ok| API[Принять]
  Re -->|fail| Err[422]`,
    cheatsheet: `### Пример

\`\`\`
^TCK-\\d+$
\`\`\`

- Flavor на regex101: **Python**
- В Pydantic: \`pattern=...\` → невалидное → **422**

### Уместно / вредно

| Уместно | Вредно |
|---------|--------|
| Код \`TCK-123\` | Парсинг HTML |
| Грубый e-mail | «Телефон всех стран» |
| Кусок из лога | Замена параметризованного SQL |

### Не делать

- Комбайн на 80 групп
- Источник правды только на клиенте

### Готово, если…

- [ ] 5+ / 3− примера на regex101
- [ ] Скрин 422 из Insomnia
- [ ] HTML не парсите regex’ом`,
  },
  {
    slug: 's01e10-react',
    episode: 'S01E10',
    title: 'React: страница списка и вызов API',
    shortTitle: 'React',
    rubricId: 'frontend',
    order: 10,
    theory: `S01E10 · React · список и fetch

UI — последний слой в этой десятке, не первый. Вы уже знаете контракт (\`GET /tickets\`) и видели JSON в Insomnia. Страница только рисует то, что API уже умеет.

Минимум Vite + React:

- Страница «Список заявок»: запрос к API при загрузке, вывод \`title\` и \`status\`.
- Один \`baseURL\` (лучше переменная \`VITE_API_URL\`), не размазанные по компонентам localhost.
- Ошибка сети — текст на странице, не пустой экран.
- Пока без дизайн-системы, без Redux, без авторизации (JWT — позже).

CORS. Если UI на \`:5173\`, а API на \`:8000\`, браузер заблокирует запрос, пока FastAPI не отдаст CORS. Это не баг React. Либо прокси Vite на \`/api\`, либо настройки CORS на бэке — выберите одно и зафиксируйте в README.

Зачем это в живом сервисе. UI CopyParse ходит в \`/api\` так же: один клиент, не «каждый экран сам знает хост core».

Граница. Не верстайте админку и не тащите компонентную библиотеку «как на проде». Список из API важнее кнопок.

Следующий выпуск: JWT — логин без самодельной криптографии.`,
    lab: `**40 минут.**

1. \`npm create vite@latest\` → React. Страница списка.
2. \`fetch\` (или тонкая обёртка) на \`GET /tickets\`. Отобразите 3 поля.
3. README: как запустить UI и API, какая переменная URL, как обойден CORS.
4. Скрин: Insomnia показывает те же заявки, что и страница.

**В группу:** скрин UI + ссылка на PR.

**Проверка:** остановка API даёт видимую ошибку в UI. Нет захардкоженного списка «на время».`,
    links: [
      {
        label: 'React: списки',
        href: 'https://react.dev/learn/rendering-lists',
      },
      {
        label: 'Эффекты и загрузка данных',
        href: 'https://react.dev/learn/synchronizing-with-effects',
      },
      { label: 'Vite, старт', href: 'https://vite.dev/guide/' },
      {
        label: 'CORS в FastAPI',
        href: 'https://fastapi.tiangolo.com/tutorial/cors/',
      },
    ],
    diagram: `flowchart LR
  Page[Страница_списка] --> Fetch[fetch]
  Fetch --> API["GET /tickets"]
  API --> PG[(PostgreSQL)]
  Fetch --> View[Таблица_на_экране]`,
    cheatsheet: `### Минимум страницы

\`\`\`ts
const base = import.meta.env.VITE_API_URL

useEffect(() => {
  fetch(\`\${base}/tickets\`)
    .then((r) => {
      if (!r.ok) throw new Error(String(r.status))
      return r.json()
    })
    .then(setTickets)
    .catch(setError)
}, [])
\`\`\`

### CORS

UI \`:5173\` + API \`:8000\` → нужен CORS на FastAPI **или** proxy Vite. Зафиксируйте в README.

### Не делать

- Хардкод списка «пока без API»
- Redux / UI-kit / JWT в этом выпуске
- Пустой экран при ошибке сети

### Готово, если…

- [ ] Список = то же, что Insomnia
- [ ] Стоп API → ошибка на экране
- [ ] Один \`VITE_API_URL\``,
  },
]
