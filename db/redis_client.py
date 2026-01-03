"""
Redis数据库客户端
新增pop_proxy方法支持获取并删除代理
"""
import redis
from loguru import logger
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setting import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB, REDIS_KEY


class RedisClient:
    """Redis客户端"""
    
    def __init__(self):
        self.host = REDIS_HOST
        self.port = REDIS_PORT
        self.password = REDIS_PASSWORD
        self.db = REDIS_DB
        self.key_prefix = REDIS_KEY
        self.redis = self._connect()
    
    def _connect(self):
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
            # 测试连接
            redis_client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            return redis_client
        except Exception as e:
            logger.error(f"Failed to connect Redis: {e}")
            return None
    
    def _get_key(self, protocol):
        """获取Redis键名"""
        return f"{self.key_prefix}:{protocol}"
    
    def add_proxy(self, proxy, protocol='http', score=10):
        """添加代理"""
        try:
            if not self.redis:
                return False
            
            key = self._get_key(protocol)
            # 使用有序集合，代理为成员，分数为质量分数
            result = self.redis.zadd(key, {proxy: score}, nx=True)
            return result > 0
        except Exception as e:
            logger.error(f"Error adding proxy {proxy}: {e}")
            return False
    
    def get_random_proxy(self, protocol='http'):
        """随机获取代理"""
        try:
            if not self.redis:
                return None
            
            key = self._get_key(protocol)
            
            # 先尝试获取高分代理
            high_score_proxies = self.redis.zrevrangebyscore(key, '+inf', 60, withscores=True)
            if high_score_proxies:
                import random
                return random.choice(high_score_proxies)[0]
            
            # 如果没有高分代理，获取所有代理
            all_proxies = self.redis.zrevrange(key, 0, -1, withscores=True)
            if all_proxies:
                import random
                return random.choice(all_proxies)[0]
            
            return None
        except Exception as e:
            logger.error(f"Error getting random proxy: {e}")
            return None
    
    def pop_proxy(self, protocol='http'):
        """获取并删除一个代理（新增方法）"""
        try:
            if not self.redis:
                return None
            
            key = self._get_key(protocol)
            
            # 获取最高分的代理
            proxies = self.redis.zrevrange(key, 0, 0, withscores=True)
            if not proxies:
                return None
            
            proxy = proxies[0][0]
            
            # 删除代理
            result = self.redis.zrem(key, proxy)
            if result > 0:
                logger.info(f"Popped proxy: {proxy}")
                return proxy
            else:
                return None
        except Exception as e:
            logger.error(f"Error popping proxy: {e}")
            return None
    
    def update_proxy_score(self, proxy, protocol='http', success=True):
        """更新代理分数"""
        try:
            if not self.redis:
                return False
            
            key = self._get_key(protocol)
            
            if success:
                # 成功，分数增加
                new_score = min(self.redis.zincrby(key, 1, proxy) or 10, 100)
            else:
                # 失败，分数减少
                new_score = max(self.redis.zincrby(key, -2, proxy) or 10, 0)
            
            logger.debug(f"Updated proxy {proxy} score to {new_score}")
            return True
        except Exception as e:
            logger.error(f"Error updating proxy score: {e}")
            return False
    
    def remove_proxy(self, proxy, protocol='http'):
        """移除代理"""
        try:
            if not self.redis:
                return False
            
            key = self._get_key(protocol)
            result = self.redis.zrem(key, proxy)
            if result > 0:
                logger.info(f"Removed proxy {proxy}")
            return result > 0
        except Exception as e:
            logger.error(f"Error removing proxy: {e}")
            return False
    
    def get_all_proxies(self, protocol='http'):
        """获取所有代理"""
        try:
            if not self.redis:
                return []
            
            key = self._get_key(protocol)
            proxies = self.redis.zrevrange(key, 0, -1, withscores=True)
            return [(proxy, score) for proxy, score in proxies]
        except Exception as e:
            logger.error(f"Error getting all proxies: {e}")
            return []
    
    def get_proxy_count(self, protocol='http'):
        """获取代理数量"""
        try:
            if not self.redis:
                return 0
            
            key = self._get_key(protocol)
            return self.redis.zcard(key)
        except Exception as e:
            logger.error(f"Error getting proxy count: {e}")
            return 0
    
    def clear_proxies(self, protocol='http'):
        """清除所有代理"""
        try:
            if not self.redis:
                return False
            
            key = self._get_key(protocol)
            result = self.redis.delete(key)
            logger.info(f"Cleared {result} proxies for {protocol}")
            return result > 0
        except Exception as e:
            logger.error(f"Error clearing proxies: {e}")
            return False
    
    def health_check(self):
        """健康检查"""
        try:
            if not self.redis:
                return False
            return self.redis.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def get_stats(self):
        """获取统计信息"""
        try:
            if not self.redis:
                return {}
            
            stats = {
                "total": 0,
                "by_protocol": {},
                "by_score_range": {
                    "0-20": 0,
                    "21-40": 0,
                    "41-60": 0,
                    "61-80": 0,
                    "81-100": 0
                }
            }
            
            for protocol in ['http', 'https', 'socks4', 'socks5']:
                key = self._get_key(protocol)
                proxies = self.redis.zrange(key, 0, -1, withscores=True)
                count = len(proxies)
                
                stats["by_protocol"][protocol] = count
                stats["total"] += count
                
                # 按分数范围统计
                for proxy, score in proxies:
                    score_int = int(score)
                    if score_int <= 20:
                        stats["by_score_range"]["0-20"] += 1
                    elif score_int <= 40:
                        stats["by_score_range"]["21-40"] += 1
                    elif score_int <= 60:
                        stats["by_score_range"]["41-60"] += 1
                    elif score_int <= 80:
                        stats["by_score_range"]["61-80"] += 1
                    else:
                        stats["by_score_range"]["81-100"] += 1
            
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}