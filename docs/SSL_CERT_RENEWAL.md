# Обновление SSL-сертификата для UI (copyparse.ru / 9to18.ru)

TLS завершается в контейнере **ui-edge** (nginx). Сертификаты монтируются с хоста в `/etc/nginx/certs/<site>/`.

Схема:

```
Браузер → ui-edge (nginx, :80 / :443) → ui (Vite, :8100)        # copyparse
                                      → ui-9to18 (static, :8200) # 9to18
```

Edge — отдельный стек: `deploy/ui-edge/docker-compose.yml`.  
Переменная `UI_SSL_CERT_DIR` по умолчанию — `./certs` относительно каталога edge (или `./deploy/ui-edge/certs` при запуске из корня через `docker-compose.dev.yaml`).

Конфигурация nginx: `deploy/ui-edge/conf.d/` (см. [deploy/ui-edge/README.md](../deploy/ui-edge/README.md)).

Общая схема деплоя: [deploy/DEPLOYMENT.md](../deploy/DEPLOYMENT.md).

## Какие файлы нужны

### copyparse

| Файл на хосте | Путь в контейнере | Назначение |
|---------------|-------------------|------------|
| `deploy/ui-edge/certs/copyparse/fullchain.pem` | `/etc/nginx/certs/copyparse/fullchain.pem` | Сертификат домена + цепочка |
| `deploy/ui-edge/certs/copyparse/privkey.pem` | `/etc/nginx/certs/copyparse/privkey.pem` | Приватный ключ |

### 9to18

| Файл на хосте | Путь в контейнере | Назначение |
|---------------|-------------------|------------|
| `deploy/ui-edge/certs/9to18/fullchain.pem` | `/etc/nginx/certs/9to18/fullchain.pem` | Сертификат домена + цепочка |
| `deploy/ui-edge/certs/9to18/privkey.pem` | `/etc/nginx/certs/9to18/privkey.pem` | Приватный ключ |

**Важно:** nginx ждёт `privkey.pem`. Если ключ от Reg.ru называется `certificate.key`:

```powershell
Copy-Item deploy/ui-edge/certs/copyparse/certificate.key deploy/ui-edge/certs/copyparse/privkey.pem -Force
```

Без `privkey.pem` контейнер `ui-edge` не запустится.

Приватные ключи **не коммитьте** в git.

Локально / staging: `deploy/ui-edge/scripts/gen-self-signed.ps1` (или `.sh`).

## Сборка fullchain.pem (Reg.ru / GlobalSign)

По [инструкции Reg.ru для Nginx](https://help.reg.ru/support/ssl-sertifikaty/3-etap-ustanovka-ssl-sertifikata/kak-nastroit-ssl-sertifikat-na-nginx) в один файл `fullchain.pem` подряд, **без пустых строк между блоками**, вставляются три сертификата:

1. **Ваш сертификат** (из письма: «Ваш сертификат предоставлен ниже»)
2. **Промежуточный сертификат**
3. **Корневой сертификат**

## Пошаговое обновление (copyparse)

1. Получите новый сертификат в личном кабинете Reg.ru.
2. Соберите `fullchain.pem` и положите в `deploy/ui-edge/certs/copyparse/`.
3. Убедитесь, что ключ лежит как `privkey.pem`.
4. Перезапустите edge:

```powershell
docker compose -f deploy/ui-edge/docker-compose.yml up -d
# или локально:
docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up -d ui-edge
```

5. Проверьте:

```powershell
docker compose -f deploy/ui-edge/docker-compose.yml logs ui-edge --tail 20
curl -I https://www.copyparse.ru
```

Аналогично для `certs/9to18/` и `https://www.9to18.ru`.

## Покрываемые домены (copyparse)

Текущий сертификат выпущен на:

- `www.copyparse.ru`
- `copyparse.ru`
- `autodiscover.copyparse.ru`
- `mail.copyparse.ru`
- `owa.copyparse.ru`

## Типичные ошибки

### `cannot load certificate key ... privkey.pem`

Положите ключ в `deploy/ui-edge/certs/<site>/privkey.pem`.

### `blocked request. This Host ("copyparse.ru") is not allowed`

Vite 6: в `ui-app/vite.config.ts` должен быть `server.allowedHosts` с `.copyparse.ru`. Затем:

```powershell
docker compose build ui
docker compose up -d ui
```

### Сайт открывается по IP, но не по домену

- A-записи DNS на IP сервера.
- `ui-edge` слушает 80/443: `docker compose -f deploy/ui-edge/docker-compose.yml ps`.

### API возвращает CORS-ошибку с нового домена

Добавьте origin в `CORS_ORIGINS` сервиса `gateway` в `docker-compose.yaml`, затем `docker compose up -d gateway`.

## Связанные настройки

| Место | Что задаёт |
|-------|------------|
| `deploy/ui-edge/docker-compose.yml` | Порты 80/443, монтирование conf/certs |
| `docker-compose.yaml` → `gateway` | `CORS_ORIGINS` |
| `docker-compose.yaml` → `core` | `FRONTEND_URL`, `VK_PUBLIC_GATEWAY_URL` |
| `ui-app/vite.config.ts` | `server.allowedHosts` |

## Чеклист после продления

- [ ] `fullchain.pem` / `privkey.pem` для нужного сайта
- [ ] `docker compose -f deploy/ui-edge/docker-compose.yml up -d` без `[emerg]`
- [ ] HTTPS открывается без ошибок цепочки
- [ ] Вход / API работают (нет CORS / blocked Host)
