"""
日志配置
优化日志输出
"""
import sys
from loguru import logger
from setting import LOG_LEVEL, LOG_FILE, LOG_FORMAT


def setup_logger(name='proxy_pool', level=None, log_file=None):
    """
    配置日志
    
    Args:
        name: 日志器名称
        level: 日志级别，可选
        log_file: 日志文件路径，可选
    
    Returns:
        logger实例
    """
    # 移除默认处理器
    logger.remove()
    
    # 设置日志级别
    log_level = level or LOG_LEVEL
    log_file_path = log_file or LOG_FILE
    
    # 控制台输出配置
    console_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
    
    # 控制台输出
    logger.add(
        sys.stderr,
        level=log_level,
        format=console_format,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 文件输出
    if log_file_path:
        logger.add(
            log_file_path,
            level=log_level,
            format=LOG_FORMAT,
            rotation="10 MB",  # 文件大小达到10MB时轮转
            retention="7 days",  # 保留7天的日志
            compression="zip",  # 压缩旧日志
            encoding="utf-8",
            backtrace=True,
            diagnose=True
        )
    
    return logger.bind(name=name)