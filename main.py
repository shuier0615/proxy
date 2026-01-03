"""
主程序入口
启动所有服务
"""
import threading
import time
import signal
import sys
import os
from loguru import logger

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.logger import setup_logger
from api.web import run_api_server
from scheduler.scheduler import ProxyScheduler

# 设置日志
logger = setup_logger('main')

# 全局调度器实例
scheduler = None
running = True
threads = []

def signal_handler(sig, frame):
    """信号处理函数"""
    global running, scheduler
    logger.info("Received stop signal, shutting down...")
    running = False
    
    if scheduler:
        scheduler.stop()
    
    # 等待线程结束
    for thread in threads:
        if thread.is_alive():
            thread.join(timeout=5)
    
    logger.info("All services stopped")
    sys.exit(0)

def start_scheduler():
    """启动调度器"""
    global scheduler
    scheduler = ProxyScheduler()
    scheduler.start()

def start_api_server():
    """启动API服务器"""
    run_api_server()

def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting Proxy Pool Services...")
    
    # 启动调度器线程
    scheduler_thread = threading.Thread(target=start_scheduler, name="ProxyScheduler")
    scheduler_thread.daemon = True
    scheduler_thread.start()
    threads.append(scheduler_thread)
    logger.info("Scheduler thread started")
    
    # 等待调度器初始化
    time.sleep(5)
    
    # 启动API服务（阻塞）
    logger.info("Starting API service...")
    start_api_server()

if __name__ == '__main__':
    main()