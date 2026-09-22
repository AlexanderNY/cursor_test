---
slug: jv-soap-client
title: SOAP-клиент в Java
shortTitle: SOAP client
episode: JV10
rubric: api
order: 810
publishedAt: 2027-06-19T10:00:00+03:00
profiles: [developer]
level: middle
tags: [java, soap, xml, собеседование]
onKnowledgeMap: true
durationMin: 28
excerpt: Клиент SOAP/WSDL; теория — SA12.
prerequisites: [jv-esb-adapter]
seoTitle: SOAP client — middle
seoDescription: Клиент SOAP/WSDL; теория — SA12.
seoKeywords: [java, soap, xml, собеседование]
canonicalUrl: https://9to18.ru/game/learn/jv-soap-client
---

## Введение

Генерация stub из WSDL и вызов операции — типичный энтерпрайз.

## Раздел: Основы

WSDL описывает операции; клиент сериализует XML envelope. Ошибки — Fault.

## Раздел: Практика

Канон понятий: [sa-soap-xml](/game/learn/sa-soap-xml). Здесь не повторяем XSD-курс.

## Раздел: На собесе

На собесе честно: «контракт читаю из WSDL, маплю поля, логирую Fault».

## Лаба

**Цель.** Сопоставить SOAP-операцию с REST-аналогом.

**Шаги.**
1. Что даёт WSDL?
2. Где Fault?
3. Ссылка SA12.
4. Когда оставить SOAP?
5. Чем REST проще для нового API?

**В группу:** сверьте с таблицей SOAP vs REST из SA12.

**Готово, если…**
- [ ] WSDL→client
- [ ] Fault
- [ ] Ссылка SA12

## Схема: Вызов

```mermaid
sequenceDiagram
  Java->>SOAP: Envelope
  SOAP-->>Java: Body/Fault
```

## Тест

### WSDL?

**Ответ:** описание сервиса

**Пояснение:** Генерация клиента.

### Fault?

**Ответ:** ошибка SOAP

**Пояснение:** В Body или отдельный элемент.

### Канон теории?

**Ответ:** SA12

**Пояснение:** Не дублируем.

## Шпаргалка

<h3>Клиент</h3><ul><li>WSDL</li><li>stub</li><li>Fault</li></ul>

## Anki

### Front: WSDL

Back: паспорт сервиса

### Front: SA12

Back: SOAP/XML канон

### Front: Fault

Back: ошибка

## Итоги

- Stub из контракта
- Логируйте XML осторожно
- Теория в SA

## Ссылки

- Learn | [SA12](/game/learn/sa-soap-xml)
- Далее: [JS glue](/game/learn/jv-js-glue)
