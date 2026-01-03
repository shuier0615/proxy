"""
代理测试器
测试代理的可用性和速度
"""
import aiohttp
import asyncio
import time
from typing import List, Tuple
from loguru import logger
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setting import VALIDATE_TIMEOUT, VALIDATE_URLS
from db.redis_client import RedisClient


class ProxyTester:
    """代理测试器"""
    
    def __init__(self):
        self.redis_client = RedisClient()
        self.timeout = aiohttp.ClientTimeout(total=VALIDATE_TIMEOUT)
        self.test_urls = VALIDATE_URLS
    
    async def test_single_proxy(self, proxy: str, protocol: str, test_url: str) -> Tuple[bool, float]:
        """测试单个代理"""
        try:
            # 构建代理URL
            if protocol in ['socks4', 'socks5']:
                proxy_url = f"{protocol}://{proxy}"
            else:
                proxy_url = f"http://{proxy}"
            
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout
            ) as session:
                start_time = time.time()
                
                async with session.get(
                    test_url,
                    proxy=proxy_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                ) as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    if response.status == 200:
                        return True, response_time
                    else:
                        return False, response_time
                        
        except asyncio.TimeoutError:
            return False, float('inf')
        except Exception as e:
            logger.debug(f"Proxy {proxy} test failed: {e}")
            return False, float('inf')
    
    async def test_proxy(self, proxy: str, protocol: str) -> Tuple[bool, float]:
        """全面测试代理"""
        success_count = 0
        total_time = 0
        
        # 测试前2个URL
        for i in range(min(2, len(self.test_urls))):
            test_url = self.test_urls[i]
            success, response_time = await self.test_single_proxy(proxy, protocol, test_url)
            
            if success:
                success_count += 1
                total_time += response_time
        
        if success_count > 0:
            avg_time = total_time / success_count
            return True, avg_time
        else:
            return False, float('inf')
    
    async def test_proxies_batch(self, proxies: List[Tuple[str, str]]):
        """批量测试代理"""
        tasks = []
        for proxy, protocol in proxies:
            task = self.test_proxy(proxy, protocol)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_count = 0
        for (proxy, protocol), result in zip(proxies, results):
            if isinstance(result, Exception):
                logger.error(f"Error testing proxy {proxy}: {result}")
                # 测试失败，降低分数
                self.redis_client.update_proxy_score(proxy, protocol, success=False)
                continue
            
            success, response_time = result
            
            if success:
                valid_count += 1
                self.redis_client.update_proxy_score(proxy, protocol, success=True)
                logger.debug(f"Proxy {proxy} valid, response time: {response_time:.2f}s")
            else:
                self.redis_client.update_proxy_score(proxy, protocol, success=False)
                logger.debug(f"Proxy {proxy} invalid")
        
        return valid_count
    
    def get_proxies_to_test(self, protocol='http', limit=50):
        """获取需要测试的代理"""
        try:
            proxies = self.redis_client.get_all_proxies(protocol)
            if not proxies:
                return []
            
            # 按分数排序，先测试分数高的代理
            proxies.sort(key=lambda x: x[1], reverse=True)
            
            # 限制测试数量
            proxies = proxies[:limit]
            
            return [(proxy, protocol) for proxy, _ in proxies]
        except Exception as e:
            logger.error(f"Error getting proxies to test: {e}")
            return []
    
    async def run_test(self):
        """运行测试"""
        if not self.redis_client.redis:
            logger.error("Redis not connected, cannot test proxies")
            return
        
        total_tested = 0
        total_valid = 0
        
        for protocol in ['http', 'https', 'socks4', 'socks5']:
            proxies = self.get_proxies_to_test(protocol, limit=20)
            if not proxies:
                continue
            
            logger.info(f"Testing {len(proxies)} {protocol} proxies...")
            
            valid_count = await self.test_proxies_batch(proxies)
            
            total_tested += len(proxies)
            total_valid += valid_count
            
            logger.info(f"{protocol.upper()} test result: {valid_count}/{len(proxies)} valid")
        
        logger.info(f"Total test result: {total_valid}/{total_tested} valid proxies")
    
    def run(self):
        """运行代理测试"""
        asyncio.run(self.run_test())

if __name__ == '__main__':
    from utils.logger import setup_logger
    setup_logger('tester')
    
    tester = ProxyTester()
    tester.run()