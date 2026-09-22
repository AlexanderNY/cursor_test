#!/usr/bin/env python3
"""Append Java / Product / JS Learn series; run after generate_cv_learn_series helpers."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "core" / "scripts" / "generate_cv_learn_series.py"
_SPEC = importlib.util.spec_from_file_location("gen_cv", HELPER)
_mod = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_mod)
article = _mod.article
write_series = _mod.write_series
build_redis = _mod.build_redis
RD_SERIES = _mod.RD_SERIES
RD_README = _mod.RD_README


def compact(
    slug, title, short, ep, rubric, order, date, profiles, level, tags, duration,
    excerpt, prereq, intro, s1, s2, s3, lab_goal, steps, group, done,
    diag_title, diag, q1, q2, q3, cheat, a1, a2, a3, summary, links, nxt=None,
    seo_title=None, seo_desc=None,
):
    return article(
        slug=slug,
        title=title,
        short=short,
        episode=ep,
        rubric=rubric,
        order=order,
        published=date,
        profiles=profiles,
        level=level,
        tags=tags + ["собеседование"],
        duration=duration,
        excerpt=excerpt,
        prerequisites=prereq,
        seo_title=seo_title or f"{short} — {level}",
        seo_desc=seo_desc or excerpt,
        seo_kw=tags[:5] + ["собеседование"],
        intro=intro,
        sections=[("Основы", s1), ("Практика", s2), ("На собесе", s3)],
        lab_goal=lab_goal,
        lab_steps=steps,
        lab_group=group,
        lab_done=done,
        diagram_title=diag_title,
        diagram=diag,
        quiz=[q1, q2, q3],
        cheat_html=cheat,
        anki=[a1, a2, a3],
        summary=summary,
        links=links,
        next_link=nxt,
    )


JV_SERIES = """# Серия Java / enterprise Learn

Карта **16 выпусков**. Файлы: `jv-*.md`.

| Поле | Значение |
|------|----------|
| `episode` | `JV01` … `JV16` |
| `order` | `801` … `816` |
| `profiles` | `[developer]` |
| Seed | `import_java_learn_series.py` |

## Junior JV01–JV06

| Ep | slug | rubric |
|----|------|--------|
| JV01 | `jv-se-jvm` | tools |
| JV02 | `jv-oop-vs-python` | tools |
| JV03 | `jv-shell-process` | tools |
| JV04 | `jv-jdbc-basics` | data |
| JV05 | `jv-jdbc-pool-tx` | data |
| JV06 | `jv-orm-concepts` | data |

## Middle JV07–JV12

| Ep | slug | rubric |
|----|------|--------|
| JV07 | `jv-jpa-nplus1` | data |
| JV08 | `jv-jms` | api |
| JV09 | `jv-esb-adapter` | architecture |
| JV10 | `jv-soap-client` | api |
| JV11 | `jv-js-glue` | frontend |
| JV12 | `jv-jvm-hosting` | tools |

## Senior JV13–JV16

| Ep | slug | rubric |
|----|------|--------|
| JV13 | `jv-integration-lab` | architecture |
| JV14 | `jv-adr-bus-vs-broker` | architecture |
| JV15 | `jv-interview-drill` | tools |
| JV16 | `jv-capstone` | architecture |
"""

PM_SERIES = """# Серия Product Learn

Карта **12 выпусков**. Файлы: `pm-*.md`. Рубрика `product`.

| `episode` | `PM01` … `PM12` |
| `order` | `901` … `912` |
| `profiles` | `[product_owner]` |
| Seed | `import_product_learn_series.py` |

| Ep | slug |
|----|------|
| PM01 | `pm-product-management` |
| PM02 | `pm-prioritization` |
| PM03 | `pm-cjm` |
| PM04 | `pm-agile-po` |
| PM05 | `pm-product-strategy` |
| PM06 | `pm-roadmapping` |
| PM07 | `pm-okr` |
| PM08 | `pm-stakeholders` |
| PM09 | `pm-pnl-unit-econ` |
| PM10 | `pm-portfolio` |
| PM11 | `pm-interview-drill` |
| PM12 | `pm-capstone` |
"""

JS_SERIES = """# Серия JavaScript Learn (язык)

Карта **6 выпусков**. React — сезон B, не здесь.

| `episode` | `JS01` … `JS06` |
| `order` | `850` … `855` |
| `profiles` | `[developer, tester]` |
| `rubric` | `frontend` |
| Seed | `import_js_learn_series.py` |

| Ep | slug |
|----|------|
| JS01 | `js-types-coerce` |
| JS02 | `js-functions-this` |
| JS03 | `js-async-fetch` |
| JS04 | `js-dom-events` |
| JS05 | `js-json-xml` |
| JS06 | `js-capstone` |
"""


def build_java() -> dict[str, str]:
    D = "2027-06-{:02d}T10:00:00+03:00"
    P = ["developer"]
    files = {}
    specs = [
        ("jv01-se-jvm.md", "jv-se-jvm", "Java SE и JVM на собесе", "Java SE JVM", "JV01", "tools", 801, D.format(1), "junior",
         ["java", "jvm"], 30, "JDK, JRE, JVM, classpath и примитивы vs ссылки.", [],
         "Первый выпуск трека Java: что исполняет байткод и чем JDK отличается от JRE.",
         "JDK включает компилятор и инструменты; JRE — среда запуска; JVM исполняет bytecode.",
         "Classpath указывает, где искать классы. Примитивы (int) хранят значение; ссылочные типы — ссылку на объект в heap.",
         "На собесе: «Java компилируется в bytecode, не в нативный код напрямую (если не считать JIT)».",
         "Объяснить цепочку .java → javac → .class → JVM.",
         ["Напишите одну фразу JDK vs JRE.", "Объясните classpath.", "Приведите пример примитива и ссылочного типа.", "Что делает JIT кратко?", "Сравните с интерпретатором Python (см. PY01)."],
         "партнёр путает JDK и JVM — поправьте.",
         ["Отличаете JDK/JRE/JVM", "Знаете classpath", "Примитив vs reference"],
         "Компиляция", "flowchart LR\n  SRC[.java] --> JAVAC --> CLS[.class] --> JVM",
         ("JDK vs JRE?", "JDK = tools+compiler; JRE = runtime", "JVM входит в оба как исполнитель."),
         ("Где ищутся классы?", "classpath / module path", "Ошибка ClassNotFound часто от неверного пути."),
         ("int и Integer?", "примитив vs объект-обёртка", "Autoboxing связывает их."),
         "<h3>Стек</h3><ul><li>JDK → JRE → JVM</li><li>bytecode + JIT</li></ul>",
         ("JDK", "development kit с javac"), ("JVM", "исполняет bytecode"), ("classpath", "поиск классов"),
         ["Bytecode, не «чистый интерпретатор»", "Classpath — частая боль", "Связка с PY01 уместна"],
         [("PY01 Intro Python", "/game/learn/py-intro-python")], ("ООП Java vs Python", "/game/learn/jv-oop-vs-python")),
        ("jv02-oop-vs-python.md", "jv-oop-vs-python", "ООП Java vs Python", "ООП vs Python", "JV02", "tools", 802, D.format(3), "junior",
         ["java", "oop"], 28, "class, interface, static; мост к Python ООП.", ["jv-se-jvm"],
         "Сравнение моделей ООП помогает разработчикам с Python-трека.",
         "В Java всё (почти) в классах; interface — контракт; class может реализовать несколько interface.",
         "static принадлежит типу, не экземпляру. См. [py-oop-basics](/game/learn/py-oop-basics).",
         "На собесе: не спорьте «что лучше» — покажите, где семантика совпадает и где нет (duck typing vs interface).",
         "Сопоставить interface Java и Protocol/ABC Python.",
         ["Напишите мини-interface Drawable.", "Реализуйте class Circle.", "Где static уместен?", "Чем interface отличается от abstract class (кратко)?", "Ссылка на PY06."],
         "один пишет Java-формулировку, второй — Python-аналог.",
         ["interface vs class", "static понятен", "Мост к PY06"],
         "Контракт", "flowchart TB\n  I[interface] --> C1[class A]\n  I --> C2[class B]",
         ("interface это?", "контракт без (полной) реализации", "default-методы с Java 8 — исключение."),
         ("static метод", "принадлежит классу", "Вызов через ИмяКласса.method."),
         ("Связь с Python", "ABC/Protocol ≈ контракт", "Duck typing слабее формальных интерфейсов."),
         "<h3>Мост</h3><ul><li>interface ↔ Protocol</li><li>class ↔ class</li></ul>",
         ("interface", "контракт"), ("static", "на типе"), ("PY06", "база ООП Python"),
         ["Контракты явны в Java", "Не демонизируйте Python", "Ссылки кросс-серий"],
         [("PY06 ООП", "/game/learn/py-oop-basics")], ("Shell и процесс", "/game/learn/jv-shell-process")),
        ("jv03-shell-process.md", "jv-shell-process", "Shell и запуск JVM-процесса", "Shell JVM", "JV03", "tools", 803, D.format(5), "junior",
         ["java", "shell", "linux"], 25, "env, PID, скрипт запуска jar; ссылка на QA17.", ["jv-oop-vs-python"],
         "Запуск сервиса — часть работы Java-разработчика; глубокий Linux — в QA17.",
         "Процесс JVM: `java -jar app.jar`. Переменные окружения (`JAVA_OPTS`, `DB_URL`) конфигурируют поведение.",
         "Скрипт: проверка Java version, выставление heap `-Xmx`, логирование PID. См. [qa-infra-linux-containers](/game/learn/qa-infra-linux-containers).",
         "На собесе: уметь прочитать `ps`/`top` и логи — достаточно junior/middle без роли админа.",
         "Написать bash-обёртку запуска jar.",
         ["echo $JAVA_HOME.", "java -version.", "Скрипт start.sh с -Xmx256m.", "Куда смотреть логи (stdout/файл)?", "Ссылка на QA17."],
         "партнёр ломает JAVA_HOME — вы диагностируете.",
         ["Запускаете jar", "Знаете JAVA_OPTS", "Ссылаетесь на QA17"],
         "Старт", "flowchart LR\n  SH[start.sh] --> JAVA[java -jar]\n  JAVA --> APP[App]",
         ("Как задать heap?", "-Xmx / -Xms", "Часто через JAVA_OPTS."),
         ("Где глубокий Linux?", "QA17 infra", "Не дублируем курс администрирования."),
         ("Зачем PID?", "диагностика процесса, kill, метрики", "ps/top/pidstat."),
         "<h3>Запуск</h3><pre><code>java -Xmx512m -jar app.jar</code></pre>",
         ("-Xmx", "лимит heap"), ("JAVA_OPTS", "опции JVM из env"), ("QA17", "Linux/Docker для QA"),
         ["Скрипт тонкий", "Env > хардкод", "Кросс на QA17"],
         [("QA17 Linux", "/game/learn/qa-infra-linux-containers")], ("JDBC basics", "/game/learn/jv-jdbc-basics")),
        ("jv04-jdbc-basics.md", "jv-jdbc-basics", "JDBC основы — Driver, Connection, PreparedStatement", "JDBC basics", "JV04", "data", 804, D.format(7), "junior",
         ["java", "jdbc", "sql"], 30, "Подключение к БД из Java без ORM.", ["jv-shell-process"],
         "JDBC — стандартный API доступа к реляционным БД из Java.",
         "Driver регистрирует протокол. Connection — сессия с БД. Statement vs PreparedStatement: второй с плейсхолдерами защищает от SQL injection.",
         "Типичный поток: getConnection → prepareStatement → setXxx → executeQuery/Update → close (try-with-resources).",
         "На собесе напишите псевдокод SELECT по id с `?`.",
         "Псевдокод безопасного SELECT.",
         ["Откройте Connection (псевдокод).", "PreparedStatement с WHERE id=?.", "Почему не Statement + конкатенация?", "Закрытие ресурсов.", "Связь с SQL01."],
         "один пишет уязвимый SQL, второй чинит PreparedStatement.",
         ["Driver/Connection", "PreparedStatement", "try-with-resources"],
         "JDBC поток", "sequenceDiagram\n  App->>Driver: connect\n  App->>DB: PreparedStatement\n  DB-->>App: ResultSet",
         ("Зачем PreparedStatement?", "плейсхолдеры и план/безопасность", "Защита от injection."),
         ("Connection это?", "сессия с СУБД", "Держать пул на middle — JV05."),
         ("SQL injection как лечить?", "параметры, не конкатенация", "Аналог placeholders в Python."),
         "<h3>Каркас</h3><pre><code>try (Connection c = ...;\n     PreparedStatement ps = c.prepareStatement(sql)) {\n  ps.setLong(1, id);\n}</code></pre>",
         ("PreparedStatement", "SQL с ?"), ("ResultSet", "курсор результата"), ("injection", "лечить параметрами"),
         ["JDBC = фундамент ORM", "Параметры обязательны", "Ресурсы закрывать"],
         [("SQL01", "/game/learn/sql-ddl-dml-dcl")], ("Пул и транзакции", "/game/learn/jv-jdbc-pool-tx")),
        ("jv05-jdbc-pool-tx.md", "jv-jdbc-pool-tx", "Пул соединений и транзакции JDBC", "JDBC pool tx", "JV05", "data", 805, D.format(9), "junior",
         ["java", "jdbc", "transactions"], 30, "Connection pool и autocommit; связь с SQL ACID.", ["jv-jdbc-basics"],
         "Открывать Connection на каждый запрос без пула — дорого. Транзакции связывают несколько DML.",
         "Пул (HikariCP и др.) держит готовые соединения. autocommit=true — каждый statement сам по себе; false — явный commit/rollback.",
         "См. [sql-acid-transactions](/game/learn/sql-acid-transactions).",
         "На собесе: «пул ограничивает число соединений к БД и снижает latency connect».",
         "Описать границы транзакции перевода денег.",
         ["Зачем пул?", "autocommit false — когда?", "ROLLBACK при ошибке.", "Риск утечки соединений.", "Ссылка SQL08."],
         "разберите deadlock на двух обновлениях.",
         ["Пул понятен", "commit/rollback", "Связь с ACID"],
         "Пул", "flowchart LR\n  App --> Pool\n  Pool --> C1\n  Pool --> C2\n  Pool --> DB[(DB)]",
         ("Зачем pool?", "переиспользование соединений", "Меньше handshake/нагрузки."),
         ("autocommit false", "явные границы транзакции", "Несколько DML атомарно."),
         ("Утечка Connection", "не вернули в пул / не закрыли", "Исчерпание пула."),
         "<h3>Tx</h3><pre><code>c.setAutoCommit(false);\n// DML\nc.commit();</code></pre>",
         ("pool", "кэш соединений"), ("rollback", "откат tx"), ("SQL08", "ACID канон"),
         ["Пул = must-have", "Tx на уровне приложения", "Читайте SQL08"],
         [("SQL08 ACID", "/game/learn/sql-acid-transactions")], ("ORM concepts", "/game/learn/jv-orm-concepts")),
        ("jv06-orm-concepts.md", "jv-orm-concepts", "Понятия ORM — identity map и dirty checking", "ORM concepts", "JV06", "data", 806, D.format(11), "junior",
         ["java", "orm"], 30, "Зачем ORM и чем отличается от raw JDBC.", ["jv-jdbc-pool-tx"],
         "ORM отображает таблицы на объекты. Важно понимать цены абстракции.",
         "Identity map: один объект на один ключ в сессии. Dirty checking: изменения полей сами попадают в UPDATE.",
         "Unit of work откладывает SQL до flush/commit. Raw SQL нужен для сложных отчётов и отладки N+1.",
         "См. Python-угол: [py-web-flask-django](/game/learn/py-web-flask-django), [py-db-cache-memcached](/game/learn/py-db-cache-memcached).",
         "Сравнить JDBC INSERT и ORM persist.",
         ["Определите identity map.", "Что такое dirty checking?", "Когда raw SQL лучше?", "Риск «магии» ORM.", "Ссылка PY19/PY20."],
         "партнёр хвалит только ORM — вы добавляете контраргумент.",
         ["Три понятия ORM", "Граница raw SQL", "Кросс на Python"],
         "Сессия ORM", "flowchart TB\n  App --> Session\n  Session --> IdentityMap\n  Session --> DB",
         ("identity map", "один объект на PK в сессии", "Избегает дублей экземпляров."),
         ("dirty checking", "отслеживание изменённых полей", "UPDATE без явного SQL."),
         ("Когда JDBC?", "сложный SQL, перф, отладка", "ORM не запрещает native query."),
         "<h3>ORM</h3><ul><li>identity map</li><li>dirty checking</li><li>unit of work</li></ul>",
         ("identity map", "уникальность объекта в сессии"), ("dirty checking", "авто-UPDATE"), ("unit of work", "пакет изменений"),
         ["ORM ускоряет CRUD", "Понимайте SQL под ним", "N+1 — следующий выпуск"],
         [("PY19", "/game/learn/py-web-flask-django"), ("PY20", "/game/learn/py-db-cache-memcached")],
         ("JPA и N+1", "/game/learn/jv-jpa-nplus1")),
        ("jv07-jpa-nplus1.md", "jv-jpa-nplus1", "JPA/Hibernate обзор и N+1", "JPA N+1", "JV07", "data", 807, D.format(13), "middle",
         ["java", "jpa", "n+1"], 35, "Entity, lazy loading и классика N+1.", ["jv-orm-concepts"],
         "JPA — спецификация; Hibernate — популярная реализация.",
         "Entity связан с таблицей. FetchType.LAZY откладывает загрузку связей. N+1: 1 запрос список + N запросов связей в цикле.",
         "Лечение: join fetch, entity graph, batch size. См. [sql-performance-explain](/game/learn/sql-performance-explain).",
         "На собесе нарисуйте N+1 на заказах и клиентах.",
         "Найти N+1 в псевдокоде и предложить join fetch.",
         ["Список Order без join — сколько SQL?", "Что такое lazy?", "Как лечить N+1?", "Связь с SQL14.", "Лог SQL в dev."],
         "один пишет антипаттерн, второй — фикс.",
         ["Видите N+1", "Знаете join fetch", "Ссылка SQL14"],
         "N+1", "flowchart LR\n  Q1[SELECT orders] --> L[loop]\n  L --> Qn[SELECT customer]",
         ("N+1 это?", "1+N запросов в цикле", "Симптом ORM-ленивости."),
         ("Лечение?", "join fetch / batch", "Один наборный SQL."),
         ("LAZY зачем?", "не тащить граф всегда", "Но опасен вне сессии."),
         "<h3>N+1</h3><ul><li>лог SQL</li><li>join fetch</li><li>см. SQL14</li></ul>",
         ("N+1", "цикл запросов"), ("join fetch", "подтянуть связь одним SQL"), ("SQL14", "планы и N+1"),
         ["Логируйте SQL", "LAZY осознанно", "Канон перфа — SQL14"],
         [("SQL14", "/game/learn/sql-performance-explain")], ("JMS", "/game/learn/jv-jms")),
        ("jv08-jms.md", "jv-jms", "JMS — очереди, топики, ack и DLQ", "JMS", "JV08", "api", 808, D.format(15), "middle",
         ["java", "jms", "messaging"], 30, "Java Message Service: queue vs topic, ack, DLQ.", ["jv-jpa-nplus1"],
         "JMS — API Java для брокеров. Не путать с Kafka client API.",
         "Queue — competing consumers (одна задача — один consumer). Topic — pub/sub подписчикам.",
         "Ack подтверждает обработку; DLQ — «мертвые» сообщения после ретраев. См. [sa-sync-async-queues](/game/learn/sa-sync-async-queues) для Kafka/Rabbit как концепций.",
         "На собесе: JMS = контракт Java; брокер может быть ActiveMQ/IBM MQ и т.д.",
         "Выбрать queue или topic для сценария уведомлений.",
         ["Заказ на обработку одним воркером — ?", "Рассылка события многим — ?", "Зачем DLQ?", "Что даёт ack?", "Ссылка SA10."],
         "сравните с Redis pub/sub (RD06).",
         ["queue vs topic", "ack/DLQ", "Мост к SA10"],
         "JMS", "flowchart TB\n  P[Producer] --> Q[Queue]\n  Q --> C1\n  P2[Producer] --> T[Topic]\n  T --> S1\n  T --> S2",
         ("Queue семантика?", "одно сообщение — один consumer", "Competing consumers."),
         ("Topic?", "fan-out подписчикам", "Pub/sub модель."),
         ("DLQ?", "хранилище ядовитых сообщений", "После исчерпания retry."),
         "<h3>JMS</h3><ul><li>Queue / Topic</li><li>ack</li><li>DLQ</li></ul>",
         ("queue", "точка-точка"), ("topic", "pub/sub"), ("DLQ", "dead letter"),
         ["JMS ≠ Kafka API", "Гарантии зависят от брокера", "Читайте SA10"],
         [("SA10", "/game/learn/sa-sync-async-queues"), ("RD06", "/game/learn/rd-pubsub-vs-queue")],
         ("ESB adapter", "/game/learn/jv-esb-adapter")),
        ("jv09-esb-adapter.md", "jv-esb-adapter", "Адаптер к ESB со стороны Java", "ESB adapter", "JV09", "architecture", 809, D.format(17), "middle",
         ["java", "esb"], 28, "Как приложение стыкуется с шиной; канон — SA13.", ["jv-jms"],
         "Канон ESB — у аналитиков. Здесь — роль адаптера в коде.",
         "Адаптер преобразует внутреннюю модель сервиса в каноническое сообщение шины и обратно.",
         "Не тащите бизнес-логику в ESB «потому что можно». См. [sa-esb-integrations](/game/learn/sa-esb-integrations).",
         "На собесе: «я реализую producer/consumer контракта, аналитик выбирает ESB vs брокер».",
         "Нарисовать границы app / adapter / ESB.",
         ["Что делает адаптер?", "Где каноническая модель?", "Почему не дублировать SA13?", "Версия контракта.", "Ссылка SA13/SA19."],
         "роль: разработчик vs СА.",
         ["Границы адаптера", "Ссылка SA13", "Версионирование"],
         "Адаптер", "flowchart LR\n  App --> Adapter --> ESB --> Other",
         ("Адаптер зачем?", "маппинг в канон шины", "Изоляция доменной модели."),
         ("Канон теории ESB?", "SA13", "Не копируем курс аналитика."),
         ("Риск богатой шины?", "божественный узел", "См. SA19 integration design."),
         "<h3>Роль</h3><ul><li>код = адаптер</li><li>выбор = SA</li></ul>",
         ("adapter", "маппинг"), ("SA13", "канон ESB"), ("canonical model", "общая схема"),
         ["Тонкий адаптер", "Канон в SA", "Версии контрактов"],
         [("SA13", "/game/learn/sa-esb-integrations"), ("SA19", "/game/learn/sa-integration-design")],
         ("SOAP client", "/game/learn/jv-soap-client")),
        ("jv10-soap-client.md", "jv-soap-client", "SOAP-клиент в Java", "SOAP client", "JV10", "api", 810, D.format(19), "middle",
         ["java", "soap", "xml"], 28, "Клиент SOAP/WSDL; теория — SA12.", ["jv-esb-adapter"],
         "Генерация stub из WSDL и вызов операции — типичный энтерпрайз.",
         "WSDL описывает операции; клиент сериализует XML envelope. Ошибки — Fault.",
         "Канон понятий: [sa-soap-xml](/game/learn/sa-soap-xml). Здесь не повторяем XSD-курс.",
         "На собесе честно: «контракт читаю из WSDL, маплю поля, логирую Fault».",
         "Сопоставить SOAP-операцию с REST-аналогом.",
         ["Что даёт WSDL?", "Где Fault?", "Ссылка SA12.", "Когда оставить SOAP?", "Чем REST проще для нового API?"],
         "сверьте с таблицей SOAP vs REST из SA12.",
         ["WSDL→client", "Fault", "Ссылка SA12"],
         "Вызов", "sequenceDiagram\n  Java->>SOAP: Envelope\n  SOAP-->>Java: Body/Fault",
         ("WSDL?", "описание сервиса", "Генерация клиента."),
         ("Fault?", "ошибка SOAP", "В Body или отдельный элемент."),
         ("Канон теории?", "SA12", "Не дублируем."),
         "<h3>Клиент</h3><ul><li>WSDL</li><li>stub</li><li>Fault</li></ul>",
         ("WSDL", "паспорт сервиса"), ("SA12", "SOAP/XML канон"), ("Fault", "ошибка"),
         ["Stub из контракта", "Логируйте XML осторожно", "Теория в SA"],
         [("SA12", "/game/learn/sa-soap-xml")], ("JS glue", "/game/learn/jv-js-glue")),
        ("jv11-js-glue.md", "jv-js-glue", "JavaScript как клей рядом с Java", "JS glue", "JV11", "frontend", 811, D.format(21), "middle",
         ["java", "javascript"], 25, "Зачем JS в энтерпрайз-стеке рядом с JVM.", ["jv-soap-client"],
         "В резюме архитекторов JS часто как скрипты/клей, не как React-курс.",
         "Сценарии: админки, bookmarklets, Nashorn/GraalJS (легаси), фронт к API.",
         "Языковой трек: серия JS01–JS06. React — B08.",
         "На собесе отделите «знаю JS» от «пишу SPA».",
         "Перечислить 3 сценария JS рядом с Java.",
         ["Скрипт автоматизации UI.", "Вызов REST из fetch.", "Почему не заменять JVM бизнес-логику на JS в legacy без нужды?", "Ссылка JS01.", "Ссылка B08."],
         "границы компетенций фронт/бек.",
         ["Сценарии клея", "Ссылка JS", "Не путать с React-треком"],
         "Клей", "flowchart LR\n  JVM[Java service] --> API\n  API --> JS[JS client]",
         ("JS рядом с Java зачем?", "UI/скрипты/клиент API", "Не обязательно полный frontend stack."),
         ("Куда за языком?", "JS01+", "/game/learn/js-types-coerce"),
         ("React где?", "сезон B", "B08 list."),
         "<h3>Граница</h3><ul><li>клей ≠ SPA-курс</li><li>см. JS series</li></ul>",
         ("glue", "скрипты и клиент"), ("JS01", "типы JS"), ("B08", "React list"),
         ["Честные границы", "Ссылки на JS series", "API first"],
         [("JS01", "/game/learn/js-types-coerce"), ("B08", "/game/learn/b08-react-list")],
         ("JVM hosting", "/game/learn/jv-jvm-hosting")),
        ("jv12-jvm-hosting.md", "jv-jvm-hosting", "Хостинг JVM — systemd и IIS обзор", "JVM hosting", "JV12", "tools", 812, D.format(23), "middle",
         ["java", "linux", "iis"], 25, "Как держат JVM-процесс в проде; без дубля QA17.", ["jv-js-glue"],
         "Сервис должен переживать релогин и ребут.",
         "Linux: unit systemd с Restart=on-failure. Windows/IIS: иногда Java как сервис/за reverse proxy.",
         "Не повторяем курс контейнеров — см. QA17. Здесь — чеклист «процесс жив, порты, логи, health».",
         "На собесе: healthcheck URL + журнал + лимиты памяти.",
         "Составить unit-файл-эскиз.",
         ["ExecStart java -jar.", "Restart политика.", "Куда логи?", "Health endpoint.", "Ссылка QA17."],
         "сравните bare metal vs Docker одной фразой.",
         ["systemd эскиз", "health", "Ссылка QA17"],
         "Сервис", "flowchart TB\n  systemd --> JVM\n  JVM --> Logs\n  JVM --> Health",
         ("Restart=on-failure?", "автоперезапуск при падении", "Не маскирует корневой баг."),
         ("Health зачем?", "оркестратор/балансер знает живость", "Отдельно от «процесс есть»."),
         ("Глубокий Linux?", "QA17", "Не дублируем."),
         "<h3>Хостинг</h3><ul><li>systemd/service</li><li>logs</li><li>health</li></ul>",
         ("systemd", "менеджер сервисов"), ("health", "проверка живости"), ("QA17", "infra deep dive"),
         ["Процесс под супервизором", "Логи и метрики", "Кросс QA17"],
         [("QA17", "/game/learn/qa-infra-linux-containers")], ("Integration lab", "/game/learn/jv-integration-lab")),
        ("jv13-integration-lab.md", "jv-integration-lab", "Лаба: JDBC + JMS учебный контур", "Integration lab", "JV13", "architecture", 813, D.format(25), "senior",
         ["java", "jdbc", "jms", "lab"], 40, "Сквозная учебная интеграция записи в БД и сообщения.", ["jv-jvm-hosting"],
         "Senior-лаба без продакшен-кода: связать JDBC и JMS.",
         "Сценарий: приняли команду → записали статус в БД → опубликовали событие в очередь.",
         "Идемпотентность consumer: повтор сообщения не создаёт дубль строки (unique key / upsert).",
         "Документируйте failure modes: БД ок / брокер упал и наоборот.",
         "Спроектировать happy-path и 2 failure.",
         ["Таблица outbox или sync publish — выбор.", "Ключ идемпотентности.", "Порядок commit vs send.", "DLQ политика.", "Критерии Done лабы."],
         "разберите dual-write проблему.",
         ["Есть схема контура", "Идемпотентность", "Failure modes"],
         "Контур", "sequenceDiagram\n  API->>DB: INSERT\n  API->>Q: publish\n  Q->>Worker: consume\n  Worker->>DB: update",
         ("Dual-write риск?", "БД и брокер расходятся", "Outbox/паттерны согласованности."),
         ("Идемпотентность?", "повтор без дубля эффекта", "Ключ операции."),
         ("Зачем лаба?", "собрать JDBC+JMS в одну историю", "Senior синтез."),
         "<h3>Лаба</h3><ul><li>write</li><li>publish</li><li>consume idempotent</li></ul>",
         ("outbox", "событие из БД"), ("idempotent", "безопасный повтор"), ("DLQ", "ядовитые"),
         ["Сначала схема", "Потом код", "Думайте о повторах"],
         [("JMS", "/game/learn/jv-jms"), ("JDBC", "/game/learn/jv-jdbc-basics")],
         ("ADR bus vs broker", "/game/learn/jv-adr-bus-vs-broker")),
        ("jv14-adr-bus-vs-broker.md", "jv-adr-bus-vs-broker", "ADR: шина vs брокер", "ADR bus/broker", "JV14", "architecture", 814, D.format(27), "senior",
         ["java", "adr", "esb"], 30, "Короткий ADR выбора ESB или брокера.", ["jv-integration-lab"],
         "Формат ADR — канон SA20; здесь пример решения для Java-контура.",
         "Контекст: много легаси XML vs новый event-driven сервис. Варианты: ESB, Kafka, прямой REST.",
         "См. [sa-architecture-decisions](/game/learn/sa-architecture-decisions) и [sa-integration-design](/game/learn/sa-integration-design).",
         "На собесе: структура Context / Options / Decision / Consequences.",
         "Написать ADR на полстраницы.",
         ["Контекст.", "3 опции.", "Решение.", "Последствия + и −.", "Ссылка SA20."],
         "ревью ADR друг друга.",
         ["Структура ADR", "Ссылки SA", "Честные последствия"],
         "ADR", "flowchart TB\n  C[Context] --> O[Options]\n  O --> D[Decision]\n  D --> P[Consequences]",
         ("ADR зачем?", "зафиксировать почему", "Через полгода не гадать."),
         ("Канон формата?", "SA20", "Не изобретаем шаблон."),
         ("ESB всегда?", "нет", "См. антипаттерн SA19."),
         "<h3>ADR</h3><ul><li>Context</li><li>Options</li><li>Decision</li><li>Consequences</li></ul>",
         ("ADR", "architecture decision record"), ("SA20", "канон ADR"), ("SA19", "выбор интеграции"),
         ["Пишите коротко", "Ссылайтесь на SA", "Последствия важны"],
         [("SA20", "/game/learn/sa-architecture-decisions"), ("SA19", "/game/learn/sa-integration-design")],
         ("Interview drill", "/game/learn/jv-interview-drill")),
        ("jv15-interview-drill.md", "jv-interview-drill", "Interview drill Java/enterprise", "JV drill", "JV15", "tools", 815, D.format(29), "senior",
         ["java", "drill"], 35, "Быстрые ответы JDBC/ORM/JMS/ESB.", ["jv-adr-bus-vs-broker"],
         "Таймер 60–90 секунд на вопрос.",
         "Пул вопросов: PreparedStatement, pool, N+1, queue vs topic, адаптер ESB, dual-write.",
         "После ❌ — возврат к slug выпуска.",
         "Запишите свои формулировки, не чужие.",
         "Пройти 10 вопросов вслух.",
         ["JDBC injection.", "Зачем pool.", "N+1 лечение.", "DLQ.", "ESB vs брокер.", "Отметить ❌.", "Повторить Anki.", "Ссылка на capstone."],
         "парный drill.",
         ["10 ответов", "Gap-list", "Готовность к JV16"],
         "Drill", "flowchart LR\n  Q --> A --> Review --> Fix",
         ("Формат drill?", "таймер + запись пробелов", "Как SA23/SQL15."),
         ("Главный JDBC must?", "PreparedStatement", "Безопасность и ясность."),
         ("Главный ORM trap?", "N+1", "Логи SQL."),
         "<h3>Drill</h3><ul><li>60с</li><li>gap-list</li><li>повтор slug</li></ul>",
         ("drill", "тренировка ответов"), ("gap-list", "список ❌"), ("N+1", "главный ORM trap"),
         ["Говорите вслух", "Чините пробелы", "Дальше capstone"],
         [("JV07", "/game/learn/jv-jpa-nplus1")], ("Capstone", "/game/learn/jv-capstone")),
        ("jv16-capstone.md", "jv-capstone", "Capstone Java/enterprise — чеклист", "JV capstone", "JV16", "architecture", 816, D.format(30), "senior",
         ["java", "capstone"], 35, "Чеклист JV01–JV15 и индекс slug.", ["jv-interview-drill"],
         "Итог трека: от JVM до интеграций.",
         "Junior: JVM, OOP, shell, JDBC, pool, ORM concepts. Middle: JPA/N+1, JMS, ESB adapter, SOAP client, JS glue, hosting. Senior: lab, ADR, drill.",
         "Индекс: jv-se-jvm … jv-capstone (см. SERIES.md).",
         "Связки: SQL, SA, QA17, JS, PY.",
         "Собрать персональный чеклист ❌/✅.",
         ["Пройти SERIES.", "Отметить пробелы.", "Повторить 3 лабы.", "Добавить pet-проект контур.", "Готово к собесу."],
         "взаимная проверка чеклистов.",
         ["Чеклист заполнен", "Индекс slug", "Кросс-серии отмечены"],
         "Трек", "flowchart LR\n  JV01 --> JV08 --> JV16",
         ("С чего начать повтор?", "gap-list drill", "Не с JV01 всегда."),
         ("Где теория ESB?", "SA13", "JV09 только адаптер."),
         ("Где N+1 SQL?", "SQL14", "JV07 мост."),
         "<h3>Чеклист</h3><ul><li>JDBC</li><li>ORM/N+1</li><li>JMS</li><li>ADR</li></ul>",
         ("JV04", "jdbc basics"), ("JV08", "jms"), ("JV14", "ADR"),
         ["Трек закрыт картой", "Не дублируйте SA", "Практика > зубрёжка"],
         [("SERIES", "/game/learn"), ("SA13", "/game/learn/sa-esb-integrations")],
         None),
    ]
    for row in specs:
        (fname, slug, title, short, ep, rubric, order, date, level, tags, dur, excerpt, prereq,
         intro, s1, s2, s3, lab_goal, steps, group, done, dt, diag, q1, q2, q3, cheat, a1, a2, a3,
         summary, links, nxt) = row
        files[fname] = compact(
            slug, title, short, ep, rubric, order, date, P, level, tags, dur, excerpt, prereq,
            intro, s1, s2, s3, lab_goal, steps, group, done, dt, diag, q1, q2, q3, cheat, a1, a2, a3,
            summary, links, nxt,
        )
    return files


def build_product() -> dict[str, str]:
    D = "2027-07-{:02d}T10:00:00+03:00"
    P = ["product_owner"]
    files = {}
    specs = [
        ("pm01-product-management.md", "pm-product-management", "Product Management — роль и границы", "Product Mgmt", "PM01", 901, D.format(1), "junior",
         ["product", "pm"], "PM/CPO vs СА vs Scrum PO.", [],
         "Кто отвечает за ценность продукта и чем роль отличается от системного аналитика.",
         "Product Management — цикл discovery→delivery→measure. CPO/Head of Product задаёт портфель и стратегию.",
         "Scrum Product Owner владеет backlog в фреймворке Scrum; PM шире (go-to-market, P&L, стратегия).",
         "СА проясняет требования и интеграции; не подменяет приоритет ценности (см. SA22).",
         "Развести PM, PO, СА на примере фичи оплаты.",
         ["Кто приоритет ценности?", "Кто пишет постановку интеграций?", "Где CPO?", "Риск смешения ролей.", "Ссылка SA22."],
         "роли в треугольнике.", ["Границы ролей", "Discovery vs Delivery", "Ссылка SA"],
         "Роли", "flowchart TB\n  CPO --> PM\n  PM --> PO\n  SA --> Spec\n  PO --> Backlog",
         ("PM vs PO?", "PM шире продукта; PO — backlog в Scrum", "Часто один человек совмещает."),
         ("СА vs PM?", "ясность решения vs ценность/приоритет", "Стык обязателен."),
         ("Discovery?", "проверка проблемы до большой поставки", "Интервью, эксперименты."),
         "<h3>Роли</h3><ul><li>ценность — PM/PO</li><li>ясность — СА</li></ul>",
         ("PM", "ценность продукта"), ("PO", "backlog Scrum"), ("SA22", "уровни СА"),
         ["Не путайте роли", "Ценность ≠ спецификация", "Дальше приоритизация"],
         [("SA22", "/game/learn/sa-profession-levels")], ("Приоритизация", "/game/learn/pm-prioritization")),
        ("pm02-prioritization.md", "pm-prioritization", "Приоритизация — RICE и WSJF", "Prioritization", "PM02", 902, D.format(3), "junior",
         ["product", "rice", "wsjf"], "Фреймворки приоритизации бэклога.", ["pm-product-management"],
         "Приоритет — явный trade-off, не «всем важно».",
         "RICE: Reach, Impact, Confidence, Effort. WSJF: Cost of Delay / Job Size (SAFe).",
         "См. также USM: [sa-user-stories-use-cases](/game/learn/sa-user-stories-use-cases); severity≠priority у QA: [qa-bugs-reports](/game/learn/qa-bugs-reports).",
         "На собесе покажите цифры и допущения Confidence.",
         "Посчитать RICE для 3 фич.",
         ["Оцените Reach.", "Impact 0.5–3.", "Confidence %.", "Effort person-months.", "Сравните с WSJF идеей CoD."],
         "поспорьте о Confidence.", ["Считаете RICE", "Знаете WSJF идею", "Ссылки SA/QA"],
         "RICE", "flowchart LR\n  R[Reach] --> Score\n  I[Impact] --> Score\n  C[Confidence] --> Score\n  E[Effort] --> Score",
         ("RICE формула?", "(R*I*C)/E", "Effort в знаменателе."),
         ("WSJF?", "Cost of Delay / размер", "SAFe-приоритизация."),
         ("QA priority vs product?", "срочность бага vs ценность фичи", "Разные шкалы."),
         "<h3>RICE</h3><pre><code>(Reach * Impact * Confidence) / Effort</code></pre>",
         ("RICE", "reach impact confidence / effort"), ("WSJF", "CoD / size"), ("USM", "SA02"),
         ["Цифры + допущения", "Не святой грааль", "Кросс SA/QA"],
         [("SA02", "/game/learn/sa-user-stories-use-cases"), ("QA04", "/game/learn/qa-bugs-reports")],
         ("CJM", "/game/learn/pm-cjm")),
        ("pm03-cjm.md", "pm-cjm", "Customer Journey Map", "CJM", "PM03", 903, D.format(5), "junior",
         ["product", "cjm"], "Этапы CJM, боли и метрики шага.", ["pm-prioritization"],
         "CJM показывает путь клиента и точки боли.",
         "Ось: этапы (узнал→купил→использует→поддерживает). На каждом: действия, эмоции, pain, метрика.",
         "Связь с USM: [sa-user-stories-use-cases](/game/learn/sa-user-stories-use-cases). Упоминание в [sa-requirements-basics](/game/learn/sa-requirements-basics).",
         "CJM не заменяет backlog — питает его.",
         "Набросать CJM для «оформить заказ».",
         ["5 этапов.", "Боль на оплате.", "Метрика шага.", "Гипотеза улучшения.", "Ссылка SA01/SA02."],
         "сверьте боли.", ["Есть карта", "Боль измерима", "Связь с USM"],
         "CJM", "flowchart LR\n  A[Aware] --> C[Consider] --> B[Buy] --> U[Use] --> S[Support]",
         ("CJM это?", "карта пути клиента", "Этапы + боли + метрики."),
         ("Связь с USM?", "оба про путь; USM ближе к backlog stories", "SA02."),
         ("Зачем метрика шага?", "увидеть где отвал", "Conversion/time/NPS proxy."),
         "<h3>CJM</h3><ul><li>этапы</li><li>боли</li><li>метрики</li></ul>",
         ("CJM", "customer journey map"), ("pain", "боль этапа"), ("USM", "story map"),
         ["Карта → гипотезы", "Не декорация", "Кросс SA"],
         [("SA01", "/game/learn/sa-requirements-basics"), ("SA02", "/game/learn/sa-user-stories-use-cases")],
         ("Agile PO", "/game/learn/pm-agile-po")),
        ("pm04-agile-po.md", "pm-agile-po", "Agile глазами Product Owner", "Agile PO", "PM04", 904, D.format(7), "junior",
         ["product", "scrum", "po"], "Scrum для PO: backlog, DoR/DoD.", ["pm-cjm"],
         "PO не «пишет задачи разработчикам», а владеет порядком ценности.",
         "Backlog упорядочен; Sprint Goal; Review принимает инкремент. DoR/DoD — канон [sa-methods-scrum-kanban](/game/learn/sa-methods-scrum-kanban), [qa-agile-scrum-kanban](/game/learn/qa-agile-scrum-kanban).",
         "Антипаттерн: PO как проектор чужих хотелок без trade-off.",
         "На собесе покажите, как отказываете от scope в пользу Sprint Goal.",
         "Собрать DoD для фичи «экспорт отчёта».",
         ["3 пункта DoD.", "DoR для story.", "Что на Review?", "Отказ от scope — пример.", "Ссылки SA08/QA16."],
         "сыграйте Review.", ["DoR/DoD", "Роль PO", "Ссылки Agile"],
         "Scrum PO", "flowchart TB\n  Backlog --> Sprint\n  Sprint --> Review\n  Review --> Learn",
         ("DoD?", "Definition of Done инкремента", "Общее для команды."),
         ("PO антипаттерн?", "сборщик хотелок без приоритета", "Нужен trade-off."),
         ("Канон Scrum?", "SA08 / QA16", "Не дублируем курс."),
         "<h3>PO</h3><ul><li>backlog order</li><li>DoR/DoD</li><li>Review</li></ul>",
         ("DoD", "критерий готовности"), ("DoR", "готовность взять в спринт"), ("SA08", "Scrum канон"),
         ["Ценность в порядке backlog", "DoD общий", "Читайте SA/QA"],
         [("SA08", "/game/learn/sa-methods-scrum-kanban"), ("QA16", "/game/learn/qa-agile-scrum-kanban")],
         ("Strategy", "/game/learn/pm-product-strategy")),
        ("pm05-product-strategy.md", "pm-product-strategy", "Product Strategy — ставка и отказ", "Strategy", "PM05", 905, D.format(9), "middle",
         ["product", "strategy"], "Сегмент, ставка, что не делаем.", ["pm-agile-po"],
         "Стратегия — выбор, а не wishlist.",
         "Кто клиент, какая работа (JTBD), чем отличаемся, какие ставки на квартал.",
         "Отказ от сегмента/фич — часть стратегии. Roadmap без стратегии — календарь желаний.",
         "Связь с OKR — следующий выпуск.",
         "Описать стратегию pet-продукта на полстраницы.",
         ["Сегмент.", "Ставка.", "Что вне scope.", "Риск ставки.", "Метрика успеха."],
         "атакуйте «мы для всех».", ["Есть ставка", "Есть отказ", "Метрика"],
         "Ставка", "flowchart TB\n  Seg[Segment] --> Bet[Bet]\n  Bet --> Scope[In/Out]",
         ("Стратегия одной фразой?", "где играем и чем выигрываем", "Плюс явный out-of-scope."),
         ("Зачем отказ?", "фокус ресурсов", "Иначе размазывание."),
         ("Roadmap без стратегии?", "список хотелок", "PM06 чинит формат."),
         "<h3>Strategy</h3><ul><li>segment</li><li>bet</li><li>out</li></ul>",
         ("bet", "ставка"), ("JTBD", "работа клиента"), ("out-of-scope", "отказ"),
         ["Выбор > активность", "Пишите out", "Дальше roadmap"],
         [("PM01", "/game/learn/pm-product-management")], ("Roadmapping", "/game/learn/pm-roadmapping")),
        ("pm06-roadmapping.md", "pm-roadmapping", "Roadmapping — Now/Next/Later", "Roadmapping", "PM06", 906, D.format(11), "middle",
         ["product", "roadmap"], "Now/Next/Later вместо ложного Ганта.", ["pm-product-strategy"],
         "Roadmap коммуницирует намерение, не контракт дат на год.",
         "Now — текущий фокус; Next — кандидаты; Later — идеи. Даты — осторожно, с доверием к данным.",
         "Не путать с roadmap автоматизации QA ([qa-shift-left-automation-roi](/game/learn/qa-shift-left-automation-roi)).",
         "Stakeholder ожидает честности про неопределённость.",
         "Собрать Now/Next/Later для учебного продукта.",
         ["3 Now.", "3 Next.", "Later корзина.", "Что сказать, если просят точную дату.", "Связь со стратегией."],
         "жёсткий стейкхолдер просит Гант.", ["Формат N/N/L", "Честность дат", "Не QA-roadmap"],
         "NNL", "flowchart LR\n  Now --> Next --> Later",
         ("Now/Next/Later?", "горизонты намерения", "Гибче ложного Ганта."),
         ("Почему не год дат?", "неопределённость discovery", "Обещания разрушают доверие."),
         ("QA roadmap?", "другой артефакт", "QA20 про автоматизацию."),
         "<h3>Roadmap</h3><ul><li>Now</li><li>Next</li><li>Later</li></ul>",
         ("Now", "текущий фокус"), ("Later", "идеи"), ("QA20", "не путать"),
         ["Намерение прозрачно", "Даты осторожно", "Стратегия выше"],
         [("QA20", "/game/learn/qa-shift-left-automation-roi")], ("OKR", "/game/learn/pm-okr")),
        ("pm07-okr.md", "pm-okr", "OKR — цели и ключевые результаты", "OKR", "PM07", 907, D.format(13), "middle",
         ["product", "okr"], "Objective vs KR; антипаттерн тасков в KR.", ["pm-roadmapping"],
         "OKR связывают амбицию с измеримым результатом.",
         "Objective — качественная цель. KR — числовой результат (не список задач).",
         "Антипаттерн: KR = «сделать кнопку». Нужно «конверсия +X п.п.» или «latency p95 < …».",
         "OKR не заменяют roadmap — дополняют фокус периода.",
         "Написать 1O + 3KR.",
         ["Objective.", "KR1 метрика.", "KR2.", "Вычеркнуть таскоподобный KR.", "Связь со стратегией."],
         "ревью KR на «тасковость».", ["O≠KR", "KR измеримы", "Нет тасков в KR"],
         "OKR", "flowchart TB\n  O[Objective] --> KR1\n  O --> KR2\n  O --> KR3",
         ("KR vs task?", "результат vs активность", "Кнопка — task; конверсия — KR."),
         ("Сколько O за квартал?", "обычно мало (1–3)", "Иначе нет фокуса."),
         ("OKR = roadmap?", "нет", "Разные артефакты."),
         "<h3>OKR</h3><pre><code>O: …\nKR: metric = target</code></pre>",
         ("Objective", " qualitatively цель"), ("KR", "числовой результат"), ("антипаттерн", "таски в KR"),
         ["Метрики > активность", "Мало целей", "Связь со ставкой"],
         [("Strategy", "/game/learn/pm-product-strategy")], ("Stakeholders", "/game/learn/pm-stakeholders")),
        ("pm08-stakeholders.md", "pm-stakeholders", "Стейкхолдеры и RACI", "Stakeholders", "PM08", 908, D.format(15), "middle",
         ["product", "stakeholders", "raci"], "Карта интересов и RACI.", ["pm-okr"],
         "Стейкхолдер — кто влияет или затронут решением.",
         "Карта: влияние × интерес. RACI: Responsible, Accountable, Consulted, Informed.",
         "Один Accountable на решение. PM часто Accountable за приоритет ценности.",
         "Конфликт интересов — норма; нужен явный trade-off.",
         "RACI на запуск фичи.",
         ["Список стейкхолдеров.", "RACI таблица.", "Кто A?", "Кого только I?", "Эскалация спора."],
         "спор sales vs support.", ["Карта есть", "Один A", "Эскалация ясна"],
         "RACI", "flowchart TB\n  A[Accountable] --> R[Responsible]\n  A --> C[Consulted]\n  A --> I[Informed]",
         ("Accountable сколько?", "один", "Иначе размытие."),
         ("Consulted vs Informed?", "спрашиваем vs уведомляем", "Не путать."),
         ("Зачем карта?", "видеть влияние и риск саботажа", "Коммуникационный план."),
         "<h3>RACI</h3><ul><li>R делает</li><li>A отвечает</li><li>C советует</li><li>I в курсе</li></ul>",
         ("RACI", "матрица ролей"), ("Accountable", "один владелец"), ("influence", "влияние"),
         ["Один A", "Карта живая", "Дальше экономика"],
         [("PM01", "/game/learn/pm-product-management")], ("P&L", "/game/learn/pm-pnl-unit-econ")),
        ("pm09-pnl-unit-econ.md", "pm-pnl-unit-econ", "P&L и unit-экономика на пальцах", "P&L", "PM09", 909, D.format(17), "senior",
         ["product", "pnl", "unit-economics"], "Выручка, маржа, contribution без MBA-простыни.", ["pm-stakeholders"],
         "PM понимает, как фича бьёт по деньгам.",
         "Выручка, себестоимость, валовая маржа. Contribution margin — после переменных затрат.",
         "Unit-экономика: LTV, CAC, payback (упрощённо). Не нужно быть CFO — нужно читать знак эффекта.",
         "Связь с OKR: денежные KR осторожно, но прозрачно.",
         "Оценить влияние −10% churn на выручку (учебно).",
         ["Определите маржу.", "Переменные vs постоянные.", "LTV/CAC идея.", "Риск vanity metric.", "Вопрос к финансисту."],
         "разберите «рост MAU без выручки».", ["Маржа понятна", "Unit-идея", "Не vanity"],
         "Деньги", "flowchart LR\n  Revenue --> COGS --> GrossMargin\n  GrossMargin --> Contribution",
         ("Contribution margin?", "после переменных затрат", "Ближе к решению о масштабе."),
         ("CAC?", "стоимость привлечения клиента", "Сравнивают с LTV."),
         ("Vanity metric?", "красиво, но не связано с ценностью/деньгами", "MAU ради MAU."),
         "<h3>P&amp;L</h3><ul><li>revenue</li><li>margin</li><li>unit economics</li></ul>",
         ("gross margin", "после COGS"), ("LTV", "ценность клиента"), ("CAC", "стоимость привлечения"),
         ["Знак эффекта", "Спрашивайте финансы", "Связь с OKR"],
         [("OKR", "/game/learn/pm-okr")], ("Portfolio", "/game/learn/pm-portfolio")),
        ("pm10-portfolio.md", "pm-portfolio", "Портфель продуктов и ставок", "Portfolio", "PM10", 910, D.format(19), "senior",
         ["product", "portfolio"], "Несколько продуктов/ставок и распределение внимания.", ["pm-pnl-unit-econ"],
         "CPO смотрит портфель, не одну фичу.",
         "Горизонты: core / adjacent / disrupt. Ресурсы конечны — убивайте слабые ставки.",
         "Связь с Product Portfolio Management из резюме CPO.",
         "Риск: все ставки «красные» одновременно.",
         "Разложить 3 продукта по горизонтам.",
         ["Core.", "Adjacent.", "Что убить?", "Метрика портфеля.", "Коммуникация совету."],
         "защитите убийство зомби-продукта.", ["Горизонты", "Kill criteria", "Фокус"],
         "Портфель", "flowchart TB\n  Core --> Adj[Adjacent]\n  Adj --> New[New bets]",
         ("Зачем kill criteria?", "не кормить зомби", "Освободить ёмкость."),
         ("CPO фокус?", "портфель ставок", "Не микроменеджмент sprint."),
         ("Связь с P&L?", "каждая ставка должна иметь экономический смысл", "PM09."),
         "<h3>Portfolio</h3><ul><li>horizons</li><li>kill</li><li>capacity</li></ul>",
         ("core", "основа"), ("kill criteria", "условия закрытия"), ("capacity", "ёмкость команд"),
         ["Портфель = выбор", "Убивайте зомби", "Дальше drill"],
         [("P&L", "/game/learn/pm-pnl-unit-econ")], ("Drill", "/game/learn/pm-interview-drill")),
        ("pm11-interview-drill.md", "pm-interview-drill", "Interview drill Product", "PM drill", "PM11", 911, D.format(21), "senior",
         ["product", "drill"], "Быстрые ответы CPO/PM.", ["pm-portfolio"],
         "Таймер на роли, RICE, CJM, OKR, P&L, roadmap.",
         "10 вопросов из PM01–PM10. ❌ → slug.",
         "Формулировки свои.",
         "После пробелов повторите Anki слабых выпусков перед capstone.",
         "Пройти drill.",
         ["Роли.", "RICE.", "CJM.", "DoD.", "Strategy out.", "NNL.", "KR vs task.", "RACI A.", "Margin.", "Kill criteria."],
         "парный drill.", ["10 ответов", "Gap-list", "К capstone"],
         "Drill", "flowchart LR\n  Ask --> Answer --> Gap",
         ("Формат?", "60–90с", "Как другие capstone."),
         ("Частый fail?", "таски в KR", "PM07."),
         ("Частый fail #2?", "даты на год", "PM06."),
         "<h3>Drill</h3><ul><li>таймер</li><li>gap</li><li>повтор</li></ul>",
         ("gap-list", "пробелы"), ("PM07", "OKR"), ("PM06", "roadmap"),
         ["Говорите вслух", "Чините пробелы", "Capstone"],
         [("PM07", "/game/learn/pm-okr")], ("Capstone", "/game/learn/pm-capstone")),
        ("pm12-capstone.md", "pm-capstone", "Capstone Product — чеклист", "PM capstone", "PM12", 912, D.format(23), "senior",
         ["product", "capstone"], "Чеклист PM01–PM11.", ["pm-interview-drill"],
         "Итог продуктового трека.",
         "Junior: роли, RICE, CJM, Agile PO. Middle: strategy, roadmap, OKR, stakeholders. Senior: P&L, portfolio, drill.",
         "Индекс slug — SERIES.md.",
         "Связки с SA/QA обязательны.",
         "Заполнить ✅/❌.",
         ["Пройти SERIES.", "3 артефакта: CJM, RICE, OKR.", "1 ADR отказа.", "Повторить ❌.", "Готово."],
         "взаимный review артефактов.", ["Чеклист", "Артефакты", "Кроссы"],
         "Трек PM", "flowchart LR\n  PM01 --> PM06 --> PM12",
         ("С чего повтор?", "gap drill", "Не всегда с PM01."),
         ("Где Scrum канон?", "SA08/QA16", "PM04 ссылка."),
         ("Где USM?", "SA02", "PM03 рядом."),
         "<h3>Чеклист</h3><ul><li>роли</li><li>приоритет</li><li>CJM/OKR</li><li>P&amp;L</li></ul>",
         ("PM02", "RICE"), ("PM07", "OKR"), ("PM09", "P&L"),
         ["Трек закрыт", "Артефакты важнее теории", "Стык с SA/QA"],
         [("SERIES", "/game/learn")], None),
    ]
    for row in specs:
        (fname, slug, title, short, ep, order, date, level, tags, excerpt, prereq,
         intro, s1, s2, s3, lab_goal, steps, group, done, dt, diag, q1, q2, q3, cheat, a1, a2, a3,
         summary, links, nxt) = row
        files[fname] = compact(
            slug, title, short, ep, "product", order, date, P, level, tags, 30, excerpt, prereq,
            intro, s1, s2, s3, lab_goal, steps, group, done, dt, diag, q1, q2, q3, cheat, a1, a2, a3,
            summary, links, nxt,
        )
    return files


def build_js() -> dict[str, str]:
    D = "2027-05-{:02d}T10:00:00+03:00"
    P = ["developer", "tester"]
    files = {}
    specs = [
        ("js01-types-coerce.md", "js-types-coerce", "Типы и приведение в JavaScript", "JS types", "JS01", 850, D.format(20), "junior",
         ["javascript", "types"], "typeof, == vs ===, falsy.", [],
         "База языка до DOM и React.",
         "Примитивы: number, string, boolean, null, undefined, symbol, bigint. typeof null === 'object' — ловушка.",
         "== делает coerce; === строго. Falsy: 0, '', null, undefined, NaN, false.",
         "На собесе предпочитайте === и явные преобразования.",
         "Разобрать 5 выражений ==/===.",
         ["0 == false?", "0 === false?", "null == undefined?", "typeof null?", "Список falsy."],
         "блэйц-квиз на coerce.", ["=== default", "Знаете falsy", "typeof null trap"],
         "Сравнение", "flowchart TB\n  Eq[== coerce] --> Trap\n  Strict[===] --> Safe",
         ("=== vs ==?", "строгое без coerce vs с coerce", "Берите ===."),
         ("falsy примеры?", "0 '' null undefined NaN false", "Не путать с false только."),
         ("typeof null?", "'object' (историческая ошибка)", "Проверка null через === null."),
         "<h3>Типы</h3><ul><li>===</li><li>falsy</li><li>typeof null</li></ul>",
         ("===", "строгое равенство"), ("falsy", "приводятся к false"), ("typeof null", "object"),
         ["Строгие сравнения", "Явные convert", "Дальше функции"],
         [("QA06 JS фраза", "/game/learn/qa-web-http-api-basics")], ("Functions", "/game/learn/js-functions-this")),
        ("js02-functions-this.md", "js-functions-this", "Функции и this", "Functions this", "JS02", 851, D.format(22), "junior",
         ["javascript", "functions"], "function vs arrow; this.", ["js-types-coerce"],
         "Функции — граждане первого класса.",
         "function declaration/expression; arrow не имеет своего this (лексический).",
         "this зависит от способа вызова (объект, call/apply, new). В стрелках — извне.",
         "На собесе приведите пример потери this в колбэке.",
         "Починить this в обработчике.",
         ["Обычная function this.", "Arrow this.", "bind.", "Когда arrow удобен.", "Когда нет."],
         "найдите баг с this.", ["Разница function/arrow", "this сценарий", "bind"],
         "this", "flowchart LR\n  Call[obj.method] --> ThisObj\n  Arrow --> Lexical",
         ("arrow this?", "лексический извне", "Нет своего this."),
         ("bind зачем?", "зафиксировать this", "Часто в колбэках."),
         ("first-class?", "функции как значения", "Передача/возврат."),
         "<h3>this</h3><ul><li>call site</li><li>arrow lexical</li><li>bind</li></ul>",
         ("arrow", "короткий синтаксис + lexical this"), ("bind", "фиксация this"), ("call site", "как вызвали"),
         ["Понимайте call site", "Arrow не везде", "Дальше async"],
         [("JS01", "/game/learn/js-types-coerce")], ("Async fetch", "/game/learn/js-async-fetch")),
        ("js03-async-fetch.md", "js-async-fetch", "Promise, async/await и fetch", "Async fetch", "JS03", 852, D.format(24), "junior",
         ["javascript", "async", "fetch"], "Асинхронность в браузере/клиенте.", ["js-functions-this"],
         "Сетевые запросы не блокируют UI поток ожиданием в лоб.",
         "Promise: pending/fulfilled/rejected. async/await — синтаксис над Promise.",
         "fetch возвращает Promise; проверяйте response.ok. Ошибки сети ≠ HTTP 4xx/5xx без проверки.",
         "Связь с Python asyncio — другая модель; здесь браузерный клиент.",
         "Написать async функцию загрузки JSON.",
         ["fetch url.", "await res.json().", "Проверка ok.", "try/catch.", "Что с 404?"],
         "сломайте URL и обработайте.", ["Promise состояния", "await", "ok check"],
         "fetch", "sequenceDiagram\n  JS->>API: fetch\n  API-->>JS: Response\n  JS->>JS: json",
         ("fetch сразу данные?", "нет, Response; нужен json()", "Два await часто."),
         ("404 это throw?", "не всегда; смотрите ok", "fetch не throw на HTTP error по умолчанию."),
         ("async функция возвращает?", "Promise", "Даже если return value."),
         "<h3>async</h3><pre><code>const r = await fetch(url);\nif (!r.ok) throw …;\nreturn r.json();</code></pre>",
         ("Promise", "результат позже"), ("await", "ждать Promise"), ("ok", "HTTP успех"),
         ["Проверяйте ok", "Ловите ошибки", "Дальше DOM"],
         [("JS02", "/game/learn/js-functions-this")], ("DOM", "/game/learn/js-dom-events")),
        ("js04-dom-events.md", "js-dom-events", "DOM и события", "DOM events", "JS04", 853, D.format(26), "junior",
         ["javascript", "dom"], "Дерево DOM, делегирование событий.", ["js-async-fetch"],
         "QA смотрит DOM в DevTools; разработчик меняет его скриптом.",
         "document.querySelector; textContent vs innerHTML (XSS риск).",
         "addEventListener; делегирование на родителе для списка элементов.",
         "См. [qa-web-http-api-basics](/game/learn/qa-web-http-api-basics).",
         "Повесить делегированный click на список.",
         ["Разметка ul/li.", "listener на ul.", "event.target.", "Почему не N listeners.", "XSS через innerHTML."],
         "QA ищет селектор — dev объясняет.", ["querySelector", "delegation", "XSS caution"],
         "Delegation", "flowchart TB\n  UL --> LI1\n  UL --> LI2\n  Click[click] --> UL",
         ("delegation зачем?", "один listener на родителя", "Динамические списки."),
         ("innerHTML риск?", "XSS", "Предпочтительнее textContent/safe API."),
         ("DevTools роль QA?", "смотреть DOM/сеть", "QA06."),
         "<h3>DOM</h3><ul><li>querySelector</li><li>listener</li><li>delegate</li></ul>",
         ("delegation", "события на родителе"), ("XSS", "внедрение скрипта"), ("QA06", "web basics"),
         ["Безопасное обновление DOM", "Делегирование", "Кросс QA"],
         [("QA06", "/game/learn/qa-web-http-api-basics")], ("JSON/XML", "/game/learn/js-json-xml")),
        ("js05-json-xml.md", "js-json-xml", "JSON и XML в браузере", "JSON XML", "JS05", 854, D.format(28), "middle",
         ["javascript", "json", "xml"], "JSON.parse/stringify; XML рядом с SOAP.", ["js-dom-events"],
         "Клиент чаще говорит JSON; XML жив в энтерпрайзе.",
         "JSON.parse / stringify; ловите SyntaxError. Не доверяйте данным с сервера слепо.",
         "XML: DOMParser; канон интеграций — [sa-soap-xml](/game/learn/sa-soap-xml). Python json — [py-stdlib-re-json-copy](/game/learn/py-stdlib-re-json-copy).",
         "На собесе: JSON = JS object notation subset; не путать с JS объектом циклическим.",
         "Спарсить JSON и сравнить с XML-деревом идеей.",
         ["stringify объекта.", "parse строки.", "Ошибка parse.", "Когда XML.", "Ссылки SA12/PY08."],
         "дайте битый JSON.", ["parse/stringify", "ошибки", "Ссылки"],
         "Форматы", "flowchart LR\n  API -->|JSON| JS\n  Legacy -->|XML| JS",
         ("JSON.parse на битом?", "SyntaxError", "try/catch."),
         ("XML канон теории?", "SA12", "Не дублируем SOAP курс."),
         ("циклы в stringify?", "TypeError без replacer", "Нужна осторожность."),
         "<h3>JSON</h3><pre><code>JSON.parse(text)\nJSON.stringify(obj)</code></pre>",
         ("parse", "строка→значение"), ("stringify", "значение→строка"), ("SA12", "XML/SOAP"),
         ["JSON по умолчанию в вебе", "XML — легаси/B2B", "Валидируйте вход"],
         [("SA12", "/game/learn/sa-soap-xml"), ("PY08", "/game/learn/py-stdlib-re-json-copy")],
         ("Capstone", "/game/learn/js-capstone")),
        ("js06-capstone.md", "js-capstone", "Capstone JavaScript — drill", "JS capstone", "JS06", 855, D.format(30), "middle",
         ["javascript", "capstone"], "Drill JS01–JS05 и мост к React B08.", ["js-json-xml"],
         "Закрывающий выпуск языка JS.",
         "Чеклист: типы, функции/this, async/fetch, DOM, JSON/XML.",
         "Дальше UI-компоненты: [b08-react-list](/game/learn/b08-react-list).",
         "Индекс slug — SERIES.md.",
         "Drill 8 вопросов + открыть B08.",
         ["===.", "arrow this.", "fetch ok.", "delegation.", "JSON parse.", "Gap-list.", "Ссылка B08.", "Готово."],
         "парный drill.", ["Чеклист", "Мост React", "Gaps закрыты"],
         "Трек JS", "flowchart LR\n  JS01 --> JS03 --> JS06 --> B08",
         ("Куда после языка?", "React B08", "Компоненты поверх API."),
         ("Главный coerce совет?", "===", "JS01."),
         ("Главный fetch совет?", "проверять ok", "JS03."),
         "<h3>Чеклист</h3><ul><li>types</li><li>this</li><li>async</li><li>DOM</li><li>JSON</li></ul>",
         ("JS01", "types"), ("JS03", "fetch"), ("B08", "React list"),
         ["Язык отделён от React", "Drill обязателен", "Дальше B08"],
         [("B08 React", "/game/learn/b08-react-list")], None),
    ]
    for row in specs:
        (fname, slug, title, short, ep, order, date, level, tags, excerpt, prereq,
         intro, s1, s2, s3, lab_goal, steps, group, done, dt, diag, q1, q2, q3, cheat, a1, a2, a3,
         summary, links, nxt) = row
        files[fname] = compact(
            slug, title, short, ep, "frontend", order, date, P, level, tags, 28, excerpt, prereq,
            intro, s1, s2, s3, lab_goal, steps, group, done, dt, diag, q1, q2, q3, cheat, a1, a2, a3,
            summary, links, nxt,
        )
    return files


def main() -> None:
    write_series("redis", build_redis(), RD_SERIES, RD_README)
    write_series(
        "java",
        build_java(),
        JV_SERIES,
        "# Java Learn series\n\nСм. [`SERIES.md`](SERIES.md).\n",
    )
    write_series(
        "product",
        build_product(),
        PM_SERIES,
        "# Product Learn series\n\nСм. [`SERIES.md`](SERIES.md).\n",
    )
    write_series(
        "js",
        build_js(),
        JS_SERIES,
        "# JavaScript Learn series\n\nСм. [`SERIES.md`](SERIES.md).\n",
    )
    print("all series written")


if __name__ == "__main__":
    main()
