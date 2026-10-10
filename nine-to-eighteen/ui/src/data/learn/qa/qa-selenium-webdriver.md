---
slug: qa-selenium-webdriver
title: Selenium WebDriver на Python
shortTitle: Selenium WebDriver на Python
episode: QA10
rubric: tools
order: 410
publishedAt: 2026-12-11T10:00:00+03:00
profiles: [tester]
level: junior
tags: [qa, selenium, webdriver, waits, grid, собеседование]
onKnowledgeMap: true
durationMin: 45
excerpt: Драйверы, локаторы, waits, исключения, Actions, фреймы, cookies и Grid — с примерами на Python Selenium.
prerequisites: [qa-aqa-principles]
seoTitle: Selenium WebDriver Python — QA junior
seoDescription: Locators, explicit waits, JSExecutor, Actions, frames, cookies, capabilities и Selenium Grid на Python.
seoKeywords: [selenium, python, waits, webdriver, grid]
canonicalUrl: https://9to18.ru/game/learn/qa-selenium-webdriver
---

## Введение

Selenium WebDriver — классика UI-автоматизации и блок J46–62 / M35–38, M41–42. На собесе ждут: чем драйвер отличается от IDE, какие локаторы стабильнее, почему `time.sleep` — запах, что такое Grid и как кликнуть в iframe. Ниже — ответы и код на **Python Selenium 4**.

Термины и определения согласованы с **ISTQB CTFL v4** и [глоссарием ISTQB](https://glossary.istqb.org/); номера J/M/S — опциональный индекс типовых вопросов собеса.

## Раздел: Драйверы, локаторы, waits, исключения

**WebDriver** — API управления браузером через протокол (W3C WebDriver). **Драйвер** (chromedriver и т.п.) — бинарник-мост; в Selenium 4 часто `Selenium Manager` подтягивает его сам. **Selenium IDE** — запись/playback, не замена фреймворку.

**Локаторы (от более хрупких к устойчивым по смыслу):** id → name → CSS → XPath. Избегайте абсолютного XPath и индексов `tr[3]`. Предпочитайте data-testid, если фронт даёт.

```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver.find_element(By.CSS_SELECTOR, "[data-testid=login]")
driver.find_elements(By.XPATH, "//table[@id='orders']//tr")
```

**Waits.** Implicit — глобальный timeout на find (смешивать с explicit опасно). Explicit — `WebDriverWait` + `expected_conditions`. Fluent — polling с ignored exceptions. **Никогда** не заменяйте стабильный wait слепым `sleep`, кроме отладки.

```python
wait = WebDriverWait(driver, 10)
btn = wait.until(EC.element_to_be_clickable((By.ID, "submit")))
btn.click()
```

**Типичные исключения:** `NoSuchElementException`, `TimeoutException`, `StaleElementReferenceException` (DOM перерисовался — перенайдите элемент), `ElementClickInterceptedException`, `NoSuchFrameException`, `UnhandledAlertException`.

**JavaScriptExecutor** — когда нативный клик не проходит (оверлей) или нужно читать/писать storage:

```python
driver.execute_script("arguments[0].scrollIntoView(true);", el)
driver.execute_script("arguments[0].click();", el)
value = driver.execute_script("return localStorage.getItem('token');")
```

## Раздел: Actions, таблицы, frames, cookies, Grid, capabilities

**Actions (ActionChains):** hover, drag-and-drop, chord клавиш.

```python
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

ActionChains(driver).move_to_element(menu).pause(0.2).click(item).perform()
ActionChains(driver).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
```

**Таблицы.** Найти строку по тексту ячейки, кликнуть кнопку в той же `tr` — через XPath `ancestor::tr` или обход `find_elements`.

**Frames / iframes.** `driver.switch_to.frame(el_or_index_or_name)` → работа → `switch_to.default_content()`. Вложенные — по цепочке. **Windows/tabs:** `window_handles`, `switch_to.window`.

**Cookies / storage.** `add_cookie` / `get_cookies` после открытия домена; для localStorage/sessionStorage — JSExecutor. Полезно для «залогиненного» состояния без UI-логина (осторожно с CSRF/expiry).

**Capabilities / Options.** `ChromeOptions`: headless, window-size, prefs загрузок, disable-gpu, args `--incognito`. В Selenium 4 — W3C capabilities через Options, не устаревший DesiredCapabilities как основной путь.

**Selenium Grid.** Hub/Router раздаёт сессии Node'ам: параллель, разные ОС/браузеры. Локально: Remote WebDriver на URL Grid.

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")
driver = webdriver.Remote(
    command_executor="http://localhost:4444/wd/hub",
    options=options,
)
```

**Когда UI-автоматизация уместна (M):** критичные user journeys, регрессия после релиза, кроссбраузер smoke. Не автоматизировать всё подряд: нестабильный UI, одноразовые проверки, чисто визуальные мелочи без контракта.

## Раздел: Частые вопросы с собеседования

**Вопрос.** Чем уровень тестирования отличается от типа (вида) тестирования?

**Ответ.** Уровень отвечает на «где режем систему»: модуль, стык, продукт целиком, приёмка. Тип — «с какой целью гоняем»: smoke, regression, exploratory, security и т.д. На собесе покажите пример: один checkout можно проверить на integration (API+БД) и оформить прогон как regression после фикса — оси независимы.

**Вопрос.** Зачем на собесе спрашивают equivalence partitioning и граничные значения?

**Ответ.** EP сжимает бесконечные входы в классы «ведут себя одинаково»; BVA бьёт по стыкам классов — там чаще ломается сравнение и валидация. Для поля 18–99 достаточно классов «ниже», «внутри», «выше» и точек 17–18–19, 98–99–100; не нужно 82 случайных числа.

**Вопрос.** Severity и priority в баг-репорте — одно и то же?

**Ответ.** Нет. Severity — ущерб для продукта и пользователя (crash vs опечатка). Priority — когда чинить в очереди команды. Критичный по severity баг может ждать, если воспроизводится только на стенде без пользователей; наоборот, мелкий UI-bug в checkout может быть P1 перед релизом.

**Вопрос.** Что имеют в виду под «пирамидой тестирования» на собеседовании?

**Ответ.** Много быстрых дешёвых проверок внизу (unit, контракт API), меньше медленных UI/e2e наверху. Цель — быстрая обратная связь в CI, а не «всё через Selenium». Пирамида не запрет на e2e: сквозные сценарии оставляют на критичные деньги-потоки.

**Вопрос.** Почему flaky e2e — отдельная тема на middle/senior QA?

**Ответ.** Flaky — тест то зелёный, то красный без изменения кода: тайминги, данные, сеть, параллельность. Команда перестаёт верить CI. Лечат изоляцией данных, явными ожиданиями, стабильными селекторами, отсечением внешних сервисов; иногда понижают уровень — проверяют API вместо хрупкого UI.

## Лаба

**Цель.** Стабильный сценарий: логин → таблица заказов → фильтр → assert строки; плюс работа с iframe и cookie.

**Шаги.**
1. Explicit wait до кликабельности кнопки входа; запретите `time.sleep` в финальном коде.
2. Переключитесь в iframe help-виджета, прочитайте заголовок, вернитесь в default_content.
3. Сохраните session cookie после логина, перезапустите браузер, подставьте cookie, откройте /orders без формы логина.
4. Наведите меню Actions → откройте пункт; обработайте `StaleElementReferenceException` повторным поиском.
5. (Опционально) Поднимите Selenium Grid в Docker и прогоните тот же тест через `Remote`.

**В группу:** почему смесь implicit 10s + explicit 10s даёт «странные» таймауты?

**Готово, если…**
- [ ] Нет sleep в коммите
- [ ] Умеете объяснить stale element
- [ ] Показываете switch_to.frame и cookie inject

## Схема: Explicit wait

```mermaid
sequenceDiagram
  participant T as Test
  participant W as WebDriverWait
  participant D as WebDriver
  participant B as Browser
  T->>W: until clickable locator
  loop poll every 0.5s
    W->>D: find + check state
    D->>B: WebDriver command
    B-->>D: DOM state
  end
  W-->>T: WebElement or TimeoutException
```

## Тест

### Чем explicit wait лучше time.sleep(5)?

**Ответ:** ждёт условие до N секунд и идёт дальше сразу; sleep всегда блокирует фиксированно

**Пояснение:** sleep замедляет suite и всё равно флакает на медленных стендах; EC привязан к готовности UI.

### Что делать со StaleElementReferenceException?

**Ответ:** заново найти элемент в DOM и повторить действие; не хранить WebElement через перерисовку

**Пояснение:** ссылка на узел протухла после AJAX/React reconcile — Page Object метод должен искать элемент в момент действия.

### Зачем Selenium Grid?

**Ответ:** параллельный прогон и/или матрица браузеров/ОС на удалённых node

**Пояснение:** экономит время CI и ловит кроссбраузерные дефекты; локальный Chrome не заменяет матрицу.

### Почему XPath //div[last()] хрупкий?

**Ответ:** зависит от порядка DOM и соседей

**Пояснение:** предпочитайте data-testid, role, стабильный текст или контракт с фронтом.

### Headless vs headed в CI?

**Ответ:** headless быстрее; headed помогает отладке флаки

**Пояснение:** в CI обычно headless; локально смотрят headed при падениях.



## Шпаргалка

<h3>Локаторы</h3>
<ul>
<li>By.ID / NAME / CSS_SELECTOR / XPATH</li>
<li>data-testid &gt; хрупкий абсолютный XPath</li>
</ul>
<h3>Wait</h3>
<pre><code>WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "go"))
)
</code></pre>
<h3>Frames / cookies</h3>
<pre><code>driver.switch_to.frame(frame_el)
driver.switch_to.default_content()
driver.add_cookie({"name": "session", "value": "..."})
</code></pre>
<h3>Исключения</h3>
<ul>
<li>Timeout / NoSuchElement / Stale / ClickIntercepted / NoSuchFrame</li>
</ul>

## Anki

### Front: Implicit vs explicit wait?

Back: implicit — глобально на find; explicit — ждать конкретное условие через WebDriverWait

### Front: Как работать с iframe в Selenium?

Back: switch_to.frame(...), затем switch_to.default_content()

### Front: Как выполнить JS в контексте страницы?

Back: driver.execute_script("...", element) — JSExecutor

### Front: WebDriver vs WebDriver W3C protocol

Back: стандартизированный протокол команд браузеру; Selenium 4 — W3C by default

### Front: StaleElementReferenceException — причина

Back: элемент перерисован в DOM после find; нужен повторный поиск

### Front: Когда Page Object не нужен?

Back: один-два smoke-теста; PO окупается при росте suite



## Итоги

- Стабильность UI-тестов = правильные локаторы + explicit waits, не sleep
- Frames, alerts, windows и cookies — обязательный junior/middle блок
- Actions и JSExecutor — инструменты обхода, не замена нормальным кликам
- Grid и capabilities выводят прогон за пределы «у меня на ноутбуке зелёный»

## Ссылки

- [ISTQB Glossary](https://glossary.istqb.org/)
- [CTFL v4 — Certified Tester Foundation Level](https://istqb.org/certifications/certified-tester-foundation-level-ctfl-v4-0/)
- [Playwright Python](https://playwright.dev/python/)
- Опционально: [QA-interview-250](https://github.com/Konstantine23/QA-interview-250) — полный список формулировок вопросов
- Learn | /game/learn
- Далее: [pytest, CI, Git](/game/learn/qa-pytest-ci-git)
