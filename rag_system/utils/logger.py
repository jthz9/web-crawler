import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """로거 생성
    
    Args:
        name: 로거 이름
        log_level: 로그 레벨 (기본값: INFO)
        
    Returns:
        로거 인스턴스
    """
    # 로그 레벨 설정
    level = getattr(logging, log_level or os.getenv("LOG_LEVEL", "INFO"))
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 이미 핸들러가 있으면 추가하지 않음
    if logger.handlers:
        return logger
    
    # 포맷터 생성
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러
    log_file = os.getenv("LOG_FILE", "logs/app.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger 