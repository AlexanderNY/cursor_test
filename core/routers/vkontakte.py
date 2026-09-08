"""Роутер для VKontakte профилей и постов."""

import hashlib
import hmac
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, List, Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Header, File, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse, Response, RedirectResponse

from services.profile_service import profile_service
from services.post_service import post_service
from services.platform_auth_service import (
    PlatformAction,
    PlatformAuthError,
    platform_auth_service,
    platform_auth_http_detail,
)
from services.vk_helpers import groups_from_get_by_id, parse_vk_group_id as _parse_vk_group_id
from schemas import VKontakteProfileCreate, VKontaktePost
from storage_client import get_storage
from pydantic import BaseModel
from config import settings, get_vk_oauth_redirect_uri
from shared import async_fs
from upload_limits import read_upload_limited

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/vk", tags=["VKontakte"])

UPLOADS_VK_DIR = Path("uploads/vk")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
S3_KEY_PREFIX = "vk/uploads"
VK_OAUTH_STATE_TTL_SEC = 600


def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> int:
    """Извлекает user_id из заголовка запроса."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID not provided")
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


def _allowed_frontend_origins() -> set[str]:
    origins: set[str] = set()
    primary = (settings.FRONTEND_URL or "").strip().rstrip("/")
    if primary:
        origins.add(primary)
    extra = (settings.VK_OAUTH_ALLOWED_FRONTENDS or "").strip()
    for part in extra.split(","):
        o = part.strip().rstrip("/")
        if o:
            origins.add(o)
    return origins


def _sanitize_frontend_url(candidate: str) -> str:
    """Разрешает только FRONTEND_URL и VK_OAUTH_ALLOWED_FRONTENDS (anti open-redirect)."""
    cleaned = (candidate or "").strip().rstrip("/")
    allowed = _allowed_frontend_origins()
    if cleaned and cleaned in allowed:
        return cleaned
    return (settings.FRONTEND_URL or "").strip().rstrip("/")


def _sign_vk_oauth_state(user_id: int, flow: str = "user") -> str:
    """Подписанный state: user_id.exp.nonce.flow.sig (HMAC-SHA256 от JWT_SECRET_KEY)."""
    flow_norm = "group" if flow == "group" else "user"
    exp = int(time.time()) + VK_OAUTH_STATE_TTL_SEC
    nonce = uuid.uuid4().hex[:16]
    payload = f"{user_id}.{exp}.{nonce}.{flow_norm}"
    secret = (settings.JWT_SECRET_KEY or "").encode("utf-8")
    sig = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def _verify_vk_oauth_state(state: str) -> Optional[tuple[int, str]]:
    """Проверяет state. Возвращает (user_id, flow) или None."""
    if not state:
        return None
    parts = state.split(".")
    # Новый формат: user.exp.nonce.flow.sig ; старый: user.exp.nonce.sig
    if len(parts) == 5:
        user_part, exp_part, nonce, flow, sig = parts
        flow_norm = "group" if flow == "group" else "user"
        payload = f"{user_part}.{exp_part}.{nonce}.{flow_norm}"
    elif len(parts) == 4:
        user_part, exp_part, nonce, sig = parts
        flow_norm = "user"
        payload = f"{user_part}.{exp_part}.{nonce}"
    else:
        return None
    try:
        user_id = int(user_part)
        exp = int(exp_part)
    except ValueError:
        return None
    if exp < int(time.time()):
        return None
    secret = (settings.JWT_SECRET_KEY or "").encode("utf-8")
    expected = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    return user_id, flow_norm


def _group_name_from_get_by_id(resp: Any) -> Optional[str]:
    groups = groups_from_get_by_id(resp)
    if not groups:
        return None
    g = groups[0]
    return g.get("name") or g.get("screen_name")


def _extract_community_tokens(token_payload: dict[str, Any]) -> dict[int, str]:
    """Достаёт access_token_{group_id} из ответа oauth.vk.com/access_token."""
    out: dict[int, str] = {}
    for key, val in token_payload.items():
        if not isinstance(key, str) or not key.startswith("access_token_"):
            continue
        suffix = key[len("access_token_") :]
        if not suffix.isdigit():
            continue
        token = str(val or "").strip()
        if token:
            out[int(suffix)] = token
    return out

@router.get("/profile")
async def get_vk_profile(x_user_id: Optional[str] = Header(None)):
    """Получает профиль VKontakte пользователя.
    
    Returns:
        Профиль VKontakte или пустой объект
    """
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.get_vk_profile(user_id)
    if profile:
        return profile
    return {
        "publish_enabled": False,
        "collect_enabled": False,
        "schedule_type": "immediate",
        "time_intervals": [],
        "owner_id": None,
        "friends_only": False,
        "from_group": True,
        "message": None,
        "attachments": None,
        "signed": False,
        "mark_as_ads": False,
        "access_token": None,
        "user_access_token": None,
        "vk_connected": False,
        "vk_user_id": None,
        "groups_to_read": [],
        "users_to_read": [],
        "group_to_post": None,
        "post_to_own_wall": False,
        "vk_app_id": None,
        "vk_app_secret": None,
        "vk_app_service_key": None,
        "vk_frontend_url": None,
        "vk_public_gateway_url": None,
        "vk_callback_confirmation": None,
        "vk_callback_secret": None,
    }


# User OAuth: права для личной стены и photos.getWallUploadServer (без groups — частая причина invalid_scope).
VK_USER_OAUTH_SCOPES = "wall,photos,offline"
# Community OAuth (group_ids): только допустимые scopes для ключа сообщества.
VK_GROUP_OAUTH_SCOPES = "wall,photos,docs,manage"
# Обратная совместимость импортов/UI
VK_OAUTH_SCOPES = VK_USER_OAUTH_SCOPES

VK_API_VERSION = "5.199"
VK_API_BASE = "https://api.vk.com/method"


async def _resolve_vk_oauth_config(user_id: int) -> dict:
    """OAuth-параметры только из профиля (БД). Env для App ID/Secret не используется."""
    raw = await profile_service.get_vk_oauth_config_raw(user_id)
    app_id = ""
    app_secret = ""
    frontend_url = ""
    public_gateway = ""
    if raw:
        app_id = (raw.get("vk_app_id") or "").strip()
        app_secret = (raw.get("vk_app_secret") or "").strip()
        frontend_url = (raw.get("vk_frontend_url") or "").strip().rstrip("/")
        public_gateway = (raw.get("vk_public_gateway_url") or "").strip()
    if not frontend_url:
        frontend_url = (settings.FRONTEND_URL or "").strip().rstrip("/")
    frontend_url = _sanitize_frontend_url(frontend_url)
    redirect_uri = get_vk_oauth_redirect_uri(public_gateway or None)
    return {
        "app_id": app_id,
        "app_secret": app_secret,
        "frontend_url": frontend_url,
        "redirect_uri": redirect_uri,
        "public_gateway": public_gateway,
    }


def _vk_parse_api_response(data: dict) -> Any:
    """Извлекает response или бросает HTTPException по полю error."""
    if "error" in data:
        err = data["error"]
        code = err.get("error_code")
        msg = err.get("error_msg", "VK API error")
        raise HTTPException(
            status_code=502,
            detail=f"VK API: {msg}" + (f" ({code})" if code is not None else ""),
        )
    return data.get("response")


async def _vk_api_get(method: str, params: dict) -> Any:
    """GET api.vk.com/method/{method} с таймаутом."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{VK_API_BASE}/{method}",
                params=params,
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, json.JSONDecodeError) as e:
            raise HTTPException(status_code=502, detail=f"VK transport error: {e}") from e
    return _vk_parse_api_response(data)


async def _vk_api_post(method: str, params: dict) -> Any:
    """POST api.vk.com/method/{method} (form) — для wall.post и длинного текста."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{VK_API_BASE}/{method}",
                data=params,
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, json.JSONDecodeError) as e:
            raise HTTPException(status_code=502, detail=f"VK transport error: {e}") from e
    return _vk_parse_api_response(data)


def _collect_group_ids_for_community_probe(
    group_to_post: Optional[str],
    groups_to_read: Optional[List[Any]],
) -> List[str]:
    """Уникальные идентификаторы групп из настроек профиля (для groups.getById)."""
    raw: List[str] = []
    if group_to_post and str(group_to_post).strip():
        raw.append(str(group_to_post).strip())
    if isinstance(groups_to_read, list):
        for g in groups_to_read:
            if g is None:
                continue
            s = str(g).strip()
            if s:
                raw.append(s)
    seen = set()
    out: List[str] = []
    for x in raw:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out[:100]


@router.get("/subscriptions")
async def vk_list_subscriptions(x_user_id: Optional[str] = Header(None)):
    """Список подписок на сообщества (users.getSubscriptions) или проверка токена сообщества (groups.getById).

    Пользовательский OAuth: полный список подписок пользователя на сообщества.
    Только токен сообщества: возвращаются данные по группам из group_to_post / groups_to_read (доступ API к этим id).
    """
    user_id = get_user_id_from_header(x_user_id)
    raw = await profile_service.get_vk_profile_tokens_raw(user_id)
    if not raw:
        raise HTTPException(
            status_code=404,
            detail="Профиль VK не найден. Сохраните настройки на вкладке Profile Settings.",
        )
    user_tok = (raw.get("user_access_token") or "").strip()
    comm_tok = (raw.get("access_token") or "").strip()

    if user_tok:
        params: dict = {
            "access_token": user_tok,
            "v": VK_API_VERSION,
            "extended": 1,
            "count": 100,
        }
        uid = raw.get("vk_user_id")
        if uid is not None:
            params["user_id"] = int(uid)
        resp = await _vk_api_get("users.getSubscriptions", params)
        subs: List[dict] = []
        if isinstance(resp, list):
            for gid in resp[:100]:
                subs.append({"id": gid, "name": None, "screen_name": None, "type": "group"})
        elif isinstance(resp, dict):
            for g in resp.get("groups") or []:
                if not isinstance(g, dict):
                    continue
                gid = g.get("id")
                subs.append(
                    {
                        "id": gid,
                        "name": g.get("name"),
                        "screen_name": g.get("screen_name"),
                        "type": g.get("type"),
                    }
                )
            if not subs and isinstance(resp.get("items"), list):
                for gid in resp["items"][:100]:
                    subs.append({"id": gid, "name": None, "screen_name": None, "type": "group"})
        return {
            "ok": True,
            "source": "user_oauth",
            "subscriptions": subs,
            "count": len(subs),
        }

    if comm_tok:
        ids = _collect_group_ids_for_community_probe(
            raw.get("group_to_post"),
            raw.get("groups_to_read"),
        )
        if not ids:
            raise HTTPException(
                status_code=400,
                detail="Укажите Group to post или группы для сбора (Collection), чтобы проверить токен сообщества.",
            )
        params = {
            "access_token": comm_tok,
            "v": VK_API_VERSION,
            "group_ids": ",".join(ids),
            "fields": "screen_name",
        }
        resp = await _vk_api_get("groups.getById", params)
        subs = []
        for g in groups_from_get_by_id(resp):
            subs.append(
                {
                    "id": g.get("id"),
                    "name": g.get("name"),
                    "screen_name": g.get("screen_name"),
                    "type": g.get("type"),
                }
            )
        return {
            "ok": True,
            "source": "community_token",
            "subscriptions": subs,
            "count": len(subs),
            "message": "Данные по указанным группам через токен сообщества. Полный список подписок пользователя — через OAuth VK.",
        }

    raise HTTPException(
        status_code=400,
        detail="Нет сохранённого токена: укажите Access token (VK) на вкладке Авторизация или подключите VK (OAuth).",
    )


@router.get("/oauth/url")
async def get_vk_oauth_url(
    flow: str = "user",
    x_user_id: Optional[str] = Header(None),
):
    """URL авторизации VK OAuth.

    flow=user — пользовательский токен (user_access_token) для загрузки фото на стену.
    flow=group — токен сообщества (access_token) для wall.post от имени группы; нужен group_to_post.
    """
    user_id = get_user_id_from_header(x_user_id)
    flow_norm = "group" if (flow or "").strip().lower() == "group" else "user"
    oauth_cfg = await _resolve_vk_oauth_config(user_id)
    app_id = oauth_cfg["app_id"]
    redirect_uri = oauth_cfg["redirect_uri"]
    if not app_id:
        raise HTTPException(
            status_code=503,
            detail=(
                "VK OAuth не настроен: сохраните VK App ID и Secret в блоке «Приложение» на вкладке Авторизация. "
                f"Redirect URI для кабинета VK: {redirect_uri}"
            ),
        )
    params: dict[str, str] = {
        "client_id": app_id,
        "display": "page",
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "v": VK_API_VERSION,
        "state": _sign_vk_oauth_state(user_id, flow_norm),
    }
    if flow_norm == "group":
        raw = await profile_service.get_vk_profile_tokens_raw(user_id)
        group_id = _parse_vk_group_id((raw or {}).get("group_to_post") if raw else None)
        if group_id is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Для OAuth сообщества сначала сохраните Group to post "
                    "(числовой id или club…), затем нажмите «Подключить сообщество»."
                ),
            )
        params["group_ids"] = str(group_id)
        params["scope"] = VK_GROUP_OAUTH_SCOPES
    else:
        params["scope"] = VK_USER_OAUTH_SCOPES
    url = f"https://oauth.vk.com/authorize?{urlencode(params)}"
    return {"url": url, "flow": flow_norm, "scope": params["scope"]}


@router.post("/callback")
async def vk_callback_api(payload: dict[str, Any]):
    """VK Callback API сообщества (без JWT). Confirmation/secret — из vk_profiles по group_id."""
    event_type = str(payload.get("type") or "").strip()
    raw_gid = payload.get("group_id")
    try:
        group_id = int(raw_gid) if raw_gid is not None else 0
    except (TypeError, ValueError):
        group_id = 0

    cfg = await profile_service.get_vk_callback_config_by_group_id(group_id) if group_id else None
    if not cfg:
        raise HTTPException(
            status_code=503,
            detail=(
                "Callback API: профиль для group_id не найден. "
                "Сохраните Group to post и строку подтверждения / секрет на вкладке Авторизация."
            ),
        )

    # confirmation от VK приходит без secret — секрет проверяем только на событиях
    if event_type != "confirmation":
        configured_secret = (cfg.get("vk_callback_secret") or "").strip()
        if configured_secret:
            incoming_secret = str(payload.get("secret") or "").strip()
            if not hmac.compare_digest(incoming_secret, configured_secret):
                raise HTTPException(status_code=403, detail="invalid secret")

    if event_type == "confirmation":
        confirmation = (cfg.get("vk_callback_confirmation") or "").strip()
        if not confirmation:
            raise HTTPException(
                status_code=503,
                detail="vk_callback_confirmation is not configured in profile",
            )
        return PlainTextResponse(content=confirmation)

    return PlainTextResponse(content="ok")


class VkAuthVerifyResponse(BaseModel):
    ok: bool
    block: str
    message: str
    details: Optional[dict[str, Any]] = None


@router.post("/auth/verify/community", response_model=VkAuthVerifyResponse)
async def verify_vk_community(x_user_id: Optional[str] = Header(None)):
    """Проверка токена сообщества: groups.getById + getTokenPermissions / messages.getConversations."""
    user_id = get_user_id_from_header(x_user_id)
    raw = await profile_service.get_vk_profile_tokens_raw(user_id)
    if not raw:
        return VkAuthVerifyResponse(ok=False, block="community", message="Профиль VK не найден")
    token = (raw.get("access_token") or "").strip()
    group_id = _parse_vk_group_id(raw.get("group_to_post"))
    if not token:
        return VkAuthVerifyResponse(ok=False, block="community", message="Нет access_token сообщества")
    if group_id is None:
        return VkAuthVerifyResponse(
            ok=False,
            block="community",
            message="Укажите ID группы (числовой id или club…)",
        )
    try:
        groups = await _vk_api_get(
            "groups.getById",
            {
                "access_token": token,
                "v": VK_API_VERSION,
                "group_ids": str(group_id),
                "fields": "screen_name",
            },
        )
    except HTTPException as e:
        return VkAuthVerifyResponse(
            ok=False,
            block="community",
            message=str(e.detail),
        )
    group_name = _group_name_from_get_by_id(groups)
    permissions: list[str] = []
    try:
        perms = await _vk_api_get(
            "groups.getTokenPermissions",
            {"access_token": token, "v": VK_API_VERSION},
        )
        if isinstance(perms, dict):
            for p in perms.get("permissions") or []:
                if isinstance(p, dict) and p.get("name"):
                    permissions.append(str(p["name"]))
                elif isinstance(p, str):
                    permissions.append(p)
    except HTTPException:
        # Fallback: community messages API
        try:
            await _vk_api_get(
                "messages.getConversations",
                {
                    "access_token": token,
                    "v": VK_API_VERSION,
                    "count": 1,
                },
            )
            permissions.append("messages")
        except HTTPException as e:
            return VkAuthVerifyResponse(
                ok=False,
                block="community",
                message=f"groups.getById ok, но права не проверены: {e.detail}",
                details={"group_id": group_id, "group_name": group_name},
            )
    return VkAuthVerifyResponse(
        ok=True,
        block="community",
        message=f"Токен сообщества работает для «{group_name or group_id}»",
        details={"group_id": group_id, "group_name": group_name, "permissions": permissions},
    )


@router.post("/auth/verify/callback", response_model=VkAuthVerifyResponse)
async def verify_vk_callback(x_user_id: Optional[str] = Header(None)):
    """Проверка Callback: confirmation + secret в БД и lookup по group_id."""
    user_id = get_user_id_from_header(x_user_id)
    raw = await profile_service.get_vk_oauth_config_raw(user_id)
    tokens = await profile_service.get_vk_profile_tokens_raw(user_id)
    group_id = _parse_vk_group_id((tokens or {}).get("group_to_post") if tokens else None)
    confirmation = ((raw or {}).get("vk_callback_confirmation") or "").strip()
    secret = ((raw or {}).get("vk_callback_secret") or "").strip()
    gateway = ((raw or {}).get("vk_public_gateway_url") or "").strip().rstrip("/")
    callback_url = f"{gateway}/vk/callback" if gateway else ""
    if group_id is None:
        return VkAuthVerifyResponse(
            ok=False,
            block="callback",
            message="Сначала сохраните Group to post (блок «Сообщество»)",
        )
    if not confirmation:
        return VkAuthVerifyResponse(
            ok=False,
            block="callback",
            message="Укажите строку подтверждения (из настроек Callback API группы)",
        )
    looked = await profile_service.get_vk_callback_config_by_group_id(group_id)
    if not looked or int(looked.get("user_id") or 0) != user_id:
        return VkAuthVerifyResponse(
            ok=False,
            block="callback",
            message="Lookup по group_id не нашёл ваш профиль — проверьте Group to post",
        )
    # Dry-run: тот же ответ, что отдаст POST /vk/callback на confirmation
    if looked.get("vk_callback_confirmation") != confirmation:
        return VkAuthVerifyResponse(
            ok=False,
            block="callback",
            message="Строка подтверждения в БД не совпадает с профилем",
        )
    return VkAuthVerifyResponse(
        ok=True,
        block="callback",
        message="Callback настроен: confirmation сохранён, lookup по group_id работает",
        details={
            "group_id": group_id,
            "callback_url": callback_url,
            "has_secret": bool(secret),
            "confirmation_preview": confirmation[:4] + "…" if len(confirmation) > 4 else confirmation,
        },
    )


@router.post("/auth/verify/app", response_model=VkAuthVerifyResponse)
async def verify_vk_app(x_user_id: Optional[str] = Header(None)):
    """Проверка ключей приложения из БД (App ID + protected; service — опционально)."""
    user_id = get_user_id_from_header(x_user_id)
    raw = await profile_service.get_vk_oauth_config_raw(user_id)
    if not raw:
        return VkAuthVerifyResponse(ok=False, block="app", message="Профиль VK не найден")
    app_id = (raw.get("vk_app_id") or "").strip()
    app_secret = (raw.get("vk_app_secret") or "").strip()
    service_key = (raw.get("vk_app_service_key") or "").strip()
    if not app_id:
        return VkAuthVerifyResponse(ok=False, block="app", message="Нет VK App ID")
    if not app_id.isdigit():
        return VkAuthVerifyResponse(ok=False, block="app", message="App ID должен быть числом")
    if not app_secret:
        return VkAuthVerifyResponse(ok=False, block="app", message="Нет защищённого ключа (App Secret)")
    details: dict[str, Any] = {
        "app_id": app_id,
        "has_secret": True,
        "has_service_key": bool(service_key),
    }
    if service_key:
        try:
            await _vk_api_get(
                "apps.get",
                {
                    "access_token": service_key,
                    "v": VK_API_VERSION,
                    "app_id": app_id,
                },
            )
            details["service_probe"] = "apps.get ok"
        except HTTPException as e:
            details["service_probe"] = str(e.detail)
            return VkAuthVerifyResponse(
                ok=True,
                block="app",
                message=(
                    "App ID и защищённый ключ сохранены. "
                    f"Сервисный ключ не прошёл apps.get ({e.detail}) — для OAuth он не обязателен."
                ),
                details=details,
            )
    return VkAuthVerifyResponse(
        ok=True,
        block="app",
        message="Ключи приложения сохранены" + (" и service key отвечает" if service_key else ""),
        details=details,
    )


@router.post("/auth/verify/oauth", response_model=VkAuthVerifyResponse)
async def verify_vk_oauth(x_user_id: Optional[str] = Header(None)):
    """Проверка пользовательского OAuth (users.get) и наличия community token."""
    user_id = get_user_id_from_header(x_user_id)
    raw = await profile_service.get_vk_profile_tokens_raw(user_id)
    oauth_cfg = await _resolve_vk_oauth_config(user_id)
    if not raw:
        return VkAuthVerifyResponse(ok=False, block="oauth", message="Профиль VK не найден")
    user_tok = (raw.get("user_access_token") or "").strip()
    comm_tok = (raw.get("access_token") or "").strip()
    details: dict[str, Any] = {
        "has_user_token": bool(user_tok),
        "has_community_token": bool(comm_tok),
        "app_id_configured": bool(oauth_cfg.get("app_id")),
        "app_secret_configured": bool(oauth_cfg.get("app_secret")),
        "redirect_uri": oauth_cfg.get("redirect_uri"),
    }
    if not user_tok and not comm_tok:
        return VkAuthVerifyResponse(
            ok=False,
            block="oauth",
            message="Нет user_access_token и access_token — подключите OAuth или токен сообщества",
            details=details,
        )
    if user_tok:
        try:
            resp = await _vk_api_get(
                "users.get",
                {"access_token": user_tok, "v": VK_API_VERSION},
            )
            vk_uid = None
            if isinstance(resp, list) and resp and isinstance(resp[0], dict):
                vk_uid = resp[0].get("id")
            details["vk_user_id"] = vk_uid
            if vk_uid is not None:
                try:
                    await profile_service.save_vk_oauth_tokens(
                        user_id, user_tok, int(vk_uid)
                    )
                except Exception:
                    logger.warning("Failed to persist vk_user_id after verify", exc_info=True)
            return VkAuthVerifyResponse(
                ok=True,
                block="oauth",
                message=f"Пользовательский токен работает (vk_user_id={vk_uid})",
                details=details,
            )
        except HTTPException as e:
            return VkAuthVerifyResponse(
                ok=False,
                block="oauth",
                message=f"user token: {e.detail}",
                details=details,
            )
    return VkAuthVerifyResponse(
        ok=True,
        block="oauth",
        message="Есть только токен сообщества — для фото нужен пользовательский OAuth",
        details=details,
    )


@router.post("/auth/test/community-wall", response_model=VkAuthVerifyResponse)
async def test_vk_community_wall(x_user_id: Optional[str] = Header(None)):
    """Тестовый wall.post от имени сообщества; в details — post_url."""
    user_id = get_user_id_from_header(x_user_id)
    raw = await profile_service.get_vk_profile_tokens_raw(user_id)
    if not raw:
        return VkAuthVerifyResponse(ok=False, block="community", message="Профиль VK не найден")
    token = (raw.get("access_token") or "").strip()
    group_id = _parse_vk_group_id(raw.get("group_to_post"))
    if not token:
        return VkAuthVerifyResponse(ok=False, block="community", message="Нет access_token сообщества")
    if group_id is None:
        return VkAuthVerifyResponse(
            ok=False,
            block="community",
            message="Укажите и сохраните Group to post",
        )
    stamp = int(time.time())
    message = f"CopyParse test post {stamp}"
    owner_id = -group_id
    try:
        result = await _vk_api_post(
            "wall.post",
            {
                "access_token": token,
                "v": VK_API_VERSION,
                "owner_id": str(owner_id),
                "from_group": "1",
                "message": message,
            },
        )
    except HTTPException as e:
        return VkAuthVerifyResponse(ok=False, block="community", message=str(e.detail))
    post_id = result.get("post_id") if isinstance(result, dict) else None
    if post_id is None:
        return VkAuthVerifyResponse(
            ok=False,
            block="community",
            message="wall.post не вернул post_id",
            details={"raw": result if isinstance(result, dict) else None},
        )
    post_url = f"https://vk.com/wall-{group_id}_{post_id}"
    return VkAuthVerifyResponse(
        ok=True,
        block="community",
        message=f"Тестовый пост опубликован: {post_url}",
        details={
            "group_id": group_id,
            "post_id": post_id,
            "owner_id": owner_id,
            "post_url": post_url,
            "message": message,
        },
    )


@router.get("/auth/admin-groups")
async def list_vk_admin_groups(x_user_id: Optional[str] = Header(None)):
    """Сообщества, где пользователь админ (groups.get filter=admin) — нужен user_access_token."""
    user_id = get_user_id_from_header(x_user_id)
    raw = await profile_service.get_vk_profile_tokens_raw(user_id)
    if not raw:
        raise HTTPException(status_code=404, detail="Профиль VK не найден")
    user_tok = (raw.get("user_access_token") or "").strip()
    if not user_tok:
        raise HTTPException(
            status_code=400,
            detail="Нужен пользовательский OAuth (кнопка «Подключить пользователя»)",
        )
    resp = await _vk_api_get(
        "groups.get",
        {
            "access_token": user_tok,
            "v": VK_API_VERSION,
            "filter": "admin",
            "extended": 1,
            "count": 100,
            "fields": "screen_name",
        },
    )
    items: List[dict] = []
    if isinstance(resp, dict):
        for g in resp.get("items") or []:
            if not isinstance(g, dict):
                continue
            items.append(
                {
                    "id": g.get("id"),
                    "name": g.get("name"),
                    "screen_name": g.get("screen_name"),
                    "type": g.get("type"),
                }
            )
    elif isinstance(resp, list):
        for gid in resp[:100]:
            items.append({"id": gid, "name": None, "screen_name": None, "type": "group"})
    return {
        "ok": True,
        "source": "user_oauth_admin",
        "subscriptions": items,
        "count": len(items),
        "message": "Сообщества, где вы администратор. Кликните, чтобы выбрать Group to post.",
    }


@router.post("/auth/test/own-wall", response_model=VkAuthVerifyResponse)
async def test_vk_own_wall(x_user_id: Optional[str] = Header(None)):
    """Тестовый wall.post на личную стену (user_access_token)."""
    user_id = get_user_id_from_header(x_user_id)
    raw = await profile_service.get_vk_profile_tokens_raw(user_id)
    if not raw:
        return VkAuthVerifyResponse(ok=False, block="oauth", message="Профиль VK не найден")
    user_tok = (raw.get("user_access_token") or "").strip()
    if not user_tok:
        return VkAuthVerifyResponse(
            ok=False,
            block="oauth",
            message="Нет user_access_token — подключите пользователя (OAuth)",
        )
    try:
        me = await _vk_api_get(
            "users.get",
            {"access_token": user_tok, "v": VK_API_VERSION},
        )
    except HTTPException as e:
        return VkAuthVerifyResponse(ok=False, block="oauth", message=str(e.detail))
    vk_uid = None
    if isinstance(me, list) and me and isinstance(me[0], dict):
        vk_uid = me[0].get("id")
    if vk_uid is None and raw.get("vk_user_id") is not None:
        vk_uid = int(raw["vk_user_id"])
    if vk_uid is None:
        return VkAuthVerifyResponse(ok=False, block="oauth", message="Не удалось получить vk_user_id")
    stamp = int(time.time())
    message = f"CopyParse test wall {stamp}"
    try:
        result = await _vk_api_post(
            "wall.post",
            {
                "access_token": user_tok,
                "v": VK_API_VERSION,
                "owner_id": str(vk_uid),
                "from_group": "0",
                "message": message,
            },
        )
    except HTTPException as e:
        return VkAuthVerifyResponse(ok=False, block="oauth", message=str(e.detail))
    post_id = result.get("post_id") if isinstance(result, dict) else None
    if post_id is None:
        return VkAuthVerifyResponse(
            ok=False,
            block="oauth",
            message="wall.post не вернул post_id",
            details={"raw": result if isinstance(result, dict) else None},
        )
    post_url = f"https://vk.com/wall{vk_uid}_{post_id}"
    return VkAuthVerifyResponse(
        ok=True,
        block="oauth",
        message=f"Тест на личную стену: {post_url}",
        details={
            "vk_user_id": vk_uid,
            "post_id": post_id,
            "post_url": post_url,
            "message": message,
        },
    )


@router.get("/oauth/callback")
async def vk_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """Callback VK OAuth: обмен code на токен(ы); user → user_access_token, group → access_token."""
    verified = _verify_vk_oauth_state(state or "") if state else None
    if verified is None:
        safe_frontend = _sanitize_frontend_url(settings.FRONTEND_URL or "")
        vk_page = f"{safe_frontend}/vkontakte"
        return RedirectResponse(url=f"{vk_page}?oauth=error&message=invalid_state")
    user_id, flow = verified
    oauth_cfg = await _resolve_vk_oauth_config(user_id)
    frontend_url = oauth_cfg["frontend_url"] or _sanitize_frontend_url(settings.FRONTEND_URL or "")
    vk_page = f"{frontend_url}/vkontakte"
    if error:
        msg = error_description or error
        return RedirectResponse(url=f"{vk_page}?oauth=error&message={msg}")
    if not code or not state:
        return RedirectResponse(url=f"{vk_page}?oauth=error&message=missing_code_or_state")
    app_id = oauth_cfg["app_id"]
    app_secret = oauth_cfg["app_secret"]
    redirect_uri = oauth_cfg["redirect_uri"]
    if not app_id or not app_secret or not redirect_uri:
        return RedirectResponse(url=f"{vk_page}?oauth=error&message=server_config")
    params = {
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    token_url = f"https://oauth.vk.com/access_token?{urlencode(params)}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(token_url, timeout=20.0)
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError):
            return RedirectResponse(url=f"{vk_page}?oauth=error&message=exchange_failed")
    if data.get("error"):
        err = data.get("error_description") or data.get("error") or "oauth_error"
        return RedirectResponse(url=f"{vk_page}?oauth=error&message={err}")

    if flow == "group":
        community_tokens = _extract_community_tokens(data)
        community_token = next(iter(community_tokens.values()), None) if community_tokens else None
        if not community_token:
            # Некоторые ответы кладут групповой ключ в access_token без суффикса
            community_token = (data.get("access_token") or "").strip() or None
        if not community_token:
            return RedirectResponse(url=f"{vk_page}?oauth=error&message=no_community_token")
        group_id = next(iter(community_tokens.keys()), None) if community_tokens else None
        if group_id is None:
            raw = await profile_service.get_vk_profile_tokens_raw(user_id)
            group_id = _parse_vk_group_id((raw or {}).get("group_to_post") if raw else None)
        await profile_service.save_vk_community_token(
            user_id=user_id,
            access_token=community_token,
            group_to_post=str(group_id) if group_id is not None else None,
        )
    else:
        access_token = (data.get("access_token") or "").strip()
        if not access_token:
            return RedirectResponse(url=f"{vk_page}?oauth=error&message=no_token")
        vk_uid = data.get("user_id")
        vk_user_id = int(vk_uid) if vk_uid is not None else None
        await profile_service.save_vk_oauth_tokens(
            user_id=user_id,
            user_access_token=access_token,
            vk_user_id=vk_user_id,
        )
    try:
        await platform_auth_service.recheck_user_platform_channels(user_id)
    except Exception:
        pass
    return RedirectResponse(url=f"{vk_page}?oauth=success&flow={flow}")


@router.get("/oauth/status")
async def vk_oauth_status(x_user_id: Optional[str] = Header(None)):
    """Статус OAuth: пользовательский токен и/или токен сообщества."""
    user_id = get_user_id_from_header(x_user_id)
    profile = await profile_service.get_vk_profile(user_id)
    raw = await profile_service.get_vk_profile_tokens_raw(user_id)
    has_user = bool(raw and (raw.get("user_access_token") or "").strip())
    has_community = bool(raw and (raw.get("access_token") or "").strip())
    if not profile and not has_user and not has_community:
        return {
            "connected": False,
            "community_connected": False,
            "message": "Профиль VK не найден. Сохраните настройки профиля или пройдите OAuth.",
            "vk_user_id": None,
        }
    if has_user and has_community:
        message = "Подключены пользовательский OAuth и токен сообщества — публикация на стену группы с фото доступна."
    elif has_community:
        message = "Токен сообщества сохранён — текстовые посты на стену группы доступны. Для фото подключите пользовательский OAuth."
    elif has_user:
        message = "Пользовательский OAuth сохранён. Для постов от имени группы подключите сообщество или вставьте токен сообщества."
    else:
        message = "Токены не сохранены — подключите сообщество (wall.post) и при необходимости пользовательский OAuth (фото)."
    return {
        "connected": has_user,
        "community_connected": has_community,
        "message": message,
        "vk_user_id": profile.get("vk_user_id") if profile else None,
    }


@router.post("/profile")
async def save_vk_profile(
    data: VKontakteProfileCreate,
    x_user_id: Optional[str] = Header(None)
):
    """Сохраняет профиль VKontakte пользователя.
    
    Args:
        data: Данные профиля
    
    Returns:
        Сохраненный профиль
    """
    user_id = get_user_id_from_header(x_user_id)
    payload = data.model_dump()
    if payload.get("collect_enabled"):
        try:
            await platform_auth_service.require_platform(
                user_id, "vk", PlatformAction.COLLECT
            )
        except PlatformAuthError as exc:
            raise HTTPException(
                status_code=400,
                detail=platform_auth_http_detail(exc),
            ) from exc
    profile = await profile_service.save_vk_profile(user_id, payload)
    return profile


@router.get("/profiles")
async def get_all_vk_profiles():
    """Получает все профили VKontakte.
    
    Returns:
        Список всех профилей VKontakte
    """
    profiles = await profile_service.get_all_vk_profiles()
    return {"profiles": profiles}


@router.post("/upload")
async def upload_vk_image(
    image: UploadFile = File(...),
    x_user_id: Optional[str] = Header(None),
):
    """Загружает изображение в единое хранилище (S3) или локально. Возвращает путь для вложения в пост."""
    get_user_id_from_header(x_user_id)
    if not image.filename:
        raise HTTPException(status_code=400, detail="No file name")
    ext = Path(image.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Allowed formats: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}",
        )
    name = f"{uuid.uuid4().hex}{ext}"
    content = await read_upload_limited(
        image, max_bytes=settings.MAX_UPLOAD_IMAGE_BYTES, label="Image"
    )
    storage = get_storage()
    if storage:
        key = f"{S3_KEY_PREFIX}/{name}"
        await storage.put(key, content)
        return {"url": f"/vk/uploads/{name}"}
    await async_fs.makedirs(UPLOADS_VK_DIR)
    path = UPLOADS_VK_DIR / name
    await async_fs.write_bytes(path, content)
    return {"url": f"/vk/uploads/{name}"}


def _media_type_for_filename(filename: str) -> str:
    """Возвращает media type по расширению файла."""
    ext = (Path(filename).suffix or "").lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "application/octet-stream")


@router.get("/uploads/{filename}")
async def get_vk_upload(filename: str):
    """Отдаёт загруженный файл: из S3 потоком через Core (для доступа из браузера) или FileResponse с локального диска."""
    if "/" in filename or filename.startswith("."):
        raise HTTPException(status_code=400, detail="Invalid filename")
    storage = get_storage()
    if storage:
        key = f"{S3_KEY_PREFIX}/{filename}"
        content = await storage.get_bytes(key)
        if content is None:
            raise HTTPException(status_code=404, detail="File not found")
        return Response(
            content=content,
            media_type=_media_type_for_filename(filename),
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    file_path = UPLOADS_VK_DIR / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename, media_type=_media_type_for_filename(filename))


@router.get("/posts")
async def get_vk_posts(
    x_user_id: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """Возвращает список постов VKontakte пользователя из таблицы vk_posts."""
    user_id = get_user_id_from_header(x_user_id)
    posts = await post_service.get_vk_posts(
        user_id=user_id,
        limit=limit,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
    )
    return posts


@router.post("/post")
async def create_vk_post(
    data: VKontaktePost,
    x_user_id: Optional[str] = Header(None)
):
    """Создает пост для VKontakte (max 15985 символов).
    
    Args:
        data: Данные поста
        
    Returns:
        Созданный пост
    """
    user_id = get_user_id_from_header(x_user_id)

    if data.to_vk:
        action = (
            PlatformAction.PUBLISH_MEDIA
            if data.images
            else PlatformAction.PUBLISH_TEXT
        )
        try:
            await platform_auth_service.require_platform(user_id, "vk", action)
        except PlatformAuthError as exc:
            raise HTTPException(status_code=403, detail=platform_auth_http_detail(exc))

    try:
        post = await post_service.create_vk_post_record(
            user_id=user_id,
            text=data.text,
            images=data.images or [],
            to_tg=data.to_tg,
            to_tw=data.to_tw,
            to_wp=data.to_wp,
            to_vk=data.to_vk,
            to_threads=data.to_threads,
            to_dzen=data.to_dzen,
            to_instagram=data.to_instagram,
            publish_at=data.publish_at,
            target_groups=data.target_groups,
            target_channels=data.target_channels,
        )
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class VKontaktePostUpdate(BaseModel):
    """Тело запроса для обновления поста VK."""
    text: Optional[str] = None
    images: Optional[list] = None
    attachments: Optional[list] = None
    status: Optional[str] = None
    publish_at: Optional[str] = None
    clear_publish_at: bool = False


@router.get("/post/{post_id}")
async def get_vk_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    """Возвращает один пост VKontakte по id."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.get_vk_post(user_id=user_id, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/post/{post_id}")
async def update_vk_post(
    post_id: int,
    data: VKontaktePostUpdate,
    x_user_id: Optional[str] = Header(None),
):
    """Обновляет пост VKontakte (текст, статус и/или publish_at)."""
    user_id = get_user_id_from_header(x_user_id)
    try:
        post = await post_service.update_vk_post(
            user_id=user_id,
            post_id=post_id,
            text=data.text,
            images=data.images,
            attachments=data.attachments,
            status=data.status,
            publish_at=None if data.clear_publish_at else data.publish_at,
            clear_publish_at=data.clear_publish_at,
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/post/{post_id}")
async def delete_vk_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    """Помечает пост VKontakte как удаленный (status = deleted)."""
    user_id = get_user_id_from_header(x_user_id)
    post = await post_service.delete_vk_post(user_id=user_id, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
