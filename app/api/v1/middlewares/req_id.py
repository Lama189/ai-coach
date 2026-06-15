import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.infrastructure.context import req_id_ctx_var  


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = req_id_ctx_var.set(req_id)

        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        
        finally:
            req_id_ctx_var.reset(token)