from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from src.core.config import settings

_API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=_API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """APIキーを検証する依存関数"""
    if api_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    return api_key
