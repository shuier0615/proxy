"""
运行脚本
提供各个模块的独立运行接口
"""
import argparse
import sys
import os
from loguru import logger

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.logger import setup_logger
from api.web import run_api_server
from getter.proxy_getter import ProxyGetter
from tester.proxy_tester import ProxyTester
from scheduler.scheduler import ProxyScheduler, run_scheduler

def run_getter():
    """运行代理获取器"""
    logger.info("Starting Proxy Getter...")
    getter = ProxyGetter()
    getter.run()

def run_tester():
    """运行代理测试器"""
    logger.info("Starting Proxy Tester...")
    tester = ProxyTester()
    tester.run()

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description="Proxy Pool Runner")
    parser.add_argument("service", 
                       choices=["all", "api", "getter", "tester", "scheduler"],
                       help="Service to run")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--host", default="0.0.0.0", help="API host")
    parser.add_argument("--port", type=int, default=5000, help="API port")
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logger(level=log_level)
    
    if args.service == "all":
        # 启动所有服务
        import threading
        
        threads = []
        
        def start_thread(target, name):
            thread = threading.Thread(target=target, name=name)
            thread.daemon = True
            thread.start()
            threads.append(thread)
            logger.info(f"Started {name}")
            return thread
        
        # 启动各个服务
        start_thread(run_scheduler, "ProxyScheduler")
        start_thread(run_getter, "ProxyGetter")
        start_thread(run_tester, "ProxyTester")
        
        # 主线程运行API
        run_api_server(host=args.host, port=args.port, debug=args.debug)
        
    elif args.service == "api":
        run_api_server(host=args.host, port=args.port, debug=args.debug)
    elif args.service == "getter":
        run_getter()
    elif args.service == "tester":
        run_tester()
    elif args.service == "scheduler":
        scheduler = ProxyScheduler()
        scheduler.start()

if __name__ == '__main__':
    main()