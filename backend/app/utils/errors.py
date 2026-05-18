"""
文件说明：
这是后端自定义异常文件。
业务层后续建议统一抛出这里的 AppError，再由全局异常处理器格式化返回。
"""
from __future__ import annotations


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)
