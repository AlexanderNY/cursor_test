<?php
/**
 * Seed a personal-site sample: 2 pages + 2 posts with stable Latin slugs.
 * Idempotent: skips a slug that already exists.
 *
 *   docker cp wp-site/seed-personal-content.php copyparse-wp-site-wordpress-1:/tmp/seed-personal-content.php
 *   docker exec copyparse-wp-site-wordpress-1 php /tmp/seed-personal-content.php
 */
require '/var/www/html/wp-load.php';

$admins = get_users(
    array(
        'role'   => 'administrator',
        'number' => 1,
        'orderby'=> 'ID',
        'order'  => 'ASC',
    )
);
if (empty($admins)) {
    fwrite(STDERR, "No administrator found\n");
    exit(1);
}
$author_id = (int) $admins[0]->ID;

$items = array(
    array(
        'post_type'    => 'page',
        'post_name'    => 'about',
        'post_title'   => 'Обо мне',
        'post_content' => "<p>Это личный сайт для заметок о работе, чтении и повседневных проектах.</p>\n"
            . "<p>Страница нужна как стабильная цель для тестов публикации и обновления страниц CopyParse.</p>",
    ),
    array(
        'post_type'    => 'page',
        'post_name'    => 'contacts',
        'post_title'   => 'Контакты',
        'post_content' => "<p>Почта для связи: hello@example.local</p>\n"
            . "<p>Сайт локальный и предназначен только для разработки и автотестов — сообщения никуда не уходят.</p>",
    ),
    array(
        'post_type'    => 'post',
        'post_name'    => 'workspace',
        'post_title'   => 'Как устроено рабочее место',
        'post_content' => "<p>Рабочий стол держу простым: один монитор для кода, второй для документации и браузера.</p>\n"
            . "<p>Утром сначала разбираю открытые pull request и письма, потом беру самую крупную задачу дня.</p>\n"
            . "<p>В конце дня оставляю короткий список на завтра, чтобы не начинать с пустого листа.</p>",
    ),
    array(
        'post_type'    => 'post',
        'post_name'    => 'reading-notes',
        'post_title'   => 'Заметки о чтении',
        'post_content' => "<p>Читаю понемногу каждый вечер: техническую статью или главу из книги.</p>\n"
            . "<p>В заметках фиксирую только то, что можно применить на следующей неделе — иначе список быстро разрастается.</p>\n"
            . "<p>Этот пост удобен как образец длинного текста для сбора и публикации через wp-bot.</p>",
    ),
);

foreach ($items as $item) {
    $slug = $item['post_name'];
    $type = $item['post_type'];
    $existing = get_page_by_path($slug, OBJECT, $type);
    if ($existing instanceof WP_Post) {
        echo "skip {$type} slug={$slug} id={$existing->ID}\n";
        continue;
    }

    $post_id = wp_insert_post(
        array(
            'post_type'    => $type,
            'post_name'    => $slug,
            'post_title'   => $item['post_title'],
            'post_content' => $item['post_content'],
            'post_status'  => 'publish',
            'post_author'  => $author_id,
        ),
        true
    );

    if (is_wp_error($post_id)) {
        fwrite(STDERR, "fail {$type} slug={$slug}: " . $post_id->get_error_message() . "\n");
        exit(1);
    }

    echo "created {$type} slug={$slug} id={$post_id}\n";
}

echo "done author_id={$author_id}\n";
