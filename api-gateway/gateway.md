Требуется создать сервис api gateway для перенаправления запросов от сервиса к сервису со следующим функционалом:
CORS
    доступ get post разрешен с сервиса ui-app
    URL остальных сервисов должны быть перечислены в конфигурационном файле  
маршрутизация запросов
    сервис auth
        перенаправить запросы с сервиса ui-app на сервис auth
        запрос с ui-app post /auth/register нужно преобразовать в post /register на сервис auth
        запрос с ui-app post /auth/login нужно преобразовать в post /login на сервис auth
        запрос с ui-app post /auth/refresh нужно преобразовать в post /refresh на сервис auth
        запрос с ui-app post /auth/logout нужно преобразовать в post /logout на сервис auth
        запрос с ui-app get /auth/profile нужно преобразовать в get /profile на сервис auth
        запрос с ui-app post /auth/profile нужно преобразовать в put /profile на сервис auth
        запрос с ui-app post /auth/verify нужно преобразовать в post /verify на сервис auth
        запрос с ui-app post /auth/reset-password нужно преобразовать в post /reset-password на сервис auth      
        запрос с ui-app post /auth/all-logout нужно преобразовать в post /all-logout на сервис auth     
        
    сервис core
        общие запросы
            запрос с ui-app get /core/healthchecks нужно преобразовать в get /healthchecks на сервис core
            запрос с ui-app get /core/statistics нужно преобразовать в get /statistics на сервис core
        для работы с WP
            запрос с ui-app GET /wp/profile нужно преобразовать в  GET /wp/profile на сервис core
            запрос с ui-app POST /wp/profile нужно преобразовать в POST /wp/profile на сервис core
            запрос с ui-app POST /wp/post нужно преобразовать в  POST /wp/post на сервис core
        для работы с TG
            запрос с ui-app GET /tg/profile нужно преобразовать в  GET /tg/profile на сервис core
            запрос с ui-app POST /tg/profile нужно преобразовать в POST /tg/profile на сервис core
            запрос с ui-app POST /tg/post нужно преобразовать в  POST /tg/post на сервис core
        для работы с TW
            запрос с ui-app GET /tw/profile нужно преобразовать в  GET /tw/profile на сервис core
            запрос с ui-app POST /tw/profile нужно преобразовать в POST /tw/profile на сервис core
            запрос с ui-app POST /tw/post нужно преобразовать в  POST /tw/post на сервис core
        для работы с VK
            запрос с ui-app GET /vk/profile нужно преобразовать в  GET /vk/profile на сервис core
            запрос с ui-app POST /vk/profile нужно преобразовать в POST /vk/profile на сервис core
            запрос с ui-app POST /vk/post нужно преобразовать в  POST /vk/post на сервис core       
        для работы с curl
            запрос с ui-app GET /curl/settings нужно преобразовать в  GET /curl/settings на сервис core
            запрос с ui-app POST /curl/settings нужно преобразовать в POST /curl/settings на сервис core  
        для работы с cpost
            запрос с ui-app GET /cpost/profile нужно преобразовать в  GET /cpost/profile на сервис core
            запрос с ui-app POST /cpost/profile нужно преобразовать в POST /cpost/profile на сервис core
            запрос с ui-app POST /cpost/post нужно преобразовать в  POST /cpost/post на сервис core


    сервис scheduler
    сервис tg-bot
    сервис vk-bot
    сервис wp-bot
    сервис url-bot
    
аутентификация и авторизация
    запрос пользоватля должен быть с JWT токеном в header
ограничение частоты запросов (Rate Limiting)
    требуется ограничение числа запросов накаждый endpoint со стороны API Gateway
    ограничения должны храниться в конфигурационно файле

