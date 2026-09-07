local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local data = redis.call('HMGET', key, 'tokens', 'timestamp')
local tokens = tonumber(data[1]) or capacity
local timestamp = tonumber(data[2]) or now

-- Calculate token refill
local elapsed = math.max(0, now - timestamp)
tokens = math.min(capacity, tokens + elapsed * rate)

local allowed = 0
local remaining = tokens

if tokens >= requested then
    tokens = tokens - requested
    allowed = 1
    remaining = tokens
end

redis.call('HSET', key, 'tokens', tokens, 'timestamp', now)
redis.call('EXPIRE', key, math.ceil(capacity / rate) + 1)

local retryAfter = 0
if allowed == 0 then
    retryAfter = math.ceil((requested - tokens) / rate)
end

return {allowed, math.floor(remaining), retryAfter}