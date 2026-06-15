from contextvars import ContextVar


req_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_ctx_var: ContextVar[str | None] = ContextVar("user_id", default=None)


def get_request_id() -> str:
    return req_id_ctx_var.get() or "unknown"


def get_current_user_id() -> str:
    return user_id_ctx_var.get() or "anonymous"