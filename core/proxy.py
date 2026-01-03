"""
代理数据模型
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse


class Proxy:
    """代理数据模型"""
    
    def __init__(self, ip: str, port: int, protocol: str = "http"):
        self.ip = ip
        self.port = port
        self.protocol = protocol
        self.score = 10
        self.last_checked: Optional[datetime] = None
        self.response_time: Optional[float] = None
        self.country: Optional[str] = None
        self.anonymous: bool = False
    
    @property
    def address(self) -> str:
        """返回代理地址"""
        return f"{self.ip}:{self.port}"
    
    @property
    def url(self) -> str:
        """返回代理URL"""
        if self.protocol in ['socks4', 'socks5']:
            return f"{self.protocol}://{self.ip}:{self.port}"
        return f"http://{self.ip}:{self.port}"
    
    @classmethod
    def from_string(cls, proxy_str: str, protocol: str = "http") -> "Proxy":
        """从字符串创建代理实例"""
        if "://" in proxy_str:
            parsed = urlparse(proxy_str)
            ip = parsed.hostname
            port = parsed.port
            if parsed.scheme in ['http', 'https', 'socks4', 'socks5']:
                protocol = parsed.scheme
        else:
            # ip:port格式
            if ":" in proxy_str:
                ip, port = proxy_str.split(":", 1)
            else:
                raise ValueError(f"Invalid proxy string: {proxy_str}")
        
        return cls(ip=ip.strip(), port=int(port), protocol=protocol)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "ip": self.ip,
            "port": self.port,
            "protocol": self.protocol,
            "score": self.score,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "response_time": self.response_time,
            "country": self.country,
            "anonymous": self.anonymous
        }
    
    def __str__(self) -> str:
        return f"{self.protocol}://{self.ip}:{self.port} (score: {self.score})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Proxy):
            return False
        return self.ip == other.ip and self.port == other.port and self.protocol == other.protocol
    
    def __hash__(self) -> int:
        return hash((self.ip, self.port, self.protocol))