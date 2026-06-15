import json
import logging
import sys

from app.infrastructure.context import get_request_id, get_current_user_id


class JsonFormatter(logging.Formatter):

    def format(self, record):
        log = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        log["request_id"] = get_request_id()

        ctx_user_id = get_current_user_id()
        if ctx_user_id != "anonymous":
            log["user_id"] = ctx_user_id
        elif "user_id" in record.__dict__:
            log["user_id"] = str(record.__dict__["user_id"])
        else:
            log["user_id"] = "anonymous"

        STANDARD_ATTRS = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
        }

        for key, value in record.__dict__.items():
            if key not in STANDARD_ATTRS and not key.startswith("_"):
                log[key] = str(value)

        return json.dumps(log, ensure_ascii=False)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    root.handlers = []
    root.addHandler(handler)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)