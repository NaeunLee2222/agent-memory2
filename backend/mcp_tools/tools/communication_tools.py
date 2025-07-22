import asyncio
from typing import Dict, Any, List

async def send_slack_message(channel: str = "#general", message: str = "", mentions: List[str] = None) -> Dict[str, Any]:
    """슬랙 메시지 전송"""
    await asyncio.sleep(0.3)  # 시뮬레이션
    
    if not mentions:
        mentions = []
    
    formatted_message = message
    if mentions:
        mention_str = " ".join([f"@{user}" for user in mentions])
        formatted_message = f"{mention_str} {message}"
    
    return {
        "channel": channel,
        "message": formatted_message,
        "mentions": mentions,
        "timestamp": asyncio.get_event_loop().time(),
        "status": "sent"
    }