from __future__ import annotations

from datetime import timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Body, status
from pydantic import BaseModel, Field

from .security import JWTSettings, create_access_token, decode_token, revoke_token_by_jti

router = APIRouter()


class TestTokenIn(BaseModel):
    sub: str = Field(..., description="subject (user id)")

    @staticmethod
    def default_roles() -> list[Literal["admin", "user"]]:
        return ["user"]

    roles: list[Literal["admin", "user"]] = Field(default_factory=default_roles)
    expires_in: int | None = Field(default=None, description="seconds to expire (default from settings)")


class TokenOut(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer", description="Type of the token")


@router.post("/token/test", response_model=TokenOut, status_code=status.HTTP_200_OK)
def issue_test_token(body: TestTokenIn) -> TokenOut:
    ttl = timedelta(seconds=body.expires_in) if body.expires_in else None
    token = create_access_token(subject=body.sub, roles=body.roles, expires_delta=ttl, settings=JWTSettings())
    return TokenOut(access_token=token)


class RevokeIn(BaseModel):
    token: str = Field(..., description="access token to revoke")


@router.post("/revoke", status_code=status.HTTP_200_OK)
def revoke(body: Annotated[RevokeIn, Body(...)]) -> dict[str, bool]:
    principal = decode_token(body.token, settings=JWTSettings())
    revoke_token_by_jti(principal.jti)
    return {"revoked": True}
