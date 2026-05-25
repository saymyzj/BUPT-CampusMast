"""
文件说明：
这是上传路由文件。
负责本地验收环境的任务图片上传。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Request, UploadFile, status

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.utils.local_upload import save_local_upload
from app.utils.response import success

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_task_image(request: Request, file: UploadFile = File(...), _: User = Depends(get_current_user)) -> dict:
    payload = await save_local_upload(file)
    payload["fileUrl"] = f"{str(request.base_url).rstrip('/')}{payload['fileUrl']}"
    return success(payload)
