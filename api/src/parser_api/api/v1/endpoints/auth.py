from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from parser_api.api.dependencies import get_auth_service, get_client_ip, get_current_user
from parser_api.core.config import get_settings
from parser_api.schemas.auth import (
    LoginRequest,
    ProfileResponse,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
)
from parser_api.services.auth_service import AuthService, AuthenticationFailed, ConflictError

router = APIRouter()


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        domain=settings.auth_cookie_domain,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.auth_cookie_name,
        domain=settings.auth_cookie_domain,
        path="/api/v1/auth",
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        _, tokens = await auth_service.register(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            user_agent=request.headers.get("user-agent"),
            ip=get_client_ip(request),
        )
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    _set_refresh_cookie(response, tokens.refresh_token)
    return TokenResponse(access_token=tokens.access_token, token_type=tokens.token_type)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        _, tokens = await auth_service.login(
            email=payload.email,
            password=payload.password,
            user_agent=request.headers.get("user-agent"),
            ip=get_client_ip(request),
        )
    except AuthenticationFailed as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    _set_refresh_cookie(response, tokens.refresh_token)
    return TokenResponse(access_token=tokens.access_token, token_type=tokens.token_type)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    settings = get_settings()
    refresh_token = request.cookies.get(settings.auth_cookie_name)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    try:
        _, tokens = await auth_service.refresh(
            refresh_token=refresh_token,
            user_agent=request.headers.get("user-agent"),
            ip=get_client_ip(request),
        )
    except AuthenticationFailed as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    _set_refresh_cookie(response, tokens.refresh_token)
    return TokenResponse(access_token=tokens.access_token, token_type=tokens.token_type)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> Response:
    settings = get_settings()
    refresh_token = request.cookies.get(settings.auth_cookie_name)
    await auth_service.logout(refresh_token)
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=ProfileResponse)
async def get_me(user=Depends(get_current_user)) -> ProfileResponse:
    return ProfileResponse.model_validate(user)


@router.patch("/me", response_model=ProfileResponse)
async def update_me(
    payload: UpdateProfileRequest,
    auth_service: AuthService = Depends(get_auth_service),
    user=Depends(get_current_user),
) -> ProfileResponse:
    updated = await auth_service.update_profile(user=user, full_name=payload.full_name)
    return ProfileResponse.model_validate(updated)
