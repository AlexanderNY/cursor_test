# TLS для 9to18.ru

Положите сюда:

- `fullchain.pem` — сертификат + цепочка
- `privkey.pem` — приватный ключ

**Не коммитьте** приватные ключи в git.

HTTPS уже включён в `conf.d/9to18.conf`. После добавления файлов:

```powershell
docker compose -f deploy/ui-edge/docker-compose.yml up -d
```

Локально: `../scripts/gen-self-signed.ps1` (или `.sh`).
