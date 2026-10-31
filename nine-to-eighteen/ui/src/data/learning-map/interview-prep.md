# собеседование

Карта подготовки: темы одного выпуска внутри статьи. Стрелка входит в статью из каждого пререквизита.

## Разработка

### Слои сервиса {learn:s01e01-sloi profiles:developer,analyst,devops,tester,product_owner}
- Карта системы {profiles:developer,analyst,devops,product_owner}
### Карта первого приложения {learn:b01-karta prereq:s01e01-sloi profiles:developer,analyst,tester,devops}
- Python для API {profiles:developer}
- FastAPI и health {profiles:developer,tester,devops}
### FastAPI контракт {learn:s01e05-fastapi prereq:b01-karta profiles:developer,analyst,tester}
### Notes API {learn:b05-api-check prereq:b01-karta profiles:developer}
- React список {profiles:developer}
- React форма {profiles:developer}
### React UI {learn:s01e09-regex prereq:py-strings-ops-io profiles:developer}
### Склейка стенда {learn:b10-docker prereq:b05-api-check profiles:developer,devops}

## Аналитика и продукт

### Системный анализ {learn:s01e03-git prereq:s01e01-sloi profiles:analyst,product_owner,developer}

## Данные

### PostgreSQL основы {learn:s01e07-postgres prereq:s01e01-sloi profiles:developer,analyst,devops,tester}
- SQL JOIN и агрегаты {profiles:developer,analyst,tester}

## Инструменты

### Git {learn:s01e03-git prereq:s01e01-sloi profiles:developer,devops,tester,analyst}
### Git ветки и PR {learn:b05-api-check prereq:b01-karta profiles:developer,devops,tester}
- Проверка API (curl) {profiles:tester,developer,devops}
### Git с нуля (сезон B) {learn:b01-karta prereq:s01e01-sloi profiles:developer}
### Regex {learn:s01e09-regex prereq:py-strings-ops-io profiles:developer,tester,analyst}
### Проверка API (Insomnia) {learn:s01e05-fastapi prereq:b01-karta profiles:tester,developer,analyst}

## DevOps

### Junior
#### Docker образ {learn:b10-docker prereq:b05-api-check profiles:devops,developer}
- Docker Compose {profiles:devops,developer}
### Middle
#### Процесс Linux {learn:ops-linux-process prereq:b10-docker profiles:devops,developer,tester}
- Объекты Kubernetes {profiles:devops,developer}
- Пайплайн {profiles:devops,developer,tester}

## Безопасность

### Кто вы и что можно {learn:sec-authn-authz prereq:net-dns-http profiles:developer,devops}
- JWT и хранение {profiles:developer}
- Инъекции {profiles:developer}
- Секреты {profiles:developer,devops}

## Soft skills

### Каркас STAR {learn:beh-star profiles:developer,analyst,devops,tester,product_owner}
- Конфликт {profiles:developer,analyst,devops,tester,product_owner}
- Провал {profiles:developer,analyst,devops,tester,product_owner}
- Набор историй {profiles:developer,analyst,devops,tester,product_owner}

## Python

### Junior
#### Python на собесе {learn:py-intro-python profiles:developer}
- Коллекции {profiles:developer}
#### Строки и I/O {learn:py-strings-ops-io prereq:py-intro-python profiles:developer}
- Функции {profiles:developer}
- Модули и venv {profiles:developer}
#### ООП база {learn:py-oop-basics prereq:py-strings-ops-io profiles:developer}
- Исключения {profiles:developer}
- Stdlib на собесе {profiles:developer}
### Middle
#### Итераторы {learn:py-iterators-generators prereq:py-oop-basics profiles:developer}
- Декораторы {profiles:developer}
- FP и itertools {profiles:developer}
#### MRO и dunder {learn:py-oop-advanced-mro prereq:py-oop-basics,py-iterators-generators profiles:developer}
- PEP 8 и typing {profiles:developer}
- Asyncio {profiles:developer}
### Senior
#### GIL и GC {learn:py-threading-gil-gc prereq:py-oop-advanced-mro profiles:developer}
- Тесты и pdb {profiles:developer}
- Метаклассы {profiles:developer}
#### Perf и PyPy {learn:py-perf-packaging-alt-runtimes prereq:py-threading-gil-gc profiles:developer}
- Веб-фреймворки {profiles:developer}
- БД и Memcached {profiles:developer}
#### Concurrency и I/O в проде {learn:py-concurrency-io-patterns prereq:py-perf-packaging-alt-runtimes,ops-linux-process profiles:developer}
- DRY и границы {profiles:developer}
- Трюки собеса {profiles:developer}
- Карта собеса Python {profiles:developer}

## SQL

### Junior
#### SQL на собесе {learn:sql-ddl-dml-dcl profiles:developer,analyst,tester}
- Ключи и constraints {profiles:developer,analyst,tester}
#### DELETE, TRUNCATE и DROP {learn:sql-delete-truncate-drop prereq:sql-ddl-dml-dcl profiles:developer,analyst,tester}
- JOIN типы {profiles:developer,analyst,tester}
#### CHAR vs VARCHAR и семантика {learn:sql-types-null prereq:sql-ddl-dml-dcl profiles:developer,analyst,tester}
- Индексы basics {profiles:developer,analyst,tester}
### Middle
#### Нормализация 1–3НФ {learn:sql-normalization prereq:sql-delete-truncate-drop,sql-types-null profiles:developer,analyst,tester}
- ACID транзакции {profiles:developer,analyst,tester}
#### Триггеры и операторы SQL {learn:sql-triggers-operators prereq:sql-delete-truncate-drop,sql-types-null profiles:developer,analyst,tester}
- Подзапросы {profiles:developer,analyst,tester}
#### Текущая дата и способы {learn:sql-agg-dates-count prereq:sql-triggers-operators profiles:developer,analyst,tester}
- Сводная лаба SQL {profiles:developer,analyst,tester}
### Senior
#### CTE и оконные функции {learn:sql-cte-window prereq:sql-agg-dates-count profiles:developer,analyst,tester}
- EXPLAIN, индексы и N+1 {profiles:developer,analyst,tester}
#### Drill SQL {learn:sql-interview-drill prereq:sql-cte-window,sql-normalization profiles:developer,analyst,tester}
- Чеклист SQL {profiles:developer,analyst,tester}

## Java

### Junior
#### Java SE и JVM на собесе {learn:jv-se-jvm profiles:developer}
- ООП vs Python {profiles:developer}
#### Shell и процесс {learn:jv-shell-process prereq:jv-se-jvm,sql-ddl-dml-dcl profiles:developer}
- JDBC основы {profiles:developer}
- Пул соединений и транзакции {profiles:developer}
### Middle
#### Понятия ORM {learn:jv-orm-concepts prereq:jv-shell-process,sql-delete-truncate-drop profiles:developer}
- JPA/Hibernate обзор и N+1 {profiles:developer}
#### Очереди JMS {learn:jv-jms prereq:jv-shell-process,sa-sync-async-queues profiles:developer}
- Адаптер и ESB со стороны {profiles:developer}
- SOAP-клиент в Java {profiles:developer}
### Senior
#### JavaScript как клей рядом с {learn:jv-js-glue prereq:jv-jms,js-types-coerce,b10-docker profiles:developer}
- Хостинг JVM {profiles:developer}
- Лаба: JDBC + JMS надёжный {profiles:developer}
#### ADR: шина vs брокер {learn:jv-adr-bus-vs-broker prereq:jv-js-glue,jv-orm-concepts,jc-collections-hashmap profiles:developer}
- Drill Java {profiles:developer}
- Чеклист Java {profiles:developer}

## JavaScript

### Junior
#### Типы и приведение в {learn:js-types-coerce profiles:developer,tester}
- Функции и this {profiles:developer,tester}
- Promise, async/await и fetch {profiles:developer,tester}
### Middle
#### DOM и события {learn:js-dom-events prereq:js-types-coerce profiles:developer,tester}
- JSON и XML в браузере {profiles:developer,tester}
- Чеклист JS {profiles:developer,tester}

## QA

### Junior
#### Тестирование на собесе {learn:qa-intro-testing profiles:tester}
- Типы и уровни тестирования {profiles:tester}
#### Тест-дизайн {learn:qa-test-design prereq:qa-intro-testing profiles:tester}
- Баги и отчёты {profiles:tester}
#### Документы QA {learn:qa-docs-plan-cases prereq:qa-test-design profiles:tester}
- Web и HTTP для QA {profiles:tester}
#### SQL и БД для QA {learn:qa-sql-db-basics prereq:qa-test-design profiles:tester}
- Практика junior QA {profiles:tester}
#### AQA принципы {learn:qa-aqa-principles prereq:qa-docs-plan-cases,py-oop-basics profiles:tester}
- Selenium WebDriver на Python {profiles:tester}
#### pytest, Git и CI для {learn:qa-pytest-ci-git prereq:qa-aqa-principles profiles:tester}
- Мобильное тестирование и {profiles:tester}
### Middle
#### Процесс QA middle: роли, {learn:qa-middle-process prereq:qa-docs-plan-cases profiles:tester}
- Продвинутый тест-дизайн: {profiles:tester}
#### API-автоматизация, контракты {learn:qa-api-contract-perf prereq:qa-pytest-ci-git profiles:tester}
- Agile для тестировщика: {profiles:tester}
#### Инфраструктура QA: VM, {learn:qa-infra-linux-containers prereq:qa-pytest-ci-git,qa-sql-db-basics,b10-docker profiles:tester}
- Middle web, mobile и SQL: {profiles:tester}
### Senior
#### Стратегия тестирования, {learn:qa-strategy-metrics prereq:qa-middle-process,qa-api-contract-perf profiles:tester}
- Shift-left и ROI {profiles:tester}
#### Senior security и {learn:qa-security-perf-senior prereq:qa-strategy-metrics,qa-infra-linux-containers,sec-authn-authz profiles:tester}
- Лидерство QA: конфликты, {profiles:tester}
#### Senior practice drill: баги, {learn:qa-senior-practice-drill prereq:qa-security-perf-senior profiles:tester}
- Capstone QA: чеклист {profiles:tester}

## Системный анализ

### Junior
#### Требования FR/NFR {learn:sa-requirements-basics profiles:analyst}
- User story, USM и use case {profiles:analyst}
#### ГОСТ и SRS {learn:sa-gost-srs-artifacts prereq:sa-requirements-basics profiles:analyst}
- BPMN и UML {profiles:analyst}
#### БД основы {learn:sa-db-basics profiles:analyst}
- SQL основы {profiles:analyst}
#### REST основы {learn:sa-rest-basics prereq:sa-requirements-basics,net-dns-http profiles:analyst}
- Scrum и Kanban {profiles:analyst}
### Middle
#### БД Advanced {learn:sa-db-advanced prereq:sa-db-basics profiles:analyst}
#### Sync/Async и очереди {learn:sa-sync-async-queues prereq:sa-rest-basics profiles:analyst}
- REST продвинутый {profiles:analyst}
#### SOAP и XML {learn:sa-soap-xml prereq:sa-sync-async-queues profiles:analyst}
- ESB и интеграции {profiles:analyst}
#### Архитектурные стили {learn:sa-architecture-styles prereq:sa-soap-xml,sa-db-advanced profiles:analyst}
- Оркестрация, CAP, API {profiles:analyst}
### Senior
#### HTTP/S, аутентификация и {learn:sa-http-security-basics prereq:sa-rest-basics,sa-gost-srs-artifacts profiles:analyst}
- Senior craft постановки {profiles:analyst}
#### Моделирующий воркшоп {learn:sa-modeling-workshop prereq:sa-gost-srs-artifacts,sa-db-basics,sa-soap-xml profiles:analyst}
- Проектирование интеграций {profiles:analyst}
#### Архитектурные решения {learn:sa-architecture-decisions prereq:sa-architecture-styles profiles:analyst}
- Оценка и поставка {profiles:analyst}
#### Уровни профессии СА {learn:sa-profession-levels prereq:sa-architecture-decisions,sa-modeling-workshop,sa-http-security-basics profiles:analyst}
- Drill аналитика {profiles:analyst}
- Capstone СА {profiles:analyst}

## Redis

### Junior
#### KV модель {learn:rd-kv-model profiles:developer,analyst}
- Типы Redis {profiles:developer,analyst}
### Middle
#### TTL и persistence Redis {learn:rd-ttl-persistence prereq:rd-kv-model profiles:developer,analyst}
- Паттерн cache-aside в Redis {profiles:developer,analyst}
- Cache stampede и блокировки {profiles:developer,analyst}
### Senior
#### Redis pub/sub vs брокер {learn:rd-pubsub-vs-queue prereq:rd-ttl-persistence profiles:developer,analyst}
- Eviction, Sentinel и Cluster {profiles:developer,analyst}
- Чеклист Redis {profiles:developer,analyst}

## Продукт

### Junior
#### Роль PM {learn:pm-product-management profiles:product_owner}
- Приоритизация {profiles:product_owner}
#### Путь клиента {learn:pm-cjm prereq:pm-product-management profiles:product_owner}
- Agile глазами Product Owner {profiles:product_owner}
### Middle
#### Стратегия продукта {learn:pm-product-strategy prereq:pm-cjm profiles:product_owner}
- Дорожная карта {profiles:product_owner}
#### Цели OKR {learn:pm-okr prereq:pm-product-strategy profiles:product_owner}
- Стейкхолдеры и RACI {profiles:product_owner}
### Senior
#### P&L и unit-экономика на {learn:pm-pnl-unit-econ prereq:pm-metrics profiles:product_owner}
- Портфель продуктов и ставок {profiles:product_owner}
#### Drill продукта {learn:pm-interview-drill prereq:pm-pnl-unit-econ,pm-discovery,pm-acceptance profiles:product_owner}
- Чеклист продукта {profiles:product_owner}

## Алгоритмы

### Сложность {learn:algo-complexity profiles:developer}
- Массив и хеш {profiles:developer}
- Два указателя {profiles:developer}
- Стек и очередь {profiles:developer}
- Деревья и графы {profiles:developer}
- Разбор задачи {profiles:developer}

## Проектирование

### Один сервис {learn:sd-one-service prereq:s01e01-sloi,net-dns-http profiles:developer}
- Кэш и очередь {profiles:developer}
- Выбор хранилища {profiles:developer}
- Что падает первым {profiles:developer}

## Postgres

### Изоляция {learn:pg-isolation prereq:sql-normalization profiles:developer,analyst}
- MVCC и блокировки {profiles:developer,analyst}
- Индекс молчит {profiles:developer,analyst}
- Разбор Postgres {profiles:developer,analyst}

## Сети

### DNS и HTTP {learn:net-dns-http profiles:developer,devops,tester}
- TCP и UDP {profiles:developer,devops}
- TLS {profiles:developer,devops,tester}
- Разбор сетей {profiles:developer,devops,tester}

## Наблюдаемость

### Логи {learn:obs-logs profiles:developer,devops}
- Метрики и трейсы {profiles:developer,devops}
- Инцидент {profiles:developer,devops}

## Java Core

### HashMap {learn:jc-collections-hashmap prereq:jv-se-jvm profiles:developer}
- Потоки {profiles:developer}
- Сборщик мусора {profiles:developer}
- Spring: бин и транзакция {profiles:developer}

## Фронтенд

### Цикл событий {learn:fe-event-loop prereq:js-types-coerce profiles:developer}
- Замыкание и прототип {profiles:developer}
- Состояние React {profiles:developer}
- TypeScript {profiles:developer}
