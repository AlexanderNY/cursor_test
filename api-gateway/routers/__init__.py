from .auth_routes import router as auth_router
from .core_routes import router as core_router
from .wp_routes import router as wp_router
from .tg_routes import router as tg_router
from .tw_routes import router as tw_router
from .vk_routes import router as vk_router
from .dzen_routes import router as dzen_router
from .instagram_routes import router as instagram_router
from .curl_routes import router as curl_router
from .cpost_routes import router as cpost_router
from .bot_proxy import router as bot_proxy_router
from .threads_routes import router as threads_router
from .stubs import router as stubs_router

__all__ = [
    "auth_router",
    "core_router",
    "wp_router",
    "tg_router",
    "tw_router",
    "vk_router",
    "dzen_router",
    "instagram_router",
    "curl_router",
    "cpost_router",
    "bot_proxy_router",
    "threads_router",
    "stubs_router",
]


