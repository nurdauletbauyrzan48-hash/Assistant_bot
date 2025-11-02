import subprocess
import time
import psutil
import logging
from datetime import datetime

def setup_watchdog_logger():
    """Configure watchdog logger"""
    logger = logging.getLogger('WatchdogBot')
    logger.setLevel(logging.INFO)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(f'watchdog_{datetime.now().strftime("%Y%m%d")}.log')

    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger

logger = setup_watchdog_logger()

def is_bot_running():
    """Check if the bot process is running"""
    try:
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and 'bot.py' in cmdline[-1]: