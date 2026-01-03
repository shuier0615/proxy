"""
调度器模块
使用 schedule 库进行定时任务调度
"""
import schedule
import time
import threading
from loguru import logger
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setting import FETCH_INTERVAL, VALIDATE_INTERVAL, CLEAN_INTERVAL
from getter.proxy_getter import ProxyGetter
from tester.proxy_tester import ProxyTester
from db.redis_client import RedisClient


class ProxyScheduler:
    """代理调度器"""
    
    def __init__(self):
        self.running = False
        self.getter = ProxyGetter()
        self.tester = ProxyTester()
        self.redis_client = RedisClient()
        self._lock = threading.Lock()
    
    def fetch_job(self):
        """获取代理任务"""
        with self._lock:
            logger.info("Running fetch job...")
            try:
                self.getter.run()
            except Exception as e:
                logger.error(f"Fetch job error: {e}")
    
    def test_job(self):
        """测试代理任务"""
        with self._lock:
            logger.info("Running test job...")
            try:
                self.tester.run()
            except Exception as e:
                logger.error(f"Test job error: {e}")
    
    def cleanup_job(self):
        """清理低分代理任务"""
        with self._lock:
            logger.info("Running cleanup job...")
            try:
                for protocol in ['http', 'https', 'socks4', 'socks5']:
                    proxies = self.redis_client.get_all_proxies(protocol)
                    for proxy, score in proxies:
                        if score < 10:  # 分数低于10的代理
                            self.redis_client.remove_proxy(proxy, protocol)
                            logger.debug(f"Removed low score proxy: {proxy} (score: {score})")
            except Exception as e:
                logger.error(f"Cleanup job error: {e}")
    
    def stats_job(self):
        """统计任务"""
        with self._lock:
            try:
                total_count = 0
                for protocol in ['http', 'https', 'socks4', 'socks5']:
                    count = self.redis_client.get_proxy_count(protocol)
                    total_count += count
                    logger.info(f"{protocol.upper()} proxies: {count}")
                
                logger.info(f"Total proxies in pool: {total_count}")
            except Exception as e:
                logger.error(f"Stats job error: {e}")
    
    def setup_schedule(self):
        """设置定时任务"""
        # 每5分钟获取一次代理
        schedule.every(FETCH_INTERVAL).seconds.do(self.fetch_job)
        
        # 每1分钟测试一次代理
        schedule.every(VALIDATE_INTERVAL).seconds.do(self.test_job)
        
        # 每30分钟清理一次低分代理
        schedule.every(CLEAN_INTERVAL).seconds.do(self.cleanup_job)
        
        # 每5分钟统计一次
        schedule.every(300).seconds.do(self.stats_job)
        
        logger.info("Schedule setup completed")
    
    def run_schedule(self):
        """运行调度循环"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def start(self):
        """启动调度器"""
        if not self.redis_client.redis:
            logger.error("Redis not connected, cannot start scheduler")
            return
        
        self.running = True
        self.setup_schedule()
        
        # 立即执行一次所有任务
        logger.info("Running initial tasks...")
        self.fetch_job()
        time.sleep(2)
        self.test_job()
        time.sleep(2)
        self.stats_job()
        
        logger.info("Proxy scheduler started")
        self.run_schedule()
    
    def stop(self):
        """停止调度器"""
        self.running = False
        logger.info("Proxy scheduler stopped")


def run_scheduler():
    """运行调度器的便捷函数"""
    scheduler = ProxyScheduler()
    scheduler.start()

if __name__ == '__main__':
    from utils.logger import setup_logger
    setup_logger('scheduler')
    
    scheduler = ProxyScheduler()
    scheduler.start()