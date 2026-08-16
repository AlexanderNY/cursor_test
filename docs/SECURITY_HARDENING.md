# Security hardening (фаза 0–1)

Краткий чеклист после аудита безопасности и нагрузки. Подробности реализации — в коде и [INSTALLATION.md](INSTALLATION.md).

## Сделано

| Область | Изменение |
|---------|-----------|
| Секреты | `GAME_BOT_TOKEN`, `GAME_ADMIN_API_TOKEN` только из env; плейсхолдеры в `.env.example` / k8s |
| Порты | Боты, MinIO, Ollama, collector/processor/scheduler — bind `127.0.0.1` |
| Admin API | `/core/admin/*` (collect/process/distribute/posts/…) требуют `get_admin_user` |
| JWT | Gateway принимает только `type=access` |
| url-bot/run | Только admin JWT |
| IDOR | `/tg-bot/auth/status/{id}`, `/tg-bot/channels/{id}` — свой user или admin |
| Rate limit | `X-Forwarded-For` только от `TRUSTED_PROXY_CIDRS` |
| VK OAuth | Signed `state` (HMAC), frontend allowlist |
| Publish | Claim `FOR UPDATE SKIP LOCKED` → `publishing` (tg/vk/ig/tw/dzen) |
| Scheduler | `pg_try_advisory_lock` в `poll_loop` |
| DB pools | `DB_POOL_MAXSIZE` default 8 через env |
| Selenium | `SELENIUM_MAX_CONCURRENT` + semaphore |
| AI | Shared httpx + `AI_MAX_CONCURRENT` semaphore |

## Обязательная ротация (вне кода)

1. **BotFather:** отозвать старый `GAME_BOT_TOKEN`, если он светился в git; выдать новый → `.env`.
2. `openssl rand -hex 32` → `GAME_ADMIN_API_TOKEN`, `JWT_SECRET_KEY`, `SECRET_KEY` (JWT и SECRET должны совпадать).
3. Сменить пароли PostgreSQL и MinIO, если использовали значения из старого `.env.example`.
4. Пересоздать/обновить `.env` из обновлённого `.env.example`.

## Проверки

```powershell
# Порты ботов не должны слушаться на LAN (только 127.0.0.1)
netstat -an | findstr ":8004 :8005 :9000 :11434"

# Без JWT
curl -i -X POST http://127.0.0.1:8000/url-bot/run

# Refresh как Bearer на защищённый путь → 401
# Non-admin на /core/admin/collect/run → 403
```

## Фаза 2 (не в этом релизе)

- AI queue / outbox worker  
- Redis rate limiter + gateway horizontal scale  
- Static production UI (не Vite dev)  
- CDN перед MinIO  
- HttpOnly cookie для refresh  

См. [ARCHITECTURE.md](ARCHITECTURE.md).
