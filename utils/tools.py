"""
工具函数
优化代理解析和格式化
"""
import re
import socket
from urllib.parse import urlparse


def format_proxy(proxy_str, default_protocol='http'):
    """
    格式化代理字符串
    
    Args:
        proxy_str: 代理字符串，如"127.0.0.1:8080"或"http://127.0.0.1:8080"
        default_protocol: 默认协议
    
    Returns:
        (ip, port, protocol)
    """
    if not proxy_str:
        return None
    
    # 移除空白字符
    proxy_str = proxy_str.strip()
    
    # 如果包含协议，解析协议
    if '://' in proxy_str:
        parsed = urlparse(proxy_str)
        protocol = parsed.scheme
        host = parsed.hostname
        port = parsed.port
    else:
        protocol = default_protocol
        # 解析IP:PORT格式
        if ':' in proxy_str:
            parts = proxy_str.split(':', 1)
            host = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                return None
        else:
            return None
    
    if not host or not port:
        return None
    
    return host, port, protocol


def validate_ip(ip):
    """验证IP地址格式"""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def validate_port(port):
    """验证端口号"""
    try:
        port = int(port)
        return 1 <= port <= 65535
    except (ValueError, TypeError):
        return False


def validate_proxy(proxy_str):
    """验证代理格式"""
    result = format_proxy(proxy_str)
    if not result:
        return False
    
    ip, port, _ = result
    return validate_ip(ip) and validate_port(port)


def parse_proxy_string(proxy_str):
    """
    解析代理字符串，支持多种格式
    
    Args:
        proxy_str: 代理字符串，如"127.0.0.1:8080", "http://127.0.0.1:8080", "socks5://127.0.0.1:1080"
    
    Returns:
        dict: 包含host, port, protocol, raw_string
    """
    if not proxy_str:
        return None
    
    proxy_str = proxy_str.strip()
    
    # 默认值
    result = {
        'raw_string': proxy_str,
        'host': None,
        'port': None,
        'protocol': 'http'
    }
    
    # 解析协议
    if '://' in proxy_str:
        parsed = urlparse(proxy_str)
        result['protocol'] = parsed.scheme
        result['host'] = parsed.hostname
        result['port'] = parsed.port
    else:
        # 解析IP:PORT格式
        if ':' in proxy_str:
            parts = proxy_str.split(':', 1)
            result['host'] = parts[0]
            try:
                result['port'] = int(parts[1])
            except ValueError:
                return None
        else:
            return None
    
    # 如果没有端口，使用默认端口
    if not result['port']:
        if result['protocol'] == 'https':
            result['port'] = 443
        else:
            result['port'] = 80
    
    return result


def proxy_to_simple_string(proxy_dict):
    """将代理字典转换为简单的 ip:port 字符串"""
    if not proxy_dict or 'host' not in proxy_dict or 'port' not in proxy_dict:
        return None
    
    return f"{proxy_dict['host']}:{proxy_dict['port']}"


def proxy_to_url(proxy_dict):
    """将代理字典转换为URL字符串"""
    if not proxy_dict or 'host' not in proxy_dict or 'port' not in proxy_dict:
        return None
    
    protocol = proxy_dict.get('protocol', 'http')
    host = proxy_dict['host']
    port = proxy_dict['port']
    
    return f"{protocol}://{host}:{port}"


def extract_proxies_from_text(text):
    """从文本中提取代理列表"""
    proxies = []
    
    # 匹配IP:PORT格式
    pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}\b'
    matches = re.findall(pattern, text)
    
    for match in matches:
        if validate_proxy(match):
            proxies.append(match)
    
    return proxies


def normalize_proxy(proxy_str):
    """规范化代理字符串，返回 ip:port 格式"""
    parsed = parse_proxy_string(proxy_str)
    if parsed:
        return f"{parsed['host']}:{parsed['port']}"
    return None


def split_list(lst, n):
    """将列表分割成n份"""
    k, m = divmod(len(lst), n)
    return [lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]


def retry_on_failure(max_retries=3, delay=1):
    """
    失败重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
    """
    import time
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # 指数退避
                    continue
            raise last_exception
        return wrapper
    return decorator