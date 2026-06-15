import time
import functools
import logging

from app.infrastructure.context import get_request_id, get_current_user_id


logger = logging.getLogger("app_logger")


def log_duration(func):

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()

        current_req_id = get_request_id()
        current_user_id = get_current_user_id()

        logger.info(
            f"{func.__name__}_started",
            extra = {
                "user_id": str(current_user_id),
                "request_id": current_req_id,
            }
        )

        result = await func(*args, **kwargs)

        duration_ms = int((time.time() - start) * 1000)

        logger.info(
            f"{func.__name__}_finished",
            extra = {
                "user_id": str(current_user_id),
                "duration_ms": duration_ms,
                "request_id": current_req_id,
            }
        )

        return result
    
    return wrapper