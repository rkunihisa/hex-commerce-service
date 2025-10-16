from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

Role = Literal["admin", "user"]


@dataclass(slots=True, frozen=True)
class JWTSettings:
    secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    algorithm: str = os.getenv("JWT_ALG", "HS256")
    access_token_ttl_seconds: int = int(os.getenv("JWT_TTL_SECONDS", "3600"))


@dataclass(slots=True, frozen=True)
class UserPrincipal:
    subject: str
    roles: set[Role]
    jti: str
    exp: int
    iat: int


# very simple in-memory blacklist for revoked tokens (by jti)
_REVOKED_JTI: set[str] = set()


def create_access_token(
    subject: str,
    roles: Iterable[Role] = ("user",),
    expires_delta: timedelta | None = None,
    settings: JWTSettings | None = None,
) -> str:
    s = settings or JWTSettings()
    now = datetime.now(tz=UTC)
    iat = int(now.timestamp())
    exp = int((now + (expires_delta or timedelta(seconds=s.access_token_ttl_seconds))).timestamp())
    jti = jwt.utils.base64url_encode(os.urandom(16)).decode("ascii")
    payload = {
        "sub": subject,
        "roles": list(roles),
        "iat": iat,
        "exp": exp,
        "jti": jti,
    }
    return jwt.encode(payload, s.secret, algorithm=s.algorithm)


def decode_token(token: str, settings: JWTSettings | None = None) -> UserPrincipal:
    s = settings or JWTSettings()
    try:
        payload = jwt.decode(
            token,
            s.secret,
            algorithms=[s.algorithm],
            options={"require": ["exp", "iat", "sub", "jti"]},
        )
    except InvalidTokenError as exc:  # signature, exp, iat, etc.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc

    jti = payload.get("jti")
    if not isinstance(jti, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token (no jti)")

    if jti in _REVOKED_JTI:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token revoked")

    sub = payload.get("sub")
    roles_raw = payload.get("roles", [])
    iat = payload.get("iat")
    exp = payload.get("exp")

    if not isinstance(sub, str) or not isinstance(roles_raw, list) or not isinstance(iat, int) or not isinstance(exp, int):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token payload")

    roles: set[Role] = set()
    for r in roles_raw:
        if r in {"admin", "user"}:
            roles.add(r)

    if not roles:
        roles.add("user")  # default

    return UserPrincipal(subject=sub, roles=roles, jti=jti, iat=iat, exp=exp)


def revoke_token_by_jti(jti: str) -> None:
    _REVOKED_JTI.add(jti)


# FastAPI dependencies

_bearer = HTTPBearer(auto_error=False)


async def bearer_credentials(request: Request) -> HTTPAuthorizationCredentials:
    creds = await _bearer(request)
    if creds is None or not creds.scheme.lower() == "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    return creds


def get_current_user(
    settings: JWTSettings | None = None,
) -> Callable[[HTTPAuthorizationCredentials], UserPrincipal]:
    def _dep(creds: HTTPAuthorizationCredentials = Depends(bearer_credentials)) -> UserPrincipal:  # noqa: B008
        return decode_token(creds.credentials, settings)

    return _dep


def require_role(role: Role, settings: JWTSettings | None = None) -> Callable[[UserPrincipal], UserPrincipal]:
    def _dep(user: UserPrincipal = Depends(get_current_user(settings))) -> UserPrincipal:  # noqa: B008
        if role not in user.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return user

    return _dep


def require_authenticated(
    settings: JWTSettings | None = None,
) -> Callable[[UserPrincipal], UserPrincipal]:
    def _dep(user: UserPrincipal = Depends(get_current_user(settings))) -> UserPrincipal:  # noqa: B008
        return user

    return _dep
