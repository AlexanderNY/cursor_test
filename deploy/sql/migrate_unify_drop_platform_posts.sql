-- One-shot: leftover *_posts → posts / post_targets, then DROP platform post tables.
-- Profiles stay. Idempotent. Existing DBs only — greenfield never creates *_posts.

CREATE TABLE IF NOT EXISTS migration_post_id_map (
    platform TEXT NOT NULL,
    old_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    PRIMARY KEY (platform, old_id)
);

CREATE INDEX IF NOT EXISTS idx_migration_post_id_map_post
    ON migration_post_id_map (post_id);

DO $$
DECLARE
    plat TEXT;
    tbl TEXT;
    extra_sel TEXT;
    video_sel TEXT;
    video_ins TEXT;
    native_sel TEXT;
    pub_at_sel TEXT;
    result_sel TEXT;
BEGIN
    FOREACH plat IN ARRAY ARRAY[
        'tg','vk','wp','tw','dzen','instagram','threads','url','cpost'
    ]
    LOOP
        tbl := plat || '_posts';
        IF plat = 'threads' THEN
            tbl := 'threads_posts';
        ELSIF plat = 'instagram' THEN
            tbl := 'instagram_posts';
        ELSIF plat = 'cpost' THEN
            tbl := 'cpost_posts';
        END IF;

        IF to_regclass('public.' || tbl) IS NULL THEN
            CONTINUE;
        END IF;

        -- Already-copied hub rows (collector ETL: source_id = old id).
        EXECUTE format(
            $q$
            INSERT INTO migration_post_id_map (platform, old_id, post_id)
            SELECT %L, src.id, p.id
            FROM %I src
            JOIN posts p ON p.user_id = src.user_id
             AND (p.source_platform = %L OR (%L = 'tg' AND p.source_platform = 'telegram'))
             AND p.source_id = src.id
            ON CONFLICT DO NOTHING
            $q$, plat, tbl, plat, plat
        );

        extra_sel := '''{}''::jsonb';
        IF plat = 'tg' THEN
            extra_sel := 'jsonb_strip_nulls(jsonb_build_object(''metadata'', src.metadata))';
        ELSIF plat = 'vk' THEN
            extra_sel := 'jsonb_strip_nulls(jsonb_build_object(''vk_source_id'', src.vk_source_id, ''attachments'', src.attachments))';
        ELSIF plat = 'instagram' THEN
            extra_sel := 'jsonb_strip_nulls(jsonb_build_object(''instagram_source_id'', src.instagram_source_id))';
        END IF;

        native_sel := 'NULL::text';
        IF plat = 'vk' THEN
            native_sel := 'src.vk_source_id::text';
        ELSIF plat = 'instagram' THEN
            native_sel := 'src.instagram_source_id';
        ELSIF plat IN ('url', 'wp', 'tw', 'dzen', 'threads', 'cpost') THEN
            native_sel := 'src.url';
        END IF;

        video_sel := '''[]''::jsonb';
        video_ins := '';
        IF plat IN ('instagram', 'dzen') THEN
            video_sel := 'src.videos';
            video_ins := ', videos';
        END IF;

        EXECUTE format(
            $q$
            INSERT INTO posts (
                user_id, brand_id, channel_id, domain, url, title, author, avatar,
                post_date, post_text, screenshot, images, image_over_text,
                comments, reposts, likes, views, is_ad, status, post_type,
                to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads,
                target_channels, target_groups
                %s,
                source_platform, source_id, source_native_id, extras
            )
            SELECT
                src.user_id, src.brand_id, src.channel_id, src.domain, src.url, src.title, src.author, src.avatar,
                src.post_date, src.post_text, src.screenshot, src.images, src.image_over_text,
                src.comments, src.reposts, src.likes, src.views, src.is_ad,
                CASE
                    WHEN src.status IN ('deleted') THEN 'deleted'
                    WHEN src.status IN ('review') THEN 'review'
                    WHEN src.status IN ('published', 'ready', 'publishing', 'failed', 'skipped', 'distributed', 'error') THEN 'ready'
                    ELSE 'collected'
                END,
                src.post_type,
                src.to_tg, src.to_tw, src.to_wp, src.to_vk, src.to_dzen, src.to_instagram, src.to_threads,
                src.target_channels, src.target_groups
                %s,
                %L, src.id, %s, %s
            FROM %I src
            WHERE NOT EXISTS (
                SELECT 1 FROM migration_post_id_map m
                WHERE m.platform = %L AND m.old_id = src.id
            )
            $q$,
            video_ins,
            CASE WHEN video_ins <> '' THEN ', ' || video_sel ELSE '' END,
            plat,
            native_sel,
            extra_sel,
            tbl,
            plat
        );

        EXECUTE format(
            $q$
            INSERT INTO migration_post_id_map (platform, old_id, post_id)
            SELECT %L, src.id, p.id
            FROM %I src
            JOIN posts p ON p.user_id = src.user_id
             AND p.source_platform = %L
             AND p.source_id = src.id
            ON CONFLICT DO NOTHING
            $q$, plat, tbl, plat
        );

        pub_at_sel := 'NULL::timestamptz';
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = tbl AND column_name = 'publish_at'
        ) THEN
            pub_at_sel := 'src.publish_at';
        END IF;

        result_sel := '''{}''::jsonb';
        IF plat = 'tg' THEN
            result_sel := 'jsonb_strip_nulls(jsonb_build_object(''telegram_message_id'', src.telegram_message_id, ''telegram_chat_id'', src.telegram_chat_id))';
        ELSIF plat = 'vk' THEN
            result_sel := 'jsonb_strip_nulls(jsonb_build_object(''published_vk_post_id'', src.published_vk_post_id, ''published_owner_id'', src.published_owner_id))';
        END IF;

        EXECUTE format(
            $q$
            INSERT INTO post_targets (
                post_id, user_id, platform, status, publish_at, target_channels, target_groups, result
            )
            SELECT
                m.post_id,
                src.user_id,
                %L,
                CASE
                    WHEN src.status IN ('published') THEN 'published'
                    WHEN src.status IN ('publishing') THEN 'publishing'
                    WHEN src.status IN ('failed', 'error') THEN 'failed'
                    WHEN src.status IN ('skipped') THEN 'skipped'
                    WHEN src.status IN ('deleted') THEN 'deleted'
                    WHEN src.status IN ('ready', 'distributed') THEN 'ready'
                    ELSE 'pending'
                END,
                %s,
                src.target_channels,
                src.target_groups,
                %s
            FROM %I src
            JOIN migration_post_id_map m ON m.platform = %L AND m.old_id = src.id
            ON CONFLICT (post_id, platform) DO NOTHING
            $q$, plat, pub_at_sel, result_sel, tbl, plat
        );
    END LOOP;

    INSERT INTO post_targets (post_id, user_id, platform, status, target_channels, target_groups)
    SELECT m.post_id, p.user_id, 'tg', 'pending', p.target_channels, p.target_groups
    FROM posts p JOIN migration_post_id_map m ON m.post_id = p.id
    WHERE COALESCE(p.to_tg, FALSE)
    ON CONFLICT (post_id, platform) DO NOTHING;

    INSERT INTO post_targets (post_id, user_id, platform, status, target_channels, target_groups)
    SELECT m.post_id, p.user_id, 'vk', 'pending', p.target_channels, p.target_groups
    FROM posts p JOIN migration_post_id_map m ON m.post_id = p.id
    WHERE COALESCE(p.to_vk, FALSE)
    ON CONFLICT (post_id, platform) DO NOTHING;

    INSERT INTO post_targets (post_id, user_id, platform, status, target_channels, target_groups)
    SELECT m.post_id, p.user_id, 'wp', 'pending', p.target_channels, p.target_groups
    FROM posts p JOIN migration_post_id_map m ON m.post_id = p.id
    WHERE COALESCE(p.to_wp, FALSE)
    ON CONFLICT (post_id, platform) DO NOTHING;

    INSERT INTO post_targets (post_id, user_id, platform, status, target_channels, target_groups)
    SELECT m.post_id, p.user_id, 'tw', 'pending', p.target_channels, p.target_groups
    FROM posts p JOIN migration_post_id_map m ON m.post_id = p.id
    WHERE COALESCE(p.to_tw, FALSE)
    ON CONFLICT (post_id, platform) DO NOTHING;

    INSERT INTO post_targets (post_id, user_id, platform, status, target_channels, target_groups)
    SELECT m.post_id, p.user_id, 'threads', 'pending', p.target_channels, p.target_groups
    FROM posts p JOIN migration_post_id_map m ON m.post_id = p.id
    WHERE COALESCE(p.to_threads, FALSE)
    ON CONFLICT (post_id, platform) DO NOTHING;

    INSERT INTO post_targets (post_id, user_id, platform, status, target_channels, target_groups)
    SELECT m.post_id, p.user_id, 'dzen', 'pending', p.target_channels, p.target_groups
    FROM posts p JOIN migration_post_id_map m ON m.post_id = p.id
    WHERE COALESCE(p.to_dzen, FALSE)
    ON CONFLICT (post_id, platform) DO NOTHING;

    INSERT INTO post_targets (post_id, user_id, platform, status, target_channels, target_groups)
    SELECT m.post_id, p.user_id, 'instagram', 'pending', p.target_channels, p.target_groups
    FROM posts p JOIN migration_post_id_map m ON m.post_id = p.id
    WHERE COALESCE(p.to_instagram, FALSE)
    ON CONFLICT (post_id, platform) DO NOTHING;
END $$;

DROP TABLE IF EXISTS tg_posts CASCADE;
DROP TABLE IF EXISTS vk_posts CASCADE;
DROP TABLE IF EXISTS wp_posts CASCADE;
DROP TABLE IF EXISTS tw_posts CASCADE;
DROP TABLE IF EXISTS dzen_posts CASCADE;
DROP TABLE IF EXISTS instagram_posts CASCADE;
DROP TABLE IF EXISTS threads_posts CASCADE;
DROP TABLE IF EXISTS url_posts CASCADE;
DROP TABLE IF EXISTS cpost_posts CASCADE;
