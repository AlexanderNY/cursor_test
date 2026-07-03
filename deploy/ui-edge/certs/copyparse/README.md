# TLS для copyparse.ru

Положите сюда (файлы не коммитятся — см. `.gitignore`):

- `fullchain.pem` — сертификат + цепочка
- `privkey.pem` — приватный ключ

Если ключ от Reg.ru называется `certificate.key`:

```powershell
Copy-Item certificate.key privkey.pem -Force
```

Подробнее: [docs/SSL_CERT_RENEWAL.md](../../../docs/SSL_CERT_RENEWAL.md)
