"""
代理获取器
"""
import requests
import time
from typing import List
from loguru import logger
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setting import PROXY_SOURCES
from .proxy import Proxy


class ProxyFetcher:
    """代理获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def fetch_from_source(self, source: dict) -> List[Proxy]:
        """从指定源获取代理"""
        proxies = []
        try:
            logger.info(f"Fetching proxies from {source['name']}")
            response = self.session.get(source['url'], timeout=10)
            response.raise_for_status()
            
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and ':' in line and not line.startswith('#'):
                    try:
                        proxy = Proxy.from_string(line, source.get('type', 'http'))
                        proxies.append(proxy)
                    except Exception as e:
                        logger.debug(f"Invalid proxy format: {line}, error: {e}")
                        continue
            
            logger.info(f"Fetched {len(proxies)} proxies from {source['name']}")
            return proxies
        except Exception as e:
            logger.error(f"Failed to fetch from {source['name']}: {e}")
            return []
    
    def fetch_all(self) -> List[Proxy]:
        """从所有源获取代理"""
        all_proxies = []
        
        for source in PROXY_SOURCES:
            proxies = self.fetch_from_source(source)
            all_proxies.extend(proxies)
            time.sleep(1)  # 避免请求过快
        
        # 去重
        unique_proxies = []
        seen = set()
        
        for proxy in all_proxies:
            if proxy.address not in seen:
                seen.add(proxy.address)
                unique_proxies.append(proxy)
        
        logger.info(f"Total fetched {len(unique_proxies)} unique proxies")
        return unique_proxies