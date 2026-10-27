> Короткие выпуски этой серии объединены в сводные статьи. Живой файл — первый выпуск группы, его текст включает соседние темы. Старые slug в таблицах ниже отдельно больше не открываются и заново их заводить не нужно. Ссылки из таблиц ведут на сводный выпуск.

# Серия Git Learn: собеседование + тренажёр

Карта **6 выпусков** поверх уже существующих B02 / B06 / S01E03 / QA11. Темы согласованы со шпаргалкой [Git: лист вопросов и ответов (Habr)](https://habr.com/ru/articles/813513/) — формулировки и примеры в статьях **оригинальные**.

**Практика в браузере:** [`/game/git`](/game/git).

| Ep | slug | Тема |
|----|------|------|
| GIT01 | `git-commit-anatomy` | commit, init/clone, stage |
| GIT02 | `git-remotes-fetch-pull` | remote, fetch/pull, branch -m |
| GIT03 | `git-stash-reset-rm` | stash, reset, rm --cached |
| GIT04 | `git-merge-rebase` | merge, rebase, squash |
| GIT05 | `git-tags-bisect-hooks` | tag, bisect, pre-commit |
| GIT06 | `git-flow-config-show` | GitFlow/GitHub Flow, config, show |

```bash
python core/scripts/import_git_learn_series.py
python core/scripts/generate_learn_episodes_ts.py
```
