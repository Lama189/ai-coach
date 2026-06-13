import logging
import json
import sys


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        if "user_id" in record.__dict__:
            log["user_id"] = record.__dict__["user_id"]

        if "task_id" in record.__dict__:
            log["task_id"] = record.__dict__["task_id"]

        return json.dumps(log)
    
    
def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    if not root.handlers:
        root.addHandler(handler)