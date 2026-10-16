#!/usr/bin/env python3
"""Write GIT01–GIT06 Learn markdown into nine-to-eighteen/ui/src/data/learn/git/."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "nine-to-eighteen" / "ui" / "src" / "data" / "learn" / "git"


def write(name: str, body: str) -> None:
    path = OUT / name
    path.write_text(body.strip() + "\n", encoding="utf-8")
    print("wrote", path.relative_to(ROOT))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    write(
        "git-commit-anatomy.md",
        r"""
---
slug: git-commit-anatomy
title: Git — commit, init и stage
shortTitle: Commit и stage
episode: GIT01
rubric: tools
order: 701
publishedAt: 2027-05-01T10:00:00+03:00
profiles: [developer, analyst, tester]
level: junior
tags: [git, commit, stage, собеседование]
onKnowledgeMap: true
durationMin: 22
excerpt: Из чего состоит commit, чем init отличается от clone, что такое stage/index.
prerequisites: [b02-git]
seoTitle: Git commit init stage — junior собеседование
seoDescription: Commit как снимок, git init vs clone и области working tree / index / HEAD для собеседования.
seoKeywords: [git, commit, stage, init, clone]
canonicalUrl: https://9to18.ru/game/learn/git-commit-anatomy
---

## Введение

База Git на собесе: что такое commit, как появляется репозиторий и зачем stage. Практика без диска — в [/game/git](/game/git). Старт сезона: [B02](/game/learn/b02-git).

## Раздел: Commit как снимок

**Commit** — снимок дерева файлов плюс метаданные: автор, время, сообщение и ссылки на родителей (обычно один; у merge — два). История — DAG, а не «папка с zip».

```bash
git init
git add README.md
git commit -m "init: учебный репозиторий"
```

**init** создаёт пустой локальный репозиторий. **clone** копирует уже существующий remote со всей историей.

**Вопрос.** Из чего состоит commit? Дерево файлов + родители + автор/время/сообщение; идентичность — хеш содержимого.

## Раздел: Working tree, index, HEAD

Три области:

- **working tree** — файлы, которые вы правите;
- **index (stage)** — что войдёт в следующий commit (`git add`);
- **HEAD** — указатель на текущий commit (часто через имя ветки).

```bash
git status
git add file.txt
git diff
git diff --staged
```

Без `add` commit не увидит правки — это и есть ответ на «что такое stage».

## Лаба

**Цель.** В [/game/git?task=init-commit](/game/git?task=init-commit) сделать init, README и commit.

**Шаги.**
1. Откройте задачу init-commit.
2. `git init`, `write README.md hello`, `git add`, `git commit -m "init: …"`.
3. Нажмите Check. Дополнительно: [stage-index](/game/git?task=stage-index).

**Готово, если…**
- [ ] Объясняете commit без «это просто save»
- [ ] Отличаете init от clone
- [ ] Показываете status до и после add

## Схема: Три области

```mermaid
flowchart LR
  WT[working_tree] --> IDX[index]
  IDX --> C[commit]
  C --> HEAD[HEAD]
```

## Тест

### Из чего состоит commit?

**Ответ:** дерево файлов + родители + метаданные

**Пояснение:** хеш считается от содержимого; сообщение — для людей и review.

### Чем git init отличается от clone?

**Ответ:** init — пустой локальный repo; clone — копия remote с историей

**Пояснение:** clone обычно сразу настраивает origin.

### Что такое stage/index?

**Ответ:** область файлов, готовых к следующему commit

**Пояснение:** попадание через git add.

### Зачем git status?

**Ответ:** показывает WT, index и текущую ветку

**Пояснение:** первая команда при «что-то сломалось».

### Где потренировать без диска?

**Ответ:** /game/git

**Пояснение:** симулятор команд на 9to18.

## Шпаргалка

<h3>Команды</h3>
<pre><code>git init
git clone &lt;url&gt;
git status
git add &lt;path&gt;
git commit -m "message"
</code></pre>
<ul>
<li>Commit = снимок + родители + метаданные</li>
<li>Stage = то, что войдёт в commit</li>
</ul>

## Anki

### Front: Что хранит commit?

Back: Снимок дерева, родители, автор, время, сообщение

### Front: git init — что делает?

Back: Создаёт новый пустой локальный репозиторий

### Front: git clone — что делает?

Back: Копирует remote-репозиторий с историей

### Front: Как попасть в index?

Back: git add

### Front: HEAD — это?

Back: Указатель на текущий commit (часто через ветку)

### Front: Зачем понятное сообщение commit?

Back: История и code review читаются людьми

## Итоги

- Commit — узел графа истории, не «файл сохранения»
- Stage отделяет «правили» от «готово к снимку»
- Тренажёр: /game/git

## Ссылки

- [B02 · Git init](/game/learn/b02-git)
- [Pro Git](https://git-scm.com/book/ru/v2)
- [Habr: лист Q&A (индекс тем)](https://habr.com/ru/articles/813513/)
- [Тренажёр Git](/game/git)
- [Далее: remotes](/game/learn/git-remotes-fetch-pull)
""",
    )

    write(
        "git-remotes-fetch-pull.md",
        r"""
---
slug: git-remotes-fetch-pull
title: Git — remote, fetch, pull и rename ветки
shortTitle: Remotes и fetch/pull
episode: GIT02
rubric: tools
order: 702
publishedAt: 2027-05-02T10:00:00+03:00
profiles: [developer, analyst, tester]
level: junior
tags: [git, remote, fetch, pull, собеседование]
onKnowledgeMap: true
durationMin: 24
excerpt: remote -v / add / set-url, разница fetch и pull, переименование ветки branch -m.
prerequisites: [git-commit-anatomy]
seoTitle: Git remote fetch pull branch -m — собеседование
seoDescription: Как менять URL remote, чем fetch отличается от pull и как переименовать ветку.
seoKeywords: [git, remote, fetch, pull, branch]
canonicalUrl: https://9to18.ru/game/learn/git-remotes-fetch-pull
---

## Введение

После локального commit появляется remote. На собесе ждут `remote -v`, смену URL и чёткое отличие **fetch** от **pull**. Практика: [/game/git](/game/git).

## Раздел: remote add и set-url

```bash
git remote -v
git remote add origin https://github.com/you/notes.git
git remote set-url origin https://github.com/you/notes.git
```

**add** регистрирует короткое имя (обычно `origin`). **set-url** меняет адрес без удаления remote — типичный ответ на «как поменять ссылку на удалённый репозиторий».

## Раздел: fetch vs pull

- **fetch** — скачивает объекты и обновляет remote-tracking refs, **не** сливает в текущую ветку.
- **pull** — fetch + merge (или rebase, если так настроено) в текущую ветку.

```bash
git fetch origin
git pull origin
```

**Вопрос.** Чем pull отличается от fetch? Pull ещё и интегрирует изменения в вашу ветку; fetch только забирает данные.

## Раздел: Переименовать ветку

```bash
# текущая ветка
git branch -m new-name
# любая ветка
git branch -m old-name new-name
```

Локальное переименование не переименовывает ветку на GitHub само — там отдельно push и удаление старого имени.

## Лаба

**Цель.** Задачи [remote-set-url](/game/git?task=remote-set-url), [fetch-vs-pull](/game/git?task=fetch-vs-pull), [branch-rename](/game/git?task=branch-rename).

**Шаги.**
1. Добавьте origin и смените URL на `https://github.com/you/notes.git`.
2. В сценарии «remote ahead» сделайте `git pull origin`.
3. Переименуйте ветку через `git branch -m`.

**Готово, если…**
- [ ] Объясняете fetch vs pull одним предложением
- [ ] Меняете URL через set-url, не через «удалить и добавить вслепую»
- [ ] Знаете `branch -m`

## Схема: fetch и pull

```mermaid
flowchart TB
  R[origin] -->|fetch| T[remote-tracking]
  T -->|merge| L[local_branch]
  R -->|pull| L
```

## Тест

### Как посмотреть remote URL?

**Ответ:** git remote -v

**Пояснение:** показывает fetch/push URL для каждого remote.

### Чем fetch отличается от pull?

**Ответ:** fetch не сливает; pull = fetch + merge

**Пояснение:** после fetch рабочая ветка не двигается сама.

### Как сменить URL origin?

**Ответ:** git remote set-url origin &lt;url&gt;

**Пояснение:** не нужно удалять remote, если меняется только адрес.

### Как переименовать текущую ветку?

**Ответ:** git branch -m new-name

**Пояснение:** для чужой ветки: git branch -m old new.

### Что делает git remote add?

**Ответ:** регистрирует имя и URL удалённого репозитория

**Пояснение:** обычно имя origin.

## Шпаргалка

<pre><code>git remote -v
git remote add origin &lt;url&gt;
git remote set-url origin &lt;url&gt;
git fetch origin
git pull origin
git branch -m new-name
</code></pre>

## Anki

### Front: git remote -v?

Back: Список remote с URL fetch/push

### Front: fetch vs pull?

Back: fetch только забирает; pull ещё сливает в текущую ветку

### Front: set-url зачем?

Back: Сменить адрес remote без удаления записи

### Front: branch -m?

Back: Переименовать ветку

### Front: Типичное имя remote?

Back: origin

### Front: После локального rename на GitHub?

Back: Нужен push новой ветки и удаление старой на remote

## Итоги

- remote — ярлык на URL
- fetch безопаснее «просто посмотреть»; pull меняет вашу ветку
- branch -m — локальное переименование

## Ссылки

- [S01E03 · Git](/game/learn/s01e03-git)
- [Pro Git · remotes](https://git-scm.com/book/ru/v2/Основы-Git-Работа-с-удалёнными-репозиториями)
- [Habr Q&A](https://habr.com/ru/articles/813513/)
- [Тренажёр](/game/git)
- [Далее: stash/reset](/game/learn/git-stash-reset-rm)
""",
    )

    write(
        "git-stash-reset-rm.md",
        r"""
---
slug: git-stash-reset-rm
title: Git — stash, reset и rm --cached
shortTitle: Stash и reset
episode: GIT03
rubric: tools
order: 703
publishedAt: 2027-05-03T10:00:00+03:00
profiles: [developer, analyst, tester]
level: junior
tags: [git, stash, reset, собеседование]
onKnowledgeMap: true
durationMin: 24
excerpt: stash list/pop/apply, отмена локального commit через reset, удаление из индекса rm --cached.
prerequisites: [git-remotes-fetch-pull]
seoTitle: Git stash reset rm --cached — собеседование
seoDescription: Когда stash, как отменить неопубликованный commit и убрать файл из индекса, оставив на диске.
seoKeywords: [git, stash, reset, rm]
canonicalUrl: https://9to18.ru/game/learn/git-stash-reset-rm
---

## Введение

Три бытовых навыка: временно убрать грязный worktree (**stash**), откатить локальный commit (**reset**) и выкинуть файл из индекса, не удаляя с диска (**rm --cached**). В QA кратко: [QA11](/game/learn/qa-pytest-ci-git).

## Раздел: stash

```bash
git stash
git stash list
git stash pop
git stash apply
git stash drop
git stash clear
```

**stash** сохраняет незакоммиченные изменения и очищает worktree. **pop** применяет и удаляет запись; **apply** оставляет запись в списке.

## Раздел: Отмена неопубликованного commit

Если commit ещё не запушен:

```bash
git reset HEAD~
```

**mixed** (по умолчанию) двигает ветку назад, index становится как у родителя, правки остаются в worktree. **--hard** ещё и затирает worktree — опаснее. **--soft** оставляет index как был.

На опубликованной истории reset + force-push согласовывайте с командой.

## Раздел: rm --cached

```bash
git rm --cached secret.env
```

Убирает путь из индекса (и из следующего commit), **файл на диске остаётся**. Типичный кейс: случайно добавили `.env` до gitignore.

## Лаба

**Цель.** [/game/git?task=stash-roundtrip](/game/git?task=stash-roundtrip), [reset-soft-local](/game/git?task=reset-soft-local), [rm-cached](/game/git?task=rm-cached).

**Шаги.**
1. Stash грязного файла до clean worktree.
2. Отмените последний commit через `git reset HEAD~`.
3. Уберите `secret.env` из index через `rm --cached`.

**Готово, если…**
- [ ] Отличаете pop от apply
- [ ] Не путаете reset --hard с mixed
- [ ] Знаете rm --cached для секретов в индексе

## Схема: stash

```mermaid
flowchart LR
  Dirty[dirty_WT] --> Stash[stash_stack]
  Stash --> Clean[clean_WT]
  Stash --> Pop[pop_or_apply]
```

## Тест

### Зачем git stash?

**Ответ:** временно сохранить незакоммиченные правки и очистить WT

**Пояснение:** удобно перед switch/pull.

### Чем stash pop отличается от apply?

**Ответ:** pop удаляет запись из списка; apply оставляет

**Пояснение:** apply безопаснее, если не уверены.

### Как отменить последний локальный commit, сохранив правки?

**Ответ:** git reset HEAD~

**Пояснение:** mixed по умолчанию; --hard опаснее.

### Что делает git rm --cached file?

**Ответ:** убирает file из index, файл на диске остаётся

**Пояснение:** частый фикс для случайного .env.

### Когда reset на опубликованной ветке опасен?

**Ответ:** нужен force-push и согласие команды

**Пояснение:** переписывает историю, которую уже кто-то скачал.

## Шпаргалка

<pre><code>git stash / list / pop / apply / drop
git reset HEAD~
git reset --hard HEAD~
git rm --cached &lt;path&gt;
</code></pre>

## Anki

### Front: git stash?

Back: Прячет незакоммиченные изменения во временный стек

### Front: stash pop vs apply?

Back: pop применяет и удаляет запись; apply только применяет

### Front: reset HEAD~?

Back: Откат указателя ветки на родителя

### Front: reset --hard?

Back: Ещё и затирает working tree и index

### Front: rm --cached?

Back: Убрать из индекса, оставить файл на диске

### Front: .env попал в add — первый шаг?

Back: rm --cached, дописать gitignore, ротация секрета если уже push

## Итоги

- stash — карман для WIP
- reset локально ок; на shared history — осторожно
- rm --cached спасает индекс от секретов

## Ссылки

- [QA11 · pytest Git CI](/game/learn/qa-pytest-ci-git)
- [Pro Git](https://git-scm.com/book/ru/v2)
- [Habr Q&A](https://habr.com/ru/articles/813513/)
- [Тренажёр](/game/git)
- [Далее: merge/rebase](/game/learn/git-merge-rebase)
""",
    )

    write(
        "git-merge-rebase.md",
        r"""
---
slug: git-merge-rebase
title: Git — merge, rebase и squash
shortTitle: Merge и rebase
episode: GIT04
rubric: tools
order: 704
publishedAt: 2027-05-04T10:00:00+03:00
profiles: [developer, analyst, tester]
level: middle
tags: [git, merge, rebase, squash, собеседование]
onKnowledgeMap: true
durationMin: 26
excerpt: Чем merge отличается от rebase, когда squash через rebase -i и почему force-push опасен.
prerequisites: [git-stash-reset-rm, b06-git-branch]
seoTitle: Git merge vs rebase squash — собеседование
seoDescription: Merge сохраняет историю ветвления; rebase переписывает. Squash и force-push — правила команды.
seoKeywords: [git, merge, rebase, squash]
canonicalUrl: https://9to18.ru/game/learn/git-merge-rebase
---

## Введение

На собесе почти всегда спрашивают **merge vs rebase**. В [B06](/game/learn/b06-git-branch) rebase откладывали — здесь разбираем. В симуляторе [/game/git](/game/git) есть линейный merge; интерактивный squash — на машине.

## Раздел: merge

```bash
git switch main
git merge feature
```

**merge** создаёт merge-commit с двумя родителями (если не fast-forward). История ветвления сохраняется, «шум» merge-коммитов возможен.

Проверка «влита ли ветка»:

```bash
git branch --merged
```

## Раздел: rebase

```bash
git switch feature
git rebase main
```

**rebase** переносит ваши коммиты «поверх» другой базы: хеши меняются, история выглядит линейной. На общих ветках rebase переписывает чужую историю — согласовывайте.

## Раздел: squash через rebase -i

```bash
git rebase -i HEAD~3
# в редакторе: pick первого, squash/s остальных
git push --force-with-lease
```

Склеивает несколько коммитов в один. После переписывания истории на уже запушенной ветке нужен force-push — только на личной feature-ветке и с `--force-with-lease`.

В браузерном тренажёре полного `rebase -i` нет: отработайте merge в задаче [merge-feature](/game/git?task=merge-feature).

## Лаба

**Цель.** Смержить feature в main в [/game/git?task=merge-feature](/game/git?task=merge-feature). Локально (по желанию) сделайте squash трёх WIP-коммитов.

**Шаги.**
1. Check задачи merge-feature.
2. На бумаге сравните граф после merge и после rebase.
3. Проговорите, когда force-push запрещён (main/shared).

**Готово, если…**
- [ ] Одним предложением отличаете merge и rebase
- [ ] Знаете branch --merged
- [ ] Не предлагаете rebase published main

## Схема: merge vs rebase

```mermaid
flowchart TB
  subgraph mergePath [merge]
    M1[feature] --> M2[merge_commit]
    M3[main] --> M2
  end
  subgraph rebasePath [rebase]
    R1[commits_replayed] --> R2[linear_main]
  end
```

## Тест

### Чем merge отличается от rebase?

**Ответ:** merge сохраняет ветвление; rebase переписывает историю линейно

**Пояснение:** у merge часто два родителя; rebase меняет хеши.

### Когда rebase опасен?

**Ответ:** на уже опубликованной общей ветке

**Пояснение:** коллеги получат конфликтующую историю.

### Как склеить коммиты?

**Ответ:** git rebase -i и squash

**Пояснение:** затем осторожный force-with-lease на feature.

### git branch --merged?

**Ответ:** список веток, уже влитых в текущую

**Пояснение:** удобно чистить старые feature.

### Fast-forward merge — что это?

**Ответ:** указатель ветки просто сдвинули, merge-commit не нужен

**Пояснение:** история уже линейна относительно цели.

## Шпаргалка

<pre><code>git merge feature
git rebase main
git rebase -i HEAD~N
git branch --merged
git push --force-with-lease
</code></pre>

## Anki

### Front: merge vs rebase?

Back: merge сохраняет развилку; rebase переносит коммиты на новую базу

### Front: squash как?

Back: interactive rebase, пометить commits как squash/fixup

### Front: force-with-lease зачем?

Back: Не затереть чужие новые коммиты на remote вслепую

### Front: branch --merged?

Back: Ветки, чьи коммиты уже достижимы из HEAD

### Front: Когда merge-commit неизбежен?

Back: Когда истории разошлись и нужен явный узел слияния

### Front: Rebase main у всех?

Back: Обычно нет; политика команды важнее «красивой линии»

## Итоги

- merge — безопасно для shared истории
- rebase — для локальной/личной feature
- squash + force только осознанно

## Ссылки

- [B06 · ветка](/game/learn/b06-git-branch)
- [Pro Git · rebase](https://git-scm.com/book/ru/v2/Ветвление-в-Git-Rebase)
- [Habr Q&A](https://habr.com/ru/articles/813513/)
- [Тренажёр](/game/git)
- [Далее: tags/bisect](/game/learn/git-tags-bisect-hooks)
""",
    )

    write(
        "git-tags-bisect-hooks.md",
        r"""
---
slug: git-tags-bisect-hooks
title: Git — tag, bisect и pre-commit
shortTitle: Tag, bisect, hooks
episode: GIT05
rubric: tools
order: 705
publishedAt: 2027-05-05T10:00:00+03:00
profiles: [developer, analyst, tester]
level: middle
tags: [git, tag, bisect, hooks, собеседование]
onKnowledgeMap: true
durationMin: 24
excerpt: Теги релизов, поиск ломающего commit через bisect, идея pre-commit hooks.
prerequisites: [git-merge-rebase]
seoTitle: Git tag bisect pre-commit — собеседование
seoDescription: Annotated tag, git bisect good/bad и хуки до commit (в т.ч. husky) для собеседования.
seoKeywords: [git, tag, bisect, pre-commit, husky]
canonicalUrl: https://9to18.ru/game/learn/git-tags-bisect-hooks
---

## Введение

Три «взрослых» инструмента: **tag** как метка релиза, **bisect** как бинарный поиск бага в истории, **pre-commit** как автоматическая проверка перед снимком. В [/game/git](/game/git) — tag и упрощённый bisect; живые hooks — на машине.

## Раздел: tag

```bash
git tag v1.0
git tag -a v1.0 -m "release 1.0"
git push origin v1.0
```

Легковесный tag — указатель на commit. Annotated (`-a`) хранит автора, дату и сообщение — предпочтительнее для релизов.

## Раздел: bisect

```bash
git bisect start
git bisect bad                # текущий сломан
git bisect good <good-hash>   # известный рабочий
# git проверяет середину; вы говорите good/bad
git bisect reset
```

**bisect** ищет первый плохой commit бинарным поиском. В тренажёре: [bisect-find](/game/git?task=bisect-find).

## Раздел: pre-commit hooks

Хук **pre-commit** — скрипт в `.git/hooks/pre-commit` (или менеджер вроде **husky** / pre-commit framework), который Git запускает перед созданием commit. Упал хук — commit не создался. Типично: lint, format, быстрые unit-тесты. Не путать с CI: хук — локальный шлагбаум, CI — командный.

## Лаба

**Цель.** [tag-release](/game/git?task=tag-release) и [bisect-find](/game/git?task=bisect-find).

**Шаги.**
1. Поставьте тег v1.0.
2. Прогоните bisect start / bad / good HEAD~2.
3. На своей машине гляньте `.git/hooks/pre-commit.sample`.

**Готово, если…**
- [ ] Отличаете lightweight и annotated tag
- [ ] Объясняете bisect без «перебираю все коммиты вручную»
- [ ] Знаете, где живёт pre-commit

## Схема: bisect

```mermaid
flowchart LR
  G[good] --> M[mid]
  M --> B[bad]
  M -->|result| F[first_bad]
```

## Тест

### Зачем tag?

**Ответ:** именованная точка в истории, часто релиз

**Пояснение:** удобнее, чем помнить хеш.

### Чем annotated tag лучше lightweight?

**Ответ:** хранит автора, дату и сообщение

**Пояснение:** для релизов обычно -a.

### Что делает git bisect?

**Ответ:** бинарный поиск commit, сломавшего поведение

**Пояснение:** помечаете good/bad, Git выбирает середину.

### Где настраивают pre-commit?

**Ответ:** .git/hooks или менеджер husky/pre-commit

**Пояснение:** выполняется локально перед commit.

### Заменяет ли hook CI?

**Ответ:** нет, дополняет

**Пояснение:** hook можно обойти; CI — общий контроль.

## Шпаргалка

<pre><code>git tag v1.0
git tag -a v1.0 -m "msg"
git bisect start / bad / good / reset
# hooks: .git/hooks/pre-commit
</code></pre>

## Anki

### Front: tag?

Back: Указатель на commit с человекочитаемым именем

### Front: annotated tag?

Back: Tag-объект с автором, датой и сообщением

### Front: bisect?

Back: Бинарный поиск первого bad commit

### Front: pre-commit hook?

Back: Скрипт проверки перед созданием commit

### Front: husky?

Back: Популярный менеджер git-hooks в JS-проектах

### Front: tag push?

Back: Обычный push не всегда шлёт tags — push origin v1.0

## Итоги

- tag — метка релиза
- bisect экономит часы бисекта «на глаз»
- hooks — локальная дисциплина, не замена CI

## Ссылки

- [Pro Git · tags](https://git-scm.com/book/ru/v2/Основы-Git-Работа-с-метками)
- [git-bisect](https://git-scm.com/docs/git-bisect)
- [Habr Q&A](https://habr.com/ru/articles/813513/)
- [Тренажёр](/game/git)
- [Далее: flow/config](/game/learn/git-flow-config-show)
""",
    )

    write(
        "git-flow-config-show.md",
        r"""
---
slug: git-flow-config-show
title: Git — GitFlow, GitHub Flow, config и show
shortTitle: Flow и config
episode: GIT06
rubric: tools
order: 706
publishedAt: 2027-05-06T10:00:00+03:00
profiles: [developer, analyst, tester]
level: middle
tags: [git, gitflow, github-flow, config, собеседование]
onKnowledgeMap: true
durationMin: 22
excerpt: Модели ветвления GitFlow vs GitHub Flow, git config, show и просмотр файлов commit.
prerequisites: [git-tags-bisect-hooks]
seoTitle: GitFlow vs GitHub Flow config show — собеседование
seoDescription: Две модели ветвления, git config user.name и как смотреть файлы конкретного commit через show/log.
seoKeywords: [git, gitflow, github flow, config, show]
canonicalUrl: https://9to18.ru/game/learn/git-flow-config-show
---

## Введение

Закрываем шпаргалку: **модели ветвления**, **config**, как смотреть «что в commit». Связка с практикой веток: [B06](/game/learn/b06-git-branch), [S01E03](/game/learn/s01e03-git).

## Раздел: GitFlow и GitHub Flow

**GitFlow** — долгоживущие `main` и `develop`, плюс feature/release/hotfix ветки. Подходит релизным циклам с версиями.

**GitHub Flow** — одна основная `main`, короткие feature-ветки и PR/review/deploy. Проще для непрерывной поставки.

На собесе достаточно назвать обе и сказать, что выбирает команда под частоту релизов.

## Раздел: git config

```bash
git config user.name "Ada"
git config user.email "ada@example.com"
git config --list
git config --get user.email
```

Настройки бывают `--system`, `--global`, `--local` (репозиторий). Локальные перекрывают global.

## Раздел: log и show

```bash
git log --oneline
git show <hash>
```

**show** показывает метаданные commit и diff (в симуляторе — список файлов снимка). Ответ на «как найти файлы, изменившиеся в commit».

## Лаба

**Цель.** Повторите [merge-feature](/game/git?task=merge-feature) и [tag-release](/game/git?task=tag-release); в песочнице выполните `git config user.name` и `git show` / `git log --oneline`.

**Шаги.**
1. Выставьте user.name в симуляторе.
2. Сделайте commit и `git show`.
3. Нарисуйте, чем GitHub Flow проще GitFlow для учебного notes.

**Готово, если…**
- [ ] Называете GitFlow и GitHub Flow
- [ ] Знаете уровни config
- [ ] Открываете содержимое commit через show/log

## Схема: GitHub Flow

```mermaid
flowchart LR
  main[main] --> feat[feature_branch]
  feat --> pr[pull_request]
  pr --> main
```

## Тест

### Чем GitHub Flow отличается от GitFlow?

**Ответ:** одна main и короткие feature; у GitFlow ещё develop/release/hotfix

**Пояснение:** GitFlow тяжелее, зато явные релизы.

### Зачем git config user.email?

**Ответ:** подпись автора в commit

**Пояснение:** без неё Git может ругаться или взять системное имя.

### Как посмотреть файлы commit?

**Ответ:** git show &lt;hash&gt; или git log -p

**Пояснение:** сначала log, потом show по хешу.

### Где хранится local config?

**Ответ:** в .git/config репозитория

**Пояснение:** global обычно в ~/.gitconfig.

### Когда выбрать GitFlow?

**Ответ:** при редких версионированных релизах и нескольких линиях поддержки

**Пояснение:** иначе часто хватает GitHub Flow.

## Шпаргалка

<pre><code>git config user.name "…"
git config user.email "…"
git log --oneline
git show &lt;hash&gt;
# GitHub Flow: main + short feature + PR
# GitFlow: main + develop + release/hotfix
</code></pre>

## Anki

### Front: GitHub Flow?

Back: main + короткие feature + PR

### Front: GitFlow?

Back: main/develop + feature/release/hotfix

### Front: git config уровни?

Back: system, global, local (local сильнее)

### Front: git show?

Back: Показать commit и его изменения

### Front: Зачем email в config?

Back: Идентификация автора в истории

### Front: branch --merged снова?

Back: Какие ветки уже влиты в текущую

## Итоги

- Модель ветвления — договорённость команды
- config задаёт автора
- show/log — глаза в истории

## Ссылки

- [GitHub Flow](https://docs.github.com/ru/get-started/using-github/github-flow)
- [Pro Git](https://git-scm.com/book/ru/v2)
- [Habr Q&A](https://habr.com/ru/articles/813513/)
- [B06](/game/learn/b06-git-branch)
- [Тренажёр](/game/git)
""",
    )


if __name__ == "__main__":
    main()
