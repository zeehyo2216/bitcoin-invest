"""
로깅 설정 모듈
일별 로그 파일 생성 및 콘솔 출력 지원
"""
import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(name: str = 'trading_bot', log_dir: str = None) -> logging.Logger:
    """
    로거 설정
    
    Args:
        name: 로거 이름
        log_dir: 로그 디렉토리 경로 (None이면 환경변수 또는 기본값 사용)
    
    Returns:
        설정된 로거 객체
    """
    # 로그 디렉토리 결정
    if log_dir is None:
        # 환경변수 확인
        log_dir = os.getenv('LOG_DIR')
        
        # 환경변수가 없으면 기본값 사용
        if log_dir is None:
            # 프로젝트 디렉토리 내 logs 폴더 (권장)
            project_root = Path(__file__).parent
            log_dir = project_root / 'logs'
            
            # 또는 /var/log 사용 (리눅스 서버 환경)
            # log_dir = '/var/log/trading_bot'
    
    # 디렉토리 생성
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 일별 로그 파일명 생성
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = log_path / f'trading_bot_{today}.log'
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 기존 핸들러 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 파일 핸들러 (일별 로그 파일)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30,  # 30일치 보관
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 콘솔 핸들러 (선택적, 환경변수로 제어)
    if os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true':
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


# 전역 로거 인스턴스
logger = setup_logger()

