from pathlib import Path

p = Path(__file__).resolve().parents[1] / "routers" / "site.py"
text = p.read_text(encoding="utf-8")

text = text.replace(
    "from database import get_db_connection, release_db_connection\n"
    "from services.system_settings_service import system_settings_service",
    "from site_database import get_site_db_connection, release_site_db_connection",
)
text = text.replace("get_db_connection()", "get_site_db_connection()")
text = text.replace("release_db_connection(", "release_site_db_connection(")

if "import json" not in text:
    text = text.replace(
        "from __future__ import annotations\n\n",
        "from __future__ import annotations\n\nimport json\n",
    )

old_get = '''@router.get("/promo")
async def get_promo() -> dict[str, Any]:
    raw = await system_settings_service.get_value(SITE_PROMO_KEY, DEFAULT_PROMO)
    data = DEFAULT_PROMO.copy()
    if isinstance(raw, dict):
        data.update({k: raw[k] for k in DEFAULT_PROMO if k in raw})
    data["enabled"] = bool(data.get("enabled", True))
    return data'''

new_get = '''async def _get_setting(key: str, default: Any = None) -> Any:
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("SELECT value FROM site_settings WHERE key = %s", (key,))
            row = await cur.fetchone()
            if not row:
                return default
            value = row[0]
            if isinstance(value, (dict, list, bool, int, float)) or value is None:
                return value
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return value
    finally:
        await release_site_db_connection(conn)


async def _set_setting(key: str, value: Any) -> Any:
    conn = await get_site_db_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO site_settings (key, value, updated_at)
                VALUES (%s, %s::jsonb, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE
                SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
                RETURNING value
                """,
                (key, json.dumps(value, ensure_ascii=False)),
            )
            row = await cur.fetchone()
            return row[0] if row else value
    finally:
        await release_site_db_connection(conn)


@router.get("/promo")
async def get_promo() -> dict[str, Any]:
    raw = await _get_setting(SITE_PROMO_KEY, DEFAULT_PROMO)
    data = DEFAULT_PROMO.copy()
    if isinstance(raw, dict):
        data.update({k: raw[k] for k in DEFAULT_PROMO if k in raw})
    data["enabled"] = bool(data.get("enabled", True))
    return data'''

if old_get not in text:
    raise SystemExit("get_promo block not found")
text = text.replace(old_get, new_get)
text = text.replace(
    "await system_settings_service.set_value(SITE_PROMO_KEY, payload)",
    "await _set_setting(SITE_PROMO_KEY, payload)",
)

old_contact = '''            await cur.execute(
                """
                INSERT INTO feedback (type, text, email, user_id)
                VALUES (%s, %s, %s, NULL)
                RETURNING id, created_at
                """,
                ("contact_author", text, str(body.email)),
            )'''

new_contact = '''            await cur.execute(
                """
                INSERT INTO site_contacts (app_slug, name, email, message)
                VALUES (%s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (app_slug, name, str(body.email), message),
            )'''

if old_contact not in text:
    raise SystemExit("contact insert not found")
text = text.replace(old_contact, new_contact)

# simplify submit_contact: drop unused text_parts if still present
# leave as-is — message variable is the user message

p.write_text(text, encoding="utf-8")
print("ok", p)
