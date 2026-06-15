
## uv pip install -e. (installing packages from a cloned project from github)
import hashlib
from typing import Optional
import time
import logging
from redisvl.extensions.llmcache import SemanticCache
from redisvl.utils.vectorize import HFTextVectorizer
logger = logging.getLogger(__name__)

## in production redis for data presistence use redis
class RedisSemanticCache:
    def __init__(self, redis_url:str, redis_ttl_seconds:int = 300):
        self.encoder = HFTextVectorizer(model_name="all-MiniLM-L6-v2")
        self.cache =  SemanticCache(
            name = "agent_cache",
            redis_url =redis_url, 
            distance_threshold = 0.1,
            vectorizer = self.encoder)
        self.cache.set_ttl(redis_ttl_seconds)
    def get(self, query:str)->Optional[str]:
        """Check if a semantic cache exists for the query and return it if it does."""
        try:
            #check() automatically embed the quey and run a vector search in redis
            hits = self.cache.check(prompt=query)
            if hits:
                logger.info(f"Cache hit for query: {query}")
                return hits[0]["response"]
            else:
                logger.info(f"Cache miss for query: {query}")
                return None
        except Exception as e:
            logger.error(f"Error checking cache: {e}")
            return None
    def set(self, query:str, response:str):
        try:
            self.cache.store(prompt=query, response=response)
        except Exception as e:
            logger.error(f"Error storing cache: {e}")
#------------------------------------------
class CacheResponse:
    """In-Memory response cache with TTL (time to live)"""
    def __init__(self, ttl_seconds:int = 300):
        self.ttl = ttl_seconds
        self._cache: dict[str, dict]={}
        self._hits = 0
        self._miss = 0
    def _make_key(self, query:str)->str:
        """create a cache key"""
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def get(self, query:str)->Optional[str]:
        """get cached response if it exists or hasn't expired
        returns none on cache misses"""
        key = self._make_key(query)

        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                self._hits +=1
                return entry["response"]
            else:
                # expired
                del self._cache[key]
        self._misses +=1
        return None
    
    def set(self, query, response):
        """cache a response"""
        key = self._make_key(query)
        self._cache[key] = {
            "response": response,
            "timestamp":time.time(),
            "quer":query

        }
    @property
    def stats(self)->dict:
        total = self._hits + self._misses
        hit_rate  = self._hits / total if total > 0.0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "cached_etries": len(self._cache),
        }

    