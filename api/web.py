"""
Web API服务
简化返回值，只返回IP和端口
"""
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from loguru import logger
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setting import API_HOST, API_PORT
from db.redis_client import RedisClient
from utils.logger import setup_logger
from utils.tools import parse_proxy_string

# 设置日志
logger = setup_logger('api')

app = Flask(__name__)
CORS(app)

# 初始化Redis客户端
redis_client = RedisClient()

@app.route('/')
def index():
    """API介绍"""
    return jsonify({
        "code": 200,
        "message": "Proxy Pool API - 返回纯IP:端口格式",
        "version": "1.0.0",
        "endpoints": {
            "/": {
                "method": "GET",
                "description": "API介绍",
                "params": "None"
            },
            "/get": {
                "method": "GET", 
                "description": "随机获取一个代理 (返回格式: ip:port)",
                "params": "type (可选): 过滤协议类型 (http, https, socks4, socks5)"
            },
            "/pop": {
                "method": "GET",
                "description": "获取并删除一个代理 (返回格式: ip:port)",
                "params": "type (可选): 过滤协议类型"
            },
            "/all": {
                "method": "GET",
                "description": "获取所有代理 (返回格式: 每行一个ip:port)",
                "params": "type (可选): 过滤协议类型"
            },
            "/count": {
                "method": "GET",
                "description": "查看代理数量", 
                "params": "None"
            },
            "/delete": {
                "method": "GET",
                "description": "删除代理 (返回格式: ip:port)",
                "params": "proxy: 代理地址 (host:port)"
            }
        },
        "note": "所有代理接口返回格式均为 ip:port，无其他信息"
    })

@app.route('/get')
def get_proxy():
    """随机获取一个代理，只返回 ip:port"""
    proxy_type = request.args.get('type', 'http')
    simple = request.args.get('simple', 'true').lower() == 'true'  # 默认简单模式
    
    try:
        proxy = redis_client.get_random_proxy(proxy_type)
        if proxy:
            if simple:
                # 简单模式：直接返回 ip:port
                return Response(f"{proxy}\n", mimetype='text/plain')
            else:
                # 完整模式：返回JSON
                return jsonify({
                    "code": 200,
                    "message": "success",
                    "proxy": proxy,
                    "type": proxy_type
                })
        else:
            if simple:
                return Response("No proxy available\n", mimetype='text/plain', status=404)
            else:
                return jsonify({
                    "code": 404,
                    "message": f"No {proxy_type} proxy available"
                }), 404
    except Exception as e:
        logger.error(f"Error getting proxy: {e}")
        if simple:
            return Response(f"Error: {str(e)}\n", mimetype='text/plain', status=500)
        else:
            return jsonify({
                "code": 500,
                "message": f"Internal server error: {str(e)}"
            }), 500

@app.route('/pop')
def pop_proxy():
    """获取并删除一个代理，只返回 ip:port"""
    proxy_type = request.args.get('type', 'http')
    simple = request.args.get('simple', 'true').lower() == 'true'  # 默认简单模式
    
    try:
        proxy = redis_client.pop_proxy(proxy_type)
        if proxy:
            if simple:
                # 简单模式：直接返回 ip:port
                return Response(f"{proxy}\n", mimetype='text/plain')
            else:
                # 完整模式：返回JSON
                return jsonify({
                    "code": 200,
                    "message": "success",
                    "proxy": proxy,
                    "type": proxy_type
                })
        else:
            if simple:
                return Response("No proxy available\n", mimetype='text/plain', status=404)
            else:
                return jsonify({
                    "code": 404,
                    "message": f"No {proxy_type} proxy available"
                }), 404
    except Exception as e:
        logger.error(f"Error popping proxy: {e}")
        if simple:
            return Response(f"Error: {str(e)}\n", mimetype='text/plain', status=500)
        else:
            return jsonify({
                "code": 500,
                "message": f"Internal server error: {str(e)}"
            }), 500

@app.route('/all')
def get_all_proxies():
    """获取所有代理，每行一个 ip:port"""
    proxy_type = request.args.get('type')
    simple = request.args.get('simple', 'true').lower() == 'true'  # 默认简单模式
    
    try:
        if proxy_type:
            proxies = redis_client.get_all_proxies(proxy_type)
        else:
            # 获取所有类型的代理
            all_proxies = []
            for proto in ['http', 'https', 'socks4', 'socks5']:
                proxies = redis_client.get_all_proxies(proto)
                all_proxies.extend([(p[0], p[1], proto) for p in proxies])
            proxies = all_proxies
        
        if simple:
            # 简单模式：每行一个 ip:port
            result = "\n".join([proxy[0] for proxy in proxies])
            if result:
                return Response(result + "\n", mimetype='text/plain')
            else:
                return Response("No proxies available\n", mimetype='text/plain')
        else:
            # 完整模式：返回JSON
            proxy_list = [
                {
                    "proxy": proxy[0],
                    "score": proxy[1],
                    "type": proxy[2] if len(proxy) > 2 else proxy_type
                }
                for proxy in proxies
            ]
            
            return jsonify({
                "code": 200,
                "message": "success",
                "data": {
                    "proxies": proxy_list,
                    "count": len(proxy_list)
                }
            })
    except Exception as e:
        logger.error(f"Error getting all proxies: {e}")
        if simple:
            return Response(f"Error: {str(e)}\n", mimetype='text/plain', status=500)
        else:
            return jsonify({
                "code": 500,
                "message": f"Internal server error: {str(e)}"
            }), 500

@app.route('/count')
def get_proxy_count():
    """查看代理数量"""
    try:
        counts = {}
        for protocol in ['http', 'https', 'socks4', 'socks5']:
            counts[protocol] = redis_client.get_proxy_count(protocol)
        
        return jsonify({
            "code": 200,
            "message": "success",
            "counts": counts,
            "total": sum(counts.values())
        })
    except Exception as e:
        logger.error(f"Error getting proxy count: {e}")
        return jsonify({
            "code": 500,
            "message": f"Internal server error: {str(e)}"
        }), 500

@app.route('/delete')
def delete_proxy():
    """删除代理，返回被删除的 ip:port"""
    proxy = request.args.get('proxy')
    simple = request.args.get('simple', 'true').lower() == 'true'  # 默认简单模式
    
    if not proxy:
        if simple:
            return Response("Missing proxy parameter\n", mimetype='text/plain', status=400)
        else:
            return jsonify({
                "code": 400,
                "message": "Missing proxy parameter"
            }), 400
    
    try:
        # 解析代理地址
        proxy_info = parse_proxy_string(proxy)
        if not proxy_info or not proxy_info.get('host') or not proxy_info.get('port'):
            if simple:
                return Response(f"Invalid proxy format: {proxy}\n", mimetype='text/plain', status=400)
            else:
                return jsonify({
                    "code": 400,
                    "message": f"Invalid proxy format: {proxy}"
                }), 400
        
        proxy_addr = f"{proxy_info['host']}:{proxy_info['port']}"
        protocol = proxy_info.get('protocol', 'http')
        
        # 尝试删除代理
        deleted = redis_client.remove_proxy(proxy_addr, protocol)
        
        if deleted:
            if simple:
                return Response(f"{proxy_addr}\n", mimetype='text/plain')
            else:
                return jsonify({
                    "code": 200,
                    "message": f"Proxy {proxy_addr} deleted successfully",
                    "proxy": proxy_addr,
                    "type": protocol
                })
        else:
            if simple:
                return Response(f"Proxy {proxy} not found\n", mimetype='text/plain', status=404)
            else:
                return jsonify({
                    "code": 404,
                    "message": f"Proxy {proxy} not found"
                }), 404
    except Exception as e:
        logger.error(f"Error deleting proxy: {e}")
        if simple:
            return Response(f"Error: {str(e)}\n", mimetype='text/plain', status=500)
        else:
            return jsonify({
                "code": 500,
                "message": f"Internal server error: {str(e)}"
            }), 500

@app.route('/simple/get')
def simple_get_proxy():
    """简单获取代理接口，只返回 ip:port (兼容旧版本)"""
    proxy_type = request.args.get('type', 'http')
    
    try:
        proxy = redis_client.get_random_proxy(proxy_type)
        if proxy:
            return Response(f"{proxy}\n", mimetype='text/plain')
        else:
            return Response("No proxy available\n", mimetype='text/plain', status=404)
    except Exception as e:
        logger.error(f"Error getting proxy: {e}")
        return Response(f"Error: {str(e)}\n", mimetype='text/plain', status=500)

@app.route('/simple/all')
def simple_get_all_proxies():
    """简单获取所有代理接口，每行一个 ip:port (兼容旧版本)"""
    proxy_type = request.args.get('type')
    
    try:
        if proxy_type:
            proxies = redis_client.get_all_proxies(proxy_type)
        else:
            # 获取所有类型的代理
            all_proxies = []
            for proto in ['http', 'https', 'socks4', 'socks5']:
                proxies = redis_client.get_all_proxies(proto)
                all_proxies.extend([p[0] for p in proxies])
            proxies = all_proxies
        
        result = "\n".join([proxy[0] if isinstance(proxy, tuple) else proxy for proxy in proxies])
        if result:
            return Response(result + "\n", mimetype='text/plain')
        else:
            return Response("No proxies available\n", mimetype='text/plain')
    except Exception as e:
        logger.error(f"Error getting all proxies: {e}")
        return Response(f"Error: {str(e)}\n", mimetype='text/plain', status=500)

def run_api_server(host=None, port=None, debug=False):
    """运行API服务器"""
    if not redis_client.redis:
        logger.error("Cannot start API server: Redis connection failed")
        return
    
    server_host = host or API_HOST
    server_port = port or API_PORT
    
    logger.info(f"Starting API server on {server_host}:{server_port}")
    logger.info("API endpoints returning plain text format (ip:port)")
    app.run(host=server_host, port=server_port, debug=debug)

if __name__ == '__main__':
    run_api_server()