import logging
from datetime import datetime

def setup_logger():
    """Configure and return a logger instance"""
    logger = logging.getLogger('TelegramBot')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(f'bot_{datetime.now().strftime("%Y%m%d")}.log')
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    
    return logger