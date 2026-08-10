# cursor_test
Тест приложения на cursor IDE

Три деплой-юнита
deploy/ui-edge/ — свой docker-compose.yml, без depends_on на UI; динамический DNS Docker, чтобы edge стартовал до приложений
ui-9to18/ — production multi-stage Dockerfile (static nginx :8200), свой compose; context . (готов к выносу в отдельный repo)
Монорепо copyparse — ui + gateway на edge_net; ui-edge/ui-9to18 убраны из корневого compose
Инфра
Сеть edge_net создана; скрипты: deploy/scripts/create-edge-net.ps1
Инструкция: deploy/DEPLOYMENT.md
Локально всё вместе: docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up -d
TLS 9to18
HTTPS в 9to18.conf
Self-signed сертификаты сгенерированы
Проверка: Host: www.9to18.ru → HTTP 200 и HTTPS 200
Запуск на VM
.\deploy\scripts\create-edge-net.ps1
docker compose up -d                                          # copyparse
docker compose -f ui-9to18/docker-compose.yml up -d --build   # 9to18
docker compose -f deploy/ui-edge/docker-compose.yml up -d     # edge :80/:443
DNS A для обоих доменов на IP VM и боевые сертификаты вместо self-signed — уже на стороне инфраструктуры.
