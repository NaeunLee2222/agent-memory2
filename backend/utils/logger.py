# 5. backend/utils/logger.py - 로거 유틸리티 파일 생성

import logging
import sys
from typing import Optional

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """로거 인스턴스 생성"""
    
    # 로그 레벨 설정
    log_level = level or "INFO"
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 핸들러가 이미 있으면 중복 추가 방지
    if not logger.handlers:
        # 콘솔 핸들러 생성
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level.upper()))
        
        # 포매터 생성
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # 핸들러를 로거에 추가
        logger.addHandler(handler)
    
    return logger
