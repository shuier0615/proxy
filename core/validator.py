"""
代理验证器
"""
import aiohttp
import asyncio
from typing import List, Tuple
from loguru import logger
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setting import VALIDATE_TIMEOUT, VALIDATE_URLS
from .proxy import Proxy


class ProxyValidator:
    """代理验证器"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=VALIDATE_TIMEOUT)
        self.test_urls = VALIDATE_URLS
    
    async def validate_single(self, proxy: Proxy, test_url: str) -> Tuple[bool, float]:
        """验证单个代理"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout
            ) as session:
                start_time = asyncio.get_event_loop().time()
                
                async with session.get(
                    test_url,
                    proxy=proxy.url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                ) as response:
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    if response.status == 200:
                        return True, response_time
                    else:
                        return False, response_time
        except Exception as e:
            logger.debug(f"Proxy validation failed: {e}")
            return False, float('inf')
    
    async def validate_proxy(self, proxy: Proxy) -> Tuple[bool, float]:
        """全面验证代理"""
        success_count = 0
        total_time = 0.0
        
        for i in range(min(2, len(self.test_urls))):
            test_url = self.test_urls[i]
            success, response_time = await self.validate_single(proxy, test_url)
            
            if success:
                success_count += 1
                total_time += response_time
        
        if success_count > 0:
            return True, total_time / success_count
        else:
            return False, float('inf')
    
    async def validate_proxies(self, proxies: List[Proxy]) -> List[Proxy]:
        """批量验证代理"""
        valid_proxies = []
        
        # 限制并发数
        semaphore = asyncio.Semaphore(20)
        
        async def validate_with_semaphore(proxy: Proxy) -> Tuple[Proxy, bool, float]:
            async with semaphore:
                is_valid, response_time = await self.validate_proxy(proxy)
                return proxy, is_valid, response_time
        
        tasks = [validate_with_semaphore(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks)
        
        for proxy, is_valid, response_time in results:
            if is_valid:
                proxy.response_time = response_time
                valid_proxies.append(proxy)
                logger.debug(f"Valid proxy: {proxy}")
        
        logger.info(f"Validation completed: {len(valid_proxies)}/{len(proxies)} valid")
        return valid_proxies