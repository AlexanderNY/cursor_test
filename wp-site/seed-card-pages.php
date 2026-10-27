<?php
/**
 * Personal card pages for the local WordPress lab.
 * Idempotent: updates pages by slug, assigns the menu, sets the static front.
 *
 * Stable lab slugs stay: about, contacts, workspace, reading-notes.
 *
 *   docker cp wp-site/seed-card-pages.php copyparse-wp-site-wordpress-1:/tmp/seed-card-pages.php
 *   docker exec copyparse-wp-site-wordpress-1 php /tmp/seed-card-pages.php
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

/**
 * @param array{slug:string,title:string,content:string,parent?:int,menu_order?:int,excerpt?:string} $item
 */
function card_upsert_page(array $item, int $author_id): int
{
    $parent_id = (int) ($item['parent'] ?? 0);
    $existing = get_posts(
        array(
            'post_type'      => 'page',
            'name'           => $item['slug'],
            'post_parent'    => $parent_id,
            'post_status'    => 'any',
            'posts_per_page' => 1,
        )
    );
    if ($existing === array() && $parent_id === 0) {
        $by_path = get_page_by_path($item['slug'], OBJECT, 'page');
        if ($by_path instanceof WP_Post && (int) $by_path->post_parent === 0) {
            $existing = array($by_path);
        }
    }

    $payload = array(
        'post_type'      => 'page',
        'post_name'      => $item['slug'],
        'post_title'     => $item['title'],
        'post_content'   => $item['content'],
        'post_excerpt'   => $item['excerpt'] ?? '',
        'post_status'    => 'publish',
        'post_author'    => $author_id,
        'post_parent'    => $parent_id,
        'menu_order'     => (int) ($item['menu_order'] ?? 0),
        'comment_status' => 'closed',
        'ping_status'    => 'closed',
    );

    if ($existing !== array()) {
        $payload['ID'] = (int) $existing[0]->ID;
        $page_id = wp_update_post($payload, true);
        $verb = 'updated';
    } else {
        $page_id = wp_insert_post($payload, true);
        $verb = 'created';
    }

    if (is_wp_error($page_id)) {
        fwrite(STDERR, "fail page slug={$item['slug']}: " . $page_id->get_error_message() . "\n");
        exit(1);
    }

    update_post_meta((int) $page_id, '_wp_page_template', 'template-full-width.php');
    echo "{$verb} page slug={$item['slug']} id={$page_id}\n";
    return (int) $page_id;
}

function card_html(string $html): string
{
    return "<!-- wp:html -->\n" . trim($html) . "\n<!-- /wp:html -->";
}

$home_html = card_html(
    <<<'HTML'
<p>Собираю сервисы на Python (FastAPI), React и PostgreSQL. Учу тому же на своём SaaS: где банковские паттерны нужны, а где уже лишние.</p>
<p>МФТИ / МИФИ. Системный аналитик и владелец продукта в FinTech. Свой продукт — <a href="https://www.copyparse.ru">CopyParse</a>.</p>

<h2>Сейчас</h2>
<p>Веду учебный сезон: собрать срез сервиса до Docker Compose и Minikube. Стенд — CopyParse, не отдельный учебный пример. Рядом площадка <a href="https://9to18.ru">9to18.ru</a>: курсы, резюме, портфолио и тренажёры.</p>

<h2>Проекты</h2>
<ul>
<li><a href="/projects/copyparse/"><strong>CopyParse</strong></a> — кросспостинг. Один материал в несколько сетей, очередь в Postgres.</li>
<li><a href="https://9to18.ru/game/learn">Learn</a> — учебные статьи, тесты и карточки Anki.</li>
<li><a href="https://9to18.ru/game/hh-resume">Резюме</a> и <a href="https://9to18.ru/game/portfolio">портфолио</a> — страница, которую можно отправить.</li>
<li><a href="https://9to18.ru/game/code">Тренажёры</a> — Python, SQL и Git в браузере.</li>
<li><a href="https://9to18.ru/game/bowl">Bowl</a> — 2D-игра на Python: чаша, перки, заказы между матчами.</li>
<li><a href="https://9to18.ru/game/mnemonics">Мнемотехники</a> — кодирование ответов к собеседованию.</li>
</ul>
<p><a href="/projects/">Все проекты</a></p>

<h2>Заметки</h2>
<p>Короткие записи о рабочем месте и чтении. Лента живёт отдельно, чтобы тестовая публикация не становилась лицом сайта.</p>
<p><a href="/notes/">К заметкам</a></p>

<h2>Связь</h2>
<ul>
<li><a href="https://github.com/AlexanderNY">GitHub</a> — AlexanderNY</li>
<li><a href="https://9to18.ru/#contacts">9to18.ru</a> — форма на площадке</li>
<li><a href="https://www.copyparse.ru">copyparse.ru</a></li>
</ul>
<p><a href="/resume/">Резюме</a> · <a href="/contacts/">Контакты</a> · <a href="/about/">Обо мне</a></p>
HTML
);

$projects_html = card_html(
    <<<'HTML'
<p>Пет-проекты, которые можно открыть. Полный кейс пока один — CopyParse. Остальные ведут на живые разделы 9to18 и репозитории.</p>

<h2>CopyParse</h2>
<p>Платформа кросспостинга и SMM. Рабочий стенд учебного курса: бренды, каналы, календарь, входящие.</p>
<p>Стек: Python, FastAPI, React, PostgreSQL, Docker, Minikube.</p>
<p><a href="/projects/copyparse/">Кейс</a> · <a href="https://www.copyparse.ru">copyparse.ru</a> · <a href="https://github.com/AlexanderNY/cursor_test">репозиторий</a></p>

<h2>9to18</h2>
<p>Площадка взаимного продвижения и обучения. Плашка открывает сервис, блог сервиса ведётся отдельно.</p>
<p><a href="https://9to18.ru">9to18.ru</a></p>

<h2>Learn</h2>
<p>Учебные статьи одного формата: введение, разделы, схемы, тест и карточки Anki. Лаба по желанию.</p>
<p><a href="https://9to18.ru/game/learn">Открыть Learn</a></p>

<h2>Карта обучения</h2>
<p>Mind map к собеседованию: аналитик, DevOps, разработчик, QA, владелец продукта. Каждый лист — статья Learn.</p>
<p><a href="https://9to18.ru/game/learning-map">Открыть карту</a></p>

<h2>Резюме</h2>
<p>Опросник, шаблон в духе HeadHunter и навыки из пройденных выпусков Learn.</p>
<p><a href="https://9to18.ru/game/hh-resume">Сервис резюме</a> · <a href="/resume/">короткая версия здесь</a></p>

<h2>Портфолио</h2>
<p>Страница, которую можно отправить: задача, что сделано, результат, стек, выпуски Learn.</p>
<p><a href="https://9to18.ru/game/portfolio">Собрать страницу</a></p>

<h2>Тренажёры</h2>
<p>Песочницы в браузере: Python (Pyodide), SQL (SQLite) и симулятор Git. Свободный режим и задачи из Learn.</p>
<p><a href="https://9to18.ru/game/code">Открыть тренажёры</a></p>

<h2>Bowl</h2>
<p>2D-игра на Python в браузере: выживание в чаше, перки, боссы и заказы между матчами.</p>
<p><a href="https://9to18.ru/game/bowl">Открыть Bowl</a></p>

<h2>Мнемотехники</h2>
<p>Тренажёр кодирования для собеседования: акронимы, цепочки, чанкинг и система крючков.</p>
<p><a href="https://9to18.ru/game/mnemonics">Открыть тренажёр</a></p>

<h2>Ранние репозитории</h2>
<ul>
<li><a href="https://github.com/AlexanderNY/python-notebook">python-notebook</a> — ноутбуки Jupyter до CopyParse.</li>
<li><a href="https://github.com/AlexanderNY/py">py</a> — скрипты Python и первый Telegram-бот на Telethon.</li>
</ul>
HTML
);

$copyparse_html = card_html(
    <<<'HTML'
<p>Один человек собирает SaaS кросспостинга и сразу показывает, где слой из большой компании нужен, а где уже мешает.</p>

<h2>Задача</h2>
<p>Публиковать один материал в Telegram, VK, WordPress и другие сети. Личный голос и продукт при этом не склеивать: учебный канал и релизы CopyParse живут отдельно.</p>

<h2>Что сделано</h2>
<p>Шлюз, авторизация, ядро и боты площадок. Очередь — статусы в PostgreSQL, без отдельного брокера. Интерфейс на React: бренды, каналы, календарь, входящие. Локальный WordPress на этом адресе — стенд, куда публикация доезжает и где её можно обновить.</p>

<h2>Результат</h2>
<p>Рабочий сайт <a href="https://www.copyparse.ru">copyparse.ru</a> и стенд учебного сезона. На нём видно путь от идеи до Compose и Minikube, без обещания поднять весь прод за один выпуск.</p>

<h2>Стек</h2>
<p>Python, FastAPI, Pydantic, React, PostgreSQL, Docker, Compose, Minikube.</p>

<h2>Роль</h2>
<p>Service Desk, затем риски, системный анализ и продукт в FinTech, затем свой сервис. Код с июня 2026 — в отдельном репозитории, до этого папка жила в <a href="https://github.com/AlexanderNY/py">py</a>.</p>

<p><a href="https://github.com/AlexanderNY/cursor_test">GitHub</a> · <a href="https://www.copyparse.ru">copyparse.ru</a> · <a href="/projects/">Все проекты</a></p>
HTML
);

$resume_html = card_html(
    <<<'HTML'
<p>Короткая публичная версия. Даты мест работы, зарплату и PDF здесь не дублирую: канон собирается в сервисе резюме на 9to18.</p>

<h2>Специализация</h2>
<p>Системный аналитик и владелец продукта. Собираю сервисы на Python, React и PostgreSQL. Свой продукт — платформа кросспостинга CopyParse.</p>

<h2>Путь</h2>
<p>Service Desk → риски → системный анализ и продукт в FinTech → свой SaaS.</p>

<h2>Образование</h2>
<p>МФТИ / МИФИ.</p>

<h2>Стек</h2>
<ul>
<li>Python, FastAPI, Pydantic</li>
<li>React</li>
<li>PostgreSQL</li>
<li>Docker, Compose, Minikube</li>
<li>JWT, очереди на статусах в базе</li>
</ul>

<h2>Где посмотреть</h2>
<ul>
<li><a href="https://github.com/AlexanderNY">GitHub</a> — AlexanderNY</li>
<li><a href="https://www.copyparse.ru">copyparse.ru</a> — продукт</li>
<li><a href="https://9to18.ru/game/hh-resume">Резюме на 9to18</a> — опросник, шаблон и PDF</li>
<li><a href="https://9to18.ru/game/portfolio">Портфолио на 9to18</a> — кейс, который можно отправить</li>
<li><a href="/projects/copyparse/">Кейс CopyParse</a> на этом сайте</li>
</ul>
HTML
);

$notes_html = card_html(
    <<<'HTML'
<p>Лента заметок. Текст этой страницы в теме не показывается: WordPress отдаёт здесь список записей.</p>
HTML
);

$contacts_html = card_html(
    <<<'HTML'
<p>Этот адрес — локальная лаборатория публикаций. Форма и почта отсюда никуда не уходят. Написать можно на площадке, код лежит на GitHub.</p>
<ul>
<li><a href="https://github.com/AlexanderNY">GitHub</a> — AlexanderNY</li>
<li><a href="https://9to18.ru/#contacts">Форма на 9to18.ru</a></li>
<li><a href="https://www.copyparse.ru">copyparse.ru</a></li>
<li><a href="/resume/">Резюме</a></li>
<li><a href="/projects/">Проекты</a></li>
</ul>
HTML
);

$about_html = card_html(
    <<<'HTML'
<p>Александр. Собираю сервисы на Python, React и Postgres и на CopyParse показываю, где паттерн из банка нужен, а где вреден.</p>
<p>Сайт на WordPress — лаборатория. Сюда CopyParse публикует страницы и записи, чтобы проверить создание и обновление. Визитка — главная, проекты и резюме. Заметки вынесены отдельно, чтобы тестовый пост не занимал первый экран.</p>
<ul>
<li><a href="/">Главная</a></li>
<li><a href="/projects/">Проекты</a></li>
<li><a href="/resume/">Резюме</a></li>
<li><a href="/notes/">Заметки</a></li>
<li><a href="/contacts/">Контакты</a></li>
</ul>
HTML
);

$home_id = card_upsert_page(
    array(
        'slug'       => 'home',
        'title'      => 'Александр',
        'content'    => $home_html,
        'menu_order' => 1,
    ),
    $author_id
);
$projects_id = card_upsert_page(
    array(
        'slug'       => 'projects',
        'title'      => 'Проекты',
        'content'    => $projects_html,
        'menu_order' => 2,
    ),
    $author_id
);
$copyparse_id = card_upsert_page(
    array(
        'slug'       => 'copyparse',
        'title'      => 'CopyParse',
        'content'    => $copyparse_html,
        'parent'     => $projects_id,
        'menu_order' => 1,
    ),
    $author_id
);
$resume_id = card_upsert_page(
    array(
        'slug'       => 'resume',
        'title'      => 'Резюме',
        'content'    => $resume_html,
        'menu_order' => 3,
    ),
    $author_id
);
$notes_id = card_upsert_page(
    array(
        'slug'       => 'notes',
        'title'      => 'Заметки',
        'content'    => $notes_html,
        'excerpt'    => 'Короткие записи о работе, чтении и проектах. Сюда же попадает публикация из лаборатории CopyParse.',
        'menu_order' => 4,
    ),
    $author_id
);
$contacts_id = card_upsert_page(
    array(
        'slug'       => 'contacts',
        'title'      => 'Контакты',
        'content'    => $contacts_html,
        'menu_order' => 5,
    ),
    $author_id
);
$about_id = card_upsert_page(
    array(
        'slug'       => 'about',
        'title'      => 'Обо мне',
        'content'    => $about_html,
        'menu_order' => 6,
    ),
    $author_id
);

foreach (array('sample-page', 'sample-page-2') as $demo_slug) {
    $demo = get_page_by_path($demo_slug, OBJECT, 'page');
    if ($demo instanceof WP_Post && $demo->post_status !== 'draft') {
        wp_update_post(
            array(
                'ID'          => $demo->ID,
                'post_status' => 'draft',
            )
        );
        echo "draft page slug={$demo_slug} id={$demo->ID}\n";
    }
}

update_option('show_on_front', 'page');
update_option('page_on_front', $home_id);
update_option('page_for_posts', $notes_id);
update_option('blogdescription', 'Собираю сервисы. Локальная лаборатория публикаций.');
set_theme_mod('newsum_header_show_ticker', false);

$sidebars = wp_get_sidebars_widgets();
if (isset($sidebars['sidebar-1']) && is_array($sidebars['sidebar-1'])) {
    $sidebars['sidebar-1'] = array_values(
        array_filter(
            $sidebars['sidebar-1'],
            static function ($widget_id): bool {
                return $widget_id !== 'block-5';
            }
        )
    );
    wp_set_sidebars_widgets($sidebars);
    echo "sidebar archives widget removed\n";
}

/**
 * @param list<array{title:string,id:int}> $items
 * @param list<string> $locations
 */
function card_assign_menu(string $name, array $items, array $locations): void
{
    $menu = wp_get_nav_menu_object($name);
    if ($menu instanceof WP_Term) {
        $menu_id = (int) $menu->term_id;
        $existing = wp_get_nav_menu_items($menu_id);
        if (is_array($existing)) {
            foreach ($existing as $item) {
                wp_delete_post((int) $item->ID, true);
            }
        }
    } else {
        $created = wp_create_nav_menu($name);
        if (is_wp_error($created)) {
            fwrite(STDERR, "fail menu {$name}: " . $created->get_error_message() . "\n");
            exit(1);
        }
        $menu_id = (int) $created;
    }

    foreach ($items as $index => $item) {
        $result = wp_update_nav_menu_item(
            $menu_id,
            0,
            array(
                'menu-item-title'     => $item['title'],
                'menu-item-object'    => 'page',
                'menu-item-object-id' => $item['id'],
                'menu-item-type'      => 'post_type',
                'menu-item-status'    => 'publish',
                'menu-item-position'  => $index + 1,
            )
        );
        if (is_wp_error($result)) {
            fwrite(STDERR, "fail menu item {$item['title']}: " . $result->get_error_message() . "\n");
            exit(1);
        }
    }

    $assigned = get_theme_mod('nav_menu_locations');
    if (!is_array($assigned)) {
        $assigned = array();
    }
    foreach ($locations as $location) {
        $assigned[$location] = $menu_id;
    }
    set_theme_mod('nav_menu_locations', $assigned);
    echo "menu {$name} id={$menu_id} items=" . count($items) . "\n";
}

card_assign_menu(
    'Визитка',
    array(
        array('title' => 'Главная', 'id' => $home_id),
        array('title' => 'Проекты', 'id' => $projects_id),
        array('title' => 'Резюме', 'id' => $resume_id),
        array('title' => 'Заметки', 'id' => $notes_id),
        array('title' => 'Контакты', 'id' => $contacts_id),
        array('title' => 'Обо мне', 'id' => $about_id),
    ),
    array('menu-1', 'drawer-menu')
);

$privacy = get_page_by_path('privacy-policy', OBJECT, 'page');
$footer_items = array(
    array('title' => 'Контакты', 'id' => $contacts_id),
);
if ($privacy instanceof WP_Post) {
    $footer_items[] = array('title' => 'Политика конфиденциальности', 'id' => (int) $privacy->ID);
}
card_assign_menu('Подвал', $footer_items, array('footer-menu'));

flush_rewrite_rules(false);

echo "front={$home_id} notes={$notes_id} projects={$projects_id} copyparse={$copyparse_id}\n";
echo "done\n";
