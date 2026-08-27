--
-- PostgreSQL database dump
--

-- Dumped from database version 16.6
-- Dumped by pg_dump version 16.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: admin_audit_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.admin_audit_log (
    id integer NOT NULL,
    admin_user_id integer NOT NULL,
    action character varying(120) NOT NULL,
    target_type character varying(80),
    target_id character varying(80),
    details_json jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.admin_audit_log OWNER TO postgres;

--
-- Name: admin_audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.admin_audit_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.admin_audit_log_id_seq OWNER TO postgres;

--
-- Name: admin_audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.admin_audit_log_id_seq OWNED BY public.admin_audit_log.id;


--
-- Name: ai_tasks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ai_tasks (
    id integer NOT NULL,
    user_id integer,
    task_type character varying(50) NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying,
    payload jsonb DEFAULT '{}'::jsonb,
    result jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    processed_at timestamp with time zone
);


ALTER TABLE public.ai_tasks OWNER TO postgres;

--
-- Name: ai_tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ai_tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ai_tasks_id_seq OWNER TO postgres;

--
-- Name: ai_tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ai_tasks_id_seq OWNED BY public.ai_tasks.id;


--
-- Name: billing_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.billing_events (
    id integer NOT NULL,
    provider character varying(32) NOT NULL,
    event_id character varying(255),
    event_type character varying(120) NOT NULL,
    payload_json jsonb,
    user_id integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.billing_events OWNER TO postgres;

--
-- Name: billing_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.billing_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.billing_events_id_seq OWNER TO postgres;

--
-- Name: billing_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.billing_events_id_seq OWNED BY public.billing_events.id;


--
-- Name: blacklisted_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.blacklisted_tokens (
    id integer NOT NULL,
    token character varying(500) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.blacklisted_tokens OWNER TO postgres;

--
-- Name: blacklisted_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.blacklisted_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.blacklisted_tokens_id_seq OWNER TO postgres;

--
-- Name: blacklisted_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.blacklisted_tokens_id_seq OWNED BY public.blacklisted_tokens.id;


--
-- Name: cpost_posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cpost_posts (
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


ALTER TABLE public.cpost_posts OWNER TO postgres;

--
-- Name: cpost_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.cpost_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cpost_posts_id_seq OWNER TO postgres;

--
-- Name: cpost_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.cpost_posts_id_seq OWNED BY public.cpost_posts.id;


--
-- Name: cpost_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cpost_profiles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    default_platforms jsonb DEFAULT '{"tg": false, "tw": false, "vk": false, "wp": false}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.cpost_profiles OWNER TO postgres;

--
-- Name: cpost_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.cpost_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cpost_profiles_id_seq OWNER TO postgres;

--
-- Name: cpost_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.cpost_profiles_id_seq OWNED BY public.cpost_profiles.id;


--
-- Name: curl_one_time_done; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.curl_one_time_done (
    id integer NOT NULL,
    user_id integer NOT NULL,
    url text NOT NULL,
    xpath text NOT NULL,
    executed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.curl_one_time_done OWNER TO postgres;

--
-- Name: curl_one_time_done_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.curl_one_time_done_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.curl_one_time_done_id_seq OWNER TO postgres;

--
-- Name: curl_one_time_done_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.curl_one_time_done_id_seq OWNED BY public.curl_one_time_done.id;


--
-- Name: curl_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.curl_settings (
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


ALTER TABLE public.curl_settings OWNER TO postgres;

--
-- Name: curl_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.curl_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.curl_settings_id_seq OWNER TO postgres;

--
-- Name: curl_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.curl_settings_id_seq OWNED BY public.curl_settings.id;


--
-- Name: dzen_posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dzen_posts (
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


ALTER TABLE public.dzen_posts OWNER TO postgres;

--
-- Name: dzen_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dzen_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dzen_posts_id_seq OWNER TO postgres;

--
-- Name: dzen_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dzen_posts_id_seq OWNED BY public.dzen_posts.id;


--
-- Name: dzen_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dzen_profiles (
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


ALTER TABLE public.dzen_profiles OWNER TO postgres;

--
-- Name: dzen_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dzen_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dzen_profiles_id_seq OWNER TO postgres;

--
-- Name: dzen_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dzen_profiles_id_seq OWNED BY public.dzen_profiles.id;


--
-- Name: email_verification_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.email_verification_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    token character varying(500) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.email_verification_tokens OWNER TO postgres;

--
-- Name: email_verification_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.email_verification_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.email_verification_tokens_id_seq OWNER TO postgres;

--
-- Name: email_verification_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.email_verification_tokens_id_seq OWNED BY public.email_verification_tokens.id;


--
-- Name: feedback; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.feedback (
    id integer NOT NULL,
    type character varying(50) NOT NULL,
    text text NOT NULL,
    email character varying(255),
    user_id integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT feedback_type_check CHECK (((type)::text = ANY ((ARRAY['bug_report'::character varying, 'suggestion'::character varying, 'contact_author'::character varying])::text[])))
);


ALTER TABLE public.feedback OWNER TO postgres;

--
-- Name: feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.feedback_id_seq OWNER TO postgres;

--
-- Name: feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.feedback_id_seq OWNED BY public.feedback.id;


--
-- Name: game_answers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_answers (
    id integer NOT NULL,
    session_id integer NOT NULL,
    question_id integer NOT NULL,
    selected_option_id integer,
    is_correct boolean NOT NULL,
    answered_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.game_answers OWNER TO postgres;

--
-- Name: game_answers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_answers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_answers_id_seq OWNER TO postgres;

--
-- Name: game_answers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_answers_id_seq OWNED BY public.game_answers.id;


--
-- Name: game_bots; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_bots (
    id integer NOT NULL,
    name text NOT NULL,
    token text NOT NULL,
    username text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.game_bots OWNER TO postgres;

--
-- Name: game_bots_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_bots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_bots_id_seq OWNER TO postgres;

--
-- Name: game_bots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_bots_id_seq OWNED BY public.game_bots.id;


--
-- Name: game_media_assets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_media_assets (
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


ALTER TABLE public.game_media_assets OWNER TO postgres;

--
-- Name: game_media_assets_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_media_assets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_media_assets_id_seq OWNER TO postgres;

--
-- Name: game_media_assets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_media_assets_id_seq OWNED BY public.game_media_assets.id;


--
-- Name: game_menu_cart_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_menu_cart_items (
    id integer NOT NULL,
    cart_id integer NOT NULL,
    node_id integer NOT NULL,
    quantity integer DEFAULT 1 NOT NULL,
    CONSTRAINT game_menu_cart_items_quantity_check CHECK ((quantity > 0))
);


ALTER TABLE public.game_menu_cart_items OWNER TO postgres;

--
-- Name: game_menu_cart_items_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_menu_cart_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_menu_cart_items_id_seq OWNER TO postgres;

--
-- Name: game_menu_cart_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_menu_cart_items_id_seq OWNED BY public.game_menu_cart_items.id;


--
-- Name: game_menu_carts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_menu_carts (
    id integer NOT NULL,
    bot_id integer NOT NULL,
    telegram_user_id bigint NOT NULL,
    mode_id integer NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.game_menu_carts OWNER TO postgres;

--
-- Name: game_menu_carts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_menu_carts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_menu_carts_id_seq OWNER TO postgres;

--
-- Name: game_menu_carts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_menu_carts_id_seq OWNED BY public.game_menu_carts.id;


--
-- Name: game_menu_nodes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_menu_nodes (
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


ALTER TABLE public.game_menu_nodes OWNER TO postgres;

--
-- Name: game_menu_nodes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_menu_nodes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_menu_nodes_id_seq OWNER TO postgres;

--
-- Name: game_menu_nodes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_menu_nodes_id_seq OWNED BY public.game_menu_nodes.id;


--
-- Name: game_menu_order_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_menu_order_items (
    id integer NOT NULL,
    order_id integer NOT NULL,
    node_id integer,
    title text NOT NULL,
    quantity integer NOT NULL,
    unit_price numeric(12,2) DEFAULT 0 NOT NULL,
    CONSTRAINT game_menu_order_items_quantity_check CHECK ((quantity > 0))
);


ALTER TABLE public.game_menu_order_items OWNER TO postgres;

--
-- Name: game_menu_order_items_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_menu_order_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_menu_order_items_id_seq OWNER TO postgres;

--
-- Name: game_menu_order_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_menu_order_items_id_seq OWNED BY public.game_menu_order_items.id;


--
-- Name: game_menu_orders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_menu_orders (
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


ALTER TABLE public.game_menu_orders OWNER TO postgres;

--
-- Name: game_menu_orders_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_menu_orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_menu_orders_id_seq OWNER TO postgres;

--
-- Name: game_menu_orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_menu_orders_id_seq OWNED BY public.game_menu_orders.id;


--
-- Name: game_modes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_modes (
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


ALTER TABLE public.game_modes OWNER TO postgres;

--
-- Name: game_modes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_modes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_modes_id_seq OWNER TO postgres;

--
-- Name: game_modes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_modes_id_seq OWNED BY public.game_modes.id;


--
-- Name: game_players; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_players (
    id integer NOT NULL,
    telegram_user_id bigint NOT NULL,
    bot_id integer,
    username text,
    first_name text,
    is_admin boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.game_players OWNER TO postgres;

--
-- Name: game_players_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_players_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_players_id_seq OWNER TO postgres;

--
-- Name: game_players_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_players_id_seq OWNED BY public.game_players.id;


--
-- Name: game_question_options; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_question_options (
    id integer NOT NULL,
    question_id integer NOT NULL,
    option_index smallint NOT NULL,
    option_text text NOT NULL,
    is_correct boolean DEFAULT false NOT NULL,
    CONSTRAINT game_question_options_option_index_check CHECK (((option_index >= 1) AND (option_index <= 6)))
);


ALTER TABLE public.game_question_options OWNER TO postgres;

--
-- Name: game_question_options_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_question_options_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_question_options_id_seq OWNER TO postgres;

--
-- Name: game_question_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_question_options_id_seq OWNED BY public.game_question_options.id;


--
-- Name: game_questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_questions (
    id integer NOT NULL,
    mode_id integer NOT NULL,
    prompt_text text NOT NULL,
    image_file_id text,
    image_url text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.game_questions OWNER TO postgres;

--
-- Name: game_questions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_questions_id_seq OWNER TO postgres;

--
-- Name: game_questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_questions_id_seq OWNED BY public.game_questions.id;


--
-- Name: game_session_questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_session_questions (
    id integer NOT NULL,
    session_id integer NOT NULL,
    step_index integer NOT NULL,
    question_id integer NOT NULL,
    CONSTRAINT game_session_questions_step_index_check CHECK ((step_index >= 0))
);


ALTER TABLE public.game_session_questions OWNER TO postgres;

--
-- Name: game_session_questions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_session_questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_session_questions_id_seq OWNER TO postgres;

--
-- Name: game_session_questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_session_questions_id_seq OWNED BY public.game_session_questions.id;


--
-- Name: game_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.game_sessions (
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


ALTER TABLE public.game_sessions OWNER TO postgres;

--
-- Name: game_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.game_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.game_sessions_id_seq OWNER TO postgres;

--
-- Name: game_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.game_sessions_id_seq OWNED BY public.game_sessions.id;


--
-- Name: group_members; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.group_members (
    id integer NOT NULL,
    group_id integer NOT NULL,
    user_id integer NOT NULL,
    role_in_group character varying(20) NOT NULL,
    joined_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT group_members_role_in_group_check CHECK (((role_in_group)::text = ANY ((ARRAY['admin'::character varying, 'editor'::character varying, 'analyst'::character varying])::text[])))
);


ALTER TABLE public.group_members OWNER TO postgres;

--
-- Name: group_members_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.group_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.group_members_id_seq OWNER TO postgres;

--
-- Name: group_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.group_members_id_seq OWNED BY public.group_members.id;


--
-- Name: groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.groups (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id integer
);


ALTER TABLE public.groups OWNER TO postgres;

--
-- Name: groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.groups_id_seq OWNER TO postgres;

--
-- Name: groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.groups_id_seq OWNED BY public.groups.id;


--
-- Name: guide_blocks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.guide_blocks (
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


ALTER TABLE public.guide_blocks OWNER TO postgres;

--
-- Name: guide_blocks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.guide_blocks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.guide_blocks_id_seq OWNER TO postgres;

--
-- Name: guide_blocks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.guide_blocks_id_seq OWNED BY public.guide_blocks.id;


--
-- Name: instagram_posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.instagram_posts (
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


ALTER TABLE public.instagram_posts OWNER TO postgres;

--
-- Name: instagram_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.instagram_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.instagram_posts_id_seq OWNER TO postgres;

--
-- Name: instagram_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.instagram_posts_id_seq OWNED BY public.instagram_posts.id;


--
-- Name: instagram_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.instagram_profiles (
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


ALTER TABLE public.instagram_profiles OWNER TO postgres;

--
-- Name: instagram_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.instagram_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.instagram_profiles_id_seq OWNER TO postgres;

--
-- Name: instagram_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.instagram_profiles_id_seq OWNED BY public.instagram_profiles.id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    message text NOT NULL,
    user_id integer,
    type character varying(50) DEFAULT 'general'::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notifications_id_seq OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: password_reset_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.password_reset_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    token character varying(500) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.password_reset_tokens OWNER TO postgres;

--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.password_reset_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.password_reset_tokens_id_seq OWNER TO postgres;

--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.password_reset_tokens_id_seq OWNED BY public.password_reset_tokens.id;


--
-- Name: plan_definitions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.plan_definitions (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    display_name character varying(120) NOT NULL,
    description text,
    limits_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    sort_order integer DEFAULT 0
);


ALTER TABLE public.plan_definitions OWNER TO postgres;

--
-- Name: plan_definitions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.plan_definitions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.plan_definitions_id_seq OWNER TO postgres;

--
-- Name: plan_definitions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.plan_definitions_id_seq OWNED BY public.plan_definitions.id;


--
-- Name: posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.posts (
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


ALTER TABLE public.posts OWNER TO postgres;

--
-- Name: posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.posts_id_seq OWNER TO postgres;

--
-- Name: posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.posts_id_seq OWNED BY public.posts.id;


--
-- Name: refresh_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.refresh_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    token character varying(500) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.refresh_tokens OWNER TO postgres;

--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.refresh_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.refresh_tokens_id_seq OWNER TO postgres;

--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.refresh_tokens_id_seq OWNED BY public.refresh_tokens.id;


--
-- Name: service_cycle_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.service_cycle_log (
    id integer NOT NULL,
    service_name character varying(50) NOT NULL,
    cycle_type character varying(50) NOT NULL,
    status character varying(20) DEFAULT 'ok'::character varying,
    detail text,
    items_processed integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.service_cycle_log OWNER TO postgres;

--
-- Name: service_cycle_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.service_cycle_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.service_cycle_log_id_seq OWNER TO postgres;

--
-- Name: service_cycle_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.service_cycle_log_id_seq OWNED BY public.service_cycle_log.id;


--
-- Name: smm_ai_usage; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.smm_ai_usage (
    user_id integer NOT NULL,
    month character(7) NOT NULL,
    calls integer DEFAULT 0
);


ALTER TABLE public.smm_ai_usage OWNER TO postgres;

--
-- Name: smm_automations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.smm_automations (
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


ALTER TABLE public.smm_automations OWNER TO postgres;

--
-- Name: smm_automations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.smm_automations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.smm_automations_id_seq OWNER TO postgres;

--
-- Name: smm_automations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.smm_automations_id_seq OWNED BY public.smm_automations.id;


--
-- Name: smm_brand_channels; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.smm_brand_channels (
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


ALTER TABLE public.smm_brand_channels OWNER TO postgres;

--
-- Name: smm_brand_channels_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.smm_brand_channels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.smm_brand_channels_id_seq OWNER TO postgres;

--
-- Name: smm_brand_channels_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.smm_brand_channels_id_seq OWNED BY public.smm_brand_channels.id;


--
-- Name: smm_brands; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.smm_brands (
    id integer NOT NULL,
    user_id integer NOT NULL,
    group_id integer,
    name character varying(255) NOT NULL,
    color character varying(7) DEFAULT '#3B82F6'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.smm_brands OWNER TO postgres;

--
-- Name: smm_brands_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.smm_brands_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.smm_brands_id_seq OWNER TO postgres;

--
-- Name: smm_brands_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.smm_brands_id_seq OWNED BY public.smm_brands.id;


--
-- Name: smm_channel_counters; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.smm_channel_counters (
    id integer NOT NULL,
    user_id integer NOT NULL,
    channel_id integer NOT NULL,
    day date NOT NULL,
    sent integer DEFAULT 0,
    received integer DEFAULT 0,
    failed integer DEFAULT 0,
    alerts_sent integer DEFAULT 0
);


ALTER TABLE public.smm_channel_counters OWNER TO postgres;

--
-- Name: smm_channel_counters_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.smm_channel_counters_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.smm_channel_counters_id_seq OWNER TO postgres;

--
-- Name: smm_channel_counters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.smm_channel_counters_id_seq OWNED BY public.smm_channel_counters.id;


--
-- Name: smm_channel_metric_snapshots; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.smm_channel_metric_snapshots (
    id integer NOT NULL,
    channel_id integer NOT NULL,
    subscribers integer DEFAULT 0,
    captured_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.smm_channel_metric_snapshots OWNER TO postgres;

--
-- Name: smm_channel_metric_snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.smm_channel_metric_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.smm_channel_metric_snapshots_id_seq OWNER TO postgres;

--
-- Name: smm_channel_metric_snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.smm_channel_metric_snapshots_id_seq OWNED BY public.smm_channel_metric_snapshots.id;


--
-- Name: smm_competitor_snapshots; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.smm_competitor_snapshots (
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


ALTER TABLE public.smm_competitor_snapshots OWNER TO postgres;

--
-- Name: smm_competitor_snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.smm_competitor_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.smm_competitor_snapshots_id_seq OWNER TO postgres;

--
-- Name: smm_competitor_snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.smm_competitor_snapshots_id_seq OWNED BY public.smm_competitor_snapshots.id;


--
-- Name: smm_inbox_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.smm_inbox_items (
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


ALTER TABLE public.smm_inbox_items OWNER TO postgres;

--
-- Name: smm_inbox_items_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.smm_inbox_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.smm_inbox_items_id_seq OWNER TO postgres;

--
-- Name: smm_inbox_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.smm_inbox_items_id_seq OWNED BY public.smm_inbox_items.id;


--
-- Name: smm_message_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.smm_message_events (
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


ALTER TABLE public.smm_message_events OWNER TO postgres;

--
-- Name: smm_message_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.smm_message_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.smm_message_events_id_seq OWNER TO postgres;

--
-- Name: smm_message_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.smm_message_events_id_seq OWNED BY public.smm_message_events.id;


--
-- Name: smm_post_metric_snapshots; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.smm_post_metric_snapshots (
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


ALTER TABLE public.smm_post_metric_snapshots OWNER TO postgres;

--
-- Name: smm_post_metric_snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.smm_post_metric_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.smm_post_metric_snapshots_id_seq OWNER TO postgres;

--
-- Name: smm_post_metric_snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.smm_post_metric_snapshots_id_seq OWNED BY public.smm_post_metric_snapshots.id;


--
-- Name: smm_publish_jobs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.smm_publish_jobs (
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


ALTER TABLE public.smm_publish_jobs OWNER TO postgres;

--
-- Name: smm_publish_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.smm_publish_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.smm_publish_jobs_id_seq OWNER TO postgres;

--
-- Name: smm_publish_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.smm_publish_jobs_id_seq OWNED BY public.smm_publish_jobs.id;


--
-- Name: system_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.system_settings (
    key character varying(100) NOT NULL,
    value jsonb NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.system_settings OWNER TO postgres;

--
-- Name: tg_dedup_cache; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tg_dedup_cache (
    id integer NOT NULL,
    user_id integer NOT NULL,
    text_hash character varying(64) NOT NULL,
    chat_id bigint NOT NULL,
    rule_id character varying(64),
    channel_to_post character varying(50),
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tg_dedup_cache OWNER TO postgres;

--
-- Name: tg_dedup_cache_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tg_dedup_cache_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tg_dedup_cache_id_seq OWNER TO postgres;

--
-- Name: tg_dedup_cache_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tg_dedup_cache_id_seq OWNED BY public.tg_dedup_cache.id;


--
-- Name: tg_digests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tg_digests (
    id integer NOT NULL,
    user_id integer NOT NULL,
    chat_id bigint NOT NULL,
    digest_text text NOT NULL,
    message_count integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tg_digests OWNER TO postgres;

--
-- Name: tg_digests_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tg_digests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tg_digests_id_seq OWNER TO postgres;

--
-- Name: tg_digests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tg_digests_id_seq OWNED BY public.tg_digests.id;


--
-- Name: tg_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tg_events (
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


ALTER TABLE public.tg_events OWNER TO postgres;

--
-- Name: tg_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tg_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tg_events_id_seq OWNER TO postgres;

--
-- Name: tg_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tg_events_id_seq OWNED BY public.tg_events.id;


--
-- Name: tg_post_templates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tg_post_templates (
    id integer NOT NULL,
    user_id integer NOT NULL,
    name character varying(200) NOT NULL,
    text text DEFAULT ''::text NOT NULL,
    hashtags text DEFAULT ''::text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tg_post_templates OWNER TO postgres;

--
-- Name: tg_post_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tg_post_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tg_post_templates_id_seq OWNER TO postgres;

--
-- Name: tg_post_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tg_post_templates_id_seq OWNED BY public.tg_post_templates.id;


--
-- Name: tg_posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tg_posts (
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


ALTER TABLE public.tg_posts OWNER TO postgres;

--
-- Name: tg_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tg_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tg_posts_id_seq OWNER TO postgres;

--
-- Name: tg_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tg_posts_id_seq OWNED BY public.tg_posts.id;


--
-- Name: tg_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tg_profiles (
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
    classification_categories jsonb DEFAULT '["новости", "реклама", "технологии", "финансы", "другое"]'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tg_profiles OWNER TO postgres;

--
-- Name: tg_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tg_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tg_profiles_id_seq OWNER TO postgres;

--
-- Name: tg_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tg_profiles_id_seq OWNED BY public.tg_profiles.id;


--
-- Name: tg_summary_cache; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tg_summary_cache (
    id integer NOT NULL,
    text_hash character varying(64) NOT NULL,
    summary text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.tg_summary_cache OWNER TO postgres;

--
-- Name: tg_summary_cache_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tg_summary_cache_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tg_summary_cache_id_seq OWNER TO postgres;

--
-- Name: tg_summary_cache_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tg_summary_cache_id_seq OWNED BY public.tg_summary_cache.id;


--
-- Name: threads_posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.threads_posts (
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


ALTER TABLE public.threads_posts OWNER TO postgres;

--
-- Name: threads_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.threads_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.threads_posts_id_seq OWNER TO postgres;

--
-- Name: threads_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.threads_posts_id_seq OWNED BY public.threads_posts.id;


--
-- Name: threads_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.threads_profiles (
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


ALTER TABLE public.threads_profiles OWNER TO postgres;

--
-- Name: threads_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.threads_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.threads_profiles_id_seq OWNER TO postgres;

--
-- Name: threads_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.threads_profiles_id_seq OWNED BY public.threads_profiles.id;


--
-- Name: threads_selenium_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.threads_selenium_sessions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    status character varying(40) NOT NULL,
    detail_message text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.threads_selenium_sessions OWNER TO postgres;

--
-- Name: threads_selenium_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.threads_selenium_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.threads_selenium_sessions_id_seq OWNER TO postgres;

--
-- Name: threads_selenium_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.threads_selenium_sessions_id_seq OWNED BY public.threads_selenium_sessions.id;


--
-- Name: tw_posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tw_posts (
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


ALTER TABLE public.tw_posts OWNER TO postgres;

--
-- Name: tw_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tw_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tw_posts_id_seq OWNER TO postgres;

--
-- Name: tw_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tw_posts_id_seq OWNED BY public.tw_posts.id;


--
-- Name: tw_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tw_profiles (
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


ALTER TABLE public.tw_profiles OWNER TO postgres;

--
-- Name: tw_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tw_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tw_profiles_id_seq OWNER TO postgres;

--
-- Name: tw_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tw_profiles_id_seq OWNED BY public.tw_profiles.id;


--
-- Name: url_posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.url_posts (
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


ALTER TABLE public.url_posts OWNER TO postgres;

--
-- Name: url_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.url_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.url_posts_id_seq OWNER TO postgres;

--
-- Name: url_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.url_posts_id_seq OWNED BY public.url_posts.id;


--
-- Name: user_role_tariff_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_role_tariff_history (
    id integer NOT NULL,
    user_id integer NOT NULL,
    changed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    changed_by_user_id integer,
    role_old character varying(20),
    role_new character varying(20),
    tariff_old character varying(50),
    tariff_new character varying(50)
);


ALTER TABLE public.user_role_tariff_history OWNER TO postgres;

--
-- Name: user_role_tariff_history_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_role_tariff_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_role_tariff_history_id_seq OWNER TO postgres;

--
-- Name: user_role_tariff_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_role_tariff_history_id_seq OWNED BY public.user_role_tariff_history.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
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


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: vk_posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vk_posts (
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


ALTER TABLE public.vk_posts OWNER TO postgres;

--
-- Name: vk_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vk_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vk_posts_id_seq OWNER TO postgres;

--
-- Name: vk_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vk_posts_id_seq OWNED BY public.vk_posts.id;


--
-- Name: vk_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vk_profiles (
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


ALTER TABLE public.vk_profiles OWNER TO postgres;

--
-- Name: vk_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vk_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vk_profiles_id_seq OWNER TO postgres;

--
-- Name: vk_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vk_profiles_id_seq OWNED BY public.vk_profiles.id;


--
-- Name: wp_collect_profile; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wp_collect_profile (
    id integer NOT NULL,
    user_id integer NOT NULL,
    collect_enabled boolean DEFAULT false,
    collect_all_available boolean DEFAULT true,
    collect_limit integer DEFAULT 1,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.wp_collect_profile OWNER TO postgres;

--
-- Name: wp_collect_profile_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wp_collect_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wp_collect_profile_id_seq OWNER TO postgres;

--
-- Name: wp_collect_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wp_collect_profile_id_seq OWNED BY public.wp_collect_profile.id;


--
-- Name: wp_collect_sites; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wp_collect_sites (
    id integer NOT NULL,
    profile_id integer NOT NULL,
    user_id integer NOT NULL,
    site_url text,
    schedule_type character varying(50) DEFAULT 'on_new_messages'::character varying,
    time_intervals character varying(5),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.wp_collect_sites OWNER TO postgres;

--
-- Name: wp_collect_sites_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wp_collect_sites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wp_collect_sites_id_seq OWNER TO postgres;

--
-- Name: wp_collect_sites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wp_collect_sites_id_seq OWNED BY public.wp_collect_sites.id;


--
-- Name: wp_posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wp_posts (
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


ALTER TABLE public.wp_posts OWNER TO postgres;

--
-- Name: wp_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wp_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wp_posts_id_seq OWNER TO postgres;

--
-- Name: wp_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wp_posts_id_seq OWNED BY public.wp_posts.id;


--
-- Name: wp_publish_profile; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wp_publish_profile (
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


ALTER TABLE public.wp_publish_profile OWNER TO postgres;

--
-- Name: wp_publish_profile_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.wp_publish_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wp_publish_profile_id_seq OWNER TO postgres;

--
-- Name: wp_publish_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.wp_publish_profile_id_seq OWNED BY public.wp_publish_profile.id;


--
-- Name: admin_audit_log id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin_audit_log ALTER COLUMN id SET DEFAULT nextval('public.admin_audit_log_id_seq'::regclass);


--
-- Name: ai_tasks id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_tasks ALTER COLUMN id SET DEFAULT nextval('public.ai_tasks_id_seq'::regclass);


--
-- Name: billing_events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.billing_events ALTER COLUMN id SET DEFAULT nextval('public.billing_events_id_seq'::regclass);


--
-- Name: blacklisted_tokens id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.blacklisted_tokens ALTER COLUMN id SET DEFAULT nextval('public.blacklisted_tokens_id_seq'::regclass);


--
-- Name: cpost_posts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cpost_posts ALTER COLUMN id SET DEFAULT nextval('public.cpost_posts_id_seq'::regclass);


--
-- Name: cpost_profiles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cpost_profiles ALTER COLUMN id SET DEFAULT nextval('public.cpost_profiles_id_seq'::regclass);


--
-- Name: curl_one_time_done id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.curl_one_time_done ALTER COLUMN id SET DEFAULT nextval('public.curl_one_time_done_id_seq'::regclass);


--
-- Name: curl_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.curl_settings ALTER COLUMN id SET DEFAULT nextval('public.curl_settings_id_seq'::regclass);


--
-- Name: dzen_posts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dzen_posts ALTER COLUMN id SET DEFAULT nextval('public.dzen_posts_id_seq'::regclass);


--
-- Name: dzen_profiles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dzen_profiles ALTER COLUMN id SET DEFAULT nextval('public.dzen_profiles_id_seq'::regclass);


--
-- Name: email_verification_tokens id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_verification_tokens ALTER COLUMN id SET DEFAULT nextval('public.email_verification_tokens_id_seq'::regclass);


--
-- Name: feedback id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feedback ALTER COLUMN id SET DEFAULT nextval('public.feedback_id_seq'::regclass);


--
-- Name: game_answers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_answers ALTER COLUMN id SET DEFAULT nextval('public.game_answers_id_seq'::regclass);


--
-- Name: game_bots id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_bots ALTER COLUMN id SET DEFAULT nextval('public.game_bots_id_seq'::regclass);


--
-- Name: game_media_assets id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_media_assets ALTER COLUMN id SET DEFAULT nextval('public.game_media_assets_id_seq'::regclass);


--
-- Name: game_menu_cart_items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_cart_items ALTER COLUMN id SET DEFAULT nextval('public.game_menu_cart_items_id_seq'::regclass);


--
-- Name: game_menu_carts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_carts ALTER COLUMN id SET DEFAULT nextval('public.game_menu_carts_id_seq'::regclass);


--
-- Name: game_menu_nodes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_nodes ALTER COLUMN id SET DEFAULT nextval('public.game_menu_nodes_id_seq'::regclass);


--
-- Name: game_menu_order_items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_order_items ALTER COLUMN id SET DEFAULT nextval('public.game_menu_order_items_id_seq'::regclass);


--
-- Name: game_menu_orders id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_orders ALTER COLUMN id SET DEFAULT nextval('public.game_menu_orders_id_seq'::regclass);


--
-- Name: game_modes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_modes ALTER COLUMN id SET DEFAULT nextval('public.game_modes_id_seq'::regclass);


--
-- Name: game_players id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_players ALTER COLUMN id SET DEFAULT nextval('public.game_players_id_seq'::regclass);


--
-- Name: game_question_options id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_question_options ALTER COLUMN id SET DEFAULT nextval('public.game_question_options_id_seq'::regclass);


--
-- Name: game_questions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_questions ALTER COLUMN id SET DEFAULT nextval('public.game_questions_id_seq'::regclass);


--
-- Name: game_session_questions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_session_questions ALTER COLUMN id SET DEFAULT nextval('public.game_session_questions_id_seq'::regclass);


--
-- Name: game_sessions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_sessions ALTER COLUMN id SET DEFAULT nextval('public.game_sessions_id_seq'::regclass);


--
-- Name: group_members id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_members ALTER COLUMN id SET DEFAULT nextval('public.group_members_id_seq'::regclass);


--
-- Name: groups id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.groups ALTER COLUMN id SET DEFAULT nextval('public.groups_id_seq'::regclass);


--
-- Name: guide_blocks id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guide_blocks ALTER COLUMN id SET DEFAULT nextval('public.guide_blocks_id_seq'::regclass);


--
-- Name: instagram_posts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.instagram_posts ALTER COLUMN id SET DEFAULT nextval('public.instagram_posts_id_seq'::regclass);


--
-- Name: instagram_profiles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.instagram_profiles ALTER COLUMN id SET DEFAULT nextval('public.instagram_profiles_id_seq'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: password_reset_tokens id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.password_reset_tokens ALTER COLUMN id SET DEFAULT nextval('public.password_reset_tokens_id_seq'::regclass);


--
-- Name: plan_definitions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plan_definitions ALTER COLUMN id SET DEFAULT nextval('public.plan_definitions_id_seq'::regclass);


--
-- Name: posts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts ALTER COLUMN id SET DEFAULT nextval('public.posts_id_seq'::regclass);


--
-- Name: refresh_tokens id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.refresh_tokens ALTER COLUMN id SET DEFAULT nextval('public.refresh_tokens_id_seq'::regclass);


--
-- Name: service_cycle_log id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service_cycle_log ALTER COLUMN id SET DEFAULT nextval('public.service_cycle_log_id_seq'::regclass);


--
-- Name: smm_automations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_automations ALTER COLUMN id SET DEFAULT nextval('public.smm_automations_id_seq'::regclass);


--
-- Name: smm_brand_channels id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_brand_channels ALTER COLUMN id SET DEFAULT nextval('public.smm_brand_channels_id_seq'::regclass);


--
-- Name: smm_brands id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_brands ALTER COLUMN id SET DEFAULT nextval('public.smm_brands_id_seq'::regclass);


--
-- Name: smm_channel_counters id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_channel_counters ALTER COLUMN id SET DEFAULT nextval('public.smm_channel_counters_id_seq'::regclass);


--
-- Name: smm_channel_metric_snapshots id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_channel_metric_snapshots ALTER COLUMN id SET DEFAULT nextval('public.smm_channel_metric_snapshots_id_seq'::regclass);


--
-- Name: smm_competitor_snapshots id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_competitor_snapshots ALTER COLUMN id SET DEFAULT nextval('public.smm_competitor_snapshots_id_seq'::regclass);


--
-- Name: smm_inbox_items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_inbox_items ALTER COLUMN id SET DEFAULT nextval('public.smm_inbox_items_id_seq'::regclass);


--
-- Name: smm_message_events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_message_events ALTER COLUMN id SET DEFAULT nextval('public.smm_message_events_id_seq'::regclass);


--
-- Name: smm_post_metric_snapshots id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_post_metric_snapshots ALTER COLUMN id SET DEFAULT nextval('public.smm_post_metric_snapshots_id_seq'::regclass);


--
-- Name: smm_publish_jobs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_publish_jobs ALTER COLUMN id SET DEFAULT nextval('public.smm_publish_jobs_id_seq'::regclass);


--
-- Name: tg_dedup_cache id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_dedup_cache ALTER COLUMN id SET DEFAULT nextval('public.tg_dedup_cache_id_seq'::regclass);


--
-- Name: tg_digests id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_digests ALTER COLUMN id SET DEFAULT nextval('public.tg_digests_id_seq'::regclass);


--
-- Name: tg_events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_events ALTER COLUMN id SET DEFAULT nextval('public.tg_events_id_seq'::regclass);


--
-- Name: tg_post_templates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_post_templates ALTER COLUMN id SET DEFAULT nextval('public.tg_post_templates_id_seq'::regclass);


--
-- Name: tg_posts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_posts ALTER COLUMN id SET DEFAULT nextval('public.tg_posts_id_seq'::regclass);


--
-- Name: tg_profiles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_profiles ALTER COLUMN id SET DEFAULT nextval('public.tg_profiles_id_seq'::regclass);


--
-- Name: tg_summary_cache id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_summary_cache ALTER COLUMN id SET DEFAULT nextval('public.tg_summary_cache_id_seq'::regclass);


--
-- Name: threads_posts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.threads_posts ALTER COLUMN id SET DEFAULT nextval('public.threads_posts_id_seq'::regclass);


--
-- Name: threads_profiles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.threads_profiles ALTER COLUMN id SET DEFAULT nextval('public.threads_profiles_id_seq'::regclass);


--
-- Name: threads_selenium_sessions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.threads_selenium_sessions ALTER COLUMN id SET DEFAULT nextval('public.threads_selenium_sessions_id_seq'::regclass);


--
-- Name: tw_posts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tw_posts ALTER COLUMN id SET DEFAULT nextval('public.tw_posts_id_seq'::regclass);


--
-- Name: tw_profiles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tw_profiles ALTER COLUMN id SET DEFAULT nextval('public.tw_profiles_id_seq'::regclass);


--
-- Name: url_posts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.url_posts ALTER COLUMN id SET DEFAULT nextval('public.url_posts_id_seq'::regclass);


--
-- Name: user_role_tariff_history id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_role_tariff_history ALTER COLUMN id SET DEFAULT nextval('public.user_role_tariff_history_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: vk_posts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vk_posts ALTER COLUMN id SET DEFAULT nextval('public.vk_posts_id_seq'::regclass);


--
-- Name: vk_profiles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vk_profiles ALTER COLUMN id SET DEFAULT nextval('public.vk_profiles_id_seq'::regclass);


--
-- Name: wp_collect_profile id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wp_collect_profile ALTER COLUMN id SET DEFAULT nextval('public.wp_collect_profile_id_seq'::regclass);


--
-- Name: wp_collect_sites id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wp_collect_sites ALTER COLUMN id SET DEFAULT nextval('public.wp_collect_sites_id_seq'::regclass);


--
-- Name: wp_posts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wp_posts ALTER COLUMN id SET DEFAULT nextval('public.wp_posts_id_seq'::regclass);


--
-- Name: wp_publish_profile id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wp_publish_profile ALTER COLUMN id SET DEFAULT nextval('public.wp_publish_profile_id_seq'::regclass);


--
-- Data for Name: admin_audit_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.admin_audit_log (id, admin_user_id, action, target_type, target_id, details_json, created_at) FROM stdin;
1	1	user_admin_update	user	1	{"role": "admin", "tariff": "full", "is_blocked": null}	2026-08-22 17:58:46.114669+03
\.


--
-- Data for Name: ai_tasks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ai_tasks (id, user_id, task_type, status, payload, result, created_at, processed_at) FROM stdin;
\.


--
-- Data for Name: billing_events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.billing_events (id, provider, event_id, event_type, payload_json, user_id, created_at) FROM stdin;
\.


--
-- Data for Name: blacklisted_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.blacklisted_tokens (id, token, expires_at, created_at) FROM stdin;
\.


--
-- Data for Name: cpost_posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cpost_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: cpost_profiles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cpost_profiles (id, user_id, default_platforms, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: curl_one_time_done; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.curl_one_time_done (id, user_id, url, xpath, executed_at) FROM stdin;
\.


--
-- Data for Name: curl_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.curl_settings (id, user_id, collect_enabled, schedule_type, time_intervals, url, xpath, take_screenshot, to_tg, to_tw, to_vk, to_wp, urls, process_before_publish, process_description, remove_emojis, remove_images, clean_html, process_services, status_review_after_process, add_static_html, static_html_content, screenshot_only, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: dzen_posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.dzen_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, videos, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: dzen_profiles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.dzen_profiles (id, user_id, publish_enabled, collect_enabled, schedule_type, time_intervals, rss_feed_url, channel_name, channels_to_read, rss_token, yandex_login, yandex_password, dzen_studio_url, collect_source, last_auth_error, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: email_verification_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.email_verification_tokens (id, user_id, token, expires_at, created_at) FROM stdin;
1	1	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ0eXBlIjoiZW1haWxfdmVyaWZpY2F0aW9uIiwiZXhwIjoxNzg3NDcxNzU0fQ.I9AHBciD3hWJx3XGaz-k9-eILevPUh3Hp204Gc4FDLQ	2026-08-23 07:55:54+03	2026-08-22 10:55:54.784545+03
\.


--
-- Data for Name: feedback; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.feedback (id, type, text, email, user_id, created_at) FROM stdin;
\.


--
-- Data for Name: game_answers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_answers (id, session_id, question_id, selected_option_id, is_correct, answered_at) FROM stdin;
\.


--
-- Data for Name: game_bots; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_bots (id, name, token, username, is_active, created_at) FROM stdin;
\.


--
-- Data for Name: game_media_assets; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_media_assets (id, filename, s3_key, original_filename, title, description, content_type, size_bytes, created_at) FROM stdin;
\.


--
-- Data for Name: game_menu_cart_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_menu_cart_items (id, cart_id, node_id, quantity) FROM stdin;
\.


--
-- Data for Name: game_menu_carts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_menu_carts (id, bot_id, telegram_user_id, mode_id, updated_at) FROM stdin;
\.


--
-- Data for Name: game_menu_nodes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_menu_nodes (id, mode_id, parent_id, title, body_text, image_url, image_file_id, sort_order, is_active, created_at, price) FROM stdin;
\.


--
-- Data for Name: game_menu_order_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_menu_order_items (id, order_id, node_id, title, quantity, unit_price) FROM stdin;
\.


--
-- Data for Name: game_menu_orders; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_menu_orders (id, order_number, bot_id, mode_id, telegram_user_id, username, first_name, status, created_at, total_amount) FROM stdin;
\.


--
-- Data for Name: game_modes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_modes (id, code, title, is_active, questions_per_game, bot_id, created_at, mode_type) FROM stdin;
1	demo	Демо-режим	t	3	\N	2026-08-22 10:54:07.96934+03	quiz
\.


--
-- Data for Name: game_players; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_players (id, telegram_user_id, bot_id, username, first_name, is_admin, created_at) FROM stdin;
\.


--
-- Data for Name: game_question_options; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_question_options (id, question_id, option_index, option_text, is_correct) FROM stdin;
\.


--
-- Data for Name: game_questions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_questions (id, mode_id, prompt_text, image_file_id, image_url, is_active, created_at) FROM stdin;
\.


--
-- Data for Name: game_session_questions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_session_questions (id, session_id, step_index, question_id) FROM stdin;
\.


--
-- Data for Name: game_sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.game_sessions (id, player_id, mode_id, status, score, correct_count, total_questions, current_step, started_at, finished_at, duration_sec) FROM stdin;
\.


--
-- Data for Name: group_members; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.group_members (id, group_id, user_id, role_in_group, joined_at) FROM stdin;
\.


--
-- Data for Name: groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.groups (id, name, description, created_at, created_by_user_id) FROM stdin;
\.


--
-- Data for Name: guide_blocks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.guide_blocks (id, slug, toc_label, title, subtitle, body, sort_order, is_visible, style, updated_at) FROM stdin;
\.


--
-- Data for Name: instagram_posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.instagram_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, instagram_source_id, videos, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: instagram_profiles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.instagram_profiles (id, user_id, publish_enabled, collect_enabled, schedule_type, time_intervals, username, password, usernames_to_read, process_enabled, processing_description, remove_emojis, remove_images, clean_html, process_services, status_review_after_process, add_static_html, static_html_content, instagrapi_session, instagram_verification_code, instagram_last_auth_error, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notifications (id, message, user_id, type, created_at) FROM stdin;
1	Telegram авторизация: код подтверждения отправлен на номер +79265990443. <a href="/telegram?auth=1" style="color:#60a5fa;text-decoration:underline">Введите код на странице Telegram</a>.	1	tg_auth_code	2026-08-22 22:16:36.750557+03
\.


--
-- Data for Name: password_reset_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.password_reset_tokens (id, user_id, token, expires_at, created_at) FROM stdin;
\.


--
-- Data for Name: plan_definitions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.plan_definitions (id, code, display_name, description, limits_json, sort_order) FROM stdin;
\.


--
-- Data for Name: posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, source_platform, source_id, platform_texts, videos, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: refresh_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.refresh_tokens (id, user_id, token, expires_at, created_at) FROM stdin;
7	1	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJyb2xlIjoiZ3Vlc3QiLCJ0eXBlIjoicmVmcmVzaCIsImlhdCI6MTc4NzM5MjU2MywiZXhwIjoxNzg3OTk3MzYzfQ.BpmtXq3PEjBjSJxiccdoa_ExX0DLXoMAZlIRHV2rl5g	2026-08-29 09:56:03+03	2026-08-22 12:56:03.151785+03
14	1	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJyb2xlIjoiYWRtaW4iLCJ0eXBlIjoicmVmcmVzaCIsImlhdCI6MTc4NzQxNzc2MywiZXhwIjoxNzg4MDIyNTYzfQ.ZcxYci-uVV79ZnXxheiai28NmIXUduy0y14CxGnYo5k	2026-08-29 16:56:03+03	2026-08-22 19:56:03.205652+03
20	1	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJyb2xlIjoiYWRtaW4iLCJ0eXBlIjoicmVmcmVzaCIsImlhdCI6MTc4NzQyNzc5NiwiZXhwIjoxNzg4MDMyNTk2fQ.XVv2U0jfC-KscbXwkCpsSgZmhGjXjpzbMehtVd1_Bts	2026-08-29 19:43:16+03	2026-08-22 22:43:16.950818+03
\.


--
-- Data for Name: service_cycle_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.service_cycle_log (id, service_name, cycle_type, status, detail, items_processed, created_at) FROM stdin;
1	processor	process	ok	\N	0	2026-08-22 10:54:33.998532+03
2	processor	process	ok	\N	0	2026-08-22 10:55:04.009415+03
3	collector	collect	ok	\N	0	2026-08-22 10:55:04.582889+03
4	processor	process	ok	\N	0	2026-08-22 10:55:34.021511+03
5	processor	process	ok	\N	0	2026-08-22 10:56:04.037282+03
6	collector	collect	ok	\N	0	2026-08-22 10:56:04.600548+03
7	processor	process	ok	\N	0	2026-08-22 10:56:34.042229+03
8	processor	process	ok	\N	0	2026-08-22 10:57:04.048653+03
9	collector	collect	ok	\N	0	2026-08-22 10:57:04.617396+03
10	processor	process	ok	\N	0	2026-08-22 10:57:34.054662+03
11	processor	process	ok	\N	0	2026-08-22 10:58:04.061772+03
12	collector	collect	ok	\N	0	2026-08-22 10:58:04.635043+03
13	processor	process	ok	\N	0	2026-08-22 10:58:34.07014+03
14	processor	process	ok	\N	0	2026-08-22 10:59:04.077242+03
15	collector	collect	ok	\N	0	2026-08-22 10:59:04.655427+03
16	processor	process	ok	\N	0	2026-08-22 10:59:34.084146+03
17	processor	process	ok	\N	0	2026-08-22 11:00:04.090905+03
18	collector	collect	ok	\N	0	2026-08-22 11:00:04.673136+03
19	processor	process	ok	\N	0	2026-08-22 11:00:34.09713+03
20	processor	process	ok	\N	0	2026-08-22 11:01:04.10163+03
21	collector	collect	ok	\N	0	2026-08-22 11:01:04.694421+03
22	processor	process	ok	\N	0	2026-08-22 11:01:34.107702+03
23	processor	process	ok	\N	0	2026-08-22 11:02:04.114276+03
24	collector	collect	ok	\N	0	2026-08-22 11:02:04.716143+03
25	processor	process	ok	\N	0	2026-08-22 11:02:34.120143+03
26	processor	process	ok	\N	0	2026-08-22 11:03:04.127325+03
27	collector	collect	ok	\N	0	2026-08-22 11:03:04.737938+03
28	processor	process	ok	\N	0	2026-08-22 11:03:34.130685+03
29	processor	process	ok	\N	0	2026-08-22 11:04:04.135866+03
30	collector	collect	ok	\N	0	2026-08-22 11:04:04.760917+03
31	processor	process	ok	\N	0	2026-08-22 11:04:34.13952+03
32	processor	process	ok	\N	0	2026-08-22 11:05:04.146959+03
33	collector	collect	ok	\N	0	2026-08-22 11:05:04.791187+03
34	processor	process	ok	\N	0	2026-08-22 11:05:34.154552+03
35	processor	process	ok	\N	0	2026-08-22 11:06:04.158701+03
36	collector	collect	ok	\N	0	2026-08-22 11:06:04.822939+03
37	processor	process	ok	\N	0	2026-08-22 11:06:34.164166+03
38	processor	process	ok	\N	0	2026-08-22 11:07:04.172592+03
39	collector	collect	ok	\N	0	2026-08-22 11:07:04.852493+03
40	processor	process	ok	\N	0	2026-08-22 11:07:34.17957+03
41	processor	process	ok	\N	0	2026-08-22 11:08:04.183387+03
42	collector	collect	ok	\N	0	2026-08-22 11:08:04.883229+03
43	processor	process	ok	\N	0	2026-08-22 11:08:34.190273+03
44	processor	process	ok	\N	0	2026-08-22 11:09:04.196963+03
45	collector	collect	ok	\N	0	2026-08-22 11:09:04.908728+03
46	processor	process	ok	\N	0	2026-08-22 11:09:34.203845+03
47	processor	process	ok	\N	0	2026-08-22 11:10:04.210814+03
48	collector	collect	ok	\N	0	2026-08-22 11:10:04.945953+03
49	processor	process	ok	\N	0	2026-08-22 11:10:34.217809+03
50	processor	process	ok	\N	0	2026-08-22 11:11:04.224357+03
51	collector	collect	ok	\N	0	2026-08-22 11:11:04.971016+03
52	processor	process	ok	\N	0	2026-08-22 11:11:34.232116+03
53	processor	process	ok	\N	0	2026-08-22 11:12:04.237903+03
54	collector	collect	ok	\N	0	2026-08-22 11:12:04.999363+03
55	processor	process	ok	\N	0	2026-08-22 11:12:34.244759+03
56	processor	process	ok	\N	0	2026-08-22 11:13:04.253217+03
57	collector	collect	ok	\N	0	2026-08-22 11:13:05.022854+03
58	processor	process	ok	\N	0	2026-08-22 11:13:34.260849+03
59	processor	process	ok	\N	0	2026-08-22 11:14:04.266661+03
60	collector	collect	ok	\N	0	2026-08-22 11:14:05.049157+03
61	processor	process	ok	\N	0	2026-08-22 11:14:34.273084+03
62	processor	process	ok	\N	0	2026-08-22 11:15:04.277302+03
63	collector	collect	ok	\N	0	2026-08-22 11:15:05.075128+03
64	processor	process	ok	\N	0	2026-08-22 11:15:34.285801+03
65	processor	process	ok	\N	0	2026-08-22 11:16:04.293523+03
66	collector	collect	ok	\N	0	2026-08-22 11:16:05.105669+03
67	processor	process	ok	\N	0	2026-08-22 11:16:34.298167+03
68	processor	process	ok	\N	0	2026-08-22 11:17:04.304953+03
69	collector	collect	ok	\N	0	2026-08-22 11:17:05.138884+03
70	processor	process	ok	\N	0	2026-08-22 11:17:34.311984+03
71	processor	process	ok	\N	0	2026-08-22 11:18:04.318432+03
72	collector	collect	ok	\N	0	2026-08-22 11:18:05.167124+03
73	processor	process	ok	\N	0	2026-08-22 11:18:34.324505+03
74	processor	process	ok	\N	0	2026-08-22 11:19:04.332117+03
75	collector	collect	ok	\N	0	2026-08-22 11:19:05.198384+03
76	processor	process	ok	\N	0	2026-08-22 11:19:34.340653+03
77	processor	process	ok	\N	0	2026-08-22 11:20:04.347062+03
78	collector	collect	ok	\N	0	2026-08-22 11:20:05.226711+03
79	processor	process	ok	\N	0	2026-08-22 11:20:34.355868+03
80	processor	process	ok	\N	0	2026-08-22 11:21:04.362162+03
81	collector	collect	ok	\N	0	2026-08-22 11:21:05.25296+03
82	processor	process	ok	\N	0	2026-08-22 11:21:34.368151+03
83	processor	process	ok	\N	0	2026-08-22 11:22:04.376568+03
84	collector	collect	ok	\N	0	2026-08-22 11:22:05.278505+03
85	processor	process	ok	\N	0	2026-08-22 11:22:34.380716+03
86	processor	process	ok	\N	0	2026-08-22 11:23:04.389594+03
87	collector	collect	ok	\N	0	2026-08-22 11:23:05.304992+03
88	processor	process	ok	\N	0	2026-08-22 11:23:34.39636+03
89	processor	process	ok	\N	0	2026-08-22 11:24:04.403677+03
90	collector	collect	ok	\N	0	2026-08-22 11:24:05.326077+03
91	processor	process	ok	\N	0	2026-08-22 11:24:34.409412+03
92	processor	process	ok	\N	0	2026-08-22 11:25:04.417622+03
93	collector	collect	ok	\N	0	2026-08-22 11:25:05.346369+03
94	processor	process	ok	\N	0	2026-08-22 11:25:34.425872+03
95	processor	process	ok	\N	0	2026-08-22 11:26:04.433831+03
96	collector	collect	ok	\N	0	2026-08-22 11:26:05.362521+03
97	processor	process	ok	\N	0	2026-08-22 11:26:34.443481+03
98	processor	process	ok	\N	0	2026-08-22 11:27:04.452431+03
99	collector	collect	ok	\N	0	2026-08-22 11:27:05.38344+03
100	processor	process	ok	\N	0	2026-08-22 11:27:34.46115+03
101	processor	process	ok	\N	0	2026-08-22 11:28:04.469074+03
102	collector	collect	ok	\N	0	2026-08-22 11:28:05.408751+03
103	processor	process	ok	\N	0	2026-08-22 11:28:34.476323+03
104	processor	process	ok	\N	0	2026-08-22 11:29:04.482275+03
105	collector	collect	ok	\N	0	2026-08-22 11:29:05.428308+03
106	processor	process	ok	\N	0	2026-08-22 11:29:34.488829+03
107	processor	process	ok	\N	0	2026-08-22 11:30:04.497719+03
108	collector	collect	ok	\N	0	2026-08-22 11:30:05.448164+03
109	processor	process	ok	\N	0	2026-08-22 11:30:34.504723+03
110	processor	process	ok	\N	0	2026-08-22 11:31:04.512156+03
111	collector	collect	ok	\N	0	2026-08-22 11:31:05.464091+03
112	processor	process	ok	\N	0	2026-08-22 11:31:34.518616+03
113	processor	process	ok	\N	0	2026-08-22 11:32:04.527429+03
114	collector	collect	ok	\N	0	2026-08-22 11:32:05.482512+03
115	processor	process	ok	\N	0	2026-08-22 11:32:34.533454+03
116	processor	process	ok	\N	0	2026-08-22 11:33:04.539644+03
117	collector	collect	ok	\N	0	2026-08-22 11:33:05.498832+03
118	processor	process	ok	\N	0	2026-08-22 11:33:34.545963+03
119	processor	process	ok	\N	0	2026-08-22 11:34:04.555057+03
120	collector	collect	ok	\N	0	2026-08-22 11:34:05.515685+03
121	processor	process	ok	\N	0	2026-08-22 11:34:34.564505+03
122	processor	process	ok	\N	0	2026-08-22 11:35:04.572877+03
124	processor	process	ok	\N	0	2026-08-22 11:35:34.579009+03
125	processor	process	ok	\N	0	2026-08-22 11:36:04.585673+03
127	processor	process	ok	\N	0	2026-08-22 11:36:34.592176+03
128	processor	process	ok	\N	0	2026-08-22 11:37:04.597658+03
130	processor	process	ok	\N	0	2026-08-22 11:37:34.606187+03
131	processor	process	ok	\N	0	2026-08-22 11:38:04.613459+03
133	processor	process	ok	\N	0	2026-08-22 11:38:34.62033+03
134	processor	process	ok	\N	0	2026-08-22 11:39:04.62754+03
136	processor	process	ok	\N	0	2026-08-22 11:39:34.633993+03
137	processor	process	ok	\N	0	2026-08-22 11:40:04.640923+03
139	processor	process	ok	\N	0	2026-08-22 11:40:34.647694+03
140	processor	process	ok	\N	0	2026-08-22 11:41:04.655981+03
142	processor	process	ok	\N	0	2026-08-22 11:41:34.664927+03
143	processor	process	ok	\N	0	2026-08-22 11:42:04.670001+03
145	processor	process	ok	\N	0	2026-08-22 11:42:34.676811+03
146	processor	process	ok	\N	0	2026-08-22 11:43:04.684179+03
148	processor	process	ok	\N	0	2026-08-22 11:43:34.690951+03
149	processor	process	ok	\N	0	2026-08-22 11:44:04.6996+03
151	processor	process	ok	\N	0	2026-08-22 11:44:34.706135+03
152	processor	process	ok	\N	0	2026-08-22 11:45:04.711902+03
154	processor	process	ok	\N	0	2026-08-22 11:45:34.719102+03
155	processor	process	ok	\N	0	2026-08-22 11:46:04.725518+03
157	processor	process	ok	\N	0	2026-08-22 11:46:34.734476+03
158	processor	process	ok	\N	0	2026-08-22 11:47:04.740448+03
160	processor	process	ok	\N	0	2026-08-22 11:47:34.749202+03
161	processor	process	ok	\N	0	2026-08-22 11:48:04.757797+03
163	processor	process	ok	\N	0	2026-08-22 11:48:34.764324+03
164	processor	process	ok	\N	0	2026-08-22 11:49:04.769366+03
166	processor	process	ok	\N	0	2026-08-22 11:49:34.777778+03
167	processor	process	ok	\N	0	2026-08-22 11:50:04.783883+03
169	processor	process	ok	\N	0	2026-08-22 11:50:34.788697+03
170	processor	process	ok	\N	0	2026-08-22 11:51:04.795561+03
172	processor	process	ok	\N	0	2026-08-22 11:51:34.802077+03
173	processor	process	ok	\N	0	2026-08-22 11:52:04.808278+03
1226	processor	process	ok	\N	0	2026-08-22 17:43:19.534836+03
1228	processor	process	ok	\N	0	2026-08-22 17:43:49.544348+03
1229	processor	process	ok	\N	0	2026-08-22 17:44:19.552272+03
1231	processor	process	ok	\N	0	2026-08-22 17:44:49.55939+03
1232	processor	process	ok	\N	0	2026-08-22 17:45:19.565623+03
1234	processor	process	ok	\N	0	2026-08-22 17:45:49.574055+03
1235	processor	process	ok	\N	0	2026-08-22 17:46:19.580807+03
1237	processor	process	ok	\N	0	2026-08-22 17:46:49.588575+03
1238	processor	process	ok	\N	0	2026-08-22 17:47:19.596501+03
1240	processor	process	ok	\N	0	2026-08-22 17:47:49.605745+03
1241	processor	process	ok	\N	0	2026-08-22 17:48:19.6134+03
1243	processor	process	ok	\N	0	2026-08-22 17:48:49.622921+03
1244	processor	process	ok	\N	0	2026-08-22 17:49:19.62899+03
1246	processor	process	ok	\N	0	2026-08-22 17:49:49.637023+03
1668	collector	collect	ok	\N	0	2026-08-22 20:10:12.257833+03
1671	collector	collect	ok	\N	0	2026-08-22 20:11:12.277222+03
1674	collector	collect	ok	\N	0	2026-08-22 20:12:12.298153+03
1677	collector	collect	ok	\N	0	2026-08-22 20:13:12.315334+03
1680	collector	collect	ok	\N	0	2026-08-22 20:14:12.336962+03
1713	collector	collect	ok	\N	0	2026-08-22 20:25:12.561304+03
1716	collector	collect	ok	\N	0	2026-08-22 20:26:12.580972+03
1719	collector	collect	ok	\N	0	2026-08-22 20:27:12.601794+03
1722	collector	collect	ok	\N	0	2026-08-22 20:28:12.621144+03
1725	collector	collect	ok	\N	0	2026-08-22 20:29:12.639986+03
1758	collector	collect	ok	\N	0	2026-08-22 20:40:12.85999+03
1761	collector	collect	ok	\N	0	2026-08-22 20:41:12.880494+03
1764	collector	collect	ok	\N	0	2026-08-22 20:42:12.901698+03
1767	collector	collect	ok	\N	0	2026-08-22 20:43:12.922606+03
1770	collector	collect	ok	\N	0	2026-08-22 20:44:12.943886+03
1803	collector	collect	ok	\N	0	2026-08-22 20:55:13.186229+03
1806	collector	collect	ok	\N	0	2026-08-22 20:56:13.207556+03
1809	collector	collect	ok	\N	0	2026-08-22 20:57:13.230164+03
1812	collector	collect	ok	\N	0	2026-08-22 20:58:13.24985+03
1815	collector	collect	ok	\N	0	2026-08-22 20:59:13.271389+03
1848	collector	collect	ok	\N	0	2026-08-22 21:10:13.620979+03
1851	collector	collect	ok	\N	0	2026-08-22 21:11:13.643111+03
1854	collector	collect	ok	\N	0	2026-08-22 21:12:13.664349+03
1857	collector	collect	ok	\N	0	2026-08-22 21:13:13.685101+03
1860	collector	collect	ok	\N	0	2026-08-22 21:14:13.705298+03
1943	collector	collect	ok	\N	0	2026-08-22 21:41:44.9888+03
1946	collector	collect	ok	\N	0	2026-08-22 21:42:45.011748+03
1949	collector	collect	ok	\N	0	2026-08-22 21:43:45.047899+03
2167	collector	collect	ok	\N	0	2026-08-22 22:56:05.340784+03
2170	collector	collect	ok	\N	0	2026-08-22 22:57:05.362943+03
2173	collector	collect	ok	\N	0	2026-08-22 22:58:05.388836+03
2176	collector	collect	ok	\N	0	2026-08-22 22:59:05.408928+03
123	collector	collect	ok	\N	0	2026-08-22 11:35:05.534589+03
126	collector	collect	ok	\N	0	2026-08-22 11:36:05.55308+03
129	collector	collect	ok	\N	0	2026-08-22 11:37:05.570436+03
132	collector	collect	ok	\N	0	2026-08-22 11:38:05.588832+03
135	collector	collect	ok	\N	0	2026-08-22 11:39:05.609131+03
138	collector	collect	ok	\N	0	2026-08-22 11:40:05.628946+03
141	collector	collect	ok	\N	0	2026-08-22 11:41:05.647944+03
144	collector	collect	ok	\N	0	2026-08-22 11:42:05.66764+03
147	collector	collect	ok	\N	0	2026-08-22 11:43:05.688635+03
165	collector	collect	ok	\N	0	2026-08-22 11:49:05.809621+03
168	collector	collect	ok	\N	0	2026-08-22 11:50:05.827454+03
171	collector	collect	ok	\N	0	2026-08-22 11:51:05.858334+03
174	collector	collect	ok	\N	0	2026-08-22 11:52:05.876992+03
1227	collector	collect	ok	\N	0	2026-08-22 17:43:19.677362+03
1230	collector	collect	ok	\N	0	2026-08-22 17:44:19.696137+03
1233	collector	collect	ok	\N	0	2026-08-22 17:45:19.715691+03
1236	collector	collect	ok	\N	0	2026-08-22 17:46:19.756817+03
1675	processor	process	ok	\N	0	2026-08-22 20:12:40.779342+03
1676	processor	process	ok	\N	0	2026-08-22 20:13:10.788917+03
1678	processor	process	ok	\N	0	2026-08-22 20:13:40.796897+03
1679	processor	process	ok	\N	0	2026-08-22 20:14:10.804926+03
1681	processor	process	ok	\N	0	2026-08-22 20:14:40.814618+03
1682	processor	process	ok	\N	0	2026-08-22 20:15:10.823879+03
1684	processor	process	ok	\N	0	2026-08-22 20:15:40.831589+03
1685	processor	process	ok	\N	0	2026-08-22 20:16:10.839919+03
1687	processor	process	ok	\N	0	2026-08-22 20:16:40.847107+03
1688	processor	process	ok	\N	0	2026-08-22 20:17:10.856284+03
1690	processor	process	ok	\N	0	2026-08-22 20:17:40.864985+03
1691	processor	process	ok	\N	0	2026-08-22 20:18:10.87377+03
1693	processor	process	ok	\N	0	2026-08-22 20:18:40.88226+03
1694	processor	process	ok	\N	0	2026-08-22 20:19:10.891761+03
1696	processor	process	ok	\N	0	2026-08-22 20:19:40.900183+03
1697	processor	process	ok	\N	0	2026-08-22 20:20:10.909218+03
1699	processor	process	ok	\N	0	2026-08-22 20:20:40.918157+03
1700	processor	process	ok	\N	0	2026-08-22 20:21:10.926116+03
1702	processor	process	ok	\N	0	2026-08-22 20:21:40.93313+03
1703	processor	process	ok	\N	0	2026-08-22 20:22:10.940054+03
1705	processor	process	ok	\N	0	2026-08-22 20:22:40.94892+03
1706	processor	process	ok	\N	0	2026-08-22 20:23:10.957595+03
1708	processor	process	ok	\N	0	2026-08-22 20:23:40.965007+03
1709	processor	process	ok	\N	0	2026-08-22 20:24:10.973217+03
1711	processor	process	ok	\N	0	2026-08-22 20:24:40.982372+03
1712	processor	process	ok	\N	0	2026-08-22 20:25:10.991543+03
1714	processor	process	ok	\N	0	2026-08-22 20:25:41.000172+03
1715	processor	process	ok	\N	0	2026-08-22 20:26:11.007826+03
1717	processor	process	ok	\N	0	2026-08-22 20:26:41.011757+03
1718	processor	process	ok	\N	0	2026-08-22 20:27:11.015605+03
1720	processor	process	ok	\N	0	2026-08-22 20:27:41.021018+03
1721	processor	process	ok	\N	0	2026-08-22 20:28:11.025396+03
1723	processor	process	ok	\N	0	2026-08-22 20:28:41.033704+03
1724	processor	process	ok	\N	0	2026-08-22 20:29:11.043134+03
1726	processor	process	ok	\N	0	2026-08-22 20:29:41.050513+03
1727	processor	process	ok	\N	0	2026-08-22 20:30:11.060189+03
1729	processor	process	ok	\N	0	2026-08-22 20:30:41.064779+03
1730	processor	process	ok	\N	0	2026-08-22 20:31:11.06971+03
1732	processor	process	ok	\N	0	2026-08-22 20:31:41.077697+03
1733	processor	process	ok	\N	0	2026-08-22 20:32:11.086157+03
1735	processor	process	ok	\N	0	2026-08-22 20:32:41.095906+03
1736	processor	process	ok	\N	0	2026-08-22 20:33:11.103603+03
1738	processor	process	ok	\N	0	2026-08-22 20:33:41.111083+03
1739	processor	process	ok	\N	0	2026-08-22 20:34:11.117969+03
1741	processor	process	ok	\N	0	2026-08-22 20:34:41.127058+03
1742	processor	process	ok	\N	0	2026-08-22 20:35:11.134635+03
1744	processor	process	ok	\N	0	2026-08-22 20:35:41.142725+03
1745	processor	process	ok	\N	0	2026-08-22 20:36:11.152329+03
1747	processor	process	ok	\N	0	2026-08-22 20:36:41.15944+03
1748	processor	process	ok	\N	0	2026-08-22 20:37:11.16628+03
1750	processor	process	ok	\N	0	2026-08-22 20:37:41.176639+03
1751	processor	process	ok	\N	0	2026-08-22 20:38:11.185013+03
1753	processor	process	ok	\N	0	2026-08-22 20:38:41.191043+03
1754	processor	process	ok	\N	0	2026-08-22 20:39:11.194307+03
1756	processor	process	ok	\N	0	2026-08-22 20:39:41.204701+03
1757	processor	process	ok	\N	0	2026-08-22 20:40:11.215863+03
1759	processor	process	ok	\N	0	2026-08-22 20:40:41.227874+03
1760	processor	process	ok	\N	0	2026-08-22 20:41:11.239057+03
1762	processor	process	ok	\N	0	2026-08-22 20:41:41.250503+03
1763	processor	process	ok	\N	0	2026-08-22 20:42:11.262001+03
1765	processor	process	ok	\N	0	2026-08-22 20:42:41.278093+03
1766	processor	process	ok	\N	0	2026-08-22 20:43:11.291634+03
1768	processor	process	ok	\N	0	2026-08-22 20:43:41.320426+03
1769	processor	process	ok	\N	0	2026-08-22 20:44:11.331053+03
1771	processor	process	ok	\N	0	2026-08-22 20:44:41.345571+03
1772	processor	process	ok	\N	0	2026-08-22 20:45:11.355039+03
1774	processor	process	ok	\N	0	2026-08-22 20:45:41.364441+03
1775	processor	process	ok	\N	0	2026-08-22 20:46:11.374313+03
1777	processor	process	ok	\N	0	2026-08-22 20:46:41.382372+03
1778	processor	process	ok	\N	0	2026-08-22 20:47:11.390952+03
1780	processor	process	ok	\N	0	2026-08-22 20:47:41.398668+03
1781	processor	process	ok	\N	0	2026-08-22 20:48:11.408243+03
1783	processor	process	ok	\N	0	2026-08-22 20:48:41.416847+03
1784	processor	process	ok	\N	0	2026-08-22 20:49:11.424912+03
1786	processor	process	ok	\N	0	2026-08-22 20:49:41.433798+03
1787	processor	process	ok	\N	0	2026-08-22 20:50:11.441343+03
1789	processor	process	ok	\N	0	2026-08-22 20:50:41.445923+03
1790	processor	process	ok	\N	0	2026-08-22 20:51:11.453858+03
1792	processor	process	ok	\N	0	2026-08-22 20:51:41.461988+03
1793	processor	process	ok	\N	0	2026-08-22 20:52:11.470312+03
1795	processor	process	ok	\N	0	2026-08-22 20:52:41.479074+03
1796	processor	process	ok	\N	0	2026-08-22 20:53:11.485227+03
1798	processor	process	ok	\N	0	2026-08-22 20:53:41.493897+03
1799	processor	process	ok	\N	0	2026-08-22 20:54:11.501435+03
1801	processor	process	ok	\N	0	2026-08-22 20:54:41.509368+03
1802	processor	process	ok	\N	0	2026-08-22 20:55:11.516003+03
1804	processor	process	ok	\N	0	2026-08-22 20:55:41.521838+03
1805	processor	process	ok	\N	0	2026-08-22 20:56:11.529106+03
1807	processor	process	ok	\N	0	2026-08-22 20:56:41.538811+03
1808	processor	process	ok	\N	0	2026-08-22 20:57:11.546549+03
1810	processor	process	ok	\N	0	2026-08-22 20:57:41.554976+03
1811	processor	process	ok	\N	0	2026-08-22 20:58:11.563707+03
1813	processor	process	ok	\N	0	2026-08-22 20:58:41.572844+03
1814	processor	process	ok	\N	0	2026-08-22 20:59:11.580626+03
1816	processor	process	ok	\N	0	2026-08-22 20:59:41.588488+03
1817	processor	process	ok	\N	0	2026-08-22 21:00:11.59523+03
1819	processor	process	ok	\N	0	2026-08-22 21:00:41.604029+03
1820	processor	process	ok	\N	0	2026-08-22 21:01:11.609661+03
1822	processor	process	ok	\N	0	2026-08-22 21:01:41.619081+03
1823	processor	process	ok	\N	0	2026-08-22 21:02:11.625471+03
1825	processor	process	ok	\N	0	2026-08-22 21:02:41.634401+03
1826	processor	process	ok	\N	0	2026-08-22 21:03:11.641744+03
1828	processor	process	ok	\N	0	2026-08-22 21:03:41.651456+03
150	collector	collect	ok	\N	0	2026-08-22 11:44:05.710936+03
153	collector	collect	ok	\N	0	2026-08-22 11:45:05.729985+03
156	collector	collect	ok	\N	0	2026-08-22 11:46:05.748837+03
159	collector	collect	ok	\N	0	2026-08-22 11:47:05.768765+03
162	collector	collect	ok	\N	0	2026-08-22 11:48:05.79005+03
175	processor	process	ok	\N	0	2026-08-22 11:52:34.813225+03
176	processor	process	ok	\N	0	2026-08-22 11:53:04.822031+03
177	collector	collect	ok	\N	0	2026-08-22 11:53:05.892942+03
178	processor	process	ok	\N	0	2026-08-22 11:53:34.828659+03
179	processor	process	ok	\N	0	2026-08-22 11:54:04.834666+03
180	collector	collect	ok	\N	0	2026-08-22 11:54:05.913253+03
181	processor	process	ok	\N	0	2026-08-22 11:54:34.840556+03
182	processor	process	ok	\N	0	2026-08-22 11:55:04.847376+03
183	collector	collect	ok	\N	0	2026-08-22 11:55:05.931404+03
184	processor	process	ok	\N	0	2026-08-22 11:55:34.861613+03
185	processor	process	ok	\N	0	2026-08-22 11:56:04.869512+03
186	collector	collect	ok	\N	0	2026-08-22 11:56:05.949442+03
187	processor	process	ok	\N	0	2026-08-22 11:56:34.875891+03
188	processor	process	ok	\N	0	2026-08-22 11:57:04.881569+03
189	collector	collect	ok	\N	0	2026-08-22 11:57:05.96938+03
190	processor	process	ok	\N	0	2026-08-22 11:57:34.889852+03
191	processor	process	ok	\N	0	2026-08-22 11:58:04.905707+03
192	collector	collect	ok	\N	0	2026-08-22 11:58:05.989319+03
193	processor	process	ok	\N	0	2026-08-22 11:58:34.913384+03
194	processor	process	ok	\N	0	2026-08-22 11:59:04.920375+03
195	collector	collect	ok	\N	0	2026-08-22 11:59:06.009108+03
196	processor	process	ok	\N	0	2026-08-22 11:59:34.929175+03
197	processor	process	ok	\N	0	2026-08-22 12:00:04.93845+03
198	collector	collect	ok	\N	0	2026-08-22 12:00:06.033817+03
199	processor	process	ok	\N	0	2026-08-22 12:00:34.946869+03
200	processor	process	ok	\N	0	2026-08-22 12:01:04.954757+03
201	collector	collect	ok	\N	0	2026-08-22 12:01:06.050207+03
202	processor	process	ok	\N	0	2026-08-22 12:01:34.960417+03
203	processor	process	ok	\N	0	2026-08-22 12:02:04.970557+03
204	collector	collect	ok	\N	0	2026-08-22 12:02:06.080444+03
205	processor	process	ok	\N	0	2026-08-22 12:02:34.980123+03
206	processor	process	ok	\N	0	2026-08-22 12:03:04.990877+03
207	collector	collect	ok	\N	0	2026-08-22 12:03:06.102631+03
208	processor	process	ok	\N	0	2026-08-22 12:03:34.998067+03
209	processor	process	ok	\N	0	2026-08-22 12:04:05.00839+03
210	collector	collect	ok	\N	0	2026-08-22 12:04:06.134861+03
211	processor	process	ok	\N	0	2026-08-22 12:04:35.016876+03
212	processor	process	ok	\N	0	2026-08-22 12:05:05.024092+03
213	collector	collect	ok	\N	0	2026-08-22 12:05:06.162058+03
214	processor	process	ok	\N	0	2026-08-22 12:05:35.031118+03
215	processor	process	ok	\N	0	2026-08-22 12:06:05.040583+03
216	collector	collect	ok	\N	0	2026-08-22 12:06:06.188702+03
217	processor	process	ok	\N	0	2026-08-22 12:06:35.049075+03
218	processor	process	ok	\N	0	2026-08-22 12:07:05.055123+03
219	collector	collect	ok	\N	0	2026-08-22 12:07:06.211537+03
220	processor	process	ok	\N	0	2026-08-22 12:07:35.063719+03
221	processor	process	ok	\N	0	2026-08-22 12:08:05.070276+03
222	collector	collect	ok	\N	0	2026-08-22 12:08:06.244897+03
223	processor	process	ok	\N	0	2026-08-22 12:08:35.078353+03
224	processor	process	ok	\N	0	2026-08-22 12:09:05.085508+03
225	collector	collect	ok	\N	0	2026-08-22 12:09:06.269658+03
226	processor	process	ok	\N	0	2026-08-22 12:09:35.091731+03
227	processor	process	ok	\N	0	2026-08-22 12:10:05.096443+03
228	collector	collect	ok	\N	0	2026-08-22 12:10:06.291447+03
229	processor	process	ok	\N	0	2026-08-22 12:10:35.103601+03
230	processor	process	ok	\N	0	2026-08-22 12:11:05.111319+03
231	collector	collect	ok	\N	0	2026-08-22 12:11:06.312114+03
232	processor	process	ok	\N	0	2026-08-22 12:11:35.116153+03
233	processor	process	ok	\N	0	2026-08-22 12:12:05.125163+03
234	collector	collect	ok	\N	0	2026-08-22 12:12:06.338873+03
235	processor	process	ok	\N	0	2026-08-22 12:12:35.13151+03
236	processor	process	ok	\N	0	2026-08-22 12:13:05.135263+03
237	collector	collect	ok	\N	0	2026-08-22 12:13:06.362853+03
238	processor	process	ok	\N	0	2026-08-22 12:13:35.140049+03
239	processor	process	ok	\N	0	2026-08-22 12:14:05.14409+03
240	collector	collect	ok	\N	0	2026-08-22 12:14:06.39009+03
241	processor	process	ok	\N	0	2026-08-22 12:14:35.151871+03
242	processor	process	ok	\N	0	2026-08-22 12:15:05.15802+03
243	collector	collect	ok	\N	0	2026-08-22 12:15:06.411159+03
244	processor	process	ok	\N	0	2026-08-22 12:15:35.163087+03
245	processor	process	ok	\N	0	2026-08-22 12:16:05.170453+03
246	collector	collect	ok	\N	0	2026-08-22 12:16:06.432655+03
247	processor	process	ok	\N	0	2026-08-22 12:16:35.176767+03
248	processor	process	ok	\N	0	2026-08-22 12:17:05.184373+03
249	collector	collect	ok	\N	0	2026-08-22 12:17:06.454565+03
250	processor	process	ok	\N	0	2026-08-22 12:17:35.188387+03
251	processor	process	ok	\N	0	2026-08-22 12:18:05.197215+03
252	collector	collect	ok	\N	0	2026-08-22 12:18:06.472434+03
253	processor	process	ok	\N	0	2026-08-22 12:18:35.201484+03
254	processor	process	ok	\N	0	2026-08-22 12:19:05.20952+03
255	collector	collect	ok	\N	0	2026-08-22 12:19:06.497393+03
256	processor	process	ok	\N	0	2026-08-22 12:19:35.216365+03
257	processor	process	ok	\N	0	2026-08-22 12:20:05.224219+03
258	collector	collect	ok	\N	0	2026-08-22 12:20:06.519556+03
259	processor	process	ok	\N	0	2026-08-22 12:20:35.232539+03
260	processor	process	ok	\N	0	2026-08-22 12:21:05.240577+03
261	collector	collect	ok	\N	0	2026-08-22 12:21:06.540067+03
262	processor	process	ok	\N	0	2026-08-22 12:21:35.246942+03
263	processor	process	ok	\N	0	2026-08-22 12:22:05.255785+03
264	collector	collect	ok	\N	0	2026-08-22 12:22:06.564286+03
265	processor	process	ok	\N	0	2026-08-22 12:22:35.264046+03
266	processor	process	ok	\N	0	2026-08-22 12:23:05.273558+03
267	collector	collect	ok	\N	0	2026-08-22 12:23:06.582471+03
268	processor	process	ok	\N	0	2026-08-22 12:23:35.279606+03
269	processor	process	ok	\N	0	2026-08-22 12:24:05.284576+03
270	collector	collect	ok	\N	0	2026-08-22 12:24:06.605072+03
271	processor	process	ok	\N	0	2026-08-22 12:24:35.288866+03
272	processor	process	ok	\N	0	2026-08-22 12:25:05.29451+03
273	collector	collect	ok	\N	0	2026-08-22 12:25:06.621166+03
274	processor	process	ok	\N	0	2026-08-22 12:25:35.299706+03
275	processor	process	ok	\N	0	2026-08-22 12:26:05.307026+03
276	collector	collect	ok	\N	0	2026-08-22 12:26:06.646279+03
277	processor	process	ok	\N	0	2026-08-22 12:26:35.314686+03
278	processor	process	ok	\N	0	2026-08-22 12:27:05.321803+03
279	collector	collect	ok	\N	0	2026-08-22 12:27:06.669304+03
280	processor	process	ok	\N	0	2026-08-22 12:27:35.330687+03
281	processor	process	ok	\N	0	2026-08-22 12:28:05.338248+03
282	collector	collect	ok	\N	0	2026-08-22 12:28:06.692311+03
283	processor	process	ok	\N	0	2026-08-22 12:28:35.344588+03
284	processor	process	ok	\N	0	2026-08-22 12:29:05.351115+03
285	collector	collect	ok	\N	0	2026-08-22 12:29:06.714817+03
286	processor	process	ok	\N	0	2026-08-22 12:29:35.357935+03
287	processor	process	ok	\N	0	2026-08-22 12:30:05.365014+03
288	collector	collect	ok	\N	0	2026-08-22 12:30:06.73905+03
289	processor	process	ok	\N	0	2026-08-22 12:30:35.37319+03
290	processor	process	ok	\N	0	2026-08-22 12:31:05.379524+03
292	processor	process	ok	\N	0	2026-08-22 12:31:35.385597+03
293	processor	process	ok	\N	0	2026-08-22 12:32:05.393653+03
295	processor	process	ok	\N	0	2026-08-22 12:32:35.399954+03
296	processor	process	ok	\N	0	2026-08-22 12:33:05.404182+03
298	processor	process	ok	\N	0	2026-08-22 12:33:35.410273+03
299	processor	process	ok	\N	0	2026-08-22 12:34:05.416788+03
301	processor	process	ok	\N	0	2026-08-22 12:34:35.423297+03
302	processor	process	ok	\N	0	2026-08-22 12:35:05.431721+03
304	processor	process	ok	\N	0	2026-08-22 12:35:35.439969+03
305	processor	process	ok	\N	0	2026-08-22 12:36:05.448901+03
307	processor	process	ok	\N	0	2026-08-22 12:36:35.457252+03
308	processor	process	ok	\N	0	2026-08-22 12:37:05.463188+03
310	processor	process	ok	\N	0	2026-08-22 12:37:35.469972+03
311	processor	process	ok	\N	0	2026-08-22 12:38:05.478273+03
313	processor	process	ok	\N	0	2026-08-22 12:38:35.486353+03
314	processor	process	ok	\N	0	2026-08-22 12:39:05.492287+03
316	processor	process	ok	\N	0	2026-08-22 12:39:35.49877+03
317	processor	process	ok	\N	0	2026-08-22 12:40:05.504631+03
1239	collector	collect	ok	\N	0	2026-08-22 17:47:19.77984+03
1242	collector	collect	ok	\N	0	2026-08-22 17:48:19.801417+03
1245	collector	collect	ok	\N	0	2026-08-22 17:49:19.824278+03
1683	collector	collect	ok	\N	0	2026-08-22 20:15:12.358808+03
1686	collector	collect	ok	\N	0	2026-08-22 20:16:12.380383+03
1689	collector	collect	ok	\N	0	2026-08-22 20:17:12.401533+03
1692	collector	collect	ok	\N	0	2026-08-22 20:18:12.421296+03
1695	collector	collect	ok	\N	0	2026-08-22 20:19:12.441398+03
1728	collector	collect	ok	\N	0	2026-08-22 20:30:12.659012+03
1731	collector	collect	ok	\N	0	2026-08-22 20:31:12.676671+03
1734	collector	collect	ok	\N	0	2026-08-22 20:32:12.695195+03
1737	collector	collect	ok	\N	0	2026-08-22 20:33:12.717582+03
1740	collector	collect	ok	\N	0	2026-08-22 20:34:12.738063+03
1773	collector	collect	ok	\N	0	2026-08-22 20:45:12.965936+03
1776	collector	collect	ok	\N	0	2026-08-22 20:46:12.988296+03
1779	collector	collect	ok	\N	0	2026-08-22 20:47:13.009615+03
1782	collector	collect	ok	\N	0	2026-08-22 20:48:13.030974+03
1785	collector	collect	ok	\N	0	2026-08-22 20:49:13.056088+03
1818	collector	collect	ok	\N	0	2026-08-22 21:00:13.291441+03
1821	collector	collect	ok	\N	0	2026-08-22 21:01:13.309606+03
1824	collector	collect	ok	\N	0	2026-08-22 21:02:13.329602+03
1827	collector	collect	ok	\N	0	2026-08-22 21:03:13.352422+03
1830	collector	collect	ok	\N	0	2026-08-22 21:04:13.492389+03
1863	collector	collect	ok	\N	0	2026-08-22 21:15:13.729574+03
1951	processor	process	ok	\N	0	2026-08-22 21:44:46.198867+03
1953	processor	process	ok	\N	0	2026-08-22 21:45:16.213383+03
291	collector	collect	ok	\N	0	2026-08-22 12:31:06.767368+03
294	collector	collect	ok	\N	0	2026-08-22 12:32:06.787764+03
297	collector	collect	ok	\N	0	2026-08-22 12:33:06.805343+03
1247	processor	process	ok	\N	0	2026-08-22 17:50:08.546528+03
1249	processor	process	ok	\N	0	2026-08-22 17:50:38.552682+03
1250	processor	process	ok	\N	0	2026-08-22 17:51:08.560025+03
1252	processor	process	ok	\N	0	2026-08-22 17:51:38.567086+03
1253	processor	process	ok	\N	0	2026-08-22 17:52:08.575838+03
1255	processor	process	ok	\N	0	2026-08-22 17:52:38.585081+03
1256	processor	process	ok	\N	0	2026-08-22 17:53:08.594295+03
1258	processor	process	ok	\N	0	2026-08-22 17:53:38.600386+03
1259	processor	process	ok	\N	0	2026-08-22 17:54:08.604438+03
1261	processor	process	ok	\N	0	2026-08-22 17:54:38.612346+03
1262	processor	process	ok	\N	0	2026-08-22 17:55:08.61723+03
1264	processor	process	ok	\N	0	2026-08-22 17:55:38.624221+03
1265	processor	process	ok	\N	0	2026-08-22 17:56:08.631132+03
1267	processor	process	ok	\N	0	2026-08-22 17:56:38.635593+03
1268	processor	process	ok	\N	0	2026-08-22 17:57:08.639022+03
1270	processor	process	ok	\N	0	2026-08-22 17:57:38.642966+03
1271	processor	process	ok	\N	0	2026-08-22 17:58:08.647981+03
1273	processor	process	ok	\N	0	2026-08-22 17:58:38.657816+03
1274	processor	process	ok	\N	0	2026-08-22 17:59:08.664327+03
1276	processor	process	ok	\N	0	2026-08-22 17:59:38.66859+03
1277	processor	process	ok	\N	0	2026-08-22 18:00:08.677061+03
1279	processor	process	ok	\N	0	2026-08-22 18:00:38.683522+03
1280	processor	process	ok	\N	0	2026-08-22 18:01:08.690531+03
1282	processor	process	ok	\N	0	2026-08-22 18:01:38.696584+03
1283	processor	process	ok	\N	0	2026-08-22 18:02:08.70239+03
1285	processor	process	ok	\N	0	2026-08-22 18:02:38.706608+03
1286	processor	process	ok	\N	0	2026-08-22 18:03:08.712854+03
1698	collector	collect	ok	\N	0	2026-08-22 20:20:12.46184+03
1701	collector	collect	ok	\N	0	2026-08-22 20:21:12.478492+03
1704	collector	collect	ok	\N	0	2026-08-22 20:22:12.49805+03
1707	collector	collect	ok	\N	0	2026-08-22 20:23:12.515751+03
1710	collector	collect	ok	\N	0	2026-08-22 20:24:12.540919+03
1743	collector	collect	ok	\N	0	2026-08-22 20:35:12.756819+03
1746	collector	collect	ok	\N	0	2026-08-22 20:36:12.778872+03
1749	collector	collect	ok	\N	0	2026-08-22 20:37:12.800351+03
1752	collector	collect	ok	\N	0	2026-08-22 20:38:12.818927+03
1755	collector	collect	ok	\N	0	2026-08-22 20:39:12.839692+03
1788	collector	collect	ok	\N	0	2026-08-22 20:50:13.077961+03
1791	collector	collect	ok	\N	0	2026-08-22 20:51:13.100456+03
1794	collector	collect	ok	\N	0	2026-08-22 20:52:13.122337+03
1797	collector	collect	ok	\N	0	2026-08-22 20:53:13.143473+03
1800	collector	collect	ok	\N	0	2026-08-22 20:54:13.163776+03
1833	collector	collect	ok	\N	0	2026-08-22 21:05:13.513574+03
1836	collector	collect	ok	\N	0	2026-08-22 21:06:13.534735+03
1839	collector	collect	ok	\N	0	2026-08-22 21:07:13.557358+03
1842	collector	collect	ok	\N	0	2026-08-22 21:08:13.579733+03
1845	collector	collect	ok	\N	0	2026-08-22 21:09:13.599446+03
1952	collector	collect	ok	\N	0	2026-08-22 21:44:47.345451+03
300	collector	collect	ok	\N	0	2026-08-22 12:34:06.822175+03
303	collector	collect	ok	\N	0	2026-08-22 12:35:06.841344+03
306	collector	collect	ok	\N	0	2026-08-22 12:36:06.869508+03
309	collector	collect	ok	\N	0	2026-08-22 12:37:06.890353+03
312	collector	collect	ok	\N	0	2026-08-22 12:38:06.934592+03
1248	collector	collect	ok	\N	0	2026-08-22 17:50:09.066728+03
1251	collector	collect	ok	\N	0	2026-08-22 17:51:09.084578+03
1254	collector	collect	ok	\N	0	2026-08-22 17:52:09.107078+03
1257	collector	collect	ok	\N	0	2026-08-22 17:53:09.128162+03
1260	collector	collect	ok	\N	0	2026-08-22 17:54:09.149983+03
1829	processor	process	ok	\N	0	2026-08-22 21:04:11.659217+03
1831	processor	process	ok	\N	0	2026-08-22 21:04:41.666576+03
1832	processor	process	ok	\N	0	2026-08-22 21:05:11.674376+03
1834	processor	process	ok	\N	0	2026-08-22 21:05:41.682464+03
1835	processor	process	ok	\N	0	2026-08-22 21:06:11.691086+03
1837	processor	process	ok	\N	0	2026-08-22 21:06:41.699501+03
1838	processor	process	ok	\N	0	2026-08-22 21:07:11.707056+03
1840	processor	process	ok	\N	0	2026-08-22 21:07:41.716583+03
1841	processor	process	ok	\N	0	2026-08-22 21:08:11.72464+03
1843	processor	process	ok	\N	0	2026-08-22 21:08:41.731309+03
1844	processor	process	ok	\N	0	2026-08-22 21:09:11.737992+03
1846	processor	process	ok	\N	0	2026-08-22 21:09:41.744819+03
1847	processor	process	ok	\N	0	2026-08-22 21:10:11.752428+03
1849	processor	process	ok	\N	0	2026-08-22 21:10:41.760722+03
1850	processor	process	ok	\N	0	2026-08-22 21:11:11.765667+03
1852	processor	process	ok	\N	0	2026-08-22 21:11:41.778549+03
1853	processor	process	ok	\N	0	2026-08-22 21:12:11.786156+03
1855	processor	process	ok	\N	0	2026-08-22 21:12:41.793717+03
1856	processor	process	ok	\N	0	2026-08-22 21:13:11.800184+03
1858	processor	process	ok	\N	0	2026-08-22 21:13:41.808358+03
1859	processor	process	ok	\N	0	2026-08-22 21:14:11.813367+03
1861	processor	process	ok	\N	0	2026-08-22 21:14:41.818134+03
1862	processor	process	ok	\N	0	2026-08-22 21:15:11.823401+03
1864	processor	process	ok	\N	0	2026-08-22 21:15:41.833279+03
1954	processor	process	ok	\N	0	2026-08-22 21:45:29.028719+03
1956	processor	process	ok	\N	0	2026-08-22 21:45:59.034345+03
1957	processor	process	ok	\N	0	2026-08-22 21:46:29.038518+03
1959	processor	process	ok	\N	0	2026-08-22 21:46:59.048037+03
1960	processor	process	ok	\N	0	2026-08-22 21:47:29.054537+03
1962	processor	process	ok	\N	0	2026-08-22 21:47:59.059358+03
1963	processor	process	ok	\N	0	2026-08-22 21:48:29.0694+03
1965	processor	process	ok	\N	0	2026-08-22 21:48:59.078728+03
1966	processor	process	ok	\N	0	2026-08-22 21:49:29.087058+03
1968	processor	process	ok	\N	0	2026-08-22 21:49:59.097334+03
1969	processor	process	ok	\N	0	2026-08-22 21:50:29.104422+03
1971	processor	process	ok	\N	0	2026-08-22 21:50:59.109417+03
1972	processor	process	ok	\N	0	2026-08-22 21:51:29.116151+03
1974	processor	process	ok	\N	0	2026-08-22 21:51:59.125772+03
1975	processor	process	ok	\N	0	2026-08-22 21:52:29.135056+03
1977	processor	process	ok	\N	0	2026-08-22 21:52:59.141867+03
1978	processor	process	ok	\N	0	2026-08-22 21:53:29.147543+03
1980	processor	process	ok	\N	0	2026-08-22 21:53:59.155559+03
1981	processor	process	ok	\N	0	2026-08-22 21:54:29.163165+03
1983	processor	process	ok	\N	0	2026-08-22 21:54:59.167196+03
1984	processor	process	ok	\N	0	2026-08-22 21:55:29.172059+03
1986	processor	process	ok	\N	0	2026-08-22 21:55:59.180324+03
1987	processor	process	ok	\N	0	2026-08-22 21:56:29.188987+03
1989	processor	process	ok	\N	0	2026-08-22 21:56:59.19391+03
1990	processor	process	ok	\N	0	2026-08-22 21:57:29.200877+03
1992	processor	process	ok	\N	0	2026-08-22 21:57:59.20733+03
1993	processor	process	ok	\N	0	2026-08-22 21:58:29.215986+03
1995	processor	process	ok	\N	0	2026-08-22 21:58:59.223223+03
1996	processor	process	ok	\N	0	2026-08-22 21:59:29.229503+03
1998	processor	process	ok	\N	0	2026-08-22 21:59:59.237645+03
1999	processor	process	ok	\N	0	2026-08-22 22:00:29.243602+03
2001	processor	process	ok	\N	0	2026-08-22 22:00:59.252981+03
2002	processor	process	ok	\N	0	2026-08-22 22:01:29.259304+03
2004	processor	process	ok	\N	0	2026-08-22 22:01:59.265512+03
2005	processor	process	ok	\N	0	2026-08-22 22:02:29.270665+03
2007	processor	process	ok	\N	0	2026-08-22 22:02:59.279222+03
2008	processor	process	ok	\N	0	2026-08-22 22:03:29.283588+03
2010	processor	process	ok	\N	0	2026-08-22 22:03:59.292013+03
2011	processor	process	ok	\N	0	2026-08-22 22:04:29.298505+03
2013	processor	process	ok	\N	0	2026-08-22 22:04:59.306744+03
2014	processor	process	ok	\N	0	2026-08-22 22:05:29.310159+03
2016	processor	process	ok	\N	0	2026-08-22 22:05:59.316468+03
2017	processor	process	ok	\N	0	2026-08-22 22:06:29.322074+03
2019	processor	process	ok	\N	0	2026-08-22 22:06:59.330593+03
2020	processor	process	ok	\N	0	2026-08-22 22:07:29.336876+03
2022	processor	process	ok	\N	0	2026-08-22 22:07:59.345569+03
2023	processor	process	ok	\N	0	2026-08-22 22:08:29.351522+03
2025	processor	process	ok	\N	0	2026-08-22 22:08:59.35925+03
2026	processor	process	ok	\N	0	2026-08-22 22:09:29.366447+03
2028	processor	process	ok	\N	0	2026-08-22 22:09:59.370788+03
2029	processor	process	ok	\N	0	2026-08-22 22:10:29.378233+03
2031	processor	process	ok	\N	0	2026-08-22 22:10:59.386685+03
2032	processor	process	ok	\N	0	2026-08-22 22:11:29.391561+03
2034	processor	process	ok	\N	0	2026-08-22 22:11:59.398309+03
2035	processor	process	ok	\N	0	2026-08-22 22:12:29.404181+03
2037	processor	process	ok	\N	0	2026-08-22 22:12:59.410566+03
2038	processor	process	ok	\N	0	2026-08-22 22:13:29.419518+03
2040	processor	process	ok	\N	0	2026-08-22 22:13:59.423925+03
2041	processor	process	ok	\N	0	2026-08-22 22:14:29.430095+03
2043	processor	process	ok	\N	0	2026-08-22 22:14:59.436129+03
2044	processor	process	ok	\N	0	2026-08-22 22:15:29.441107+03
2046	processor	process	ok	\N	0	2026-08-22 22:15:59.449643+03
2047	processor	process	ok	\N	0	2026-08-22 22:16:29.456644+03
2049	processor	process	ok	\N	0	2026-08-22 22:16:59.46158+03
2050	processor	process	ok	\N	0	2026-08-22 22:17:29.471559+03
2052	processor	process	ok	\N	0	2026-08-22 22:17:59.475708+03
2053	processor	process	ok	\N	0	2026-08-22 22:18:29.482575+03
2055	processor	process	ok	\N	0	2026-08-22 22:18:59.488153+03
2056	processor	process	ok	\N	0	2026-08-22 22:19:29.495975+03
2058	processor	process	ok	\N	0	2026-08-22 22:19:59.503766+03
2059	processor	process	ok	\N	0	2026-08-22 22:20:29.508169+03
2061	processor	process	ok	\N	0	2026-08-22 22:20:59.516983+03
2062	processor	process	ok	\N	0	2026-08-22 22:21:29.526348+03
2064	processor	process	ok	\N	0	2026-08-22 22:21:59.53396+03
2065	processor	process	ok	\N	0	2026-08-22 22:22:29.542747+03
2067	processor	process	ok	\N	0	2026-08-22 22:22:59.548555+03
2068	processor	process	ok	\N	0	2026-08-22 22:23:29.555823+03
2070	processor	process	ok	\N	0	2026-08-22 22:23:59.560941+03
2071	processor	process	ok	\N	0	2026-08-22 22:24:29.571111+03
2073	processor	process	ok	\N	0	2026-08-22 22:24:59.578993+03
2074	processor	process	ok	\N	0	2026-08-22 22:25:29.585241+03
2076	processor	process	ok	\N	0	2026-08-22 22:25:59.589499+03
2077	processor	process	ok	\N	0	2026-08-22 22:26:29.600284+03
2079	processor	process	ok	\N	0	2026-08-22 22:26:59.60738+03
2080	processor	process	ok	\N	0	2026-08-22 22:27:29.616003+03
2082	processor	process	ok	\N	0	2026-08-22 22:27:59.624097+03
315	collector	collect	ok	\N	0	2026-08-22 12:39:06.953932+03
318	collector	collect	ok	\N	0	2026-08-22 12:40:06.989686+03
319	processor	process	ok	\N	0	2026-08-22 12:40:35.512482+03
320	processor	process	ok	\N	0	2026-08-22 12:41:05.518841+03
321	collector	collect	ok	\N	0	2026-08-22 12:41:07.018795+03
322	processor	process	ok	\N	0	2026-08-22 12:41:35.525384+03
323	processor	process	ok	\N	0	2026-08-22 12:42:05.52994+03
324	collector	collect	ok	\N	0	2026-08-22 12:42:07.045445+03
325	processor	process	ok	\N	0	2026-08-22 12:42:35.599087+03
326	processor	process	ok	\N	0	2026-08-22 12:43:05.608651+03
327	collector	collect	ok	\N	0	2026-08-22 12:43:07.074919+03
328	processor	process	ok	\N	0	2026-08-22 12:43:35.615351+03
329	processor	process	ok	\N	0	2026-08-22 12:44:05.621433+03
330	collector	collect	ok	\N	0	2026-08-22 12:44:07.10267+03
331	processor	process	ok	\N	0	2026-08-22 12:44:35.628668+03
332	processor	process	ok	\N	0	2026-08-22 12:45:05.640631+03
333	collector	collect	ok	\N	0	2026-08-22 12:45:07.129891+03
334	processor	process	ok	\N	0	2026-08-22 12:45:35.648669+03
335	processor	process	ok	\N	0	2026-08-22 12:46:05.655558+03
336	collector	collect	ok	\N	0	2026-08-22 12:46:07.155851+03
337	processor	process	ok	\N	0	2026-08-22 12:46:35.664272+03
338	processor	process	ok	\N	0	2026-08-22 12:47:05.670291+03
339	collector	collect	ok	\N	0	2026-08-22 12:47:07.184787+03
340	processor	process	ok	\N	0	2026-08-22 12:47:35.678566+03
341	processor	process	ok	\N	0	2026-08-22 12:48:05.685469+03
342	collector	collect	ok	\N	0	2026-08-22 12:48:07.215216+03
343	processor	process	ok	\N	0	2026-08-22 12:48:35.691251+03
344	processor	process	ok	\N	0	2026-08-22 12:49:05.70003+03
345	collector	collect	ok	\N	0	2026-08-22 12:49:07.256372+03
346	processor	process	ok	\N	0	2026-08-22 12:49:35.707819+03
347	processor	process	ok	\N	0	2026-08-22 12:50:05.714586+03
348	collector	collect	ok	\N	0	2026-08-22 12:50:07.29197+03
349	processor	process	ok	\N	0	2026-08-22 12:50:35.721351+03
350	processor	process	ok	\N	0	2026-08-22 12:51:05.72851+03
351	collector	collect	ok	\N	0	2026-08-22 12:51:07.321937+03
352	processor	process	ok	\N	0	2026-08-22 12:51:35.735745+03
353	processor	process	ok	\N	0	2026-08-22 12:52:05.744499+03
354	collector	collect	ok	\N	0	2026-08-22 12:52:07.34467+03
355	processor	process	ok	\N	0	2026-08-22 12:52:35.750975+03
356	processor	process	ok	\N	0	2026-08-22 12:53:05.759437+03
357	collector	collect	ok	\N	0	2026-08-22 12:53:07.376106+03
358	processor	process	ok	\N	0	2026-08-22 12:53:35.765751+03
359	processor	process	ok	\N	0	2026-08-22 12:54:05.771426+03
360	collector	collect	ok	\N	0	2026-08-22 12:54:07.41163+03
361	processor	process	ok	\N	0	2026-08-22 12:54:35.775822+03
362	processor	process	ok	\N	0	2026-08-22 12:55:05.78226+03
363	collector	collect	ok	\N	0	2026-08-22 12:55:07.44612+03
364	processor	process	ok	\N	0	2026-08-22 12:55:35.786656+03
365	processor	process	ok	\N	0	2026-08-22 12:56:05.795535+03
366	collector	collect	ok	\N	0	2026-08-22 12:56:07.478313+03
367	processor	process	ok	\N	0	2026-08-22 12:56:35.801483+03
368	processor	process	ok	\N	0	2026-08-22 12:57:05.810256+03
369	collector	collect	ok	\N	0	2026-08-22 12:57:07.511669+03
370	processor	process	ok	\N	0	2026-08-22 12:57:35.816414+03
371	processor	process	ok	\N	0	2026-08-22 12:58:05.824501+03
372	collector	collect	ok	\N	0	2026-08-22 12:58:07.543011+03
373	processor	process	ok	\N	0	2026-08-22 12:58:35.828419+03
374	processor	process	ok	\N	0	2026-08-22 12:59:05.835131+03
375	collector	collect	ok	\N	0	2026-08-22 12:59:07.578141+03
376	processor	process	ok	\N	0	2026-08-22 12:59:35.841877+03
377	processor	process	ok	\N	0	2026-08-22 13:00:05.848312+03
378	collector	collect	ok	\N	0	2026-08-22 13:00:07.610446+03
379	processor	process	ok	\N	0	2026-08-22 13:00:35.856584+03
380	processor	process	ok	\N	0	2026-08-22 13:01:05.865304+03
381	collector	collect	ok	\N	0	2026-08-22 13:01:07.643457+03
382	processor	process	ok	\N	0	2026-08-22 13:01:35.871072+03
383	processor	process	ok	\N	0	2026-08-22 13:02:05.877607+03
384	collector	collect	ok	\N	0	2026-08-22 13:02:07.6749+03
385	processor	process	ok	\N	0	2026-08-22 13:02:35.88437+03
386	processor	process	ok	\N	0	2026-08-22 13:03:05.889916+03
387	collector	collect	ok	\N	0	2026-08-22 13:03:07.699497+03
388	processor	process	ok	\N	0	2026-08-22 13:03:35.895433+03
389	processor	process	ok	\N	0	2026-08-22 13:04:05.905322+03
390	collector	collect	ok	\N	0	2026-08-22 13:04:07.72545+03
391	processor	process	ok	\N	0	2026-08-22 13:04:35.913652+03
392	processor	process	ok	\N	0	2026-08-22 13:05:05.920205+03
393	collector	collect	ok	\N	0	2026-08-22 13:05:07.745305+03
394	processor	process	ok	\N	0	2026-08-22 13:05:35.926262+03
395	processor	process	ok	\N	0	2026-08-22 13:06:05.933072+03
396	collector	collect	ok	\N	0	2026-08-22 13:06:07.764268+03
397	processor	process	ok	\N	0	2026-08-22 13:06:35.939376+03
398	processor	process	ok	\N	0	2026-08-22 13:07:05.946117+03
399	collector	collect	ok	\N	0	2026-08-22 13:07:07.784947+03
400	processor	process	ok	\N	0	2026-08-22 13:07:35.955756+03
401	processor	process	ok	\N	0	2026-08-22 13:08:05.964057+03
402	collector	collect	ok	\N	0	2026-08-22 13:08:07.804776+03
403	processor	process	ok	\N	0	2026-08-22 13:08:35.97036+03
404	processor	process	ok	\N	0	2026-08-22 13:09:05.978804+03
405	collector	collect	ok	\N	0	2026-08-22 13:09:07.824267+03
406	processor	process	ok	\N	0	2026-08-22 13:09:35.985228+03
407	processor	process	ok	\N	0	2026-08-22 13:10:05.993306+03
408	collector	collect	ok	\N	0	2026-08-22 13:10:07.842016+03
409	processor	process	ok	\N	0	2026-08-22 13:10:35.998731+03
410	processor	process	ok	\N	0	2026-08-22 13:11:06.003998+03
411	collector	collect	ok	\N	0	2026-08-22 13:11:07.867017+03
412	processor	process	ok	\N	0	2026-08-22 13:11:36.012974+03
413	processor	process	ok	\N	0	2026-08-22 13:12:06.01787+03
414	collector	collect	ok	\N	0	2026-08-22 13:12:07.891695+03
415	processor	process	ok	\N	0	2026-08-22 13:12:36.024299+03
416	processor	process	ok	\N	0	2026-08-22 13:13:06.030259+03
417	collector	collect	ok	\N	0	2026-08-22 13:13:07.91229+03
418	processor	process	ok	\N	0	2026-08-22 13:13:36.035972+03
419	processor	process	ok	\N	0	2026-08-22 13:14:06.04103+03
420	collector	collect	ok	\N	0	2026-08-22 13:14:07.936936+03
421	processor	process	ok	\N	0	2026-08-22 13:14:36.047941+03
422	processor	process	ok	\N	0	2026-08-22 13:15:06.052947+03
423	collector	collect	ok	\N	0	2026-08-22 13:15:07.954083+03
424	processor	process	ok	\N	0	2026-08-22 13:15:36.060989+03
425	processor	process	ok	\N	0	2026-08-22 13:16:06.067384+03
426	collector	collect	ok	\N	0	2026-08-22 13:16:07.972013+03
427	processor	process	ok	\N	0	2026-08-22 13:16:36.075562+03
428	processor	process	ok	\N	0	2026-08-22 13:17:06.079866+03
429	collector	collect	ok	\N	0	2026-08-22 13:17:07.989043+03
430	processor	process	ok	\N	0	2026-08-22 13:17:36.088309+03
431	processor	process	ok	\N	0	2026-08-22 13:18:06.093096+03
432	collector	collect	ok	\N	0	2026-08-22 13:18:08.006817+03
433	processor	process	ok	\N	0	2026-08-22 13:18:36.102299+03
434	processor	process	ok	\N	0	2026-08-22 13:19:06.108501+03
435	collector	collect	ok	\N	0	2026-08-22 13:19:08.027082+03
436	processor	process	ok	\N	0	2026-08-22 13:19:36.117261+03
437	processor	process	ok	\N	0	2026-08-22 13:20:06.125474+03
439	processor	process	ok	\N	0	2026-08-22 13:20:36.133264+03
440	processor	process	ok	\N	0	2026-08-22 13:21:06.141928+03
442	processor	process	ok	\N	0	2026-08-22 13:21:36.147726+03
443	processor	process	ok	\N	0	2026-08-22 13:22:06.152196+03
445	processor	process	ok	\N	0	2026-08-22 13:22:36.16079+03
446	processor	process	ok	\N	0	2026-08-22 13:23:06.167014+03
448	processor	process	ok	\N	0	2026-08-22 13:23:36.174022+03
449	processor	process	ok	\N	0	2026-08-22 13:24:06.180731+03
451	processor	process	ok	\N	0	2026-08-22 13:24:36.18746+03
452	processor	process	ok	\N	0	2026-08-22 13:25:06.193942+03
454	processor	process	ok	\N	0	2026-08-22 13:25:36.199584+03
455	processor	process	ok	\N	0	2026-08-22 13:26:06.20809+03
457	processor	process	ok	\N	0	2026-08-22 13:26:36.216786+03
458	processor	process	ok	\N	0	2026-08-22 13:27:06.220903+03
460	processor	process	ok	\N	0	2026-08-22 13:27:36.226943+03
461	processor	process	ok	\N	0	2026-08-22 13:28:06.234315+03
463	processor	process	ok	\N	0	2026-08-22 13:28:36.241235+03
464	processor	process	ok	\N	0	2026-08-22 13:29:06.247319+03
466	processor	process	ok	\N	0	2026-08-22 13:29:36.256112+03
467	processor	process	ok	\N	0	2026-08-22 13:30:06.261865+03
469	processor	process	ok	\N	0	2026-08-22 13:30:36.26868+03
470	processor	process	ok	\N	0	2026-08-22 13:31:06.277284+03
472	processor	process	ok	\N	0	2026-08-22 13:31:36.284311+03
473	processor	process	ok	\N	0	2026-08-22 13:32:06.292704+03
475	processor	process	ok	\N	0	2026-08-22 13:32:36.299141+03
476	processor	process	ok	\N	0	2026-08-22 13:33:06.306268+03
478	processor	process	ok	\N	0	2026-08-22 13:33:36.313033+03
479	processor	process	ok	\N	0	2026-08-22 13:34:06.31984+03
481	processor	process	ok	\N	0	2026-08-22 13:34:36.324324+03
482	processor	process	ok	\N	0	2026-08-22 13:35:06.330726+03
484	processor	process	ok	\N	0	2026-08-22 13:35:36.336987+03
485	processor	process	ok	\N	0	2026-08-22 13:36:06.343247+03
487	processor	process	ok	\N	0	2026-08-22 13:36:36.347269+03
488	processor	process	ok	\N	0	2026-08-22 13:37:06.355514+03
490	processor	process	ok	\N	0	2026-08-22 13:37:36.365064+03
491	processor	process	ok	\N	0	2026-08-22 13:38:06.372438+03
493	processor	process	ok	\N	0	2026-08-22 13:38:36.381176+03
494	processor	process	ok	\N	0	2026-08-22 13:39:06.387553+03
1263	collector	collect	ok	\N	0	2026-08-22 17:55:09.172897+03
1266	collector	collect	ok	\N	0	2026-08-22 17:56:09.194496+03
1269	collector	collect	ok	\N	0	2026-08-22 17:57:09.215497+03
1272	collector	collect	ok	\N	0	2026-08-22 17:58:09.237589+03
1275	collector	collect	ok	\N	0	2026-08-22 17:59:09.258752+03
1865	processor	process	ok	\N	0	2026-08-22 21:16:15.055676+03
1867	processor	process	ok	\N	0	2026-08-22 21:16:45.063421+03
1868	processor	process	ok	\N	0	2026-08-22 21:17:15.073683+03
1870	processor	process	ok	\N	0	2026-08-22 21:17:45.080573+03
1871	processor	process	ok	\N	0	2026-08-22 21:18:15.089205+03
1873	processor	process	ok	\N	0	2026-08-22 21:18:45.095994+03
1874	processor	process	ok	\N	0	2026-08-22 21:19:15.101922+03
1876	processor	process	ok	\N	0	2026-08-22 21:19:45.105881+03
1955	collector	collect	ok	\N	0	2026-08-22 21:45:30.833102+03
1958	collector	collect	ok	\N	0	2026-08-22 21:46:30.86075+03
1961	collector	collect	ok	\N	0	2026-08-22 21:47:30.890768+03
1964	collector	collect	ok	\N	0	2026-08-22 21:48:30.914266+03
1967	collector	collect	ok	\N	0	2026-08-22 21:49:30.935303+03
2000	collector	collect	ok	\N	0	2026-08-22 22:00:31.146028+03
2003	collector	collect	ok	\N	0	2026-08-22 22:01:31.163782+03
2006	collector	collect	ok	\N	0	2026-08-22 22:02:31.185219+03
2009	collector	collect	ok	\N	0	2026-08-22 22:03:31.207233+03
2012	collector	collect	ok	\N	0	2026-08-22 22:04:31.228495+03
2045	collector	collect	ok	\N	0	2026-08-22 22:15:31.483773+03
2048	collector	collect	ok	\N	0	2026-08-22 22:16:31.50222+03
2051	collector	collect	ok	\N	0	2026-08-22 22:17:31.527995+03
2054	collector	collect	ok	\N	0	2026-08-22 22:18:31.554493+03
2057	collector	collect	ok	\N	0	2026-08-22 22:19:31.581266+03
2090	collector	collect	ok	\N	0	2026-08-22 22:30:31.871288+03
2093	collector	collect	ok	\N	0	2026-08-22 22:31:31.892939+03
2096	collector	collect	ok	\N	0	2026-08-22 22:32:31.916949+03
2099	collector	collect	ok	\N	0	2026-08-22 22:33:31.940938+03
2102	collector	collect	ok	\N	0	2026-08-22 22:34:31.963667+03
438	collector	collect	ok	\N	0	2026-08-22 13:20:08.048007+03
441	collector	collect	ok	\N	0	2026-08-22 13:21:08.067823+03
444	collector	collect	ok	\N	0	2026-08-22 13:22:08.08595+03
447	collector	collect	ok	\N	0	2026-08-22 13:23:08.103385+03
480	collector	collect	ok	\N	0	2026-08-22 13:34:08.309721+03
483	collector	collect	ok	\N	0	2026-08-22 13:35:08.327258+03
486	collector	collect	ok	\N	0	2026-08-22 13:36:08.347614+03
489	collector	collect	ok	\N	0	2026-08-22 13:37:08.36552+03
492	collector	collect	ok	\N	0	2026-08-22 13:38:08.385992+03
1278	collector	collect	ok	\N	0	2026-08-22 18:00:09.281922+03
1281	collector	collect	ok	\N	0	2026-08-22 18:01:09.303742+03
1284	collector	collect	ok	\N	0	2026-08-22 18:02:09.325237+03
1287	collector	collect	ok	\N	0	2026-08-22 18:03:09.346022+03
1866	collector	collect	ok	\N	0	2026-08-22 21:16:15.856507+03
1869	collector	collect	ok	\N	0	2026-08-22 21:17:15.912312+03
1872	collector	collect	ok	\N	0	2026-08-22 21:18:15.94693+03
1875	collector	collect	ok	\N	0	2026-08-22 21:19:16.002193+03
1970	collector	collect	ok	\N	0	2026-08-22 21:50:30.956094+03
1973	collector	collect	ok	\N	0	2026-08-22 21:51:30.980305+03
1976	collector	collect	ok	\N	0	2026-08-22 21:52:30.9971+03
1979	collector	collect	ok	\N	0	2026-08-22 21:53:31.014891+03
1982	collector	collect	ok	\N	0	2026-08-22 21:54:31.03237+03
2015	collector	collect	ok	\N	0	2026-08-22 22:05:31.24602+03
2018	collector	collect	ok	\N	0	2026-08-22 22:06:31.264631+03
2021	collector	collect	ok	\N	0	2026-08-22 22:07:31.283526+03
2024	collector	collect	ok	\N	0	2026-08-22 22:08:31.312513+03
2027	collector	collect	ok	\N	0	2026-08-22 22:09:31.364415+03
2060	collector	collect	ok	\N	0	2026-08-22 22:20:31.606014+03
2063	collector	collect	ok	\N	0	2026-08-22 22:21:31.633424+03
2066	collector	collect	ok	\N	0	2026-08-22 22:22:31.652925+03
2069	collector	collect	ok	\N	0	2026-08-22 22:23:31.676143+03
2072	collector	collect	ok	\N	0	2026-08-22 22:24:31.717718+03
2105	collector	collect	ok	\N	0	2026-08-22 22:35:31.983906+03
2108	collector	collect	ok	\N	0	2026-08-22 22:36:32.005132+03
2111	collector	collect	ok	\N	0	2026-08-22 22:37:32.027288+03
2114	collector	collect	ok	\N	0	2026-08-22 22:38:32.052623+03
2117	collector	collect	ok	\N	0	2026-08-22 22:39:32.078644+03
450	collector	collect	ok	\N	0	2026-08-22 13:24:08.122171+03
453	collector	collect	ok	\N	0	2026-08-22 13:25:08.140635+03
456	collector	collect	ok	\N	0	2026-08-22 13:26:08.160595+03
459	collector	collect	ok	\N	0	2026-08-22 13:27:08.179433+03
462	collector	collect	ok	\N	0	2026-08-22 13:28:08.199232+03
495	collector	collect	ok	\N	0	2026-08-22 13:39:08.405883+03
1288	processor	process	ok	\N	0	2026-08-22 18:03:38.719048+03
1289	processor	process	ok	\N	0	2026-08-22 18:04:08.724361+03
1291	processor	process	ok	\N	0	2026-08-22 18:04:38.730512+03
1292	processor	process	ok	\N	0	2026-08-22 18:05:08.740373+03
1294	processor	process	ok	\N	0	2026-08-22 18:05:38.746309+03
1295	processor	process	ok	\N	0	2026-08-22 18:06:08.752137+03
1297	processor	process	ok	\N	0	2026-08-22 18:06:38.758352+03
1298	processor	process	ok	\N	0	2026-08-22 18:07:08.765779+03
1300	processor	process	ok	\N	0	2026-08-22 18:07:38.773383+03
1301	processor	process	ok	\N	0	2026-08-22 18:08:08.783256+03
1303	processor	process	ok	\N	0	2026-08-22 18:08:38.788648+03
1304	processor	process	ok	\N	0	2026-08-22 18:09:08.796558+03
1306	processor	process	ok	\N	0	2026-08-22 18:09:38.804548+03
1307	processor	process	ok	\N	0	2026-08-22 18:10:08.813736+03
1309	processor	process	ok	\N	0	2026-08-22 18:10:38.8198+03
1310	processor	process	ok	\N	0	2026-08-22 18:11:08.828632+03
1312	processor	process	ok	\N	0	2026-08-22 18:11:38.913275+03
1313	processor	process	ok	\N	0	2026-08-22 18:12:08.921919+03
1315	processor	process	ok	\N	0	2026-08-22 18:12:38.929253+03
1316	processor	process	ok	\N	0	2026-08-22 18:13:08.937858+03
1318	processor	process	ok	\N	0	2026-08-22 18:13:38.943576+03
1319	processor	process	ok	\N	0	2026-08-22 18:14:08.950112+03
1321	processor	process	ok	\N	0	2026-08-22 18:14:38.954831+03
1322	processor	process	ok	\N	0	2026-08-22 18:15:08.962136+03
1324	processor	process	ok	\N	0	2026-08-22 18:15:38.970648+03
1325	processor	process	ok	\N	0	2026-08-22 18:16:08.976491+03
1327	processor	process	ok	\N	0	2026-08-22 18:16:38.985043+03
1328	processor	process	ok	\N	0	2026-08-22 18:17:08.994367+03
1330	processor	process	ok	\N	0	2026-08-22 18:17:38.99985+03
1331	processor	process	ok	\N	0	2026-08-22 18:18:09.003942+03
1333	processor	process	ok	\N	0	2026-08-22 18:18:39.01412+03
1334	processor	process	ok	\N	0	2026-08-22 18:19:09.023089+03
1336	processor	process	ok	\N	0	2026-08-22 18:19:39.030737+03
1337	processor	process	ok	\N	0	2026-08-22 18:20:09.038808+03
1339	processor	process	ok	\N	0	2026-08-22 18:20:39.047175+03
1340	processor	process	ok	\N	0	2026-08-22 18:21:09.054383+03
1342	processor	process	ok	\N	0	2026-08-22 18:21:39.059825+03
1343	processor	process	ok	\N	0	2026-08-22 18:22:09.067433+03
1345	processor	process	ok	\N	0	2026-08-22 18:22:39.072122+03
1346	processor	process	ok	\N	0	2026-08-22 18:23:09.078108+03
1348	processor	process	ok	\N	0	2026-08-22 18:23:39.084995+03
1349	processor	process	ok	\N	0	2026-08-22 18:24:09.093596+03
1351	processor	process	ok	\N	0	2026-08-22 18:24:39.099904+03
1352	processor	process	ok	\N	0	2026-08-22 18:25:09.107733+03
1354	processor	process	ok	\N	0	2026-08-22 18:25:39.116832+03
1355	processor	process	ok	\N	0	2026-08-22 18:26:09.123815+03
1357	processor	process	ok	\N	0	2026-08-22 18:26:39.130213+03
1358	processor	process	ok	\N	0	2026-08-22 18:27:09.139325+03
1360	processor	process	ok	\N	0	2026-08-22 18:27:39.145826+03
1361	processor	process	ok	\N	0	2026-08-22 18:28:09.151404+03
1363	processor	process	ok	\N	0	2026-08-22 18:28:39.157856+03
1364	processor	process	ok	\N	0	2026-08-22 18:29:09.166738+03
1366	processor	process	ok	\N	0	2026-08-22 18:29:39.173556+03
1367	processor	process	ok	\N	0	2026-08-22 18:30:09.180036+03
1369	processor	process	ok	\N	0	2026-08-22 18:30:39.183891+03
1370	processor	process	ok	\N	0	2026-08-22 18:31:09.189956+03
1372	processor	process	ok	\N	0	2026-08-22 18:31:39.197815+03
1373	processor	process	ok	\N	0	2026-08-22 18:32:09.204611+03
1375	processor	process	ok	\N	0	2026-08-22 18:32:39.212907+03
1376	processor	process	ok	\N	0	2026-08-22 18:33:09.218816+03
1378	processor	process	ok	\N	0	2026-08-22 18:33:39.227488+03
1379	processor	process	ok	\N	0	2026-08-22 18:34:09.234048+03
1381	processor	process	ok	\N	0	2026-08-22 18:34:39.242307+03
1382	processor	process	ok	\N	0	2026-08-22 18:35:09.251819+03
1384	processor	process	ok	\N	0	2026-08-22 18:35:39.25828+03
1385	processor	process	ok	\N	0	2026-08-22 18:36:09.266169+03
1387	processor	process	ok	\N	0	2026-08-22 18:36:39.274631+03
1388	processor	process	ok	\N	0	2026-08-22 18:37:09.283016+03
1390	processor	process	ok	\N	0	2026-08-22 18:37:39.292342+03
1391	processor	process	ok	\N	0	2026-08-22 18:38:09.299835+03
1393	processor	process	ok	\N	0	2026-08-22 18:38:39.307832+03
1394	processor	process	ok	\N	0	2026-08-22 18:39:09.315984+03
1396	processor	process	ok	\N	0	2026-08-22 18:39:39.323981+03
1397	processor	process	ok	\N	0	2026-08-22 18:40:09.332481+03
1399	processor	process	ok	\N	0	2026-08-22 18:40:39.340904+03
1400	processor	process	ok	\N	0	2026-08-22 18:41:09.349863+03
1402	processor	process	ok	\N	0	2026-08-22 18:41:39.356193+03
1403	processor	process	ok	\N	0	2026-08-22 18:42:09.365037+03
1405	processor	process	ok	\N	0	2026-08-22 18:42:39.374763+03
1406	processor	process	ok	\N	0	2026-08-22 18:43:09.383403+03
1408	processor	process	ok	\N	0	2026-08-22 18:43:39.392793+03
1409	processor	process	ok	\N	0	2026-08-22 18:44:09.399308+03
1411	processor	process	ok	\N	0	2026-08-22 18:44:39.407921+03
1412	processor	process	ok	\N	0	2026-08-22 18:45:09.414101+03
1414	processor	process	ok	\N	0	2026-08-22 18:45:39.421453+03
1415	processor	process	ok	\N	0	2026-08-22 18:46:09.430132+03
1417	processor	process	ok	\N	0	2026-08-22 18:46:39.438762+03
1418	processor	process	ok	\N	0	2026-08-22 18:47:09.446074+03
1420	processor	process	ok	\N	0	2026-08-22 18:47:39.454044+03
1421	processor	process	ok	\N	0	2026-08-22 18:48:09.461792+03
1423	processor	process	ok	\N	0	2026-08-22 18:48:39.468615+03
1424	processor	process	ok	\N	0	2026-08-22 18:49:09.476889+03
1426	processor	process	ok	\N	0	2026-08-22 18:49:39.484311+03
1427	processor	process	ok	\N	0	2026-08-22 18:50:09.491865+03
1429	processor	process	ok	\N	0	2026-08-22 18:50:39.500437+03
1430	processor	process	ok	\N	0	2026-08-22 18:51:09.506764+03
1432	processor	process	ok	\N	0	2026-08-22 18:51:39.513527+03
1433	processor	process	ok	\N	0	2026-08-22 18:52:09.522339+03
1435	processor	process	ok	\N	0	2026-08-22 18:52:39.531753+03
1436	processor	process	ok	\N	0	2026-08-22 18:53:09.540763+03
1438	processor	process	ok	\N	0	2026-08-22 18:53:39.54688+03
1439	processor	process	ok	\N	0	2026-08-22 18:54:09.555278+03
1441	processor	process	ok	\N	0	2026-08-22 18:54:39.561891+03
1442	processor	process	ok	\N	0	2026-08-22 18:55:09.566888+03
1444	processor	process	ok	\N	0	2026-08-22 18:55:39.573682+03
1445	processor	process	ok	\N	0	2026-08-22 18:56:09.580103+03
1447	processor	process	ok	\N	0	2026-08-22 18:56:39.586039+03
1448	processor	process	ok	\N	0	2026-08-22 18:57:09.594157+03
1450	processor	process	ok	\N	0	2026-08-22 18:57:39.599114+03
1451	processor	process	ok	\N	0	2026-08-22 18:58:09.606599+03
1453	processor	process	ok	\N	0	2026-08-22 18:58:39.613697+03
1454	processor	process	ok	\N	0	2026-08-22 18:59:09.621249+03
1456	processor	process	ok	\N	0	2026-08-22 18:59:39.627615+03
1457	processor	process	ok	\N	0	2026-08-22 19:00:09.633891+03
465	collector	collect	ok	\N	0	2026-08-22 13:29:08.217962+03
468	collector	collect	ok	\N	0	2026-08-22 13:30:08.237522+03
471	collector	collect	ok	\N	0	2026-08-22 13:31:08.254671+03
474	collector	collect	ok	\N	0	2026-08-22 13:32:08.275316+03
477	collector	collect	ok	\N	0	2026-08-22 13:33:08.292321+03
496	processor	process	ok	\N	0	2026-08-22 13:39:36.393693+03
497	processor	process	ok	\N	0	2026-08-22 13:40:06.402042+03
498	collector	collect	ok	\N	0	2026-08-22 13:40:08.424389+03
499	processor	process	ok	\N	0	2026-08-22 13:40:36.408612+03
500	processor	process	ok	\N	0	2026-08-22 13:41:06.416032+03
501	collector	collect	ok	\N	0	2026-08-22 13:41:08.444638+03
502	processor	process	ok	\N	0	2026-08-22 13:41:36.423472+03
503	processor	process	ok	\N	0	2026-08-22 13:42:06.430893+03
504	collector	collect	ok	\N	0	2026-08-22 13:42:08.461924+03
505	processor	process	ok	\N	0	2026-08-22 13:42:36.435436+03
506	processor	process	ok	\N	0	2026-08-22 13:43:06.442024+03
507	collector	collect	ok	\N	0	2026-08-22 13:43:08.531307+03
508	processor	process	ok	\N	0	2026-08-22 13:43:36.447851+03
509	processor	process	ok	\N	0	2026-08-22 13:44:06.452539+03
510	collector	collect	ok	\N	0	2026-08-22 13:44:08.55225+03
511	processor	process	ok	\N	0	2026-08-22 13:44:36.459242+03
512	processor	process	ok	\N	0	2026-08-22 13:45:06.467329+03
513	collector	collect	ok	\N	0	2026-08-22 13:45:08.572458+03
514	processor	process	ok	\N	0	2026-08-22 13:45:36.476177+03
515	processor	process	ok	\N	0	2026-08-22 13:46:06.483145+03
516	collector	collect	ok	\N	0	2026-08-22 13:46:08.589877+03
517	processor	process	ok	\N	0	2026-08-22 13:46:36.490165+03
518	processor	process	ok	\N	0	2026-08-22 13:47:06.498676+03
519	collector	collect	ok	\N	0	2026-08-22 13:47:08.616216+03
520	processor	process	ok	\N	0	2026-08-22 13:47:36.505956+03
521	processor	process	ok	\N	0	2026-08-22 13:48:06.513946+03
522	collector	collect	ok	\N	0	2026-08-22 13:48:08.63457+03
523	processor	process	ok	\N	0	2026-08-22 13:48:36.520693+03
524	processor	process	ok	\N	0	2026-08-22 13:49:06.52638+03
525	collector	collect	ok	\N	0	2026-08-22 13:49:08.653349+03
526	processor	process	ok	\N	0	2026-08-22 13:49:36.534897+03
527	processor	process	ok	\N	0	2026-08-22 13:50:06.543137+03
528	collector	collect	ok	\N	0	2026-08-22 13:50:08.674372+03
529	processor	process	ok	\N	0	2026-08-22 13:50:36.551984+03
530	processor	process	ok	\N	0	2026-08-22 13:51:06.557631+03
531	collector	collect	ok	\N	0	2026-08-22 13:51:08.707843+03
532	processor	process	ok	\N	0	2026-08-22 13:51:36.563823+03
533	processor	process	ok	\N	0	2026-08-22 13:52:06.57167+03
534	collector	collect	ok	\N	0	2026-08-22 13:52:08.725001+03
535	processor	process	ok	\N	0	2026-08-22 13:52:36.578019+03
536	processor	process	ok	\N	0	2026-08-22 13:53:06.587151+03
537	collector	collect	ok	\N	0	2026-08-22 13:53:08.741032+03
538	processor	process	ok	\N	0	2026-08-22 13:53:36.593847+03
539	processor	process	ok	\N	0	2026-08-22 13:54:06.603049+03
540	collector	collect	ok	\N	0	2026-08-22 13:54:08.759168+03
541	processor	process	ok	\N	0	2026-08-22 13:54:36.609519+03
542	processor	process	ok	\N	0	2026-08-22 13:55:06.616186+03
543	collector	collect	ok	\N	0	2026-08-22 13:55:08.775568+03
544	processor	process	ok	\N	0	2026-08-22 13:55:36.622871+03
545	processor	process	ok	\N	0	2026-08-22 13:56:06.628676+03
546	collector	collect	ok	\N	0	2026-08-22 13:56:08.795346+03
547	processor	process	ok	\N	0	2026-08-22 13:56:36.635505+03
548	processor	process	ok	\N	0	2026-08-22 13:57:06.642401+03
549	collector	collect	ok	\N	0	2026-08-22 13:57:08.812115+03
550	processor	process	ok	\N	0	2026-08-22 13:57:36.651207+03
551	processor	process	ok	\N	0	2026-08-22 13:58:06.658799+03
552	collector	collect	ok	\N	0	2026-08-22 13:58:08.831948+03
553	processor	process	ok	\N	0	2026-08-22 13:58:36.66759+03
554	processor	process	ok	\N	0	2026-08-22 13:59:06.674848+03
555	collector	collect	ok	\N	0	2026-08-22 13:59:08.849417+03
556	processor	process	ok	\N	0	2026-08-22 13:59:36.681803+03
557	processor	process	ok	\N	0	2026-08-22 14:00:06.688782+03
558	collector	collect	ok	\N	0	2026-08-22 14:00:08.870402+03
559	processor	process	ok	\N	0	2026-08-22 14:00:36.695145+03
560	processor	process	ok	\N	0	2026-08-22 14:01:06.70306+03
561	collector	collect	ok	\N	0	2026-08-22 14:01:08.889852+03
562	processor	process	ok	\N	0	2026-08-22 14:01:36.711532+03
563	processor	process	ok	\N	0	2026-08-22 14:02:06.715466+03
564	collector	collect	ok	\N	0	2026-08-22 14:02:08.910323+03
565	processor	process	ok	\N	0	2026-08-22 14:02:36.722943+03
566	processor	process	ok	\N	0	2026-08-22 14:03:06.730359+03
567	collector	collect	ok	\N	0	2026-08-22 14:03:08.928227+03
568	processor	process	ok	\N	0	2026-08-22 14:03:36.737466+03
569	processor	process	ok	\N	0	2026-08-22 14:04:06.745741+03
570	collector	collect	ok	\N	0	2026-08-22 14:04:08.947156+03
571	processor	process	ok	\N	0	2026-08-22 14:04:36.752903+03
572	processor	process	ok	\N	0	2026-08-22 14:05:06.75925+03
573	collector	collect	ok	\N	0	2026-08-22 14:05:08.966442+03
574	processor	process	ok	\N	0	2026-08-22 14:05:36.767877+03
575	processor	process	ok	\N	0	2026-08-22 14:06:06.776205+03
576	collector	collect	ok	\N	0	2026-08-22 14:06:08.985142+03
577	processor	process	ok	\N	0	2026-08-22 14:06:36.784752+03
578	processor	process	ok	\N	0	2026-08-22 14:07:06.793785+03
579	collector	collect	ok	\N	0	2026-08-22 14:07:09.005664+03
580	processor	process	ok	\N	0	2026-08-22 14:07:36.80002+03
581	processor	process	ok	\N	0	2026-08-22 14:08:06.808076+03
582	collector	collect	ok	\N	0	2026-08-22 14:08:09.024101+03
583	processor	process	ok	\N	0	2026-08-22 14:08:36.817273+03
584	processor	process	ok	\N	0	2026-08-22 14:09:06.82471+03
585	collector	collect	ok	\N	0	2026-08-22 14:09:09.054287+03
586	processor	process	ok	\N	0	2026-08-22 14:09:36.832783+03
587	processor	process	ok	\N	0	2026-08-22 14:10:06.838087+03
588	collector	collect	ok	\N	0	2026-08-22 14:10:09.07256+03
589	processor	process	ok	\N	0	2026-08-22 14:10:36.843083+03
590	processor	process	ok	\N	0	2026-08-22 14:11:06.851169+03
591	collector	collect	ok	\N	0	2026-08-22 14:11:09.092459+03
592	processor	process	ok	\N	0	2026-08-22 14:11:36.859112+03
593	processor	process	ok	\N	0	2026-08-22 14:12:06.867132+03
594	collector	collect	ok	\N	0	2026-08-22 14:12:09.112282+03
595	processor	process	ok	\N	0	2026-08-22 14:12:36.873477+03
596	processor	process	ok	\N	0	2026-08-22 14:13:06.879513+03
597	collector	collect	ok	\N	0	2026-08-22 14:13:09.132257+03
598	processor	process	ok	\N	0	2026-08-22 14:13:36.88636+03
599	processor	process	ok	\N	0	2026-08-22 14:14:06.893366+03
600	collector	collect	ok	\N	0	2026-08-22 14:14:09.152374+03
601	processor	process	ok	\N	0	2026-08-22 14:14:36.901434+03
602	processor	process	ok	\N	0	2026-08-22 14:15:06.909621+03
603	collector	collect	ok	\N	0	2026-08-22 14:15:09.171462+03
604	processor	process	ok	\N	0	2026-08-22 14:15:36.916067+03
605	processor	process	ok	\N	0	2026-08-22 14:16:06.924905+03
606	collector	collect	ok	\N	0	2026-08-22 14:16:09.189239+03
607	processor	process	ok	\N	0	2026-08-22 14:16:36.931976+03
608	processor	process	ok	\N	0	2026-08-22 14:17:06.940126+03
609	collector	collect	ok	\N	0	2026-08-22 14:17:09.205211+03
610	processor	process	ok	\N	0	2026-08-22 14:17:36.948699+03
611	processor	process	ok	\N	0	2026-08-22 14:18:06.956734+03
613	processor	process	ok	\N	0	2026-08-22 14:18:36.960871+03
614	processor	process	ok	\N	0	2026-08-22 14:19:06.967715+03
616	processor	process	ok	\N	0	2026-08-22 14:19:36.97435+03
617	processor	process	ok	\N	0	2026-08-22 14:20:06.983394+03
619	processor	process	ok	\N	0	2026-08-22 14:20:36.990771+03
620	processor	process	ok	\N	0	2026-08-22 14:21:06.997318+03
622	processor	process	ok	\N	0	2026-08-22 14:21:37.005984+03
623	processor	process	ok	\N	0	2026-08-22 14:22:07.012524+03
625	processor	process	ok	\N	0	2026-08-22 14:22:37.017886+03
626	processor	process	ok	\N	0	2026-08-22 14:23:07.025977+03
628	processor	process	ok	\N	0	2026-08-22 14:23:37.032047+03
629	processor	process	ok	\N	0	2026-08-22 14:24:07.037165+03
631	processor	process	ok	\N	0	2026-08-22 14:24:37.045467+03
632	processor	process	ok	\N	0	2026-08-22 14:25:07.051691+03
634	processor	process	ok	\N	0	2026-08-22 14:25:37.057628+03
635	processor	process	ok	\N	0	2026-08-22 14:26:07.066447+03
637	processor	process	ok	\N	0	2026-08-22 14:26:37.0729+03
638	processor	process	ok	\N	0	2026-08-22 14:27:07.080181+03
640	processor	process	ok	\N	0	2026-08-22 14:27:37.086547+03
641	processor	process	ok	\N	0	2026-08-22 14:28:07.094731+03
643	processor	process	ok	\N	0	2026-08-22 14:28:37.102207+03
644	processor	process	ok	\N	0	2026-08-22 14:29:07.108685+03
646	processor	process	ok	\N	0	2026-08-22 14:29:37.114636+03
647	processor	process	ok	\N	0	2026-08-22 14:30:07.122927+03
649	processor	process	ok	\N	0	2026-08-22 14:30:37.130312+03
650	processor	process	ok	\N	0	2026-08-22 14:31:07.139103+03
652	processor	process	ok	\N	0	2026-08-22 14:31:37.145401+03
653	processor	process	ok	\N	0	2026-08-22 14:32:07.151073+03
655	processor	process	ok	\N	0	2026-08-22 14:32:37.157408+03
656	processor	process	ok	\N	0	2026-08-22 14:33:07.164784+03
658	processor	process	ok	\N	0	2026-08-22 14:33:37.171381+03
659	processor	process	ok	\N	0	2026-08-22 14:34:07.179842+03
661	processor	process	ok	\N	0	2026-08-22 14:34:37.186948+03
662	processor	process	ok	\N	0	2026-08-22 14:35:07.192884+03
664	processor	process	ok	\N	0	2026-08-22 14:35:37.200541+03
665	processor	process	ok	\N	0	2026-08-22 14:36:07.2089+03
667	processor	process	ok	\N	0	2026-08-22 14:36:37.218151+03
668	processor	process	ok	\N	0	2026-08-22 14:37:07.225866+03
670	processor	process	ok	\N	0	2026-08-22 14:37:37.232155+03
671	processor	process	ok	\N	0	2026-08-22 14:38:07.240786+03
673	processor	process	ok	\N	0	2026-08-22 14:38:37.249211+03
674	processor	process	ok	\N	0	2026-08-22 14:39:07.257651+03
676	processor	process	ok	\N	0	2026-08-22 14:39:37.263852+03
677	processor	process	ok	\N	0	2026-08-22 14:40:07.272823+03
679	processor	process	ok	\N	0	2026-08-22 14:40:37.279538+03
680	processor	process	ok	\N	0	2026-08-22 14:41:07.287982+03
682	processor	process	ok	\N	0	2026-08-22 14:41:37.294093+03
683	processor	process	ok	\N	0	2026-08-22 14:42:07.303815+03
685	processor	process	ok	\N	0	2026-08-22 14:42:37.312874+03
686	processor	process	ok	\N	0	2026-08-22 14:43:07.320799+03
688	processor	process	ok	\N	0	2026-08-22 14:43:37.327499+03
689	processor	process	ok	\N	0	2026-08-22 14:44:07.336088+03
691	processor	process	ok	\N	0	2026-08-22 14:44:37.342202+03
692	processor	process	ok	\N	0	2026-08-22 14:45:07.349945+03
694	processor	process	ok	\N	0	2026-08-22 14:45:37.358658+03
695	processor	process	ok	\N	0	2026-08-22 14:46:07.368161+03
697	processor	process	ok	\N	0	2026-08-22 14:46:37.375948+03
698	processor	process	ok	\N	0	2026-08-22 14:47:07.38184+03
700	processor	process	ok	\N	0	2026-08-22 14:47:37.390037+03
701	processor	process	ok	\N	0	2026-08-22 14:48:07.397195+03
703	processor	process	ok	\N	0	2026-08-22 14:48:37.404454+03
704	processor	process	ok	\N	0	2026-08-22 14:49:07.412052+03
706	processor	process	ok	\N	0	2026-08-22 14:49:37.418115+03
707	processor	process	ok	\N	0	2026-08-22 14:50:07.424552+03
1290	collector	collect	ok	\N	0	2026-08-22 18:04:09.369612+03
1323	collector	collect	ok	\N	0	2026-08-22 18:15:09.629702+03
1326	collector	collect	ok	\N	0	2026-08-22 18:16:09.661649+03
1329	collector	collect	ok	\N	0	2026-08-22 18:17:09.696229+03
1332	collector	collect	ok	\N	0	2026-08-22 18:18:09.720641+03
1335	collector	collect	ok	\N	0	2026-08-22 18:19:09.74281+03
1368	collector	collect	ok	\N	0	2026-08-22 18:30:09.96389+03
1371	collector	collect	ok	\N	0	2026-08-22 18:31:09.980678+03
1374	collector	collect	ok	\N	0	2026-08-22 18:32:10.008967+03
1377	collector	collect	ok	\N	0	2026-08-22 18:33:10.040511+03
1380	collector	collect	ok	\N	0	2026-08-22 18:34:10.061679+03
1413	collector	collect	ok	\N	0	2026-08-22 18:45:10.292384+03
1416	collector	collect	ok	\N	0	2026-08-22 18:46:10.312143+03
1419	collector	collect	ok	\N	0	2026-08-22 18:47:10.33148+03
1422	collector	collect	ok	\N	0	2026-08-22 18:48:10.350639+03
1425	collector	collect	ok	\N	0	2026-08-22 18:49:10.371561+03
1458	collector	collect	ok	\N	0	2026-08-22 19:00:10.599519+03
1461	collector	collect	ok	\N	0	2026-08-22 19:01:10.621282+03
1464	collector	collect	ok	\N	0	2026-08-22 19:02:10.642852+03
1467	collector	collect	ok	\N	0	2026-08-22 19:03:10.664746+03
1877	processor	process	ok	\N	0	2026-08-22 21:20:05.439848+03
1879	processor	process	ok	\N	0	2026-08-22 21:20:35.454034+03
1880	processor	process	ok	\N	0	2026-08-22 21:21:05.462978+03
1882	processor	process	ok	\N	0	2026-08-22 21:21:35.468744+03
1883	processor	process	ok	\N	0	2026-08-22 21:22:05.475803+03
1985	collector	collect	ok	\N	0	2026-08-22 21:55:31.052645+03
1988	collector	collect	ok	\N	0	2026-08-22 21:56:31.075596+03
1991	collector	collect	ok	\N	0	2026-08-22 21:57:31.094009+03
1994	collector	collect	ok	\N	0	2026-08-22 21:58:31.110679+03
1997	collector	collect	ok	\N	0	2026-08-22 21:59:31.129105+03
2030	collector	collect	ok	\N	0	2026-08-22 22:10:31.385154+03
2033	collector	collect	ok	\N	0	2026-08-22 22:11:31.406565+03
2036	collector	collect	ok	\N	0	2026-08-22 22:12:31.424751+03
2039	collector	collect	ok	\N	0	2026-08-22 22:13:31.441711+03
2042	collector	collect	ok	\N	0	2026-08-22 22:14:31.462671+03
2075	collector	collect	ok	\N	0	2026-08-22 22:25:31.757344+03
2078	collector	collect	ok	\N	0	2026-08-22 22:26:31.782951+03
2081	collector	collect	ok	\N	0	2026-08-22 22:27:31.805178+03
2084	collector	collect	ok	\N	0	2026-08-22 22:28:31.826788+03
2087	collector	collect	ok	\N	0	2026-08-22 22:29:31.849644+03
2120	collector	collect	ok	\N	0	2026-08-22 22:40:32.100824+03
612	collector	collect	ok	\N	0	2026-08-22 14:18:09.222784+03
615	collector	collect	ok	\N	0	2026-08-22 14:19:09.237692+03
618	collector	collect	ok	\N	0	2026-08-22 14:20:09.254891+03
621	collector	collect	ok	\N	0	2026-08-22 14:21:09.271593+03
624	collector	collect	ok	\N	0	2026-08-22 14:22:09.292128+03
627	collector	collect	ok	\N	0	2026-08-22 14:23:09.310548+03
630	collector	collect	ok	\N	0	2026-08-22 14:24:09.329479+03
633	collector	collect	ok	\N	0	2026-08-22 14:25:09.347751+03
636	collector	collect	ok	\N	0	2026-08-22 14:26:09.36829+03
639	collector	collect	ok	\N	0	2026-08-22 14:27:09.385113+03
642	collector	collect	ok	\N	0	2026-08-22 14:28:09.405416+03
645	collector	collect	ok	\N	0	2026-08-22 14:29:09.422459+03
648	collector	collect	ok	\N	0	2026-08-22 14:30:09.441243+03
651	collector	collect	ok	\N	0	2026-08-22 14:31:09.457936+03
654	collector	collect	ok	\N	0	2026-08-22 14:32:09.476451+03
657	collector	collect	ok	\N	0	2026-08-22 14:33:09.503883+03
660	collector	collect	ok	\N	0	2026-08-22 14:34:09.521129+03
663	collector	collect	ok	\N	0	2026-08-22 14:35:09.539854+03
666	collector	collect	ok	\N	0	2026-08-22 14:36:09.558348+03
669	collector	collect	ok	\N	0	2026-08-22 14:37:09.579454+03
672	collector	collect	ok	\N	0	2026-08-22 14:38:09.60266+03
675	collector	collect	ok	\N	0	2026-08-22 14:39:09.625098+03
678	collector	collect	ok	\N	0	2026-08-22 14:40:09.646644+03
681	collector	collect	ok	\N	0	2026-08-22 14:41:09.665932+03
684	collector	collect	ok	\N	0	2026-08-22 14:42:09.685658+03
687	collector	collect	ok	\N	0	2026-08-22 14:43:09.703129+03
690	collector	collect	ok	\N	0	2026-08-22 14:44:09.720667+03
693	collector	collect	ok	\N	0	2026-08-22 14:45:09.740503+03
696	collector	collect	ok	\N	0	2026-08-22 14:46:09.758535+03
699	collector	collect	ok	\N	0	2026-08-22 14:47:09.776002+03
702	collector	collect	ok	\N	0	2026-08-22 14:48:09.793125+03
705	collector	collect	ok	\N	0	2026-08-22 14:49:09.811438+03
708	collector	collect	ok	\N	0	2026-08-22 14:50:09.831261+03
709	processor	process	ok	\N	0	2026-08-22 14:50:37.430604+03
710	processor	process	ok	\N	0	2026-08-22 14:51:07.435898+03
711	collector	collect	ok	\N	0	2026-08-22 14:51:09.848118+03
712	processor	process	ok	\N	0	2026-08-22 14:51:37.44286+03
713	processor	process	ok	\N	0	2026-08-22 14:52:07.450861+03
714	collector	collect	ok	\N	0	2026-08-22 14:52:09.866223+03
715	processor	process	ok	\N	0	2026-08-22 14:52:37.456462+03
716	processor	process	ok	\N	0	2026-08-22 14:53:07.465136+03
717	collector	collect	ok	\N	0	2026-08-22 14:53:09.884751+03
718	processor	process	ok	\N	0	2026-08-22 14:53:37.470988+03
719	processor	process	ok	\N	0	2026-08-22 14:54:07.479127+03
720	collector	collect	ok	\N	0	2026-08-22 14:54:09.904704+03
721	processor	process	ok	\N	0	2026-08-22 14:54:37.488173+03
722	processor	process	ok	\N	0	2026-08-22 14:55:07.494041+03
723	collector	collect	ok	\N	0	2026-08-22 14:55:09.923831+03
724	processor	process	ok	\N	0	2026-08-22 14:55:37.501506+03
725	processor	process	ok	\N	0	2026-08-22 14:56:07.509987+03
726	collector	collect	ok	\N	0	2026-08-22 14:56:09.942+03
727	processor	process	ok	\N	0	2026-08-22 14:56:37.515927+03
728	processor	process	ok	\N	0	2026-08-22 14:57:07.524426+03
729	collector	collect	ok	\N	0	2026-08-22 14:57:09.961082+03
730	processor	process	ok	\N	0	2026-08-22 14:57:37.532328+03
731	processor	process	ok	\N	0	2026-08-22 14:58:07.538913+03
732	collector	collect	ok	\N	0	2026-08-22 14:58:09.979552+03
733	processor	process	ok	\N	0	2026-08-22 14:58:37.54449+03
734	processor	process	ok	\N	0	2026-08-22 14:59:07.55317+03
735	collector	collect	ok	\N	0	2026-08-22 14:59:09.997761+03
736	processor	process	ok	\N	0	2026-08-22 14:59:37.560831+03
737	processor	process	ok	\N	0	2026-08-22 15:00:07.567275+03
738	collector	collect	ok	\N	0	2026-08-22 15:00:10.015711+03
739	processor	process	ok	\N	0	2026-08-22 15:00:37.576538+03
740	processor	process	ok	\N	0	2026-08-22 15:01:07.582713+03
741	collector	collect	ok	\N	0	2026-08-22 15:01:10.036393+03
742	processor	process	ok	\N	0	2026-08-22 15:01:37.589972+03
743	processor	process	ok	\N	0	2026-08-22 15:02:07.598536+03
744	collector	collect	ok	\N	0	2026-08-22 15:02:10.053672+03
745	processor	process	ok	\N	0	2026-08-22 15:02:37.605218+03
746	processor	process	ok	\N	0	2026-08-22 15:03:07.61102+03
747	collector	collect	ok	\N	0	2026-08-22 15:03:10.071452+03
748	processor	process	ok	\N	0	2026-08-22 15:03:37.61963+03
749	processor	process	ok	\N	0	2026-08-22 15:04:07.628178+03
750	collector	collect	ok	\N	0	2026-08-22 15:04:10.093017+03
751	processor	process	ok	\N	0	2026-08-22 15:04:37.63434+03
752	processor	process	ok	\N	0	2026-08-22 15:05:07.640988+03
753	collector	collect	ok	\N	0	2026-08-22 15:05:10.113807+03
754	processor	process	ok	\N	0	2026-08-22 15:05:37.649288+03
755	processor	process	ok	\N	0	2026-08-22 15:06:07.655002+03
756	collector	collect	ok	\N	0	2026-08-22 15:06:10.133909+03
757	processor	process	ok	\N	0	2026-08-22 15:06:37.662203+03
758	processor	process	ok	\N	0	2026-08-22 15:07:07.670622+03
759	collector	collect	ok	\N	0	2026-08-22 15:07:10.154346+03
760	processor	process	ok	\N	0	2026-08-22 15:07:37.677253+03
761	processor	process	ok	\N	0	2026-08-22 15:08:07.683622+03
762	collector	collect	ok	\N	0	2026-08-22 15:08:10.173114+03
763	processor	process	ok	\N	0	2026-08-22 15:08:37.688146+03
764	processor	process	ok	\N	0	2026-08-22 15:09:07.693497+03
765	collector	collect	ok	\N	0	2026-08-22 15:09:10.197121+03
766	processor	process	ok	\N	0	2026-08-22 15:09:37.697362+03
767	processor	process	ok	\N	0	2026-08-22 15:10:07.700977+03
768	collector	collect	ok	\N	0	2026-08-22 15:10:10.219541+03
769	processor	process	ok	\N	0	2026-08-22 15:10:37.703801+03
770	processor	process	ok	\N	0	2026-08-22 15:11:07.712259+03
771	collector	collect	ok	\N	0	2026-08-22 15:11:10.235623+03
772	processor	process	ok	\N	0	2026-08-22 15:11:37.720099+03
773	processor	process	ok	\N	0	2026-08-22 15:12:07.72928+03
774	collector	collect	ok	\N	0	2026-08-22 15:12:10.255888+03
775	processor	process	ok	\N	0	2026-08-22 15:12:37.736695+03
776	processor	process	ok	\N	0	2026-08-22 15:13:07.743834+03
777	collector	collect	ok	\N	0	2026-08-22 15:13:10.275735+03
778	processor	process	ok	\N	0	2026-08-22 15:13:37.751735+03
779	processor	process	ok	\N	0	2026-08-22 15:14:07.757776+03
780	collector	collect	ok	\N	0	2026-08-22 15:14:10.292672+03
781	processor	process	ok	\N	0	2026-08-22 15:14:37.765973+03
782	processor	process	ok	\N	0	2026-08-22 15:15:07.772527+03
783	collector	collect	ok	\N	0	2026-08-22 15:15:10.312884+03
784	processor	process	ok	\N	0	2026-08-22 15:15:37.778992+03
785	processor	process	ok	\N	0	2026-08-22 15:16:07.786095+03
786	collector	collect	ok	\N	0	2026-08-22 15:16:10.332605+03
787	processor	process	ok	\N	0	2026-08-22 15:16:37.792153+03
788	processor	process	ok	\N	0	2026-08-22 15:17:07.798344+03
789	collector	collect	ok	\N	0	2026-08-22 15:17:10.34998+03
790	processor	process	ok	\N	0	2026-08-22 15:17:37.802599+03
791	processor	process	ok	\N	0	2026-08-22 15:18:07.811847+03
792	collector	collect	ok	\N	0	2026-08-22 15:18:10.36693+03
793	processor	process	ok	\N	0	2026-08-22 15:18:37.816803+03
794	processor	process	ok	\N	0	2026-08-22 15:19:07.824171+03
795	collector	collect	ok	\N	0	2026-08-22 15:19:10.385591+03
796	processor	process	ok	\N	0	2026-08-22 15:19:37.831126+03
797	processor	process	ok	\N	0	2026-08-22 15:20:07.83905+03
799	processor	process	ok	\N	0	2026-08-22 15:20:37.843483+03
800	processor	process	ok	\N	0	2026-08-22 15:21:07.849739+03
802	processor	process	ok	\N	0	2026-08-22 15:21:37.85802+03
803	processor	process	ok	\N	0	2026-08-22 15:22:07.866763+03
805	processor	process	ok	\N	0	2026-08-22 15:22:37.872641+03
806	processor	process	ok	\N	0	2026-08-22 15:23:07.881739+03
808	processor	process	ok	\N	0	2026-08-22 15:23:37.891159+03
809	processor	process	ok	\N	0	2026-08-22 15:24:07.897997+03
811	processor	process	ok	\N	0	2026-08-22 15:24:37.906471+03
812	processor	process	ok	\N	0	2026-08-22 15:25:07.912652+03
814	processor	process	ok	\N	0	2026-08-22 15:25:37.918727+03
815	processor	process	ok	\N	0	2026-08-22 15:26:07.92701+03
817	processor	process	ok	\N	0	2026-08-22 15:26:37.935489+03
818	processor	process	ok	\N	0	2026-08-22 15:27:07.943719+03
820	processor	process	ok	\N	0	2026-08-22 15:27:37.950563+03
821	processor	process	ok	\N	0	2026-08-22 15:28:07.958428+03
823	processor	process	ok	\N	0	2026-08-22 15:28:37.966453+03
824	processor	process	ok	\N	0	2026-08-22 15:29:07.974964+03
826	processor	process	ok	\N	0	2026-08-22 15:29:37.983914+03
827	processor	process	ok	\N	0	2026-08-22 15:30:07.991132+03
829	processor	process	ok	\N	0	2026-08-22 15:30:37.996133+03
830	processor	process	ok	\N	0	2026-08-22 15:31:08.002882+03
1293	collector	collect	ok	\N	0	2026-08-22 18:05:09.392569+03
1296	collector	collect	ok	\N	0	2026-08-22 18:06:09.41431+03
1299	collector	collect	ok	\N	0	2026-08-22 18:07:09.435194+03
1302	collector	collect	ok	\N	0	2026-08-22 18:08:09.458297+03
1305	collector	collect	ok	\N	0	2026-08-22 18:09:09.476416+03
1338	collector	collect	ok	\N	0	2026-08-22 18:20:09.767137+03
1341	collector	collect	ok	\N	0	2026-08-22 18:21:09.787726+03
1344	collector	collect	ok	\N	0	2026-08-22 18:22:09.808843+03
1347	collector	collect	ok	\N	0	2026-08-22 18:23:09.828962+03
1350	collector	collect	ok	\N	0	2026-08-22 18:24:09.850355+03
1383	collector	collect	ok	\N	0	2026-08-22 18:35:10.082528+03
1386	collector	collect	ok	\N	0	2026-08-22 18:36:10.100372+03
1389	collector	collect	ok	\N	0	2026-08-22 18:37:10.119468+03
1392	collector	collect	ok	\N	0	2026-08-22 18:38:10.139142+03
1395	collector	collect	ok	\N	0	2026-08-22 18:39:10.159166+03
1428	collector	collect	ok	\N	0	2026-08-22 18:50:10.393236+03
1431	collector	collect	ok	\N	0	2026-08-22 18:51:10.413321+03
1434	collector	collect	ok	\N	0	2026-08-22 18:52:10.437158+03
1437	collector	collect	ok	\N	0	2026-08-22 18:53:10.45696+03
1440	collector	collect	ok	\N	0	2026-08-22 18:54:10.478965+03
1878	collector	collect	ok	\N	0	2026-08-22 21:20:08.071049+03
1881	collector	collect	ok	\N	0	2026-08-22 21:21:08.09699+03
1884	collector	collect	ok	\N	0	2026-08-22 21:22:08.120494+03
2083	processor	process	ok	\N	0	2026-08-22 22:28:29.643733+03
2085	processor	process	ok	\N	0	2026-08-22 22:28:59.649297+03
2086	processor	process	ok	\N	0	2026-08-22 22:29:29.657101+03
2088	processor	process	ok	\N	0	2026-08-22 22:29:59.66238+03
2089	processor	process	ok	\N	0	2026-08-22 22:30:29.666748+03
2091	processor	process	ok	\N	0	2026-08-22 22:30:59.673603+03
2092	processor	process	ok	\N	0	2026-08-22 22:31:29.680619+03
2094	processor	process	ok	\N	0	2026-08-22 22:31:59.68482+03
2095	processor	process	ok	\N	0	2026-08-22 22:32:29.69119+03
2097	processor	process	ok	\N	0	2026-08-22 22:32:59.698457+03
2098	processor	process	ok	\N	0	2026-08-22 22:33:29.704969+03
2100	processor	process	ok	\N	0	2026-08-22 22:33:59.710512+03
2101	processor	process	ok	\N	0	2026-08-22 22:34:29.717154+03
2103	processor	process	ok	\N	0	2026-08-22 22:34:59.721494+03
2104	processor	process	ok	\N	0	2026-08-22 22:35:29.730305+03
2106	processor	process	ok	\N	0	2026-08-22 22:35:59.737256+03
2107	processor	process	ok	\N	0	2026-08-22 22:36:29.742914+03
2109	processor	process	ok	\N	0	2026-08-22 22:36:59.749216+03
2110	processor	process	ok	\N	0	2026-08-22 22:37:29.758704+03
2112	processor	process	ok	\N	0	2026-08-22 22:37:59.767034+03
2113	processor	process	ok	\N	0	2026-08-22 22:38:29.776096+03
2115	processor	process	ok	\N	0	2026-08-22 22:38:59.786127+03
2116	processor	process	ok	\N	0	2026-08-22 22:39:29.79212+03
2118	processor	process	ok	\N	0	2026-08-22 22:39:59.797456+03
2119	processor	process	ok	\N	0	2026-08-22 22:40:29.804199+03
2121	processor	process	ok	\N	0	2026-08-22 22:40:59.811236+03
798	collector	collect	ok	\N	0	2026-08-22 15:20:10.402888+03
801	collector	collect	ok	\N	0	2026-08-22 15:21:10.42124+03
804	collector	collect	ok	\N	0	2026-08-22 15:22:10.439068+03
807	collector	collect	ok	\N	0	2026-08-22 15:23:10.455313+03
1308	collector	collect	ok	\N	0	2026-08-22 18:10:09.497945+03
1311	collector	collect	ok	\N	0	2026-08-22 18:11:09.519936+03
1314	collector	collect	ok	\N	0	2026-08-22 18:12:09.543159+03
1317	collector	collect	ok	\N	0	2026-08-22 18:13:09.569425+03
1320	collector	collect	ok	\N	0	2026-08-22 18:14:09.610737+03
1353	collector	collect	ok	\N	0	2026-08-22 18:25:09.86913+03
1356	collector	collect	ok	\N	0	2026-08-22 18:26:09.887799+03
1359	collector	collect	ok	\N	0	2026-08-22 18:27:09.906047+03
1362	collector	collect	ok	\N	0	2026-08-22 18:28:09.928324+03
1365	collector	collect	ok	\N	0	2026-08-22 18:29:09.945661+03
1398	collector	collect	ok	\N	0	2026-08-22 18:40:10.178626+03
1401	collector	collect	ok	\N	0	2026-08-22 18:41:10.200473+03
1404	collector	collect	ok	\N	0	2026-08-22 18:42:10.230527+03
1407	collector	collect	ok	\N	0	2026-08-22 18:43:10.249805+03
1410	collector	collect	ok	\N	0	2026-08-22 18:44:10.27144+03
1443	collector	collect	ok	\N	0	2026-08-22 18:55:10.499049+03
1446	collector	collect	ok	\N	0	2026-08-22 18:56:10.519221+03
1449	collector	collect	ok	\N	0	2026-08-22 18:57:10.540079+03
1452	collector	collect	ok	\N	0	2026-08-22 18:58:10.560122+03
1455	collector	collect	ok	\N	0	2026-08-22 18:59:10.57908+03
1885	processor	process	ok	\N	0	2026-08-22 21:22:35.483615+03
1886	processor	process	ok	\N	0	2026-08-22 21:23:05.488471+03
1888	processor	process	ok	\N	0	2026-08-22 21:23:35.493388+03
1889	processor	process	ok	\N	0	2026-08-22 21:24:05.496895+03
1891	processor	process	ok	\N	0	2026-08-22 21:24:35.50298+03
1892	processor	process	ok	\N	0	2026-08-22 21:25:05.507637+03
1894	processor	process	ok	\N	0	2026-08-22 21:25:35.515539+03
1895	processor	process	ok	\N	0	2026-08-22 21:26:05.519611+03
1897	processor	process	ok	\N	0	2026-08-22 21:26:35.52397+03
1898	processor	process	ok	\N	0	2026-08-22 21:27:05.527324+03
1900	processor	process	ok	\N	0	2026-08-22 21:27:35.534222+03
1901	processor	process	ok	\N	0	2026-08-22 21:28:05.539683+03
1903	processor	process	ok	\N	0	2026-08-22 21:28:35.549344+03
1904	processor	process	ok	\N	0	2026-08-22 21:29:05.55668+03
1906	processor	process	ok	\N	0	2026-08-22 21:29:35.563558+03
1907	processor	process	ok	\N	0	2026-08-22 21:30:05.571574+03
1909	processor	process	ok	\N	0	2026-08-22 21:30:35.57801+03
1910	processor	process	ok	\N	0	2026-08-22 21:31:05.583795+03
1912	processor	process	ok	\N	0	2026-08-22 21:31:35.592334+03
1913	processor	process	ok	\N	0	2026-08-22 21:32:05.600895+03
1915	processor	process	ok	\N	0	2026-08-22 21:32:35.610419+03
1916	processor	process	ok	\N	0	2026-08-22 21:33:05.615733+03
1918	processor	process	ok	\N	0	2026-08-22 21:33:35.622789+03
1919	processor	process	ok	\N	0	2026-08-22 21:34:05.628828+03
1921	processor	process	ok	\N	0	2026-08-22 21:34:35.638224+03
1922	processor	process	ok	\N	0	2026-08-22 21:35:05.642967+03
1924	processor	process	ok	\N	0	2026-08-22 21:35:35.647893+03
1925	processor	process	ok	\N	0	2026-08-22 21:36:05.661918+03
2122	processor	process	ok	\N	0	2026-08-22 22:41:29.818708+03
2124	processor	process	ok	\N	0	2026-08-22 22:41:59.82471+03
2125	processor	process	ok	\N	0	2026-08-22 22:42:29.832635+03
2127	processor	process	ok	\N	0	2026-08-22 22:42:59.839035+03
2128	processor	process	ok	\N	0	2026-08-22 22:43:29.844354+03
2130	processor	process	ok	\N	0	2026-08-22 22:43:59.850079+03
2131	processor	process	ok	\N	0	2026-08-22 22:44:29.859944+03
2133	processor	process	ok	\N	0	2026-08-22 22:44:59.867298+03
2134	processor	process	ok	\N	0	2026-08-22 22:45:29.87492+03
2136	processor	process	ok	\N	0	2026-08-22 22:45:59.881612+03
2137	processor	process	ok	\N	0	2026-08-22 22:46:29.890161+03
2139	processor	process	ok	\N	0	2026-08-22 22:46:59.901018+03
2140	processor	process	ok	\N	0	2026-08-22 22:47:29.907832+03
2142	processor	process	ok	\N	0	2026-08-22 22:47:59.915995+03
2143	processor	process	ok	\N	0	2026-08-22 22:48:29.924056+03
2145	processor	process	ok	\N	0	2026-08-22 22:48:59.930176+03
2146	processor	process	ok	\N	0	2026-08-22 22:49:29.939102+03
2148	processor	process	ok	\N	0	2026-08-22 22:49:59.952064+03
2149	processor	process	ok	\N	0	2026-08-22 22:50:29.962026+03
810	collector	collect	ok	\N	0	2026-08-22 15:24:10.473034+03
813	collector	collect	ok	\N	0	2026-08-22 15:25:10.493678+03
816	collector	collect	ok	\N	0	2026-08-22 15:26:10.511579+03
819	collector	collect	ok	\N	0	2026-08-22 15:27:10.530115+03
822	collector	collect	ok	\N	0	2026-08-22 15:28:10.551327+03
1459	processor	process	ok	\N	0	2026-08-22 19:00:39.639819+03
1460	processor	process	ok	\N	0	2026-08-22 19:01:09.649217+03
1462	processor	process	ok	\N	0	2026-08-22 19:01:39.656145+03
1463	processor	process	ok	\N	0	2026-08-22 19:02:09.663695+03
1465	processor	process	ok	\N	0	2026-08-22 19:02:39.673316+03
1466	processor	process	ok	\N	0	2026-08-22 19:03:09.680063+03
1887	collector	collect	ok	\N	0	2026-08-22 21:23:08.14364+03
1890	collector	collect	ok	\N	0	2026-08-22 21:24:08.165848+03
1923	collector	collect	ok	\N	0	2026-08-22 21:35:08.52451+03
1926	collector	collect	ok	\N	0	2026-08-22 21:36:08.565547+03
2123	collector	collect	ok	\N	0	2026-08-22 22:41:32.122269+03
2126	collector	collect	ok	\N	0	2026-08-22 22:42:32.142938+03
2129	collector	collect	ok	\N	0	2026-08-22 22:43:32.167201+03
2132	collector	collect	ok	\N	0	2026-08-22 22:44:32.186478+03
825	collector	collect	ok	\N	0	2026-08-22 15:29:10.568822+03
828	collector	collect	ok	\N	0	2026-08-22 15:30:10.587411+03
831	collector	collect	ok	\N	0	2026-08-22 15:31:10.605528+03
832	processor	process	ok	\N	0	2026-08-22 15:31:38.012016+03
833	processor	process	ok	\N	0	2026-08-22 15:32:08.021338+03
834	collector	collect	ok	\N	0	2026-08-22 15:32:10.630925+03
835	processor	process	ok	\N	0	2026-08-22 15:32:38.027608+03
836	processor	process	ok	\N	0	2026-08-22 15:33:08.036302+03
837	collector	collect	ok	\N	0	2026-08-22 15:33:10.651323+03
838	processor	process	ok	\N	0	2026-08-22 15:33:38.044793+03
839	processor	process	ok	\N	0	2026-08-22 15:34:08.051345+03
840	collector	collect	ok	\N	0	2026-08-22 15:34:10.669079+03
841	processor	process	ok	\N	0	2026-08-22 15:34:38.060632+03
842	processor	process	ok	\N	0	2026-08-22 15:35:08.068043+03
843	collector	collect	ok	\N	0	2026-08-22 15:35:10.687972+03
844	processor	process	ok	\N	0	2026-08-22 15:35:38.074968+03
845	processor	process	ok	\N	0	2026-08-22 15:36:08.082504+03
846	collector	collect	ok	\N	0	2026-08-22 15:36:10.708786+03
847	processor	process	ok	\N	0	2026-08-22 15:36:38.089342+03
848	processor	process	ok	\N	0	2026-08-22 15:37:08.097896+03
849	collector	collect	ok	\N	0	2026-08-22 15:37:10.727115+03
850	processor	process	ok	\N	0	2026-08-22 15:37:38.105942+03
851	processor	process	ok	\N	0	2026-08-22 15:38:08.111587+03
852	collector	collect	ok	\N	0	2026-08-22 15:38:10.746679+03
853	processor	process	ok	\N	0	2026-08-22 15:38:38.117869+03
854	processor	process	ok	\N	0	2026-08-22 15:39:08.125071+03
855	collector	collect	ok	\N	0	2026-08-22 15:39:10.767486+03
856	processor	process	ok	\N	0	2026-08-22 15:39:38.133857+03
857	processor	process	ok	\N	0	2026-08-22 15:40:08.139972+03
858	collector	collect	ok	\N	0	2026-08-22 15:40:10.785758+03
859	processor	process	ok	\N	0	2026-08-22 15:40:38.146074+03
860	processor	process	ok	\N	0	2026-08-22 15:41:08.155383+03
861	collector	collect	ok	\N	0	2026-08-22 15:41:10.805274+03
862	processor	process	ok	\N	0	2026-08-22 15:41:38.164677+03
863	processor	process	ok	\N	0	2026-08-22 15:42:08.171096+03
864	collector	collect	ok	\N	0	2026-08-22 15:42:10.823658+03
865	processor	process	ok	\N	0	2026-08-22 15:42:38.175807+03
866	processor	process	ok	\N	0	2026-08-22 15:43:08.183439+03
867	collector	collect	ok	\N	0	2026-08-22 15:43:10.842244+03
868	processor	process	ok	\N	0	2026-08-22 15:43:38.187663+03
869	processor	process	ok	\N	0	2026-08-22 15:44:08.194276+03
870	collector	collect	ok	\N	0	2026-08-22 15:44:10.863873+03
871	processor	process	ok	\N	0	2026-08-22 15:44:38.200677+03
872	processor	process	ok	\N	0	2026-08-22 15:45:08.207773+03
873	collector	collect	ok	\N	0	2026-08-22 15:45:10.882863+03
874	processor	process	ok	\N	0	2026-08-22 15:45:38.215498+03
875	processor	process	ok	\N	0	2026-08-22 15:46:08.223484+03
876	collector	collect	ok	\N	0	2026-08-22 15:46:10.900821+03
877	processor	process	ok	\N	0	2026-08-22 15:46:38.230721+03
878	processor	process	ok	\N	0	2026-08-22 15:47:08.239654+03
879	collector	collect	ok	\N	0	2026-08-22 15:47:10.920289+03
880	processor	process	ok	\N	0	2026-08-22 15:47:38.245946+03
881	processor	process	ok	\N	0	2026-08-22 15:48:08.251843+03
882	collector	collect	ok	\N	0	2026-08-22 15:48:10.938109+03
883	processor	process	ok	\N	0	2026-08-22 15:48:38.258052+03
884	processor	process	ok	\N	0	2026-08-22 15:49:08.267788+03
885	collector	collect	ok	\N	0	2026-08-22 15:49:10.955645+03
886	processor	process	ok	\N	0	2026-08-22 15:49:38.278189+03
887	processor	process	ok	\N	0	2026-08-22 15:50:08.287872+03
888	collector	collect	ok	\N	0	2026-08-22 15:50:10.975128+03
889	processor	process	ok	\N	0	2026-08-22 15:50:38.295825+03
890	processor	process	ok	\N	0	2026-08-22 15:51:08.304536+03
891	collector	collect	ok	\N	0	2026-08-22 15:51:10.994047+03
892	processor	process	ok	\N	0	2026-08-22 15:51:38.3121+03
893	processor	process	ok	\N	0	2026-08-22 15:52:08.319196+03
894	collector	collect	ok	\N	0	2026-08-22 15:52:11.012502+03
895	processor	process	ok	\N	0	2026-08-22 15:52:38.324714+03
896	processor	process	ok	\N	0	2026-08-22 15:53:08.331464+03
897	collector	collect	ok	\N	0	2026-08-22 15:53:11.033788+03
898	processor	process	ok	\N	0	2026-08-22 15:53:38.339032+03
899	processor	process	ok	\N	0	2026-08-22 15:54:08.344907+03
900	collector	collect	ok	\N	0	2026-08-22 15:54:11.053045+03
901	processor	process	ok	\N	0	2026-08-22 15:54:38.34922+03
902	processor	process	ok	\N	0	2026-08-22 15:55:08.35412+03
903	collector	collect	ok	\N	0	2026-08-22 15:55:11.070967+03
904	processor	process	ok	\N	0	2026-08-22 15:55:38.359414+03
905	processor	process	ok	\N	0	2026-08-22 15:56:08.365946+03
906	collector	collect	ok	\N	0	2026-08-22 15:56:11.088596+03
907	processor	process	ok	\N	0	2026-08-22 15:56:38.370299+03
908	processor	process	ok	\N	0	2026-08-22 15:57:08.379143+03
909	collector	collect	ok	\N	0	2026-08-22 15:57:11.107817+03
910	processor	process	ok	\N	0	2026-08-22 15:57:38.383374+03
911	processor	process	ok	\N	0	2026-08-22 15:58:08.389835+03
912	collector	collect	ok	\N	0	2026-08-22 15:58:11.12764+03
913	processor	process	ok	\N	0	2026-08-22 15:58:38.39737+03
914	processor	process	ok	\N	0	2026-08-22 15:59:08.402985+03
915	collector	collect	ok	\N	0	2026-08-22 15:59:11.14594+03
916	processor	process	ok	\N	0	2026-08-22 15:59:38.40875+03
917	processor	process	ok	\N	0	2026-08-22 16:00:08.41663+03
918	collector	collect	ok	\N	0	2026-08-22 16:00:11.162218+03
919	processor	process	ok	\N	0	2026-08-22 16:00:38.421729+03
920	processor	process	ok	\N	0	2026-08-22 16:01:08.427108+03
921	collector	collect	ok	\N	0	2026-08-22 16:01:11.178757+03
922	processor	process	ok	\N	0	2026-08-22 16:01:38.432541+03
923	processor	process	ok	\N	0	2026-08-22 16:02:08.437845+03
924	collector	collect	ok	\N	0	2026-08-22 16:02:11.198632+03
925	processor	process	ok	\N	0	2026-08-22 16:02:38.446843+03
926	processor	process	ok	\N	0	2026-08-22 16:03:08.457821+03
927	collector	collect	ok	\N	0	2026-08-22 16:03:11.218939+03
928	processor	process	ok	\N	0	2026-08-22 16:03:38.473129+03
929	processor	process	ok	\N	0	2026-08-22 16:04:08.48446+03
930	collector	collect	ok	\N	0	2026-08-22 16:04:11.237818+03
931	processor	process	ok	\N	0	2026-08-22 16:04:38.494221+03
932	processor	process	ok	\N	0	2026-08-22 16:05:08.505238+03
933	collector	collect	ok	\N	0	2026-08-22 16:05:11.256465+03
934	processor	process	ok	\N	0	2026-08-22 16:05:38.513448+03
935	processor	process	ok	\N	0	2026-08-22 16:06:08.520475+03
936	collector	collect	ok	\N	0	2026-08-22 16:06:11.27663+03
937	processor	process	ok	\N	0	2026-08-22 16:06:38.526571+03
938	processor	process	ok	\N	0	2026-08-22 16:07:08.535075+03
939	collector	collect	ok	\N	0	2026-08-22 16:07:11.294923+03
940	processor	process	ok	\N	0	2026-08-22 16:07:38.53977+03
941	processor	process	ok	\N	0	2026-08-22 16:08:08.543456+03
942	collector	collect	ok	\N	0	2026-08-22 16:08:11.313253+03
943	processor	process	ok	\N	0	2026-08-22 16:08:38.546388+03
944	processor	process	ok	\N	0	2026-08-22 16:09:08.553878+03
945	collector	collect	ok	\N	0	2026-08-22 16:09:11.333175+03
946	processor	process	ok	\N	0	2026-08-22 16:09:38.562753+03
947	processor	process	ok	\N	0	2026-08-22 16:10:08.571035+03
948	collector	collect	ok	\N	0	2026-08-22 16:10:11.354642+03
949	processor	process	ok	\N	0	2026-08-22 16:10:38.579087+03
950	processor	process	ok	\N	0	2026-08-22 16:11:08.5859+03
952	processor	process	ok	\N	0	2026-08-22 16:11:38.591854+03
953	processor	process	ok	\N	0	2026-08-22 16:12:08.599147+03
955	processor	process	ok	\N	0	2026-08-22 16:12:38.605732+03
956	processor	process	ok	\N	0	2026-08-22 16:13:08.615901+03
958	processor	process	ok	\N	0	2026-08-22 16:13:38.623066+03
959	processor	process	ok	\N	0	2026-08-22 16:14:08.628221+03
961	processor	process	ok	\N	0	2026-08-22 16:14:38.633163+03
962	processor	process	ok	\N	0	2026-08-22 16:15:08.64228+03
964	processor	process	ok	\N	0	2026-08-22 16:15:38.650884+03
965	processor	process	ok	\N	0	2026-08-22 16:16:08.657605+03
1468	processor	process	ok	\N	0	2026-08-22 19:03:39.689029+03
1469	processor	process	ok	\N	0	2026-08-22 19:04:09.698601+03
1471	processor	process	ok	\N	0	2026-08-22 19:04:39.706752+03
1472	processor	process	ok	\N	0	2026-08-22 19:05:09.71528+03
1474	processor	process	ok	\N	0	2026-08-22 19:05:39.722358+03
1475	processor	process	ok	\N	0	2026-08-22 19:06:09.726756+03
1477	processor	process	ok	\N	0	2026-08-22 19:06:39.735868+03
1478	processor	process	ok	\N	0	2026-08-22 19:07:09.745675+03
1480	processor	process	ok	\N	0	2026-08-22 19:07:39.754238+03
1481	processor	process	ok	\N	0	2026-08-22 19:08:09.758999+03
1483	processor	process	ok	\N	0	2026-08-22 19:08:39.768378+03
1484	processor	process	ok	\N	0	2026-08-22 19:09:09.776179+03
1486	processor	process	ok	\N	0	2026-08-22 19:09:39.782911+03
1487	processor	process	ok	\N	0	2026-08-22 19:10:09.788362+03
1489	processor	process	ok	\N	0	2026-08-22 19:10:39.797873+03
1490	processor	process	ok	\N	0	2026-08-22 19:11:09.806458+03
1492	processor	process	ok	\N	0	2026-08-22 19:11:39.815084+03
1493	processor	process	ok	\N	0	2026-08-22 19:12:09.823744+03
1495	processor	process	ok	\N	0	2026-08-22 19:12:39.83216+03
1496	processor	process	ok	\N	0	2026-08-22 19:13:09.838354+03
1498	processor	process	ok	\N	0	2026-08-22 19:13:39.847889+03
1499	processor	process	ok	\N	0	2026-08-22 19:14:09.856985+03
1501	processor	process	ok	\N	0	2026-08-22 19:14:39.861201+03
1502	processor	process	ok	\N	0	2026-08-22 19:15:09.87056+03
1504	processor	process	ok	\N	0	2026-08-22 19:15:39.879072+03
1505	processor	process	ok	\N	0	2026-08-22 19:16:09.887551+03
1507	processor	process	ok	\N	0	2026-08-22 19:16:39.895336+03
1508	processor	process	ok	\N	0	2026-08-22 19:17:09.902511+03
1510	processor	process	ok	\N	0	2026-08-22 19:17:39.90955+03
1511	processor	process	ok	\N	0	2026-08-22 19:18:09.91542+03
1513	processor	process	ok	\N	0	2026-08-22 19:18:39.923653+03
1514	processor	process	ok	\N	0	2026-08-22 19:19:09.928821+03
1516	processor	process	ok	\N	0	2026-08-22 19:19:39.937128+03
1517	processor	process	ok	\N	0	2026-08-22 19:20:09.94131+03
1519	processor	process	ok	\N	0	2026-08-22 19:20:39.948715+03
1520	processor	process	ok	\N	0	2026-08-22 19:21:09.950794+03
1522	processor	process	ok	\N	0	2026-08-22 19:21:39.959702+03
1523	processor	process	ok	\N	0	2026-08-22 19:22:09.965977+03
1525	processor	process	ok	\N	0	2026-08-22 19:22:39.973082+03
1526	processor	process	ok	\N	0	2026-08-22 19:23:09.977524+03
1528	processor	process	ok	\N	0	2026-08-22 19:23:39.985113+03
1529	processor	process	ok	\N	0	2026-08-22 19:24:09.990551+03
1531	processor	process	ok	\N	0	2026-08-22 19:24:39.996441+03
1532	processor	process	ok	\N	0	2026-08-22 19:25:10.003566+03
1534	processor	process	ok	\N	0	2026-08-22 19:25:40.010756+03
1535	processor	process	ok	\N	0	2026-08-22 19:26:10.017173+03
1537	processor	process	ok	\N	0	2026-08-22 19:26:40.027389+03
1538	processor	process	ok	\N	0	2026-08-22 19:27:10.034782+03
1540	processor	process	ok	\N	0	2026-08-22 19:27:40.044138+03
1541	processor	process	ok	\N	0	2026-08-22 19:28:10.0514+03
1543	processor	process	ok	\N	0	2026-08-22 19:28:40.059709+03
1544	processor	process	ok	\N	0	2026-08-22 19:29:10.068082+03
1546	processor	process	ok	\N	0	2026-08-22 19:29:40.077331+03
1547	processor	process	ok	\N	0	2026-08-22 19:30:10.082376+03
1549	processor	process	ok	\N	0	2026-08-22 19:30:40.091707+03
1550	processor	process	ok	\N	0	2026-08-22 19:31:10.100195+03
1552	processor	process	ok	\N	0	2026-08-22 19:31:40.109382+03
1553	processor	process	ok	\N	0	2026-08-22 19:32:10.118589+03
1555	processor	process	ok	\N	0	2026-08-22 19:32:40.125959+03
1556	processor	process	ok	\N	0	2026-08-22 19:33:10.133474+03
1558	processor	process	ok	\N	0	2026-08-22 19:33:40.140645+03
1559	processor	process	ok	\N	0	2026-08-22 19:34:10.149042+03
1561	processor	process	ok	\N	0	2026-08-22 19:34:40.156466+03
1562	processor	process	ok	\N	0	2026-08-22 19:35:10.16393+03
1564	processor	process	ok	\N	0	2026-08-22 19:35:40.170358+03
1565	processor	process	ok	\N	0	2026-08-22 19:36:10.179829+03
1567	processor	process	ok	\N	0	2026-08-22 19:36:40.187545+03
1568	processor	process	ok	\N	0	2026-08-22 19:37:10.193538+03
1570	processor	process	ok	\N	0	2026-08-22 19:37:40.198619+03
1571	processor	process	ok	\N	0	2026-08-22 19:38:10.205966+03
1573	processor	process	ok	\N	0	2026-08-22 19:38:40.212458+03
1574	processor	process	ok	\N	0	2026-08-22 19:39:10.221864+03
1576	processor	process	ok	\N	0	2026-08-22 19:39:40.228537+03
1577	processor	process	ok	\N	0	2026-08-22 19:40:10.235982+03
1579	processor	process	ok	\N	0	2026-08-22 19:40:40.242318+03
1580	processor	process	ok	\N	0	2026-08-22 19:41:10.249111+03
1582	processor	process	ok	\N	0	2026-08-22 19:41:40.254313+03
1583	processor	process	ok	\N	0	2026-08-22 19:42:10.263233+03
1585	processor	process	ok	\N	0	2026-08-22 19:42:40.269659+03
1586	processor	process	ok	\N	0	2026-08-22 19:43:10.275978+03
1588	processor	process	ok	\N	0	2026-08-22 19:43:40.335189+03
1589	processor	process	ok	\N	0	2026-08-22 19:44:10.342529+03
1591	processor	process	ok	\N	0	2026-08-22 19:44:40.350061+03
1592	processor	process	ok	\N	0	2026-08-22 19:45:10.356839+03
1594	processor	process	ok	\N	0	2026-08-22 19:45:40.365013+03
1595	processor	process	ok	\N	0	2026-08-22 19:46:10.370846+03
1597	processor	process	ok	\N	0	2026-08-22 19:46:40.379807+03
1598	processor	process	ok	\N	0	2026-08-22 19:47:10.389114+03
1600	processor	process	ok	\N	0	2026-08-22 19:47:40.398089+03
1601	processor	process	ok	\N	0	2026-08-22 19:48:10.404849+03
1603	processor	process	ok	\N	0	2026-08-22 19:48:40.411963+03
1604	processor	process	ok	\N	0	2026-08-22 19:49:10.417987+03
1606	processor	process	ok	\N	0	2026-08-22 19:49:40.425106+03
1607	processor	process	ok	\N	0	2026-08-22 19:50:10.429194+03
1609	processor	process	ok	\N	0	2026-08-22 19:50:40.436716+03
1610	processor	process	ok	\N	0	2026-08-22 19:51:10.444004+03
1612	processor	process	ok	\N	0	2026-08-22 19:51:40.452121+03
1613	processor	process	ok	\N	0	2026-08-22 19:52:10.459776+03
1615	processor	process	ok	\N	0	2026-08-22 19:52:40.467722+03
1616	processor	process	ok	\N	0	2026-08-22 19:53:10.477103+03
1618	processor	process	ok	\N	0	2026-08-22 19:53:40.485672+03
1619	processor	process	ok	\N	0	2026-08-22 19:54:10.495001+03
1621	processor	process	ok	\N	0	2026-08-22 19:54:40.503738+03
1622	processor	process	ok	\N	0	2026-08-22 19:55:10.512399+03
1624	processor	process	ok	\N	0	2026-08-22 19:55:40.52191+03
1625	processor	process	ok	\N	0	2026-08-22 19:56:10.529901+03
1627	processor	process	ok	\N	0	2026-08-22 19:56:40.53739+03
1628	processor	process	ok	\N	0	2026-08-22 19:57:10.546234+03
951	collector	collect	ok	\N	0	2026-08-22 16:11:11.373279+03
954	collector	collect	ok	\N	0	2026-08-22 16:12:11.395289+03
957	collector	collect	ok	\N	0	2026-08-22 16:13:11.419345+03
1470	collector	collect	ok	\N	0	2026-08-22 19:04:10.683733+03
1503	collector	collect	ok	\N	0	2026-08-22 19:15:10.906709+03
1506	collector	collect	ok	\N	0	2026-08-22 19:16:10.928631+03
1509	collector	collect	ok	\N	0	2026-08-22 19:17:10.950321+03
1512	collector	collect	ok	\N	0	2026-08-22 19:18:10.970879+03
1515	collector	collect	ok	\N	0	2026-08-22 19:19:10.992787+03
1548	collector	collect	ok	\N	0	2026-08-22 19:30:11.318458+03
1551	collector	collect	ok	\N	0	2026-08-22 19:31:11.338679+03
1554	collector	collect	ok	\N	0	2026-08-22 19:32:11.359209+03
1557	collector	collect	ok	\N	0	2026-08-22 19:33:11.37667+03
1560	collector	collect	ok	\N	0	2026-08-22 19:34:11.396258+03
1593	collector	collect	ok	\N	0	2026-08-22 19:45:11.728675+03
1596	collector	collect	ok	\N	0	2026-08-22 19:46:11.751493+03
1599	collector	collect	ok	\N	0	2026-08-22 19:47:11.771506+03
1602	collector	collect	ok	\N	0	2026-08-22 19:48:11.791165+03
1605	collector	collect	ok	\N	0	2026-08-22 19:49:11.810279+03
1638	collector	collect	ok	\N	0	2026-08-22 20:00:12.041943+03
1641	collector	collect	ok	\N	0	2026-08-22 20:01:12.063848+03
1644	collector	collect	ok	\N	0	2026-08-22 20:02:12.08424+03
1647	collector	collect	ok	\N	0	2026-08-22 20:03:12.10525+03
1650	collector	collect	ok	\N	0	2026-08-22 20:04:12.126203+03
1893	collector	collect	ok	\N	0	2026-08-22 21:25:08.184612+03
1896	collector	collect	ok	\N	0	2026-08-22 21:26:08.20332+03
1899	collector	collect	ok	\N	0	2026-08-22 21:27:08.226061+03
1902	collector	collect	ok	\N	0	2026-08-22 21:28:08.249033+03
1905	collector	collect	ok	\N	0	2026-08-22 21:29:08.277869+03
2135	collector	collect	ok	\N	0	2026-08-22 22:45:32.20483+03
2138	collector	collect	ok	\N	0	2026-08-22 22:46:32.228896+03
2141	collector	collect	ok	\N	0	2026-08-22 22:47:32.253968+03
2144	collector	collect	ok	\N	0	2026-08-22 22:48:32.275728+03
2147	collector	collect	ok	\N	0	2026-08-22 22:49:32.318385+03
960	collector	collect	ok	\N	0	2026-08-22 16:14:11.440593+03
963	collector	collect	ok	\N	0	2026-08-22 16:15:11.46492+03
966	collector	collect	ok	\N	0	2026-08-22 16:16:11.485202+03
967	processor	process	ok	\N	0	2026-08-22 16:16:38.667398+03
968	processor	process	ok	\N	0	2026-08-22 16:17:08.676365+03
969	collector	collect	ok	\N	0	2026-08-22 16:17:11.50484+03
970	processor	process	ok	\N	0	2026-08-22 16:17:38.681642+03
971	processor	process	ok	\N	0	2026-08-22 16:18:08.690982+03
972	collector	collect	ok	\N	0	2026-08-22 16:18:11.523835+03
973	processor	process	ok	\N	0	2026-08-22 16:18:38.697275+03
974	processor	process	ok	\N	0	2026-08-22 16:19:08.704818+03
975	collector	collect	ok	\N	0	2026-08-22 16:19:11.544172+03
976	processor	process	ok	\N	0	2026-08-22 16:19:38.711081+03
977	processor	process	ok	\N	0	2026-08-22 16:20:08.719912+03
978	collector	collect	ok	\N	0	2026-08-22 16:20:11.56696+03
979	processor	process	ok	\N	0	2026-08-22 16:20:38.728179+03
980	processor	process	ok	\N	0	2026-08-22 16:21:08.734571+03
981	collector	collect	ok	\N	0	2026-08-22 16:21:11.588325+03
982	processor	process	ok	\N	0	2026-08-22 16:21:38.743588+03
983	processor	process	ok	\N	0	2026-08-22 16:22:08.752219+03
984	collector	collect	ok	\N	0	2026-08-22 16:22:11.607186+03
985	processor	process	ok	\N	0	2026-08-22 16:22:38.758628+03
986	processor	process	ok	\N	0	2026-08-22 16:23:08.766002+03
987	collector	collect	ok	\N	0	2026-08-22 16:23:11.62636+03
988	processor	process	ok	\N	0	2026-08-22 16:23:38.77445+03
989	processor	process	ok	\N	0	2026-08-22 16:24:08.781938+03
990	collector	collect	ok	\N	0	2026-08-22 16:24:11.644687+03
991	processor	process	ok	\N	0	2026-08-22 16:24:38.791388+03
992	processor	process	ok	\N	0	2026-08-22 16:25:08.797839+03
993	collector	collect	ok	\N	0	2026-08-22 16:25:11.66568+03
994	processor	process	ok	\N	0	2026-08-22 16:25:38.802816+03
995	processor	process	ok	\N	0	2026-08-22 16:26:08.810414+03
996	collector	collect	ok	\N	0	2026-08-22 16:26:11.686048+03
997	processor	process	ok	\N	0	2026-08-22 16:26:38.818031+03
998	processor	process	ok	\N	0	2026-08-22 16:27:08.826514+03
999	collector	collect	ok	\N	0	2026-08-22 16:27:11.705601+03
1000	processor	process	ok	\N	0	2026-08-22 16:27:38.834196+03
1001	processor	process	ok	\N	0	2026-08-22 16:28:08.842029+03
1002	collector	collect	ok	\N	0	2026-08-22 16:28:11.726712+03
1003	processor	process	ok	\N	0	2026-08-22 16:28:38.849825+03
1004	processor	process	ok	\N	0	2026-08-22 16:29:08.858199+03
1005	collector	collect	ok	\N	0	2026-08-22 16:29:11.748134+03
1006	processor	process	ok	\N	0	2026-08-22 16:29:38.866263+03
1007	processor	process	ok	\N	0	2026-08-22 16:30:08.87253+03
1008	collector	collect	ok	\N	0	2026-08-22 16:30:11.769006+03
1009	processor	process	ok	\N	0	2026-08-22 16:30:38.879213+03
1010	processor	process	ok	\N	0	2026-08-22 16:31:08.887526+03
1011	collector	collect	ok	\N	0	2026-08-22 16:31:11.79092+03
1012	processor	process	ok	\N	0	2026-08-22 16:31:38.895651+03
1013	processor	process	ok	\N	0	2026-08-22 16:32:08.972762+03
1014	collector	collect	ok	\N	0	2026-08-22 16:32:11.812729+03
1015	processor	process	ok	\N	0	2026-08-22 16:32:38.977181+03
1016	processor	process	ok	\N	0	2026-08-22 16:33:08.983737+03
1017	collector	collect	ok	\N	0	2026-08-22 16:33:11.831012+03
1018	processor	process	ok	\N	0	2026-08-22 16:33:38.993371+03
1019	processor	process	ok	\N	0	2026-08-22 16:34:09.00259+03
1020	collector	collect	ok	\N	0	2026-08-22 16:34:11.851349+03
1021	processor	process	ok	\N	0	2026-08-22 16:34:39.008968+03
1022	processor	process	ok	\N	0	2026-08-22 16:35:09.013907+03
1023	collector	collect	ok	\N	0	2026-08-22 16:35:11.870981+03
1024	processor	process	ok	\N	0	2026-08-22 16:35:39.021643+03
1025	processor	process	ok	\N	0	2026-08-22 16:36:09.027038+03
1026	collector	collect	ok	\N	0	2026-08-22 16:36:11.890486+03
1027	processor	process	ok	\N	0	2026-08-22 16:36:39.033795+03
1028	processor	process	ok	\N	0	2026-08-22 16:37:09.040777+03
1029	collector	collect	ok	\N	0	2026-08-22 16:37:11.911254+03
1030	processor	process	ok	\N	0	2026-08-22 16:37:39.051068+03
1031	processor	process	ok	\N	0	2026-08-22 16:38:09.060651+03
1032	collector	collect	ok	\N	0	2026-08-22 16:38:11.930773+03
1033	processor	process	ok	\N	0	2026-08-22 16:38:39.068884+03
1034	processor	process	ok	\N	0	2026-08-22 16:39:09.074701+03
1035	collector	collect	ok	\N	0	2026-08-22 16:39:11.95199+03
1036	processor	process	ok	\N	0	2026-08-22 16:39:39.083017+03
1037	processor	process	ok	\N	0	2026-08-22 16:40:09.08695+03
1038	collector	collect	ok	\N	0	2026-08-22 16:40:11.974138+03
1039	processor	process	ok	\N	0	2026-08-22 16:40:39.091285+03
1040	processor	process	ok	\N	0	2026-08-22 16:41:09.09908+03
1041	collector	collect	ok	\N	0	2026-08-22 16:41:11.994798+03
1042	processor	process	ok	\N	0	2026-08-22 16:41:39.106227+03
1043	processor	process	ok	\N	0	2026-08-22 16:42:09.113688+03
1044	collector	collect	ok	\N	0	2026-08-22 16:42:12.015959+03
1045	processor	process	ok	\N	0	2026-08-22 16:42:39.11849+03
1046	processor	process	ok	\N	0	2026-08-22 16:43:09.15263+03
1047	collector	collect	ok	\N	0	2026-08-22 16:43:12.037567+03
1048	processor	process	ok	\N	0	2026-08-22 16:43:39.16049+03
1049	processor	process	ok	\N	0	2026-08-22 16:44:09.16834+03
1050	collector	collect	ok	\N	0	2026-08-22 16:44:12.065215+03
1051	processor	process	ok	\N	0	2026-08-22 16:44:39.173003+03
1052	processor	process	ok	\N	0	2026-08-22 16:45:09.179773+03
1053	collector	collect	ok	\N	0	2026-08-22 16:45:12.087071+03
1054	processor	process	ok	\N	0	2026-08-22 16:45:39.189135+03
1055	processor	process	ok	\N	0	2026-08-22 16:46:09.198205+03
1056	collector	collect	ok	\N	0	2026-08-22 16:46:12.104859+03
1057	processor	process	ok	\N	0	2026-08-22 16:46:39.202313+03
1058	processor	process	ok	\N	0	2026-08-22 16:47:09.20758+03
1059	collector	collect	ok	\N	0	2026-08-22 16:47:12.121797+03
1060	processor	process	ok	\N	0	2026-08-22 16:47:39.214371+03
1061	processor	process	ok	\N	0	2026-08-22 16:48:09.223306+03
1062	collector	collect	ok	\N	0	2026-08-22 16:48:12.142231+03
1063	processor	process	ok	\N	0	2026-08-22 16:48:39.231553+03
1064	processor	process	ok	\N	0	2026-08-22 16:49:09.240127+03
1065	collector	collect	ok	\N	0	2026-08-22 16:49:12.160318+03
1066	processor	process	ok	\N	0	2026-08-22 16:49:39.249541+03
1067	processor	process	ok	\N	0	2026-08-22 16:50:09.258048+03
1068	collector	collect	ok	\N	0	2026-08-22 16:50:12.179386+03
1069	processor	process	ok	\N	0	2026-08-22 16:50:39.262736+03
1070	processor	process	ok	\N	0	2026-08-22 16:51:09.268111+03
1071	collector	collect	ok	\N	0	2026-08-22 16:51:12.197781+03
1072	processor	process	ok	\N	0	2026-08-22 16:51:39.273227+03
1073	processor	process	ok	\N	0	2026-08-22 16:52:09.279117+03
1074	collector	collect	ok	\N	0	2026-08-22 16:52:12.217851+03
1075	processor	process	ok	\N	0	2026-08-22 16:52:39.285775+03
1076	processor	process	ok	\N	0	2026-08-22 16:53:09.290426+03
1077	collector	collect	ok	\N	0	2026-08-22 16:53:12.247929+03
1078	processor	process	ok	\N	0	2026-08-22 16:53:39.295227+03
1079	processor	process	ok	\N	0	2026-08-22 16:54:09.301618+03
1080	collector	collect	ok	\N	0	2026-08-22 16:54:12.269492+03
1081	processor	process	ok	\N	0	2026-08-22 16:54:39.308626+03
1082	processor	process	ok	\N	0	2026-08-22 16:55:09.316466+03
1083	collector	collect	ok	\N	0	2026-08-22 16:55:12.291052+03
1084	processor	process	ok	\N	0	2026-08-22 16:55:39.323028+03
1085	processor	process	ok	\N	0	2026-08-22 16:56:09.32926+03
1087	processor	process	ok	\N	0	2026-08-22 16:56:39.33592+03
1088	processor	process	ok	\N	0	2026-08-22 16:57:09.344309+03
1090	processor	process	ok	\N	0	2026-08-22 16:57:39.351501+03
1091	processor	process	ok	\N	0	2026-08-22 16:58:09.359726+03
1093	processor	process	ok	\N	0	2026-08-22 16:58:39.36619+03
1094	processor	process	ok	\N	0	2026-08-22 16:59:09.371886+03
1096	processor	process	ok	\N	0	2026-08-22 16:59:39.377962+03
1097	processor	process	ok	\N	0	2026-08-22 17:00:09.385612+03
1099	processor	process	ok	\N	0	2026-08-22 17:00:39.393066+03
1100	processor	process	ok	\N	0	2026-08-22 17:01:09.400037+03
1102	processor	process	ok	\N	0	2026-08-22 17:01:39.406314+03
1103	processor	process	ok	\N	0	2026-08-22 17:02:09.41068+03
1105	processor	process	ok	\N	0	2026-08-22 17:02:39.415829+03
1106	processor	process	ok	\N	0	2026-08-22 17:03:09.422547+03
1108	processor	process	ok	\N	0	2026-08-22 17:03:39.42767+03
1109	processor	process	ok	\N	0	2026-08-22 17:04:09.435458+03
1111	processor	process	ok	\N	0	2026-08-22 17:04:39.440645+03
1112	processor	process	ok	\N	0	2026-08-22 17:05:09.446463+03
1473	collector	collect	ok	\N	0	2026-08-22 19:05:10.705133+03
1476	collector	collect	ok	\N	0	2026-08-22 19:06:10.723143+03
1479	collector	collect	ok	\N	0	2026-08-22 19:07:10.741684+03
1482	collector	collect	ok	\N	0	2026-08-22 19:08:10.759294+03
1485	collector	collect	ok	\N	0	2026-08-22 19:09:10.778902+03
1518	collector	collect	ok	\N	0	2026-08-22 19:20:11.026961+03
1521	collector	collect	ok	\N	0	2026-08-22 19:21:11.046186+03
1524	collector	collect	ok	\N	0	2026-08-22 19:22:11.064057+03
1527	collector	collect	ok	\N	0	2026-08-22 19:23:11.085412+03
1530	collector	collect	ok	\N	0	2026-08-22 19:24:11.104921+03
1563	collector	collect	ok	\N	0	2026-08-22 19:35:11.41615+03
1566	collector	collect	ok	\N	0	2026-08-22 19:36:11.445908+03
1569	collector	collect	ok	\N	0	2026-08-22 19:37:11.470659+03
1572	collector	collect	ok	\N	0	2026-08-22 19:38:11.490375+03
1575	collector	collect	ok	\N	0	2026-08-22 19:39:11.51126+03
1608	collector	collect	ok	\N	0	2026-08-22 19:50:11.829778+03
1611	collector	collect	ok	\N	0	2026-08-22 19:51:11.850879+03
1614	collector	collect	ok	\N	0	2026-08-22 19:52:11.872357+03
1617	collector	collect	ok	\N	0	2026-08-22 19:53:11.892513+03
1620	collector	collect	ok	\N	0	2026-08-22 19:54:11.916841+03
1653	collector	collect	ok	\N	0	2026-08-22 20:05:12.147734+03
1656	collector	collect	ok	\N	0	2026-08-22 20:06:12.168518+03
1659	collector	collect	ok	\N	0	2026-08-22 20:07:12.189689+03
1662	collector	collect	ok	\N	0	2026-08-22 20:08:12.21272+03
1665	collector	collect	ok	\N	0	2026-08-22 20:09:12.237954+03
1908	collector	collect	ok	\N	0	2026-08-22 21:30:08.412066+03
1911	collector	collect	ok	\N	0	2026-08-22 21:31:08.431386+03
1914	collector	collect	ok	\N	0	2026-08-22 21:32:08.457305+03
1917	collector	collect	ok	\N	0	2026-08-22 21:33:08.47892+03
1920	collector	collect	ok	\N	0	2026-08-22 21:34:08.504109+03
2150	collector	collect	ok	\N	0	2026-08-22 22:50:32.347004+03
1086	collector	collect	ok	\N	0	2026-08-22 16:56:12.312825+03
1089	collector	collect	ok	\N	0	2026-08-22 16:57:12.332973+03
1092	collector	collect	ok	\N	0	2026-08-22 16:58:12.354337+03
1488	collector	collect	ok	\N	0	2026-08-22 19:10:10.796206+03
1491	collector	collect	ok	\N	0	2026-08-22 19:11:10.820667+03
1494	collector	collect	ok	\N	0	2026-08-22 19:12:10.842233+03
1497	collector	collect	ok	\N	0	2026-08-22 19:13:10.86231+03
1500	collector	collect	ok	\N	0	2026-08-22 19:14:10.884507+03
1533	collector	collect	ok	\N	0	2026-08-22 19:25:11.220619+03
1536	collector	collect	ok	\N	0	2026-08-22 19:26:11.237094+03
1539	collector	collect	ok	\N	0	2026-08-22 19:27:11.258535+03
1542	collector	collect	ok	\N	0	2026-08-22 19:28:11.277672+03
1545	collector	collect	ok	\N	0	2026-08-22 19:29:11.297913+03
1578	collector	collect	ok	\N	0	2026-08-22 19:40:11.528078+03
1581	collector	collect	ok	\N	0	2026-08-22 19:41:11.547902+03
1584	collector	collect	ok	\N	0	2026-08-22 19:42:11.569171+03
1587	collector	collect	ok	\N	0	2026-08-22 19:43:11.589925+03
1590	collector	collect	ok	\N	0	2026-08-22 19:44:11.709563+03
1623	collector	collect	ok	\N	0	2026-08-22 19:55:11.939567+03
1626	collector	collect	ok	\N	0	2026-08-22 19:56:11.957923+03
1629	collector	collect	ok	\N	0	2026-08-22 19:57:11.979743+03
1632	collector	collect	ok	\N	0	2026-08-22 19:58:11.999704+03
1635	collector	collect	ok	\N	0	2026-08-22 19:59:12.022058+03
1927	processor	process	ok	\N	0	2026-08-22 21:36:43.602225+03
1929	processor	process	ok	\N	0	2026-08-22 21:37:13.609364+03
1930	processor	process	ok	\N	0	2026-08-22 21:37:43.616289+03
1932	processor	process	ok	\N	0	2026-08-22 21:38:13.625407+03
1933	processor	process	ok	\N	0	2026-08-22 21:38:43.63663+03
1935	processor	process	ok	\N	0	2026-08-22 21:39:13.643921+03
1936	processor	process	ok	\N	0	2026-08-22 21:39:43.652449+03
1938	processor	process	ok	\N	0	2026-08-22 21:40:13.660869+03
1939	processor	process	ok	\N	0	2026-08-22 21:40:43.666849+03
1941	processor	process	ok	\N	0	2026-08-22 21:41:13.71967+03
1942	processor	process	ok	\N	0	2026-08-22 21:41:43.744312+03
1944	processor	process	ok	\N	0	2026-08-22 21:42:13.750465+03
1945	processor	process	ok	\N	0	2026-08-22 21:42:43.758701+03
1947	processor	process	ok	\N	0	2026-08-22 21:43:13.766439+03
1948	processor	process	ok	\N	0	2026-08-22 21:43:43.771309+03
1950	processor	process	ok	\N	0	2026-08-22 21:44:13.776524+03
2151	processor	process	ok	\N	0	2026-08-22 22:51:03.981962+03
2153	processor	process	ok	\N	0	2026-08-22 22:51:33.988761+03
2154	processor	process	ok	\N	0	2026-08-22 22:52:03.993088+03
2156	processor	process	ok	\N	0	2026-08-22 22:52:33.998095+03
2157	processor	process	ok	\N	0	2026-08-22 22:53:04.007905+03
2159	processor	process	ok	\N	0	2026-08-22 22:53:34.015156+03
2160	processor	process	ok	\N	0	2026-08-22 22:54:04.02354+03
2162	processor	process	ok	\N	0	2026-08-22 22:54:34.033945+03
2163	processor	process	ok	\N	0	2026-08-22 22:55:04.041712+03
2165	processor	process	ok	\N	0	2026-08-22 22:55:34.048348+03
2166	processor	process	ok	\N	0	2026-08-22 22:56:04.058731+03
2168	processor	process	ok	\N	0	2026-08-22 22:56:34.065539+03
2169	processor	process	ok	\N	0	2026-08-22 22:57:04.074066+03
2171	processor	process	ok	\N	0	2026-08-22 22:57:34.082516+03
2172	processor	process	ok	\N	0	2026-08-22 22:58:04.090118+03
2174	processor	process	ok	\N	0	2026-08-22 22:58:34.096865+03
2175	processor	process	ok	\N	0	2026-08-22 22:59:04.110259+03
1095	collector	collect	ok	\N	0	2026-08-22 16:59:12.372069+03
1098	collector	collect	ok	\N	0	2026-08-22 17:00:12.390706+03
1101	collector	collect	ok	\N	0	2026-08-22 17:01:12.41331+03
1104	collector	collect	ok	\N	0	2026-08-22 17:02:12.440668+03
1107	collector	collect	ok	\N	0	2026-08-22 17:03:12.463876+03
1630	processor	process	ok	\N	0	2026-08-22 19:57:40.552487+03
1631	processor	process	ok	\N	0	2026-08-22 19:58:10.560175+03
1633	processor	process	ok	\N	0	2026-08-22 19:58:40.566926+03
1634	processor	process	ok	\N	0	2026-08-22 19:59:10.575403+03
1636	processor	process	ok	\N	0	2026-08-22 19:59:40.579885+03
1637	processor	process	ok	\N	0	2026-08-22 20:00:10.589415+03
1639	processor	process	ok	\N	0	2026-08-22 20:00:40.595847+03
1640	processor	process	ok	\N	0	2026-08-22 20:01:10.603843+03
1642	processor	process	ok	\N	0	2026-08-22 20:01:40.61052+03
1643	processor	process	ok	\N	0	2026-08-22 20:02:10.617182+03
1645	processor	process	ok	\N	0	2026-08-22 20:02:40.62449+03
1646	processor	process	ok	\N	0	2026-08-22 20:03:10.63341+03
1648	processor	process	ok	\N	0	2026-08-22 20:03:40.641586+03
1649	processor	process	ok	\N	0	2026-08-22 20:04:10.650475+03
1651	processor	process	ok	\N	0	2026-08-22 20:04:40.659239+03
1652	processor	process	ok	\N	0	2026-08-22 20:05:10.668426+03
1654	processor	process	ok	\N	0	2026-08-22 20:05:40.67454+03
1655	processor	process	ok	\N	0	2026-08-22 20:06:10.682436+03
1657	processor	process	ok	\N	0	2026-08-22 20:06:40.689758+03
1658	processor	process	ok	\N	0	2026-08-22 20:07:10.696048+03
1660	processor	process	ok	\N	0	2026-08-22 20:07:40.703093+03
1661	processor	process	ok	\N	0	2026-08-22 20:08:10.711428+03
1663	processor	process	ok	\N	0	2026-08-22 20:08:40.720688+03
1664	processor	process	ok	\N	0	2026-08-22 20:09:10.727916+03
1928	collector	collect	ok	\N	0	2026-08-22 21:36:44.86249+03
1931	collector	collect	ok	\N	0	2026-08-22 21:37:44.89955+03
1934	collector	collect	ok	\N	0	2026-08-22 21:38:44.921095+03
1937	collector	collect	ok	\N	0	2026-08-22 21:39:44.943122+03
1940	collector	collect	ok	\N	0	2026-08-22 21:40:44.967098+03
2152	collector	collect	ok	\N	0	2026-08-22 22:51:05.23079+03
2155	collector	collect	ok	\N	0	2026-08-22 22:52:05.253207+03
2158	collector	collect	ok	\N	0	2026-08-22 22:53:05.27188+03
2161	collector	collect	ok	\N	0	2026-08-22 22:54:05.290709+03
2164	collector	collect	ok	\N	0	2026-08-22 22:55:05.316835+03
1110	collector	collect	ok	\N	0	2026-08-22 17:04:12.487422+03
1113	collector	collect	ok	\N	0	2026-08-22 17:05:12.508925+03
1114	processor	process	ok	\N	0	2026-08-22 17:05:39.45066+03
1115	processor	process	ok	\N	0	2026-08-22 17:06:09.45686+03
1116	collector	collect	ok	\N	0	2026-08-22 17:06:12.529136+03
1117	processor	process	ok	\N	0	2026-08-22 17:06:39.461643+03
1118	processor	process	ok	\N	0	2026-08-22 17:07:09.46979+03
1119	collector	collect	ok	\N	0	2026-08-22 17:07:12.550154+03
1120	processor	process	ok	\N	0	2026-08-22 17:07:39.477674+03
1121	processor	process	ok	\N	0	2026-08-22 17:08:09.484954+03
1122	collector	collect	ok	\N	0	2026-08-22 17:08:12.579195+03
1123	processor	process	ok	\N	0	2026-08-22 17:08:39.491786+03
1124	processor	process	ok	\N	0	2026-08-22 17:09:09.499107+03
1125	collector	collect	ok	\N	0	2026-08-22 17:09:12.601033+03
1126	processor	process	ok	\N	0	2026-08-22 17:09:39.505719+03
1127	processor	process	ok	\N	0	2026-08-22 17:10:09.511501+03
1128	collector	collect	ok	\N	0	2026-08-22 17:10:12.622478+03
1129	processor	process	ok	\N	0	2026-08-22 17:10:39.521695+03
1130	processor	process	ok	\N	0	2026-08-22 17:11:09.530378+03
1131	collector	collect	ok	\N	0	2026-08-22 17:11:12.642988+03
1132	processor	process	ok	\N	0	2026-08-22 17:11:39.535366+03
1133	processor	process	ok	\N	0	2026-08-22 17:12:09.54482+03
1134	collector	collect	ok	\N	0	2026-08-22 17:12:12.664439+03
1135	processor	process	ok	\N	0	2026-08-22 17:12:39.55404+03
1136	processor	process	ok	\N	0	2026-08-22 17:13:09.561427+03
1137	collector	collect	ok	\N	0	2026-08-22 17:13:12.684084+03
1138	processor	process	ok	\N	0	2026-08-22 17:13:39.568965+03
1139	processor	process	ok	\N	0	2026-08-22 17:14:09.575665+03
1140	collector	collect	ok	\N	0	2026-08-22 17:14:12.705001+03
1141	processor	process	ok	\N	0	2026-08-22 17:14:39.581759+03
1142	processor	process	ok	\N	0	2026-08-22 17:15:09.587796+03
1143	collector	collect	ok	\N	0	2026-08-22 17:15:12.727948+03
1144	processor	process	ok	\N	0	2026-08-22 17:15:39.597129+03
1145	processor	process	ok	\N	0	2026-08-22 17:16:09.603787+03
1146	collector	collect	ok	\N	0	2026-08-22 17:16:12.749562+03
1147	processor	process	ok	\N	0	2026-08-22 17:16:39.6113+03
1148	processor	process	ok	\N	0	2026-08-22 17:17:09.61941+03
1149	collector	collect	ok	\N	0	2026-08-22 17:17:12.772573+03
1150	processor	process	ok	\N	0	2026-08-22 17:17:39.626151+03
1151	processor	process	ok	\N	0	2026-08-22 17:18:09.63319+03
1152	collector	collect	ok	\N	0	2026-08-22 17:18:12.791958+03
1153	processor	process	ok	\N	0	2026-08-22 17:18:39.639945+03
1154	processor	process	ok	\N	0	2026-08-22 17:19:09.648343+03
1155	collector	collect	ok	\N	0	2026-08-22 17:19:12.814723+03
1156	processor	process	ok	\N	0	2026-08-22 17:19:39.657051+03
1157	processor	process	ok	\N	0	2026-08-22 17:20:09.664827+03
1158	collector	collect	ok	\N	0	2026-08-22 17:20:12.837057+03
1159	processor	process	ok	\N	0	2026-08-22 17:20:39.672667+03
1160	processor	process	ok	\N	0	2026-08-22 17:21:09.682441+03
1161	collector	collect	ok	\N	0	2026-08-22 17:21:12.861456+03
1162	processor	process	ok	\N	0	2026-08-22 17:21:39.678334+03
1163	processor	process	ok	\N	0	2026-08-22 17:22:19.213813+03
1164	collector	collect	ok	\N	0	2026-08-22 17:22:19.253619+03
1165	processor	process	ok	\N	0	2026-08-22 17:22:49.219776+03
1166	processor	process	ok	\N	0	2026-08-22 17:23:19.227705+03
1167	collector	collect	ok	\N	0	2026-08-22 17:23:19.27039+03
1168	processor	process	ok	\N	0	2026-08-22 17:23:49.233203+03
1169	processor	process	ok	\N	0	2026-08-22 17:24:19.239494+03
1170	collector	collect	ok	\N	0	2026-08-22 17:24:19.287111+03
1171	processor	process	ok	\N	0	2026-08-22 17:24:49.246289+03
1172	processor	process	ok	\N	0	2026-08-22 17:25:19.249634+03
1173	collector	collect	ok	\N	0	2026-08-22 17:25:19.303002+03
1174	processor	process	ok	\N	0	2026-08-22 17:25:49.256744+03
1175	processor	process	ok	\N	0	2026-08-22 17:26:19.263907+03
1176	collector	collect	ok	\N	0	2026-08-22 17:26:19.328092+03
1177	processor	process	ok	\N	0	2026-08-22 17:26:49.273809+03
1178	processor	process	ok	\N	0	2026-08-22 17:27:19.278355+03
1179	collector	collect	ok	\N	0	2026-08-22 17:27:19.348595+03
1180	processor	process	ok	\N	0	2026-08-22 17:27:49.282146+03
1181	processor	process	ok	\N	0	2026-08-22 17:28:19.28819+03
1182	collector	collect	ok	\N	0	2026-08-22 17:28:19.376766+03
1183	processor	process	ok	\N	0	2026-08-22 17:28:49.295493+03
1184	processor	process	ok	\N	0	2026-08-22 17:29:19.301649+03
1185	collector	collect	ok	\N	0	2026-08-22 17:29:19.397478+03
1186	processor	process	ok	\N	0	2026-08-22 17:29:49.309128+03
1187	processor	process	ok	\N	0	2026-08-22 17:30:19.3146+03
1188	collector	collect	ok	\N	0	2026-08-22 17:30:19.414423+03
1189	processor	process	ok	\N	0	2026-08-22 17:30:49.322089+03
1190	processor	process	ok	\N	0	2026-08-22 17:31:19.328837+03
1191	collector	collect	ok	\N	0	2026-08-22 17:31:19.442887+03
1192	processor	process	ok	\N	0	2026-08-22 17:31:49.334854+03
1193	processor	process	ok	\N	0	2026-08-22 17:32:19.342178+03
1194	collector	collect	ok	\N	0	2026-08-22 17:32:19.462953+03
1195	processor	process	ok	\N	0	2026-08-22 17:32:49.34976+03
1196	processor	process	ok	\N	0	2026-08-22 17:33:19.35426+03
1197	collector	collect	ok	\N	0	2026-08-22 17:33:19.482953+03
1198	processor	process	ok	\N	0	2026-08-22 17:33:49.362619+03
1199	processor	process	ok	\N	0	2026-08-22 17:34:19.368366+03
1200	collector	collect	ok	\N	0	2026-08-22 17:34:19.505116+03
1201	processor	process	ok	\N	0	2026-08-22 17:34:49.376372+03
1202	processor	process	ok	\N	0	2026-08-22 17:35:19.384353+03
1203	collector	collect	ok	\N	0	2026-08-22 17:35:19.522484+03
1204	processor	process	ok	\N	0	2026-08-22 17:35:49.390302+03
1205	processor	process	ok	\N	0	2026-08-22 17:36:19.396299+03
1206	collector	collect	ok	\N	0	2026-08-22 17:36:19.539715+03
1207	processor	process	ok	\N	0	2026-08-22 17:36:49.404395+03
1208	processor	process	ok	\N	0	2026-08-22 17:37:19.411647+03
1209	collector	collect	ok	\N	0	2026-08-22 17:37:19.55746+03
1210	processor	process	ok	\N	0	2026-08-22 17:37:49.417699+03
1211	processor	process	ok	\N	0	2026-08-22 17:38:19.420738+03
1212	collector	collect	ok	\N	0	2026-08-22 17:38:19.574069+03
1213	processor	process	ok	\N	0	2026-08-22 17:38:49.428975+03
1214	processor	process	ok	\N	0	2026-08-22 17:39:19.436925+03
1215	collector	collect	ok	\N	0	2026-08-22 17:39:19.58997+03
1216	processor	process	ok	\N	0	2026-08-22 17:39:49.442763+03
1217	processor	process	ok	\N	0	2026-08-22 17:40:19.448916+03
1218	collector	collect	ok	\N	0	2026-08-22 17:40:19.619456+03
1219	processor	process	ok	\N	0	2026-08-22 17:40:49.455238+03
1220	processor	process	ok	\N	0	2026-08-22 17:41:19.461768+03
1221	collector	collect	ok	\N	0	2026-08-22 17:41:19.638818+03
1222	processor	process	ok	\N	0	2026-08-22 17:41:49.469907+03
1223	processor	process	ok	\N	0	2026-08-22 17:42:19.475104+03
1224	collector	collect	ok	\N	0	2026-08-22 17:42:19.657973+03
1225	processor	process	ok	\N	0	2026-08-22 17:42:49.481433+03
1666	processor	process	ok	\N	0	2026-08-22 20:09:40.737426+03
1667	processor	process	ok	\N	0	2026-08-22 20:10:10.742384+03
1669	processor	process	ok	\N	0	2026-08-22 20:10:40.748304+03
1670	processor	process	ok	\N	0	2026-08-22 20:11:10.752298+03
1672	processor	process	ok	\N	0	2026-08-22 20:11:40.761781+03
1673	processor	process	ok	\N	0	2026-08-22 20:12:10.770562+03
\.


--
-- Data for Name: smm_ai_usage; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.smm_ai_usage (user_id, month, calls) FROM stdin;
\.


--
-- Data for Name: smm_automations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.smm_automations (id, user_id, brand_id, type, config, enabled, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: smm_brand_channels; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.smm_brand_channels (id, brand_id, network, external_id, title, kind, role, color_override, publish_enabled, collect_enabled, discussion_external_id, discussion_title, comments_collect_enabled, alert_enabled, save_conditions, processing, alert_delivery, alert_rules, conditions_mode, publish_targets, created_at, auth_status, auth_checked_at, auth_error, auth_capabilities) FROM stdin;
1	1	tg	-1002142359467	По ту сторону	channel	competitor	\N	f	f	\N	\N	f	f	[]	{}	{}	[]	any_of	[]	2026-08-22 18:01:37.534585+03	not_required	2026-08-22 19:20:28.93328+03	\N	{}
2	1	tg	-1001677806302	ЗМ-ФБТ-11	channel	own	\N	f	t	\N	\N	f	f	[]	{}	{}	[]	any_of	[]	2026-08-22 19:00:36.93578+03	connected	2026-08-22 19:51:28.57561+03	\N	{"can_alert": true, "can_collect": true, "can_publish_text": true}
4	1	tg	-1002026625379	Кибер Тороп	channel	own	\N	f	t	\N	\N	f	f	[]	{}	{}	[]	any_of	[]	2026-08-22 21:39:59.166281+03	connected	2026-08-22 19:51:30.011181+03	\N	{"can_alert": true, "can_collect": true, "can_publish_text": true}
15	1	tg	-1002009872429	Экономический ежедневник	channel	own	\N	f	t	\N	\N	f	f	[]	{}	{}	[]	any_of	[]	2026-08-22 21:47:33.043318+03	connected	2026-08-22 19:51:31.678089+03	\N	{"can_alert": true, "can_collect": true, "can_publish_text": true}
14	1	tg	-1001411610346	Профита нет. А если найду?	channel	source	\N	f	t	\N	\N	f	f	[]	{}	{}	[]	any_of	[]	2026-08-22 21:47:16.328574+03	connected	2026-08-22 19:51:33.851407+03	\N	{"can_alert": true, "can_collect": true, "can_publish_text": true}
\.


--
-- Data for Name: smm_brands; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.smm_brands (id, user_id, group_id, name, color, created_at, updated_at) FROM stdin;
1	1	\N	Test Admin	#EC4899	2026-08-22 17:25:55.951829+03	2026-08-22 17:25:55.951829+03
2	1	\N	Test Admin 2	#84CC16	2026-08-22 18:00:32.028414+03	2026-08-22 18:00:32.028414+03
\.


--
-- Data for Name: smm_channel_counters; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.smm_channel_counters (id, user_id, channel_id, day, sent, received, failed, alerts_sent) FROM stdin;
\.


--
-- Data for Name: smm_channel_metric_snapshots; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.smm_channel_metric_snapshots (id, channel_id, subscribers, captured_at) FROM stdin;
\.


--
-- Data for Name: smm_competitor_snapshots; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.smm_competitor_snapshots (id, channel_id, external_post_id, post_text, views, likes, comments, reposts, posted_at, collected_at) FROM stdin;
\.


--
-- Data for Name: smm_inbox_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.smm_inbox_items (id, user_id, brand_id, network, channel_id, thread_id, type, author, text, status, external_msg_id, edited_text, meta, created_at) FROM stdin;
\.


--
-- Data for Name: smm_message_events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.smm_message_events (id, user_id, channel_id, direction, platform, post_id, external_msg_id, metadata, created_at) FROM stdin;
\.


--
-- Data for Name: smm_post_metric_snapshots; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.smm_post_metric_snapshots (id, user_id, platform, post_id, views, likes, comments, reposts, captured_at) FROM stdin;
\.


--
-- Data for Name: smm_publish_jobs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.smm_publish_jobs (id, user_id, brand_id, source_text, media, targets, adapters_result, publish_at, status, retry_count, last_error, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: system_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.system_settings (key, value, updated_at) FROM stdin;
ai_enabled	true	2026-08-22 10:54:08.704668+03
\.


--
-- Data for Name: tg_dedup_cache; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tg_dedup_cache (id, user_id, text_hash, chat_id, rule_id, channel_to_post, expires_at, created_at) FROM stdin;
\.


--
-- Data for Name: tg_digests; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tg_digests (id, user_id, chat_id, digest_text, message_count, created_at) FROM stdin;
\.


--
-- Data for Name: tg_events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tg_events (id, user_id, chat_id, message_id, event_type, rule_id, matched_conditions, text_hash, text_preview, metadata, created_at) FROM stdin;
\.


--
-- Data for Name: tg_post_templates; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tg_post_templates (id, user_id, name, text, hashtags, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tg_posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tg_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, metadata, publish_at, telegram_message_id, telegram_chat_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tg_profiles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tg_profiles (id, user_id, publish_enabled, collect_enabled, schedule_type, time_intervals, api_id, api_hash, chats_to_read, save_conditions, channel_to_post, channels_to_post, alert_enabled, alert_rules, process_enabled, processing_description, remove_emojis, remove_images, clean_html, process_services, status_review_after_process, add_static_html, static_html_content, telegram_username, auth_state, auth_phone_code_hash, auth_phone_number, summarize_enabled, summarize_min_length, digest_interval_min, digest_channel, classification_enabled, classification_categories, created_at, updated_at) FROM stdin;
1	1	f	f	immediate	[]	15723016	fd10c198eaa94bc4fe3f82415eb46ee6	[]	[]	\N	[]	f	[]	f	\N	f	f	f	\N	f	f	\N	pulchrum	authorized	\N	+79265990443	f	500	30	\N	f	["новости", "реклама", "технологии", "финансы", "другое"]	2026-08-22 22:16:34.610962+03	2026-08-22 22:16:47.269679+03
\.


--
-- Data for Name: tg_summary_cache; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tg_summary_cache (id, text_hash, summary, expires_at, created_at) FROM stdin;
\.


--
-- Data for Name: threads_posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.threads_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: threads_profiles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.threads_profiles (id, user_id, publish_enabled, collect_enabled, schedule_type, time_intervals, access_token, refresh_token, token_expires_at, threads_user_id, instagram_handle, process_enabled, processing_description, remove_emojis, remove_images, clean_html, process_services, status_review_after_process, add_static_html, static_html_content, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: threads_selenium_sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.threads_selenium_sessions (id, user_id, status, detail_message, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tw_posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tw_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tw_profiles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tw_profiles (id, user_id, publish_enabled, collect_enabled, schedule_type, time_intervals, use_proxy, proxy_user, proxy_pass, proxy_host, proxy_port, twitter_username, twitter_password, twitter_oauth_access_token, twitter_oauth_refresh_token, twitter_oauth_expires_at, twitter_rest_id, oauth_pkce_verifier, oauth_pkce_expires_at, take_screenshot_collect, screenshot_xpath, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: url_posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.url_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: user_role_tariff_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_role_tariff_history (id, user_id, changed_at, changed_by_user_id, role_old, role_new, tariff_old, tariff_new) FROM stdin;
1	1	2026-08-22 17:58:46.11198+03	1	admin	admin	free	full
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, email, password_hash, role, tariff, is_email_verified, is_blocked, billing_provider, billing_customer_id, billing_subscription_id, subscription_status, subscription_current_period_end, created_at, updated_at) FROM stdin;
1	Alex_admin	pulchrum@yandex.ru	$2b$12$e4.qP.l.F1yXCK/9zhL3XOOCFz.Db2LcTNjWu9bcmKUXbBZnxx6Ii	admin	full	f	f	\N	\N	\N	\N	\N	2026-08-22 10:55:54.77595+03	2026-08-22 17:58:46.108288+03
\.


--
-- Data for Name: vk_posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.vk_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, vk_source_id, attachments, publish_at, created_at, updated_at, published_vk_post_id, published_owner_id) FROM stdin;
\.


--
-- Data for Name: vk_profiles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.vk_profiles (id, user_id, publish_enabled, collect_enabled, schedule_type, time_intervals, owner_id, friends_only, from_group, message, attachments, signed, mark_as_ads, access_token, user_access_token, groups_to_read, users_to_read, group_to_post, process_enabled, processing_description, remove_emojis, remove_images, clean_html, process_services, status_review_after_process, add_static_html, static_html_content, post_to_own_wall, vk_user_id, vk_app_id, vk_app_secret, vk_frontend_url, vk_public_gateway_url, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: wp_collect_profile; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wp_collect_profile (id, user_id, collect_enabled, collect_all_available, collect_limit, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: wp_collect_sites; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wp_collect_sites (id, profile_id, user_id, site_url, schedule_type, time_intervals, created_at) FROM stdin;
\.


--
-- Data for Name: wp_posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wp_posts (id, user_id, domain, url, title, author, avatar, post_date, post_text, screenshot, images, image_over_text, comments, reposts, likes, views, is_ad, status, post_type, to_tg, to_tw, to_wp, to_vk, to_dzen, to_instagram, to_threads, target_channels, target_groups, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: wp_publish_profile; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wp_publish_profile (id, user_id, publish_enabled, schedule_type, time_intervals, site_url, username, app_password, publish_all_ready, publish_limit, publish_interval_minutes, process_before_publish, process_description, remove_emojis, remove_images, clean_html, process_services, status_review_after_process, add_static_html, static_html_content, created_at, updated_at) FROM stdin;
\.


--
-- Name: admin_audit_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.admin_audit_log_id_seq', 1, true);


--
-- Name: ai_tasks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ai_tasks_id_seq', 1, false);


--
-- Name: billing_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.billing_events_id_seq', 1, false);


--
-- Name: blacklisted_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.blacklisted_tokens_id_seq', 1, false);


--
-- Name: cpost_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.cpost_posts_id_seq', 1, false);


--
-- Name: cpost_profiles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.cpost_profiles_id_seq', 1, false);


--
-- Name: curl_one_time_done_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.curl_one_time_done_id_seq', 1, false);


--
-- Name: curl_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.curl_settings_id_seq', 1, false);


--
-- Name: dzen_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.dzen_posts_id_seq', 1, false);


--
-- Name: dzen_profiles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.dzen_profiles_id_seq', 1, false);


--
-- Name: email_verification_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.email_verification_tokens_id_seq', 1, true);


--
-- Name: feedback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.feedback_id_seq', 1, false);


--
-- Name: game_answers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_answers_id_seq', 1, false);


--
-- Name: game_bots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_bots_id_seq', 1, false);


--
-- Name: game_media_assets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_media_assets_id_seq', 1, false);


--
-- Name: game_menu_cart_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_menu_cart_items_id_seq', 1, false);


--
-- Name: game_menu_carts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_menu_carts_id_seq', 1, false);


--
-- Name: game_menu_nodes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_menu_nodes_id_seq', 1, false);


--
-- Name: game_menu_order_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_menu_order_items_id_seq', 1, false);


--
-- Name: game_menu_orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_menu_orders_id_seq', 1, false);


--
-- Name: game_modes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_modes_id_seq', 1, true);


--
-- Name: game_players_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_players_id_seq', 1, false);


--
-- Name: game_question_options_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_question_options_id_seq', 1, false);


--
-- Name: game_questions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_questions_id_seq', 1, false);


--
-- Name: game_session_questions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_session_questions_id_seq', 1, false);


--
-- Name: game_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.game_sessions_id_seq', 1, false);


--
-- Name: group_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.group_members_id_seq', 1, false);


--
-- Name: groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.groups_id_seq', 1, false);


--
-- Name: guide_blocks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.guide_blocks_id_seq', 1, false);


--
-- Name: instagram_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.instagram_posts_id_seq', 1, false);


--
-- Name: instagram_profiles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.instagram_profiles_id_seq', 1, false);


--
-- Name: notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notifications_id_seq', 1, true);


--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.password_reset_tokens_id_seq', 1, false);


--
-- Name: plan_definitions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.plan_definitions_id_seq', 1, false);


--
-- Name: posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.posts_id_seq', 1, false);


--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.refresh_tokens_id_seq', 20, true);


--
-- Name: service_cycle_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.service_cycle_log_id_seq', 2176, true);


--
-- Name: smm_automations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.smm_automations_id_seq', 1, false);


--
-- Name: smm_brand_channels_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.smm_brand_channels_id_seq', 15, true);


--
-- Name: smm_brands_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.smm_brands_id_seq', 2, true);


--
-- Name: smm_channel_counters_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.smm_channel_counters_id_seq', 1, false);


--
-- Name: smm_channel_metric_snapshots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.smm_channel_metric_snapshots_id_seq', 1, false);


--
-- Name: smm_competitor_snapshots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.smm_competitor_snapshots_id_seq', 1, false);


--
-- Name: smm_inbox_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.smm_inbox_items_id_seq', 1, false);


--
-- Name: smm_message_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.smm_message_events_id_seq', 1, false);


--
-- Name: smm_post_metric_snapshots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.smm_post_metric_snapshots_id_seq', 1, false);


--
-- Name: smm_publish_jobs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.smm_publish_jobs_id_seq', 1, false);


--
-- Name: tg_dedup_cache_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tg_dedup_cache_id_seq', 1, false);


--
-- Name: tg_digests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tg_digests_id_seq', 1, false);


--
-- Name: tg_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tg_events_id_seq', 1, false);


--
-- Name: tg_post_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tg_post_templates_id_seq', 1, false);


--
-- Name: tg_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tg_posts_id_seq', 1, false);


--
-- Name: tg_profiles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tg_profiles_id_seq', 1, true);


--
-- Name: tg_summary_cache_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tg_summary_cache_id_seq', 1, false);


--
-- Name: threads_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.threads_posts_id_seq', 1, false);


--
-- Name: threads_profiles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.threads_profiles_id_seq', 1, false);


--
-- Name: threads_selenium_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.threads_selenium_sessions_id_seq', 1, false);


--
-- Name: tw_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tw_posts_id_seq', 1, false);


--
-- Name: tw_profiles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tw_profiles_id_seq', 1, false);


--
-- Name: url_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.url_posts_id_seq', 1, false);


--
-- Name: user_role_tariff_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_role_tariff_history_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: vk_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.vk_posts_id_seq', 1, false);


--
-- Name: vk_profiles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.vk_profiles_id_seq', 1, false);


--
-- Name: wp_collect_profile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wp_collect_profile_id_seq', 1, false);


--
-- Name: wp_collect_sites_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wp_collect_sites_id_seq', 1, false);


--
-- Name: wp_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wp_posts_id_seq', 1, false);


--
-- Name: wp_publish_profile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.wp_publish_profile_id_seq', 1, false);


--
-- Name: admin_audit_log admin_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin_audit_log
    ADD CONSTRAINT admin_audit_log_pkey PRIMARY KEY (id);


--
-- Name: ai_tasks ai_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_tasks
    ADD CONSTRAINT ai_tasks_pkey PRIMARY KEY (id);


--
-- Name: billing_events billing_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.billing_events
    ADD CONSTRAINT billing_events_pkey PRIMARY KEY (id);


--
-- Name: blacklisted_tokens blacklisted_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.blacklisted_tokens
    ADD CONSTRAINT blacklisted_tokens_pkey PRIMARY KEY (id);


--
-- Name: blacklisted_tokens blacklisted_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.blacklisted_tokens
    ADD CONSTRAINT blacklisted_tokens_token_key UNIQUE (token);


--
-- Name: cpost_posts cpost_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cpost_posts
    ADD CONSTRAINT cpost_posts_pkey PRIMARY KEY (id);


--
-- Name: cpost_profiles cpost_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cpost_profiles
    ADD CONSTRAINT cpost_profiles_pkey PRIMARY KEY (id);


--
-- Name: cpost_profiles cpost_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cpost_profiles
    ADD CONSTRAINT cpost_profiles_user_id_key UNIQUE (user_id);


--
-- Name: curl_one_time_done curl_one_time_done_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.curl_one_time_done
    ADD CONSTRAINT curl_one_time_done_pkey PRIMARY KEY (id);


--
-- Name: curl_one_time_done curl_one_time_done_user_id_url_xpath_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.curl_one_time_done
    ADD CONSTRAINT curl_one_time_done_user_id_url_xpath_key UNIQUE (user_id, url, xpath);


--
-- Name: curl_settings curl_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.curl_settings
    ADD CONSTRAINT curl_settings_pkey PRIMARY KEY (id);


--
-- Name: curl_settings curl_settings_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.curl_settings
    ADD CONSTRAINT curl_settings_user_id_key UNIQUE (user_id);


--
-- Name: dzen_posts dzen_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dzen_posts
    ADD CONSTRAINT dzen_posts_pkey PRIMARY KEY (id);


--
-- Name: dzen_profiles dzen_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dzen_profiles
    ADD CONSTRAINT dzen_profiles_pkey PRIMARY KEY (id);


--
-- Name: dzen_profiles dzen_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dzen_profiles
    ADD CONSTRAINT dzen_profiles_user_id_key UNIQUE (user_id);


--
-- Name: email_verification_tokens email_verification_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_verification_tokens
    ADD CONSTRAINT email_verification_tokens_pkey PRIMARY KEY (id);


--
-- Name: email_verification_tokens email_verification_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_verification_tokens
    ADD CONSTRAINT email_verification_tokens_token_key UNIQUE (token);


--
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (id);


--
-- Name: game_answers game_answers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_answers
    ADD CONSTRAINT game_answers_pkey PRIMARY KEY (id);


--
-- Name: game_answers game_answers_session_id_question_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_answers
    ADD CONSTRAINT game_answers_session_id_question_id_key UNIQUE (session_id, question_id);


--
-- Name: game_bots game_bots_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_bots
    ADD CONSTRAINT game_bots_pkey PRIMARY KEY (id);


--
-- Name: game_bots game_bots_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_bots
    ADD CONSTRAINT game_bots_token_key UNIQUE (token);


--
-- Name: game_media_assets game_media_assets_filename_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_media_assets
    ADD CONSTRAINT game_media_assets_filename_key UNIQUE (filename);


--
-- Name: game_media_assets game_media_assets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_media_assets
    ADD CONSTRAINT game_media_assets_pkey PRIMARY KEY (id);


--
-- Name: game_media_assets game_media_assets_s3_key_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_media_assets
    ADD CONSTRAINT game_media_assets_s3_key_key UNIQUE (s3_key);


--
-- Name: game_menu_cart_items game_menu_cart_items_cart_id_node_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_cart_items
    ADD CONSTRAINT game_menu_cart_items_cart_id_node_id_key UNIQUE (cart_id, node_id);


--
-- Name: game_menu_cart_items game_menu_cart_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_cart_items
    ADD CONSTRAINT game_menu_cart_items_pkey PRIMARY KEY (id);


--
-- Name: game_menu_carts game_menu_carts_bot_id_telegram_user_id_mode_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_carts
    ADD CONSTRAINT game_menu_carts_bot_id_telegram_user_id_mode_id_key UNIQUE (bot_id, telegram_user_id, mode_id);


--
-- Name: game_menu_carts game_menu_carts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_carts
    ADD CONSTRAINT game_menu_carts_pkey PRIMARY KEY (id);


--
-- Name: game_menu_nodes game_menu_nodes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_nodes
    ADD CONSTRAINT game_menu_nodes_pkey PRIMARY KEY (id);


--
-- Name: game_menu_order_items game_menu_order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_order_items
    ADD CONSTRAINT game_menu_order_items_pkey PRIMARY KEY (id);


--
-- Name: game_menu_orders game_menu_orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_orders
    ADD CONSTRAINT game_menu_orders_order_number_key UNIQUE (order_number);


--
-- Name: game_menu_orders game_menu_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_orders
    ADD CONSTRAINT game_menu_orders_pkey PRIMARY KEY (id);


--
-- Name: game_modes game_modes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_modes
    ADD CONSTRAINT game_modes_pkey PRIMARY KEY (id);


--
-- Name: game_players game_players_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_players
    ADD CONSTRAINT game_players_pkey PRIMARY KEY (id);


--
-- Name: game_question_options game_question_options_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_question_options
    ADD CONSTRAINT game_question_options_pkey PRIMARY KEY (id);


--
-- Name: game_question_options game_question_options_question_id_option_index_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_question_options
    ADD CONSTRAINT game_question_options_question_id_option_index_key UNIQUE (question_id, option_index);


--
-- Name: game_questions game_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_questions
    ADD CONSTRAINT game_questions_pkey PRIMARY KEY (id);


--
-- Name: game_session_questions game_session_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_session_questions
    ADD CONSTRAINT game_session_questions_pkey PRIMARY KEY (id);


--
-- Name: game_session_questions game_session_questions_session_id_step_index_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_session_questions
    ADD CONSTRAINT game_session_questions_session_id_step_index_key UNIQUE (session_id, step_index);


--
-- Name: game_sessions game_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_sessions
    ADD CONSTRAINT game_sessions_pkey PRIMARY KEY (id);


--
-- Name: group_members group_members_group_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_members
    ADD CONSTRAINT group_members_group_id_user_id_key UNIQUE (group_id, user_id);


--
-- Name: group_members group_members_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_members
    ADD CONSTRAINT group_members_pkey PRIMARY KEY (id);


--
-- Name: groups groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (id);


--
-- Name: guide_blocks guide_blocks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guide_blocks
    ADD CONSTRAINT guide_blocks_pkey PRIMARY KEY (id);


--
-- Name: guide_blocks guide_blocks_slug_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guide_blocks
    ADD CONSTRAINT guide_blocks_slug_key UNIQUE (slug);


--
-- Name: instagram_posts instagram_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.instagram_posts
    ADD CONSTRAINT instagram_posts_pkey PRIMARY KEY (id);


--
-- Name: instagram_profiles instagram_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.instagram_profiles
    ADD CONSTRAINT instagram_profiles_pkey PRIMARY KEY (id);


--
-- Name: instagram_profiles instagram_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.instagram_profiles
    ADD CONSTRAINT instagram_profiles_user_id_key UNIQUE (user_id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_token_key UNIQUE (token);


--
-- Name: plan_definitions plan_definitions_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plan_definitions
    ADD CONSTRAINT plan_definitions_code_key UNIQUE (code);


--
-- Name: plan_definitions plan_definitions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.plan_definitions
    ADD CONSTRAINT plan_definitions_pkey PRIMARY KEY (id);


--
-- Name: posts posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT posts_pkey PRIMARY KEY (id);


--
-- Name: refresh_tokens refresh_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


--
-- Name: refresh_tokens refresh_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_token_key UNIQUE (token);


--
-- Name: service_cycle_log service_cycle_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service_cycle_log
    ADD CONSTRAINT service_cycle_log_pkey PRIMARY KEY (id);


--
-- Name: smm_ai_usage smm_ai_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_ai_usage
    ADD CONSTRAINT smm_ai_usage_pkey PRIMARY KEY (user_id, month);


--
-- Name: smm_automations smm_automations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_automations
    ADD CONSTRAINT smm_automations_pkey PRIMARY KEY (id);


--
-- Name: smm_brand_channels smm_brand_channels_brand_id_network_external_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_brand_channels
    ADD CONSTRAINT smm_brand_channels_brand_id_network_external_id_key UNIQUE (brand_id, network, external_id);


--
-- Name: smm_brand_channels smm_brand_channels_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_brand_channels
    ADD CONSTRAINT smm_brand_channels_pkey PRIMARY KEY (id);


--
-- Name: smm_brands smm_brands_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_brands
    ADD CONSTRAINT smm_brands_pkey PRIMARY KEY (id);


--
-- Name: smm_channel_counters smm_channel_counters_channel_id_day_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_channel_counters
    ADD CONSTRAINT smm_channel_counters_channel_id_day_key UNIQUE (channel_id, day);


--
-- Name: smm_channel_counters smm_channel_counters_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_channel_counters
    ADD CONSTRAINT smm_channel_counters_pkey PRIMARY KEY (id);


--
-- Name: smm_channel_metric_snapshots smm_channel_metric_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_channel_metric_snapshots
    ADD CONSTRAINT smm_channel_metric_snapshots_pkey PRIMARY KEY (id);


--
-- Name: smm_competitor_snapshots smm_competitor_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_competitor_snapshots
    ADD CONSTRAINT smm_competitor_snapshots_pkey PRIMARY KEY (id);


--
-- Name: smm_inbox_items smm_inbox_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_inbox_items
    ADD CONSTRAINT smm_inbox_items_pkey PRIMARY KEY (id);


--
-- Name: smm_message_events smm_message_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_message_events
    ADD CONSTRAINT smm_message_events_pkey PRIMARY KEY (id);


--
-- Name: smm_post_metric_snapshots smm_post_metric_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_post_metric_snapshots
    ADD CONSTRAINT smm_post_metric_snapshots_pkey PRIMARY KEY (id);


--
-- Name: smm_publish_jobs smm_publish_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_publish_jobs
    ADD CONSTRAINT smm_publish_jobs_pkey PRIMARY KEY (id);


--
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (key);


--
-- Name: tg_dedup_cache tg_dedup_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_dedup_cache
    ADD CONSTRAINT tg_dedup_cache_pkey PRIMARY KEY (id);


--
-- Name: tg_digests tg_digests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_digests
    ADD CONSTRAINT tg_digests_pkey PRIMARY KEY (id);


--
-- Name: tg_events tg_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_events
    ADD CONSTRAINT tg_events_pkey PRIMARY KEY (id);


--
-- Name: tg_post_templates tg_post_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_post_templates
    ADD CONSTRAINT tg_post_templates_pkey PRIMARY KEY (id);


--
-- Name: tg_posts tg_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_posts
    ADD CONSTRAINT tg_posts_pkey PRIMARY KEY (id);


--
-- Name: tg_profiles tg_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_profiles
    ADD CONSTRAINT tg_profiles_pkey PRIMARY KEY (id);


--
-- Name: tg_profiles tg_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_profiles
    ADD CONSTRAINT tg_profiles_user_id_key UNIQUE (user_id);


--
-- Name: tg_summary_cache tg_summary_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_summary_cache
    ADD CONSTRAINT tg_summary_cache_pkey PRIMARY KEY (id);


--
-- Name: tg_summary_cache tg_summary_cache_text_hash_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tg_summary_cache
    ADD CONSTRAINT tg_summary_cache_text_hash_key UNIQUE (text_hash);


--
-- Name: threads_posts threads_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.threads_posts
    ADD CONSTRAINT threads_posts_pkey PRIMARY KEY (id);


--
-- Name: threads_profiles threads_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.threads_profiles
    ADD CONSTRAINT threads_profiles_pkey PRIMARY KEY (id);


--
-- Name: threads_profiles threads_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.threads_profiles
    ADD CONSTRAINT threads_profiles_user_id_key UNIQUE (user_id);


--
-- Name: threads_selenium_sessions threads_selenium_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.threads_selenium_sessions
    ADD CONSTRAINT threads_selenium_sessions_pkey PRIMARY KEY (id);


--
-- Name: tw_posts tw_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tw_posts
    ADD CONSTRAINT tw_posts_pkey PRIMARY KEY (id);


--
-- Name: tw_profiles tw_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tw_profiles
    ADD CONSTRAINT tw_profiles_pkey PRIMARY KEY (id);


--
-- Name: tw_profiles tw_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tw_profiles
    ADD CONSTRAINT tw_profiles_user_id_key UNIQUE (user_id);


--
-- Name: url_posts url_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.url_posts
    ADD CONSTRAINT url_posts_pkey PRIMARY KEY (id);


--
-- Name: user_role_tariff_history user_role_tariff_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_role_tariff_history
    ADD CONSTRAINT user_role_tariff_history_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: vk_posts vk_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vk_posts
    ADD CONSTRAINT vk_posts_pkey PRIMARY KEY (id);


--
-- Name: vk_profiles vk_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vk_profiles
    ADD CONSTRAINT vk_profiles_pkey PRIMARY KEY (id);


--
-- Name: vk_profiles vk_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vk_profiles
    ADD CONSTRAINT vk_profiles_user_id_key UNIQUE (user_id);


--
-- Name: wp_collect_profile wp_collect_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wp_collect_profile
    ADD CONSTRAINT wp_collect_profile_pkey PRIMARY KEY (id);


--
-- Name: wp_collect_profile wp_collect_profile_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wp_collect_profile
    ADD CONSTRAINT wp_collect_profile_user_id_key UNIQUE (user_id);


--
-- Name: wp_collect_sites wp_collect_sites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wp_collect_sites
    ADD CONSTRAINT wp_collect_sites_pkey PRIMARY KEY (id);


--
-- Name: wp_posts wp_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wp_posts
    ADD CONSTRAINT wp_posts_pkey PRIMARY KEY (id);


--
-- Name: wp_publish_profile wp_publish_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wp_publish_profile
    ADD CONSTRAINT wp_publish_profile_pkey PRIMARY KEY (id);


--
-- Name: wp_publish_profile wp_publish_profile_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wp_publish_profile
    ADD CONSTRAINT wp_publish_profile_user_id_key UNIQUE (user_id);


--
-- Name: idx_admin_audit_log_admin_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_admin_audit_log_admin_user_id ON public.admin_audit_log USING btree (admin_user_id);


--
-- Name: idx_admin_audit_log_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_admin_audit_log_created_at ON public.admin_audit_log USING btree (created_at);


--
-- Name: idx_ai_tasks_status_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ai_tasks_status_created ON public.ai_tasks USING btree (status, created_at);


--
-- Name: idx_billing_events_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_billing_events_created_at ON public.billing_events USING btree (created_at);


--
-- Name: idx_billing_events_provider_event_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_billing_events_provider_event_id ON public.billing_events USING btree (provider, event_id);


--
-- Name: idx_billing_events_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_billing_events_user_id ON public.billing_events USING btree (user_id);


--
-- Name: idx_blacklisted_tokens_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_blacklisted_tokens_token ON public.blacklisted_tokens USING btree (token);


--
-- Name: idx_cpost_posts_status_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cpost_posts_status_created ON public.cpost_posts USING btree (status, created_at);


--
-- Name: idx_cpost_posts_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_cpost_posts_user_created ON public.cpost_posts USING btree (user_id, created_at);


--
-- Name: idx_curl_one_time_done_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_curl_one_time_done_user ON public.curl_one_time_done USING btree (user_id);


--
-- Name: idx_dzen_posts_status_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dzen_posts_status_created ON public.dzen_posts USING btree (status, created_at);


--
-- Name: idx_dzen_posts_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_dzen_posts_user_created ON public.dzen_posts USING btree (user_id, created_at);


--
-- Name: idx_email_verification_tokens_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_email_verification_tokens_token ON public.email_verification_tokens USING btree (token);


--
-- Name: idx_email_verification_tokens_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_email_verification_tokens_user_id ON public.email_verification_tokens USING btree (user_id);


--
-- Name: idx_feedback_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_feedback_created_at ON public.feedback USING btree (created_at DESC);


--
-- Name: idx_game_menu_nodes_mode_parent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_game_menu_nodes_mode_parent ON public.game_menu_nodes USING btree (mode_id, parent_id);


--
-- Name: idx_game_menu_orders_bot; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_game_menu_orders_bot ON public.game_menu_orders USING btree (bot_id, created_at DESC);


--
-- Name: idx_game_menu_orders_mode; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_game_menu_orders_mode ON public.game_menu_orders USING btree (mode_id, created_at DESC);


--
-- Name: idx_game_modes_bot_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_game_modes_bot_code ON public.game_modes USING btree (bot_id, code);


--
-- Name: idx_game_players_bot_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_game_players_bot_user ON public.game_players USING btree (bot_id, telegram_user_id);


--
-- Name: idx_game_questions_mode; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_game_questions_mode ON public.game_questions USING btree (mode_id) WHERE (is_active = true);


--
-- Name: idx_game_sessions_finished; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_game_sessions_finished ON public.game_sessions USING btree (status, finished_at DESC);


--
-- Name: idx_game_sessions_player_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_game_sessions_player_status ON public.game_sessions USING btree (player_id, status);


--
-- Name: idx_group_members_group_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_group_members_group_id ON public.group_members USING btree (group_id);


--
-- Name: idx_group_members_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_group_members_user_id ON public.group_members USING btree (user_id);


--
-- Name: idx_guide_blocks_sort; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_guide_blocks_sort ON public.guide_blocks USING btree (sort_order);


--
-- Name: idx_instagram_posts_source; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_instagram_posts_source ON public.instagram_posts USING btree (user_id, instagram_source_id) WHERE (instagram_source_id IS NOT NULL);


--
-- Name: idx_instagram_posts_status_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_instagram_posts_status_created ON public.instagram_posts USING btree (status, created_at);


--
-- Name: idx_instagram_posts_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_instagram_posts_user_created ON public.instagram_posts USING btree (user_id, created_at);


--
-- Name: idx_instagram_posts_user_domain; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_instagram_posts_user_domain ON public.instagram_posts USING btree (user_id, domain);


--
-- Name: idx_notifications_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_created_at ON public.notifications USING btree (created_at DESC);


--
-- Name: idx_notifications_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_user_id ON public.notifications USING btree (user_id);


--
-- Name: idx_password_reset_tokens_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_password_reset_tokens_token ON public.password_reset_tokens USING btree (token);


--
-- Name: idx_password_reset_tokens_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_password_reset_tokens_user_id ON public.password_reset_tokens USING btree (user_id);


--
-- Name: idx_posts_source; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_posts_source ON public.posts USING btree (source_platform, source_id) WHERE (source_platform IS NOT NULL);


--
-- Name: idx_posts_status_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_posts_status_created ON public.posts USING btree (status, created_at);


--
-- Name: idx_posts_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_posts_user_created ON public.posts USING btree (user_id, created_at);


--
-- Name: idx_refresh_tokens_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_refresh_tokens_token ON public.refresh_tokens USING btree (token);


--
-- Name: idx_refresh_tokens_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_refresh_tokens_user_id ON public.refresh_tokens USING btree (user_id);


--
-- Name: idx_service_cycle_log_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_service_cycle_log_created ON public.service_cycle_log USING btree (created_at DESC);


--
-- Name: idx_service_cycle_log_service_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_service_cycle_log_service_created ON public.service_cycle_log USING btree (service_name, created_at DESC);


--
-- Name: idx_smm_automations_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_automations_user ON public.smm_automations USING btree (user_id);


--
-- Name: idx_smm_brand_channels_brand_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_brand_channels_brand_id ON public.smm_brand_channels USING btree (brand_id);


--
-- Name: idx_smm_brands_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_brands_user_id ON public.smm_brands USING btree (user_id);


--
-- Name: idx_smm_channel_counters_user_day; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_channel_counters_user_day ON public.smm_channel_counters USING btree (user_id, day);


--
-- Name: idx_smm_channel_metric_channel; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_channel_metric_channel ON public.smm_channel_metric_snapshots USING btree (channel_id, captured_at);


--
-- Name: idx_smm_channels_discussion; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_channels_discussion ON public.smm_brand_channels USING btree (network, discussion_external_id) WHERE (discussion_external_id IS NOT NULL);


--
-- Name: idx_smm_channels_tg_external; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_channels_tg_external ON public.smm_brand_channels USING btree (network, external_id) WHERE ((network)::text = 'tg'::text);


--
-- Name: idx_smm_competitor_channel; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_competitor_channel ON public.smm_competitor_snapshots USING btree (channel_id);


--
-- Name: idx_smm_inbox_brand_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_inbox_brand_status ON public.smm_inbox_items USING btree (brand_id, status);


--
-- Name: idx_smm_inbox_dedup; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_smm_inbox_dedup ON public.smm_inbox_items USING btree (user_id, network, external_msg_id) WHERE (external_msg_id IS NOT NULL);


--
-- Name: idx_smm_inbox_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_inbox_user_id ON public.smm_inbox_items USING btree (user_id);


--
-- Name: idx_smm_jobs_status_publish; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_jobs_status_publish ON public.smm_publish_jobs USING btree (status, publish_at);


--
-- Name: idx_smm_jobs_user_brand; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_jobs_user_brand ON public.smm_publish_jobs USING btree (user_id, brand_id);


--
-- Name: idx_smm_message_events_channel_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_message_events_channel_created ON public.smm_message_events USING btree (channel_id, created_at);


--
-- Name: idx_smm_message_events_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_message_events_user_created ON public.smm_message_events USING btree (user_id, created_at);


--
-- Name: idx_smm_post_metric_snapshots_post; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_smm_post_metric_snapshots_post ON public.smm_post_metric_snapshots USING btree (platform, post_id, captured_at);


--
-- Name: idx_tg_dedup_expires; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tg_dedup_expires ON public.tg_dedup_cache USING btree (expires_at);


--
-- Name: idx_tg_dedup_user_hash_chat; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tg_dedup_user_hash_chat ON public.tg_dedup_cache USING btree (user_id, text_hash, chat_id);


--
-- Name: idx_tg_digests_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tg_digests_user_created ON public.tg_digests USING btree (user_id, created_at);


--
-- Name: idx_tg_events_hash_chat; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tg_events_hash_chat ON public.tg_events USING btree (text_hash, chat_id);


--
-- Name: idx_tg_events_rule_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tg_events_rule_created ON public.tg_events USING btree (rule_id, created_at);


--
-- Name: idx_tg_events_type_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tg_events_type_created ON public.tg_events USING btree (event_type, created_at);


--
-- Name: idx_tg_events_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tg_events_user_created ON public.tg_events USING btree (user_id, created_at);


--
-- Name: idx_tg_post_templates_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tg_post_templates_user ON public.tg_post_templates USING btree (user_id);


--
-- Name: idx_tg_posts_publish_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tg_posts_publish_at ON public.tg_posts USING btree (publish_at);


--
-- Name: idx_tg_posts_status_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tg_posts_status_created ON public.tg_posts USING btree (status, created_at);


--
-- Name: idx_tg_posts_status_publish_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tg_posts_status_publish_at ON public.tg_posts USING btree (status, publish_at);


--
-- Name: idx_tg_posts_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tg_posts_user_created ON public.tg_posts USING btree (user_id, created_at);


--
-- Name: idx_tg_summary_cache_expires; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tg_summary_cache_expires ON public.tg_summary_cache USING btree (expires_at);


--
-- Name: idx_threads_posts_status_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_threads_posts_status_created ON public.threads_posts USING btree (status, created_at);


--
-- Name: idx_threads_posts_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_threads_posts_user_created ON public.threads_posts USING btree (user_id, created_at);


--
-- Name: idx_threads_selenium_sessions_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_threads_selenium_sessions_created_at ON public.threads_selenium_sessions USING btree (created_at DESC);


--
-- Name: idx_threads_selenium_sessions_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_threads_selenium_sessions_user_id ON public.threads_selenium_sessions USING btree (user_id);


--
-- Name: idx_tw_posts_status_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tw_posts_status_created ON public.tw_posts USING btree (status, created_at);


--
-- Name: idx_tw_posts_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tw_posts_user_created ON public.tw_posts USING btree (user_id, created_at);


--
-- Name: idx_url_posts_status_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_url_posts_status_created ON public.url_posts USING btree (status, created_at);


--
-- Name: idx_url_posts_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_url_posts_user_created ON public.url_posts USING btree (user_id, created_at);


--
-- Name: idx_user_role_tariff_history_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_role_tariff_history_user_id ON public.user_role_tariff_history USING btree (user_id);


--
-- Name: idx_users_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_created_at ON public.users USING btree (created_at DESC);


--
-- Name: idx_vk_posts_publish_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vk_posts_publish_at ON public.vk_posts USING btree (publish_at);


--
-- Name: idx_vk_posts_status_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vk_posts_status_created ON public.vk_posts USING btree (status, created_at);


--
-- Name: idx_vk_posts_status_publish_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vk_posts_status_publish_at ON public.vk_posts USING btree (status, publish_at);


--
-- Name: idx_vk_posts_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vk_posts_user_created ON public.vk_posts USING btree (user_id, created_at);


--
-- Name: idx_vk_posts_user_domain; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vk_posts_user_domain ON public.vk_posts USING btree (user_id, domain);


--
-- Name: idx_wp_collect_sites_profile_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_wp_collect_sites_profile_id ON public.wp_collect_sites USING btree (profile_id);


--
-- Name: idx_wp_collect_sites_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_wp_collect_sites_user_id ON public.wp_collect_sites USING btree (user_id);


--
-- Name: idx_wp_posts_status_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_wp_posts_status_created ON public.wp_posts USING btree (status, created_at);


--
-- Name: idx_wp_posts_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_wp_posts_user_created ON public.wp_posts USING btree (user_id, created_at);


--
-- Name: admin_audit_log admin_audit_log_admin_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin_audit_log
    ADD CONSTRAINT admin_audit_log_admin_user_id_fkey FOREIGN KEY (admin_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: billing_events billing_events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.billing_events
    ADD CONSTRAINT billing_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: email_verification_tokens email_verification_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_verification_tokens
    ADD CONSTRAINT email_verification_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: posts fk_posts_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT fk_posts_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: game_answers game_answers_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_answers
    ADD CONSTRAINT game_answers_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.game_questions(id) ON DELETE CASCADE;


--
-- Name: game_answers game_answers_selected_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_answers
    ADD CONSTRAINT game_answers_selected_option_id_fkey FOREIGN KEY (selected_option_id) REFERENCES public.game_question_options(id) ON DELETE SET NULL;


--
-- Name: game_answers game_answers_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_answers
    ADD CONSTRAINT game_answers_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.game_sessions(id) ON DELETE CASCADE;


--
-- Name: game_menu_cart_items game_menu_cart_items_cart_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_cart_items
    ADD CONSTRAINT game_menu_cart_items_cart_id_fkey FOREIGN KEY (cart_id) REFERENCES public.game_menu_carts(id) ON DELETE CASCADE;


--
-- Name: game_menu_cart_items game_menu_cart_items_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_cart_items
    ADD CONSTRAINT game_menu_cart_items_node_id_fkey FOREIGN KEY (node_id) REFERENCES public.game_menu_nodes(id) ON DELETE CASCADE;


--
-- Name: game_menu_carts game_menu_carts_bot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_carts
    ADD CONSTRAINT game_menu_carts_bot_id_fkey FOREIGN KEY (bot_id) REFERENCES public.game_bots(id) ON DELETE CASCADE;


--
-- Name: game_menu_carts game_menu_carts_mode_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_carts
    ADD CONSTRAINT game_menu_carts_mode_id_fkey FOREIGN KEY (mode_id) REFERENCES public.game_modes(id) ON DELETE CASCADE;


--
-- Name: game_menu_nodes game_menu_nodes_mode_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_nodes
    ADD CONSTRAINT game_menu_nodes_mode_id_fkey FOREIGN KEY (mode_id) REFERENCES public.game_modes(id) ON DELETE CASCADE;


--
-- Name: game_menu_nodes game_menu_nodes_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_nodes
    ADD CONSTRAINT game_menu_nodes_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.game_menu_nodes(id) ON DELETE CASCADE;


--
-- Name: game_menu_order_items game_menu_order_items_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_order_items
    ADD CONSTRAINT game_menu_order_items_node_id_fkey FOREIGN KEY (node_id) REFERENCES public.game_menu_nodes(id) ON DELETE SET NULL;


--
-- Name: game_menu_order_items game_menu_order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_order_items
    ADD CONSTRAINT game_menu_order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.game_menu_orders(id) ON DELETE CASCADE;


--
-- Name: game_menu_orders game_menu_orders_bot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_orders
    ADD CONSTRAINT game_menu_orders_bot_id_fkey FOREIGN KEY (bot_id) REFERENCES public.game_bots(id) ON DELETE RESTRICT;


--
-- Name: game_menu_orders game_menu_orders_mode_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_menu_orders
    ADD CONSTRAINT game_menu_orders_mode_id_fkey FOREIGN KEY (mode_id) REFERENCES public.game_modes(id) ON DELETE RESTRICT;


--
-- Name: game_modes game_modes_bot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_modes
    ADD CONSTRAINT game_modes_bot_id_fkey FOREIGN KEY (bot_id) REFERENCES public.game_bots(id) ON DELETE RESTRICT;


--
-- Name: game_players game_players_bot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_players
    ADD CONSTRAINT game_players_bot_id_fkey FOREIGN KEY (bot_id) REFERENCES public.game_bots(id) ON DELETE CASCADE;


--
-- Name: game_question_options game_question_options_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_question_options
    ADD CONSTRAINT game_question_options_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.game_questions(id) ON DELETE CASCADE;


--
-- Name: game_questions game_questions_mode_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_questions
    ADD CONSTRAINT game_questions_mode_id_fkey FOREIGN KEY (mode_id) REFERENCES public.game_modes(id) ON DELETE CASCADE;


--
-- Name: game_session_questions game_session_questions_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_session_questions
    ADD CONSTRAINT game_session_questions_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.game_questions(id) ON DELETE CASCADE;


--
-- Name: game_session_questions game_session_questions_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_session_questions
    ADD CONSTRAINT game_session_questions_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.game_sessions(id) ON DELETE CASCADE;


--
-- Name: game_sessions game_sessions_mode_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_sessions
    ADD CONSTRAINT game_sessions_mode_id_fkey FOREIGN KEY (mode_id) REFERENCES public.game_modes(id) ON DELETE CASCADE;


--
-- Name: game_sessions game_sessions_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.game_sessions
    ADD CONSTRAINT game_sessions_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.game_players(id) ON DELETE CASCADE;


--
-- Name: group_members group_members_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_members
    ADD CONSTRAINT group_members_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE CASCADE;


--
-- Name: group_members group_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.group_members
    ADD CONSTRAINT group_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: groups groups_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: password_reset_tokens password_reset_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: refresh_tokens refresh_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: smm_automations smm_automations_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_automations
    ADD CONSTRAINT smm_automations_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.smm_brands(id) ON DELETE CASCADE;


--
-- Name: smm_brand_channels smm_brand_channels_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_brand_channels
    ADD CONSTRAINT smm_brand_channels_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.smm_brands(id) ON DELETE CASCADE;


--
-- Name: smm_brands smm_brands_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_brands
    ADD CONSTRAINT smm_brands_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE SET NULL;


--
-- Name: smm_channel_counters smm_channel_counters_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_channel_counters
    ADD CONSTRAINT smm_channel_counters_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.smm_brand_channels(id) ON DELETE CASCADE;


--
-- Name: smm_channel_metric_snapshots smm_channel_metric_snapshots_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_channel_metric_snapshots
    ADD CONSTRAINT smm_channel_metric_snapshots_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.smm_brand_channels(id) ON DELETE CASCADE;


--
-- Name: smm_competitor_snapshots smm_competitor_snapshots_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_competitor_snapshots
    ADD CONSTRAINT smm_competitor_snapshots_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.smm_brand_channels(id) ON DELETE CASCADE;


--
-- Name: smm_inbox_items smm_inbox_items_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_inbox_items
    ADD CONSTRAINT smm_inbox_items_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.smm_brands(id) ON DELETE SET NULL;


--
-- Name: smm_inbox_items smm_inbox_items_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_inbox_items
    ADD CONSTRAINT smm_inbox_items_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.smm_brand_channels(id) ON DELETE SET NULL;


--
-- Name: smm_message_events smm_message_events_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_message_events
    ADD CONSTRAINT smm_message_events_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES public.smm_brand_channels(id) ON DELETE SET NULL;


--
-- Name: smm_publish_jobs smm_publish_jobs_brand_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.smm_publish_jobs
    ADD CONSTRAINT smm_publish_jobs_brand_id_fkey FOREIGN KEY (brand_id) REFERENCES public.smm_brands(id) ON DELETE SET NULL;


--
-- Name: user_role_tariff_history user_role_tariff_history_changed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_role_tariff_history
    ADD CONSTRAINT user_role_tariff_history_changed_by_user_id_fkey FOREIGN KEY (changed_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: user_role_tariff_history user_role_tariff_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_role_tariff_history
    ADD CONSTRAINT user_role_tariff_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: wp_collect_sites wp_collect_sites_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wp_collect_sites
    ADD CONSTRAINT wp_collect_sites_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES public.wp_collect_profile(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

