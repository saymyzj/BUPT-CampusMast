"""
文件说明：
这是审核记录路由文件。
负责用户侧查询自己的审核记录。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.services.moderation_service import list_user_moderation_records
from app.utils.response import success

router = APIRouter(prefix="/moderation", tags=["Moderation"])


@router.get("/my-records")
def list_my_moderation_records(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return success(list_user_moderation_records(db, user.id))
