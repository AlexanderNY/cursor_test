-- Разовая миграция (после ввода cpost_posts / tw_posts):
-- перенос старых строк из posts, созданных напрямую через create_post (post_type = cpost | tw).
--
-- Внимание: id в posts и id в cpost_posts/tw_posts разойдутся; клиентам нужно заново получить списки
-- из API /cpost/posts — идентификаторы теперь из платформенных таблиц.
--
-- Перед запуском сделайте резервную копию БД.
-- Раскомментируйте DELETE в конце только если уверены, что дубликаты в posts не нужны.

-- cpost
INSERT INTO cpost_posts (
    user_id, domain, url, title, author, avatar, post_date, post_text,
    screenshot, images, image_over_text, comments, reposts, likes, views,
    is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads
)
SELECT
    user_id, domain, url, title, author, avatar, post_date, post_text,
    screenshot, images, image_over_text, comments, reposts, likes, views,
    is_ad, COALESCE(status, 'collected'), 'cpost', to_tg, to_tw, to_wp, to_vk,
    COALESCE(to_dzen, FALSE), COALESCE(to_instagram, FALSE), COALESCE(to_threads, FALSE)
FROM posts
WHERE post_type = 'cpost'
  AND (source_platform IS NULL OR source_platform = '');

-- tw
INSERT INTO tw_posts (
    user_id, domain, url, title, author, avatar, post_date, post_text,
    screenshot, images, image_over_text, comments, reposts, likes, views,
    is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads
)
SELECT
    user_id, domain, url, title, author, avatar, post_date, post_text,
    screenshot, images, image_over_text, comments, reposts, likes, views,
    is_ad, COALESCE(status, 'collected'), 'tw', to_tg, to_tw, to_wp, to_vk,
    COALESCE(to_dzen, FALSE), COALESCE(to_instagram, FALSE), COALESCE(to_threads, FALSE)
FROM posts
WHERE post_type = 'tw'
  AND (source_platform IS NULL OR source_platform = '');

-- Опционально: удалить устаревшие прямые записи в posts (после проверки collector).
-- DELETE FROM posts WHERE post_type IN ('cpost', 'tw') AND source_platform IS NULL;
