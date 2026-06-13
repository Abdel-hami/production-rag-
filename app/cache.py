import hashlib
from typing import Optional
import time


## in production redis for data presistence

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

    