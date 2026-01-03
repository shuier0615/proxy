"""
API测试客户端
用于测试新增的API功能
"""
import requests
import time
import json
from loguru import logger
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger


class ProxyPoolClient:
    """代理池API客户端"""
    
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ProxyPoolClient/1.0.0"
        })
    
    def get_api_info(self):
        """获取API信息"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting API info: {e}")
            return None
    
    def get_proxy(self, proxy_type='http'):
        """获取随机代理"""
        try:
            response = self.session.get(
                f"{self.base_url}/get",
                params={"type": proxy_type},
                timeout=5
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error getting proxy: {e}")
            return None
    
    def pop_proxy(self, proxy_type='http'):
        """获取并删除代理"""
        try:
            response = self.session.get(
                f"{self.base_url}/pop",
                params={"type": proxy_type},
                timeout=5
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error popping proxy: {e}")
            return None
    
    def get_all_proxies(self, proxy_type=None):
        """获取所有代理"""
        try:
            params = {}
            if proxy_type:
                params['type'] = proxy_type
            
            response = self.session.get(
                f"{self.base_url}/all",
                params=params,
                timeout=10
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error getting all proxies: {e}")
            return None
    
    def get_count(self):
        """获取代理数量"""
        try:
            response = self.session.get(f"{self.base_url}/count", timeout=5)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting count: {e}")
            return None
    
    def delete_proxy(self, proxy):
        """删除代理"""
        try:
            response = self.session.get(
                f"{self.base_url}/delete",
                params={"proxy": proxy},
                timeout=5
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error deleting proxy: {e}")
            return None
    
    def get_status(self):
        """获取系统状态"""
        try:
            response = self.session.get(f"{self.base_url}/status", timeout=5)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return None
    
    def test_all_endpoints(self):
        """测试所有API端点"""
        results = {}
        
        # 1. 测试API信息
        logger.info("Testing / endpoint...")
        results['api_info'] = self.get_api_info()
        
        # 2. 测试状态
        logger.info("Testing /status endpoint...")
        results['status'] = self.get_status()
        
        # 3. 测试代理数量
        logger.info("Testing /count endpoint...")
        results['count'] = self.get_count()
        
        # 4. 测试获取代理
        logger.info("Testing /get endpoint...")
        results['get_proxy'] = self.get_proxy('http')
        
        # 5. 测试获取所有代理
        logger.info("Testing /all endpoint...")
        results['all_proxies'] = self.get_all_proxies()
        
        # 6. 测试pop代理（如果有代理的话）
        if results['get_proxy'] and results['get_proxy']['code'] == 200:
            proxy = results['get_proxy']['data']['proxy']
            logger.info(f"Testing /pop endpoint with proxy: {proxy}")
            results['pop_proxy'] = self.pop_proxy('http')
            
            # 7. 测试删除代理
            if results['pop_proxy'] and results['pop_proxy']['code'] == 200:
                popped_proxy = results['pop_proxy']['data']['proxy']
                logger.info(f"Testing /delete endpoint with proxy: {popped_proxy}")
                results['delete_proxy'] = self.delete_proxy(popped_proxy)
        
        return results
    
    def benchmark(self, iterations=10):
        """性能基准测试"""
        logger.info(f"Starting benchmark with {iterations} iterations...")
        
        times = []
        successes = 0
        
        for i in range(iterations):
            start_time = time.time()
            result = self.get_proxy('http')
            end_time = time.time()
            
            response_time = end_time - start_time
            times.append(response_time)
            
            if result and result.get('code') == 200:
                successes += 1
            
            time.sleep(0.1)  # 避免请求过快
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            success_rate = (successes / iterations) * 100
            
            return {
                "iterations": iterations,
                "success_rate": f"{success_rate:.1f}%",
                "avg_response_time": f"{avg_time:.3f}s",
                "min_response_time": f"{min_time:.3f}s",
                "max_response_time": f"{max_time:.3f}s"
            }
        
        return None


def main():
    """主函数"""
    # 设置日志
    setup_logger('api_client')
    
    # 创建客户端
    client = ProxyPoolClient()
    
    # 测试所有端点
    logger.info("=" * 50)
    logger.info("Starting API endpoint tests...")
    logger.info("=" * 50)
    
    results = client.test_all_endpoints()
    
    # 打印结果
    logger.info("\n" + "=" * 50)
    logger.info("API Test Results:")
    logger.info("=" * 50)
    
    for endpoint, result in results.items():
        if result:
            logger.info(f"\n{endpoint.upper()}:")
            logger.info(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            logger.error(f"\n{endpoint.upper()}: No response")
    
    # 性能测试
    logger.info("\n" + "=" * 50)
    logger.info("Performance Benchmark:")
    logger.info("=" * 50)
    
    benchmark_result = client.benchmark(5)
    if benchmark_result:
        for key, value in benchmark_result.items():
            logger.info(f"{key}: {value}")
    
    logger.info("\nAPI testing completed!")


if __name__ == '__main__':
    main()