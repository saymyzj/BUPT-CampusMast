"""
文件说明：
这是后端 FastAPI 应用入口文件。
它负责统一挂载所有 HTTP Router、注册基础中间件、暴露健康检查接口并接入
 WebSocket 网关。你和 B 同学后续都应以它为唯一应用入口继续扩展。
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_cors_origin_list, settings
from app.routers import admin, auth, chat, credit, map, moderation, notification, recommendation, task, upload, wallet
from app.utils.errors import AppError
from app.utils.response import failure
from app.websockets.gateway import router as websocket_router

app = FastAPI(title=settings.app_name, debug=settings.app_debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origin_list(),
    allow_origin_regex=r"^https?://.*:5173$" if settings.app_env == "development" else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=failure(exc.code, exc.message, exc.details))

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(task.router, prefix=settings.api_prefix)
app.include_router(wallet.router, prefix=settings.api_prefix)
app.include_router(credit.router, prefix=settings.api_prefix)
app.include_router(notification.router, prefix=settings.api_prefix)
app.include_router(chat.router, prefix=settings.api_prefix)
app.include_router(map.router, prefix=settings.api_prefix)
app.include_router(moderation.router, prefix=settings.api_prefix)
app.include_router(recommendation.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
app.include_router(upload.router, prefix=settings.api_prefix)
app.include_router(websocket_router)


@app.get("/", tags=["Health"])
def root() -> dict:
    return {"status": "ok", "service": settings.app_name, "docs": "/docs"}


@app.get("/healthz", tags=["Health"])
def healthcheck() -> dict:
    return {"status": "ok", "service": settings.app_name}
