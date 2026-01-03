"""
代理存储管理器
"""
import redis
from typing import List, Optional, Dict, Any
from loguru import logger
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setting import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB, REDIS_KEY
from .proxy import Proxy


class ProxyStorage:
    """代理存储管理器"""
    
    def __init__(self):
        self.host = REDIS_HOST
        self.port = REDIS_PORT
        self.password = REDIS_PASSWORD
        self.db = REDIS_DB
        self.key_prefix = REDIS_KEY
        self.redis = self._connect()
    
    def _connect(self) -> Optional[redis.Redis]:
        """连接Redis"""
        try:
            redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password if self.password else None,
                db=self.db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            redis_client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            return redis_client
        except Exception as e:
            logger.error(f"Failed to connect Redis: {e}")
            return None
    
    def _get_key(self, protocol: str) -> str:
        """获取Redis键名"""
        return f"{self.key_prefix}:{protocol}"
    
    def add_proxy(self, proxy: Proxy) -> bool:
        """添加代理"""
        try:
            if not self.redis:
                return False
            
            key = self._get_key(proxy.protocol)
            result = self.redis.zadd(key, {proxy.address: proxy.score}, nx=True)
            
            if result > 0:
                logger.debug(f"Added proxy: {proxy}")
            return result > 0
        except Exception as e:
            logger.error(f"Error adding proxy {proxy}: {e}")
            return False
    
    def get_random_proxy(self, protocol: str = "http") -> Optional[str]:
        """随机获取代理地址"""
        try:
            if not self.redis:
                return None
            
            key = self._get_key(protocol)
            
            # 获取高分代理
            proxies = self.redis.zrangebyscore(key, 60, 100, withscores=True)
            if not proxies:
                # 获取所有代理
                proxies = self.redis.zrange(key, 0, -1, withscores=True)
            
            if proxies:
                import random
                proxy_hash = random.choice(proxies)[0]
                return proxy_hash
            
            return None
        except Exception as e:
            logger.error(f"Error getting random proxy: {e}")
            return None
    
    def get_all_proxies(self, protocol: str = "http") -> List[tuple]:
        """获取所有代理"""
        try:
            if not self.redis:
                return []
            
            key = self._get_key(protocol)
            return self.redis.zrange(key, 0, -1, withscores=True)
        except Exception as e:
            logger.error(f"Error getting all proxies: {e}")
            return []
    
    def update_proxy_score(self, proxy: str, protocol: str = "http", success: bool = True) -> bool:
        """更新代理分数"""
        try:
            if not self.redis:
                return False
            
            key = self._get_key(protocol)
            
            if success:
                # 成功，增加分数
                new_score = min(self.redis.zincrby(key, 1, proxy) or 10, 100)
            else:
                # 失败，减少分数
                new_score = max(self.redis.zincrby(key, -2, proxy) or 10, 0)
            
            logger.debug(f"Updated proxy {proxy} score to {new_score}")
            return True
        except Exception as e:
            logger.error(f"Error updating proxy score: {e}")
            return False
    
    def remove_proxy(self, proxy: str, protocol: str = "http") -> bool:
        """移除代理"""
        try:
            if not self.redis:
                return False
            
            key = self._get_key(protocol)
            result = self.redis.zrem(key, proxy)
            logger.info(f"Removed proxy {proxy}, result: {result}")
            return result > 0
        except Exception as e:
            logger.error(f"Error removing proxy: {e}")
            return False
    
    def get_count(self, protocol: Optional[str] = None) -> Dict[str, int]:
        """获取代理数量"""
        try:
            if not self.redis:
                return {}
            
            if protocol:
                key = self._get_key(protocol)
                return {protocol: self.redis.zcard(key)}
            else:
                counts = {}
                for proto in ['http', 'https', 'socks4', 'socks5']:
                    key = self._get_key(proto)
                    counts[proto] = self.redis.zcard(key)
                return counts
        except Exception as e:
            logger.error(f"Error getting proxy count: {e}")
            return {}
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.redis:
                return False
            return self.redis.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False