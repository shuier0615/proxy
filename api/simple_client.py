"""
简单的API客户端
用于快速测试简化后的API
"""
import requests
import sys
import argparse
from loguru import logger
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger


class SimpleProxyClient:
    """简单代理客户端"""
    
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_proxy(self, proxy_type='http', simple=True):
        """获取代理"""
        try:
            if simple:
                response = self.session.get(
                    f"{self.base_url}/simple/get",
                    params={"type": proxy_type} if proxy_type else {},
                    timeout=5
                )
                return response.text.strip()
            else:
                response = self.session.get(
                    f"{self.base_url}/get",
                    params={"type": proxy_type} if proxy_type else {},
                    timeout=5
                )
                if response.headers.get('Content-Type', '').startswith('text/plain'):
                    return response.text.strip()
                else:
                    data = response.json()
                    if 'proxy' in data:
                        return data['proxy']
                    else:
                        return None
        except Exception as e:
            logger.error(f"Error getting proxy: {e}")
            return None
    
    def get_all_proxies(self, proxy_type=None, simple=True):
        """获取所有代理"""
        try:
            if simple:
                response = self.session.get(
                    f"{self.base_url}/simple/all",
                    params={"type": proxy_type} if proxy_type else {},
                    timeout=10
                )
                return [line.strip() for line in response.text.strip().split('\n') if line.strip()]
            else:
                response = self.session.get(
                    f"{self.base_url}/all",
                    params={"type": proxy_type} if proxy_type else {},
                    timeout=10
                )
                if response.headers.get('Content-Type', '').startswith('text/plain'):
                    return [line.strip() for line in response.text.strip().split('\n') if line.strip()]
                else:
                    data = response.json()
                    if 'data' in data and 'proxies' in data['data']:
                        return [item['proxy'] for item in data['data']['proxies']]
                    else:
                        return []
        except Exception as e:
            logger.error(f"Error getting all proxies: {e}")
            return []
    
    def get_count(self):
        """获取代理数量"""
        try:
            response = self.session.get(f"{self.base_url}/count", timeout=5)
            data = response.json()
            if 'counts' in data:
                return data['counts']
            return {}
        except Exception as e:
            logger.error(f"Error getting count: {e}")
            return {}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Simple Proxy Client")
    parser.add_argument("action", choices=["get", "all", "count"], help="Action to perform")
    parser.add_argument("--type", choices=["http", "https", "socks4", "socks5"], 
                       default="http", help="Proxy type")
    parser.add_argument("--url", default="http://127.0.0.1:5000", help="API base URL")
    parser.add_argument("--format", choices=["simple", "json"], default="simple", 
                       help="Output format")
    
    args = parser.parse_args()
    
    # 创建客户端
    client = SimpleProxyClient(args.url)
    
    if args.action == "get":
        proxy = client.get_proxy(args.type, simple=(args.format == "simple"))
        if proxy:
            print(proxy)
        else:
            print("No proxy available")
    
    elif args.action == "all":
        proxies = client.get_all_proxies(args.type, simple=(args.format == "simple"))
        for proxy in proxies:
            print(proxy)
    
    elif args.action == "count":
        counts = client.get_count()
        for protocol, count in counts.items():
            print(f"{protocol}: {count}")
        print(f"Total: {sum(counts.values())}")


if __name__ == '__main__':
    main()