"""Админ API справочника стран — состав вопросов режимов по странам."""

from __future__ import annotations

import psycopg2
from fastapi import APIRouter, Depends, HTTPException

from deps_game_admin import verify_game_admin_token
from schemas_game import GameCountryCreate, GameCountryOut, GameCountryUpdate
from services.game_repository import GameCountryAdminRow, game_repository
from services.media_storage import resolve_public_media_url

router = APIRouter(prefix="/admin", tags=["Game Countries Admin"])


def _country_out(row: GameCountryAdminRow) -> GameCountryOut:
    flag_url = resolve_public_media_url(row.flag_image_url)
    map_url = resolve_public_media_url(row.map_image_url)
    return GameCountryOut(
        id=row.id,
        iso2=row.iso2,
        name_ru=row.name_ru,
        capital_ru=row.capital_ru,
        area_km2=row.area_km2,
        population=row.population,
        flag_image_url=flag_url,
        map_image_url=map_url,
        is_active=row.is_active,
        is_ready=bool(row.is_active and flag_url and map_url),
    )


@router.get(
    "/countries",
    response_model=list[GameCountryOut],
    dependencies=[Depends(verify_game_admin_token)],
)
async def list_countries() -> list[GameCountryOut]:
    rows = await game_repository.admin_list_countries()
    return [_country_out(row) for row in rows]


@router.post(
    "/countries",
    response_model=GameCountryOut,
    dependencies=[Depends(verify_game_admin_token)],
)
async def create_country(body: GameCountryCreate) -> GameCountryOut:
    try:
        country_id = await game_repository.admin_create_country(
            iso2=body.iso2,
            name_ru=body.name_ru,
            capital_ru=body.capital_ru,
            area_km2=body.area_km2,
            population=body.population,
            flag_image_url=body.flag_image_url,
            map_image_url=body.map_image_url,
            is_active=body.is_active,
        )
    except psycopg2.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Страна с таким ISO уже есть") from exc
    row = await game_repository.admin_get_country(country_id)
    if not row:
        raise HTTPException(status_code=500, detail="Country not found after create")
    return _country_out(row)


@router.delete(
    "/countries/{country_id}",
    dependencies=[Depends(verify_game_admin_token)],
)
async def delete_country(country_id: int) -> dict[str, str]:
    deleted = await game_repository.admin_delete_country(country_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Country not found")
    return {"status": "ok"}


@router.patch(
    "/countries/{country_id}",
    response_model=GameCountryOut,
    dependencies=[Depends(verify_game_admin_token)],
)
async def update_country(country_id: int, body: GameCountryUpdate) -> GameCountryOut:
    updates = body.model_dump(exclude_unset=True)
    updated = await game_repository.admin_update_country(country_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Country not found")
    row = await game_repository.admin_get_country(country_id)
    if not row:
        raise HTTPException(status_code=404, detail="Country not found")
    return _country_out(row)
