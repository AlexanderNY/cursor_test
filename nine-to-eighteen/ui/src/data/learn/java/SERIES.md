> Короткие выпуски этой серии объединены в сводные статьи. Живой файл — первый выпуск группы, его текст включает соседние темы. Старые slug в таблицах ниже отдельно больше не открываются и заново их заводить не нужно. Ссылки из таблиц ведут на сводный выпуск.

# Серия Java / enterprise Learn

Карта **16 выпусков** для трека разработчика. Полные тексты: `jv01-….md` … `jv16-….md` (glob `jv*.md`).

В статьях — **оригинальные** русские разборы для собеседования и практики. Не копипаст Oracle Tutorials, Jakarta/Hibernate User Guide или постов Vlad Mihalcea (последний — только further reading в ORM-выпусках).

## Источники тем (канон ссылок)

| Блок | Опора |
|------|--------|
| JV01–JV03 | [Oracle Java Tutorials](https://docs.oracle.com/javase/tutorial/) (SE, OOP, environment/process) |
| JV04–JV05 | [Oracle JDBC Tutorial](https://docs.oracle.com/javase/tutorial/jdbc/) / JDBC API docs |
| JV06–JV07 | [Jakarta Persistence](https://jakarta.ee/specifications/persistence/) + [Hibernate User Guide](https://docs.jboss.org/hibernate/orm/current/userguide/html_single/Hibernate_User_Guide.html); доп. чтение [vladmihalcea.com](https://vladmihalcea.com/) |
| JV08 | [Jakarta Messaging](https://jakarta.ee/specifications/messaging/) |
| JV09–JV10 | оригинальные ESB/SOAP-разборы + стандарты [SOAP](https://www.w3.org/TR/soap/) / [WSDL](https://www.w3.org/TR/wsdl/); кросс к SA12/SA13 |
| JV11 | оригинальный polyglot glue; при необходимости [MDN](https://developer.mozilla.org/) |
| JV12 | оригинальный JVM hosting (Docker, heap/cgroup) |
| JV13–JV16 | labs, ADR bus vs broker, interview drill, capstone; кросс к SA19/SA20 и SQL-треку |

## Конвенции

| Поле | Значение |
|------|----------|
| Файлы постов | `jv01-….md` … `jv16-….md` рядом с этим файлом |
| `episode` | `JV01` … `JV16` |
| `order` | `801` … `816` |
| `profiles` | `[developer]` |
| `onKnowledgeMap` | `true` (+ тег `собеседование`) |
| Seed | `import_java_learn_series.py` |

Структура тела — по [`../article-template.md`](../article-template.md): Введение → Разделы → Лаба → Схема (mermaid) → Тест (5) → Шпаргалка HTML → Anki (6) → Итоги → Ссылки.

---

## Junior · `level: junior` · JV01–JV06

| Ep | slug | rubric | Файл |
|----|------|--------|------|
| JV01 | `jv-se-jvm` | tools | [`jv01-se-jvm.md`](jv01-se-jvm.md) |
| JV02 | `jv-oop-vs-python` | tools | [`jv02-oop-vs-python.md`](jv02-oop-vs-python.md) |
| JV03 | `jv-shell-process` | tools | [`jv03-shell-process.md`](jv03-shell-process.md) |
| JV04 | `jv-jdbc-basics` | data | [`jv04-jdbc-basics.md`](jv04-jdbc-basics.md) |
| JV05 | `jv-jdbc-pool-tx` | data | [`jv05-jdbc-pool-tx.md`](jv05-jdbc-pool-tx.md) |
| JV06 | `jv-orm-concepts` | data | [`jv06-orm-concepts.md`](jv06-orm-concepts.md) |

## Middle · `level: middle` · JV07–JV12

| Ep | slug | rubric | Файл |
|----|------|--------|------|
| JV07 | `jv-jpa-nplus1` | data | [`jv07-jpa-nplus1.md`](jv07-jpa-nplus1.md) |
| JV08 | `jv-jms` | api | [`jv08-jms.md`](jv08-jms.md) |
| JV09 | `jv-esb-adapter` | architecture | [`jv09-esb-adapter.md`](jv09-esb-adapter.md) |
| JV10 | `jv-soap-client` | api | [`jv10-soap-client.md`](jv10-soap-client.md) |
| JV11 | `jv-js-glue` | frontend | [`jv11-js-glue.md`](jv11-js-glue.md) |
| JV12 | `jv-jvm-hosting` | tools | [`jv12-jvm-hosting.md`](jv12-jvm-hosting.md) |

## Senior · `level: senior` · JV13–JV16

| Ep | slug | rubric | Файл |
|----|------|--------|------|
| JV13 | `jv-integration-lab` | architecture | [`jv13-integration-lab.md`](jv13-integration-lab.md) |
| JV14 | `jv-adr-bus-vs-broker` | architecture | [`jv14-adr-bus-vs-broker.md`](jv14-adr-bus-vs-broker.md) |
| JV15 | `jv-interview-drill` | tools | [`jv15-interview-drill.md`](jv15-interview-drill.md) |
| JV16 | `jv-capstone` | architecture | [`jv16-capstone.md`](jv16-capstone.md) |

## Обслуживание

```bash
python core/scripts/import_java_learn_series.py
```
