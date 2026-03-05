# -*- encoding: utf-8 -*-
"""
自定义异常类和全局异常处理器
"""

from typing import Union, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from loguru import logger


# ==================== 自定义异常类 ====================

class AppException(Exception):
    """应用基础异常类"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Union[dict, list, None] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class ValidationError(AppException):
    """数据验证错误"""

    def __init__(self, message: str, details: Union[dict, list, None] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details
        )


class NotFoundError(AppException):
    """资源未找到错误"""

    def __init__(self, message: str, resource_type: str = "资源"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details={"resource_type": resource_type}
        )


class AuthenticationError(AppException):
    """认证错误"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(AppException):
    """授权错误"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR"
        )


class BusinessError(AppException):
    """业务逻辑错误"""

    def __init__(self, message: str, details: Union[dict, list, None] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="BUSINESS_ERROR",
            details=details
        )


class ExternalServiceError(AppException):
    """外部服务错误"""

    def __init__(self, message: str, service_name: str = "外部服务"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name}
        )


# ==================== 全局异常处理器 ====================

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """自定义应用异常处理器"""
    logger.error(
        f"应用异常: {exc.error_code} - {exc.message} | "
        f"Path: {request.url.path} | Method: {request.method}"
    )

    response_data = {
        "success": False,
        "error_code": exc.error_code,
        "message": exc.message,
    }

    if exc.details:
        response_data["details"] = exc.details

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    logger.warning(
        f"HTTP异常: {exc.status_code} - {exc.detail} | "
        f"Path: {request.url.path} | Method: {request.method}"
    )

    response_data = {
        "success": False,
        "error_code": f"HTTP_{exc.status_code}",
        "message": str(exc.detail),
    }

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器（捕获所有未处理的异常）"""
    logger.error(
        f"未捕获的异常: {type(exc).__name__} - {str(exc)} | "
        f"Path: {request.url.path} | Method: {request.method}",
        exc_info=True
    )

    response_data = {
        "success": False,
        "error_code": "INTERNAL_ERROR",
        "message": "服务器内部错误，请稍后重试",
    }

    # 在开发模式下，返回详细的错误信息
    from backend.config import settings
    if settings.debug:
        response_data["message"] = str(exc)
        response_data["exception_type"] = type(exc).__name__

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


# ==================== 错误响应构建器 ====================

def error_response(
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_code: str = "ERROR",
    details: Union[dict, list, None] = None
) -> dict:
    """构建错误响应"""
    response = {
        "success": False,
        "error_code": error_code,
        "message": message,
    }
    if details:
        response["details"] = details
    return response


def success_response(data: Any = None, message: str = "操作成功") -> dict:
    """构建成功响应"""
    response = {
        "success": True,
        "message": message,
    }
    if data is not None:
        response["data"] = data
    return response
