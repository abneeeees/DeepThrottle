# DeepThrottle

A rate limiting library for HTTP APIs built with FastAPI. Supports multiple rate limiting algorithms that can be swapped via configuration.

## Algorithms

| Algorithm | How it works |
|---|---|
| **Token Bucket** | Tokens refill at a fixed rate. Each request consumes a token. Denied when empty. |
| **Leaky Bucket** | Requests queue up and leak out at a fixed rate. Denied when queue is full. |
| **Sliding Window Counter** | Counts requests in a rolling time window using weighted overlap between adjacent windows. |

## Project Structure

```
DeepThrottle/
├── src/deepthrottle/
│   ├── __main__.py
│   ├── __init__.py
│   ├── api/
│   │   └── routes.py          # FastAPI endpoints and middleware
│   ├── algorithms/
│   │   ├── token_bucket.py    # Token bucket implementation
│   │   ├── leaky_bucket.py    # Leaky bucket implementation
│   │   └── sliding_window_counter.py  # Sliding window implementation
│   └── services/
│       ├── ratelimiter_services.py    # RateLimiter wrapper + AlgorithmType enum
│       └── benchmark.py    # Benchmarking
├── pyproject.toml
└── README.md
```

## Setup

Requires Python 3.13+

```bash
# install dependencies
uv sync

# run the server
uvicorn deepthrottle.api.routes:app --reload
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| `middleware` | `http` | Validate API key and rate limit requests |
| `GET` | `/health` | Health check |
| `GET` | `/check/{key}` | Get rate limit state for a key (planned) |
| `POST` | `/create` | Create a rate limiter for a given key |
| `DELETE` | `/delete/{key}` | Delete a rate limiter for a given key |

## Usage

```python
from deepthrottle.services.ratelimiter_services import RateLimiter, AlgorithmType

limiter = RateLimiter(AlgorithmType.TOKEN_BUCKET, rate=10.0, capacity=100)
tokens, allowed, wait_time = limiter.allow()
```
