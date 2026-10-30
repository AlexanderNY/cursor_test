<?php
/**
 * Navigation and styles for Twenty Twenty-Five on the local lab.
 * Idempotent. Run after the theme is active and seed-card-pages.php has run.
 *
 *   docker cp wp-site/setup-tt5-appearance.php copyparse-wp-site-wordpress-1:/tmp/setup-tt5-appearance.php
 *   docker exec copyparse-wp-site-wordpress-1 php /tmp/setup-tt5-appearance.php
 */
require '/var/www/html/wp-load.php';

if (get_stylesheet() !== 'twentytwentyfive') {
    fwrite(STDERR, 'Active theme is ' . get_stylesheet() . ", expected twentytwentyfive\n");
    exit(1);
}

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
wp_set_current_user((int) $admins[0]->ID);

/**
 * @return array{home:int,projects:int,copyparse:int,resume:int,notes:int,contacts:int,about:int}
 */
function card_page_ids(): array
{
    $wanted = array(
        'home'      => array('home', 0),
        'projects'  => array('projects', 0),
        'resume'    => array('resume', 0),
        'notes'     => array('notes', 0),
        'contacts'  => array('contacts', 0),
        'about'     => array('about', 0),
    );
    $ids = array();
    foreach ($wanted as $key => $spec) {
        $found = get_posts(
            array(
                'post_type'      => 'page',
                'name'           => $spec[0],
                'post_parent'    => $spec[1],
                'post_status'    => 'publish',
                'posts_per_page' => 1,
            )
        );
        if ($found === array()) {
            fwrite(STDERR, "missing page {$spec[0]}\n");
            exit(1);
        }
        $ids[$key] = (int) $found[0]->ID;
    }
    $projects = $ids['projects'];
    $child = get_posts(
        array(
            'post_type'      => 'page',
            'name'           => 'copyparse',
            'post_parent'    => $projects,
            'post_status'    => 'publish',
            'posts_per_page' => 1,
        )
    );
    if ($child === array()) {
        fwrite(STDERR, "missing page projects/copyparse\n");
        exit(1);
    }
    $ids['copyparse'] = (int) $child[0]->ID;
    return $ids;
}

function card_nav_link(string $label, int $page_id, bool $top_level, ?string $url = null): string
{
    $attrs = array(
        'label'          => $label,
        'type'           => 'page',
        'id'             => $page_id,
        'url'            => $url ?? get_permalink($page_id),
        'kind'           => 'post-type',
        'isTopLevelLink' => $top_level,
    );
    $json = wp_json_encode($attrs, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    return "<!-- wp:navigation-link {$json} /-->";
}

function card_custom_link(string $label, string $url): string
{
    $json = wp_json_encode(
        array(
            'label'          => $label,
            'url'            => $url,
            'kind'           => 'custom',
            'isTopLevelLink' => true,
        ),
        JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES
    );
    return "<!-- wp:navigation-link {$json} /-->";
}

$pages = card_page_ids();

$projects_attrs = wp_json_encode(
    array(
        'label' => 'Проекты',
        'type'  => 'page',
        'id'    => $pages['projects'],
        'url'   => get_permalink($pages['projects']),
        'kind'  => 'post-type',
    ),
    JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES
);

$nav_content = implode(
    "\n\n",
    array(
        card_nav_link('Главная', $pages['home'], true, home_url('/')),
        "<!-- wp:navigation-submenu {$projects_attrs} -->\n"
            . card_nav_link('CopyParse', $pages['copyparse'], false) . "\n"
            . '<!-- /wp:navigation-submenu -->',
        card_nav_link('Резюме', $pages['resume'], true),
        card_nav_link('Заметки', $pages['notes'], true),
        card_nav_link('Контакты', $pages['contacts'], true),
        card_nav_link('Обо мне', $pages['about'], true),
    )
);

$nav_posts = get_posts(
    array(
        'post_type'      => 'wp_navigation',
        'name'           => 'navigation',
        'post_status'    => 'any',
        'posts_per_page' => 1,
    )
);
if ($nav_posts === array()) {
    $nav_id = wp_insert_post(
        array(
            'post_type'    => 'wp_navigation',
            'post_status'  => 'publish',
            'post_title'   => 'Navigation',
            'post_name'    => 'navigation',
            'post_content' => $nav_content,
        ),
        true
    );
} else {
    $nav_id = wp_update_post(
        array(
            'ID'           => (int) $nav_posts[0]->ID,
            'post_content' => $nav_content,
        ),
        true
    );
}
if (is_wp_error($nav_id)) {
    fwrite(STDERR, 'nav: ' . $nav_id->get_error_message() . "\n");
    exit(1);
}
$nav_id = (int) $nav_id;
echo "navigation id={$nav_id}\n";

$header = <<<HTML
<!-- wp:group {"align":"full","style":{"border":{"bottom":{"color":"var:preset|color|accent-6","width":"1px","style":"solid"}},"spacing":{"padding":{"top":"var:preset|spacing|30","bottom":"var:preset|spacing|30"}}},"layout":{"type":"default"}} -->
<div class="wp-block-group alignfull" style="border-bottom-color:var(--wp--preset--color--accent-6);border-bottom-width:1px;border-bottom-style:solid;padding-top:var(--wp--preset--spacing--30);padding-bottom:var(--wp--preset--spacing--30)"><!-- wp:group {"layout":{"type":"constrained"}} -->
<div class="wp-block-group"><!-- wp:group {"align":"wide","layout":{"type":"flex","flexWrap":"nowrap","justifyContent":"space-between","verticalAlignment":"center"}} -->
<div class="wp-block-group alignwide"><!-- wp:site-title {"level":0} /-->

<!-- wp:navigation {"ref":{$nav_id},"overlayMenu":"mobile","overlayBackgroundColor":"base","overlayTextColor":"contrast","fontSize":"small","layout":{"type":"flex","justifyContent":"right","flexWrap":"wrap"}} /--></div>
<!-- /wp:group --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->
HTML;

$external = implode(
    "\n\n",
    array(
        card_custom_link('GitHub', 'https://github.com/AlexanderNY'),
        card_custom_link('9to18.ru', 'https://9to18.ru'),
        card_custom_link('copyparse.ru', 'https://www.copyparse.ru'),
    )
);

$footer = <<<HTML
<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|60","bottom":"var:preset|spacing|50"}},"color":{"background":"var:preset|color|accent-5"}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group has-background" style="background-color:var(--wp--preset--color--accent-5);padding-top:var(--wp--preset--spacing--60);padding-bottom:var(--wp--preset--spacing--50)"><!-- wp:group {"align":"wide","style":{"spacing":{"blockGap":"var:preset|spacing|40"}},"layout":{"type":"constrained","justifyContent":"left"}} -->
<div class="wp-block-group alignwide"><!-- wp:site-title {"level":2,"fontSize":"large"} /-->

<!-- wp:site-tagline /-->

<!-- wp:navigation {"ref":{$nav_id},"overlayMenu":"never","fontSize":"small","layout":{"type":"flex","orientation":"horizontal","flexWrap":"wrap","justifyContent":"left"}} /-->

<!-- wp:navigation {"overlayMenu":"never","fontSize":"small","layout":{"type":"flex","orientation":"horizontal","flexWrap":"wrap","justifyContent":"left"}} -->
{$external}
<!-- /wp:navigation -->

<!-- wp:paragraph {"fontSize":"small"} -->
<p class="has-small-font-size">Локальная лаборатория публикаций</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->
HTML;

$page_template = <<<'HTML'
<!-- wp:template-part {"slug":"header"} /-->

<!-- wp:group {"tagName":"main","layout":{"type":"constrained"}} -->
<main class="wp-block-group">
	<!-- wp:group {"align":"full","style":{"spacing":{"padding":{"top":"var:preset|spacing|50","bottom":"var:preset|spacing|60"}}},"layout":{"type":"constrained"}} -->
	<div class="wp-block-group alignfull" style="padding-top:var(--wp--preset--spacing--50);padding-bottom:var(--wp--preset--spacing--60)">
		<!-- wp:post-title {"level":1} /-->
		<!-- wp:post-content {"align":"full","layout":{"type":"constrained"}} /-->
	</div>
	<!-- /wp:group -->
</main>
<!-- /wp:group -->

<!-- wp:template-part {"slug":"footer"} /-->
HTML;

$home_template = <<<'HTML'
<!-- wp:template-part {"slug":"header"} /-->

<!-- wp:group {"tagName":"main","layout":{"type":"constrained"}} -->
<main class="wp-block-group">
	<!-- wp:group {"align":"full","style":{"spacing":{"padding":{"top":"var:preset|spacing|50","bottom":"0"}}},"layout":{"type":"constrained"}} -->
	<div class="wp-block-group alignfull" style="padding-top:var(--wp--preset--spacing--50);padding-bottom:0">
		<!-- wp:heading {"level":1} -->
		<h1 class="wp-block-heading">Заметки</h1>
		<!-- /wp:heading -->

		<!-- wp:paragraph -->
		<p>Короткие записи о работе, чтении и проектах. Сюда попадает публикация из лаборатории.</p>
		<!-- /wp:paragraph -->
	</div>
	<!-- /wp:group -->

	<!-- wp:query {"query":{"perPage":10,"pages":0,"offset":0,"postType":"post","order":"desc","orderBy":"date","author":"","search":"","exclude":[],"sticky":"","inherit":true},"align":"full","layout":{"type":"default"}} -->
	<div class="wp-block-query alignfull">
		<!-- wp:post-template {"align":"full","layout":{"type":"default"}} -->
			<!-- wp:group {"style":{"spacing":{"padding":{"top":"var:preset|spacing|40","bottom":"var:preset|spacing|40"},"blockGap":"var:preset|spacing|20"},"border":{"bottom":{"color":"var:preset|color|accent-6","width":"1px","style":"solid"}}},"layout":{"type":"constrained"}} -->
			<div class="wp-block-group" style="border-bottom-color:var(--wp--preset--color--accent-6);border-bottom-width:1px;border-bottom-style:solid;padding-top:var(--wp--preset--spacing--40);padding-bottom:var(--wp--preset--spacing--40)">
				<!-- wp:post-title {"isLink":true,"fontSize":"x-large"} /-->
				<!-- wp:post-excerpt {"moreText":"Читать","excerptLength":32} /-->
				<!-- wp:post-date {"fontSize":"small"} /-->
			</div>
			<!-- /wp:group -->
		<!-- /wp:post-template -->

		<!-- wp:query-pagination {"paginationArrow":"arrow","layout":{"type":"flex","justifyContent":"space-between"}} -->
			<!-- wp:query-pagination-previous /-->
			<!-- wp:query-pagination-next /-->
		<!-- /wp:query-pagination -->
	</div>
	<!-- /wp:query -->
</main>
<!-- /wp:group -->

<!-- wp:template-part {"slug":"footer"} /-->
HTML;

/**
 * @param array<string, string> $taxonomies
 */
function card_upsert_theme_post(string $post_type, string $slug, string $title, string $content, array $taxonomies): int
{
    $existing = get_posts(
        array(
            'post_type'      => $post_type,
            'name'           => $slug,
            'post_status'    => 'any',
            'posts_per_page' => 1,
        )
    );
    $payload = array(
        'post_type'    => $post_type,
        'post_name'    => $slug,
        'post_title'   => $title,
        'post_status'  => 'publish',
        'post_content' => $content,
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
        fwrite(STDERR, "{$post_type} {$slug}: " . $post_id->get_error_message() . "\n");
        exit(1);
    }
    $post_id = (int) $post_id;
    foreach ($taxonomies as $taxonomy => $term) {
        $result = wp_set_object_terms($post_id, $term, $taxonomy);
        if (is_wp_error($result)) {
            fwrite(STDERR, "term {$taxonomy}={$term}: " . $result->get_error_message() . "\n");
            exit(1);
        }
    }
    echo "{$verb} {$post_type} {$slug} id={$post_id}\n";
    return $post_id;
}

card_upsert_theme_post(
    'wp_template_part',
    'header',
    'Header',
    $header,
    array(
        'wp_theme'              => 'twentytwentyfive',
        'wp_template_part_area' => 'header',
    )
);
card_upsert_theme_post(
    'wp_template_part',
    'footer',
    'Footer',
    $footer,
    array(
        'wp_theme'              => 'twentytwentyfive',
        'wp_template_part_area' => 'footer',
    )
);
card_upsert_theme_post(
    'wp_template',
    'page',
    'Page',
    $page_template,
    array(
        'wp_theme' => 'twentytwentyfive',
    )
);
card_upsert_theme_post(
    'wp_template',
    'home',
    'Blog Home',
    $home_template,
    array(
        'wp_theme' => 'twentytwentyfive',
    )
);

$styles = array(
    'version'                     => 3,
    'isGlobalStylesUserThemeJSON' => true,
    'settings'                    => array(
        'color'  => array(
            'palette' => array(
                'theme' => array(
                    array('slug' => 'base', 'color' => '#f6f3ec', 'name' => 'Base'),
                    array('slug' => 'contrast', 'color' => '#1c1917', 'name' => 'Contrast'),
                    array('slug' => 'accent-1', 'color' => '#1d6b45', 'name' => 'Accent 1'),
                    array('slug' => 'accent-2', 'color' => '#e4efe8', 'name' => 'Accent 2'),
                    array('slug' => 'accent-3', 'color' => '#1d6b45', 'name' => 'Accent 3'),
                    array('slug' => 'accent-4', 'color' => '#6b6560', 'name' => 'Accent 4'),
                    array('slug' => 'accent-5', 'color' => '#efeae1', 'name' => 'Accent 5'),
                    array(
                        'slug'  => 'accent-6',
                        'color' => 'color-mix(in srgb, currentColor 16%, transparent)',
                        'name'  => 'Accent 6',
                    ),
                ),
            ),
        ),
        'layout' => array(
            'contentSize' => '720px',
            'wideSize'    => '1120px',
        ),
    ),
    'styles'                      => array(
        'color'      => array(
            'background' => 'var:preset|color|base',
            'text'       => 'var:preset|color|contrast',
        ),
        'typography' => array(
            'fontFamily'  => 'var:preset|font-family|manrope',
            'fontSize'    => 'var:preset|font-size|medium',
            'fontWeight'  => '400',
            'lineHeight'  => '1.6',
            'letterSpacing' => '0px',
        ),
        'elements'   => array(
            'link'    => array(
                'color'      => array('text' => 'var:preset|color|accent-1'),
                'typography' => array('textDecoration' => 'underline'),
                ':hover'     => array(
                    'typography' => array('textDecoration' => 'none'),
                ),
            ),
            'heading' => array(
                'typography' => array(
                    'fontWeight'   => '500',
                    'lineHeight'   => '1.2',
                    'letterSpacing' => '-0.02em',
                ),
            ),
            'h1'      => array(
                'typography' => array('fontSize' => 'var:preset|font-size|xx-large'),
            ),
        ),
        'blocks'     => array(
            'core/navigation' => array(
                'typography' => array(
                    'fontSize'   => 'var:preset|font-size|small',
                    'fontWeight' => '500',
                ),
                'elements'   => array(
                    'link' => array(
                        'color'      => array('text' => 'var:preset|color|contrast'),
                        ':hover'     => array(
                            'typography' => array('textDecoration' => 'underline'),
                        ),
                        'typography' => array('textDecoration' => 'none'),
                    ),
                ),
            ),
            'core/site-title' => array(
                'typography' => array(
                    'fontSize'   => 'var:preset|font-size|medium',
                    'fontWeight' => '600',
                ),
                'elements'   => array(
                    'link' => array(
                        'color'      => array('text' => 'var:preset|color|contrast'),
                        'typography' => array('textDecoration' => 'none'),
                    ),
                ),
            ),
        ),
    ),
);

$style_posts = get_posts(
    array(
        'post_type'      => 'wp_global_styles',
        'name'           => 'wp-global-styles-twentytwentyfive',
        'post_status'    => 'any',
        'posts_per_page' => 1,
    )
);
$style_json = wp_json_encode($styles, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
if ($style_posts === array()) {
    $style_id = wp_insert_post(
        array(
            'post_type'    => 'wp_global_styles',
            'post_name'    => 'wp-global-styles-twentytwentyfive',
            'post_title'   => 'Custom Styles',
            'post_status'  => 'publish',
            'post_content' => $style_json,
        ),
        true
    );
} else {
    $style_id = wp_update_post(
        array(
            'ID'           => (int) $style_posts[0]->ID,
            'post_content' => $style_json,
        ),
        true
    );
}
if (is_wp_error($style_id)) {
    fwrite(STDERR, 'styles: ' . $style_id->get_error_message() . "\n");
    exit(1);
}
wp_set_object_terms((int) $style_id, 'twentytwentyfive', 'wp_theme');
echo "styles id={$style_id}\n";

foreach ($pages as $page_id) {
    $template = get_post_meta($page_id, '_wp_page_template', true);
    if ($template === 'template-full-width.php') {
        delete_post_meta($page_id, '_wp_page_template');
        echo "cleared old template on page {$page_id}\n";
    }
}

wp_cache_flush();
echo "done\n";
