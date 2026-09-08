from typing import Dict

from fastapi import APIRouter, Depends
from schemas import ActivityHeartbeatRequest, AdminProductMetrics
from dependencies import get_admin_user, get_current_user
from services.activity_service import get_product_metrics, record_session_heartbeat

router = APIRouter(tags=["activity"])


@router.post("/activity/heartbeat")
async def activity_heartbeat(
    body: ActivityHeartbeatRequest,
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, bool]:
    """Heartbeat активного сеанса в UI (видимая вкладка)."""
    await record_session_heartbeat(int(current_user["id"]), body.client_session_id)
    return {"ok": True}


@router.get("/admin/product-metrics", response_model=AdminProductMetrics)
async def admin_product_metrics(
    admin_user: Dict = Depends(get_admin_user),
) -> AdminProductMetrics:
    """Active Users, Engagement, Retention, Conversion."""
    _ = admin_user
    data = await get_product_metrics()
    return AdminProductMetrics(**data)
