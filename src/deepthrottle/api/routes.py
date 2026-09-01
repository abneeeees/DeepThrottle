from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from deepthrottle.services.ratelimiter_services import AlgorithmType, RateLimiter

app = FastAPI()

DEFAULT_STRATEGY = AlgorithmType.TOKEN_BUCKET
DEFAULT_RATE = 10.0
DEFAULT_CAPACITY = 100

# simple in-memory approach
# TODO: Later to be replaced with a persistent store such as Redis
limiters: dict[str, RateLimiter] = {}

@app.middleware("http")
async def validate_users(request: Request, call_next) -> JSONResponse | Request:
    key = request.headers.get("x-api-key")
    if not key:
        return JSONResponse(status_code=401, content={"error": "missing key"})

    if key not in limiters:
        limiters[key] = RateLimiter(DEFAULT_STRATEGY, DEFAULT_RATE, DEFAULT_CAPACITY)

    _, allowed, _ = limiters[key].allow(key)

    if not allowed:
        return JSONResponse(status_code=429, content={"error": "rate limit exceeded"})

    return await call_next(request)

# checks the health of the API
# TODO: Add health checks for the rate limiter and Redis
@app.get("/health")
def health():
    return {"status": "ok"}


# checks if a request is allowed
class CheckRequest(BaseModel):
    key: str  # the API key to check

# this endpoint checks if a request is allowed based on the configured rate limiter
@app.get("/check/{key}")
async def check(key: str):
    if key not in limiters:
        return JSONResponse(status_code=404, content={"error": "key not found"})

    state_a = limiters[key].get_state(key)
    
    limiter = RateLimiter(DEFAULT_STRATEGY, DEFAULT_RATE, DEFAULT_CAPACITY)
    tokens, allowed, wait_time = limiter.allow(key)

    state_b:dict[str, float | None] = {
        "Remaining Requests": tokens,
        "Allowed": allowed,
        "Wait Time (s)": wait_time
    }
    
    return {**state_a, **state_b}

