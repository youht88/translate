import logging
from logging.handlers import TimedRotatingFileHandler
from logger import logger

from ylz_translate.utils.config_utils import Config

def init(args):
    # 设置logger
    log_level = logging.INFO if args.log_level=="INFO" else logging.DEBUG
    log_file = args.log if args.log else "task.log"

    logger.setLevel(log_level)

    file_handler = TimedRotatingFileHandler(
        filename= log_file,
        when="midnight",  # 每天午夜滚动
        interval=1,  # 滚动间隔为 1 天
        backupCount=7,  # 保留 7 天的日志文件
        encoding='utf-8'
    )
    #file_handler = logging.FileHandler("task.log")
    #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter('%(asctime)s %(name)s [pid:%(process)d] [%(threadName)s] [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    #设置config
    Config.init("ylz_translate", args.env_file) 