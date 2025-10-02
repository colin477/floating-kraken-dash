import redis
import os

def test_redis_connection():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    print(f"Attempting to connect to Redis at {redis_url}")
    try:
        r = redis.from_url(redis_url, socket_connect_timeout=5)
        r.ping()
        print("Successfully connected to Redis and received a pong.")
    except redis.exceptions.ConnectionError as e:
        print(f"Failed to connect to Redis: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_redis_connection()
