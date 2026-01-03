"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Redis配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_KEY = os.getenv("REDIS_KEY", "proxy_pool")

# API配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 5000))

# 代理分数配置
PROXY_SCORE_MAX = 100
PROXY_SCORE_MIN = 0
PROXY_SCORE_INIT = 10

# 代理源配置
PROXY_SOURCES = [
    {
        "name": "all_proxies",
        "url": "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt",
        "type": "all"
    },
    {
        "name": "http_proxies", 
        "url": "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt",
        "type": "http"
    },
    {
        "name": "socks4_proxies",
        "url": "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks4/data.txt", 
        "type": "socks4"
    },
    {
        "name": "socks5_proxies",
        "url": "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks5/data.txt",
        "type": "socks5"
    },
    {
        "name": "us_proxies",
        "url": "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/countries/US/data.txt",
        "type": "http"
    }
]

# 代理验证配置
VALIDATE_TIMEOUT = 5
VALIDATE_URLS = [
    "http://httpbin.org/ip",
    "http://www.google.com",
    "http://www.baidu.com"
]

# 调度器配置
FETCH_INTERVAL = 300  # 5分钟
VALIDATE_INTERVAL = 60  # 1分钟
CLEAN_INTERVAL = 1800  # 30分钟

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "proxy_pool.log")
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"

# 并发配置
MAX_CONCURRENT_TASKS = 20
BATCH_SIZE = 50