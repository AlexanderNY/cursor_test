PGDMP                       ~            db_bot    16.6    16.6 Љ   ц           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false            ч           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false            ш           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false            щ           1262    34681    db_bot    DATABASE     z   CREATE DATABASE db_bot WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'Russian_Russia.1251';
    DROP DATABASE db_bot;
                postgres    false                       1259    35302    admin_audit_log    TABLE     8  CREATE TABLE public.admin_audit_log (
    id integer NOT NULL,
    admin_user_id integer NOT NULL,
    action character varying(120) NOT NULL,
    target_type character varying(80),
    target_id character varying(80),
    details_json jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 #   DROP TABLE public.admin_audit_log;
       public         heap    postgres    false                       1259    35301    admin_audit_log_id_seq    SEQUENCE     Ћ   CREATE SEQUENCE public.admin_audit_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.admin_audit_log_id_seq;
       public          postgres    false    276            ъ           0    0    admin_audit_log_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.admin_audit_log_id_seq OWNED BY public.admin_audit_log.id;
          public          postgres    false    275            B           1259    35808    ai_tasks    TABLE     k  CREATE TABLE public.ai_tasks (
    id integer NOT NULL,
    user_id integer,
    task_type character varying(50) NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying,
    payload jsonb DEFAULT '{}'::jsonb,
    result jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    processed_at timestamp with time zone
);
    DROP TABLE public.ai_tasks;
       public         heap    postgres    false            A           1259    35807    ai_tasks_id_seq    SEQUENCE     ‡   CREATE SEQUENCE public.ai_tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.ai_tasks_id_seq;
       public          postgres    false    322            ы           0    0    ai_tasks_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.ai_tasks_id_seq OWNED BY public.ai_tasks.id;
          public          postgres    false    321                       1259    35286    billing_events    TABLE     2  CREATE TABLE public.billing_events (
    id integer NOT NULL,
    provider character varying(32) NOT NULL,
    event_id character varying(255),
    event_type character varying(120) NOT NULL,
    payload_json jsonb,
    user_id integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 "   DROP TABLE public.billing_events;
       public         heap    postgres    false                       1259    35285    billing_events_id_seq    SEQUENCE     Ќ   CREATE SEQUENCE public.billing_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 ,   DROP SEQUENCE public.billing_events_id_seq;
       public          postgres    false    274            ь           0    0    billing_events_id_seq    SEQUENCE OWNED BY     O   ALTER SEQUENCE public.billing_events_id_seq OWNED BY public.billing_events.id;
          public          postgres    false    273                        1259    35110    blacklisted_tokens    TABLE     д   CREATE TABLE public.blacklisted_tokens (
    id integer NOT NULL,
    token character varying(500) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 &   DROP TABLE public.blacklisted_tokens;
       public         heap    postgres    false            я            1259    35109    blacklisted_tokens_id_seq    SEQUENCE     ‘   CREATE SEQUENCE public.blacklisted_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 0   DROP SEQUENCE public.blacklisted_tokens_id_seq;
       public          postgres    false    256            э           0    0    blacklisted_tokens_id_seq    SEQUENCE OWNED BY     W   ALTER SEQUENCE public.blacklisted_tokens_id_seq OWNED BY public.blacklisted_tokens.id;
          public          postgres    false    255            :           1259    35722    cpost_posts    TABLE     Е  CREATE TABLE public.cpost_posts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    domain character varying(255),
    url text,
    title character varying(500),
    author character varying(255),
    avatar text,
    post_date timestamp with time zone,
    post_text text,
    screenshot text,
    images jsonb DEFAULT '[]'::jsonb,
    image_over_text text,
    comments integer DEFAULT 0,
    reposts integer DEFAULT 0,
    likes integer DEFAULT 0,
    views integer DEFAULT 0,
    is_ad boolean DEFAULT false,
    status character varying(50) DEFAULT 'collected'::character varying,
    post_type character varying(50),
    to_tg boolean DEFAULT false,
    to_tw boolean DEFAULT false,
    to_wp boolean DEFAULT false,
    to_vk boolean DEFAULT false,
    to_dzen boolean DEFAULT false,
    to_instagram boolean DEFAULT false,
    to_threads boolean DEFAULT false,
    target_channels jsonb DEFAULT '[]'::jsonb,
    target_groups jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT cpost_posts_status_check CHECK (((status)::text = ANY ((ARRAY['created'::character varying, 'collected'::character varying, 'processing'::character varying, 'ready'::character varying, 'review'::character varying, 'publishing'::character varying, 'published'::character varying, 'distributed'::character varying, 'deleted'::character varying])::text[])))
);
    DROP TABLE public.cpost_posts;
       public         heap    postgres    false            9           1259    35721    cpost_posts_id_seq    SEQUENCE     Љ   CREATE SEQUENCE public.cpost_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 )   DROP SEQUENCE public.cpost_posts_id_seq;
       public          postgres    false    314            ю           0    0    cpost_posts_id_seq    SEQUENCE OWNED BY     I   ALTER SEQUENCE public.cpost_posts_id_seq OWNED BY public.cpost_posts.id;
          public          postgres    false    313            8           1259    35708    cpost_profiles    TABLE     G  CREATE TABLE public.cpost_profiles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    default_platforms jsonb DEFAULT '{"tg": false, "tw": false, "vk": false, "wp": false}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 "   DROP TABLE public.cpost_profiles;
       public         heap    postgres    false            7           1259    35707    cpost_profiles_id_seq    SEQUENCE     Ќ   CREATE SEQUENCE public.cpost_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 ,   DROP SEQUENCE public.cpost_profiles_id_seq;
       public          postgres    false    312            я           0    0    cpost_profiles_id_seq    SEQUENCE OWNED BY     O   ALTER SEQUENCE public.cpost_profiles_id_seq OWNED BY public.cpost_profiles.id;
          public          postgres    false    311            >           1259    35781    curl_one_time_done    TABLE     Ц   CREATE TABLE public.curl_one_time_done (
    id integer NOT NULL,
    user_id integer NOT NULL,
    url text NOT NULL,
    xpath text NOT NULL,
    executed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 &   DROP TABLE public.curl_one_time_done;
       public         heap    postgres    false            =           1259    35780    curl_one_time_done_id_seq    SEQUENCE     ‘   CREATE SEQUENCE public.curl_one_time_done_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 0   DROP SEQUENCE public.curl_one_time_done_id_seq;
       public          postgres    false    318                        0    0    curl_one_time_done_id_seq    SEQUENCE OWNED BY     W   ALTER SEQUENCE public.curl_one_time_done_id_seq OWNED BY public.curl_one_time_done.id;
          public          postgres    false    317            <           1259    35752 
   curl_settings    TABLE       CREATE TABLE public.curl_settings (
    id integer NOT NULL,
    user_id integer NOT NULL,
    collect_enabled boolean DEFAULT false,
    schedule_type character varying(20) DEFAULT 'standard'::character varying,
    time_intervals jsonb DEFAULT '[]'::jsonb,
    url text,
    xpath text,
    take_screenshot boolean DEFAULT false,
    to_tg boolean DEFAULT false,
    to_tw boolean DEFAULT false,
    to_vk boolean DEFAULT false,
    to_wp boolean DEFAULT false,
    urls jsonb DEFAULT '[]'::jsonb,
    process_before_publish boolean DEFAULT false,
    process_description text,
    remove_emojis boolean DEFAULT false,
    remove_images boolean DEFAULT false,
    clean_html boolean DEFAULT false,
    process_services jsonb,
    status_review_after_process boolean DEFAULT false,
    add_static_html boolean DEFAULT false,
    static_html_content text,
    screenshot_only boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 !   DROP TABLE public.curl_settings;
       public         heap    postgres    false            ;           1259    35751    curl_settings_id_seq    SEQUENCE     Њ   CREATE SEQUENCE public.curl_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.curl_settings_id_seq;
       public          postgres    false    316                       0    0    curl_settings_id_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.curl_settings_id_seq OWNED BY public.curl_settings.id;
          public          postgres    false    315            р            1259    34919 
   dzen_posts    TABLE     и  CREATE TABLE public.dzen_posts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    domain character varying(255),
    url text,
    title character varying(500),
    author character varying(255),
    avatar text,
    post_date timestamp with time zone,
    post_text text,
    screenshot text,
    images jsonb DEFAULT '[]'::jsonb,
    image_over_text text,
    comments integer DEFAULT 0,
    reposts integer DEFAULT 0,
    likes integer DEFAULT 0,
    views integer DEFAULT 0,
    is_ad boolean DEFAULT false,
    status character varying(50) DEFAULT 'collected'::character varying,
    post_type character varying(50),
    to_tg boolean DEFAULT false,
    to_tw boolean DEFAULT false,
    to_wp boolean DEFAULT false,
    to_vk boolean DEFAULT false,
    to_dzen boolean DEFAULT true,
    to_instagram boolean DEFAULT false,
    to_threads boolean DEFAULT false,
    target_channels jsonb DEFAULT '[]'::jsonb,
    target_groups jsonb DEFAULT '[]'::jsonb,
    videos jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT dzen_posts_status_check CHECK (((status)::text = ANY ((ARRAY['created'::character varying, 'collected'::character varying, 'processing'::character varying, 'ready'::character varying, 'review'::character varying, 'publishing'::character varying, 'published'::character varying, 'distributed'::character varying, 'deleted'::character varying])::text[])))
);
    DROP TABLE public.dzen_posts;
       public         heap    postgres    false            п            1259    34918    dzen_posts_id_seq    SEQUENCE     ‰   CREATE SEQUENCE public.dzen_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 (   DROP SEQUENCE public.dzen_posts_id_seq;
       public          postgres    false    240                       0    0    dzen_posts_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.dzen_posts_id_seq OWNED BY public.dzen_posts.id;
          public          postgres    false    239            о            1259    34900 
   dzen_profiles    TABLE       CREATE TABLE public.dzen_profiles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    publish_enabled boolean DEFAULT false,
    collect_enabled boolean DEFAULT false,
    schedule_type character varying(20) DEFAULT 'immediate'::character varying,
    time_intervals jsonb DEFAULT '[]'::jsonb,
    rss_feed_url text,
    channel_name character varying(255),
    channels_to_read jsonb DEFAULT '[]'::jsonb,
    rss_token character varying(255),
    yandex_login character varying(255),
    yandex_password text,
    dzen_studio_url text,
    collect_source character varying(20) DEFAULT 'rss'::character varying,
    last_auth_error text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 !   DROP TABLE public.dzen_profiles;
       public         heap    postgres    false            н            1259    34899    dzen_profiles_id_seq    SEQUENCE     Њ   CREATE SEQUENCE public.dzen_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.dzen_profiles_id_seq;
       public          postgres    false    238                       0    0    dzen_profiles_id_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.dzen_profiles_id_seq OWNED BY public.dzen_profiles.id;
          public          postgres    false    237                       1259    35139    email_verification_tokens    TABLE     	  CREATE TABLE public.email_verification_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    token character varying(500) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 -   DROP TABLE public.email_verification_tokens;
       public         heap    postgres    false                       1259    35138     email_verification_tokens_id_seq    SEQUENCE        CREATE SEQUENCE public.email_verification_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 7   DROP SEQUENCE public.email_verification_tokens_id_seq;
       public          postgres    false    260                       0    0     email_verification_tokens_id_seq    SEQUENCE OWNED BY     e   ALTER SEQUENCE public.email_verification_tokens_id_seq OWNED BY public.email_verification_tokens.id;
          public          postgres    false    259            F           1259    35834    feedback    TABLE     Ї  CREATE TABLE public.feedback (
    id integer NOT NULL,
    type character varying(50) NOT NULL,
    text text NOT NULL,
    email character varying(255),
    user_id integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT feedback_type_check CHECK (((type)::text = ANY ((ARRAY['bug_report'::character varying, 'suggestion'::character varying, 'contact_author'::character varying])::text[])))
);
    DROP TABLE public.feedback;
       public         heap    postgres    false            E           1259    35833    feedback_id_seq    SEQUENCE     ‡   CREATE SEQUENCE public.feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.feedback_id_seq;
       public          postgres    false    326                       0    0    feedback_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.feedback_id_seq OWNED BY public.feedback.id;
          public          postgres    false    325            (           1259    35508    game_answers    TABLE       CREATE TABLE public.game_answers (
    id integer NOT NULL,
    session_id integer NOT NULL,
    question_id integer NOT NULL,
    selected_option_id integer,
    is_correct boolean NOT NULL,
    answered_at timestamp with time zone DEFAULT now() NOT NULL
);
     DROP TABLE public.game_answers;
       public         heap    postgres    false            '           1259    35507    game_answers_id_seq    SEQUENCE     ‹   CREATE SEQUENCE public.game_answers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.game_answers_id_seq;
       public          postgres    false    296                       0    0    game_answers_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.game_answers_id_seq OWNED BY public.game_answers.id;
          public          postgres    false    295                       1259    35382 	   game_bots    TABLE     м   CREATE TABLE public.game_bots (
    id integer NOT NULL,
    name text NOT NULL,
    token text NOT NULL,
    username text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
    DROP TABLE public.game_bots;
       public         heap    postgres    false                       1259    35381    game_bots_id_seq    SEQUENCE     €   CREATE SEQUENCE public.game_bots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.game_bots_id_seq;
       public          postgres    false    282                       0    0    game_bots_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.game_bots_id_seq OWNED BY public.game_bots.id;
          public          postgres    false    281            *           1259    35536    game_media_assets    TABLE     V  CREATE TABLE public.game_media_assets (
    id integer NOT NULL,
    filename text NOT NULL,
    s3_key text NOT NULL,
    original_filename text,
    title text DEFAULT ''::text NOT NULL,
    description text,
    content_type text,
    size_bytes bigint DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
 %   DROP TABLE public.game_media_assets;
       public         heap    postgres    false            )           1259    35535    game_media_assets_id_seq    SEQUENCE     ђ   CREATE SEQUENCE public.game_media_assets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 /   DROP SEQUENCE public.game_media_assets_id_seq;
       public          postgres    false    298                       0    0    game_media_assets_id_seq    SEQUENCE OWNED BY     U   ALTER SEQUENCE public.game_media_assets_id_seq OWNED BY public.game_media_assets.id;
          public          postgres    false    297            0           1259    35601    game_menu_cart_items    TABLE     ц   CREATE TABLE public.game_menu_cart_items (
    id integer NOT NULL,
    cart_id integer NOT NULL,
    node_id integer NOT NULL,
    quantity integer DEFAULT 1 NOT NULL,
    CONSTRAINT game_menu_cart_items_quantity_check CHECK ((quantity > 0))
);
 (   DROP TABLE public.game_menu_cart_items;
       public         heap    postgres    false            /           1259    35600    game_menu_cart_items_id_seq    SEQUENCE     “   CREATE SEQUENCE public.game_menu_cart_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 2   DROP SEQUENCE public.game_menu_cart_items_id_seq;
       public          postgres    false    304            	           0    0    game_menu_cart_items_id_seq    SEQUENCE OWNED BY     [   ALTER SEQUENCE public.game_menu_cart_items_id_seq OWNED BY public.game_menu_cart_items.id;
          public          postgres    false    303            .           1259    35581    game_menu_carts    TABLE     в   CREATE TABLE public.game_menu_carts (
    id integer NOT NULL,
    bot_id integer NOT NULL,
    telegram_user_id bigint NOT NULL,
    mode_id integer NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);
 #   DROP TABLE public.game_menu_carts;
       public         heap    postgres    false            -           1259    35580    game_menu_carts_id_seq    SEQUENCE     Ћ   CREATE SEQUENCE public.game_menu_carts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.game_menu_carts_id_seq;
       public          postgres    false    302            
           0    0    game_menu_carts_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.game_menu_carts_id_seq OWNED BY public.game_menu_carts.id;
          public          postgres    false    301            ,           1259    35557    game_menu_nodes    TABLE     “  CREATE TABLE public.game_menu_nodes (
    id integer NOT NULL,
    mode_id integer NOT NULL,
    parent_id integer,
    title text NOT NULL,
    body_text text,
    image_url text,
    image_file_id text,
    sort_order integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    price numeric(12,2) DEFAULT 0 NOT NULL
);
 #   DROP TABLE public.game_menu_nodes;
       public         heap    postgres    false            +           1259    35556    game_menu_nodes_id_seq    SEQUENCE     Ћ   CREATE SEQUENCE public.game_menu_nodes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.game_menu_nodes_id_seq;
       public          postgres    false    300                       0    0    game_menu_nodes_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.game_menu_nodes_id_seq OWNED BY public.game_menu_nodes.id;
          public          postgres    false    299            4           1259    35647    game_menu_order_items    TABLE     0  CREATE TABLE public.game_menu_order_items (
    id integer NOT NULL,
    order_id integer NOT NULL,
    node_id integer,
    title text NOT NULL,
    quantity integer NOT NULL,
    unit_price numeric(12,2) DEFAULT 0 NOT NULL,
    CONSTRAINT game_menu_order_items_quantity_check CHECK ((quantity > 0))
);
 )   DROP TABLE public.game_menu_order_items;
       public         heap    postgres    false            3           1259    35646    game_menu_order_items_id_seq    SEQUENCE     ”   CREATE SEQUENCE public.game_menu_order_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 3   DROP SEQUENCE public.game_menu_order_items_id_seq;
       public          postgres    false    308                       0    0    game_menu_order_items_id_seq    SEQUENCE OWNED BY     ]   ALTER SEQUENCE public.game_menu_order_items_id_seq OWNED BY public.game_menu_order_items.id;
          public          postgres    false    307            2           1259    35622    game_menu_orders    TABLE     я  CREATE TABLE public.game_menu_orders (
    id integer NOT NULL,
    order_number text NOT NULL,
    bot_id integer NOT NULL,
    mode_id integer NOT NULL,
    telegram_user_id bigint NOT NULL,
    username text,
    first_name text,
    status text DEFAULT 'placed'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    total_amount numeric(12,2) DEFAULT 0 NOT NULL,
    CONSTRAINT game_menu_orders_status_check CHECK ((status = ANY (ARRAY['placed'::text, 'cancelled'::text])))
);
 $   DROP TABLE public.game_menu_orders;
       public         heap    postgres    false            1           1259    35621    game_menu_orders_id_seq    SEQUENCE     Џ   CREATE SEQUENCE public.game_menu_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.game_menu_orders_id_seq;
       public          postgres    false    306            
           0    0    game_menu_orders_id_seq    SEQUENCE OWNED BY     S   ALTER SEQUENCE public.game_menu_orders_id_seq OWNED BY public.game_menu_orders.id;
          public          postgres    false    305                       1259    35411 
   game_modes    TABLE     4  CREATE TABLE public.game_modes (
    id integer NOT NULL,
    code text NOT NULL,
    title text NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    questions_per_game integer DEFAULT 10 NOT NULL,
    bot_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    mode_type text DEFAULT 'quiz'::text NOT NULL,
    CONSTRAINT game_modes_mode_type_check CHECK ((mode_type = ANY (ARRAY['quiz'::text, 'menu'::text]))),
    CONSTRAINT game_modes_questions_per_game_check CHECK (((questions_per_game > 0) AND (questions_per_game <= 300)))
);
    DROP TABLE public.game_modes;
       public         heap    postgres    false                       1259    35410    game_modes_id_seq    SEQUENCE     ‰   CREATE SEQUENCE public.game_modes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 (   DROP SEQUENCE public.game_modes_id_seq;
       public          postgres    false    286                       0    0    game_modes_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.game_modes_id_seq OWNED BY public.game_modes.id;
          public          postgres    false    285                       1259    35395    game_players    TABLE     
  CREATE TABLE public.game_players (
    id integer NOT NULL,
    telegram_user_id bigint NOT NULL,
    bot_id integer,
    username text,
    first_name text,
    is_admin boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
     DROP TABLE public.game_players;
       public         heap    postgres    false                       1259    35394    game_players_id_seq    SEQUENCE     ‹   CREATE SEQUENCE public.game_players_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.game_players_id_seq;
       public          postgres    false    284                       0    0    game_players_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.game_players_id_seq OWNED BY public.game_players.id;
          public          postgres    false    283            "           1259    35445    game_question_options    TABLE     J  CREATE TABLE public.game_question_options (
    id integer NOT NULL,
    question_id integer NOT NULL,
    option_index smallint NOT NULL,
    option_text text NOT NULL,
    is_correct boolean DEFAULT false NOT NULL,
    CONSTRAINT game_question_options_option_index_check CHECK (((option_index >= 1) AND (option_index <= 6)))
);
 )   DROP TABLE public.game_question_options;
       public         heap    postgres    false            !           1259    35444    game_question_options_id_seq    SEQUENCE     ”   CREATE SEQUENCE public.game_question_options_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 3   DROP SEQUENCE public.game_question_options_id_seq;
       public          postgres    false    290                       0    0    game_question_options_id_seq    SEQUENCE OWNED BY     ]   ALTER SEQUENCE public.game_question_options_id_seq OWNED BY public.game_question_options.id;
          public          postgres    false    289                        1259    35429    game_questions    TABLE       CREATE TABLE public.game_questions (
    id integer NOT NULL,
    mode_id integer NOT NULL,
    prompt_text text NOT NULL,
    image_file_id text,
    image_url text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
 "   DROP TABLE public.game_questions;
       public         heap    postgres    false                       1259    35428    game_questions_id_seq    SEQUENCE     Ќ   CREATE SEQUENCE public.game_questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 ,   DROP SEQUENCE public.game_questions_id_seq;
       public          postgres    false    288                       0    0    game_questions_id_seq    SEQUENCE OWNED BY     O   ALTER SEQUENCE public.game_questions_id_seq OWNED BY public.game_questions.id;
          public          postgres    false    287            &           1259    35488    game_session_questions    TABLE     ю   CREATE TABLE public.game_session_questions (
    id integer NOT NULL,
    session_id integer NOT NULL,
    step_index integer NOT NULL,
    question_id integer NOT NULL,
    CONSTRAINT game_session_questions_step_index_check CHECK ((step_index >= 0))
);
 *   DROP TABLE public.game_session_questions;
       public         heap    postgres    false            %           1259    35487    game_session_questions_id_seq    SEQUENCE     •   CREATE SEQUENCE public.game_session_questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 4   DROP SEQUENCE public.game_session_questions_id_seq;
       public          postgres    false    294                       0    0    game_session_questions_id_seq    SEQUENCE OWNED BY     _   ALTER SEQUENCE public.game_session_questions_id_seq OWNED BY public.game_session_questions.id;
          public          postgres    false    293            $           1259    35463 
   game_sessions    TABLE     a  CREATE TABLE public.game_sessions (
    id integer NOT NULL,
    player_id integer NOT NULL,
    mode_id integer NOT NULL,
    status text DEFAULT 'in_progress'::text NOT NULL,
    score integer DEFAULT 0 NOT NULL,
    correct_count integer DEFAULT 0 NOT NULL,
    total_questions integer NOT NULL,
    current_step integer DEFAULT 0 NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    finished_at timestamp with time zone,
    duration_sec integer,
    CONSTRAINT game_sessions_status_check CHECK ((status = ANY (ARRAY['in_progress'::text, 'completed'::text, 'aborted'::text])))
);
 !   DROP TABLE public.game_sessions;
       public         heap    postgres    false            #           1259    35462    game_sessions_id_seq    SEQUENCE     Њ   CREATE SEQUENCE public.game_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.game_sessions_id_seq;
       public          postgres    false    292                       0    0    game_sessions_id_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.game_sessions_id_seq OWNED BY public.game_sessions.id;
          public          postgres    false    291                       1259    35219 
   group_members    TABLE     ±  CREATE TABLE public.group_members (
    id integer NOT NULL,
    group_id integer NOT NULL,
    user_id integer NOT NULL,
    role_in_group character varying(20) NOT NULL,
    joined_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT group_members_role_in_group_check CHECK (((role_in_group)::text = ANY ((ARRAY['admin'::character varying, 'editor'::character varying, 'analyst'::character varying])::text[])))
);
 !   DROP TABLE public.group_members;
       public         heap    postgres    false                       1259    35218    group_members_id_seq    SEQUENCE     Њ   CREATE SEQUENCE public.group_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.group_members_id_seq;
       public          postgres    false    268                       0    0    group_members_id_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.group_members_id_seq OWNED BY public.group_members.id;
          public          postgres    false    267                       1259    35174    groups    TABLE     Ы   CREATE TABLE public.groups (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id integer
);
    DROP TABLE public.groups;
       public         heap    postgres    false                       1259    35173 
   groups_id_seq    SEQUENCE     …   CREATE SEQUENCE public.groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 $   DROP SEQUENCE public.groups_id_seq;
       public          postgres    false    264                       0    0 
   groups_id_seq    SEQUENCE OWNED BY     ?   ALTER SEQUENCE public.groups_id_seq OWNED BY public.groups.id;
          public          postgres    false    263            I           1259    35854    guide_blocks    TABLE       CREATE TABLE public.guide_blocks (
    id integer NOT NULL,
    slug character varying(64) NOT NULL,
    toc_label character varying(128) DEFAULT ''::character varying NOT NULL,
    title character varying(255) DEFAULT ''::character varying NOT NULL,
    subtitle text DEFAULT ''::text NOT NULL,
    body text DEFAULT ''::text NOT NULL,
    sort_order integer DEFAULT 0 NOT NULL,
    is_visible boolean DEFAULT true NOT NULL,
    style jsonb DEFAULT '{}'::jsonb NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
     DROP TABLE public.guide_blocks;
       public         heap    postgres    false            H           1259    35853    guide_blocks_id_seq    SEQUENCE     ‹   CREATE SEQUENCE public.guide_blocks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.guide_blocks_id_seq;
       public          postgres    false    329                       0    0    guide_blocks_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.guide_blocks_id_seq OWNED BY public.guide_blocks.id;
          public          postgres    false    328            ф            1259    34974    instagram_posts    TABLE     "  CREATE TABLE public.instagram_posts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    domain character varying(255),
    url text,
    title character varying(500),
    author character varying(255),
    avatar text,
    post_date timestamp with time zone,
    post_text text,
    screenshot text,
    images jsonb DEFAULT '[]'::jsonb,
    image_over_text text,
    comments integer DEFAULT 0,
    reposts integer DEFAULT 0,
    likes integer DEFAULT 0,
    views integer DEFAULT 0,
    is_ad boolean DEFAULT false,
    status character varying(50) DEFAULT 'collected'::character varying,
    post_type character varying(50),
    to_tg boolean DEFAULT false,
    to_tw boolean DEFAULT false,
    to_wp boolean DEFAULT false,
    to_vk boolean DEFAULT false,
    to_dzen boolean DEFAULT false,
    to_instagram boolean DEFAULT true,
    to_threads boolean DEFAULT false,
    target_channels jsonb DEFAULT '[]'::jsonb,
    target_groups jsonb DEFAULT '[]'::jsonb,
    instagram_source_id character varying(100),
    videos jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT instagram_posts_status_check CHECK (((status)::text = ANY ((ARRAY['created'::character varying, 'collected'::character varying, 'processing'::character varying, 'ready'::character varying, 'review'::character varying, 'publishing'::character varying, 'published'::character varying, 'distributed'::character varying, 'deleted'::character varying])::text[])))
);
 #   DROP TABLE public.instagram_posts;
       public         heap    postgres    false            у            1259    34973    instagram_posts_id_seq    SEQUENCE     Ћ   CREATE SEQUENCE public.instagram_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.instagram_posts_id_seq;
       public          postgres    false    244                       0    0    instagram_posts_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.instagram_posts_id_seq OWNED BY public.instagram_posts.id;
          public          postgres    false    243            т            1259    34946    instagram_profiles    TABLE       CREATE TABLE public.instagram_profiles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    publish_enabled boolean DEFAULT false,
    collect_enabled boolean DEFAULT false,
    schedule_type character varying(20) DEFAULT 'immediate'::character varying,
    time_intervals jsonb DEFAULT '[]'::jsonb,
    username character varying(255),
    password character varying(512),
    usernames_to_read jsonb DEFAULT '[]'::jsonb,
    process_enabled boolean DEFAULT false,
    processing_description text,
    remove_emojis boolean DEFAULT false,
    remove_images boolean DEFAULT false,
    clean_html boolean DEFAULT false,
    process_services jsonb,
    status_review_after_process boolean DEFAULT false,
    add_static_html boolean DEFAULT false,
    static_html_content text,
    instagrapi_session jsonb,
    instagram_verification_code character varying(64),
    instagram_last_auth_error text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 &   DROP TABLE public.instagram_profiles;
       public         heap    postgres    false            с            1259    34945    instagram_profiles_id_seq    SEQUENCE     ‘   CREATE SEQUENCE public.instagram_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 0   DROP SEQUENCE public.instagram_profiles_id_seq;
       public          postgres    false    242                       0    0    instagram_profiles_id_seq    SEQUENCE OWNED BY     W   ALTER SEQUENCE public.instagram_profiles_id_seq OWNED BY public.instagram_profiles.id;
          public          postgres    false    241            D           1259    35821 
   notifications    TABLE     ч   CREATE TABLE public.notifications (
    id integer NOT NULL,
    message text NOT NULL,
    user_id integer,
    type character varying(50) DEFAULT 'general'::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 !   DROP TABLE public.notifications;
       public         heap    postgres    false            C           1259    35820    notifications_id_seq    SEQUENCE     Њ   CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.notifications_id_seq;
       public          postgres    false    324                       0    0    notifications_id_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;
          public          postgres    false    323                       1259    35122    password_reset_tokens    TABLE       CREATE TABLE public.password_reset_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    token character varying(500) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 )   DROP TABLE public.password_reset_tokens;
       public         heap    postgres    false                       1259    35121    password_reset_tokens_id_seq    SEQUENCE     ”   CREATE SEQUENCE public.password_reset_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 3   DROP SEQUENCE public.password_reset_tokens_id_seq;
       public          postgres    false    258                       0    0    password_reset_tokens_id_seq    SEQUENCE OWNED BY     ]   ALTER SEQUENCE public.password_reset_tokens_id_seq OWNED BY public.password_reset_tokens.id;
          public          postgres    false    257                       1259    35269    plan_definitions    TABLE     	  CREATE TABLE public.plan_definitions (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    display_name character varying(120) NOT NULL,
    description text,
    limits_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    sort_order integer DEFAULT 0
);
 $   DROP TABLE public.plan_definitions;
       public         heap    postgres    false                       1259    35268    plan_definitions_id_seq    SEQUENCE     Џ   CREATE SEQUENCE public.plan_definitions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.plan_definitions_id_seq;
       public          postgres    false    272                       0    0    plan_definitions_id_seq    SEQUENCE OWNED BY     S   ALTER SEQUENCE public.plan_definitions_id_seq OWNED BY public.plan_definitions.id;
          public          postgres    false    271            6           1259    35670    posts    TABLE     O  CREATE TABLE public.posts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    domain character varying(255),
    url text,
    title character varying(500),
    author character varying(255),
    avatar text,
    post_date timestamp with time zone,
    post_text text,
    screenshot text,
    images jsonb DEFAULT '[]'::jsonb,
    image_over_text text,
    comments integer DEFAULT 0,
    reposts integer DEFAULT 0,
    likes integer DEFAULT 0,
    views integer DEFAULT 0,
    is_ad boolean DEFAULT false,
    status character varying(50) DEFAULT 'collected'::character varying,
    post_type character varying(50),
    to_tg boolean DEFAULT false,
    to_tw boolean DEFAULT false,
    to_wp boolean DEFAULT false,
    to_vk boolean DEFAULT false,
    to_dzen boolean DEFAULT false,
    to_instagram boolean DEFAULT false,
    to_threads boolean DEFAULT false,
    target_channels jsonb DEFAULT '[]'::jsonb,
    target_groups jsonb DEFAULT '[]'::jsonb,
    source_platform character varying(10),
    source_id integer,
    platform_texts jsonb DEFAULT '{}'::jsonb,
    videos jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT posts_status_check CHECK (((status)::text = ANY ((ARRAY['created'::character varying, 'collected'::character varying, 'processing'::character varying, 'ready'::character varying, 'review'::character varying, 'publishing'::character varying, 'published'::character varying, 'distributed'::character varying, 'deleted'::character varying])::text[])))
);
    DROP TABLE public.posts;
       public         heap    postgres    false            5           1259    35669    posts_id_seq    SEQUENCE     „   CREATE SEQUENCE public.posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 #   DROP SEQUENCE public.posts_id_seq;
       public          postgres    false    310                       0    0    posts_id_seq    SEQUENCE OWNED BY     =   ALTER SEQUENCE public.posts_id_seq OWNED BY public.posts.id;
          public          postgres    false    309            ю            1259    35093    refresh_tokens    TABLE     ю   CREATE TABLE public.refresh_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    token character varying(500) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 "   DROP TABLE public.refresh_tokens;
       public         heap    postgres    false            э            1259    35092    refresh_tokens_id_seq    SEQUENCE     Ќ   CREATE SEQUENCE public.refresh_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 ,   DROP SEQUENCE public.refresh_tokens_id_seq;
       public          postgres    false    254                       0    0    refresh_tokens_id_seq    SEQUENCE OWNED BY     O   ALTER SEQUENCE public.refresh_tokens_id_seq OWNED BY public.refresh_tokens.id;
          public          postgres    false    253            @           1259    35794    service_cycle_log    TABLE     `  CREATE TABLE public.service_cycle_log (
    id integer NOT NULL,
    service_name character varying(50) NOT NULL,
    cycle_type character varying(50) NOT NULL,
    status character varying(20) DEFAULT 'ok'::character varying,
    detail text,
    items_processed integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 %   DROP TABLE public.service_cycle_log;
       public         heap    postgres    false            ?           1259    35793    service_cycle_log_id_seq    SEQUENCE     ђ   CREATE SEQUENCE public.service_cycle_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 /   DROP SEQUENCE public.service_cycle_log_id_seq;
       public          postgres    false    320                       0    0    service_cycle_log_id_seq    SEQUENCE OWNED BY     U   ALTER SEQUENCE public.service_cycle_log_id_seq OWNED BY public.service_cycle_log.id;
          public          postgres    false    319            X           1259    36033    smm_ai_usage    TABLE     Ѓ   CREATE TABLE public.smm_ai_usage (
    user_id integer NOT NULL,
    month character(7) NOT NULL,
    calls integer DEFAULT 0
);
     DROP TABLE public.smm_ai_usage;
       public         heap    postgres    false            S           1259    35971    smm_automations    TABLE     '  CREATE TABLE public.smm_automations (
    id integer NOT NULL,
    user_id integer NOT NULL,
    brand_id integer,
    type character varying(20) NOT NULL,
    config jsonb DEFAULT '{}'::jsonb NOT NULL,
    enabled boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT smm_automations_type_check CHECK (((type)::text = ANY ((ARRAY['rss'::character varying, 'tg_repost'::character varying, 'mention'::character varying])::text[])))
);
 #   DROP TABLE public.smm_automations;
       public         heap    postgres    false            R           1259    35970    smm_automations_id_seq    SEQUENCE     Ћ   CREATE SEQUENCE public.smm_automations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.smm_automations_id_seq;
       public          postgres    false    339                       0    0    smm_automations_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.smm_automations_id_seq OWNED BY public.smm_automations.id;
          public          postgres    false    338            M           1259    35889    smm_brand_channels    TABLE     ж  CREATE TABLE public.smm_brand_channels (
    id integer NOT NULL,
    brand_id integer NOT NULL,
    network character varying(10) NOT NULL,
    external_id character varying(128) NOT NULL,
    title character varying(255),
    kind character varying(20) DEFAULT 'channel'::character varying NOT NULL,
    role character varying(20) DEFAULT 'own'::character varying NOT NULL,
    color_override character varying(7),
    publish_enabled boolean DEFAULT true,
    collect_enabled boolean DEFAULT false,
    discussion_external_id character varying(128),
    discussion_title character varying(255),
    comments_collect_enabled boolean DEFAULT false,
    alert_enabled boolean DEFAULT false,
    save_conditions jsonb DEFAULT '[]'::jsonb,
    processing jsonb DEFAULT '{}'::jsonb,
    alert_delivery jsonb DEFAULT '{}'::jsonb,
    alert_rules jsonb DEFAULT '[]'::jsonb,
    conditions_mode character varying(20) DEFAULT 'any_of'::character varying,
    publish_targets jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    auth_status character varying(20) DEFAULT 'unknown'::character varying,
    auth_checked_at timestamp with time zone,
    auth_error text,
    auth_capabilities jsonb DEFAULT '{}'::jsonb,
    CONSTRAINT smm_brand_channels_kind_check CHECK (((kind)::text = ANY ((ARRAY['channel'::character varying, 'group'::character varying, 'public'::character varying])::text[]))),
    CONSTRAINT smm_brand_channels_network_check CHECK (((network)::text = ANY ((ARRAY['tg'::character varying, 'vk'::character varying])::text[]))),
    CONSTRAINT smm_brand_channels_role_check CHECK (((role)::text = ANY ((ARRAY['own'::character varying, 'competitor'::character varying, 'source'::character varying])::text[])))
);
 &   DROP TABLE public.smm_brand_channels;
       public         heap    postgres    false            L           1259    35888    smm_brand_channels_id_seq    SEQUENCE     ‘   CREATE SEQUENCE public.smm_brand_channels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 0   DROP SEQUENCE public.smm_brand_channels_id_seq;
       public          postgres    false    333                        0    0    smm_brand_channels_id_seq    SEQUENCE OWNED BY     W   ALTER SEQUENCE public.smm_brand_channels_id_seq OWNED BY public.smm_brand_channels.id;
          public          postgres    false    332            K           1259    35874 
   smm_brands    TABLE     n  CREATE TABLE public.smm_brands (
    id integer NOT NULL,
    user_id integer NOT NULL,
    group_id integer,
    name character varying(255) NOT NULL,
    color character varying(7) DEFAULT '#3B82F6'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.smm_brands;
       public         heap    postgres    false            J           1259    35873    smm_brands_id_seq    SEQUENCE     ‰   CREATE SEQUENCE public.smm_brands_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 (   DROP SEQUENCE public.smm_brands_id_seq;
       public          postgres    false    331            !           0    0    smm_brands_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.smm_brands_id_seq OWNED BY public.smm_brands.id;
          public          postgres    false    330            W           1259    36016    smm_channel_counters    TABLE       CREATE TABLE public.smm_channel_counters (
    id integer NOT NULL,
    user_id integer NOT NULL,
    channel_id integer NOT NULL,
    day date NOT NULL,
    sent integer DEFAULT 0,
    received integer DEFAULT 0,
    failed integer DEFAULT 0,
    alerts_sent integer DEFAULT 0
);
 (   DROP TABLE public.smm_channel_counters;
       public         heap    postgres    false            V           1259    36015    smm_channel_counters_id_seq    SEQUENCE     “   CREATE SEQUENCE public.smm_channel_counters_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 2   DROP SEQUENCE public.smm_channel_counters_id_seq;
       public          postgres    false    343            "           0    0    smm_channel_counters_id_seq    SEQUENCE OWNED BY     [   ALTER SEQUENCE public.smm_channel_counters_id_seq OWNED BY public.smm_channel_counters.id;
          public          postgres    false    342            `           1259    36109    smm_channel_metric_snapshots    TABLE     Ц   CREATE TABLE public.smm_channel_metric_snapshots (
    id integer NOT NULL,
    channel_id integer NOT NULL,
    subscribers integer DEFAULT 0,
    captured_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 0   DROP TABLE public.smm_channel_metric_snapshots;
       public         heap    postgres    false            _           1259    36108 #   smm_channel_metric_snapshots_id_seq    SEQUENCE     ›   CREATE SEQUENCE public.smm_channel_metric_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 :   DROP SEQUENCE public.smm_channel_metric_snapshots_id_seq;
       public          postgres    false    352            #           0    0 #   smm_channel_metric_snapshots_id_seq    SEQUENCE OWNED BY     k   ALTER SEQUENCE public.smm_channel_metric_snapshots_id_seq OWNED BY public.smm_channel_metric_snapshots.id;
          public          postgres    false    351            U           1259    35990    smm_competitor_snapshots    TABLE     ’  CREATE TABLE public.smm_competitor_snapshots (
    id integer NOT NULL,
    channel_id integer NOT NULL,
    external_post_id character varying(128),
    post_text text,
    views integer DEFAULT 0,
    likes integer DEFAULT 0,
    comments integer DEFAULT 0,
    reposts integer DEFAULT 0,
    posted_at timestamp with time zone,
    collected_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 ,   DROP TABLE public.smm_competitor_snapshots;
       public         heap    postgres    false            T           1259    35989    smm_competitor_snapshots_id_seq    SEQUENCE     —   CREATE SEQUENCE public.smm_competitor_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 6   DROP SEQUENCE public.smm_competitor_snapshots_id_seq;
       public          postgres    false    341            $           0    0    smm_competitor_snapshots_id_seq    SEQUENCE OWNED BY     c   ALTER SEQUENCE public.smm_competitor_snapshots_id_seq OWNED BY public.smm_competitor_snapshots.id;
          public          postgres    false    340            O           1259    35923    smm_inbox_items    TABLE     †  CREATE TABLE public.smm_inbox_items (
    id integer NOT NULL,
    user_id integer NOT NULL,
    brand_id integer,
    network character varying(10) NOT NULL,
    channel_id integer,
    thread_id character varying(128),
    type character varying(20) NOT NULL,
    author character varying(255),
    text text,
    status character varying(20) DEFAULT 'new'::character varying NOT NULL,
    external_msg_id character varying(128),
    edited_text text,
    meta jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT smm_inbox_items_network_check CHECK (((network)::text = ANY ((ARRAY['tg'::character varying, 'vk'::character varying])::text[]))),
    CONSTRAINT smm_inbox_items_status_check CHECK (((status)::text = ANY ((ARRAY['new'::character varying, 'read'::character varying, 'replied'::character varying, 'archived'::character varying, 'reply_failed'::character varying, 'in_progress'::character varying])::text[]))),
    CONSTRAINT smm_inbox_items_type_check CHECK (((type)::text = ANY ((ARRAY['dm'::character varying, 'comment'::character varying, 'reaction'::character varying])::text[])))
);
 #   DROP TABLE public.smm_inbox_items;
       public         heap    postgres    false            N           1259    35922    smm_inbox_items_id_seq    SEQUENCE     Ћ   CREATE SEQUENCE public.smm_inbox_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.smm_inbox_items_id_seq;
       public          postgres    false    335            %           0    0    smm_inbox_items_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.smm_inbox_items_id_seq OWNED BY public.smm_inbox_items.id;
          public          postgres    false    334            \           1259    36075    smm_message_events    TABLE     ш  CREATE TABLE public.smm_message_events (
    id integer NOT NULL,
    user_id integer NOT NULL,
    channel_id integer,
    direction character varying(20) NOT NULL,
    platform character varying(10) NOT NULL,
    post_id integer,
    external_msg_id character varying(128),
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT smm_message_events_direction_check CHECK (((direction)::text = ANY ((ARRAY['collected'::character varying, 'published'::character varying, 'alert'::character varying, 'failed'::character varying])::text[]))),
    CONSTRAINT smm_message_events_platform_check CHECK (((platform)::text = ANY ((ARRAY['tg'::character varying, 'vk'::character varying])::text[])))
);
 &   DROP TABLE public.smm_message_events;
       public         heap    postgres    false            [           1259    36074    smm_message_events_id_seq    SEQUENCE     ‘   CREATE SEQUENCE public.smm_message_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 0   DROP SEQUENCE public.smm_message_events_id_seq;
       public          postgres    false    348            &           0    0    smm_message_events_id_seq    SEQUENCE OWNED BY     W   ALTER SEQUENCE public.smm_message_events_id_seq OWNED BY public.smm_message_events.id;
          public          postgres    false    347            ^           1259    36095    smm_post_metric_snapshots    TABLE       CREATE TABLE public.smm_post_metric_snapshots (
    id integer NOT NULL,
    user_id integer NOT NULL,
    platform character varying(10) NOT NULL,
    post_id integer NOT NULL,
    views integer DEFAULT 0,
    likes integer DEFAULT 0,
    comments integer DEFAULT 0,
    reposts integer DEFAULT 0,
    captured_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT smm_post_metric_snapshots_platform_check CHECK (((platform)::text = ANY ((ARRAY['tg'::character varying, 'vk'::character varying])::text[])))
);
 -   DROP TABLE public.smm_post_metric_snapshots;
       public         heap    postgres    false            ]           1259    36094     smm_post_metric_snapshots_id_seq    SEQUENCE        CREATE SEQUENCE public.smm_post_metric_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 7   DROP SEQUENCE public.smm_post_metric_snapshots_id_seq;
       public          postgres    false    350            '           0    0     smm_post_metric_snapshots_id_seq    SEQUENCE OWNED BY     e   ALTER SEQUENCE public.smm_post_metric_snapshots_id_seq OWNED BY public.smm_post_metric_snapshots.id;
          public          postgres    false    349            Q           1259    35949    smm_publish_jobs    TABLE     E  CREATE TABLE public.smm_publish_jobs (
    id integer NOT NULL,
    user_id integer NOT NULL,
    brand_id integer,
    source_text text NOT NULL,
    media jsonb DEFAULT '[]'::jsonb,
    targets jsonb DEFAULT '[]'::jsonb,
    adapters_result jsonb DEFAULT '{}'::jsonb,
    publish_at timestamp with time zone,
    status character varying(30) DEFAULT 'draft'::character varying NOT NULL,
    retry_count integer DEFAULT 0,
    last_error text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 $   DROP TABLE public.smm_publish_jobs;
       public         heap    postgres    false            P           1259    35948    smm_publish_jobs_id_seq    SEQUENCE     Џ   CREATE SEQUENCE public.smm_publish_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.smm_publish_jobs_id_seq;
       public          postgres    false    337            (           0    0    smm_publish_jobs_id_seq    SEQUENCE OWNED BY     S   ALTER SEQUENCE public.smm_publish_jobs_id_seq OWNED BY public.smm_publish_jobs.id;
          public          postgres    false    336            G           1259    35845    system_settings    TABLE     ®   CREATE TABLE public.system_settings (
    key character varying(100) NOT NULL,
    value jsonb NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 #   DROP TABLE public.system_settings;
       public         heap    postgres    false            и            1259    34865    tg_dedup_cache    TABLE     l  CREATE TABLE public.tg_dedup_cache (
    id integer NOT NULL,
    user_id integer NOT NULL,
    text_hash character varying(64) NOT NULL,
    chat_id bigint NOT NULL,
    rule_id character varying(64),
    channel_to_post character varying(50),
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 "   DROP TABLE public.tg_dedup_cache;
       public         heap    postgres    false            з            1259    34864    tg_dedup_cache_id_seq    SEQUENCE     Ќ   CREATE SEQUENCE public.tg_dedup_cache_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 ,   DROP SEQUENCE public.tg_dedup_cache_id_seq;
       public          postgres    false    232            )           0    0    tg_dedup_cache_id_seq    SEQUENCE OWNED BY     O   ALTER SEQUENCE public.tg_dedup_cache_id_seq OWNED BY public.tg_dedup_cache.id;
          public          postgres    false    231            м            1259    34888 
   tg_digests    TABLE     ю   CREATE TABLE public.tg_digests (
    id integer NOT NULL,
    user_id integer NOT NULL,
    chat_id bigint NOT NULL,
    digest_text text NOT NULL,
    message_count integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.tg_digests;
       public         heap    postgres    false            л            1259    34887    tg_digests_id_seq    SEQUENCE     ‰   CREATE SEQUENCE public.tg_digests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 (   DROP SEQUENCE public.tg_digests_id_seq;
       public          postgres    false    236            *           0    0    tg_digests_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.tg_digests_id_seq OWNED BY public.tg_digests.id;
          public          postgres    false    235            ж            1259    34849 	   tg_events    TABLE     Ї  CREATE TABLE public.tg_events (
    id integer NOT NULL,
    user_id integer NOT NULL,
    chat_id bigint,
    message_id bigint,
    event_type character varying(50) NOT NULL,
    rule_id character varying(64),
    matched_conditions jsonb DEFAULT '[]'::jsonb,
    text_hash character varying(64),
    text_preview text,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.tg_events;
       public         heap    postgres    false            е            1259    34848    tg_events_id_seq    SEQUENCE     €   CREATE SEQUENCE public.tg_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.tg_events_id_seq;
       public          postgres    false    230            +           0    0    tg_events_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.tg_events_id_seq OWNED BY public.tg_events.id;
          public          postgres    false    229            д            1259    34835    tg_post_templates    TABLE     ^  CREATE TABLE public.tg_post_templates (
    id integer NOT NULL,
    user_id integer NOT NULL,
    name character varying(200) NOT NULL,
    text text DEFAULT ''::text NOT NULL,
    hashtags text DEFAULT ''::text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 %   DROP TABLE public.tg_post_templates;
       public         heap    postgres    false            г            1259    34834    tg_post_templates_id_seq    SEQUENCE     ђ   CREATE SEQUENCE public.tg_post_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 /   DROP SEQUENCE public.tg_post_templates_id_seq;
       public          postgres    false    228            ,           0    0    tg_post_templates_id_seq    SEQUENCE OWNED BY     U   ALTER SEQUENCE public.tg_post_templates_id_seq OWNED BY public.tg_post_templates.id;
          public          postgres    false    227            в            1259    34802    tg_posts    TABLE     K  CREATE TABLE public.tg_posts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    domain character varying(255),
    url text,
    title character varying(500),
    author character varying(255),
    avatar text,
    post_date timestamp with time zone,
    post_text text,
    screenshot text,
    images jsonb DEFAULT '[]'::jsonb,
    image_over_text text,
    comments integer DEFAULT 0,
    reposts integer DEFAULT 0,
    likes integer DEFAULT 0,
    views integer DEFAULT 0,
    is_ad boolean DEFAULT false,
    status character varying(50) DEFAULT 'collected'::character varying,
    post_type character varying(50),
    to_tg boolean DEFAULT false,
    to_tw boolean DEFAULT false,
    to_wp boolean DEFAULT false,
    to_vk boolean DEFAULT false,
    to_dzen boolean DEFAULT false,
    to_instagram boolean DEFAULT false,
    to_threads boolean DEFAULT false,
    target_channels jsonb DEFAULT '[]'::jsonb,
    target_groups jsonb DEFAULT '[]'::jsonb,
    metadata jsonb DEFAULT '{}'::jsonb,
    publish_at timestamp with time zone,
    telegram_message_id bigint,
    telegram_chat_id text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tg_posts_status_check CHECK (((status)::text = ANY ((ARRAY['created'::character varying, 'collected'::character varying, 'processing'::character varying, 'ready'::character varying, 'review'::character varying, 'publishing'::character varying, 'published'::character varying, 'distributed'::character varying, 'deleted'::character varying])::text[])))
);
    DROP TABLE public.tg_posts;
       public         heap    postgres    false            б            1259    34801    tg_posts_id_seq    SEQUENCE     ‡   CREATE SEQUENCE public.tg_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.tg_posts_id_seq;
       public          postgres    false    226            -           0    0    tg_posts_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.tg_posts_id_seq OWNED BY public.tg_posts.id;
          public          postgres    false    225            а            1259    34768    tg_profiles    TABLE     №  CREATE TABLE public.tg_profiles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    publish_enabled boolean DEFAULT false,
    collect_enabled boolean DEFAULT false,
    schedule_type character varying(20) DEFAULT 'immediate'::character varying,
    time_intervals jsonb DEFAULT '[]'::jsonb,
    api_id character varying(50),
    api_hash character varying(100),
    chats_to_read jsonb DEFAULT '[]'::jsonb,
    save_conditions jsonb DEFAULT '[]'::jsonb,
    channel_to_post character varying(50),
    channels_to_post jsonb DEFAULT '[]'::jsonb,
    alert_enabled boolean DEFAULT false,
    alert_rules jsonb DEFAULT '[]'::jsonb,
    process_enabled boolean DEFAULT false,
    processing_description text,
    remove_emojis boolean DEFAULT false,
    remove_images boolean DEFAULT false,
    clean_html boolean DEFAULT false,
    process_services jsonb,
    status_review_after_process boolean DEFAULT false,
    add_static_html boolean DEFAULT false,
    static_html_content text,
    telegram_username character varying(255),
    auth_state character varying(50) DEFAULT 'authorized'::character varying,
    auth_phone_code_hash character varying(255),
    auth_phone_number character varying(50),
    summarize_enabled boolean DEFAULT false,
    summarize_min_length integer DEFAULT 500,
    digest_interval_min integer DEFAULT 30,
    digest_channel character varying(50),
    classification_enabled boolean DEFAULT false,
    classification_categories jsonb DEFAULT '["РЅРѕРІРѕСЃС‚Рё", "СЂРµРєР»Р°РјР°", "С‚РµС…РЅРѕР»РѕРіРёРё", "С„РёРЅР°РЅСЃС‹", "РґСЂСѓРіРѕРµ"]'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.tg_profiles;
       public         heap    postgres    false            Я            1259    34767    tg_profiles_id_seq    SEQUENCE     Љ   CREATE SEQUENCE public.tg_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 )   DROP SEQUENCE public.tg_profiles_id_seq;
       public          postgres    false    224            .           0    0    tg_profiles_id_seq    SEQUENCE OWNED BY     I   ALTER SEQUENCE public.tg_profiles_id_seq OWNED BY public.tg_profiles.id;
          public          postgres    false    223            к            1259    34875    tg_summary_cache    TABLE        CREATE TABLE public.tg_summary_cache (
    id integer NOT NULL,
    text_hash character varying(64) NOT NULL,
    summary text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 $   DROP TABLE public.tg_summary_cache;
       public         heap    postgres    false            й            1259    34874    tg_summary_cache_id_seq    SEQUENCE     Џ   CREATE SEQUENCE public.tg_summary_cache_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.tg_summary_cache_id_seq;
       public          postgres    false    234            /           0    0    tg_summary_cache_id_seq    SEQUENCE OWNED BY     S   ALTER SEQUENCE public.tg_summary_cache_id_seq OWNED BY public.tg_summary_cache.id;
          public          postgres    false    233            ш            1259    35030 
   threads_posts    TABLE     Й  CREATE TABLE public.threads_posts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    domain character varying(255),
    url text,
    title character varying(500),
    author character varying(255),
    avatar text,
    post_date timestamp with time zone,
    post_text text,
    screenshot text,
    images jsonb DEFAULT '[]'::jsonb,
    image_over_text text,
    comments integer DEFAULT 0,
    reposts integer DEFAULT 0,
    likes integer DEFAULT 0,
    views integer DEFAULT 0,
    is_ad boolean DEFAULT false,
    status character varying(50) DEFAULT 'collected'::character varying,
    post_type character varying(50),
    to_tg boolean DEFAULT false,
    to_tw boolean DEFAULT false,
    to_wp boolean DEFAULT false,
    to_vk boolean DEFAULT false,
    to_dzen boolean DEFAULT false,
    to_instagram boolean DEFAULT false,
    to_threads boolean DEFAULT false,
    target_channels jsonb DEFAULT '[]'::jsonb,
    target_groups jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT threads_posts_status_check CHECK (((status)::text = ANY ((ARRAY['created'::character varying, 'collected'::character varying, 'processing'::character varying, 'ready'::character varying, 'review'::character varying, 'publishing'::character varying, 'published'::character varying, 'distributed'::character varying, 'deleted'::character varying])::text[])))
);
 !   DROP TABLE public.threads_posts;
       public         heap    postgres    false            ч            1259    35029    threads_posts_id_seq    SEQUENCE     Њ   CREATE SEQUENCE public.threads_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.threads_posts_id_seq;
       public          postgres    false    248            0           0    0    threads_posts_id_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.threads_posts_id_seq OWNED BY public.threads_posts.id;
          public          postgres    false    247            ц            1259    35007    threads_profiles    TABLE     х  CREATE TABLE public.threads_profiles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    publish_enabled boolean DEFAULT false,
    collect_enabled boolean DEFAULT false,
    schedule_type character varying(20) DEFAULT 'immediate'::character varying,
    time_intervals jsonb DEFAULT '[]'::jsonb,
    access_token character varying(512),
    refresh_token character varying(512),
    token_expires_at timestamp with time zone,
    threads_user_id character varying(100),
    instagram_handle character varying(255),
    process_enabled boolean DEFAULT false,
    processing_description text,
    remove_emojis boolean DEFAULT false,
    remove_images boolean DEFAULT false,
    clean_html boolean DEFAULT false,
    process_services jsonb,
    status_review_after_process boolean DEFAULT false,
    add_static_html boolean DEFAULT false,
    static_html_content text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 $   DROP TABLE public.threads_profiles;
       public         heap    postgres    false            х            1259    35006    threads_profiles_id_seq    SEQUENCE     Џ   CREATE SEQUENCE public.threads_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.threads_profiles_id_seq;
       public          postgres    false    246            1           0    0    threads_profiles_id_seq    SEQUENCE OWNED BY     S   ALTER SEQUENCE public.threads_profiles_id_seq OWNED BY public.threads_profiles.id;
          public          postgres    false    245            ъ            1259    35060    threads_selenium_sessions    TABLE     3  CREATE TABLE public.threads_selenium_sessions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    status character varying(40) NOT NULL,
    detail_message text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 -   DROP TABLE public.threads_selenium_sessions;
       public         heap    postgres    false            щ            1259    35059     threads_selenium_sessions_id_seq    SEQUENCE        CREATE SEQUENCE public.threads_selenium_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 7   DROP SEQUENCE public.threads_selenium_sessions_id_seq;
       public          postgres    false    250            2           0    0     threads_selenium_sessions_id_seq    SEQUENCE OWNED BY     e   ALTER SEQUENCE public.threads_selenium_sessions_id_seq OWNED BY public.threads_selenium_sessions.id;
          public          postgres    false    249                       1259    35345    tw_posts    TABLE     ї  CREATE TABLE public.tw_posts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    domain character varying(255),
    url text,
    title character varying(500),
    author character varying(255),
    avatar text,
    post_date timestamp with time zone,
    post_text text,
    screenshot text,
    images jsonb DEFAULT '[]'::jsonb,
    image_over_text text,
    comments integer DEFAULT 0,
    reposts integer DEFAULT 0,
    likes integer DEFAULT 0,
    views integer DEFAULT 0,
    is_ad boolean DEFAULT false,
    status character varying(50) DEFAULT 'collected'::character varying,
    post_type character varying(50),
    to_tg boolean DEFAULT false,
    to_tw boolean DEFAULT false,
    to_wp boolean DEFAULT false,
    to_vk boolean DEFAULT false,
    to_dzen boolean DEFAULT false,
    to_instagram boolean DEFAULT false,
    to_threads boolean DEFAULT false,
    target_channels jsonb DEFAULT '[]'::jsonb,
    target_groups jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tw_posts_status_check CHECK (((status)::text = ANY ((ARRAY['created'::character varying, 'collected'::character varying, 'processing'::character varying, 'ready'::character varying, 'review'::character varying, 'publishing'::character varying, 'published'::character varying, 'distributed'::character varying, 'deleted'::character varying])::text[])))
);
    DROP TABLE public.tw_posts;
       public         heap    postgres    false                       1259    35344    tw_posts_id_seq    SEQUENCE     ‡   CREATE SEQUENCE public.tw_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.tw_posts_id_seq;
       public          postgres    false    280            3           0    0    tw_posts_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.tw_posts_id_seq OWNED BY public.tw_posts.id;
          public          postgres    false    279                       1259    35318    tw_profiles    TABLE        CREATE TABLE public.tw_profiles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    publish_enabled boolean DEFAULT false,
    collect_enabled boolean DEFAULT false,
    schedule_type character varying(20) DEFAULT 'immediate'::character varying,
    time_intervals jsonb DEFAULT '[]'::jsonb,
    use_proxy boolean DEFAULT false,
    proxy_user character varying(100),
    proxy_pass character varying(100),
    proxy_host character varying(255),
    proxy_port integer,
    twitter_username character varying(100),
    twitter_password character varying(255),
    twitter_oauth_access_token text,
    twitter_oauth_refresh_token text,
    twitter_oauth_expires_at timestamp with time zone,
    twitter_rest_id character varying(32),
    oauth_pkce_verifier character varying(128),
    oauth_pkce_expires_at timestamp with time zone,
    take_screenshot_collect boolean DEFAULT false,
    screenshot_xpath text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.tw_profiles;
       public         heap    postgres    false                       1259    35316    tw_profiles_id_seq    SEQUENCE     Љ   CREATE SEQUENCE public.tw_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 )   DROP SEQUENCE public.tw_profiles_id_seq;
       public          postgres    false    278            4           0    0    tw_profiles_id_seq    SEQUENCE OWNED BY     I   ALTER SEQUENCE public.tw_profiles_id_seq OWNED BY public.tw_profiles.id;
          public          postgres    false    277            Z           1259    36040 	   url_posts    TABLE     Б  CREATE TABLE public.url_posts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    domain character varying(255),
    url text,
    title character varying(500),
    author character varying(255),
    avatar text,
    post_date timestamp with time zone,
    post_text text,
    screenshot text,
    images jsonb DEFAULT '[]'::jsonb,
    image_over_text text,
    comments integer DEFAULT 0,
    reposts integer DEFAULT 0,
    likes integer DEFAULT 0,
    views integer DEFAULT 0,
    is_ad boolean DEFAULT false,
    status character varying(50) DEFAULT 'collected'::character varying,
    post_type character varying(50),
    to_tg boolean DEFAULT false,
    to_tw boolean DEFAULT false,
    to_wp boolean DEFAULT false,
    to_vk boolean DEFAULT false,
    to_dzen boolean DEFAULT false,
    to_instagram boolean DEFAULT false,
    to_threads boolean DEFAULT false,
    target_channels jsonb DEFAULT '[]'::jsonb,
    target_groups jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT url_posts_status_check CHECK (((status)::text = ANY ((ARRAY['created'::character varying, 'collected'::character varying, 'processing'::character varying, 'ready'::character varying, 'review'::character varying, 'publishing'::character varying, 'published'::character varying, 'distributed'::character varying, 'deleted'::character varying])::text[])))
);
    DROP TABLE public.url_posts;
       public         heap    postgres    false            Y           1259    36039    url_posts_id_seq    SEQUENCE     €   CREATE SEQUENCE public.url_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.url_posts_id_seq;
       public          postgres    false    346            5           0    0    url_posts_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.url_posts_id_seq OWNED BY public.url_posts.id;
          public          postgres    false    345                       1259    35156    user_role_tariff_history    TABLE     _  CREATE TABLE public.user_role_tariff_history (
    id integer NOT NULL,
    user_id integer NOT NULL,
    changed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    changed_by_user_id integer,
    role_old character varying(20),
    role_new character varying(20),
    tariff_old character varying(50),
    tariff_new character varying(50)
);
 ,   DROP TABLE public.user_role_tariff_history;
       public         heap    postgres    false                       1259    35155    user_role_tariff_history_id_seq    SEQUENCE     —   CREATE SEQUENCE public.user_role_tariff_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 6   DROP SEQUENCE public.user_role_tariff_history_id_seq;
       public          postgres    false    262            6           0    0    user_role_tariff_history_id_seq    SEQUENCE OWNED BY     c   ALTER SEQUENCE public.user_role_tariff_history_id_seq OWNED BY public.user_role_tariff_history.id;
          public          postgres    false    261            ь            1259    35073    users    TABLE       CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(20) DEFAULT 'guest'::character varying NOT NULL,
    tariff character varying(50) DEFAULT 'free'::character varying NOT NULL,
    is_email_verified boolean DEFAULT false,
    is_blocked boolean DEFAULT false NOT NULL,
    billing_provider character varying(32),
    billing_customer_id character varying(255),
    billing_subscription_id character varying(255),
    subscription_status character varying(40),
    subscription_current_period_end timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_role_check CHECK (((role)::text = ANY ((ARRAY['guest'::character varying, 'user'::character varying, 'admin'::character varying, 'manager'::character varying, 'author'::character varying])::text[])))
);
    DROP TABLE public.users;
       public         heap    postgres    false            ы            1259    35072    users_id_seq    SEQUENCE     „   CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 #   DROP SEQUENCE public.users_id_seq;
       public          postgres    false    252            7           0    0    users_id_seq    SEQUENCE OWNED BY     =   ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;
          public          postgres    false    251                       1259    35228    vk_posts    TABLE     n  CREATE TABLE public.vk_posts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    domain character varying(255),
    url text,
    title character varying(500),
    author character varying(255),
    avatar text,
    post_date timestamp with time zone,
    post_text text,
    screenshot text,
    images jsonb DEFAULT '[]'::jsonb,
    image_over_text text,
    comments integer DEFAULT 0,
    reposts integer DEFAULT 0,
    likes integer DEFAULT 0,
    views integer DEFAULT 0,
    is_ad boolean DEFAULT false,
    status character varying(50) DEFAULT 'collected'::character varying,
    post_type character varying(50),
    to_tg boolean DEFAULT false,
    to_tw boolean DEFAULT false,
    to_wp boolean DEFAULT false,
    to_vk boolean DEFAULT false,
    to_dzen boolean DEFAULT false,
    to_instagram boolean DEFAULT false,
    to_threads boolean DEFAULT false,
    target_channels jsonb DEFAULT '[]'::jsonb,
    target_groups jsonb DEFAULT '[]'::jsonb,
    vk_source_id integer,
    attachments jsonb DEFAULT '[]'::jsonb,
    publish_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    published_vk_post_id integer,
    published_owner_id bigint,
    CONSTRAINT vk_posts_status_check CHECK (((status)::text = ANY ((ARRAY['created'::character varying, 'collected'::character varying, 'processing'::character varying, 'ready'::character varying, 'review'::character varying, 'publishing'::character varying, 'published'::character varying, 'distributed'::character varying, 'deleted'::character varying])::text[])))
);
    DROP TABLE public.vk_posts;
       public         heap    postgres    false            
           1259    35226    vk_posts_id_seq    SEQUENCE     ‡   CREATE SEQUENCE public.vk_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.vk_posts_id_seq;
       public          postgres    false    270            8           0    0    vk_posts_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.vk_posts_id_seq OWNED BY public.vk_posts.id;
          public          postgres    false    269            
           1259    35182    vk_profiles    TABLE     Г  CREATE TABLE public.vk_profiles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    publish_enabled boolean DEFAULT false,
    collect_enabled boolean DEFAULT false,
    schedule_type character varying(20) DEFAULT 'immediate'::character varying,
    time_intervals jsonb DEFAULT '[]'::jsonb,
    owner_id character varying(50),
    friends_only boolean DEFAULT false,
    from_group boolean DEFAULT false,
    message text,
    attachments text,
    signed boolean DEFAULT false,
    mark_as_ads boolean DEFAULT false,
    access_token character varying(512),
    user_access_token character varying(512),
    groups_to_read jsonb DEFAULT '[]'::jsonb,
    users_to_read jsonb DEFAULT '[]'::jsonb,
    group_to_post character varying(50),
    process_enabled boolean DEFAULT false,
    processing_description text,
    remove_emojis boolean DEFAULT false,
    remove_images boolean DEFAULT false,
    clean_html boolean DEFAULT false,
    process_services jsonb,
    status_review_after_process boolean DEFAULT false,
    add_static_html boolean DEFAULT false,
    static_html_content text,
    post_to_own_wall boolean DEFAULT false,
    vk_user_id bigint,
    vk_app_id character varying(32),
    vk_app_secret character varying(512),
    vk_frontend_url character varying(512),
    vk_public_gateway_url character varying(512),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
    DROP TABLE public.vk_profiles;
       public         heap    postgres    false            	           1259    35181    vk_profiles_id_seq    SEQUENCE     Љ   CREATE SEQUENCE public.vk_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 )   DROP SEQUENCE public.vk_profiles_id_seq;
       public          postgres    false    266            9           0    0    vk_profiles_id_seq    SEQUENCE OWNED BY     I   ALTER SEQUENCE public.vk_profiles_id_seq OWNED BY public.vk_profiles.id;
          public          postgres    false    265            Ъ            1259    34706    wp_collect_profile    TABLE     h  CREATE TABLE public.wp_collect_profile (
    id integer NOT NULL,
    user_id integer NOT NULL,
    collect_enabled boolean DEFAULT false,
    collect_all_available boolean DEFAULT true,
    collect_limit integer DEFAULT 1,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 &   DROP TABLE public.wp_collect_profile;
       public         heap    postgres    false            Щ            1259    34705    wp_collect_profile_id_seq    SEQUENCE     ‘   CREATE SEQUENCE public.wp_collect_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 0   DROP SEQUENCE public.wp_collect_profile_id_seq;
       public          postgres    false    218            :           0    0    wp_collect_profile_id_seq    SEQUENCE OWNED BY     W   ALTER SEQUENCE public.wp_collect_profile_id_seq OWNED BY public.wp_collect_profile.id;
          public          postgres    false    217            Ь            1259    34720    wp_collect_sites    TABLE     V  CREATE TABLE public.wp_collect_sites (
    id integer NOT NULL,
    profile_id integer NOT NULL,
    user_id integer NOT NULL,
    site_url text,
    schedule_type character varying(50) DEFAULT 'on_new_messages'::character varying,
    time_intervals character varying(5),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 $   DROP TABLE public.wp_collect_sites;
       public         heap    postgres    false            Ы            1259    34719    wp_collect_sites_id_seq    SEQUENCE     Џ   CREATE SEQUENCE public.wp_collect_sites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.wp_collect_sites_id_seq;
       public          postgres    false    220            ;           0    0    wp_collect_sites_id_seq    SEQUENCE OWNED BY     S   ALTER SEQUENCE public.wp_collect_sites_id_seq OWNED BY public.wp_collect_sites.id;
          public          postgres    false    219            Ю            1259    34738    wp_posts    TABLE     ї  CREATE TABLE public.wp_posts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    domain character varying(255),
    url text,
    title character varying(500),
    author character varying(255),
    avatar text,
    post_date timestamp with time zone,
    post_text text,
    screenshot text,
    images jsonb DEFAULT '[]'::jsonb,
    image_over_text text,
    comments integer DEFAULT 0,
    reposts integer DEFAULT 0,
    likes integer DEFAULT 0,
    views integer DEFAULT 0,
    is_ad boolean DEFAULT false,
    status character varying(50) DEFAULT 'collected'::character varying,
    post_type character varying(50),
    to_tg boolean DEFAULT false,
    to_tw boolean DEFAULT false,
    to_wp boolean DEFAULT false,
    to_vk boolean DEFAULT false,
    to_dzen boolean DEFAULT false,
    to_instagram boolean DEFAULT false,
    to_threads boolean DEFAULT false,
    target_channels jsonb DEFAULT '[]'::jsonb,
    target_groups jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT wp_posts_status_check CHECK (((status)::text = ANY ((ARRAY['created'::character varying, 'collected'::character varying, 'processing'::character varying, 'ready'::character varying, 'review'::character varying, 'publishing'::character varying, 'published'::character varying, 'distributed'::character varying, 'deleted'::character varying])::text[])))
);
    DROP TABLE public.wp_posts;
       public         heap    postgres    false            Э            1259    34737    wp_posts_id_seq    SEQUENCE     ‡   CREATE SEQUENCE public.wp_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.wp_posts_id_seq;
       public          postgres    false    222            <           0    0    wp_posts_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.wp_posts_id_seq OWNED BY public.wp_posts.id;
          public          postgres    false    221            Ш            1259    34683    wp_publish_profile    TABLE     Й  CREATE TABLE public.wp_publish_profile (
    id integer NOT NULL,
    user_id integer NOT NULL,
    publish_enabled boolean DEFAULT false,
    schedule_type character varying(50) DEFAULT 'on_new_messages'::character varying,
    time_intervals jsonb DEFAULT '[]'::jsonb,
    site_url text,
    username character varying(255),
    app_password character varying(255),
    publish_all_ready boolean DEFAULT true,
    publish_limit integer,
    publish_interval_minutes integer,
    process_before_publish boolean DEFAULT false,
    process_description text,
    remove_emojis boolean DEFAULT false,
    remove_images boolean DEFAULT false,
    clean_html boolean DEFAULT false,
    process_services jsonb,
    status_review_after_process boolean DEFAULT false,
    add_static_html boolean DEFAULT false,
    static_html_content text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
 &   DROP TABLE public.wp_publish_profile;
       public         heap    postgres    false            Ч            1259    34682    wp_publish_profile_id_seq    SEQUENCE     ‘   CREATE SEQUENCE public.wp_publish_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 0   DROP SEQUENCE public.wp_publish_profile_id_seq;
       public          postgres    false    216            =           0    0    wp_publish_profile_id_seq    SEQUENCE OWNED BY     W   ALTER SEQUENCE public.wp_publish_profile_id_seq OWNED BY public.wp_publish_profile.id;
          public          postgres    false    215            z           2604    35305    admin_audit_log id    DEFAULT     x   ALTER TABLE ONLY public.admin_audit_log ALTER COLUMN id SET DEFAULT nextval('public.admin_audit_log_id_seq'::regclass);
 A   ALTER TABLE public.admin_audit_log ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    275    276    276            	           2604    35811    ai_tasks id    DEFAULT     j   ALTER TABLE ONLY public.ai_tasks ALTER COLUMN id SET DEFAULT nextval('public.ai_tasks_id_seq'::regclass);
 :   ALTER TABLE public.ai_tasks ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    321    322    322            x           2604    35290    billing_events id    DEFAULT     v   ALTER TABLE ONLY public.billing_events ALTER COLUMN id SET DEFAULT nextval('public.billing_events_id_seq'::regclass);
 @   ALTER TABLE public.billing_events ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    273    274    274            A           2604    35113    blacklisted_tokens id    DEFAULT     ~   ALTER TABLE ONLY public.blacklisted_tokens ALTER COLUMN id SET DEFAULT nextval('public.blacklisted_tokens_id_seq'::regclass);
 D   ALTER TABLE public.blacklisted_tokens ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    255    256    256            Э           2604    35725    cpost_posts id    DEFAULT     p   ALTER TABLE ONLY public.cpost_posts ALTER COLUMN id SET DEFAULT nextval('public.cpost_posts_id_seq'::regclass);
 =   ALTER TABLE public.cpost_posts ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    313    314    314            Щ           2604    35711    cpost_profiles id    DEFAULT     v   ALTER TABLE ONLY public.cpost_profiles ALTER COLUMN id SET DEFAULT nextval('public.cpost_profiles_id_seq'::regclass);
 @   ALTER TABLE public.cpost_profiles ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    312    311    312                       2604    35784    curl_one_time_done id    DEFAULT     ~   ALTER TABLE ONLY public.curl_one_time_done ALTER COLUMN id SET DEFAULT nextval('public.curl_one_time_done_id_seq'::regclass);
 D   ALTER TABLE public.curl_one_time_done ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    318    317    318            р           2604    35755    curl_settings id    DEFAULT     t   ALTER TABLE ONLY public.curl_settings ALTER COLUMN id SET DEFAULT nextval('public.curl_settings_id_seq'::regclass);
 ?   ALTER TABLE public.curl_settings ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    315    316    316            Я           2604    34922 
   dzen_posts id    DEFAULT     n   ALTER TABLE ONLY public.dzen_posts ALTER COLUMN id SET DEFAULT nextval('public.dzen_posts_id_seq'::regclass);
 <   ALTER TABLE public.dzen_posts ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    240    239    240            Ц           2604    34903    dzen_profiles id    DEFAULT     t   ALTER TABLE ONLY public.dzen_profiles ALTER COLUMN id SET DEFAULT nextval('public.dzen_profiles_id_seq'::regclass);
 ?   ALTER TABLE public.dzen_profiles ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    237    238    238            E           2604    35142    email_verification_tokens id    DEFAULT     Њ   ALTER TABLE ONLY public.email_verification_tokens ALTER COLUMN id SET DEFAULT nextval('public.email_verification_tokens_id_seq'::regclass);
 K   ALTER TABLE public.email_verification_tokens ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    259    260    260                       2604    35837    feedback id    DEFAULT     j   ALTER TABLE ONLY public.feedback ALTER COLUMN id SET DEFAULT nextval('public.feedback_id_seq'::regclass);
 :   ALTER TABLE public.feedback ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    325    326    326            Ї           2604    35511    game_answers id    DEFAULT     r   ALTER TABLE ONLY public.game_answers ALTER COLUMN id SET DEFAULT nextval('public.game_answers_id_seq'::regclass);
 >   ALTER TABLE public.game_answers ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    296    295    296                       2604    35385    game_bots id    DEFAULT     l   ALTER TABLE ONLY public.game_bots ALTER COLUMN id SET DEFAULT nextval('public.game_bots_id_seq'::regclass);
 ;   ALTER TABLE public.game_bots ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    282    281    282            ±           2604    35539    game_media_assets id    DEFAULT     |   ALTER TABLE ONLY public.game_media_assets ALTER COLUMN id SET DEFAULT nextval('public.game_media_assets_id_seq'::regclass);
 C   ALTER TABLE public.game_media_assets ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    298    297    298            ј           2604    35604    game_menu_cart_items id    DEFAULT     ‚   ALTER TABLE ONLY public.game_menu_cart_items ALTER COLUMN id SET DEFAULT nextval('public.game_menu_cart_items_id_seq'::regclass);
 F   ALTER TABLE public.game_menu_cart_items ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    304    303    304            є           2604    35584    game_menu_carts id    DEFAULT     x   ALTER TABLE ONLY public.game_menu_carts ALTER COLUMN id SET DEFAULT nextval('public.game_menu_carts_id_seq'::regclass);
 A   ALTER TABLE public.game_menu_carts ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    302    301    302            µ           2604    35560    game_menu_nodes id    DEFAULT     x   ALTER TABLE ONLY public.game_menu_nodes ALTER COLUMN id SET DEFAULT nextval('public.game_menu_nodes_id_seq'::regclass);
 A   ALTER TABLE public.game_menu_nodes ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    300    299    300            В           2604    35650    game_menu_order_items id    DEFAULT     „   ALTER TABLE ONLY public.game_menu_order_items ALTER COLUMN id SET DEFAULT nextval('public.game_menu_order_items_id_seq'::regclass);
 G   ALTER TABLE public.game_menu_order_items ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    307    308    308            ѕ           2604    35625    game_menu_orders id    DEFAULT     z   ALTER TABLE ONLY public.game_menu_orders ALTER COLUMN id SET DEFAULT nextval('public.game_menu_orders_id_seq'::regclass);
 B   ALTER TABLE public.game_menu_orders ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    305    306    306            ћ           2604    35414 
   game_modes id    DEFAULT     n   ALTER TABLE ONLY public.game_modes ALTER COLUMN id SET DEFAULT nextval('public.game_modes_id_seq'::regclass);
 <   ALTER TABLE public.game_modes ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    285    286    286            ›           2604    35398    game_players id    DEFAULT     r   ALTER TABLE ONLY public.game_players ALTER COLUMN id SET DEFAULT nextval('public.game_players_id_seq'::regclass);
 >   ALTER TABLE public.game_players ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    283    284    284            ¦           2604    35448    game_question_options id    DEFAULT     „   ALTER TABLE ONLY public.game_question_options ALTER COLUMN id SET DEFAULT nextval('public.game_question_options_id_seq'::regclass);
 G   ALTER TABLE public.game_question_options ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    289    290    290            Ј           2604    35432    game_questions id    DEFAULT     v   ALTER TABLE ONLY public.game_questions ALTER COLUMN id SET DEFAULT nextval('public.game_questions_id_seq'::regclass);
 @   ALTER TABLE public.game_questions ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    288    287    288            ®           2604    35491    game_session_questions id    DEFAULT     †   ALTER TABLE ONLY public.game_session_questions ALTER COLUMN id SET DEFAULT nextval('public.game_session_questions_id_seq'::regclass);
 H   ALTER TABLE public.game_session_questions ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    294    293    294            Ё           2604    35466    game_sessions id    DEFAULT     t   ALTER TABLE ONLY public.game_sessions ALTER COLUMN id SET DEFAULT nextval('public.game_sessions_id_seq'::regclass);
 ?   ALTER TABLE public.game_sessions ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    291    292    292            _           2604    35222    group_members id    DEFAULT     t   ALTER TABLE ONLY public.group_members ALTER COLUMN id SET DEFAULT nextval('public.group_members_id_seq'::regclass);
 ?   ALTER TABLE public.group_members ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    267    268    268            I           2604    35177 	   groups id    DEFAULT     f   ALTER TABLE ONLY public.groups ALTER COLUMN id SET DEFAULT nextval('public.groups_id_seq'::regclass);
 8   ALTER TABLE public.groups ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    263    264    264                       2604    35857    guide_blocks id    DEFAULT     r   ALTER TABLE ONLY public.guide_blocks ALTER COLUMN id SET DEFAULT nextval('public.guide_blocks_id_seq'::regclass);
 >   ALTER TABLE public.guide_blocks ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    329    328    329                       2604    34977    instagram_posts id    DEFAULT     x   ALTER TABLE ONLY public.instagram_posts ALTER COLUMN id SET DEFAULT nextval('public.instagram_posts_id_seq'::regclass);
 A   ALTER TABLE public.instagram_posts ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    244    243    244            у           2604    34951    instagram_profiles id    DEFAULT     ~   ALTER TABLE ONLY public.instagram_profiles ALTER COLUMN id SET DEFAULT nextval('public.instagram_profiles_id_seq'::regclass);
 D   ALTER TABLE public.instagram_profiles ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    242    241    242            
           2604    35824    notifications id    DEFAULT     t   ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);
 ?   ALTER TABLE public.notifications ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    324    323    324            C           2604    35125    password_reset_tokens id    DEFAULT     „   ALTER TABLE ONLY public.password_reset_tokens ALTER COLUMN id SET DEFAULT nextval('public.password_reset_tokens_id_seq'::regclass);
 G   ALTER TABLE public.password_reset_tokens ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    257    258    258            u           2604    35272    plan_definitions id    DEFAULT     z   ALTER TABLE ONLY public.plan_definitions ALTER COLUMN id SET DEFAULT nextval('public.plan_definitions_id_seq'::regclass);
 B   ALTER TABLE public.plan_definitions ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    272    271    272            Д           2604    35673    posts id    DEFAULT     d   ALTER TABLE ONLY public.posts ALTER COLUMN id SET DEFAULT nextval('public.posts_id_seq'::regclass);
 7   ALTER TABLE public.posts ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    309    310    310            ?           2604    35096    refresh_tokens id    DEFAULT     v   ALTER TABLE ONLY public.refresh_tokens ALTER COLUMN id SET DEFAULT nextval('public.refresh_tokens_id_seq'::regclass);
 @   ALTER TABLE public.refresh_tokens ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    253    254    254                       2604    35797    service_cycle_log id    DEFAULT     |   ALTER TABLE ONLY public.service_cycle_log ALTER COLUMN id SET DEFAULT nextval('public.service_cycle_log_id_seq'::regclass);
 C   ALTER TABLE public.service_cycle_log ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    320    319    320            <           2604    35974    smm_automations id    DEFAULT     x   ALTER TABLE ONLY public.smm_automations ALTER COLUMN id SET DEFAULT nextval('public.smm_automations_id_seq'::regclass);
 A   ALTER TABLE public.smm_automations ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    339    338    339                        2604    35892    smm_brand_channels id    DEFAULT     ~   ALTER TABLE ONLY public.smm_brand_channels ALTER COLUMN id SET DEFAULT nextval('public.smm_brand_channels_id_seq'::regclass);
 D   ALTER TABLE public.smm_brand_channels ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    332    333    333                       2604    35877 
   smm_brands id    DEFAULT     n   ALTER TABLE ONLY public.smm_brands ALTER COLUMN id SET DEFAULT nextval('public.smm_brands_id_seq'::regclass);
 <   ALTER TABLE public.smm_brands ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    330    331    331            G           2604    36019    smm_channel_counters id    DEFAULT     ‚   ALTER TABLE ONLY public.smm_channel_counters ALTER COLUMN id SET DEFAULT nextval('public.smm_channel_counters_id_seq'::regclass);
 F   ALTER TABLE public.smm_channel_counters ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    342    343    343            i           2604    36112    smm_channel_metric_snapshots id    DEFAULT     ’   ALTER TABLE ONLY public.smm_channel_metric_snapshots ALTER COLUMN id SET DEFAULT nextval('public.smm_channel_metric_snapshots_id_seq'::regclass);
 N   ALTER TABLE public.smm_channel_metric_snapshots ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    352    351    352            A           2604    35993    smm_competitor_snapshots id    DEFAULT     Љ   ALTER TABLE ONLY public.smm_competitor_snapshots ALTER COLUMN id SET DEFAULT nextval('public.smm_competitor_snapshots_id_seq'::regclass);
 J   ALTER TABLE public.smm_competitor_snapshots ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    341    340    341            0           2604    35926    smm_inbox_items id    DEFAULT     x   ALTER TABLE ONLY public.smm_inbox_items ALTER COLUMN id SET DEFAULT nextval('public.smm_inbox_items_id_seq'::regclass);
 A   ALTER TABLE public.smm_inbox_items ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    334    335    335            `           2604    36078    smm_message_events id    DEFAULT     ~   ALTER TABLE ONLY public.smm_message_events ALTER COLUMN id SET DEFAULT nextval('public.smm_message_events_id_seq'::regclass);
 D   ALTER TABLE public.smm_message_events ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    347    348    348            c           2604    36098    smm_post_metric_snapshots id    DEFAULT     Њ   ALTER TABLE ONLY public.smm_post_metric_snapshots ALTER COLUMN id SET DEFAULT nextval('public.smm_post_metric_snapshots_id_seq'::regclass);
 K   ALTER TABLE public.smm_post_metric_snapshots ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    350    349    350            4           2604    35952    smm_publish_jobs id    DEFAULT     z   ALTER TABLE ONLY public.smm_publish_jobs ALTER COLUMN id SET DEFAULT nextval('public.smm_publish_jobs_id_seq'::regclass);
 B   ALTER TABLE public.smm_publish_jobs ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    336    337    337            П           2604    34868    tg_dedup_cache id    DEFAULT     v   ALTER TABLE ONLY public.tg_dedup_cache ALTER COLUMN id SET DEFAULT nextval('public.tg_dedup_cache_id_seq'::regclass);
 @   ALTER TABLE public.tg_dedup_cache ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    231    232    232            У           2604    34891 
   tg_digests id    DEFAULT     n   ALTER TABLE ONLY public.tg_digests ALTER COLUMN id SET DEFAULT nextval('public.tg_digests_id_seq'::regclass);
 <   ALTER TABLE public.tg_digests ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    235    236    236            Л           2604    34852    tg_events id    DEFAULT     l   ALTER TABLE ONLY public.tg_events ALTER COLUMN id SET DEFAULT nextval('public.tg_events_id_seq'::regclass);
 ;   ALTER TABLE public.tg_events ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    229    230    230            Ж           2604    34838    tg_post_templates id    DEFAULT     |   ALTER TABLE ONLY public.tg_post_templates ALTER COLUMN id SET DEFAULT nextval('public.tg_post_templates_id_seq'::regclass);
 C   ALTER TABLE public.tg_post_templates ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    227    228    228            І           2604    34805    tg_posts id    DEFAULT     j   ALTER TABLE ONLY public.tg_posts ALTER COLUMN id SET DEFAULT nextval('public.tg_posts_id_seq'::regclass);
 :   ALTER TABLE public.tg_posts ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    225    226    226            љ           2604    34771    tg_profiles id    DEFAULT     p   ALTER TABLE ONLY public.tg_profiles ALTER COLUMN id SET DEFAULT nextval('public.tg_profiles_id_seq'::regclass);
 =   ALTER TABLE public.tg_profiles ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    224    223    224            С           2604    34878    tg_summary_cache id    DEFAULT     z   ALTER TABLE ONLY public.tg_summary_cache ALTER COLUMN id SET DEFAULT nextval('public.tg_summary_cache_id_seq'::regclass);
 B   ALTER TABLE public.tg_summary_cache ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    233    234    234            "           2604    35033    threads_posts id    DEFAULT     t   ALTER TABLE ONLY public.threads_posts ALTER COLUMN id SET DEFAULT nextval('public.threads_posts_id_seq'::regclass);
 ?   ALTER TABLE public.threads_posts ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    247    248    248                       2604    35010    threads_profiles id    DEFAULT     z   ALTER TABLE ONLY public.threads_profiles ALTER COLUMN id SET DEFAULT nextval('public.threads_profiles_id_seq'::regclass);
 B   ALTER TABLE public.threads_profiles ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    245    246    246            5           2604    35063    threads_selenium_sessions id    DEFAULT     Њ   ALTER TABLE ONLY public.threads_selenium_sessions ALTER COLUMN id SET DEFAULT nextval('public.threads_selenium_sessions_id_seq'::regclass);
 K   ALTER TABLE public.threads_selenium_sessions ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    250    249    250            …           2604    35349    tw_posts id    DEFAULT     j   ALTER TABLE ONLY public.tw_posts ALTER COLUMN id SET DEFAULT nextval('public.tw_posts_id_seq'::regclass);
 :   ALTER TABLE public.tw_posts ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    280    279    280            |           2604    35321    tw_profiles id    DEFAULT     p   ALTER TABLE ONLY public.tw_profiles ALTER COLUMN id SET DEFAULT nextval('public.tw_profiles_id_seq'::regclass);
 =   ALTER TABLE public.tw_profiles ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    277    278    278            M           2604    36043    url_posts id    DEFAULT     l   ALTER TABLE ONLY public.url_posts ALTER COLUMN id SET DEFAULT nextval('public.url_posts_id_seq'::regclass);
 ;   ALTER TABLE public.url_posts ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    345    346    346            G           2604    35159    user_role_tariff_history id    DEFAULT     Љ   ALTER TABLE ONLY public.user_role_tariff_history ALTER COLUMN id SET DEFAULT nextval('public.user_role_tariff_history_id_seq'::regclass);
 J   ALTER TABLE public.user_role_tariff_history ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    262    261    262            8           2604    35076    users id    DEFAULT     d   ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);
 7   ALTER TABLE public.users ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    252    251    252            a           2604    35231    vk_posts id    DEFAULT     j   ALTER TABLE ONLY public.vk_posts ALTER COLUMN id SET DEFAULT nextval('public.vk_posts_id_seq'::regclass);
 :   ALTER TABLE public.vk_posts ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    270    269    270            K           2604    35187    vk_profiles id    DEFAULT     p   ALTER TABLE ONLY public.vk_profiles ALTER COLUMN id SET DEFAULT nextval('public.vk_profiles_id_seq'::regclass);
 =   ALTER TABLE public.vk_profiles ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    265    266    266            ~           2604    34709    wp_collect_profile id    DEFAULT     ~   ALTER TABLE ONLY public.wp_collect_profile ALTER COLUMN id SET DEFAULT nextval('public.wp_collect_profile_id_seq'::regclass);
 D   ALTER TABLE public.wp_collect_profile ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    218    217    218            „           2604    34723    wp_collect_sites id    DEFAULT     z   ALTER TABLE ONLY public.wp_collect_sites ALTER COLUMN id SET DEFAULT nextval('public.wp_collect_sites_id_seq'::regclass);
 B   ALTER TABLE public.wp_collect_sites ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    220    219    220            ‡           2604    34741    wp_posts id    DEFAULT     j   ALTER TABLE ONLY public.wp_posts ALTER COLUMN id SET DEFAULT nextval('public.wp_posts_id_seq'::regclass);
 :   ALTER TABLE public.wp_posts ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    221    222    222            q           2604    34686    wp_publish_profile id    DEFAULT     ~   ALTER TABLE ONLY public.wp_publish_profile ALTER COLUMN id SET DEFAULT nextval('public.wp_publish_profile_id_seq'::regclass);
 D   ALTER TABLE public.wp_publish_profile ALTER COLUMN id DROP DEFAULT;
       public          postgres    false    216    215    216            §          0    35302    admin_audit_log 
   TABLE DATA           v   COPY public.admin_audit_log (id, admin_user_id, action, target_type, target_id, details_json, created_at) FROM stdin;
    public          postgres    false    276   [№      Х          0    35808    ai_tasks 
   TABLE DATA           m   COPY public.ai_tasks (id, user_id, task_type, status, payload, result, created_at, processed_at) FROM stdin;
    public          postgres    false    322   Ъ№      Ґ          0    35286    billing_events 
   TABLE DATA           o   COPY public.billing_events (id, provider, event_id, event_type, payload_json, user_id, created_at) FROM stdin;
    public          postgres    false    274   ч№      “          0    35110    blacklisted_tokens 
   TABLE DATA           O   COPY public.blacklisted_tokens (id, token, expires_at, created_at) FROM stdin;
    public          postgres    false    256   є      Н          0    35722    cpost_posts 
   TABLE DATA           C  COPY public.cpost_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, created_at, updated_at) FROM stdin;
    public          postgres    false    314   1є      Л          0    35708    cpost_profiles 
   TABLE DATA           `   COPY public.cpost_profiles (id, user_id, default_platforms, created_at, updated_at) FROM stdin;
    public          postgres    false    312   Nє      С          0    35781    curl_one_time_done 
   TABLE DATA           R   COPY public.curl_one_time_done (id, user_id, url, xpath, executed_at) FROM stdin;
    public          postgres    false    318   kє      П          0    35752 
   curl_settings 
   TABLE DATA           x  COPY public.curl_settings (id, user_id, collect_enabled, schedule_type, time_intervals, url, xpath, take_screenshot, to_tg, to_tw, to_vk, to_wp, urls, process_before_publish, process_description, remove_emojis, remove_images, clean_html, process_services, status_review_after_process, add_static_html, static_html_content, screenshot_only, created_at, updated_at) FROM stdin;
    public          postgres    false    316   €є      ѓ          0    34919 
   dzen_posts 
   TABLE DATA           J  COPY public.dzen_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, videos, created_at, updated_at) FROM stdin;
    public          postgres    false    240   Ґє      Ѓ          0    34900 
   dzen_profiles 
   TABLE DATA             COPY public.dzen_profiles (id, user_id, publish_enabled, collect_enabled, schedule_type, time_intervals, rss_feed_url, channel_name, channels_to_read, rss_token, yandex_login, yandex_password, dzen_studio_url, collect_source, last_auth_error, created_at, updated_at) FROM stdin;
    public          postgres    false    238   Вє      —          0    35139    email_verification_tokens 
   TABLE DATA           _   COPY public.email_verification_tokens (id, user_id, token, expires_at, created_at) FROM stdin;
    public          postgres    false    260   Яє      Щ          0    35834    feedback 
   TABLE DATA           N   COPY public.feedback (id, type, text, email, user_id, created_at) FROM stdin;
    public          postgres    false    326   ·»      »          0    35508    game_answers 
   TABLE DATA           p   COPY public.game_answers (id, session_id, question_id, selected_option_id, is_correct, answered_at) FROM stdin;
    public          postgres    false    296   Ф»      ­          0    35382 	   game_bots 
   TABLE DATA           U   COPY public.game_bots (id, name, token, username, is_active, created_at) FROM stdin;
    public          postgres    false    282   с»      Ѕ          0    35536    game_media_assets 
   TABLE DATA           Ћ   COPY public.game_media_assets (id, filename, s3_key, original_filename, title, description, content_type, size_bytes, created_at) FROM stdin;
    public          postgres    false    298   ј      Г          0    35601    game_menu_cart_items 
   TABLE DATA           N   COPY public.game_menu_cart_items (id, cart_id, node_id, quantity) FROM stdin;
    public          postgres    false    304   +ј      Б          0    35581    game_menu_carts 
   TABLE DATA           \   COPY public.game_menu_carts (id, bot_id, telegram_user_id, mode_id, updated_at) FROM stdin;
    public          postgres    false    302   Hј      ї          0    35557    game_menu_nodes 
   TABLE DATA           —   COPY public.game_menu_nodes (id, mode_id, parent_id, title, body_text, image_url, image_file_id, sort_order, is_active, created_at, price) FROM stdin;
    public          postgres    false    300   eј      З          0    35647    game_menu_order_items 
   TABLE DATA           c   COPY public.game_menu_order_items (id, order_id, node_id, title, quantity, unit_price) FROM stdin;
    public          postgres    false    308   ‚ј      Е          0    35622    game_menu_orders 
   TABLE DATA           —   COPY public.game_menu_orders (id, order_number, bot_id, mode_id, telegram_user_id, username, first_name, status, created_at, total_amount) FROM stdin;
    public          postgres    false    306   џј      ±          0    35411 
   game_modes 
   TABLE DATA           s   COPY public.game_modes (id, code, title, is_active, questions_per_game, bot_id, created_at, mode_type) FROM stdin;
    public          postgres    false    286   јј      Ї          0    35395    game_players 
   TABLE DATA           p   COPY public.game_players (id, telegram_user_id, bot_id, username, first_name, is_admin, created_at) FROM stdin;
    public          postgres    false    284   Ѕ      µ          0    35445    game_question_options 
   TABLE DATA           g   COPY public.game_question_options (id, question_id, option_index, option_text, is_correct) FROM stdin;
    public          postgres    false    290   :Ѕ      і          0    35429    game_questions 
   TABLE DATA           s   COPY public.game_questions (id, mode_id, prompt_text, image_file_id, image_url, is_active, created_at) FROM stdin;
    public          postgres    false    288   WЅ      №          0    35488    game_session_questions 
   TABLE DATA           Y   COPY public.game_session_questions (id, session_id, step_index, question_id) FROM stdin;
    public          postgres    false    294   tЅ      ·          0    35463 
   game_sessions 
   TABLE DATA           Ј   COPY public.game_sessions (id, player_id, mode_id, status, score, correct_count, total_questions, current_step, started_at, finished_at, duration_sec) FROM stdin;
    public          postgres    false    292   ‘Ѕ      џ          0    35219 
   group_members 
   TABLE DATA           X   COPY public.group_members (id, group_id, user_id, role_in_group, joined_at) FROM stdin;
    public          postgres    false    268   ®Ѕ      ›          0    35174    groups 
   TABLE DATA           W   COPY public.groups (id, name, description, created_at, created_by_user_id) FROM stdin;
    public          postgres    false    264   ЛЅ      Ь          0    35854    guide_blocks 
   TABLE DATA           }   COPY public.guide_blocks (id, slug, toc_label, title, subtitle, body, sort_order, is_visible, style, updated_at) FROM stdin;
    public          postgres    false    329   иЅ      ‡          0    34974    instagram_posts 
   TABLE DATA           d  COPY public.instagram_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, instagram_source_id, videos, created_at, updated_at) FROM stdin;
    public          postgres    false    244   ѕ      …          0    34946    instagram_profiles 
   TABLE DATA           ­  COPY public.instagram_profiles (id, user_id, publish_enabled, collect_enabled, schedule_type, time_intervals, username, password, usernames_to_read, process_enabled, processing_description, remove_emojis, remove_images, clean_html, process_services, status_review_after_process, add_static_html, static_html_content, instagrapi_session, instagram_verification_code, instagram_last_auth_error, created_at, updated_at) FROM stdin;
    public          postgres    false    242   "ѕ      Ч          0    35821 
   notifications 
   TABLE DATA           O   COPY public.notifications (id, message, user_id, type, created_at) FROM stdin;
    public          postgres    false    324   ?ѕ      •          0    35122    password_reset_tokens 
   TABLE DATA           [   COPY public.password_reset_tokens (id, user_id, token, expires_at, created_at) FROM stdin;
    public          postgres    false    258   Mї      Ј          0    35269    plan_definitions 
   TABLE DATA           h   COPY public.plan_definitions (id, code, display_name, description, limits_json, sort_order) FROM stdin;
    public          postgres    false    272   jї      Й          0    35670    posts 
   TABLE DATA           q  COPY public.posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, source_platform, source_id, platform_texts, videos, created_at, updated_at) FROM stdin;
    public          postgres    false    310   ‡ї      ‘          0    35093    refresh_tokens 
   TABLE DATA           T   COPY public.refresh_tokens (id, user_id, token, expires_at, created_at) FROM stdin;
    public          postgres    false    254   ¤ї      У          0    35794    service_cycle_log 
   TABLE DATA           v   COPY public.service_cycle_log (id, service_name, cycle_type, status, detail, items_processed, created_at) FROM stdin;
    public          postgres    false    320   %Б      л          0    36033    smm_ai_usage 
   TABLE DATA           =   COPY public.smm_ai_usage (user_id, month, calls) FROM stdin;
    public          postgres    false    344   Q      ж          0    35971    smm_automations 
   TABLE DATA           o   COPY public.smm_automations (id, user_id, brand_id, type, config, enabled, created_at, updated_at) FROM stdin;
    public          postgres    false    339   n      а          0    35889    smm_brand_channels 
   TABLE DATA           Ќ  COPY public.smm_brand_channels (id, brand_id, network, external_id, title, kind, role, color_override, publish_enabled, collect_enabled, discussion_external_id, discussion_title, comments_collect_enabled, alert_enabled, save_conditions, processing, alert_delivery, alert_rules, conditions_mode, publish_targets, created_at, auth_status, auth_checked_at, auth_error, auth_capabilities) FROM stdin;
    public          postgres    false    333   ‹      Ю          0    35874 
   smm_brands 
   TABLE DATA           `   COPY public.smm_brands (id, user_id, group_id, name, color, created_at, updated_at) FROM stdin;
    public          postgres    false    331   d      к          0    36016    smm_channel_counters 
   TABLE DATA           q   COPY public.smm_channel_counters (id, user_id, channel_id, day, sent, received, failed, alerts_sent) FROM stdin;
    public          postgres    false    343   Ы      у          0    36109    smm_channel_metric_snapshots 
   TABLE DATA           `   COPY public.smm_channel_metric_snapshots (id, channel_id, subscribers, captured_at) FROM stdin;
    public          postgres    false    352   ш      и          0    35990    smm_competitor_snapshots 
   TABLE DATA           ™   COPY public.smm_competitor_snapshots (id, channel_id, external_post_id, post_text, views, likes, comments, reposts, posted_at, collected_at) FROM stdin;
    public          postgres    false    341         в          0    35923    smm_inbox_items 
   TABLE DATA           ¬   COPY public.smm_inbox_items (id, user_id, brand_id, network, channel_id, thread_id, type, author, text, status, external_msg_id, edited_text, meta, created_at) FROM stdin;
    public          postgres    false    335   2      п          0    36075    smm_message_events 
   TABLE DATA           Љ   COPY public.smm_message_events (id, user_id, channel_id, direction, platform, post_id, external_msg_id, metadata, created_at) FROM stdin;
    public          postgres    false    348   O      с          0    36095    smm_post_metric_snapshots 
   TABLE DATA           Ѓ   COPY public.smm_post_metric_snapshots (id, user_id, platform, post_id, views, likes, comments, reposts, captured_at) FROM stdin;
    public          postgres    false    350   l      д          0    35949    smm_publish_jobs 
   TABLE DATA           ґ   COPY public.smm_publish_jobs (id, user_id, brand_id, source_text, media, targets, adapters_result, publish_at, status, retry_count, last_error, created_at, updated_at) FROM stdin;
    public          postgres    false    337   ‰      Ъ          0    35845    system_settings 
   TABLE DATA           A   COPY public.system_settings (key, value, updated_at) FROM stdin;
    public          postgres    false    327   ¦      {          0    34865    tg_dedup_cache 
   TABLE DATA           {   COPY public.tg_dedup_cache (id, user_id, text_hash, chat_id, rule_id, channel_to_post, expires_at, created_at) FROM stdin;
    public          postgres    false    232   с                0    34888 
   tg_digests 
   TABLE DATA           b   COPY public.tg_digests (id, user_id, chat_id, digest_text, message_count, created_at) FROM stdin;
    public          postgres    false    236         y          0    34849 	   tg_events 
   TABLE DATA           ќ   COPY public.tg_events (id, user_id, chat_id, message_id, event_type, rule_id, matched_conditions, text_hash, text_preview, metadata, created_at) FROM stdin;
    public          postgres    false    230   +      w          0    34835    tg_post_templates 
   TABLE DATA           f   COPY public.tg_post_templates (id, user_id, name, text, hashtags, created_at, updated_at) FROM stdin;
    public          postgres    false    228   H      u          0    34802    tg_posts 
   TABLE DATA           }  COPY public.tg_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, metadata, publish_at, telegram_message_id, telegram_chat_id, created_at, updated_at) FROM stdin;
    public          postgres    false    226   e      s          0    34768    tg_profiles 
   TABLE DATA           m  COPY public.tg_profiles (id, user_id, publish_enabled, collect_enabled, schedule_type, time_intervals, api_id, api_hash, chats_to_read, save_conditions, channel_to_post, channels_to_post, alert_enabled, alert_rules, process_enabled, processing_description, remove_emojis, remove_images, clean_html, process_services, status_review_after_process, add_static_html, static_html_content, telegram_username, auth_state, auth_phone_code_hash, auth_phone_number, summarize_enabled, summarize_min_length, digest_interval_min, digest_channel, classification_enabled, classification_categories, created_at, updated_at) FROM stdin;
    public          postgres    false    224   ‚      }          0    34875    tg_summary_cache 
   TABLE DATA           Z   COPY public.tg_summary_cache (id, text_hash, summary, expires_at, created_at) FROM stdin;
    public          postgres    false    234   ~      ‹          0    35030 
   threads_posts 
   TABLE DATA           E  COPY public.threads_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, created_at, updated_at) FROM stdin;
    public          postgres    false    248   ›      ‰          0    35007    threads_profiles 
   TABLE DATA           Љ  COPY public.threads_profiles (id, user_id, publish_enabled, collect_enabled, schedule_type, time_intervals, access_token, refresh_token, token_expires_at, threads_user_id, instagram_handle, process_enabled, processing_description, remove_emojis, remove_images, clean_html, process_services, status_review_after_process, add_static_html, static_html_content, created_at, updated_at) FROM stdin;
    public          postgres    false    246   ё      Ќ          0    35060    threads_selenium_sessions 
   TABLE DATA           p   COPY public.threads_selenium_sessions (id, user_id, status, detail_message, created_at, updated_at) FROM stdin;
    public          postgres    false    250   Х      «          0    35345    tw_posts 
   TABLE DATA           @  COPY public.tw_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, created_at, updated_at) FROM stdin;
    public          postgres    false    280   т      ©          0    35318    tw_profiles 
   TABLE DATA           Ґ  COPY public.tw_profiles (id, user_id, publish_enabled, collect_enabled, schedule_type, time_intervals, use_proxy, proxy_user, proxy_pass, proxy_host, proxy_port, twitter_username, twitter_password, twitter_oauth_access_token, twitter_oauth_refresh_token, twitter_oauth_expires_at, twitter_rest_id, oauth_pkce_verifier, oauth_pkce_expires_at, take_screenshot_collect, screenshot_xpath, created_at, updated_at) FROM stdin;
    public          postgres    false    278          н          0    36040 	   url_posts 
   TABLE DATA           A  COPY public.url_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, created_at, updated_at) FROM stdin;
    public          postgres    false    346   ,       ™          0    35156    user_role_tariff_history 
   TABLE DATA           ‹   COPY public.user_role_tariff_history (id, user_id, changed_at, changed_by_user_id, role_old, role_new, tariff_old, tariff_new) FROM stdin;
    public          postgres    false    262   I       Џ          0    35073    users 
   TABLE DATA           ю   COPY public.users (id, username, email, password_hash, role, tariff, is_email_verified, is_blocked, billing_provider, billing_customer_id, billing_subscription_id, subscription_status, subscription_current_period_end, created_at, updated_at) FROM stdin;
    public          postgres    false    252          Ў          0    35228    vk_posts 
   TABLE DATA           ‘  COPY public.vk_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, vk_source_id, attachments, publish_at, created_at, updated_at, published_vk_post_id, published_owner_id) FROM stdin;
    public          postgres    false    270   K!      ќ          0    35182    vk_profiles 
   TABLE DATA           1  COPY public.vk_profiles (id, user_id, publish_enabled, collect_enabled, schedule_type, time_intervals, owner_id, friends_only, from_group, message, attachments, signed, mark_as_ads, access_token, user_access_token, groups_to_read, users_to_read, group_to_post, process_enabled, processing_description, remove_emojis, remove_images, clean_html, process_services, status_review_after_process, add_static_html, static_html_content, post_to_own_wall, vk_user_id, vk_app_id, vk_app_secret, vk_frontend_url, vk_public_gateway_url, created_at, updated_at) FROM stdin;
    public          postgres    false    266   h!      m          0    34706    wp_collect_profile 
   TABLE DATA           €   COPY public.wp_collect_profile (id, user_id, collect_enabled, collect_all_available, collect_limit, created_at, updated_at) FROM stdin;
    public          postgres    false    218   …!      o          0    34720    wp_collect_sites 
   TABLE DATA           x   COPY public.wp_collect_sites (id, profile_id, user_id, site_url, schedule_type, time_intervals, created_at) FROM stdin;
    public          postgres    false    220   ў!      q          0    34738    wp_posts 
   TABLE DATA           @  COPY public.wp_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, created_at, updated_at) FROM stdin;
    public          postgres    false    222   ї!      k          0    34683    wp_publish_profile 
   TABLE DATA           ‹  COPY public.wp_publish_profile (id, user_id, publish_enabled, schedule_type, time_intervals, site_url, username, app_password, publish_all_ready, publish_limit, publish_interval_minutes, process_before_publish, process_description, remove_emojis, remove_images, clean_html, process_services, status_review_after_process, add_static_html, static_html_content, created_at, updated_at) FROM stdin;
    public          postgres    false    216   Ь!      >           0    0    admin_audit_log_id_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('public.admin_audit_log_id_seq', 1, true);
          public          postgres    false    275            ?           0    0    ai_tasks_id_seq    SEQUENCE SET     >   SELECT pg_catalog.setval('public.ai_tasks_id_seq', 1, false);
          public          postgres    false    321            @           0    0    billing_events_id_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('public.billing_events_id_seq', 1, false);
          public          postgres    false    273            A           0    0    blacklisted_tokens_id_seq    SEQUENCE SET     H   SELECT pg_catalog.setval('public.blacklisted_tokens_id_seq', 1, false);
          public          postgres    false    255            B           0    0    cpost_posts_id_seq    SEQUENCE SET     A   SELECT pg_catalog.setval('public.cpost_posts_id_seq', 1, false);
          public          postgres    false    313            C           0    0    cpost_profiles_id_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('public.cpost_profiles_id_seq', 1, false);
          public          postgres    false    311            D           0    0    curl_one_time_done_id_seq    SEQUENCE SET     H   SELECT pg_catalog.setval('public.curl_one_time_done_id_seq', 1, false);
          public          postgres    false    317            E           0    0    curl_settings_id_seq    SEQUENCE SET     C   SELECT pg_catalog.setval('public.curl_settings_id_seq', 1, false);
          public          postgres    false    315            F           0    0    dzen_posts_id_seq    SEQUENCE SET     @   SELECT pg_catalog.setval('public.dzen_posts_id_seq', 1, false);
          public          postgres    false    239            G           0    0    dzen_profiles_id_seq    SEQUENCE SET     C   SELECT pg_catalog.setval('public.dzen_profiles_id_seq', 1, false);
          public          postgres    false    237            H           0    0     email_verification_tokens_id_seq    SEQUENCE SET     N   SELECT pg_catalog.setval('public.email_verification_tokens_id_seq', 1, true);
          public          postgres    false    259            I           0    0    feedback_id_seq    SEQUENCE SET     >   SELECT pg_catalog.setval('public.feedback_id_seq', 1, false);
          public          postgres    false    325            J           0    0    game_answers_id_seq    SEQUENCE SET     B   SELECT pg_catalog.setval('public.game_answers_id_seq', 1, false);
          public          postgres    false    295            K           0    0    game_bots_id_seq    SEQUENCE SET     ?   SELECT pg_catalog.setval('public.game_bots_id_seq', 1, false);
          public          postgres    false    281            L           0    0    game_media_assets_id_seq    SEQUENCE SET     G   SELECT pg_catalog.setval('public.game_media_assets_id_seq', 1, false);
          public          postgres    false    297            M           0    0    game_menu_cart_items_id_seq    SEQUENCE SET     J   SELECT pg_catalog.setval('public.game_menu_cart_items_id_seq', 1, false);
          public          postgres    false    303            N           0    0    game_menu_carts_id_seq    SEQUENCE SET     E   SELECT pg_catalog.setval('public.game_menu_carts_id_seq', 1, false);
          public          postgres    false    301            O           0    0    game_menu_nodes_id_seq    SEQUENCE SET     E   SELECT pg_catalog.setval('public.game_menu_nodes_id_seq', 1, false);
          public          postgres    false    299            P           0    0    game_menu_order_items_id_seq    SEQUENCE SET     K   SELECT pg_catalog.setval('public.game_menu_order_items_id_seq', 1, false);
          public          postgres    false    307            Q           0    0    game_menu_orders_id_seq    SEQUENCE SET     F   SELECT pg_catalog.setval('public.game_menu_orders_id_seq', 1, false);
          public          postgres    false    305            R           0    0    game_modes_id_seq    SEQUENCE SET     ?   SELECT pg_catalog.setval('public.game_modes_id_seq', 1, true);
          public          postgres    false    285            S           0    0    game_players_id_seq    SEQUENCE SET     B   SELECT pg_catalog.setval('public.game_players_id_seq', 1, false);
          public          postgres    false    283            T           0    0    game_question_options_id_seq    SEQUENCE SET     K   SELECT pg_catalog.setval('public.game_question_options_id_seq', 1, false);
          public          postgres    false    289            U           0    0    game_questions_id_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('public.game_questions_id_seq', 1, false);
          public          postgres    false    287            V           0    0    game_session_questions_id_seq    SEQUENCE SET     L   SELECT pg_catalog.setval('public.game_session_questions_id_seq', 1, false);
          public          postgres    false    293            W           0    0    game_sessions_id_seq    SEQUENCE SET     C   SELECT pg_catalog.setval('public.game_sessions_id_seq', 1, false);
          public          postgres    false    291            X           0    0    group_members_id_seq    SEQUENCE SET     C   SELECT pg_catalog.setval('public.group_members_id_seq', 1, false);
          public          postgres    false    267            Y           0    0 
   groups_id_seq    SEQUENCE SET     <   SELECT pg_catalog.setval('public.groups_id_seq', 1, false);
          public          postgres    false    263            Z           0    0    guide_blocks_id_seq    SEQUENCE SET     B   SELECT pg_catalog.setval('public.guide_blocks_id_seq', 1, false);
          public          postgres    false    328            [           0    0    instagram_posts_id_seq    SEQUENCE SET     E   SELECT pg_catalog.setval('public.instagram_posts_id_seq', 1, false);
          public          postgres    false    243            \           0    0    instagram_profiles_id_seq    SEQUENCE SET     H   SELECT pg_catalog.setval('public.instagram_profiles_id_seq', 1, false);
          public          postgres    false    241            ]           0    0    notifications_id_seq    SEQUENCE SET     B   SELECT pg_catalog.setval('public.notifications_id_seq', 1, true);
          public          postgres    false    323            ^           0    0    password_reset_tokens_id_seq    SEQUENCE SET     K   SELECT pg_catalog.setval('public.password_reset_tokens_id_seq', 1, false);
          public          postgres    false    257            _           0    0    plan_definitions_id_seq    SEQUENCE SET     F   SELECT pg_catalog.setval('public.plan_definitions_id_seq', 1, false);
          public          postgres    false    271            `           0    0    posts_id_seq    SEQUENCE SET     ;   SELECT pg_catalog.setval('public.posts_id_seq', 1, false);
          public          postgres    false    309            a           0    0    refresh_tokens_id_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('public.refresh_tokens_id_seq', 20, true);
          public          postgres    false    253            b           0    0    service_cycle_log_id_seq    SEQUENCE SET     I   SELECT pg_catalog.setval('public.service_cycle_log_id_seq', 2176, true);
          public          postgres    false    319            c           0    0    smm_automations_id_seq    SEQUENCE SET     E   SELECT pg_catalog.setval('public.smm_automations_id_seq', 1, false);
          public          postgres    false    338            d           0    0    smm_brand_channels_id_seq    SEQUENCE SET     H   SELECT pg_catalog.setval('public.smm_brand_channels_id_seq', 15, true);
          public          postgres    false    332            e           0    0    smm_brands_id_seq    SEQUENCE SET     ?   SELECT pg_catalog.setval('public.smm_brands_id_seq', 2, true);
          public          postgres    false    330            f           0    0    smm_channel_counters_id_seq    SEQUENCE SET     J   SELECT pg_catalog.setval('public.smm_channel_counters_id_seq', 1, false);
          public          postgres    false    342            g           0    0 #   smm_channel_metric_snapshots_id_seq    SEQUENCE SET     R   SELECT pg_catalog.setval('public.smm_channel_metric_snapshots_id_seq', 1, false);
          public          postgres    false    351            h           0    0    smm_competitor_snapshots_id_seq    SEQUENCE SET     N   SELECT pg_catalog.setval('public.smm_competitor_snapshots_id_seq', 1, false);
          public          postgres    false    340            i           0    0    smm_inbox_items_id_seq    SEQUENCE SET     E   SELECT pg_catalog.setval('public.smm_inbox_items_id_seq', 1, false);
          public          postgres    false    334            j           0    0    smm_message_events_id_seq    SEQUENCE SET     H   SELECT pg_catalog.setval('public.smm_message_events_id_seq', 1, false);
          public          postgres    false    347            k           0    0     smm_post_metric_snapshots_id_seq    SEQUENCE SET     O   SELECT pg_catalog.setval('public.smm_post_metric_snapshots_id_seq', 1, false);
          public          postgres    false    349            l           0    0    smm_publish_jobs_id_seq    SEQUENCE SET     F   SELECT pg_catalog.setval('public.smm_publish_jobs_id_seq', 1, false);
          public          postgres    false    336            m           0    0    tg_dedup_cache_id_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('public.tg_dedup_cache_id_seq', 1, false);
          public          postgres    false    231            n           0    0    tg_digests_id_seq    SEQUENCE SET     @   SELECT pg_catalog.setval('public.tg_digests_id_seq', 1, false);
          public          postgres    false    235            o           0    0    tg_events_id_seq    SEQUENCE SET     ?   SELECT pg_catalog.setval('public.tg_events_id_seq', 1, false);
          public          postgres    false    229            p           0    0    tg_post_templates_id_seq    SEQUENCE SET     G   SELECT pg_catalog.setval('public.tg_post_templates_id_seq', 1, false);
          public          postgres    false    227            q           0    0    tg_posts_id_seq    SEQUENCE SET     >   SELECT pg_catalog.setval('public.tg_posts_id_seq', 1, false);
          public          postgres    false    225            r           0    0    tg_profiles_id_seq    SEQUENCE SET     @   SELECT pg_catalog.setval('public.tg_profiles_id_seq', 1, true);
          public          postgres    false    223            s           0    0    tg_summary_cache_id_seq    SEQUENCE SET     F   SELECT pg_catalog.setval('public.tg_summary_cache_id_seq', 1, false);
          public          postgres    false    233            t           0    0    threads_posts_id_seq    SEQUENCE SET     C   SELECT pg_catalog.setval('public.threads_posts_id_seq', 1, false);
          public          postgres    false    247            u           0    0    threads_profiles_id_seq    SEQUENCE SET     F   SELECT pg_catalog.setval('public.threads_profiles_id_seq', 1, false);
          public          postgres    false    245            v           0    0     threads_selenium_sessions_id_seq    SEQUENCE SET     O   SELECT pg_catalog.setval('public.threads_selenium_sessions_id_seq', 1, false);
          public          postgres    false    249            w           0    0    tw_posts_id_seq    SEQUENCE SET     >   SELECT pg_catalog.setval('public.tw_posts_id_seq', 1, false);
          public          postgres    false    279            x           0    0    tw_profiles_id_seq    SEQUENCE SET     A   SELECT pg_catalog.setval('public.tw_profiles_id_seq', 1, false);
          public          postgres    false    277            y           0    0    url_posts_id_seq    SEQUENCE SET     ?   SELECT pg_catalog.setval('public.url_posts_id_seq', 1, false);
          public          postgres    false    345            z           0    0    user_role_tariff_history_id_seq    SEQUENCE SET     M   SELECT pg_catalog.setval('public.user_role_tariff_history_id_seq', 1, true);
          public          postgres    false    261            {           0    0    users_id_seq    SEQUENCE SET     :   SELECT pg_catalog.setval('public.users_id_seq', 1, true);
          public          postgres    false    251            |           0    0    vk_posts_id_seq    SEQUENCE SET     >   SELECT pg_catalog.setval('public.vk_posts_id_seq', 1, false);
          public          postgres    false    269            }           0    0    vk_profiles_id_seq    SEQUENCE SET     A   SELECT pg_catalog.setval('public.vk_profiles_id_seq', 1, false);
          public          postgres    false    265            ~           0    0    wp_collect_profile_id_seq    SEQUENCE SET     H   SELECT pg_catalog.setval('public.wp_collect_profile_id_seq', 1, false);
          public          postgres    false    217                       0    0    wp_collect_sites_id_seq    SEQUENCE SET     F   SELECT pg_catalog.setval('public.wp_collect_sites_id_seq', 1, false);
          public          postgres    false    219            Ђ           0    0    wp_posts_id_seq    SEQUENCE SET     >   SELECT pg_catalog.setval('public.wp_posts_id_seq', 1, false);
          public          postgres    false    221            Ѓ           0    0    wp_publish_profile_id_seq    SEQUENCE SET     H   SELECT pg_catalog.setval('public.wp_publish_profile_id_seq', 1, false);
          public          postgres    false    215                       2606    35310 $   admin_audit_log admin_audit_log_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.admin_audit_log
    ADD CONSTRAINT admin_audit_log_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.admin_audit_log DROP CONSTRAINT admin_audit_log_pkey;
       public            postgres    false    276            r           2606    35818    ai_tasks ai_tasks_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.ai_tasks
    ADD CONSTRAINT ai_tasks_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.ai_tasks DROP CONSTRAINT ai_tasks_pkey;
       public            postgres    false    322                       2606    35295 "   billing_events billing_events_pkey 
   CONSTRAINT     `   ALTER TABLE ONLY public.billing_events
    ADD CONSTRAINT billing_events_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.billing_events DROP CONSTRAINT billing_events_pkey;
       public            postgres    false    274            ж           2606    35118 *   blacklisted_tokens blacklisted_tokens_pkey 
   CONSTRAINT     h   ALTER TABLE ONLY public.blacklisted_tokens
    ADD CONSTRAINT blacklisted_tokens_pkey PRIMARY KEY (id);
 T   ALTER TABLE ONLY public.blacklisted_tokens DROP CONSTRAINT blacklisted_tokens_pkey;
       public            postgres    false    256            и           2606    35120 /   blacklisted_tokens blacklisted_tokens_token_key 
   CONSTRAINT     k   ALTER TABLE ONLY public.blacklisted_tokens
    ADD CONSTRAINT blacklisted_tokens_token_key UNIQUE (token);
 Y   ALTER TABLE ONLY public.blacklisted_tokens DROP CONSTRAINT blacklisted_tokens_token_key;
       public            postgres    false    256            a           2606    35748    cpost_posts cpost_posts_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.cpost_posts
    ADD CONSTRAINT cpost_posts_pkey PRIMARY KEY (id);
 F   ALTER TABLE ONLY public.cpost_posts DROP CONSTRAINT cpost_posts_pkey;
       public            postgres    false    314            ]           2606    35718 "   cpost_profiles cpost_profiles_pkey 
   CONSTRAINT     `   ALTER TABLE ONLY public.cpost_profiles
    ADD CONSTRAINT cpost_profiles_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.cpost_profiles DROP CONSTRAINT cpost_profiles_pkey;
       public            postgres    false    312            _           2606    35720 )   cpost_profiles cpost_profiles_user_id_key 
   CONSTRAINT     g   ALTER TABLE ONLY public.cpost_profiles
    ADD CONSTRAINT cpost_profiles_user_id_key UNIQUE (user_id);
 S   ALTER TABLE ONLY public.cpost_profiles DROP CONSTRAINT cpost_profiles_user_id_key;
       public            postgres    false    312            i           2606    35789 *   curl_one_time_done curl_one_time_done_pkey 
   CONSTRAINT     h   ALTER TABLE ONLY public.curl_one_time_done
    ADD CONSTRAINT curl_one_time_done_pkey PRIMARY KEY (id);
 T   ALTER TABLE ONLY public.curl_one_time_done DROP CONSTRAINT curl_one_time_done_pkey;
       public            postgres    false    318            k           2606    35791 ;   curl_one_time_done curl_one_time_done_user_id_url_xpath_key 
   CONSTRAINT     …   ALTER TABLE ONLY public.curl_one_time_done
    ADD CONSTRAINT curl_one_time_done_user_id_url_xpath_key UNIQUE (user_id, url, xpath);
 e   ALTER TABLE ONLY public.curl_one_time_done DROP CONSTRAINT curl_one_time_done_user_id_url_xpath_key;
       public            postgres    false    318    318    318            e           2606    35777     curl_settings curl_settings_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.curl_settings
    ADD CONSTRAINT curl_settings_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.curl_settings DROP CONSTRAINT curl_settings_pkey;
       public            postgres    false    316            g           2606    35779 '   curl_settings curl_settings_user_id_key 
   CONSTRAINT     e   ALTER TABLE ONLY public.curl_settings
    ADD CONSTRAINT curl_settings_user_id_key UNIQUE (user_id);
 Q   ALTER TABLE ONLY public.curl_settings DROP CONSTRAINT curl_settings_user_id_key;
       public            postgres    false    316            ї           2606    34950    dzen_posts dzen_posts_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.dzen_posts
    ADD CONSTRAINT dzen_posts_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.dzen_posts DROP CONSTRAINT dzen_posts_pkey;
       public            postgres    false    240            »           2606    34915     dzen_profiles dzen_profiles_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.dzen_profiles
    ADD CONSTRAINT dzen_profiles_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.dzen_profiles DROP CONSTRAINT dzen_profiles_pkey;
       public            postgres    false    238            Ѕ           2606    34917 '   dzen_profiles dzen_profiles_user_id_key 
   CONSTRAINT     e   ALTER TABLE ONLY public.dzen_profiles
    ADD CONSTRAINT dzen_profiles_user_id_key UNIQUE (user_id);
 Q   ALTER TABLE ONLY public.dzen_profiles DROP CONSTRAINT dzen_profiles_user_id_key;
       public            postgres    false    238            с           2606    35147 8   email_verification_tokens email_verification_tokens_pkey 
   CONSTRAINT     v   ALTER TABLE ONLY public.email_verification_tokens
    ADD CONSTRAINT email_verification_tokens_pkey PRIMARY KEY (id);
 b   ALTER TABLE ONLY public.email_verification_tokens DROP CONSTRAINT email_verification_tokens_pkey;
       public            postgres    false    260            у           2606    35149 =   email_verification_tokens email_verification_tokens_token_key 
   CONSTRAINT     y   ALTER TABLE ONLY public.email_verification_tokens
    ADD CONSTRAINT email_verification_tokens_token_key UNIQUE (token);
 g   ALTER TABLE ONLY public.email_verification_tokens DROP CONSTRAINT email_verification_tokens_token_key;
       public            postgres    false    260            y           2606    35843    feedback feedback_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.feedback DROP CONSTRAINT feedback_pkey;
       public            postgres    false    326            ;           2606    35514    game_answers game_answers_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.game_answers
    ADD CONSTRAINT game_answers_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.game_answers DROP CONSTRAINT game_answers_pkey;
       public            postgres    false    296            =           2606    35516 4   game_answers game_answers_session_id_question_id_key 
   CONSTRAINT     ‚   ALTER TABLE ONLY public.game_answers
    ADD CONSTRAINT game_answers_session_id_question_id_key UNIQUE (session_id, question_id);
 ^   ALTER TABLE ONLY public.game_answers DROP CONSTRAINT game_answers_session_id_question_id_key;
       public            postgres    false    296    296            "           2606    35391    game_bots game_bots_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.game_bots
    ADD CONSTRAINT game_bots_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.game_bots DROP CONSTRAINT game_bots_pkey;
       public            postgres    false    282            $           2606    35393    game_bots game_bots_token_key 
   CONSTRAINT     Y   ALTER TABLE ONLY public.game_bots
    ADD CONSTRAINT game_bots_token_key UNIQUE (token);
 G   ALTER TABLE ONLY public.game_bots DROP CONSTRAINT game_bots_token_key;
       public            postgres    false    282            ?           2606    35548 0   game_media_assets game_media_assets_filename_key 
   CONSTRAINT     o   ALTER TABLE ONLY public.game_media_assets
    ADD CONSTRAINT game_media_assets_filename_key UNIQUE (filename);
 Z   ALTER TABLE ONLY public.game_media_assets DROP CONSTRAINT game_media_assets_filename_key;
       public            postgres    false    298            A           2606    35546 (   game_media_assets game_media_assets_pkey 
   CONSTRAINT     f   ALTER TABLE ONLY public.game_media_assets
    ADD CONSTRAINT game_media_assets_pkey PRIMARY KEY (id);
 R   ALTER TABLE ONLY public.game_media_assets DROP CONSTRAINT game_media_assets_pkey;
       public            postgres    false    298            C           2606    35550 .   game_media_assets game_media_assets_s3_key_key 
   CONSTRAINT     k   ALTER TABLE ONLY public.game_media_assets
    ADD CONSTRAINT game_media_assets_s3_key_key UNIQUE (s3_key);
 X   ALTER TABLE ONLY public.game_media_assets DROP CONSTRAINT game_media_assets_s3_key_key;
       public            postgres    false    298            L           2606    35610 =   game_menu_cart_items game_menu_cart_items_cart_id_node_id_key 
   CONSTRAINT     „   ALTER TABLE ONLY public.game_menu_cart_items
    ADD CONSTRAINT game_menu_cart_items_cart_id_node_id_key UNIQUE (cart_id, node_id);
 g   ALTER TABLE ONLY public.game_menu_cart_items DROP CONSTRAINT game_menu_cart_items_cart_id_node_id_key;
       public            postgres    false    304    304            N           2606    35608 .   game_menu_cart_items game_menu_cart_items_pkey 
   CONSTRAINT     l   ALTER TABLE ONLY public.game_menu_cart_items
    ADD CONSTRAINT game_menu_cart_items_pkey PRIMARY KEY (id);
 X   ALTER TABLE ONLY public.game_menu_cart_items DROP CONSTRAINT game_menu_cart_items_pkey;
       public            postgres    false    304            H           2606    35589 C   game_menu_carts game_menu_carts_bot_id_telegram_user_id_mode_id_key 
   CONSTRAINT     ›   ALTER TABLE ONLY public.game_menu_carts
    ADD CONSTRAINT game_menu_carts_bot_id_telegram_user_id_mode_id_key UNIQUE (bot_id, telegram_user_id, mode_id);
 m   ALTER TABLE ONLY public.game_menu_carts DROP CONSTRAINT game_menu_carts_bot_id_telegram_user_id_mode_id_key;
       public            postgres    false    302    302    302            J           2606    35587 $   game_menu_carts game_menu_carts_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.game_menu_carts
    ADD CONSTRAINT game_menu_carts_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.game_menu_carts DROP CONSTRAINT game_menu_carts_pkey;
       public            postgres    false    302            E           2606    35567 $   game_menu_nodes game_menu_nodes_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.game_menu_nodes
    ADD CONSTRAINT game_menu_nodes_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.game_menu_nodes DROP CONSTRAINT game_menu_nodes_pkey;
       public            postgres    false    300            V           2606    35656 0   game_menu_order_items game_menu_order_items_pkey 
   CONSTRAINT     n   ALTER TABLE ONLY public.game_menu_order_items
    ADD CONSTRAINT game_menu_order_items_pkey PRIMARY KEY (id);
 Z   ALTER TABLE ONLY public.game_menu_order_items DROP CONSTRAINT game_menu_order_items_pkey;
       public            postgres    false    308            P           2606    35634 2   game_menu_orders game_menu_orders_order_number_key 
   CONSTRAINT     u   ALTER TABLE ONLY public.game_menu_orders
    ADD CONSTRAINT game_menu_orders_order_number_key UNIQUE (order_number);
 \   ALTER TABLE ONLY public.game_menu_orders DROP CONSTRAINT game_menu_orders_order_number_key;
       public            postgres    false    306            R           2606    35632 &   game_menu_orders game_menu_orders_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.game_menu_orders
    ADD CONSTRAINT game_menu_orders_pkey PRIMARY KEY (id);
 P   ALTER TABLE ONLY public.game_menu_orders DROP CONSTRAINT game_menu_orders_pkey;
       public            postgres    false    306            )           2606    35422    game_modes game_modes_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.game_modes
    ADD CONSTRAINT game_modes_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.game_modes DROP CONSTRAINT game_modes_pkey;
       public            postgres    false    286            &           2606    35404    game_players game_players_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.game_players
    ADD CONSTRAINT game_players_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.game_players DROP CONSTRAINT game_players_pkey;
       public            postgres    false    284            /           2606    35454 0   game_question_options game_question_options_pkey 
   CONSTRAINT     n   ALTER TABLE ONLY public.game_question_options
    ADD CONSTRAINT game_question_options_pkey PRIMARY KEY (id);
 Z   ALTER TABLE ONLY public.game_question_options DROP CONSTRAINT game_question_options_pkey;
       public            postgres    false    290            1           2606    35456 H   game_question_options game_question_options_question_id_option_index_key 
   CONSTRAINT        ALTER TABLE ONLY public.game_question_options
    ADD CONSTRAINT game_question_options_question_id_option_index_key UNIQUE (question_id, option_index);
 r   ALTER TABLE ONLY public.game_question_options DROP CONSTRAINT game_question_options_question_id_option_index_key;
       public            postgres    false    290    290            ,           2606    35438 "   game_questions game_questions_pkey 
   CONSTRAINT     `   ALTER TABLE ONLY public.game_questions
    ADD CONSTRAINT game_questions_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.game_questions DROP CONSTRAINT game_questions_pkey;
       public            postgres    false    288            7           2606    35494 2   game_session_questions game_session_questions_pkey 
   CONSTRAINT     p   ALTER TABLE ONLY public.game_session_questions
    ADD CONSTRAINT game_session_questions_pkey PRIMARY KEY (id);
 \   ALTER TABLE ONLY public.game_session_questions DROP CONSTRAINT game_session_questions_pkey;
       public            postgres    false    294            9           2606    35496 G   game_session_questions game_session_questions_session_id_step_index_key 
   CONSTRAINT     ”   ALTER TABLE ONLY public.game_session_questions
    ADD CONSTRAINT game_session_questions_session_id_step_index_key UNIQUE (session_id, step_index);
 q   ALTER TABLE ONLY public.game_session_questions DROP CONSTRAINT game_session_questions_session_id_step_index_key;
       public            postgres    false    294    294            3           2606    35476     game_sessions game_sessions_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.game_sessions
    ADD CONSTRAINT game_sessions_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.game_sessions DROP CONSTRAINT game_sessions_pkey;
       public            postgres    false    292                        2606    35238 0   group_members group_members_group_id_user_id_key 
   CONSTRAINT     x   ALTER TABLE ONLY public.group_members
    ADD CONSTRAINT group_members_group_id_user_id_key UNIQUE (group_id, user_id);
 Z   ALTER TABLE ONLY public.group_members DROP CONSTRAINT group_members_group_id_user_id_key;
       public            postgres    false    268    268                       2606    35227     group_members group_members_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.group_members
    ADD CONSTRAINT group_members_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.group_members DROP CONSTRAINT group_members_pkey;
       public            postgres    false    268            ъ           2606    35186    groups groups_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.groups DROP CONSTRAINT groups_pkey;
       public            postgres    false    264            ~           2606    35869    guide_blocks guide_blocks_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.guide_blocks
    ADD CONSTRAINT guide_blocks_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.guide_blocks DROP CONSTRAINT guide_blocks_pkey;
       public            postgres    false    329            Ђ           2606    35871 "   guide_blocks guide_blocks_slug_key 
   CONSTRAINT     ]   ALTER TABLE ONLY public.guide_blocks
    ADD CONSTRAINT guide_blocks_slug_key UNIQUE (slug);
 L   ALTER TABLE ONLY public.guide_blocks DROP CONSTRAINT guide_blocks_slug_key;
       public            postgres    false    329            Л           2606    35001 $   instagram_posts instagram_posts_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.instagram_posts
    ADD CONSTRAINT instagram_posts_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.instagram_posts DROP CONSTRAINT instagram_posts_pkey;
       public            postgres    false    244            Г           2606    34968 *   instagram_profiles instagram_profiles_pkey 
   CONSTRAINT     h   ALTER TABLE ONLY public.instagram_profiles
    ADD CONSTRAINT instagram_profiles_pkey PRIMARY KEY (id);
 T   ALTER TABLE ONLY public.instagram_profiles DROP CONSTRAINT instagram_profiles_pkey;
       public            postgres    false    242            Е           2606    34971 1   instagram_profiles instagram_profiles_user_id_key 
   CONSTRAINT     o   ALTER TABLE ONLY public.instagram_profiles
    ADD CONSTRAINT instagram_profiles_user_id_key UNIQUE (user_id);
 [   ALTER TABLE ONLY public.instagram_profiles DROP CONSTRAINT instagram_profiles_user_id_key;
       public            postgres    false    242            w           2606    35830     notifications notifications_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.notifications DROP CONSTRAINT notifications_pkey;
       public            postgres    false    324            н           2606    35130 0   password_reset_tokens password_reset_tokens_pkey 
   CONSTRAINT     n   ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (id);
 Z   ALTER TABLE ONLY public.password_reset_tokens DROP CONSTRAINT password_reset_tokens_pkey;
       public            postgres    false    258            п           2606    35132 5   password_reset_tokens password_reset_tokens_token_key 
   CONSTRAINT     q   ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_token_key UNIQUE (token);
 _   ALTER TABLE ONLY public.password_reset_tokens DROP CONSTRAINT password_reset_tokens_token_key;
       public            postgres    false    258            
           2606    35282 *   plan_definitions plan_definitions_code_key 
   CONSTRAINT     e   ALTER TABLE ONLY public.plan_definitions
    ADD CONSTRAINT plan_definitions_code_key UNIQUE (code);
 T   ALTER TABLE ONLY public.plan_definitions DROP CONSTRAINT plan_definitions_code_key;
       public            postgres    false    272                       2606    35279 &   plan_definitions plan_definitions_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.plan_definitions
    ADD CONSTRAINT plan_definitions_pkey PRIMARY KEY (id);
 P   ALTER TABLE ONLY public.plan_definitions DROP CONSTRAINT plan_definitions_pkey;
       public            postgres    false    272            [           2606    35698    posts posts_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public.posts
    ADD CONSTRAINT posts_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.posts DROP CONSTRAINT posts_pkey;
       public            postgres    false    310            в           2606    35101 "   refresh_tokens refresh_tokens_pkey 
   CONSTRAINT     `   ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.refresh_tokens DROP CONSTRAINT refresh_tokens_pkey;
       public            postgres    false    254            д           2606    35103 '   refresh_tokens refresh_tokens_token_key 
   CONSTRAINT     c   ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_token_key UNIQUE (token);
 Q   ALTER TABLE ONLY public.refresh_tokens DROP CONSTRAINT refresh_tokens_token_key;
       public            postgres    false    254            p           2606    35804 (   service_cycle_log service_cycle_log_pkey 
   CONSTRAINT     f   ALTER TABLE ONLY public.service_cycle_log
    ADD CONSTRAINT service_cycle_log_pkey PRIMARY KEY (id);
 R   ALTER TABLE ONLY public.service_cycle_log DROP CONSTRAINT service_cycle_log_pkey;
       public            postgres    false    320            Ў           2606    36038    smm_ai_usage smm_ai_usage_pkey 
   CONSTRAINT     h   ALTER TABLE ONLY public.smm_ai_usage
    ADD CONSTRAINT smm_ai_usage_pkey PRIMARY KEY (user_id, month);
 H   ALTER TABLE ONLY public.smm_ai_usage DROP CONSTRAINT smm_ai_usage_pkey;
       public            postgres    false    344    344            —           2606    35983 $   smm_automations smm_automations_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.smm_automations
    ADD CONSTRAINT smm_automations_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.smm_automations DROP CONSTRAINT smm_automations_pkey;
       public            postgres    false    339            ‰           2606    35914 F   smm_brand_channels smm_brand_channels_brand_id_network_external_id_key 
   CONSTRAINT     ›   ALTER TABLE ONLY public.smm_brand_channels
    ADD CONSTRAINT smm_brand_channels_brand_id_network_external_id_key UNIQUE (brand_id, network, external_id);
 p   ALTER TABLE ONLY public.smm_brand_channels DROP CONSTRAINT smm_brand_channels_brand_id_network_external_id_key;
       public            postgres    false    333    333    333            ‹           2606    35912 *   smm_brand_channels smm_brand_channels_pkey 
   CONSTRAINT     h   ALTER TABLE ONLY public.smm_brand_channels
    ADD CONSTRAINT smm_brand_channels_pkey PRIMARY KEY (id);
 T   ALTER TABLE ONLY public.smm_brand_channels DROP CONSTRAINT smm_brand_channels_pkey;
       public            postgres    false    333            „           2606    35882    smm_brands smm_brands_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.smm_brands
    ADD CONSTRAINT smm_brands_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.smm_brands DROP CONSTRAINT smm_brands_pkey;
       public            postgres    false    331            ќ           2606    36026 <   smm_channel_counters smm_channel_counters_channel_id_day_key 
   CONSTRAINT     ‚   ALTER TABLE ONLY public.smm_channel_counters
    ADD CONSTRAINT smm_channel_counters_channel_id_day_key UNIQUE (channel_id, day);
 f   ALTER TABLE ONLY public.smm_channel_counters DROP CONSTRAINT smm_channel_counters_channel_id_day_key;
       public            postgres    false    343    343            џ           2606    36024 .   smm_channel_counters smm_channel_counters_pkey 
   CONSTRAINT     l   ALTER TABLE ONLY public.smm_channel_counters
    ADD CONSTRAINT smm_channel_counters_pkey PRIMARY KEY (id);
 X   ALTER TABLE ONLY public.smm_channel_counters DROP CONSTRAINT smm_channel_counters_pkey;
       public            postgres    false    343            Ї           2606    36116 >   smm_channel_metric_snapshots smm_channel_metric_snapshots_pkey 
   CONSTRAINT     |   ALTER TABLE ONLY public.smm_channel_metric_snapshots
    ADD CONSTRAINT smm_channel_metric_snapshots_pkey PRIMARY KEY (id);
 h   ALTER TABLE ONLY public.smm_channel_metric_snapshots DROP CONSTRAINT smm_channel_metric_snapshots_pkey;
       public            postgres    false    352            љ           2606    36002 6   smm_competitor_snapshots smm_competitor_snapshots_pkey 
   CONSTRAINT     t   ALTER TABLE ONLY public.smm_competitor_snapshots
    ADD CONSTRAINT smm_competitor_snapshots_pkey PRIMARY KEY (id);
 `   ALTER TABLE ONLY public.smm_competitor_snapshots DROP CONSTRAINT smm_competitor_snapshots_pkey;
       public            postgres    false    341            ђ           2606    35936 $   smm_inbox_items smm_inbox_items_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.smm_inbox_items
    ADD CONSTRAINT smm_inbox_items_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.smm_inbox_items DROP CONSTRAINT smm_inbox_items_pkey;
       public            postgres    false    335            ©           2606    36086 *   smm_message_events smm_message_events_pkey 
   CONSTRAINT     h   ALTER TABLE ONLY public.smm_message_events
    ADD CONSTRAINT smm_message_events_pkey PRIMARY KEY (id);
 T   ALTER TABLE ONLY public.smm_message_events DROP CONSTRAINT smm_message_events_pkey;
       public            postgres    false    348            ¬           2606    36106 8   smm_post_metric_snapshots smm_post_metric_snapshots_pkey 
   CONSTRAINT     v   ALTER TABLE ONLY public.smm_post_metric_snapshots
    ADD CONSTRAINT smm_post_metric_snapshots_pkey PRIMARY KEY (id);
 b   ALTER TABLE ONLY public.smm_post_metric_snapshots DROP CONSTRAINT smm_post_metric_snapshots_pkey;
       public            postgres    false    350            ”           2606    35963 &   smm_publish_jobs smm_publish_jobs_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.smm_publish_jobs
    ADD CONSTRAINT smm_publish_jobs_pkey PRIMARY KEY (id);
 P   ALTER TABLE ONLY public.smm_publish_jobs DROP CONSTRAINT smm_publish_jobs_pkey;
       public            postgres    false    337            |           2606    35852 $   system_settings system_settings_pkey 
   CONSTRAINT     c   ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (key);
 N   ALTER TABLE ONLY public.system_settings DROP CONSTRAINT system_settings_pkey;
       public            postgres    false    327            ±           2606    34871 "   tg_dedup_cache tg_dedup_cache_pkey 
   CONSTRAINT     `   ALTER TABLE ONLY public.tg_dedup_cache
    ADD CONSTRAINT tg_dedup_cache_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.tg_dedup_cache DROP CONSTRAINT tg_dedup_cache_pkey;
       public            postgres    false    232            №           2606    34897    tg_digests tg_digests_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.tg_digests
    ADD CONSTRAINT tg_digests_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.tg_digests DROP CONSTRAINT tg_digests_pkey;
       public            postgres    false    236            ­           2606    34859    tg_events tg_events_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.tg_events
    ADD CONSTRAINT tg_events_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.tg_events DROP CONSTRAINT tg_events_pkey;
       public            postgres    false    230            §           2606    34846 (   tg_post_templates tg_post_templates_pkey 
   CONSTRAINT     f   ALTER TABLE ONLY public.tg_post_templates
    ADD CONSTRAINT tg_post_templates_pkey PRIMARY KEY (id);
 R   ALTER TABLE ONLY public.tg_post_templates DROP CONSTRAINT tg_post_templates_pkey;
       public            postgres    false    228            ¤           2606    34829    tg_posts tg_posts_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.tg_posts
    ADD CONSTRAINT tg_posts_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.tg_posts DROP CONSTRAINT tg_posts_pkey;
       public            postgres    false    226            њ           2606    34798    tg_profiles tg_profiles_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.tg_profiles
    ADD CONSTRAINT tg_profiles_pkey PRIMARY KEY (id);
 F   ALTER TABLE ONLY public.tg_profiles DROP CONSTRAINT tg_profiles_pkey;
       public            postgres    false    224            ћ           2606    34800 #   tg_profiles tg_profiles_user_id_key 
   CONSTRAINT     a   ALTER TABLE ONLY public.tg_profiles
    ADD CONSTRAINT tg_profiles_user_id_key UNIQUE (user_id);
 M   ALTER TABLE ONLY public.tg_profiles DROP CONSTRAINT tg_profiles_user_id_key;
       public            postgres    false    224            ґ           2606    34883 &   tg_summary_cache tg_summary_cache_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.tg_summary_cache
    ADD CONSTRAINT tg_summary_cache_pkey PRIMARY KEY (id);
 P   ALTER TABLE ONLY public.tg_summary_cache DROP CONSTRAINT tg_summary_cache_pkey;
       public            postgres    false    234            ¶           2606    34885 /   tg_summary_cache tg_summary_cache_text_hash_key 
   CONSTRAINT     o   ALTER TABLE ONLY public.tg_summary_cache
    ADD CONSTRAINT tg_summary_cache_text_hash_key UNIQUE (text_hash);
 Y   ALTER TABLE ONLY public.tg_summary_cache DROP CONSTRAINT tg_summary_cache_text_hash_key;
       public            postgres    false    234            У           2606    35056     threads_posts threads_posts_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.threads_posts
    ADD CONSTRAINT threads_posts_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.threads_posts DROP CONSTRAINT threads_posts_pkey;
       public            postgres    false    248            Н           2606    35026 &   threads_profiles threads_profiles_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.threads_profiles
    ADD CONSTRAINT threads_profiles_pkey PRIMARY KEY (id);
 P   ALTER TABLE ONLY public.threads_profiles DROP CONSTRAINT threads_profiles_pkey;
       public            postgres    false    246            П           2606    35028 -   threads_profiles threads_profiles_user_id_key 
   CONSTRAINT     k   ALTER TABLE ONLY public.threads_profiles
    ADD CONSTRAINT threads_profiles_user_id_key UNIQUE (user_id);
 W   ALTER TABLE ONLY public.threads_profiles DROP CONSTRAINT threads_profiles_user_id_key;
       public            postgres    false    246            Ч           2606    35069 8   threads_selenium_sessions threads_selenium_sessions_pkey 
   CONSTRAINT     v   ALTER TABLE ONLY public.threads_selenium_sessions
    ADD CONSTRAINT threads_selenium_sessions_pkey PRIMARY KEY (id);
 b   ALTER TABLE ONLY public.threads_selenium_sessions DROP CONSTRAINT threads_selenium_sessions_pkey;
       public            postgres    false    250                        2606    35374    tw_posts tw_posts_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.tw_posts
    ADD CONSTRAINT tw_posts_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.tw_posts DROP CONSTRAINT tw_posts_pkey;
       public            postgres    false    280                       2606    35336    tw_profiles tw_profiles_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.tw_profiles
    ADD CONSTRAINT tw_profiles_pkey PRIMARY KEY (id);
 F   ALTER TABLE ONLY public.tw_profiles DROP CONSTRAINT tw_profiles_pkey;
       public            postgres    false    278                       2606    35339 #   tw_profiles tw_profiles_user_id_key 
   CONSTRAINT     a   ALTER TABLE ONLY public.tw_profiles
    ADD CONSTRAINT tw_profiles_user_id_key UNIQUE (user_id);
 M   ALTER TABLE ONLY public.tw_profiles DROP CONSTRAINT tw_profiles_user_id_key;
       public            postgres    false    278            Ґ           2606    36066    url_posts url_posts_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.url_posts
    ADD CONSTRAINT url_posts_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.url_posts DROP CONSTRAINT url_posts_pkey;
       public            postgres    false    346            ш           2606    35162 6   user_role_tariff_history user_role_tariff_history_pkey 
   CONSTRAINT     t   ALTER TABLE ONLY public.user_role_tariff_history
    ADD CONSTRAINT user_role_tariff_history_pkey PRIMARY KEY (id);
 `   ALTER TABLE ONLY public.user_role_tariff_history DROP CONSTRAINT user_role_tariff_history_pkey;
       public            postgres    false    262            Ъ           2606    35091    users users_email_key 
   CONSTRAINT     Q   ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);
 ?   ALTER TABLE ONLY public.users DROP CONSTRAINT users_email_key;
       public            postgres    false    252            Ь           2606    35087    users users_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
       public            postgres    false    252            Ю           2606    35089    users users_username_key 
   CONSTRAINT     W   ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);
 B   ALTER TABLE ONLY public.users DROP CONSTRAINT users_username_key;
       public            postgres    false    252                       2606    35267    vk_posts vk_posts_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.vk_posts
    ADD CONSTRAINT vk_posts_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.vk_posts DROP CONSTRAINT vk_posts_pkey;
       public            postgres    false    270            ь           2606    35215    vk_profiles vk_profiles_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.vk_profiles
    ADD CONSTRAINT vk_profiles_pkey PRIMARY KEY (id);
 F   ALTER TABLE ONLY public.vk_profiles DROP CONSTRAINT vk_profiles_pkey;
       public            postgres    false    266            ю           2606    35217 #   vk_profiles vk_profiles_user_id_key 
   CONSTRAINT     a   ALTER TABLE ONLY public.vk_profiles
    ADD CONSTRAINT vk_profiles_user_id_key UNIQUE (user_id);
 M   ALTER TABLE ONLY public.vk_profiles DROP CONSTRAINT vk_profiles_user_id_key;
       public            postgres    false    266            ђ           2606    34716 *   wp_collect_profile wp_collect_profile_pkey 
   CONSTRAINT     h   ALTER TABLE ONLY public.wp_collect_profile
    ADD CONSTRAINT wp_collect_profile_pkey PRIMARY KEY (id);
 T   ALTER TABLE ONLY public.wp_collect_profile DROP CONSTRAINT wp_collect_profile_pkey;
       public            postgres    false    218            ’           2606    34718 1   wp_collect_profile wp_collect_profile_user_id_key 
   CONSTRAINT     o   ALTER TABLE ONLY public.wp_collect_profile
    ADD CONSTRAINT wp_collect_profile_user_id_key UNIQUE (user_id);
 [   ALTER TABLE ONLY public.wp_collect_profile DROP CONSTRAINT wp_collect_profile_user_id_key;
       public            postgres    false    218            –           2606    34729 &   wp_collect_sites wp_collect_sites_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.wp_collect_sites
    ADD CONSTRAINT wp_collect_sites_pkey PRIMARY KEY (id);
 P   ALTER TABLE ONLY public.wp_collect_sites DROP CONSTRAINT wp_collect_sites_pkey;
       public            postgres    false    220            љ           2606    34764    wp_posts wp_posts_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.wp_posts
    ADD CONSTRAINT wp_posts_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.wp_posts DROP CONSTRAINT wp_posts_pkey;
       public            postgres    false    222            Њ           2606    34702 *   wp_publish_profile wp_publish_profile_pkey 
   CONSTRAINT     h   ALTER TABLE ONLY public.wp_publish_profile
    ADD CONSTRAINT wp_publish_profile_pkey PRIMARY KEY (id);
 T   ALTER TABLE ONLY public.wp_publish_profile DROP CONSTRAINT wp_publish_profile_pkey;
       public            postgres    false    216            Ћ           2606    34704 1   wp_publish_profile wp_publish_profile_user_id_key 
   CONSTRAINT     o   ALTER TABLE ONLY public.wp_publish_profile
    ADD CONSTRAINT wp_publish_profile_user_id_key UNIQUE (user_id);
 [   ALTER TABLE ONLY public.wp_publish_profile DROP CONSTRAINT wp_publish_profile_user_id_key;
       public            postgres    false    216                       1259    35380 !   idx_admin_audit_log_admin_user_id    INDEX     f   CREATE INDEX idx_admin_audit_log_admin_user_id ON public.admin_audit_log USING btree (admin_user_id);
 5   DROP INDEX public.idx_admin_audit_log_admin_user_id;
       public            postgres    false    276                       1259    35378    idx_admin_audit_log_created_at    INDEX     `   CREATE INDEX idx_admin_audit_log_created_at ON public.admin_audit_log USING btree (created_at);
 2   DROP INDEX public.idx_admin_audit_log_created_at;
       public            postgres    false    276            s           1259    35819    idx_ai_tasks_status_created    INDEX     ^   CREATE INDEX idx_ai_tasks_status_created ON public.ai_tasks USING btree (status, created_at);
 /   DROP INDEX public.idx_ai_tasks_status_created;
       public            postgres    false    322    322                       1259    35375    idx_billing_events_created_at    INDEX     ^   CREATE INDEX idx_billing_events_created_at ON public.billing_events USING btree (created_at);
 1   DROP INDEX public.idx_billing_events_created_at;
       public            postgres    false    274                       1259    35376 $   idx_billing_events_provider_event_id    INDEX     t   CREATE UNIQUE INDEX idx_billing_events_provider_event_id ON public.billing_events USING btree (provider, event_id);
 8   DROP INDEX public.idx_billing_events_provider_event_id;
       public            postgres    false    274    274                       1259    35372    idx_billing_events_user_id    INDEX     X   CREATE INDEX idx_billing_events_user_id ON public.billing_events USING btree (user_id);
 .   DROP INDEX public.idx_billing_events_user_id;
       public            postgres    false    274            й           1259    35333    idx_blacklisted_tokens_token    INDEX     \   CREATE INDEX idx_blacklisted_tokens_token ON public.blacklisted_tokens USING btree (token);
 0   DROP INDEX public.idx_blacklisted_tokens_token;
       public            postgres    false    256            b           1259    35750    idx_cpost_posts_status_created    INDEX     d   CREATE INDEX idx_cpost_posts_status_created ON public.cpost_posts USING btree (status, created_at);
 2   DROP INDEX public.idx_cpost_posts_status_created;
       public            postgres    false    314    314            c           1259    35749    idx_cpost_posts_user_created    INDEX     c   CREATE INDEX idx_cpost_posts_user_created ON public.cpost_posts USING btree (user_id, created_at);
 0   DROP INDEX public.idx_cpost_posts_user_created;
       public            postgres    false    314    314            l           1259    35792    idx_curl_one_time_done_user    INDEX     ]   CREATE INDEX idx_curl_one_time_done_user ON public.curl_one_time_done USING btree (user_id);
 /   DROP INDEX public.idx_curl_one_time_done_user;
       public            postgres    false    318            А           1259    34972    idx_dzen_posts_status_created    INDEX     b   CREATE INDEX idx_dzen_posts_status_created ON public.dzen_posts USING btree (status, created_at);
 1   DROP INDEX public.idx_dzen_posts_status_created;
       public            postgres    false    240    240            Б           1259    34969    idx_dzen_posts_user_created    INDEX     a   CREATE INDEX idx_dzen_posts_user_created ON public.dzen_posts USING btree (user_id, created_at);
 /   DROP INDEX public.idx_dzen_posts_user_created;
       public            postgres    false    240    240            ф           1259    35341 #   idx_email_verification_tokens_token    INDEX     j   CREATE INDEX idx_email_verification_tokens_token ON public.email_verification_tokens USING btree (token);
 7   DROP INDEX public.idx_email_verification_tokens_token;
       public            postgres    false    260            х           1259    35340 %   idx_email_verification_tokens_user_id    INDEX     n   CREATE INDEX idx_email_verification_tokens_user_id ON public.email_verification_tokens USING btree (user_id);
 9   DROP INDEX public.idx_email_verification_tokens_user_id;
       public            postgres    false    260            z           1259    35844    idx_feedback_created_at    INDEX     W   CREATE INDEX idx_feedback_created_at ON public.feedback USING btree (created_at DESC);
 +   DROP INDEX public.idx_feedback_created_at;
       public            postgres    false    326            F           1259    35578    idx_game_menu_nodes_mode_parent    INDEX     i   CREATE INDEX idx_game_menu_nodes_mode_parent ON public.game_menu_nodes USING btree (mode_id, parent_id);
 3   DROP INDEX public.idx_game_menu_nodes_mode_parent;
       public            postgres    false    300    300            S           1259    35668    idx_game_menu_orders_bot    INDEX     h   CREATE INDEX idx_game_menu_orders_bot ON public.game_menu_orders USING btree (bot_id, created_at DESC);
 ,   DROP INDEX public.idx_game_menu_orders_bot;
       public            postgres    false    306    306            T           1259    35667    idx_game_menu_orders_mode    INDEX     j   CREATE INDEX idx_game_menu_orders_mode ON public.game_menu_orders USING btree (mode_id, created_at DESC);
 -   DROP INDEX public.idx_game_menu_orders_mode;
       public            postgres    false    306    306            *           1259    35551    idx_game_modes_bot_code    INDEX     ]   CREATE UNIQUE INDEX idx_game_modes_bot_code ON public.game_modes USING btree (bot_id, code);
 +   DROP INDEX public.idx_game_modes_bot_code;
       public            postgres    false    286    286            '           1259    35552    idx_game_players_bot_user    INDEX     m   CREATE UNIQUE INDEX idx_game_players_bot_user ON public.game_players USING btree (bot_id, telegram_user_id);
 -   DROP INDEX public.idx_game_players_bot_user;
       public            postgres    false    284    284            -           1259    35532    idx_game_questions_mode    INDEX     n   CREATE INDEX idx_game_questions_mode ON public.game_questions USING btree (mode_id) WHERE (is_active = true);
 +   DROP INDEX public.idx_game_questions_mode;
       public            postgres    false    288    288            4           1259    35534    idx_game_sessions_finished    INDEX     h   CREATE INDEX idx_game_sessions_finished ON public.game_sessions USING btree (status, finished_at DESC);
 .   DROP INDEX public.idx_game_sessions_finished;
       public            postgres    false    292    292            5           1259    35533    idx_game_sessions_player_status    INDEX     f   CREATE INDEX idx_game_sessions_player_status ON public.game_sessions USING btree (player_id, status);
 3   DROP INDEX public.idx_game_sessions_player_status;
       public            postgres    false    292    292                       1259    35343    idx_group_members_group_id    INDEX     X   CREATE INDEX idx_group_members_group_id ON public.group_members USING btree (group_id);
 .   DROP INDEX public.idx_group_members_group_id;
       public            postgres    false    268                       1259    35348    idx_group_members_user_id    INDEX     V   CREATE INDEX idx_group_members_user_id ON public.group_members USING btree (user_id);
 -   DROP INDEX public.idx_group_members_user_id;
       public            postgres    false    268            Ѓ           1259    35872    idx_guide_blocks_sort    INDEX     T   CREATE INDEX idx_guide_blocks_sort ON public.guide_blocks USING btree (sort_order);
 )   DROP INDEX public.idx_guide_blocks_sort;
       public            postgres    false    329            Ж           1259    35005    idx_instagram_posts_source    INDEX     ќ   CREATE UNIQUE INDEX idx_instagram_posts_source ON public.instagram_posts USING btree (user_id, instagram_source_id) WHERE (instagram_source_id IS NOT NULL);
 .   DROP INDEX public.idx_instagram_posts_source;
       public            postgres    false    244    244    244            З           1259    35003 "   idx_instagram_posts_status_created    INDEX     l   CREATE INDEX idx_instagram_posts_status_created ON public.instagram_posts USING btree (status, created_at);
 6   DROP INDEX public.idx_instagram_posts_status_created;
       public            postgres    false    244    244            И           1259    35002     idx_instagram_posts_user_created    INDEX     k   CREATE INDEX idx_instagram_posts_user_created ON public.instagram_posts USING btree (user_id, created_at);
 4   DROP INDEX public.idx_instagram_posts_user_created;
       public            postgres    false    244    244            Й           1259    35004    idx_instagram_posts_user_domain    INDEX     f   CREATE INDEX idx_instagram_posts_user_domain ON public.instagram_posts USING btree (user_id, domain);
 3   DROP INDEX public.idx_instagram_posts_user_domain;
       public            postgres    false    244    244            t           1259    35831    idx_notifications_created_at    INDEX     a   CREATE INDEX idx_notifications_created_at ON public.notifications USING btree (created_at DESC);
 0   DROP INDEX public.idx_notifications_created_at;
       public            postgres    false    324            u           1259    35832    idx_notifications_user_id    INDEX     V   CREATE INDEX idx_notifications_user_id ON public.notifications USING btree (user_id);
 -   DROP INDEX public.idx_notifications_user_id;
       public            postgres    false    324            к           1259    35337    idx_password_reset_tokens_token    INDEX     b   CREATE INDEX idx_password_reset_tokens_token ON public.password_reset_tokens USING btree (token);
 3   DROP INDEX public.idx_password_reset_tokens_token;
       public            postgres    false    258            л           1259    35335 !   idx_password_reset_tokens_user_id    INDEX     f   CREATE INDEX idx_password_reset_tokens_user_id ON public.password_reset_tokens USING btree (user_id);
 5   DROP INDEX public.idx_password_reset_tokens_user_id;
       public            postgres    false    258            W           1259    35705    idx_posts_source    INDEX     ѓ   CREATE UNIQUE INDEX idx_posts_source ON public.posts USING btree (source_platform, source_id) WHERE (source_platform IS NOT NULL);
 $   DROP INDEX public.idx_posts_source;
       public            postgres    false    310    310    310            X           1259    35704    idx_posts_status_created    INDEX     X   CREATE INDEX idx_posts_status_created ON public.posts USING btree (status, created_at);
 ,   DROP INDEX public.idx_posts_status_created;
       public            postgres    false    310    310            Y           1259    35706    idx_posts_user_created    INDEX     W   CREATE INDEX idx_posts_user_created ON public.posts USING btree (user_id, created_at);
 *   DROP INDEX public.idx_posts_user_created;
       public            postgres    false    310    310            Я           1259    35322    idx_refresh_tokens_token    INDEX     T   CREATE INDEX idx_refresh_tokens_token ON public.refresh_tokens USING btree (token);
 ,   DROP INDEX public.idx_refresh_tokens_token;
       public            postgres    false    254            а           1259    35317    idx_refresh_tokens_user_id    INDEX     X   CREATE INDEX idx_refresh_tokens_user_id ON public.refresh_tokens USING btree (user_id);
 .   DROP INDEX public.idx_refresh_tokens_user_id;
       public            postgres    false    254            m           1259    35805    idx_service_cycle_log_created    INDEX     f   CREATE INDEX idx_service_cycle_log_created ON public.service_cycle_log USING btree (created_at DESC);
 1   DROP INDEX public.idx_service_cycle_log_created;
       public            postgres    false    320            n           1259    35806 %   idx_service_cycle_log_service_created    INDEX     |   CREATE INDEX idx_service_cycle_log_service_created ON public.service_cycle_log USING btree (service_name, created_at DESC);
 9   DROP INDEX public.idx_service_cycle_log_service_created;
       public            postgres    false    320    320            •           1259    36013    idx_smm_automations_user    INDEX     W   CREATE INDEX idx_smm_automations_user ON public.smm_automations USING btree (user_id);
 ,   DROP INDEX public.idx_smm_automations_user;
       public            postgres    false    339            …           1259    36009    idx_smm_brand_channels_brand_id    INDEX     b   CREATE INDEX idx_smm_brand_channels_brand_id ON public.smm_brand_channels USING btree (brand_id);
 3   DROP INDEX public.idx_smm_brand_channels_brand_id;
       public            postgres    false    333            ‚           1259    36008    idx_smm_brands_user_id    INDEX     P   CREATE INDEX idx_smm_brands_user_id ON public.smm_brands USING btree (user_id);
 *   DROP INDEX public.idx_smm_brands_user_id;
       public            postgres    false    331            ›           1259    36032 !   idx_smm_channel_counters_user_day    INDEX     j   CREATE INDEX idx_smm_channel_counters_user_day ON public.smm_channel_counters USING btree (user_id, day);
 5   DROP INDEX public.idx_smm_channel_counters_user_day;
       public            postgres    false    343    343            ­           1259    36122    idx_smm_channel_metric_channel    INDEX     z   CREATE INDEX idx_smm_channel_metric_channel ON public.smm_channel_metric_snapshots USING btree (channel_id, captured_at);
 2   DROP INDEX public.idx_smm_channel_metric_channel;
       public            postgres    false    352    352            †           1259    35920    idx_smm_channels_discussion    INDEX         CREATE INDEX idx_smm_channels_discussion ON public.smm_brand_channels USING btree (network, discussion_external_id) WHERE (discussion_external_id IS NOT NULL);
 /   DROP INDEX public.idx_smm_channels_discussion;
       public            postgres    false    333    333    333            ‡           1259    35921    idx_smm_channels_tg_external    INDEX     ђ   CREATE INDEX idx_smm_channels_tg_external ON public.smm_brand_channels USING btree (network, external_id) WHERE ((network)::text = 'tg'::text);
 0   DROP INDEX public.idx_smm_channels_tg_external;
       public            postgres    false    333    333    333                       1259    36014    idx_smm_competitor_channel    INDEX     e   CREATE INDEX idx_smm_competitor_channel ON public.smm_competitor_snapshots USING btree (channel_id);
 .   DROP INDEX public.idx_smm_competitor_channel;
       public            postgres    false    341            Њ           1259    36011    idx_smm_inbox_brand_status    INDEX     b   CREATE INDEX idx_smm_inbox_brand_status ON public.smm_inbox_items USING btree (brand_id, status);
 .   DROP INDEX public.idx_smm_inbox_brand_status;
       public            postgres    false    335    335            Ќ           1259    35947    idx_smm_inbox_dedup    INDEX     —   CREATE UNIQUE INDEX idx_smm_inbox_dedup ON public.smm_inbox_items USING btree (user_id, network, external_msg_id) WHERE (external_msg_id IS NOT NULL);
 '   DROP INDEX public.idx_smm_inbox_dedup;
       public            postgres    false    335    335    335    335            Ћ           1259    36010    idx_smm_inbox_user_id    INDEX     T   CREATE INDEX idx_smm_inbox_user_id ON public.smm_inbox_items USING btree (user_id);
 )   DROP INDEX public.idx_smm_inbox_user_id;
       public            postgres    false    335            ‘           1259    35969    idx_smm_jobs_status_publish    INDEX     f   CREATE INDEX idx_smm_jobs_status_publish ON public.smm_publish_jobs USING btree (status, publish_at);
 /   DROP INDEX public.idx_smm_jobs_status_publish;
       public            postgres    false    337    337            ’           1259    36012    idx_smm_jobs_user_brand    INDEX     a   CREATE INDEX idx_smm_jobs_user_brand ON public.smm_publish_jobs USING btree (user_id, brand_id);
 +   DROP INDEX public.idx_smm_jobs_user_brand;
       public            postgres    false    337    337            ¦           1259    36092 &   idx_smm_message_events_channel_created    INDEX     w   CREATE INDEX idx_smm_message_events_channel_created ON public.smm_message_events USING btree (channel_id, created_at);
 :   DROP INDEX public.idx_smm_message_events_channel_created;
       public            postgres    false    348    348            §           1259    36093 #   idx_smm_message_events_user_created    INDEX     q   CREATE INDEX idx_smm_message_events_user_created ON public.smm_message_events USING btree (user_id, created_at);
 7   DROP INDEX public.idx_smm_message_events_user_created;
       public            postgres    false    348    348            Є           1259    36107 "   idx_smm_post_metric_snapshots_post    INDEX     ‚   CREATE INDEX idx_smm_post_metric_snapshots_post ON public.smm_post_metric_snapshots USING btree (platform, post_id, captured_at);
 6   DROP INDEX public.idx_smm_post_metric_snapshots_post;
       public            postgres    false    350    350    350            ®           1259    34873    idx_tg_dedup_expires    INDEX     U   CREATE INDEX idx_tg_dedup_expires ON public.tg_dedup_cache USING btree (expires_at);
 (   DROP INDEX public.idx_tg_dedup_expires;
       public            postgres    false    232            Ї           1259    34872    idx_tg_dedup_user_hash_chat    INDEX     m   CREATE INDEX idx_tg_dedup_user_hash_chat ON public.tg_dedup_cache USING btree (user_id, text_hash, chat_id);
 /   DROP INDEX public.idx_tg_dedup_user_hash_chat;
       public            postgres    false    232    232    232            ·           1259    34898    idx_tg_digests_user_created    INDEX     a   CREATE INDEX idx_tg_digests_user_created ON public.tg_digests USING btree (user_id, created_at);
 /   DROP INDEX public.idx_tg_digests_user_created;
       public            postgres    false    236    236            Ё           1259    34862    idx_tg_events_hash_chat    INDEX     [   CREATE INDEX idx_tg_events_hash_chat ON public.tg_events USING btree (text_hash, chat_id);
 +   DROP INDEX public.idx_tg_events_hash_chat;
       public            postgres    false    230    230            ©           1259    34863    idx_tg_events_rule_created    INDEX     _   CREATE INDEX idx_tg_events_rule_created ON public.tg_events USING btree (rule_id, created_at);
 .   DROP INDEX public.idx_tg_events_rule_created;
       public            postgres    false    230    230            Є           1259    34861    idx_tg_events_type_created    INDEX     b   CREATE INDEX idx_tg_events_type_created ON public.tg_events USING btree (event_type, created_at);
 .   DROP INDEX public.idx_tg_events_type_created;
       public            postgres    false    230    230            «           1259    34860    idx_tg_events_user_created    INDEX     _   CREATE INDEX idx_tg_events_user_created ON public.tg_events USING btree (user_id, created_at);
 .   DROP INDEX public.idx_tg_events_user_created;
       public            postgres    false    230    230            Ґ           1259    34847    idx_tg_post_templates_user    INDEX     [   CREATE INDEX idx_tg_post_templates_user ON public.tg_post_templates USING btree (user_id);
 .   DROP INDEX public.idx_tg_post_templates_user;
       public            postgres    false    228            џ           1259    34832    idx_tg_posts_publish_at    INDEX     R   CREATE INDEX idx_tg_posts_publish_at ON public.tg_posts USING btree (publish_at);
 +   DROP INDEX public.idx_tg_posts_publish_at;
       public            postgres    false    226                        1259    34831    idx_tg_posts_status_created    INDEX     ^   CREATE INDEX idx_tg_posts_status_created ON public.tg_posts USING btree (status, created_at);
 /   DROP INDEX public.idx_tg_posts_status_created;
       public            postgres    false    226    226            Ў           1259    34833    idx_tg_posts_status_publish_at    INDEX     a   CREATE INDEX idx_tg_posts_status_publish_at ON public.tg_posts USING btree (status, publish_at);
 2   DROP INDEX public.idx_tg_posts_status_publish_at;
       public            postgres    false    226    226            ў           1259    34830    idx_tg_posts_user_created    INDEX     ]   CREATE INDEX idx_tg_posts_user_created ON public.tg_posts USING btree (user_id, created_at);
 -   DROP INDEX public.idx_tg_posts_user_created;
       public            postgres    false    226    226            І           1259    34886    idx_tg_summary_cache_expires    INDEX     _   CREATE INDEX idx_tg_summary_cache_expires ON public.tg_summary_cache USING btree (expires_at);
 0   DROP INDEX public.idx_tg_summary_cache_expires;
       public            postgres    false    234            Р           1259    35058     idx_threads_posts_status_created    INDEX     h   CREATE INDEX idx_threads_posts_status_created ON public.threads_posts USING btree (status, created_at);
 4   DROP INDEX public.idx_threads_posts_status_created;
       public            postgres    false    248    248            С           1259    35057    idx_threads_posts_user_created    INDEX     g   CREATE INDEX idx_threads_posts_user_created ON public.threads_posts USING btree (user_id, created_at);
 2   DROP INDEX public.idx_threads_posts_user_created;
       public            postgres    false    248    248            Ф           1259    35071 (   idx_threads_selenium_sessions_created_at    INDEX     y   CREATE INDEX idx_threads_selenium_sessions_created_at ON public.threads_selenium_sessions USING btree (created_at DESC);
 <   DROP INDEX public.idx_threads_selenium_sessions_created_at;
       public            postgres    false    250            Х           1259    35070 %   idx_threads_selenium_sessions_user_id    INDEX     n   CREATE INDEX idx_threads_selenium_sessions_user_id ON public.threads_selenium_sessions USING btree (user_id);
 9   DROP INDEX public.idx_threads_selenium_sessions_user_id;
       public            postgres    false    250                       1259    35379    idx_tw_posts_status_created    INDEX     ^   CREATE INDEX idx_tw_posts_status_created ON public.tw_posts USING btree (status, created_at);
 /   DROP INDEX public.idx_tw_posts_status_created;
       public            postgres    false    280    280                       1259    35377    idx_tw_posts_user_created    INDEX     ]   CREATE INDEX idx_tw_posts_user_created ON public.tw_posts USING btree (user_id, created_at);
 -   DROP INDEX public.idx_tw_posts_user_created;
       public            postgres    false    280    280            ў           1259    36068    idx_url_posts_status_created    INDEX     `   CREATE INDEX idx_url_posts_status_created ON public.url_posts USING btree (status, created_at);
 0   DROP INDEX public.idx_url_posts_status_created;
       public            postgres    false    346    346            Ј           1259    36067    idx_url_posts_user_created    INDEX     _   CREATE INDEX idx_url_posts_user_created ON public.url_posts USING btree (user_id, created_at);
 .   DROP INDEX public.idx_url_posts_user_created;
       public            postgres    false    346    346            ц           1259    35342 $   idx_user_role_tariff_history_user_id    INDEX     l   CREATE INDEX idx_user_role_tariff_history_user_id ON public.user_role_tariff_history USING btree (user_id);
 8   DROP INDEX public.idx_user_role_tariff_history_user_id;
       public            postgres    false    262            Ш           1259    35369    idx_users_created_at    INDEX     Q   CREATE INDEX idx_users_created_at ON public.users USING btree (created_at DESC);
 (   DROP INDEX public.idx_users_created_at;
       public            postgres    false    252                       1259    35283    idx_vk_posts_publish_at    INDEX     R   CREATE INDEX idx_vk_posts_publish_at ON public.vk_posts USING btree (publish_at);
 +   DROP INDEX public.idx_vk_posts_publish_at;
       public            postgres    false    270                       1259    35281    idx_vk_posts_status_created    INDEX     ^   CREATE INDEX idx_vk_posts_status_created ON public.vk_posts USING btree (status, created_at);
 /   DROP INDEX public.idx_vk_posts_status_created;
       public            postgres    false    270    270                       1259    35284    idx_vk_posts_status_publish_at    INDEX     a   CREATE INDEX idx_vk_posts_status_publish_at ON public.vk_posts USING btree (status, publish_at);
 2   DROP INDEX public.idx_vk_posts_status_publish_at;
       public            postgres    false    270    270                       1259    35277    idx_vk_posts_user_created    INDEX     ]   CREATE INDEX idx_vk_posts_user_created ON public.vk_posts USING btree (user_id, created_at);
 -   DROP INDEX public.idx_vk_posts_user_created;
       public            postgres    false    270    270            	           1259    35289    idx_vk_posts_user_domain    INDEX     X   CREATE INDEX idx_vk_posts_user_domain ON public.vk_posts USING btree (user_id, domain);
 ,   DROP INDEX public.idx_vk_posts_user_domain;
       public            postgres    false    270    270            “           1259    34736    idx_wp_collect_sites_profile_id    INDEX     b   CREATE INDEX idx_wp_collect_sites_profile_id ON public.wp_collect_sites USING btree (profile_id);
 3   DROP INDEX public.idx_wp_collect_sites_profile_id;
       public            postgres    false    220            ”           1259    34735    idx_wp_collect_sites_user_id    INDEX     \   CREATE INDEX idx_wp_collect_sites_user_id ON public.wp_collect_sites USING btree (user_id);
 0   DROP INDEX public.idx_wp_collect_sites_user_id;
       public            postgres    false    220            —           1259    34766    idx_wp_posts_status_created    INDEX     ^   CREATE INDEX idx_wp_posts_status_created ON public.wp_posts USING btree (status, created_at);
 /   DROP INDEX public.idx_wp_posts_status_created;
       public            postgres    false    222    222                       1259    34765    idx_wp_posts_user_created    INDEX     ]   CREATE INDEX idx_wp_posts_user_created ON public.wp_posts USING btree (user_id, created_at);
 -   DROP INDEX public.idx_wp_posts_user_created;
       public            postgres    false    222    222            є           2606    35311 2   admin_audit_log admin_audit_log_admin_user_id_fkey 
   FK CONSTRAINT     ©   ALTER TABLE ONLY public.admin_audit_log
    ADD CONSTRAINT admin_audit_log_admin_user_id_fkey FOREIGN KEY (admin_user_id) REFERENCES public.users(id) ON DELETE CASCADE;
 \   ALTER TABLE ONLY public.admin_audit_log DROP CONSTRAINT admin_audit_log_admin_user_id_fkey;
       public          postgres    false    252    276    5596            №           2606    35296 *   billing_events billing_events_user_id_fkey 
   FK CONSTRAINT     њ   ALTER TABLE ONLY public.billing_events
    ADD CONSTRAINT billing_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;
 T   ALTER TABLE ONLY public.billing_events DROP CONSTRAINT billing_events_user_id_fkey;
       public          postgres    false    252    5596    274            і           2606    35150 @   email_verification_tokens email_verification_tokens_user_id_fkey 
   FK CONSTRAINT     ±   ALTER TABLE ONLY public.email_verification_tokens
    ADD CONSTRAINT email_verification_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
 j   ALTER TABLE ONLY public.email_verification_tokens DROP CONSTRAINT email_verification_tokens_user_id_fkey;
       public          postgres    false    5596    252    260            Р           2606    35699    posts fk_posts_user 
   FK CONSTRAINT     „   ALTER TABLE ONLY public.posts
    ADD CONSTRAINT fk_posts_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
 =   ALTER TABLE ONLY public.posts DROP CONSTRAINT fk_posts_user;
       public          postgres    false    252    310    5596            Г           2606    35522 *   game_answers game_answers_question_id_fkey 
   FK CONSTRAINT     Ё   ALTER TABLE ONLY public.game_answers
    ADD CONSTRAINT game_answers_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.game_questions(id) ON DELETE CASCADE;
 T   ALTER TABLE ONLY public.game_answers DROP CONSTRAINT game_answers_question_id_fkey;
       public          postgres    false    296    5676    288            Д           2606    35527 1   game_answers game_answers_selected_option_id_fkey 
   FK CONSTRAINT     ѕ   ALTER TABLE ONLY public.game_answers
    ADD CONSTRAINT game_answers_selected_option_id_fkey FOREIGN KEY (selected_option_id) REFERENCES public.game_question_options(id) ON DELETE SET NULL;
 [   ALTER TABLE ONLY public.game_answers DROP CONSTRAINT game_answers_selected_option_id_fkey;
       public          postgres    false    296    290    5679            Е           2606    35517 )   game_answers game_answers_session_id_fkey 
   FK CONSTRAINT     Ґ   ALTER TABLE ONLY public.game_answers
    ADD CONSTRAINT game_answers_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.game_sessions(id) ON DELETE CASCADE;
 S   ALTER TABLE ONLY public.game_answers DROP CONSTRAINT game_answers_session_id_fkey;
       public          postgres    false    292    5683    296            К           2606    35611 6   game_menu_cart_items game_menu_cart_items_cart_id_fkey 
   FK CONSTRAINT     ±   ALTER TABLE ONLY public.game_menu_cart_items
    ADD CONSTRAINT game_menu_cart_items_cart_id_fkey FOREIGN KEY (cart_id) REFERENCES public.game_menu_carts(id) ON DELETE CASCADE;
 `   ALTER TABLE ONLY public.game_menu_cart_items DROP CONSTRAINT game_menu_cart_items_cart_id_fkey;
       public          postgres    false    304    5706    302            Л           2606    35616 6   game_menu_cart_items game_menu_cart_items_node_id_fkey 
   FK CONSTRAINT     ±   ALTER TABLE ONLY public.game_menu_cart_items
    ADD CONSTRAINT game_menu_cart_items_node_id_fkey FOREIGN KEY (node_id) REFERENCES public.game_menu_nodes(id) ON DELETE CASCADE;
 `   ALTER TABLE ONLY public.game_menu_cart_items DROP CONSTRAINT game_menu_cart_items_node_id_fkey;
       public          postgres    false    304    300    5701            И           2606    35590 +   game_menu_carts game_menu_carts_bot_id_fkey 
   FK CONSTRAINT     џ   ALTER TABLE ONLY public.game_menu_carts
    ADD CONSTRAINT game_menu_carts_bot_id_fkey FOREIGN KEY (bot_id) REFERENCES public.game_bots(id) ON DELETE CASCADE;
 U   ALTER TABLE ONLY public.game_menu_carts DROP CONSTRAINT game_menu_carts_bot_id_fkey;
       public          postgres    false    282    5666    302            Й           2606    35595 ,   game_menu_carts game_menu_carts_mode_id_fkey 
   FK CONSTRAINT     ў   ALTER TABLE ONLY public.game_menu_carts
    ADD CONSTRAINT game_menu_carts_mode_id_fkey FOREIGN KEY (mode_id) REFERENCES public.game_modes(id) ON DELETE CASCADE;
 V   ALTER TABLE ONLY public.game_menu_carts DROP CONSTRAINT game_menu_carts_mode_id_fkey;
       public          postgres    false    5673    286    302            Ж           2606    35568 ,   game_menu_nodes game_menu_nodes_mode_id_fkey 
   FK CONSTRAINT     ў   ALTER TABLE ONLY public.game_menu_nodes
    ADD CONSTRAINT game_menu_nodes_mode_id_fkey FOREIGN KEY (mode_id) REFERENCES public.game_modes(id) ON DELETE CASCADE;
 V   ALTER TABLE ONLY public.game_menu_nodes DROP CONSTRAINT game_menu_nodes_mode_id_fkey;
       public          postgres    false    286    300    5673            З           2606    35573 .   game_menu_nodes game_menu_nodes_parent_id_fkey 
   FK CONSTRAINT     «   ALTER TABLE ONLY public.game_menu_nodes
    ADD CONSTRAINT game_menu_nodes_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.game_menu_nodes(id) ON DELETE CASCADE;
 X   ALTER TABLE ONLY public.game_menu_nodes DROP CONSTRAINT game_menu_nodes_parent_id_fkey;
       public          postgres    false    5701    300    300            О           2606    35662 8   game_menu_order_items game_menu_order_items_node_id_fkey 
   FK CONSTRAINT     ґ   ALTER TABLE ONLY public.game_menu_order_items
    ADD CONSTRAINT game_menu_order_items_node_id_fkey FOREIGN KEY (node_id) REFERENCES public.game_menu_nodes(id) ON DELETE SET NULL;
 b   ALTER TABLE ONLY public.game_menu_order_items DROP CONSTRAINT game_menu_order_items_node_id_fkey;
       public          postgres    false    300    308    5701            П           2606    35657 9   game_menu_order_items game_menu_order_items_order_id_fkey 
   FK CONSTRAINT     ¶   ALTER TABLE ONLY public.game_menu_order_items
    ADD CONSTRAINT game_menu_order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.game_menu_orders(id) ON DELETE CASCADE;
 c   ALTER TABLE ONLY public.game_menu_order_items DROP CONSTRAINT game_menu_order_items_order_id_fkey;
       public          postgres    false    308    5714    306            М           2606    35635 -   game_menu_orders game_menu_orders_bot_id_fkey 
   FK CONSTRAINT     ў   ALTER TABLE ONLY public.game_menu_orders
    ADD CONSTRAINT game_menu_orders_bot_id_fkey FOREIGN KEY (bot_id) REFERENCES public.game_bots(id) ON DELETE RESTRICT;
 W   ALTER TABLE ONLY public.game_menu_orders DROP CONSTRAINT game_menu_orders_bot_id_fkey;
       public          postgres    false    5666    306    282            Н           2606    35640 .   game_menu_orders game_menu_orders_mode_id_fkey 
   FK CONSTRAINT     Ґ   ALTER TABLE ONLY public.game_menu_orders
    ADD CONSTRAINT game_menu_orders_mode_id_fkey FOREIGN KEY (mode_id) REFERENCES public.game_modes(id) ON DELETE RESTRICT;
 X   ALTER TABLE ONLY public.game_menu_orders DROP CONSTRAINT game_menu_orders_mode_id_fkey;
       public          postgres    false    286    5673    306            ј           2606    35423 !   game_modes game_modes_bot_id_fkey 
   FK CONSTRAINT     –   ALTER TABLE ONLY public.game_modes
    ADD CONSTRAINT game_modes_bot_id_fkey FOREIGN KEY (bot_id) REFERENCES public.game_bots(id) ON DELETE RESTRICT;
 K   ALTER TABLE ONLY public.game_modes DROP CONSTRAINT game_modes_bot_id_fkey;
       public          postgres    false    282    286    5666            »           2606    35405 %   game_players game_players_bot_id_fkey 
   FK CONSTRAINT     ™   ALTER TABLE ONLY public.game_players
    ADD CONSTRAINT game_players_bot_id_fkey FOREIGN KEY (bot_id) REFERENCES public.game_bots(id) ON DELETE CASCADE;
 O   ALTER TABLE ONLY public.game_players DROP CONSTRAINT game_players_bot_id_fkey;
       public          postgres    false    5666    282    284            ѕ           2606    35457 <   game_question_options game_question_options_question_id_fkey 
   FK CONSTRAINT     є   ALTER TABLE ONLY public.game_question_options
    ADD CONSTRAINT game_question_options_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.game_questions(id) ON DELETE CASCADE;
 f   ALTER TABLE ONLY public.game_question_options DROP CONSTRAINT game_question_options_question_id_fkey;
       public          postgres    false    5676    290    288            Ѕ           2606    35439 *   game_questions game_questions_mode_id_fkey 
   FK CONSTRAINT         ALTER TABLE ONLY public.game_questions
    ADD CONSTRAINT game_questions_mode_id_fkey FOREIGN KEY (mode_id) REFERENCES public.game_modes(id) ON DELETE CASCADE;
 T   ALTER TABLE ONLY public.game_questions DROP CONSTRAINT game_questions_mode_id_fkey;
       public          postgres    false    286    288    5673            Б           2606    35502 >   game_session_questions game_session_questions_question_id_fkey 
   FK CONSTRAINT     ј   ALTER TABLE ONLY public.game_session_questions
    ADD CONSTRAINT game_session_questions_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.game_questions(id) ON DELETE CASCADE;
 h   ALTER TABLE ONLY public.game_session_questions DROP CONSTRAINT game_session_questions_question_id_fkey;
       public          postgres    false    294    5676    288            В           2606    35497 =   game_session_questions game_session_questions_session_id_fkey 
   FK CONSTRAINT     №   ALTER TABLE ONLY public.game_session_questions
    ADD CONSTRAINT game_session_questions_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.game_sessions(id) ON DELETE CASCADE;
 g   ALTER TABLE ONLY public.game_session_questions DROP CONSTRAINT game_session_questions_session_id_fkey;
       public          postgres    false    5683    294    292            ї           2606    35482 (   game_sessions game_sessions_mode_id_fkey 
   FK CONSTRAINT     ћ   ALTER TABLE ONLY public.game_sessions
    ADD CONSTRAINT game_sessions_mode_id_fkey FOREIGN KEY (mode_id) REFERENCES public.game_modes(id) ON DELETE CASCADE;
 R   ALTER TABLE ONLY public.game_sessions DROP CONSTRAINT game_sessions_mode_id_fkey;
       public          postgres    false    286    5673    292            А           2606    35477 *   game_sessions game_sessions_player_id_fkey 
   FK CONSTRAINT     ¤   ALTER TABLE ONLY public.game_sessions
    ADD CONSTRAINT game_sessions_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.game_players(id) ON DELETE CASCADE;
 T   ALTER TABLE ONLY public.game_sessions DROP CONSTRAINT game_sessions_player_id_fkey;
       public          postgres    false    5670    284    292            ·           2606    35255 )   group_members group_members_group_id_fkey 
   FK CONSTRAINT     њ   ALTER TABLE ONLY public.group_members
    ADD CONSTRAINT group_members_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE CASCADE;
 S   ALTER TABLE ONLY public.group_members DROP CONSTRAINT group_members_group_id_fkey;
       public          postgres    false    268    264    5626            ё           2606    35261 (   group_members group_members_user_id_fkey 
   FK CONSTRAINT     ™   ALTER TABLE ONLY public.group_members
    ADD CONSTRAINT group_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
 R   ALTER TABLE ONLY public.group_members DROP CONSTRAINT group_members_user_id_fkey;
       public          postgres    false    252    268    5596            ¶           2606    35194 %   groups groups_created_by_user_id_fkey 
   FK CONSTRAINT     ў   ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;
 O   ALTER TABLE ONLY public.groups DROP CONSTRAINT groups_created_by_user_id_fkey;
       public          postgres    false    264    5596    252            І           2606    35133 8   password_reset_tokens password_reset_tokens_user_id_fkey 
   FK CONSTRAINT     ©   ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
 b   ALTER TABLE ONLY public.password_reset_tokens DROP CONSTRAINT password_reset_tokens_user_id_fkey;
       public          postgres    false    258    5596    252            ±           2606    35104 *   refresh_tokens refresh_tokens_user_id_fkey 
   FK CONSTRAINT     ›   ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
 T   ALTER TABLE ONLY public.refresh_tokens DROP CONSTRAINT refresh_tokens_user_id_fkey;
       public          postgres    false    254    252    5596            Ц           2606    35984 -   smm_automations smm_automations_brand_id_fkey 
   FK CONSTRAINT     ¤   ALTER TABLE ONLY public.smm_automations
    ADD CONSTRAINT smm_automations_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.smm_brands(id) ON DELETE CASCADE;
 W   ALTER TABLE ONLY public.smm_automations DROP CONSTRAINT smm_automations_brand_id_fkey;
       public          postgres    false    339    5764    331            Т           2606    35915 3   smm_brand_channels smm_brand_channels_brand_id_fkey 
   FK CONSTRAINT     Є   ALTER TABLE ONLY public.smm_brand_channels
    ADD CONSTRAINT smm_brand_channels_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.smm_brands(id) ON DELETE CASCADE;
 ]   ALTER TABLE ONLY public.smm_brand_channels DROP CONSTRAINT smm_brand_channels_brand_id_fkey;
       public          postgres    false    333    331    5764            С           2606    35883 #   smm_brands smm_brands_group_id_fkey 
   FK CONSTRAINT     —   ALTER TABLE ONLY public.smm_brands
    ADD CONSTRAINT smm_brands_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE SET NULL;
 M   ALTER TABLE ONLY public.smm_brands DROP CONSTRAINT smm_brands_group_id_fkey;
       public          postgres    false    264    5626    331            Ш           2606    36027 9   smm_channel_counters smm_channel_counters_channel_id_fkey 
   FK CONSTRAINT     є   ALTER TABLE ONLY public.smm_channel_counters
    ADD CONSTRAINT smm_channel_counters_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.smm_brand_channels(id) ON DELETE CASCADE;
 c   ALTER TABLE ONLY public.smm_channel_counters DROP CONSTRAINT smm_channel_counters_channel_id_fkey;
       public          postgres    false    333    343    5771            Ъ           2606    36117 I   smm_channel_metric_snapshots smm_channel_metric_snapshots_channel_id_fkey 
   FK CONSTRAINT     К   ALTER TABLE ONLY public.smm_channel_metric_snapshots
    ADD CONSTRAINT smm_channel_metric_snapshots_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.smm_brand_channels(id) ON DELETE CASCADE;
 s   ALTER TABLE ONLY public.smm_channel_metric_snapshots DROP CONSTRAINT smm_channel_metric_snapshots_channel_id_fkey;
       public          postgres    false    333    5771    352            Ч           2606    36003 A   smm_competitor_snapshots smm_competitor_snapshots_channel_id_fkey 
   FK CONSTRAINT     В   ALTER TABLE ONLY public.smm_competitor_snapshots
    ADD CONSTRAINT smm_competitor_snapshots_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.smm_brand_channels(id) ON DELETE CASCADE;
 k   ALTER TABLE ONLY public.smm_competitor_snapshots DROP CONSTRAINT smm_competitor_snapshots_channel_id_fkey;
       public          postgres    false    333    5771    341            У           2606    35937 -   smm_inbox_items smm_inbox_items_brand_id_fkey 
   FK CONSTRAINT     Ґ   ALTER TABLE ONLY public.smm_inbox_items
    ADD CONSTRAINT smm_inbox_items_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.smm_brands(id) ON DELETE SET NULL;
 W   ALTER TABLE ONLY public.smm_inbox_items DROP CONSTRAINT smm_inbox_items_brand_id_fkey;
       public          postgres    false    5764    335    331            Ф           2606    35942 /   smm_inbox_items smm_inbox_items_channel_id_fkey 
   FK CONSTRAINT     ±   ALTER TABLE ONLY public.smm_inbox_items
    ADD CONSTRAINT smm_inbox_items_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.smm_brand_channels(id) ON DELETE SET NULL;
 Y   ALTER TABLE ONLY public.smm_inbox_items DROP CONSTRAINT smm_inbox_items_channel_id_fkey;
       public          postgres    false    335    5771    333            Щ           2606    36087 5   smm_message_events smm_message_events_channel_id_fkey 
   FK CONSTRAINT     ·   ALTER TABLE ONLY public.smm_message_events
    ADD CONSTRAINT smm_message_events_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.smm_brand_channels(id) ON DELETE SET NULL;
 _   ALTER TABLE ONLY public.smm_message_events DROP CONSTRAINT smm_message_events_channel_id_fkey;
       public          postgres    false    5771    348    333            Х           2606    35964 /   smm_publish_jobs smm_publish_jobs_brand_id_fkey 
   FK CONSTRAINT     §   ALTER TABLE ONLY public.smm_publish_jobs
    ADD CONSTRAINT smm_publish_jobs_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.smm_brands(id) ON DELETE SET NULL;
 Y   ALTER TABLE ONLY public.smm_publish_jobs DROP CONSTRAINT smm_publish_jobs_brand_id_fkey;
       public          postgres    false    5764    337    331            ґ           2606    35168 I   user_role_tariff_history user_role_tariff_history_changed_by_user_id_fkey 
   FK CONSTRAINT     Ж   ALTER TABLE ONLY public.user_role_tariff_history
    ADD CONSTRAINT user_role_tariff_history_changed_by_user_id_fkey FOREIGN KEY (changed_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;
 s   ALTER TABLE ONLY public.user_role_tariff_history DROP CONSTRAINT user_role_tariff_history_changed_by_user_id_fkey;
       public          postgres    false    252    262    5596            µ           2606    35163 >   user_role_tariff_history user_role_tariff_history_user_id_fkey 
   FK CONSTRAINT     Ї   ALTER TABLE ONLY public.user_role_tariff_history
    ADD CONSTRAINT user_role_tariff_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
 h   ALTER TABLE ONLY public.user_role_tariff_history DROP CONSTRAINT user_role_tariff_history_user_id_fkey;
       public          postgres    false    5596    252    262            °           2606    34730 1   wp_collect_sites wp_collect_sites_profile_id_fkey 
   FK CONSTRAINT     І   ALTER TABLE ONLY public.wp_collect_sites
    ADD CONSTRAINT wp_collect_sites_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES public.wp_collect_profile(id) ON DELETE CASCADE;
 [   ALTER TABLE ONLY public.wp_collect_sites DROP CONSTRAINT wp_collect_sites_profile_id_fkey;
       public          postgres    false    5520    220    218            §   o   xњЙKѓ  А5њ‚јm«бQEе,&„HHс”•соўЫ$Hтж’6v
іО«5»{¤Дi‰ѓgбН`7)x“П1Ю6эЌЛппlС№аIІв}%ГNµЅjdЌШH9јш‡Ћ5ҐфИы!¤      Х   
   xњ‹Сгвв Е ©      Ґ   
   xњ‹Сгвв Е ©      “   
   xњ‹Сгвв Е ©      Н   
   xњ‹Сгвв Е ©      Л   
   xњ‹Сгвв Е ©      С   
   xњ‹Сгвв Е ©      П   
   xњ‹Сгвв Е ©      ѓ   
   xњ‹Сгвв Е ©      Ѓ   
   xњ‹Сгвв Е ©      —   И   xњEЉНn‚@FЧро
дОџЉ»
п„Рj3%nиќЫ’4­АУ—Ж…«пЛ9‡xДkiЯRгћќДbD’;ьЖПѓ01.°нtЛ(њ"bh9hzmстХg±„Fo®Уw•"¶VэйэЈjUuЇtµЉ~РЭ\ҐннїПЗ3Л3m§}€СУnc\В¬’=Уi=m45ї/…e»ЋO
Я&ЩЮЈ@¬Кf°\±|мЃйЊА‡Л\LЦ?†ѕпяг¤@r      Щ   
   xњ‹Сгвв Е ©      »   
   xњ‹Сгвв Е ©      ­   
   xњ‹Сгвв Е ©      Ѕ   
   xњ‹Сгвв Е ©      Г   
   xњ‹Сгвв Е ©      Б   
   xњ‹Сгвв Е ©      ї   
   xњ‹Сгвв Е ©      З   
   xњ‹Сгвв Е ©      Е   
   xњ‹Сгвв Е ©      ±   Q   xњ3дLIННзј0еВЦ{.мУЅШ dl»°гВОNcО?N##3]]##C+S+s=K3KcmcОВТМ*®=... j|      Ї   
   xњ‹Сгвв Е ©      µ   
   xњ‹Сгвв Е ©      і   
   xњ‹Сгвв Е ©      №   
   xњ‹Сгвв Е ©      ·   
   xњ‹Сгвв Е ©      џ   
   xњ‹Сгвв Е ©      ›   
   xњ‹Сгвв Е ©      Ь   
   xњ‹Сгвв Е ©      ‡   
   xњ‹Сгвв Е ©      …   
   xњ‹Сгвв Е ©      Ч   ю   xњ=ЏMNГ0…ЧЙ)¬°¬’:NгУ”K°DЄ¬Дэ‘B,W‚dС-'‰Є"~Т+ЊoT›iЮ›yЯДЮЌЁЕZс;LЈy‚ЮЎ3{МCр#њ\і†фЦтGибЫYђЭiбd‡ц|є1ІJзК_ОЋ&YNhљзx6K"4зhЈДЄ¦ъ7эљпф¦€tЇkQҐ¬ҐbуtЕЇґxРa%J©ёЮК†нљJЁzЫ€`ЇИВ–Ўя‡uсжЩґ?PЋroЕїWзSѕ€јШУлҐ‹]–ІБ„†ш2$ВbКe)NУl‚я6т}я‰ЎЏb      •   
   xњ‹Сгвв Е ©      Ј   
   xњ‹Сгвв Е ©      Й   
   xњ‹Сгвв Е ©      ‘   q  xњЕР]OВ0аkшЮ–цlw2	vТ)_µ,&КЗє@Щцл-`ў/ј0св$Н{љ7yNЅ‚+уВЏ¦m©”O‡%ЕЃў[єкйQ›&Б=Я5ф',ЃТ„ЖлјгщЕтTїUhтTљ]Ґ34НS&3ћй)'ћ.ЛТh¦ЛШ@ZAЙ‹‡АЉѓ
Et8vеТ|$&+Gеўk47ЩNјЏ­ёчэ\I9[OЖ­\ ЫЋXі›0ҐЅ;Ї)YV Ѓ]CN
Ь+д6€Э@ж52?cёВpЋ
LpЭ!z[ЕЦ_ЁGOЅЭдЙъҐє«•тRm±[Zѓ“:”щHЄЪћує®DНХDЃdTgыШттцjґ&ЙW5¶VГ DlG5 PZMu©fZќЂVюC/јЪэVNЕ!с6Ыю2Мўv,вM9eуhЗgxЬЬmї©Э†e6°}Ў8З†KђѓќЈъЩЁV«пиЧд‘      У      xњ•ЅMОm;ЋЪО…ыю°$Q9Џ z·ћЃ2lП&ѓБќЇх:·‘'—ЪKяDЫ?юзяъПяшпяыязяЄыЗюїяшчяцЏпэллї~зїцю_ЪчПiягпЮ3Gяѕсo]GО~цч}ЧЪдшЗьзяшяэ?юЏ#щoяїИyъ97ђц"sёМЮfkЃњ:raµcчѓЯ№фХ№ѕoЪ	д~‘«µЮ;~зС‘«µіждХWдj{ЬИцЅЌеN[џЁ5z°^»ЪхєЖь?µЌ©±аэ5тб]¬ЧWk№Ю©ЇР5§х
иz‘л=Ц,чF=JнџЯ‡_я—­qБ]{ґ‘Rп‹ФXрЭ
[УХідИBЫЧV"›ѕ\ Ч5лёв]ХHЂЋєч—єL=JнXoуMЕGк¦/РЭVЛЬUҐh,ёUП’CЬчи8}лtЏ}ZWх ±ас­“RО’aБcћ…/<>}БЂохЭ†+7TЕ(|'NДx8L0R~Sп„тЄ}+иѕ­ќ\ЇЄ ЌхN›\рГa‚ќjуё>T5q=n¦FюЦЕЧ–5nлГa‚©j»П›їUµr=іЫЕЕ±Н+ЧцќШ{8K°TнЊ‘ЫjЄ‘+и9ѓћЂ=h&№v?їкЂ>&ЄvЧM-lЄ•+иэЋыKЂ>h&X№юЌcР¦¦SХЫwТў›nеzmЮфLЧL
V®·}>lОФ4М_п6т4MЭО%ФM«ЫH@uХФ`зъиЌPэ45«оєяГgљєќKиЅwдiљєjj°sЭl§.ќъij0VЭЈ“ФэS·sќ,ф3qљ¦®љм\_о«е‚NЊU_юjxйv. ѕ`»-OУТuSѓќsб+фб4БZхнШЊЊtCP_рћ-µДТuSѓЎу­9i­ЦГi‚µr[5;вТ
]@§{€s-млzРM0tэћ¶rsN¬ХрЌMЭґtCP_р8'чu?и&єСЪ%фб4Б\Ќv,“[·tхЇЭzJ}РM°tЈЫМg?њ&«›іuKP_р=ѓџйA7БТ
ыҐoэ4u«aыЛX{л–. УmЋbЬњ­л¦K7¦ыаёЇG?Mжj¬ЮrБG·tхПћ‰Ј«¦C7Цi?хи‡©ГZЌЅ&ЄnиклЭ‡зриЄ©ГРЌунґМG?L†n7pЏnи:]и—t¤Џ®љ:Эp1Чыp–`змkгК]ЭОuШ№бж•P]3uШ9‹¤#~к}8L°sЦцк	Хн\‡ќж_	fгкљ©ГОYч°,Ґ>&Ш9уpcаф_ЭОuШ9ї­3“(чA3БО™
;	}8L°sжQ¬Ы№;зїФ2•ч=h&Ш9[-УРоOлPШ9сїM±єЎл0tжRк¦ц=('X:Ыk¤Уѕ‡Sg¬oю^ЭЦuШ:лЗЭДД>и';sG$CШцйgjАЪЩЭ»«›»sg~чHЧQцn~¶щќеlёcaрЬіm3У¦M·xП–л©<MWS6o¶іекзjАиНѕЌ{Фt«7`хь\НЖмї®©МЮГ2ТjrRЬ±°{УMЇ~У
ЯЂбі‰•ДкКjАтM›LЋґ‡јшЂн›У„|иєс0~УOU¦PэЂЅИЌ5ЇтђЫCr|дЈЫоgsНєО0bsЯ/3$н!З=V>цН•щ«ЦфlСјыз]xHUЈyЭL]7о>LКъён!г<т=«щ]Иo5о/мВкЯаSШГеі”…јEгбBіЇ1оҐX}‡,—\СQГэґуr3xщ~§пђ5ѕВЭфRљй7Б aЧІЛј‡l¬х|LыѕЏrх›`Р’k{8C¬ѕG-№Ћ»ЇyЄLї	MзNОҐ§тђ5ЛЧ8>&Oэt•З·m¤®zHpZ> ґИz'Vї]еЋF+мГAWн>Эь&цб&@Wmw`©«ТЌ]µні,1hлб&@Wm?МьЅYCѓ®ЪsпЛ·м‡› ]µ—ЌLфґ‡дџЭ|Р»#ЌЪzё	РV;юр[й{4Ў­цо0$Vї	Ъjџіш­Rqіеѓањ™n[їЪк|ќБr{ИЁMh«уќОoХежjЈ]wМм°n ЛЦ`s0ВH‚ХOЅCu„дй!«IdыpHћ|Кt¬ъ­wиЋјжў5лІ8ы-ћtОдЗЫЪ#$ыV}фОd#pH>gо’ь°S’пљґh]6Г »деn°QІьћєCѓёдр”U6 !ЧUЇE?lФ…Ь~.O€l‡Ѓ
Бc<!k‰ЎlявЎ±хї>]јЕ2А
аЅ{§ћЯbpа°;Kі$‹QVЂGЂG‹ш.БGwl ЏuYT¶›wspџvҐ9>#XМЃx|ѕ»KІЏ
рръЬЭўд.¦†| о~XМСшмОшa‘ШФOб„ќyyґчТбЂќуYэдҐ0Г»џ[ФC°~Амєqъш“·~АмљЫфџO?`УШшkg±.ГБъ›+Аn—з,Йъ›асUZлЁ5“…Џ¶ЛВQл;ЉлЧрр'«UҐц х29jЕCGЩBЂm4Ж?G­>и(!°Ј­$«ПщцЕТЖхUѕгiЭБы›ќGЫПљ¶„юо9UЏВE›_kЫ
¬/Д|¶M#Ч›|;*ћг№гЫщ$Ъ›|;
ђсфpYУ«>щpиsFвG_fдo§П©їрјрёі;y+єюШ2р№ж¬¤zЧџ=>ЦЬџСЗъДА·љз—ьъCАА§Љ‚К|©qe c
	щpџXЕlzbЬђ_жV•)=AmHPЇµ©0MПтДЛ-sKяT†OеЄ}СХT>Ж›Ћн»твЄїЗС±у”ЧҐє{Њылцe %—WЬзвX}©Щн
ЭЬЩkЈвхVшµЫ\|6йr
kEP{®УЛШbш•ю±}{Яaе\‹1эг/2ч'Yї’п:•‚Qл9и\б±uжQЋ~%Ш%џf‹Й®ҐVfxBІљtЦ°‡dЏ(NЃ¶jAІыЗ­Аb¤њађl»1М^j­DЂ7$OW}Њѓ®)'8$ЇџП¶ФЄ‡ HЮѓ) uЕP9±!шф:"jсB`/дЮ€#~ё7Япkїd›ѕQ€–мс=зХЇЎїnqҐкфЌ‚—лБИbq­ѓхkћ—ѓЗИ†ЗкеL¶h4#Xї
мЪЎВЯкЛ~`ЎїоЬуN‚хKСЎї"{фХ·~Ш(иЇ»«ёЧнЈ~):фЧuф‹п6
ъЛuИdЧЩV»Зlн/ћЂ~’vКхWЂчб…ЬjX‚CІЗuІХoж4<_Џ·ЪР•ађЬ=‚bЂЇѕ[3!аYM‰[mНJpHcWH}№f6ЕБs–ҐfА’з7л:«oЧQhщAттпЕ\ЊљOpHvG™жu«ЇЧn)щn>6ЁрД†аЅЇкуuЂ;џхУ»j<Б!щО[I х	;А#$·o¬Џ;ҐfАм’[kЯ)рГN$7чаёSj<Б!№»¦зҐRџ±<!9ЄyќХx‚CІхЭь°UPamцСл7?ЬЁ°6+ЬкKv`ЎБЪZр·ЪЄ“Шђ»ЧвГРVіЦОьJЁ=7	Й·U‡уVџі9§ІЇjуL‚]rяЊ-Ѓa6d°AЃuwТW-[їжaзЩ•LЦ·К АъёU^µХv–‡dWЪҐ
ФGm¦±јz•wlµ/%Б!9ЪИJІѕU
Цo[eЁФ“»дб]>…ъ°НєѓGыш6ґХN‘‡d›іЊЌъґ`h°1}§x%Х–Џ‡дef%щa« БЖ¶џЈ®цn$8$яП‡xЯ ВFг¬6a$8$ЯіаCјoРaцќ^jHm§H°K¶уy%в}ѓіn·Хo~ёРaжо_Ѕ,=Ды:МOИшэfэbLи0іYµmы!ЮџРa6З)У®¶*$8$ЇvOЃх­љРa®тG}mµз Б!yя*вчCД?ЎГмDбБъЕРavG%ВцCД?ЎГfр(рELнH°шЮЄусOи°ЩЦGssФZю‡дЮО(Й[6Эd|хьшp1 ГьtV-вy€щ'tШґ5л-N­«OpHv(лдОCМ?ЎГfФ_l‚.tXT@[=№>ltШ<Якµм‡‹6П1Юз#Зь a	Й—Э®ЋUп°.x}цХы¶тѓNҐшІ“ЩБкЅ 8$·ыќ«;^”ђЬ§н«чађ<Мк±WщAp’-‚)‚Х{pHћНX0х¶ C[АnЎ…«?^/wї•[ћъгҐбсТѓ°Г›©ї^^/ЭQu/9“ґълҐбх2:
кUєuФ~у{Е®zхиd:щFyЌъ«^ПнЧКЌy‘kоg±+аЎkwўыx їJСлkЖ±єю­fiЏ№±жЁg¤\съЬо,ЋТтъqћ8Оw4cВOu5k^mС±hЮMў·іnu@эeЙДµ ­JмCU2*ЗПћ‡Пћэ»IчжV|2эtфл›•w‘Є©ЮmBcЙЗNюЬ‡Ю$|‹Шћ6ькZ#лCосГ‘?Wх‹лkц«АFяцРЕ›¤oЧµ+lЇ^@Ш<‰Ќх!ЄGќШXіыx%W=Vќјo·hx<–—њР)чzKW]сДЖ’mќ<‘]nенд~»nц3сУ?µ^"±+’хэ#VХVќДqЧэ¤F¬z¬:йЯоv-I¬Z§‘X_і‡йmtХэOl¬Щќф»ЬЛЫЙ wѓЮ‰kV­`bЧ_уїKЪХА!±±f_фўЬ‡s•д8Я,hSЌ`BWdКO:І]f¶vD^89‰}8VIЏУЈ;.±ЄL¬Їyu>
t™ЭШXsФYыp¬Vr№Ш<VjЕ5±ѕжsЉQ&ёvЂыиKMЧеVЮ68ЗОYWA-ф&vэщ‰йяv™дШXіGЈiЌєЬКЫБФI_NЄхеД® УbЄ¤ЛD—АЖљчйv№
ёѓО±gОґd]-k'ЦЧј.ЫqхN$`cНn©rдв^ёА.c9jЧН`ѓtгkЖп¬«« •›щ"™k–ЫЏ;Ёбf<HТЛ‰ц'yН0ѓЈEуAbu}…:X—»Ш%ТеЦеv8ЗцYЊЇC7ѓёюоmњM¬®Ї‚Z.ІИФеѕ    зN~ё6fЇ%лV°Б
ЋХO}*]]№њЛµп3nпГ±‚ф™ЌшС«%/VpTїЮ©h¬xzT“_Yо¶од€kуР&ЁЕу„®?у‹0№d]W5Ш@?Њ_¶рw№Q»KЬюЊ›«Vнлk}e`—й/ЃЌ5пµйЙMЮЅ€вЋ
Ю!µYЂX_уґ™yњ.3`k>‡¤Ё]nпЕwwo”«ЫАhЫПSк9™X_s°.іїAn/п¤‹лх|Ч§nL Э=т}ёЛ4АЖ’э<ЧйЗЄг¬УњЁ
eД®їЩ.s@]fВ6Ц©§”+wµчвЊs7”ЉЪИF¬ЇЩх+Ї‘L†	l¬Щs|]о€пЕзq Й±Хю9bW0»фмbл2&°±жeџ«џ«¤Ћл;8«ЫА8Og–ѕЛ”АЖљчeЛ_—;с;йгъ±IЧYнN"vEГт—oч]fЕ6Ц|М»ЬЕЯЙ ЧЇСMQ{ў]и&-±є¶к°‚эЮНП,§Щ{qИE€B¬n;¬аІХі~±ЛФАъљG‹RbЋU6џхhM¬n;¬аZ—НЖ]fЗ6Цјш©rд4{'‘њ{їЭHЗЇ[Б+ё®Gy®d†L`cНfуPоГ№‚і‘tПЭ`}Н0ѓЫЌ/“m2I&°±ж№п \э\%‘ЬћоЇnМањѕСeћL@cЙ»b99ЛЮI#7¶ы№b™нШл±:sr¦ј“
ОЅтЪv™ґШђ{пќ\іѕ»¤sы¬еЊћ.sOлr­M~HY'%›EЯnВђ)$Ѓ
№Q
›іТОЩtj#jй«ЯАНnюЎ3Н>RЗЩ°й#NЉђ©Ѓ
№swЁxHяf·«­Сшќe:F`Cоєds9Ьм”µ}x6†Z4’ШђќЈД>мQ6$ЯЮ9D¦EvЂЪpЄoQ6иОПЎo]ћ¬Qt0{“4јuyКEєЧЇ­(UіP¬,n‹«h©OЖlGмnОщ
¬у84…wЄQM}DeS`wќм(	Vџ3ЩЧзаЮHЌн`ќИЎЃ($j«0RMmІ;Ґя­йЂµjЋ‘
&=€мЦЇГDg
`
‰Gцк6SУnмуио;мyёl5ЖV
ыFWA»МLђµК=ъЬЄ>gЛМYnЬѓўцy«~)+†Gј/oХAdСЇѓЗw«ћSхФX·ла№ѕ_ЩљNтЃ*Йу*ГТ©B>P…шЄ‹жЁ№X=ж`яЦdД;jч;Амi–ЋЪэ†ь »Вяq«ЁГ4:&bП€;[ЬЄ+7Ё |МVL18‹/цrѓ
кЗZјЃ
*@Я4Э3FІeЇНвYqu,’ЫMЬўЇЁ'’з›UЩ­'Z7x
X‹)D¦Дxњ`§[ФAzєtѓХББлыX»ЦeZLЂCтЪ©Ћф¤з'„ѓ]sІЬ§ЛД ‡д3«љSП]nФН9шZїх›uzє(њ;1}sь~уГVYH^џYэf™ађЂ”,з7jШ\Дг]fЗ6‡вЗ–“Ѓ…hvч¬0]жЗ8$Џ`O$шa§vJѕ5g—2Й~DXгЁ'ж6ЄВXeкtК™ ‡д№O+Й[u!9HPйсКµЁ ‡дuXЄ'Й*ґNђґ|«~Іz- БЗ­wJNuФYќ`ћ]ИeЎ ‡д(`x!'¬ЄҐО_0/т{ЙµќАЋА®U$MrЦй дЙБ­‰ЙќмDЃ]&zyN±:иЋ6xП"pµ­ѓоhw8ЪAV…µZдEJ€$х5Ьb«еVduисюR-[&LЛ®жћ4>Цэм?{пsЄ3O¦LЛжвоЕ7к7«П‘lvp;Е)ѕХ‡Aцшц ґYµНjj’-n#:цoq«Ю»ФЖ_ыѕкXШЄыЖF3ч>Fulй'lВПn6ЊcьГл`шЩmЌэ«.Чэм~цlЈьмЈІLбaаX5НФЬJЗиС OЗ2ћR“+s@мЯ‰†Ј&W:frш^Ј/sеіќ±ЕЋ_>^
u§Z]СoБжЎ’s2=кШhЮґДкPPQЛя1Ґ«?
<ќыэR~ъѓМАѓМЌб4­тУKоџЫЁ]a‰<O4#‹ГЕgq}Лі=38ё19ыыЃuВёрпЬO+В8yжeєи¶{™|;2MJЖЫСpu‹?иЁDб	Ћn­µжO‰€Ћ•€ѓЭІэАj/!А!щt+оW™'%5ђѓЈ› $?фўнsЭ[dЯGжIIхХЬ‡Ъ_х©Lб	vЙ»­Yы,у¤¤оsрїѕ—JћШ<ЪшЉпцa§РхЈТyќЏКћађЈ«JІѕS
]џ;тPe+ф{СРц№Ч·+‰%Ґ$MoЂзb*йЁ)Љ‡д}~­Бy(” юнавSS	ЙwмТ2QJ·рэКK?jЉ"Бау3л2QJІ·hfхµХE‚CrtAsЩ2QJж[P8юъdХE‚Cт,рp‡BЫьgwSХOЌѓ»[еайабћcµbй·К$ЏS^оГV98$Ыщип^™УЅІ!Щ}ЁXЯ*Ыђ<oќ°+sЪ У6$ЧђҐ+3Ъ rwMЃwрГF]И=?r«+3Ъ ’ГЩ­eл5ѓєНЅ«ю•m ћѕх€yeFђц†дЁ oлЧb6HvЧkЧІх­љ’З,г|eFЂCІµЯлЃМhѓЦжђl»ЁЇМhpHћю‡Є@fґAѓrH^Ј­jqФЇ…ѓCтrД&3Ъ Н8$пюэ–­_Њ	
%jњњteF4‡дhЅеVЙЊ6 ‡д;Шh|eBґьєаюUП ѓоXя*vЅ2џ
ъvCp›5гК|6 ‡а>z/Й
Цы-*±+уЩ ’=>(;%уЩ ‰6$Ыаfр‘ЅЂCrМ+`‡¦МgѓVШђ<UђџМgpH^“фV·

­!9rґ“`хZ ’чеtњ8§:¬‡я–oџМgpHѕќФЂюї[
жЕЃћсy»дс­]ЭГ2џ
zD]тh_хЦ|2џ
А!№-[хБ¶
М/$)¦ьp1 БЖшшBеяпГVA…№§]ЅјџLhpH¶9«Ї]&ґAЧeHћmЦс”	m Йуvћ™П­“!x­jaьd>ЂCp$…ёНrn
ђ!y{ЂБќ’s3 ‡да№гo–s3hcЙ·qЪћѓх{Т… ШcєАБъNЎB9XKІ~/T5wаx:еЬz
CrФЊp«дЬА!№ЏЯ	“s3и
ЙгыnЃх{С ВЬМµОЇ-'gРв’­µb|ђ“3 ‡d»‹}БџњњAЈ^Hћk•ж•“3 ‡dёSrnЭv!x·YZ[ОН ‚чЬ_I~Ш)h°ОюьOОН ’OЌџsрГNA…™Gк?Йч*Мэ·]—JшСАЦ|Z©|97pHЋ·bюf9аGZHо‹г3¬Я8џ1Ќэт'Л?zЙB°х]цB-Ip¶3ЩыъЙ?:ВBтњ§шLФт‘‡дQ;Б;
6wг\ІS^А!9жlХІv
lћЩЛЦпE‡›зG|}rДЏ&«ѓ;?О2qрГЅЂ[ю™x8еЂќR!шЗ—йа‡k
¶‚P…UсzЫС@ЫСќг6ин?†цЏґЩ’6TЏ5±cєи–е‚гЃ`$Зe№I?y>†ZBKмюыЪЩi—‡кл&6ЦЬ'©ІЖБHЋйтауЄЧѓФ—lУЊKЦ{Z}GњF‰Х{-8м;‹Ьтґ¬Дъљ·±ШeИC’Ѓх5ЫFЙ}8V–SШљҐ{=д!]‰Э pКO%OWt`шЁЗЅHТT.ыШ—2дС`‰х%{¤|‰ХЫp­RЛ|Н№Eф"IЏ№"?ЙЯ«Ч vGnуp{е‘ОАЖљ—qцxаIZОµ=ZЈ\Ѕц!°;h$6Ї‘<ШXу>`ЖГHТЃzґgЬ#№н(±;„ЅQоѓ¶B{ЧєQj‘Ш‡s…ц®эС’
№Щ)Ўѕд 2Он•GP;Bмжітx`ЙЃ„»Щ¤!“«S»ЈЎѓ¶W.™4–Ь[)є‚‘њѓё{]"№$&Ў;єБoѕ№
№ЦШXтЁЙжгЃ_$З/n3zfC®ДIl[uі\¤h,y~”ЖїHrЫоy­>•n'L GX$"ry?°±жU…¦гЃ_$№m·џж$(rЩQbwPe+Шђы Ќ%GZЮЭz‘¤¶Э5ЊoЁнA„ъЉm5JХХ„Ьnя&Е>Єд‡ѕsfБгXєњ0ЂnJ8ecИ­АЋ‰^ТCмГЎ‚<оаФпХ
а„њA¶‘wWnb 6ЦЬ–%ГАx IfЫУЌ•Ynф5Г N_#цAWБ iMШErатq•L‡nлpВFЧC№qШXіµjЋ–''{8clХ&v»їю±ЉvИ=АЖљgu>№еb еВ±kтMnХ&vЗРuKzЪ!wk kЋa©щ­дfЌЃfЌАFZbUШЕ•y"е6 cЕ§¬Ьд1РдР{йEХ&vGYҐС7’јЃЌ%ЯYЃњМ-2И‰­84EWµЂ‰ЭоWMъ72ѓч 'оmnG(цбL%№{јЫQ®jлK6їДЄєjђчцХЧьpЄ’ЬЭClЮѓ«ЪАДъљ=ђcА,3xrв^яDщ^9d>”ANЬлоB–1Ќ«ЪАДъљЏЭL›Lб=И‰лоВNЫk2—К 'о]Ж№oц©60±;Faі%Дd
пANЬ»їAиГ±‚	јыњTНѕt}Й0ЃБx±шsґL`РпgeћЙ.ѓ”ё7О3ЇnLа±(H¬®­’чЮC_“й_im=ТѕIvбћ»ѕfАіц—WБd
o`‡Лmќь	¦Цg6ЩЭS)окK†<7A«k+tїлxПиУdЦ™AZЫoёзL¬nqщЭ*фNЁ®¬‚7ДN’ыњ_¤µэь0Б|ъЙФWx=<аЕ—щ»ЃЌ%Ыж‹“ЙйхA^ЫoцТЇ]·Ѓ
6РЅ«5™їШXуъnТSњ_дµэЦж“Ђ+-}Н°Ѓѕ·,‘2™їШXућ3н¶ЙщхA^Ыo_6ъЌРЧиЉC[Mжп6Ц|Є†Дды Їнwѓы$±є
lиѓяѕEf=“щ»ЃлPZCN°Ы¶п0vµЎБ†ъЇп/џЗL&р6Ц3Ѕ)W?WIlMrTм2	7°!wЊћэH&'ЙЙi=иЅ4Ь2•6°!Ч]њL™њи    $Ќ9П•М‡
lИхH.Џ†њ¬д€ma{щ©флЫa‚в)Ј“3Оѓ<Ї1‘ѕ†LK
lИ=;Ј|“іЖѓ\­Q`ќфБ&3Kbпe†АдФп Яj<ДзЙмРЂЋ яYырз>мPПиЯҐс•ћЃ
№}]*X9;H{Ъ‡+ЦtЏd–f`C®;ЃѓШ‡-К!Vdћ&3-r§dy4дdи эЁk№іёfэ&(+Џ>3ю49џ9ИнФчf‘€Й„ЗА†Шcd¦59'9ИХЇКХoВЂ®r#ЖјўЙyЕAN©#>щ­ф«0 ¬ўЛ4У8цђМ&щСИ№h2y0 !¶{Iм!Ѕ—эхИjдН—	ЂЃ
№о:3ёyHТeoю€%ыp ­†џДLПЫC¦-ыъЗњ“¶H¦в6д®щСд?¤Л’`ДЁ‚<V2/°!чё““{фђтКЉ§qЬwЖ‘l]~nJ+t8Х8ж.?ь$	UфEy-Б:iјА ЯЗJІь’TPиє™§H•t
Тx“€Юяb5 тЎяxy|CЁV1И•“ &IYЇ^Ь‡юг
ЙБА—ы|дКIЂCтщfс°<фJiЂ/“№~иц>ђ|'+ЕВбТБ7$·ПЭиљ·щРн}Crыж!_Ш•ЙzР<ѕи|nd—јк8Ќl!ръjњЈ:Ц"›Ђ{їЅЄџVзДЊ:—ппЖS9›иФAЩЊа1GХlК\=9ІyРІѕОjQ•&КјўЌ„`•«''$:шМљ{т©$0ЩЦеао¶±ЪWTмМ
°{?їћхЂедўцggl2™j‘N6ЊeяkѓSЛeІ? °}ЯZµZ·’%юcЭ­к Х
’¬ТрiЅЄфХ‡¬ћы-^){u)©OJ=iтf:sFН§ѕнфдєo‘¤µлlаЂ]ы8~·7хµЈ'лјѓЧ G‡{rЖҐѓ:0hтeЦLOҐѓO%ІЂ,Т7УsЪиd‹йЃLi›ћZо аk1ђ6±тмt®OP	“dЯдIФй!;Цђ¬ю4y"tz№'<ХEoSћМњћк	o3э“'$§іybоC1Цt№А!Y%ЈцgU»\iђДђСЋ:¶X=ЙнMЎі“ЈЛПпЙП­™«GЏк«юь¶(МшЉЂEgtKЧл¶>jdёк«юј§лБ|y^єюOј‡EmcЪsuRR\„=G»Б:}^F~1wЏрЦ?v”(:шоbЗР?х„ѕЊz°"/ђiРs”ЅѓO—sЭ°ЗЭ~­ш2	zNµm1љл7,Y&AПсІ
mйЅЪ•u{ьБЏЁk¦=–IРsаЄѓ—›†jдТн1ь-‡pОО'“ зь5„
¬ЫcШуї5ыЇЏUѕК9‘,Э\]уѓЙW9Gѓ»ЩЮ5qY­и9КЕЌщ—Cєљъ ЯsKwE0ЙчЬ›ъ2ЮsЁJЏЗ—rќљъFЭs2JЏWМUS—ХЗвћгMz0±ѓЦ¦nС;,zNIжцu‹ЮaС[ф ¤'1u‹ЮaСЫъКѓ™єEп°иAЇКфаТMz‡Iѕ•Aw@^x^‹iЮМ
t9a»¤Йн~V¤Й$УШҐHzCµњ28$»‰Ў]ХG_”‰9Ш>ЋBm]Nљ’]a“.P~uPмu‚ґЇ•#W{’gи{‚¶
з+киЙЗ6дљ-ЂCт®щMЂuPxеа3XlрpH>®Б[…іЅпboVrА.щDіaЃх­jЎЋптЁЯ¬_Њцuч±)W®‚:Ёd:Q¬ЅHо?дR&Ђ]оu;Бд“>л  ЙБоn’ІoИI ‡д0Л<_rIТAY‘ѓЗ>µЛraА!ЩFqјкќ»еAћ_мЪђлѓ Й3
Н	~Ш*h°»\ЏpЩr•А!yї;%—щ”кxЩ­e?\h° 3"њЮ{Ppг`Я+rР
№вађ|пбС–+nЄf.J·№lаq#*©#"—Н”ѕ
жшшV1дЪЂC°k­QџKЯЁћDУг7.mИХ/ ‡dЫ­ф€\юrђ@
жПФИх/ Р`ћ^’хќBX©+z`mИ0 ‡дЭ3zГжAц
,љ­ѕ¶\р ­7“ІMп»<р”ѓEsLѕГ
№ађм—*_б›Ю>yаgѓPјя†\	р ‹ж)3'—ВxйБў9ЗҐ
№ађ<<LЇe?l.[LPІ\pH¶y:·J®‡9€‚EУгn•\pHЋ©е%щa« ГЪZдiC.‰8$Зрс’¬oХЂ‹±e#еўЂCт•LТЫьКbм7’’еєЂCтЭїг)ЖЖЌftu¬_Њі&™иФ[оJc|jJТђkc Й}зкЌsщыxС·
B‡\pH6·±ьНГЉЖМrЂVьнC.ђx – ЧЄv
*¬ЇEЮ©6д
ЂCрюMХ›СА„щХ6Л52 0aЋr¤"ю‘…1‚чB®’xДУГюЊ‡€@…Ќа—Ґт”GV’ыЁСczЧ­PрQvыЃх{aPa~-К<л]Zд@ѕ‡ЈPM[
pHћ«Юф^«Ћџ‹B*ъ­&®8$oЫїeл[eщJtь“Xї6nЯїЯь°UPaѕ№ѓ ЙГ«Б)№/KѓфцҐЪњ …ґцXїfЭќюж‡Я Гў%ќWТд	Ц ‡dW{«А[f¶И/ЫLfЬ8$O·6~Ш*и07О›oЇ&уf’Ч©1їzgПџLP;®ГPТdъ+ЂCтЇT·йэ9‡3‹мVir3™Д
а‹џ•2x€щsаСф€ЋSaLжў8$GLS’х­КiI3џсkЛЊR ‡дбС3oХCФџЈ–ьtю МpHц#F-ффз¦9gMg7™Ь	ајZyЫzУЛa!к\ѕк’¬Я‹	6Ј4’7т!иП*ЦyѕVCfZ8$џхХyъіv^Wё<ќ2aА!щЮЦx/‚ю¬џ]Яљ—Л–yЏ Бни‘X-ыa« ВVЏYМ?ЬЁ°ХчOyКAяeХЛЪТЯЧ:Ю єk|¶'.Ѕkа!j•ЩЯґхB¬Ѓ—Ђо—™o [/ДИеwЧ?мбЮz%Ц@6>||VSЙѕ2Ю"Ј–э¶‰Хлю“ЃУЅФЏЌUкVbЏы1Ж©м&{ЩАЋђ{H»4Ён3Ц\«пЇa]Х­М«LЩ?6ЦЬЈK"±zїЃЎхЖ"%=«џ+Г№rчзfнЖ”={`cНcZfsж‚ЎmЗmКWrхуl9›<ъvvbх~CЛЏRУН.CЛЏЕ*ОдTзл‹ф™fњr0h,yъеСx B0ґ№ВќKЦЛ.lжрщnщ€7е0ШXі«цd{љ\†VЈxѓ3~+ЅЬГр6cРе>Ё+ґ)Щэ8™h>ђ!Ъ”"4П7ЛЩф2Лмm‘
sКЎ°ѕжХ-Д>њ+ґ8НИ»«—·XNo/‚Є)ЗLЂЖ’ЈО+µХ‚Ў;*(ЦуDvЭи[N}џc¤«2е`ШXт0цUН.„	#и*’е%ілFpr`ј‘qtКa°±жY
ЉуЃaВО№™ЋtU«Ї№еАч}т=yК°±fЯЭN¬~¬&ЊаЬ-_ў}іф%зЊъо~®®¬&lаЬpд±z B°Ѓуlћ›C·Ѓ3ЗЫѓJ
9¦6Ц|З1~«‡cиЮСЗkdє
њY]6oЛfЁ)‡ЈАЋђ{'їуГ„tЫІ[~ЄЈн‰Ќ2«9kНє¶љ0‚«ЗММД>њ+Бам¦A1ЭО¬h»~€}PW0‚kL·љЬFp№УО{dєњ;«іzЛ`pКБ3°±fч‹и>рFLБе—0cз©ОX'ЦЧ<ЪНW®)‡ЭАЖљЧћыp¬`Э*њ«[Б	+$qЌџкA]Б
®C«+CёШГћА©ц_лkЮџ}ДЄк
ШXіk
ъ’тлѕЎ7f№%#гЪTЫ>	=БKyІ,tКtГАъ’·Яjv№,АР‘XЧ\іjҐ†Сp‘XU[kоќј S.(04­(ј
j“+±Q¤xzf„§L8l¬yмЯ·z8V°‚ЫЅЯ$¬j#±QЮё90{К„ГАЖљЭд”‹ЦЃeџЕTЫ‡ЌТЖeЊ@eѕa`cЙkWD&W?Jі»[Х§ЪµD,к[­щA[БєKNЃ)ЧMЉєFљ®Y5‚‰ЌЄЖQ¬М7¬Їщ|•¤\paЁищиkЁMZДF=d=VN™nШXrЫ=kю§\ЄaЁ#_БГIЧкЁ60Ў(gмIѓ2eВa`cЙЈпГ%л§ЄБћqѕ’«ЫА–Еџ›хъSой 4–йБ\І\bdр<Б¬ћєщк6°eХинFЅ.wѓ<Џ‹cW®+12xєЯМGмyuШрHиB;Э№ЏДHбyц0*:9Лn¤рЊ©OЌ{¤ЫА6І‚±wжbд#‡з9‹	\9Йn¤р<wЊ4џKҐ— 6ЄыИЧю%·®9<пЧlыp¬`пEъ‰Хm`#·Nі|4ZrУ‹‘ГУГЮ/“KNІ9<эЭґЃK%У EЏ=ЦKn—1rxЮ­В‰}8V°ЃЧГАN¬n[Vі}іgaГ’[mЊћЌ­ж–њe7rx^ч>y®ЪѓКЃ!»ю‰6Чьp6rДЭЪ;Я%·Щ№4п¶AЁѕЅќУсЖёь№ъХO*Н{їНџ+'¬ЌTљчо‘M·Kо°vмpЏТ\rЦЩРI“хъмДкWM·а„ОьС’SЗ†>ЗvЧиyхео`Cо€1·‰}Ш#Р$cу1cЙН5АЋйGu%§p
=ЋЌЄy6дЮ`C®{щY»д<¬ЎѓА±ї™ЩKо¬6до|"[r&ХР=°ѓ€‹іЈ—ЬUlH=krЕr6ФР;аШkdJ]rO
°ѓ™-[rFУP9ШГЯKоЁ6дєэLgcЙYICХELzЙДк7!Ъvґ‡ђоcЙ™ECЕF`/«‰–ЬMlИЌІДЬ#9;hЁц€)„нЫ”«Я„mХ<FПВХ%§ш•"Ћх­Ў†•;iЂ
№;jэы°G9Ьr»bП=’ыhЂ
№nу3єrm#'TЮ~ш{е.`]nws”9 хђ/РVќ=„Kо 2¤єѕ™”ъ°CРV'ђZ}Йэ3А†ЬС[Ћ‰^Y«‘ін#[с’»gЂ
№vЛ|H=
lЬ»дЮ`C®ѓL­‡ф‘еРЕЭщЊ№дО`Cn    <Юдi~HефаоadFЇKо›6д‚Ъ,±ъе`W°lЏZrЫ°.wuTЮА‡dLЋс1;п‘Ь4lИнЫ
ы°GРVш~YЭєд–`C®№хН=zИЉд<Эб+ОЗЊ%7М rэкO®щaЏ ­Ж:-YA–\lИЌ!•”ы°GРW~ЄR9o№ЊР{?v¬м‡CЋ¦w·мЮЭr)°.7&Чь°E7З[Fм›Ш‡« uenЧ¬oQО€µnуЗaў¦r’1&Zѓоъс-Ё9•ГњЉ‡5ы+°љЬ8LnDїkЏ‡<)д0Ла«жа›Ўѓ‘уЮэ[Ж0yvFlлХ>&Wым]ЈёдвгjЂЅ'x 	Ц™юЬ§lџGЮзПѓ\~ЊNТ ›…ХЬЁџЇa ы.“#'†9©`WzЋВgv	љ\J€~&»e"·XЊяРБаСШяjrmљЉ;їU]r™ъ‚Џ‹lЫђ_ЪQTпаy«И¦™ьж}гЭЪБСPmтгуЌд ы­VШЌ—Ь {ФbdсVќµЮђ›6.«),z	ќgѓtШЄ»`LµP”¬ъk	ЙЛЭ¦’¬іxѓ сПцd%G»куYР2‚щ.(дЊ\’к;VЂБ­“ЎHnqХҐ ѓ[сs•4_W}Ъ	0ё[ыJ‘\хЌ%АаV6ґЏ$…CзVlаVф@ўMТ#ќ[±Ѓ[С>ЏвKІО­ША­и–ќѓє¬s+ўaеПМ#z‚MзVDю#О6[]ЬGЧ№;NШћ{?J‡`њ°}ъ­Я¬Тб'мёҐЪ¤ҐVйpЊvь'§µJ‡`њ°c—ЬЉ®FхAcяknџ™ЬViПщо<ЅR>*Л*Я.0ёaeпмRYVщ \E
»T’U>"]B›VUЋU>Ђр 1Й¬R¬2™¬щз–ЄђТЃk›ifэн1‰yвa™‰U01ъ©м¶ю—Ь8ЎётUz©
ЂкиЂџЦнХЏUтУёЛДКЃҐrй3SЌд­3§ъ±JЩжжhЙҐRй3c‹fnг©LъМєFSф ЯзR‰{™9Ќ¶жЦёїтё#WКtЧg2ы©«¤;™уЊКєкз*	Kь33H^т¬#еИъzҐ0хc5Ш¬:їdq\2Йє‘хcЩўz^2Зє‘·c-WVLЛйЗ*™7FР'V?VЙќ±гЭ#Џ†ЦЩ/"Де <сЫИ_±эоуСDћјmd pЗtтI[ћЂmдђ€бху'ъ±Jїш­3ўџ«дq8­qTФ–G3™Ћ‹НpmЛн€АFОg|+ЙdцCҐДDЄШFtК%V?ПЙбабRkДк)М‰4іyњ·Є§Ц&ІМ6Ј­7±ъ5Jт‡іVПЊь–ЫЃЌ%ПЕВџэP 1‘Ў67BѓїWїѕIqN9п[nG6Цм§йp‹ЋІЫоҐґ|kЭтpf#гДэЊC ·ЬЋl¬щњ–oћыЎ2d"3nfFnЛIH#WEд€±zКv"«>ї6іG`?T•LdХЭqЯ–sџF–rџn№АX°;Оµ№‡
йшЩэцтЗкє9Й1оjњјеnD`cНЈЏфШчC)ЛD.KD*9Нk¤Хёы2/ѕеnD`cНf™›ЮU0П 3ИfЄ[ў¤гёЧm`e№ШXсъкИ4:ЃЭd©ЮтdЈЙњЈЯ ¦¶ЬЊl¬y/>–n№ьfўEЗ±ЗЈИ<тDҐЙTз7<"VUUАЖљЏпRћ*№tgўEЗ±оЇУњИ“њ&3¬џ#K®ЄЄЂх5ЇЁЙдwVПХD‹Ћc'пmy‚Фd^чsCП(ч"Knwq‡Nак‡I -Џ№ 6–|ЗЗЫ+·"K,lЮr­СDѓЋCнgпейАъ’[јКpЙЄ®6–l·—Ь‡Cы·ж,w]ћкl¬yЊ›™а-·"kvW0Г“-Ч8M4и8v«sНЄ	6Ц<Ќ]№[nE6Цј7Йш·\5СЎгШ3jНт`cНnq“–jЛЅ€АЖљЭџ«Яыp®`=ид8Щ-і;kѕ–¤A‘{ЃЌ5_7њьVъ№j0‚ыыXй»е‡]`гЎІ]Ц’m№Шrэю&V®кљиСqlл=3m[~P6Ц<&G	m№ШXsч¤\э\5Aw>й
КПШЂЖ’з$-Э–{ЃЌ%ЏµX"“Mґи86шууЙЇзАЖљг5„ruu…©„nѓ~Ш‡c+иbwцlщСШ|w/_CnF6Цјжe(±MФ“8Цµ$Јyl$°щЬПRР-7#kЮ‡у·\ 7QЖвШФ‰ХН`Л…СЧGмѓє‚‚Zљ№xnўz&°‡t[“	l¬Щ.Or7" ѕдН©5дє»‰g®I:rћly<'°±дEВў-7#Kn‹/н[.Щ›x]ЫСвК‘i[!l,щМy‰}РV0‚І{kЛе~ЇzЃeіЪ–

±ое+И‘Лэ&л:г&VWЩUtжI7фИХ~“MEg-2»№ЇoІ©имО"І#WыM6!SЖџ«ЯЭl*:·µIмГБ&њлЫЉKtдюєЙ¦ўы-vl9k<ЩTtэ<f xдюєЙ¦ўC^№ж‡=‚nѕ}\тГEЂzЅ#Ю·ы°EPЇЧЖО2¬#чЧMvЭщMI9;ЩUtз±t­ЋЬ_7ЩU“r¶Љоо(~HмГUЂІЉ9њЌX}ЏІ«(8wуaоИэu“]Eч®–іrЋњРњдЃх°чњ*ёХkї¬ё}®љuЁЧ4~‹ФтЈЖ;к%ЌINac6 тыЪ!MDК!ЛрђШ	вmЅ\ИщЕ›µѓЂ’еD_Mѕ
к’р#gЬjx•лжS“ХдЬWНџ:эђЈё
9U#¤ОьЖд\ЩЖ”Hawўk
Љ~АF&fўмћЛ–]CМ"A&кЪўdЩIГ8¤„nы
2СOШИњA0Уе>›МТBьрµоиjd2]"8нlQОz]™ёґфЋjЯb‡ЧOШD`i®Fёj™ЙдрЃuїџЋ\Ў—·'Тє¤ЊщD:8uзe‡їcхPLШюkЭеІ®P®™Eu_Џ
ђБбh‰П‹<йе,sµН)KCтЬ¤Шq°иK$8$Ї>Є&Q­nЋ©пј‚j.БjА•ајЗъшЅФN'L‡dч‰Уr°иN$8$;њэ®¶:¶C°»%W­$6дЮCR\лы4‚–юoыСLіЮ›ю$Ш%ыщадe?l”ArЫUћЬФ(Б!№·єRMmxКк!y|ѓUХMЌЃ’GQ"9шa«$[§Чиа‡k± 9ZR)Y-јЙйнN¬ђ€ВЅр„/Гv?lX”GЭZцГЅЂЫБЁї	~Ш*(°H5Хґы‡{эµ=8ЁmVKYІ.є‡fнтR©СP‚'КєhЦ·<Ѕ №Њ°Џббg$%O@>"°1S#Ўz~»Ур(›bх<s§;ґъфРuЁq Рfgjr=Щ!Q‡·†BК•]‡Њ]AЇ=kЖµо%u–{@VГ?еZ§C«Хю5МW~t­Q«gЭЯИRЭЗОЉогA	} !їBЦјУ5ѓ\µьX#Ko?ЈЧИRЭЗОЄn? kХа<эЂЩ—‘g13щFaц]<G|ю“Бъі|3rUC§дK…	t¶{>Ћё‘GF`€^~ZM5“i«1C)nsЊ®IFъ›вьBцЉId"gL2
°}_5lКЊКFахХИf“№Ќ1O(Аы~ХN§Ъ7„СNwFН":ІѓЮ«ш0µй`ХА’п§–эРhђ|Чб й#{и »дщхKБІѓЮ ї»•Я‘tЂCp›њЈва‡ќZђЬnЌУ=І‹pHогЦЄ6jCpЯҐь®мЎ‚ѓчЎь°Q’‡oу шЎЧу@І0«e?мФ…ддFмГ­ёTтЦ7j +ЧCЮ№kХъ­иКЕL†ДКюyCnЦ±glЮЁ+ыз ‡аЫЫЃЇмџ7tНїMц%YїъЛќcзц•эу†юЈ Пљы~eађэѓ%щa§ їV$ВyFdађ<NЇ©VЊЈy’=$ЈБU,’#яЕ¦Ц}
Мќ ›Е”оил !1rљ‡ЏЦгmCbдЗ™мX= 4$FЬс[ѓ±єъР’амqЙ¬GЂ†МИ±3–`х©%Б™pz#~€ ‘9уЮкЙU+А’Ч¦yuрГN!3r"З@¬m#1уЅВmµ’;АHЊњЃЕ3ў–c'xFlСѕ:Щj=vЂ‘№їqа~ёHЊёВј—L­Є0#~яїJ1ЁҐС	ЙQп[а‡­BbдЅ`эж‡{ЃМИЌAZ<ќjЌіѓ'2#wЕЯ"S З%xЙGт0uљ^eХ—ІР™ђOкKЬNсI]Ї:к•ш6Ґd><mv¶Q МlJ•rЈж‹RE}(ҐК—ПЌ’enCЂCт\}Д›:8ыNЧ`µc3™ЭаЃФ?g•:X}Р™:^їЏУ’ЏМўђ‘Шщ‹йМ$EQ[^K9vН"‚№jЭ‰ЅQ“.§ЪМE‡А±k’Ц­ЈОј}=Q{ЅИ’a—мNР(oBз	=»ЃыКT€w*­cЂOшPyхЪ¶ћqюr§‘ezbv$Г‘[ЦЊЏьT‹ІЌ ъ&ЖЏL‹м8A?эе•8r/ЩдиЯ/јКХ3ВIЬµЖЗ©/G¦T6ЦЬчъ(W/ЛЙ‘ГС!ЕЄ:щaz’/,zf;KkфТ©€F\®ЩѕД>”ф@|.7ж‘Д'iКЦєф3ЏLжl¬y№ВЛoхРM–zзsu™5&GОNz¬іЩ‰vd"h`cНQІ•gгЎ›,х]дШ‘S““х%ьђJцИ$ТАЖљ=f3юЮ‡sµім *«ыYЦІы.ЯC& ЦЧЬѕЙ^ЯуРO60ћ®№Фl0>r"vІљ&Fcс<ЛдХАЖљ#YOмГ№єYў1?V‰КщЯЙ"ћХ
№G2с5°±fЧ°“ЯJ?W9ЄЬҐєG2гЮд»Жvq™$;Іk	l¬ЩКМ‘ќ‡†ІUX[ЛD“П)'D(WЧW;Ш–­l’:
e9ЄјнЖм#уNѕвњ>ИЈrdwШXs°еqНъ№КQеНM6+µeZГЙЗЈ<HьОєѕ2ШБvцbрCCYЋ*o®q2¤=тp»Й7+ЯХ“OmG¦	ЦЧЬЭсзЩxh(ЛYеэЫ»дкv    0YB#Йo%SЊknУ2Лs:КrVyпГІгиИУн&ЙIo0ѕҐћ”йЙЃЌ5Џoцб\БцqЧдљu;њЁЧя’%с2µ9°±fЏјі™ф<t”е¬т>лpЏ<Юn’‹ХГЈцqНъ
v°ПC>зуРQ–УК»ЯђИун&)`пњ$и”џ2kЮ§Хйз*§•w?Nґѓт|»ЙЪ»'YщдGРДЖљп<ЊqZКrZщшЊЊ
Gp7Yє{ѓt&х•Lе¬Їy°Eщ<t”е°тП,\±nЈ^ёaЈ2™ШXq<дНи(ЛaеБ†Мyј°±ж1к&ИтАЖљгЭЃїчбTБ
і›VяКунЂЌ5П8W‰ХµХ„v3№q:ЩrVщЦХm`Ф‹/пЗз0щ‘8±±bWНy2оC\Ћ*wЇЊzэКУнЂЌ5»jјД>и*ША±їћ5TчЎѓ.G•Џ}I~ейvАъљЫз
6їіМЩl¬щNMјЭw9Є|шеЙё+3Дkvoђb”Lаё,‘»}{9©Ьў:…+Ц-`TµЅt№вUhЯЩ”Єћ©Е9еЦиr_™РXрк$Ш‘ЯР+оЌуЛ®Ь-ё8§Ьэ–)ѕ+“рkvkџ!іьъћШXуид»ёr§бвњrs{@е*“яkѕ‡©6щЭ>±±f[t#ЇЬҐё8§Ьж¦»~eТa`}Н~0оаюЄЄ
ШXу.
Р+w8.О)чШ„љYж:4–<ВЌL¬Є©ЂЌ%{фЙO%gЩз”Oч·еЄШXsР<ж±’)ЫЂх5GвШ(чбXелOМx¤\Хk® яК”mЂЖ’{ґ%цбTБ О1їZІj ЃЌ%_чorН2e°±жA‚ќ+зШъOO”‰іЌаКTЦАъ’G$_є2c°±d[¬ојrЋ}ЎнхаЩДЄШXі»ЬЬ"™±
ШXук»~Ї~¬l`ґЄСПђ©»ЃЌ5ыЗК\ч•9ЫЂЌ5Gнoћ
9ЗѕРаШ“
W¦]2¤єҐПlИ•ідЌЃuџ€+ЦuFѓ)ZЯЬ4cr¦{ЎзбD±ЯНgЫ+УџrышІMцКЩк…v‰АћТл2…°!7к	тDКзN …~™Xё2 !v~¤єrТxЃЦ'°{UеїњЅE
DPюЄhдЎв$ыRЬЗaщ«Й9XЂGґ!®]sxд$м%5БnХ8nr"ШЬыЁVf9“zIk°»Їљ'r:ађЈсJтГN%зё[•Нm–“љ ‡дitWь°S‡Lй—]@&§&ЙлЊ]’¶к’gЅU‡‡њ`8$џ~Yѕor†сІНlџCz>лчўЎkЯ}ЄHО^цЁќoYO9Щр€ў]W$мд‘у}—
nЗќйj’“v TнV!–њґ»lЋ;г°оЦБъЅhР`ЗЇ«ВMNЅ]vЦќ№ъы‡Уп=ьEЈ*ХЯ”3h—	Пf%ЁcхkЃWdЗЮЏФSОѓ]3<KПZхГµЂ;о}ЊZцГN±!°Чtѕ)§¤ ѕд™rJкrрРm“|SО+;АЩѕТEuрГF]v12wрГ­ЂютH‹Ц7*№h<n%XїкЛэйНµ)зy.ylЬ)Юдо™rІађ<S:§њ­№$Б№Aзё	ЦoъїяоdЌw°ѕSЙ гbgЇЯ¬ЯЉэuЈЏь°U9б~їЛ,з? Й1¬А[•Ь=|‘ЗfКYЂ-Шїтў¦њЖё,ОюЪжф?Ь‹Й}Ч`У)g#.K»їб¶†‡DN) ’э[У›rRбІ0ь›ЌзKО rгNсЛ‰ЃЛШ(ъыэв‡kq!yGu6БъFeщмЮЏ€Ј’oЫUЃ¤_Я¶пгPfлЧВБа;кѓЙЃъe	mуї§©’ыјіАъVe!l~ґyВдXађl_Ќйњ]YОrg9Z8$G&•‡дЎk!‹R[MV€яК6пЇbИщРґ@жІ}9(ПБч
¬№ыVы!Ъ'нЩіtђМа
pHцhџэ%у!ЪП*ПоjЁvJжбШ‚іјWH4Вэ¬ХЊз.vjL™NађЬПdущ|чівІЏyKИ¤Ш ‡dШуCёO
уИ—љW¦¶8$С	/ЖCёO‹5ъ(°~1*¬ЇрбЦ·КЉЅјfO™f`zлЩJу>„ыY‰8¬ПєП2[4А†Ь№JжCёџх„о‚ќQ’х‹aРaЧ|µПб>G–ппpц”©›Й® Л<?ДыњwґВyџ—МЮpHvБЬзхпg…ћ}v¬А:МZЌ‰qрГVЭ¤nЬаеа‡‹ж§іед0л[•ХrБ^vлkлcB‡ЩX›IЎхр“®Тмы(Y¦q8$ПОІ7л[E®Л€#kЩъЕРaQtNъЌхт“(sЗЈБъЕРav&G!8шa«ІУЦгvжІ–Мж°KћЯШt+ЦCМџьAіхБмт’щњЙЅЭZхГNe“oїчч“оT{Јэ°Qд-Z}р-O/…i(…q±}у
Q/Ii(IwІ*ъКѓѓсзXsЧ±Z|еRэЛQUсPNЃ\/x9-г~лїК…{—c+nФЫWІS- ёњбWbьІwкSюе$‡эc\¶\Uv9SбЮѕ©п§ьёќ‘sњџ·,џЇ~г5я¬Z¶|А2~ЌgхЫk«д–!hњlЋцёF?`ГтdыхзO–iОУ‰jЫПЦ¦Lsћ~P‹№7VQ¤Мsћ®ЊѓwНфtгЄ0C­Иv7€ДИKж9O‡ўэќцQЌx¬І*(!мБяC¶сҐтњёмтШыѕTћу wЂЏ1ПєTљуАЋА¶o’Ђq©,зЃ5`ыв ·ЁђБI`
RF–”vФуEІи6Ј°jЫ|Т€EЧПЄРвЄЗ‹L`СsїbjRЏЙјў·Јъ2{SG‹&«Мию“9њЕ±кС/L`ы9Е<+MP»мg«Gм,Юsч«g+v•=XЃ,л>T¬„e¶o¦тшBЗBхЩ"щП]zA |‘р6ыGмCй*]СЏЛJ™‡В кѓГвЙҐW6иЫщ±оКЙ/@cЙ§UЕњыZx~tмэє[ЇimРV5Ѕњ66Ц|kVо•іf/—'HВ«®vлЃЁC€‰Дmуч>ФЊЎ"p·цќ¬Э’уm‹lя»ЭЛ®uR@bcН‹#
®њ©4–C\У­–u‹3¶;Х¬ЌUз$6–|ОH‹vе°±f“ЕўrЉoq¶БћЅ7ю^=йрЧ·[6О_9;l¬yћЕъ:99ёИЦгѕ%'А^•й'±±жѕ—¬+«Ћ*ЖЅЌэrRq‘#hџFВњ«т%6V
Yр)з#ЃЌ%ЯVeДr:rСУ‰є'цИ^8°±ж5ЕкєЄЈxт|~s‡д<жўu‚Н2m‚мыK>лc-ѕњ6ЦЬО—Ѓй•3 ‹~ЭйkЦљuШ3дшf•l~rцаXф06„Ж©†tЧЅ*M?9Ш1ЪЪфЎ?9х
p,Ы.»vьpё`П<$цw°n	;,бv#J–ЦOОЫЛ^ЎyЦПЧЂ-<5ЕЩ±є-МВv‡е«mЦхЦЂ5<1‚Ѓ’ењпвёІЁM#чъ'“ы/¦.¶»Y<"rѕx‘4лЬ№XGуЙщвEЦ¬pіVIЦ-bжLNл»®…њl^дНr©ќZ¶~ѕ’8лFVn¬ЕМЦњ_™`]Ѓ%u–[‡±kЩ%OЯЗ9Тн“),ж‰NґOXW`еRAљМкнпЎ
q ЬУO{ј¬ЫЖЫx¶ь^rЉаXvчИ…тЎq Xфл1у›`Э>ШЗs?І$E¶йEr,{ьШ±ї‡fДЃJУП‚¤…`ЭDИЫZg5т'\8–omь`
‰uЄAПVZHе9Lp,{|дҐqрѓ
C•«Ї™э'~8aЁrэ¶нт)ФlO‚cЩуg^eк?`cХ'(q	ЦЎBц;E;ъЙ“ЃЌEп_-Я'“я«ц •5зЯCcўЎјц»5yв“GL«ѕ¶oЃuf(НхcЭIMы=ф&Js[л”dЭBZ&}ЫЇ°н“ Ћe·zІяє
eЅQ	М%Х6=ц\х№tхe(	Ћ
ЃZфГй‚ylл”З)у№щЩYшэЙЂ Зўчш#яЪ
ж±yиXКKћp0^цWо„Lp,ыxА[їщбtБ<6,ѕлж1ћЋвAВNќk™	`_¶я]i}Н•уШ?2зЈѕкќO!±W	–№ ЋUЗрPоФCk¦Б:ц>F…%т<)Ђш‡ы(ЙкЦС‘іў©‡ЦNѓuмцµRњт$+ЂcЩл«*АOf8–m—ФЦШ„yJ1+Йє}њx!ф#2Ку“»JЋeЇѕЩcф=дй'мc_§*]'иЛЖЫds%T~¶Ь’
p,{ЏџЃ|HХOИЇ№Ц
д„ЃфyКm”ZЋeџ№щъэ=dл',dЏЪнЪ*ЭDNИоЮHEѕr7,А±м;яхµNlд€Й<ЫG7’FІЇk•gђ[i!щ7\о{HЪПњЗЮ~Хоџ<kаXцm¤t°®Г&ЊдиглхБNЊдичч“ґМЬ€’bЋ¬Ь0¬Fщд.\ЂCрЊ†P‚v–К]іЬ?№ађјЄК^ћGXШ7®§ф®Ь…pЮ»жАЛ‰гMжbњYEџЬ…»9№bЬ"{hтDв CгЫѓа	VЇФжд
sgЂЕДтDв CiЫ/Фorожа
‹ВьK°єS›ѓ+Ь—б‡x-}‡дѕWa6
Љ3Ж#Сslrо&бѓэ«MHћG`и>3Ч}й‚™L»ЖP№П6
¬Wx}ЙпЮџXЇръ’ђЭ<cg»Мк„ »о»Ц+јѕ¤(ЯБмр”Iв._ГїиД`еЈМЦvщ.нЃ6Яx¬—ж±‘oVЇ^B/µn›HKЩ¦М$vщh±vU{К…4—Zk5УsК•4—iRіY9ќ)—ґ\&+mї–№ёд2e%^Uщ(Wy\&о¦_вЄ]ФПЧДщrХ·Щ«ідwћl€$юЇІvЙП-—јґЗЇ3ПЧ’=.	bПн“Aч’Я.™Zoh–›«)ЋЁk™ѕоНґОR
ОDГтрЂ_[Ќчњс~<zрk«Q7Кq22йХ‘ †ѕ / 6тя5—S­l|юt5 	  PЕUsнc«ихЄЊі5Бї8ѕљ­©•К'№цИС­кщвЂЛ`$4т‡ч&ёbH[ єaіЌG(zhЃу5ZяЅЇ=џ4qѕ†‡•щ»zVgв|№;2иы™L–ћ°ђ1™®(kt%Фr2Eњ/J–Й±Б•ГqеЏИ,Ха»БЬѓюлhРuPЛ™	Зf5ЮЙґ•—:ЭrхяКь‘—µ2~›їў‘™/‹Vъ<“9Ъ)s*^–ЋфЅ«-jКд†—~6oхHК5…—ЇDіџпЧ‘Є°|¬qязїЙevЩ…ХЊ®{ЄяW?`6І®рrђWрчй`Лъў;«НQ~зѕ¤їгЦЈЙ’_›/9єпЬ¤ыt°~В’,Ы·yWKѓьтzЙZ}пЭХ©(ї^HwwµыWі«еi·зgгo9љ[%іоШsЂoЌ0јтґ[ЂCrфЅqіКѓТSHцр•jиКУnЙѓLґMfА№Ы(яКУnБНXэd}vuиЇЏнКУnЙkХ+¦МGа’wыMџ–‡Эл‚·№/D‡DеЋ	p‡`чHШ tеa· ‡dЧ[5Y]еЋ	рЂдµ8
©]yШ-А!y·JКЇ6HЮ‹LPо„йC гнbьЕшЦЕЅ*wL‚GЂП®qКк#hЂ;$»8l^Q№c’пщj"ІъЋ`чxн/ff~-<ЬлЌКЂVг”Х·И $чЯ¬o•:&±!xЊk\µъља	БЦvMНV№c’нгN©‚^ђм—jрЊЁЌ7	ЙkОБшB}Ур†дmЊЗzSыg’=єh~ШЄЙчk5)\н‚IpHцШwqџХ—µ Gгу_¤Јл}якїйЊнЮvЃUЗsіA3J
їК§«Ћзfѓ¦µ"нjџкwnцgFЉч—WэОННа//Ъ№о\фг»Ъ-†Њ"ј™c·ЧG
s?°EЂШ#:‡*ц@„7sАрvOЁьО¶{ёГ{N-[UјЩДг‰Э•(°zќЙЧc~mµ„ЌА1Ьxњ_ы°zќvЙлчЉ№Ф*4vv·S`х6‚ОЯRЙШzЈ‘GeюdwШђ/E<^j1ы–cѕqM|pKЈЄ]ЂCтфxЉ?Y-иbВ2¦џЄXІ;pHЮ6+Щщ°O+№&єЌьp)Ак±О­КЁҐVU1Sка[н@n™.фЧюЬйдҐP+ЈfэўiТzI~ёР_ahNЃvкrар%ГПU'¤3zµИdэв©‡нцрU'•3‚ґ?й°¶«Ћgиа€€*$ТsґИ98ЁLКПV“йLУ¬ь®ЮSюЊЦцћ·ѓх¦ърСUtьфћърІgTнКJ«Јtй)П(xaуssBw'P§гоЂqЈZS3Q›п-у;•k2лужЂ›їj№ЈgsѕЂНu
«fА6ЯyfїmшЎЂ•6¶~m"MnиЩњM`лтE®55х¶щА4§‡q,БђЩ¦7зX$wьPђЂ2ќ`sыIV“~›O[о|Kl“©Є7‡"Шm»¶YnиЩЉ`ч6fПZWгЉНW5чt‹ЦЈЙ<Ч›ж77_ љЬРі9Qa¶_EUSME‚cЩЅSйM&ЙЮЗ0#`еVЙЃЕж8†9ѕљ_СT+•аX¶х{
¬—јд,‡9ж(="G%›і¦]Э¦ЪЗДЖЄ—Uъ¬ЙмЬ›s ¦4јSr@і9b.чcxІUГњаXх±}СdfпН!®uпЄ#тpѕPеAЬ*°к$Ш—Ѕїс^“iБ7'PМгq+wJоиЩњ@1Oь¬ИЋќЭ&іЉoОЇw·*~“;z6зW¬ёЏ<$¦›И№]гіЖ±Й”д›Г/Vсф7№ЈgsфЕЉД=±єЃДҐъЫ»Oѕђ7™М|slЖк«±6\NH2†aq›To5±±к0Џ< 2ъжРЌ5о­RA№ЈgsиЖЉi}/Э>вuюпД0Є?и/ШG8їЯЗЦOWNмp­{Jщ©.z‚cЩcWЩњњFOp,{чЄeђУи†}Њx»Ћ¶$8–н
џs д$|‚±м3X%'бм6.:‘Ж©Ы¬Ж%я»a®‹!іїl!щЗ.+gр< №пНкў¶tIрюК¬Лґ[АЖЄЗ(<9ы`ѓаqЌЕM&эЃП®Ћщй Б±lы=SЛOћђlwХ“kЋмn#‡љьођаXц\5‰K~wрВІЧЏj ЙХОэ‹F“	ё 6ґ@ќЇѕцГ	Ыy:=ЦзС–л¬<ў•’`™„аXцйЌ\жMоиЩ(/
р)U xvxрZѕLГ°ЎЄG›ЬРіQЧ”PVЛЦm$Бwя‚1™‰`Й·¦Z5№hѓ™&: ~ы¤[И„љ»©eШe2.ЂcСЅm|“[‰6xipҐN5ЁИu†цEџтve>.ЂcЩq-ЁFд>¤
bљёRСWH°n!мjчІc¶Йњ\ ЗІн–Ѓ”›6xiўхЄћљ\YYXчїюµh]}
Ићv‘‡у7Ц©PїЛEќћоs¶лкkА@є
¬ЋмЭS#mЬ±БЦe^пПЮЙЖй`]
H·pг«e?њЇґqЧOз%X7ђ	ЋЙа|7н2+Анf6nЃNШN
¬Зл2БsnЄО.іr«v7ўѕЧCЧЧЂЌ3яJ¤Jй2‰zЃg”Ќ”дйљутсі?дрlњЌU ]¦o/pTРrЈdV.`
іѕ±?$с-ЌњќzЋлrУWЃ#G1¬k0ѓ…ґ9kАpИв[№е'¬Ає…LpLЅoЦ5БBљlъКэ!‹oiдцlМuv№С­Аkок{и2-А±мУlФkсC5КFцШї§y•"ІЩ4s¤щ6/WЃ’нЊ*”V™РђЭђЅ“ЅhЙU` ‡d?advX*92+ЩJщ1iшпяцoяцШЈ›м      л   
   xњ‹Сгвв Е ©      ж   
   xњ‹Сгвв Е ©      а   Й  xњ­SЭjФ@ѕћ<ЕР[M3яЙЌoаXYЦнBLjљEҐ,ґ»‚·z%€ o…*]I\_бМyІ¶u‹‹v™™d83Мч7Xы”Е „-•Iµu?б‚‡iсp¦ёёАaЖтќaU%Ллg»E;jл†mЯgOЁСпrца!Ыџфќ&ГкХ ^–¤ђ6>–’ѓПdК%FiгНЎXU·ѓ¦x>5Ег[УLЉLъ$UJъ~'ЃмO"щ‡6Xзј°JH†псcЊџсЕ ЧdлХonн?±L3!2e	Ъё%t^УqyыC=CгЊ…+†[щ°Лўi·2Ю6гв._–тє,й€›ЕЭсЈrґ·3h‹—W+“HЇChVеR†°ГЇ8Џ.sщyKЎ’І i„вaЌR% ~ѓRБ¬j©wRKТъПъkGг»р†TRҐГSЋsьNг„зшЌѕћЭЮн2ҐЎ•‚uy+H,Э:џnР…•ДAXJ[zЉ}Иб590ЕcЮ+У„г[ѕфг»ѕvЊ§xfч®MШ«ЗM^ь·`zoЖйu>ЁДРВmО‡н$Љў_‚{      Ю   g   xњ}МЎ…0FaЭ>Е$ai6n7G,
‰Ѓ Г}я Ѓэе%Ґy¤i=я®_цн j(БR"єF¬њю2bЋС§Ё†TKы­ЊзХЃ*Ґhw+-‹д^`AГуыRћ=3_q\$Ј      к   
   xњ‹Сгвв Е ©      у   
   xњ‹Сгвв Е ©      и   
   xњ‹Сгвв Е ©      в   
   xњ‹Сгвв Е ©      п   
   xњ‹Сгвв Е ©      с   
   xњ‹Сгвв Е ©      д   
   xњ‹Сгвв Е ©      Ъ   ;   xњKМЊOНKLКIMб,)*Mе4202У5°Р52R04°25±2°Р37013іР60жЉСгвв wа*      {   
   xњ‹Сгвв Е ©         
   xњ‹Сгвв Е ©      y   
   xњ‹Сгвв Е ©      w   
   xњ‹Сгвв Е ©      u   
   xњ‹Сгвв Е ©      s   м   xњe‹MnВ0…ЧО)P¶”И;“CфА"$¶@jФ
‘MW”¶«^µЌ„J“3ЊoФI`WНя{Я(Ў„зШЦµ«¶ЕЮ‰ЕJЁ4-
_)Y*›»ў°f]пґПБЁФ­
:‡М№јєї6>ь·…ЗSуPnvM-ЉfїyЬmџ]5ИУМ¦ЦJc4ѓ©”BЛлЫ"¦Ћzъ¤>ј„#ќг»IФТ]иDїt•#µб}$/\_tѕ‘oјuМuьэ1(фб•‰ћЪx%@Оd> МОµIPI‹0•ъїkІРbfЩЌ–IEВ«mB      }   
   xњ‹Сгвв Е ©      ‹   
   xњ‹Сгвв Е ©      ‰   
   xњ‹Сгвв Е ©      Ќ   
   xњ‹Сгвв Е ©      «   
   xњ‹Сгвв Е ©      ©   
   xњ‹Сгвв Е ©      н   
   xњ‹Сгвв Е ©      ™   ?   xњ3д4д4202У5°Р52R04·2µ°21У344ґґР60J'¦дfжAЙґўФTОґТњ®=... љµo      Џ   Ј   xњUЊM‚0 @ПЫЇиа-\Ыt:wЄ!нP$!„уЌ)%¦ї>ЎSјw{р8ЁЖ<ЛzиGрЦЄк&=мзr¬ѓ&
,*-B­ЖEџR("sЖ»`й'ПІ0ZРIТ¤є¦Ї»d5Д·\Ј1Ю№їk«•нJ‘юI1хlМmJ7Жs‘піЂm±у}Бёp=D0§њЇBшМh2:      Ў   
   xњ‹Сгвв Е ©      ќ   
   xњ‹Сгвв Е ©      m   
   xњ‹Сгвв Е ©      o   
   xњ‹Сгвв Е ©      q   
   xњ‹Сгвв Е ©      k   
   xњ‹Сгвв Е ©     