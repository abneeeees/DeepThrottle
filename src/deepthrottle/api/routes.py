from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.deepthrottle.services.ratelimiter_services import AlgorithmType, RateLimiter

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_STRATEGY = AlgorithmType.TOKEN_BUCKET
DEFAULT_RATE = 10.0
DEFAULT_CAPACITY = 100
DEFAULT_WINDOW_SIZE: float | None = None

limiters: dict[str, RateLimiter] = {}

EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/keys", "/create"}                                                                                                                                     

# The middleware validates the API key and rate limits requests
@app.middleware("http")
async def validate_users(request: Request, call_next):

    # Excludes exempt paths for rate limiting
    if request.url.path in EXEMPT_PATHS or request.url.path.startswith(("/check/", "/delete/")):
        return await call_next(request)

    key = request.headers.get("x-api-key")
    if not key:
        return JSONResponse(status_code=401, content={"error": "missing key"})

    if key not in limiters:
        limiters[key] = RateLimiter(
            DEFAULT_STRATEGY,
            rate=DEFAULT_RATE,
            capacity=DEFAULT_CAPACITY,
            window_size_seconds=DEFAULT_WINDOW_SIZE,
        )

    _, allowed, wait_time = limiters[key].allow(key)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": "rate limit exceeded", "wait_time": wait_time},
            headers={"Retry-After": str(wait_time)}
        )

    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/keys")
def list_keys():
    keys = []
    for key, limiter in limiters.items():
        algo_name = limiter.algorithm.name
        keys.append({
            "key": key,
            "algorithm": algo_name,
            "rate": limiter.rate,
            "capacity": limiter.capacity,
        })
    return {"keys": keys}


@app.get("/check/{key}")
async def check(key: str):
    if key not in limiters:
        return JSONResponse(status_code=404, content={"error": "key not found"})

    return limiters[key].get_state()


@app.post("/create")
async def create_limiter(request: Request):
    body = await request.json()
    key = body.get("key")

    if not key:
        return JSONResponse(status_code=400, content={"error": "key is required"})

    strategy_name = body.get("strategy", DEFAULT_STRATEGY.name)
    if isinstance(strategy_name, str):
        try:
            strategy = AlgorithmType[strategy_name]
        except KeyError:
            return JSONResponse(
                status_code=400,
                content={"error": f"invalid strategy: {strategy_name}"},
            )
    else:
        strategy = strategy_name

    rate = float(body.get("rate", DEFAULT_RATE))
    capacity = int(body.get("capacity", DEFAULT_CAPACITY))
    window_size = body.get("window_size_seconds")
    if window_size is not None:
        window_size = float(window_size)

    limiters[key] = RateLimiter(
        strategy,
        rate=rate,
        capacity=capacity,
        window_size_seconds=window_size,
    )

    return JSONResponse(status_code=201, content={"message": "limiter created"})


@app.delete("/delete/{key}")
async def delete_limiter(key: str):
    if key not in limiters:
        return JSONResponse(status_code=404, content={"error": "key not found"})

    del limiters[key]
    return JSONResponse(status_code=200, content={"message": "limiter deleted"})
