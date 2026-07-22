
## uv pip install -e. (installing packages from a cloned project from github)

from typing import Optional

import logging
from redisvl.extensions.llmcache import SemanticCache
from redisvl.utils.vectorize import HFTextVectorizer
logger = logging.getLogger(__name__)

## in production redis for data presistence use redis
class RedisSemanticCache:
    def __init__(self, redis_url:str="redis://localhost:6379", redis_ttl_seconds:int = 300):
        self.encoder = HFTextVectorizer(model="all-MiniLM-L6-v2")
        self.cache =  SemanticCache(
            name = "agent_cache",
            redis_url =redis_url, 
            distance_threshold = 0.3,
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
# class CacheResponse:
#     """In-Memory response cache with TTL (time to live)"""
#     def __init__(self, ttl_seconds:int = 300):
#         self.ttl = ttl_seconds
#         self._cache: dict[str, dict]={}
#         self._hits = 0
#         self._miss = 0

#     def _make_key(self, query:str)->str:
#         """create a cache key"""
#         normalized = query.lower().strip()
#         return hashlib.sha256(normalized.encode()).hexdigest()
    
#     def get(self, query:str)->Optional[str]:
#         """get cached response if it exists or hasn't expired
#         returns none on cache misses"""
#         key = self._make_key(query)

#         if key in self._cache:
#             entry = self._cache[key]
#             if time.time() - entry["timestamp"] < self.ttl:
#                 self._hits +=1
#                 return entry["response"]
#             else:
#                 # expired
#                 del self._cache[key]
#         self._misses +=1
#         return None
    
#     def set(self, query, response):
#         """cache a response"""
#         key = self._make_key(query)
#         self._cache[key] = {
#             "response": response,
#             "timestamp":time.time(),
#             "quer":query

#         }
#     @property
#     def stats(self)->dict:
#         total = self._hits + self._misses
#         hit_rate  = self._hits / total if total > 0.0 else 0.0
#         return {
#             "hits": self._hits,
#             "misses": self._misses,
#             "hit_rate": hit_rate,
#             "cached_etries": len(self._cache),
#         }
    


def test_redis_semantic_cache():
    print("\n" + "="*50)
    print("TESTING: Redis Semantic Cache (RedisSemanticCache)")
    print("="*50)
    


    # Ensure you have Redis Stack running locally on port 6379
    redis_url = "redis://localhost:6379"
    
    try:
        # Note: The first time this runs, it will download the 'all-MiniLM-L6-v2' model
        cache = RedisSemanticCache(redis_url=redis_url, redis_ttl_seconds=60)
        
        print("\n1. First query (Expecting MISS):")
        query1 = "what is my name?"
        response = cache.get(query1)
        print(f"   -> Result: {response}")
        
        print("\n2. Setting cache and querying exact match (Expecting HIT):")
        cache.set(query1, "abdelhamid")
        response = cache.get(query1)
        print(f"   -> Result: {response}")
        
        print("\n3. Querying a SEMANTICALLY SIMILAR string (Expecting HIT):")
        # Notice this is not an exact string match, but semantically very close!
        ## other manner to say the question "
        query_similar = "tell my name?"
        response = cache.get(query_similar)
        print(f"   -> Result: {response}")
        
        print("\n4. Querying a DIFFERENT topic (Expecting MISS):")
        query_diff = "How to fix a flat tire on a car?"
        response = cache.get(query_diff)
        print(f"   -> Result: {response}")
        
    except Exception as e:
        print(f"\nError testing Redis cache: {e}")
        print("Make sure you have a Redis Stack server running. You can start one via Docker:")
        print("docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest")
