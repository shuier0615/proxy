# 代理池系统

## 项目简介
ProxyPool 是一个智能代理管理系统，提供多协议代理服务、分布式存储和高效的代理调度功能。本项目采用 MIT 许可证，欢迎贡献代码。

## 功能特点
- 支持 HTTP/HTTPS/SOCKS4/SOCKS5 四种协议
- Redis 分布式存储，高性能代理管理
- 自动化代理获取、验证和清理系统
- Docker 和传统方式两种部署方案
- 完整的 RESTful API 接口

## 项目结构
```
core/         # 核心模块
├── proxy.py   # 代理数据模型
├── storage.py # 代理存储管理
├── fetcher.py # 代理获取器
├── validator.py # 代理验证器
api/          # API模块
├── web.py     # Flask应用
db/           # 数据库模块
├── redis_client.py # Redis客户端
scheduler/    # 调度器模块
├── scheduler.py # 定时任务调度
utils/        # 工具模块
├── logger.py  # 日志配置
├── tools.py   # 工具函数
```
## 快速开始

### 安装
```bash
pip install -r requirements.txt
```

### 配置
修改 `setting.py` 中的以下参数：
```python
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
MAX_CONCURRENT_TASKS = 20
BATCH_SIZE = 50
VALIDATE_TIMEOUT = 5
```

### 运行
```bash
python -m main.py
```

## API 使用

### 接口说明

| 接口 | 方法 | 描述 | 参数 | 返回 |
|------|------|------|------|------|
| /get | GET | 随机获取代理 | type(可选) | ip:port |
| /pop | GET | 获取并删除代理 | type(可选) | ip:port |
| /all | GET | 获取所有代理 | type(可选) | 每行一个ip:port |
| /count | GET | 获取代理数量 | 无 | JSON |
| /delete | GET | 删除代理 | proxy(必需) | 无 |
| /status | GET | 系统状态 | 无 | JSON |

### 使用示例
```bash
# 获取HTTP代理
curl http://localhost:5000/get
# 返回: 123.45.67.89:8080

# 获取HTTPS代理
curl "http://localhost:5000/get?type=https"
# 返回: 123.45.67.90:443

# 获取所有代理
curl http://localhost:5000/all
# 返回:
# 123.45.67.89:8080
# 123.45.67.90:443
# 123.45.67.91:3128

# 获取代理数量
curl http://localhost:5000/count
# 返回: {"http": 150, "https": 45, "socks4": 12, "socks5": 8, "total": 215}
```

### 爬虫集成
```python
import requests

def get_proxy(proxy_type='http'):
    """从代理池获取代理"""
    try:
        response = requests.get(f"http://localhost:5000/get?type={proxy_type}", timeout=5)
        if response.status_code == 200:
            return response.text.strip()  # 返回格式: ip:port
    except:
        return None

def delete_proxy(proxy):
    """删除失效代理"""
    try:
        requests.get(f"http://localhost:5000/delete?proxy={proxy}", timeout=5)
    except:
        pass

# 使用代理
proxy = get_proxy('http')
if proxy:
    proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}'
    }
    response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
    print(response.json())
```

## 模块说明

1. **核心模块** (core/)
   - proxy.py: 代理数据模型，定义代理对象结构
   - storage.py: 代理存储管理，处理Redis操作
   - fetcher.py: 代理获取器，从多个源获取代理
   - validator.py: 代理验证器，验证代理可用性

2. **API模块** (api/)
   - web.py: Flask应用，提供RESTful API接口

3. **数据库模块** (db/)
   - redis_client.py: Redis客户端封装，处理代理存储

4. **调度器模块** (scheduler/)
   - scheduler.py: 定时任务调度，管理代理获取、验证、清理任务

5. **工具模块** (utils/)
   - logger.py: 日志配置
   - tools.py: 工具函数

## 扩展代理源

在 `proxy_getter.py` 中添加自定义代理源方法：

```python
def fetch_custom_source(self):
    """自定义代理源获取方法"""
    proxies = []
    try:
        response = requests.get("https://api.example.com/proxies", timeout=10)
        data = response.json()
        
        for item in data.get('proxies', []):
            proxies.append({
                'proxy': f"{item['ip']}:{item['port']}",
                'protocol': item.get('type', 'http')
            })
    except Exception as e:
        print(f"获取自定义代理源失败: {e}")
    
    return proxies
```

在 run方法中调用新的代理源方法。

## 故障排除

### 常见问题

**Redis连接失败**
```bash
# 检查Redis服务状态
redis-cli ping

# 检查配置
cat setting.py | grep REDIS
```

**代理获取失败**
```bash
# 查看代理获取日志
tail -f proxy_pool.log | grep "fetch"

# 手动测试代理源
python -c "import requests; r=requests.get('https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt'); print(len(r.text))"
```

**API服务无法启动**
```bash
# 检查端口占用
lsof -i:5000

# 检查依赖
pip install -r requirements.txt
```

## 性能调优

### 调整并发参数
在 setting.py中调整以下参数：
```python
# 并发配置
MAX_CONCURRENT_TASKS = 20    # 最大并发任务数
BATCH_SIZE = 50             # 批量处理大小
VALIDATE_TIMEOUT = 5        # 验证超时时间
```

### Redis优化
```bash
# 调整Redis配置
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## 贡献指南
1. Fork 本仓库
2. 创建特性分支 `git checkout -b feature/AmazingFeature`
3. 提交更改 `git commit -m 'Add some AmazingFeature'`
4. 推送到分支 `git push origin feature/AmazingFeature`
5. 创建 Pull Request

## 许可证
本项目采用 MIT 许可证 - 查看 LICENSE 了解详情

## 联系方式
- 项目地址: https://github.com/shuier0615/proxy
- 问题反馈: Issues
- 文档: Wiki