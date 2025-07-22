# 2. backend/services/feedback_service.py - 임포트 수정

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import asyncio
from dataclasses import dataclass, asdict

from models.feedback import FeedbackType, FeedbackData, ProcessedFeedback
from models.memory import MemoryType, MemoryData
from services.memory_service import MemoryService
from utils.logger import get_logger

logger = get_logger(__name__)

# 나머지 FeedbackService 코드는 이전에 제공한 것과 동일...
# (중복을 피하기 위해 여기서는 클래스 시그니처만 표시)

class FeedbackService:
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
        self.feedback_queue = asyncio.Queue()
        # ... 나머지 초기화 코드
