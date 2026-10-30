<?php
/**
 * Two example notes about how CopyParse was built.
 * Idempotent: updates the same slugs.
 *
 *   docker cp wp-site/seed-copyparse-notes.php copyparse-wp-site-wordpress-1:/tmp/seed-copyparse-notes.php
 *   docker exec copyparse-wp-site-wordpress-1 php /tmp/seed-copyparse-notes.php
 */
require '/var/www/html/wp-load.php';

$admins = get_users(
    array(
        'role'    => 'administrator',
        'number'  => 1,
        'orderby' => 'ID',
        'order'   => 'ASC',
    )
);
if (empty($admins)) {
    fwrite(STDERR, "No administrator found\n");
    exit(1);
}
$author_id = (int) $admins[0]->ID;
wp_set_current_user($author_id);

$category = wp_insert_term(
    'Развитие CopyParse',
    'category',
    array(
        'slug'        => 'copyparse',
        'description' => 'Заметки о том, как собирался сервис.',
    )
);
if (is_wp_error($category)) {
    if ($category->get_error_code() !== 'term_exists') {
        fwrite(STDERR, 'category: ' . $category->get_error_message() . "\n");
        exit(1);
    }
    $category_id = (int) $category->get_error_data('term_exists');
} else {
    $category_id = (int) $category['term_id'];
}

$posts = array(
    array(
        'slug'    => 'copyparse-boxes',
        'title'   => 'Коммит «cursor test» сервисом не был',
        'excerpt' => '1 января в диффе лежали четыре файла правил редактора. Кнопку «создать пост» я нарисовал раньше, чем появился хоть один бот.',
        'content' => <<<'HTML'
<p>До января 2026 кросспостера не было. Были ноутбуки Jupyter и папка <code>bot/</code> в репозитории <a href="https://github.com/AlexanderNY/py">py</a>: один скрипт на Telethon, который сам ходил в Telegram. Второй пользователь, статус «собрали / готово / опубликовано» и вторая площадка в этот скрипт не помещались. Я ещё какое-то время называл это заделом сервиса. Это был просто скрипт.</p>
<p>1 января коммит <code>feb6f841</code> называется <code>cursor test</code>. Открыл дифф и нашёл четыре файла правил Cursor: FastAPI, микросервисы, скрейпинг, React. Папки <code>api-gateway</code> там нет. Первая ошибка года: принять правила редактора за старт архитектуры. Продукт начался в этом месяце, но в тот день в git лежала инструкция, как мне писать код.</p>
<p>7 января, коммит <code>c0d145b9</code> (<code>cursor test with fastapi</code>), в <code>py/cursor_test</code> появились четыре каталога: <code>api-gateway</code>, <code>auth</code>, <code>core</code>, <code>ui-app</code>. 10 января сообщение ещё честнее само по себе и пустее по факту: «масштабный рефакторинг и разделение на сервисы». В шлюзе уже был набросок маршрутов WordPress, а Telegram всё ещё жил планом в markdown. Бот сбора сообщений в базу в тот день не появился.</p>
<p>16 января я повторил ту же ошибку крупнее. В шлюз легли маршруты <code>tg</code>, <code>vk</code>, <code>tw</code>, <code>cpost</code>, в интерфейсе — страница создания поста. Живых ботов под эти сети в коммите не было. Кнопка VK в меню и публикация в VK — разные недели. 23 января завёлся экспериментальный <code>selectcb</code>: полезен для пробы экрана и легко притворяется частью продукта, если не подписать, что это проба.</p>
<p>Первый замкнутый контур собрался кусками, не пачкой. 25 января — <code>scheduler</code> и <code>wp-bot</code>. 6 февраля у <code>tg-bot</code> появились свои <code>config.py</code>, <code>database.py</code> и роутеры: это уже не скрипт из <code>bot/</code>. 8 февраля добавился <code>url-bot</code>, и только после двух живых площадок. Пока одна публикация не доходит до строки в Postgres, вторая площадка размножает дыру.</p>
<p>В марте дерево опять соврало объёмом. 6-го в один коммит упали <code>vk-bot</code>, <code>th-bot</code> и каталог <code>k8s</code> на десятки файлов. Папка манифестов выглядела как «мы в Kubernetes». Стенд по-прежнему поднимался через Compose. 9 марта рядом оказались <code>cv/</code> и <code>portfolio-site</code>: личные файлы в том же git, дифф читать стало больно. 18 марта графики уехали в отдельный <code>graphs-vite-app</code>, чтобы не ломать основной интерфейс. К июню этой гипотезы в корне уже не было. Эксперимент имеет право умереть.</p>
<p>22 июня на GitHub появился <a href="https://github.com/AlexanderNY/cursor_test">AlexanderNY/cursor_test</a>. Initial commit на следующий день — снимок уже собранного кросспостера, переезд из <code>py/cursor_test</code>. Январь–июнь остались в старом репозитории. Если датировать продукт днём нового git, полгода истории пропадают. Свой репозиторий упростил деплой. Днём рождения он не стал.</p>
<p>Сейчас браузер ходит в UI, наружу смотрит шлюз, токены лежат в auth, посты — в core. До этой схемы я несколько раз рисовал фасад раньше комнаты. Кейс — на странице <a href="/projects/copyparse/">CopyParse</a>.</p>
HTML,
    ),
    array(
        'slug'    => 'copyparse-queue',
        'title'   => 'Коммит «всё пропало» был очередью',
        'excerpt' => '20 февраля сообщение коммита звучало как авария. В диффе — collector, processor и ни одной Kafka.',
        'content' => <<<'HTML'
<p>20 февраля коммит <code>75e7d55b</code> подписан «всё пропало». По сообщению я бы искал откат. По диффу там +5132 / −185 строк: новые каталоги <code>collector</code> и <code>processor</code>, правки <code>tg-bot</code> и интерфейса. Сообщения коммитов в этом репозитории почти все бессодержательные, этот хотя бы эмоциональный. Смотреть пришлось файлы.</p>
<p>До этого дня публикация была набором сервисов, которые как-то договаривались. После него появилась цепочка, которую можно ткнуть пальцем: собрать → обработать → разложить по целям → опубликовать. Статусы лежат в <code>posts</code> и в таблицах площадок. Воркер забирает строку через <code>FOR UPDATE SKIP LOCKED</code>, чтобы второй экземпляр бота не увёл тот же пост. Отдельной шины в тот день не завезли.</p>
<p>Привычка из FinTech тут мешала. Кажется, что «настоящая» очередь — это Kafka, журнал и десяток подписчиков. У соло-сервиса на одном хосте подписчик один: бот, который и так ходит в ту же Postgres. Redis в CopyParse держит чёрный список JWT. Задачи он не возит. Я несколько раз чуть не поставил брокер «чтобы было как в банке», и каждый раз нагрузка этого не просила.</p>
<p>Дальше очередь обрастала обходами, а не сменой транспорта. После материализации SMM-пост сразу становится <code>ready</code>, и core будит бота коротким <code>POST /internal/publish-now</code>, не дожидаясь следующего опроса раз в полминуты. Итоговый статус <code>published</code> / <code>failed</code> / <code>partial</code> бот приносит отдельным вызовом. Если записать «опубликовано» в момент вставки строки, лента врёт: пост ещё даже не ушёл.</p>
<p>27 сентября в документах появился <code>KAFKA_MIGRATION_PLAN.md</code>. Это была вторая ловушка: план на бумаге легко принять за решение. Очередь постов от плана не сменилась. Брокер имеет смысл, когда строку начинают дёргать независимо биллинг, вебхуки и аналитика или когда блокировки в Postgres перестают успевать. До тех пор план остаётся планом.</p>
<p>Лабораторный WordPress на этом адресе поймал похожую ошибку уже с другой стороны. Тема новостного блога звала архивы через <code>YEAR()</code> и <code>MONTH()</code> — функции MySQL. База здесь PostgreSQL, драйвер PG4WP такой запрос не переваривает, и лента падала с ошибкой синтаксиса прямо в сайдбаре. Виджет архивов пришлось снять. Публикация CopyParse в страницы и записи при этом жива: ей нужен обычный REST, а не виджет календаря из чужой СУБД.</p>
<p>Как устроен контур сейчас — в кейсе <a href="/projects/copyparse/">CopyParse</a>.</p>
HTML,
    ),
);

foreach ($posts as $item) {
    $existing = get_posts(
        array(
            'post_type'      => 'post',
            'name'           => $item['slug'],
            'post_status'    => 'any',
            'posts_per_page' => 1,
        )
    );
    $payload = array(
        'post_type'      => 'post',
        'post_name'      => $item['slug'],
        'post_title'     => $item['title'],
        'post_excerpt'   => $item['excerpt'],
        'post_content'   => trim($item['content']),
        'post_status'    => 'publish',
        'post_author'    => $author_id,
        'comment_status' => 'closed',
        'ping_status'    => 'closed',
        'post_category'  => array($category_id),
    );
    if ($existing !== array()) {
        $payload['ID'] = (int) $existing[0]->ID;
        $post_id = wp_update_post($payload, true);
        $verb = 'updated';
    } else {
        $post_id = wp_insert_post($payload, true);
        $verb = 'created';
    }
    if (is_wp_error($post_id)) {
        fwrite(STDERR, "fail {$item['slug']}: " . $post_id->get_error_message() . "\n");
        exit(1);
    }
    echo "{$verb} post slug={$item['slug']} id={$post_id}\n";
}

echo "done category_id={$category_id}\n";
