from __future__ import annotations

import asyncio
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from . import service
from .database import get_db
from .schemas import JobStatusOut, MessageOut


router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/douyin/status", response_model=JobStatusOut)
def douyin_status() -> JobStatusOut:
    return JobStatusOut(**service.get_douyin_status())


@router.post("/douyin/login", status_code=status.HTTP_202_ACCEPTED, response_model=MessageOut)
async def douyin_login() -> MessageOut:
    if service.is_refresh_running():
        raise HTTPException(status_code=409, detail="采集任务正在运行，请稍后再登录")

    def _open() -> None:
        service.open_login_window()

    asyncio.get_running_loop().run_in_executor(None, _open)
    return MessageOut(message="已打开浏览器，请扫码登录抖音")


@router.post("/refresh", status_code=status.HTTP_202_ACCEPTED)
async def manual_refresh() -> dict[str, str]:
    if service.is_refresh_running():
        raise HTTPException(status_code=409, detail="采集任务正在运行")

    def _run() -> None:
        try:
            service.refresh_job()
        except Exception as exc:
            # The failed job is persisted by refresh_job; this task intentionally ends here.
            print(f"Manual refresh failed: {exc}")

    asyncio.get_running_loop().run_in_executor(None, _run)
    return {"status": "accepted", "message": "采集任务已开始"}


@router.get("/itineraries")
def itineraries(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    keyword: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[dict]:
    return service.list_itineraries(
        date_from=date_from,
        date_to=date_to,
        status=status_filter,
        keyword=keyword,
        user_id=user_id,
    )


@router.get("/following")
def following() -> list[dict]:
    return service.list_following()


@router.delete("/itineraries/{itinerary_id}")
def delete_itinerary(itinerary_id: int) -> MessageOut:
    if not service.delete_itinerary(itinerary_id):
        raise HTTPException(status_code=404, detail="行程不存在")
    return MessageOut(message="已删除")
