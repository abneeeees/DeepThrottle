-- Leaky Bucket Atomic Lua Script
-- KEYS[1] = limiter key (e.g. 'deepthrottle:limiter:user-123')
-- ARGV[1] = bucket capacity (max water level)
-- ARGV[2] = leak rate (units leaked per second)
-- ARGV[3] = requested tokens / units (default: 1)
-- ARGV[4] = current timestamp (seconds as float)
-- ARGV[5] = key TTL (seconds)

local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local leak_rate = tonumber(ARGV[2])
local requested = tonumber(ARGV[3])
local now = tonumber(ARGV[4])
local ttl = tonumber(ARGV[5]) or math.ceil(capacity / leak_rate) * 2

-- HINT 1: Fetch current water level and last leak timestamp from Redis Hash
local data = redis.call('HMGET', key, 'water_level', 'last_leak')
local water_level = tonumber(data[1]) or 0.0
local last_leak = tonumber(data[2]) or now

-- HINT 2: Leak water based on elapsed time since last request
local elapsed = math.max(0, now - last_leak)
water_level = math.max(0.0, water_level - (elapsed * leak_rate))

local allowed = 0
local wait_time = 0

-- HINT 3: Check if adding new request exceeds bucket capacity
if water_level + requested <= capacity then
    water_level = water_level + requested
    allowed = 1
else
    -- Calculate how long client must wait for enough water to leak
    local excess = (water_level + requested) - capacity
    wait_time = excess / leak_rate
end

local remaining_capacity = math.max(0, capacity - water_level)

-- HINT 4: Save new state and refresh TTL
redis.call('HSET', key, 'water_level', water_level, 'last_leak', now)
redis.call('EXPIRE', key, ttl)

-- Return: {allowed (1 or 0), remaining_capacity, wait_time_seconds}
return {allowed, remaining_capacity, wait_time}