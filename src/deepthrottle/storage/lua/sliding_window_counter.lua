-- Sliding Window Counter Atomic Lua Script
-- KEYS[1] = limiter key (e.g. 'deepthrottle:limiter:user-123')
-- ARGV[1] = max requests allowed in the window
-- ARGV[2] = window size in seconds
-- ARGV[3] = requested cost / requests count (default: 1)
-- ARGV[4] = current timestamp (seconds as float)
-- ARGV[5] = key TTL (seconds)

local key = KEYS[1]
local max_requests = tonumber(ARGV[1])
local window_size = tonumber(ARGV[2])
local requested = tonumber(ARGV[3])
local now = tonumber(ARGV[4])
local ttl = tonumber(ARGV[5]) or math.ceil(window_size * 2)

-- HINT 1: Fetch current window counts and window start time from Redis Hash
local data = redis.call('HMGET', key, 'curr_count', 'prev_count', 'window_start')
local curr_count = tonumber(data[1]) or 0
local prev_count = tonumber(data[2]) or 0
local window_start = tonumber(data[3]) or now

-- HINT 2: Check if window has rolled over
local elapsed = now - window_start
if elapsed >= window_size then
    local windows_passed = math.floor(elapsed / window_size)
    if windows_passed == 1 then
        prev_count = curr_count
    else
        prev_count = 0
    end
    curr_count = 0
    window_start = window_start + (windows_passed * window_size)
    elapsed = now - window_start
end

-- HINT 3: Calculate weighted request count
local weight_prev = math.max(0.0, 1.0 - (elapsed / window_size))
local estimated = curr_count + (weight_prev * prev_count)

local allowed = 0
local wait_time = 0

if estimated + requested <= max_requests then
    curr_count = curr_count + requested
    allowed = 1
else
    wait_time = math.max(0.0, window_size - elapsed)
end

local remaining = math.max(0, math.floor(max_requests - (estimated + (allowed == 1 and requested or 0))))

-- HINT 4: Save state and refresh TTL
redis.call('HSET', key, 'curr_count', curr_count, 'prev_count', prev_count, 'window_start', window_start)
redis.call('EXPIRE', key, ttl)

-- Return: {allowed (1 or 0), remaining, wait_time}
return {allowed, remaining, wait_time}