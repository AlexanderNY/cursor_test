import type { TopicDeck } from '@/data/learning-map/decks/types'

export const deckSecurity: TopicDeck = {
  branchTitle: 'Безопасность',
  cards: [
    {
      id: 'pool:security:jwt',
      front: `Что такое JWT?`,
      back: `Подписанный токен (header.payload.signature). Проверка подписи и claims (exp, aud). Не храните секреты в payload как «защиту».`,
      learnSlug: 'sec-jwt-storage',
    },
    {
      id: 'pool:security:authn-authz',
      front: `Authentication vs authorization?`,
      back: `AuthN — кто ты; AuthZ — что можно. Путаница даёт IDOR и дырявые роли.`,
      learnSlug: 'sec-jwt-storage',
    },
    {
      id: 'pool:security:https',
      front: `Зачем HTTPS?`,
      back: `Конфиденциальность и целостность в транзите, защита от перехвата/подмены. HSTS усиливает.`,
      learnSlug: 'net-tls',
    },
    {
      id: 'pool:security:password',
      front: `Хранение паролей?`,
      back: `Хэш с солью (bcrypt/argon2), не plaintext/обратимое шифрование. Политика сложности + breach check по возможности.`,
      learnSlug: 'sec-jwt-storage',
    },
    {
      id: 'pool:security:xss',
      front: `XSS?`,
      back: `Внедрение скрипта в страницу жертвы. Экранирование, CSP, httpOnly cookies для сессий.`,
      learnSlug: 'net-tls',
    },
    {
      id: 'pool:security:csrf',
      front: `CSRF?`,
      back: `Браузер жертвы шлёт cookie на ваш сайт по воле злоумышленника. SameSite, CSRF-токены.`,
      learnSlug: 'net-tls',
    },
    {
      id: 'pool:security:sqli',
      front: `SQL injection?`,
      back: `Склейка SQL с user input. Параметры/ORM bind, least privilege БД.`,
      learnSlug: 'sec-jwt-storage',
    },
    {
      id: 'pool:security:oauth',
      front: `OAuth2 идея?`,
      back: `Делегированный доступ без передачи пароля ресурсу. Роли authorization server / client / resource.`,
      learnSlug: 'sec-jwt-storage',
    },
    {
      id: 'pool:security:secrets',
      front: `Утечка секретов?`,
      back: `Не коммитить ключи; ротация; scan истории. В логах маскировать токены.`,
      learnSlug: 'net-tls',
    },
    {
      id: 'pool:security:tls-cert',
      front: `Сертификаты TLS?`,
      back: `Цепочка доверия CA, срок, hostname. Let's Encrypt автоматизирует выпуск.`,
      learnSlug: 'net-tls',
    },
    {
      id: 'pool:security:session',
      front: `Session vs JWT?`,
      back: `Server-side session — отзыв проще; JWT —stateless, отзыв сложнее (denylist/короткий TTL).`,
      learnSlug: 'sec-jwt-storage',
    },
    {
      id: 'pool:security:least-priv',
      front: `Least privilege?`,
      back: `Минимальные права роли/сервиса/БД. Снижает blast radius компрометации.`,
      learnSlug: 'net-tls',
    },
    {
      id: 'pool:security:idor',
      front: `IDOR?`,
      back: `Доступ к чужому объекту по угаданному id без проверки владельца. AuthZ на каждый объект.`,
      learnSlug: 'sec-jwt-storage',
    },
    {
      id: 'pool:security:headers',
      front: `Security headers?`,
      back: `CSP, X-Frame-Options/frame-ancestors, nosniff, Referrer-Policy. Не серебряная пуля, но дешёвый слой.`,
      learnSlug: 'net-tls',
    },
    {
      id: 'pool:security:mfa',
      front: `MFA?`,
      back: `Второй фактор снижает риск украденного пароля. UX vs безопасность — внедрять на критичных действиях.`,
      learnSlug: 'sec-jwt-storage',
    },
    {
      id: 'pool:security:deps',
      front: `Уязвимости зависимостей?`,
      back: `Аудит/renovate, pin версий, реагирование на CVE. Supply chain — часть threat model.`,
      learnSlug: 'net-tls',
    },
    {
      id: 'pool:security:rate-limit',
      front: `Rate limiting?`,
      back: `Защита auth/API от брутфорса и абьюза. По IP/user/ключа с понятным 429.`,
      learnSlug: 'sec-jwt-storage',
    },
    {
      id: 'pool:security:logging-pii',
      front: `PII в логах?`,
      back: `Не логировать пароли/токены/полные карты. Политика ретенции и доступ к логам.`,
      learnSlug: 'net-tls',
    },
  ],
}
