"""
代理获取器
从免费代理网站获取代理
"""
import requests
import time
from loguru import logger
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setting import PROXY_SOURCES
from db.redis_client import RedisClient


class ProxyGetter:
    """代理获取器"""
    
    def __init__(self):
        self.redis_client = RedisClient()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def fetch_from_source(self, source):
        """从指定源获取代理"""
        proxies = []
        try:
            logger.info(f"Fetching proxies from {source['name']}")
            response = self.session.get(source['url'], timeout=10)
            response.raise_for_status()
            
            # 解析代理列表 (ip:port格式)
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and ':' in line and not line.startswith('#'):
                    try:
                        # 清理可能的空白字符
                        proxy = line.strip()
                        if '://' in proxy:
                            # 去掉协议前缀
                            proxy = proxy.split('://')[1]
                        
                        ip, port = proxy.split(':', 1)
                        port = int(port)
                        
                        # 验证IP和端口
                        if 1 <= port <= 65535 and len(ip.split('.')) == 4:
                            proxies.append({
                                'proxy': f"{ip}:{port}",
                                'protocol': source.get('type', 'http')
                            })
                    except Exception as e:
                        logger.debug(f"Invalid proxy format: {line}, error: {e}")
                        continue
            
            logger.info(f"Fetched {len(proxies)} proxies from {source['name']}")
            return proxies
            
        except Exception as e:
            logger.error(f"Failed to fetch from {source['name']}: {e}")
            return []
    
    def process_proxies(self, proxies):
        """处理获取到的代理"""
        if not proxies:
            return
        
        added_count = 0
        for proxy_info in proxies:
            proxy = proxy_info['proxy']
            protocol = proxy_info['protocol']
            
            if self.redis_client.add_proxy(proxy, protocol):
                added_count += 1
        
        logger.info(f"Added {added_count} new proxies to pool")
    
    def run(self):
        """运行代理获取"""
        if not self.redis_client.redis:
            logger.error("Redis not connected, cannot fetch proxies")
            return
        
        logger.info("Starting proxy fetching...")
        
        all_proxies = []
        for source in PROXY_SOURCES:
            proxies = self.fetch_from_source(source)
            all_proxies.extend(proxies)
            
            # 避免请求过快
            time.sleep(1)
        
        # 去重
        unique_proxies = []
        seen = set()
        for proxy_info in all_proxies:
            proxy_key = (proxy_info['proxy'], proxy_info['protocol'])
            if proxy_key not in seen:
                seen.add(proxy_key)
                unique_proxies.append(proxy_info)
        
        logger.info(f"Total unique proxies: {len(unique_proxies)}")
        
        # 保存到Redis
        self.process_proxies(unique_proxies)
        
        # 统计
        for protocol in ['http', 'https', 'socks4', 'socks5']:
            count = self.redis_client.get_proxy_count(protocol)
            logger.info(f"{protocol} proxies count: {count}")

if __name__ == '__main__':
    from utils.logger import setup_logger
    setup_logger('getter')
    
    getter = ProxyGetter()
    getter.run()