from prometheus_client import Counter, Histogram, Gauge

http_requests_total = Counter(
    "http_requests_total",
    "Общее количество HTTP запросов",
    ["method", "endpoint", "statuscode"]
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "Время обработки HTTP запроса",
    ["method", "endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

llm_tokens_used = Counter(
    "llm_tokens_used_total",
    "Токены используесые на все запросы",
    ["node"]
)

llm_requests_total = Counter(
    "llm_requests_total",
    "Количество запросов к Groq API",
    ["node", "status"],  
)

llm_request_duration = Histogram(
    "llm_request_duration_seconds",
    "Время ответа Groq API",
    ["node"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0],
)