"""Час работы в уже открытой сессии CopyParse.

Тот же безопасный цикл, что session_cycle.py, плюс простой перед удалением данных.
По умолчанию 60 минут, шаг 5 минут: Inbox, Calendar, Channels. Сбор и публикация не включаются.

Запуск только явно:

    set E2E_SOAK=1
    python ui-app/e2e/soak_hour.py

E2E_SOAK_MINUTES — длительность, E2E_SOAK_STEP_SECONDS — пауза между кругами.
Живой пайплайн за этот час появится только с тестовыми токенами площадок и тарифом standard или admin.
"""

from __future__ import annotations

import asyncio
import os
import sys

if os.getenv("E2E_SOAK") != "1":
    print(
        "Часовой прогон не запущен. Задайте E2E_SOAK=1.\n"
        "Без токенов площадок и тарифа standard/admin час будет пустым ожиданием инбокса.\n"
        "Короткий цикл без ожидания: python ui-app/e2e/session_cycle.py"
    )
    raise SystemExit(0)

os.environ["E2E_SOAK"] = "1"

from session_cycle import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
