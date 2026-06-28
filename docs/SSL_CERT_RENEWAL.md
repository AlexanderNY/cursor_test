# Обновление SSL-сертификата для UI (copyparse.ru)

TLS завершается в контейнере **ui-edge** (nginx). Сертификаты монтируются с хоста в `/etc/nginx/certs/<site>/`.

Схема:

```
Браузер → ui-edge (nginx, :80 / :443) → ui (Vite, :8100)   # copyparse
                                      → ui-site2 (:8200)    # второй сайт, когда включён
```

Переменная окружения `UI_SSL_CERT_DIR` в `docker-compose.yaml` по умолчанию указывает на `./deploy/ui-edge/certs`.

Конфигурация nginx: `deploy/ui-edge/conf.d/` (см. [deploy/ui-edge/README.md](../deploy/ui-edge/README.md)).

## Какие файлы нужны (copyparse)

| Файл на хосте | Путь в контейнере | Назначение |
|---------------|-------------------|------------|
| `deploy/ui-edge/certs/copyparse/fullchain.pem` | `/etc/nginx/certs/copyparse/fullchain.pem` | Сертификат домена + цепочка |
| `deploy/ui-edge/certs/copyparse/privkey.pem` | `/etc/nginx/certs/copyparse/privkey.pem` | Приватный ключ |
| `deploy/ui-edge/certs/copyparse/ca.crt` | не монтируется отдельно | Корневой (опционально, OCSP) |

**Важно:** nginx ждёт `privkey.pem`. Если ключ от Reg.ru называется `certificate.key`:

```powershell
Copy-Item deploy/ui-edge/certs/copyparse/certificate.key deploy/ui-edge/certs/copyparse/privkey.pem -Force
```

Без `privkey.pem` контейнер `ui-edge` не запустится:

```
cannot load certificate key "/etc/nginx/certs/copyparse/privkey.pem": No such file or directory
```

Приватные ключи **не коммитьте** в git.

## Сборка fullchain.pem (Reg.ru / GlobalSign)

По [инструкции Reg.ru для Nginx](https://help.reg.ru/support/ssl-sertifikaty/3-etap-ustanovka-ssl-sertifikata/kak-nastroit-ssl-sertifikat-na-nginx) в один файл `fullchain.pem` подряд, **без пустых строк между блоками**, вставляются три сертификата:

1. **Ваш сертификат** (из письма: «Ваш сертификат предоставлен ниже»)
2. **Промежуточный сертификат**
3. **Корневой сертификат**

Итоговый вид:

```
-----BEGIN CERTIFICATE-----
# доменный сертификат (www.copyparse.ru)
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
# промежуточный (GlobalSign GCC R3 DV TLS CA 2020)
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
# корневой (GlobalSign Root CA - R3)
-----END CERTIFICATE-----
```

Для `ca.crt` сохраните отдельно только корневой сертификат (один блок `BEGIN/END CERTIFICATE`).

## Пошаговое обновление

1. Получите новый сертификат в личном кабинете Reg.ru (статус услуги — «Активна»).
2. Соберите `fullchain.pem` по схеме выше и положите в `deploy/ui-edge/certs/copyparse/`.
3. Убедитесь, что приватный ключ лежит как `deploy/ui-edge/certs/copyparse/privkey.pem` (см. раздел про `certificate.key`).
4. Перезапустите nginx:

```powershell
cd K:\Project\cursor_test
docker compose up -d ui-edge
```

5. Проверьте логи:

```powershell
docker compose logs ui-edge --tail 20
```

Ошибок `[emerg]` быть не должно. Статус:

```powershell
docker compose ps ui-edge
```

6. Проверьте HTTPS в браузере или:

```powershell
curl -I https://www.copyparse.ru
curl -I https://copyparse.ru
```

## Покрываемые домены

Текущий сертификат выпущен на:

- `www.copyparse.ru`
- `copyparse.ru`
- `autodiscover.copyparse.ru`
- `mail.copyparse.ru`
- `owa.copyparse.ru`

## Типичные ошибки

### `cannot load certificate key ... privkey.pem`

Ключа нет или неверное имя файла. Положите ключ в `deploy/ui-edge/certs/copyparse/privkey.pem` (скопируйте из `certificate.key`, если нужно).

### `blocked request. This Host ("copyparse.ru") is not allowed`

Vite 6 блокирует незнакомый заголовок `Host`. В `ui-app/vite.config.ts` должен быть `server.allowedHosts` с доменом (например `.copyparse.ru`). После изменения конфига пересоберите UI:

```powershell
docker compose build ui
docker compose up -d ui
```

### Сайт открывается по IP, но не по домену

- Проверьте A-записи DNS на IP сервера.
- Убедитесь, что `ui-edge` слушает 80/443: `docker compose ps ui-edge`.

### API возвращает CORS-ошибку с нового домена

Добавьте origin в `CORS_ORIGINS` сервиса `gateway` в `docker-compose.yaml` (http и https), затем:

```powershell
docker compose up -d gateway
```

При смене публичного URL обновите `FRONTEND_URL` и `VK_OAUTH_REDIRECT_URI` в сервисе `core`.

## Связанные настройки в репозитории

| Место | Что задаёт |
|-------|------------|
| `docker-compose.yaml` → `ui-edge` | Порты 80/443, монтирование `deploy/ui-edge/conf.d`, `includes`, `certs` |
| `docker-compose.yaml` → `gateway` | `CORS_ORIGINS` |
| `docker-compose.yaml` → `core` | `FRONTEND_URL`, `VK_OAUTH_REDIRECT_URI` |
| `ui-app/vite.config.ts` | `server.allowedHosts` для прокси через nginx |

## Чеклист после продления

- [ ] `fullchain.pem` — три сертификата подряд, без лишних пустых строк
- [ ] `privkey.pem` — тот же ключ, что при генерации CSR
- [ ] `docker compose up -d ui-edge` — без ошибок в логах
- [ ] https://www.copyparse.ru и https://copyparse.ru открываются без предупреждений о цепочке
- [ ] Вход в приложение и API работают (нет CORS / blocked request)
