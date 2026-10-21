import hmac

from fastapi import Header, HTTPException, Request


async def require_token(request: Request, x_internal_token: str | None = Header(default=None)) -> None:
    expected: str = request.app.state.settings.executor_token
    if x_internal_token is None or not hmac.compare_digest(x_internal_token.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
