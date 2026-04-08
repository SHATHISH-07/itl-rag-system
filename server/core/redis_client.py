import redis
import logging
import os

logger = logging.getLogger(__name__)


def get_redis_client():
    try:
        client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )

        client.ping()
        logger.info("Redis connected ")

        return client

    except redis.ConnectionError as e:
        logger.error(f"Redis connection failed : {e}")
        return None



redis_client = get_redis_client()