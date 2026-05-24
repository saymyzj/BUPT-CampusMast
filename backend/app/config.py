"""
文件说明：
这是后端统一配置入口，负责从环境变量中读取应用、数据库、Redis、JWT、
OSS 与 DeepSeek 等配置。组长后续应保持所有新配置都从这里集中读取。
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CampusMast API"
    app_env: str = "development"
    app_debug: bool = True
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = "mysql+pymysql://campusmast:campusmast@127.0.0.1:3306/campusmast"
    redis_url: str = "redis://127.0.0.1:6379/0"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    oss_endpoint: str = ""
    oss_bucket_name: str = ""
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_base_url: str = ""

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


def get_cors_origin_list() -> list[str]:
    """
    文件说明：
    这是 CORS 白名单解析函数。
    它把环境变量中的逗号分隔字符串转成 FastAPI 可直接使用的 origin 列表，
    避免把 `allow_origins=["*"]` 带到部署环境里。
    """
    return [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
