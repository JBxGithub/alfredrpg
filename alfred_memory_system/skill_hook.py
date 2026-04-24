#!/usr/bin/env python3
"""
AMS Skill Hook - OpenClaw 整合入口

這個檔案讓 AMS 可以作為 OpenClaw Skill 運行，
在每次對話後自動執行 Context 檢查和記憶同步。
"""

import os
import sys

# 添加 AMS 到路徑
AMS_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AMS_PATH not in sys.path:
    sys.path.insert(0, AMS_PATH)

from alfred_memory_system import AMS
from alfred_memory_system.config import AMSConfig

# 全局 AMS 實例
_ams_instance = None

def get_ams():
    """獲取或創建 AMS 實例"""
    global _ams_instance
    if _ams_instance is None:
        config = AMSConfig.load_from_file()
        _ams_instance = AMS(config)
    return _ams_instance


def on_session_start(session_id: str, platform: str = 'unknown'):
    """
    Session 開始時調用
    
    Args:
        session_id: Session ID
        platform: 平台 (whatsapp, telegram, etc.)
    """
    try:
        ams = get_ams()
        
        # 創建 session 記錄
        ams.db.create_session(session_id, platform)
        
        # 同步現有記憶
        if ams.config.memory.auto_sync:
            ams.integration.memory_sync.sync_to_memory_md()
        
        print(f"✅ AMS initialized for session {session_id[:8]}...")
        
    except Exception as e:
        print(f"⚠️ AMS initialization warning: {e}")


def on_message(session_id: str, messages: list, role: str = 'user'):
    """
    每次消息後調用
    
    Args:
        session_id: Session ID
        messages: 當前對話消息列表
        role: 消息角色 (user/assistant)
    """
    try:
        ams = get_ams()
        
        # 檢查是否需要 Context 檢查
        if ams.context_monitor.should_check(len(messages)):
            status = ams.context_monitor.check_context(messages)
            
            # 記錄使用情況
            ams.context_monitor.log_usage(session_id, status)
            
            # 如果需要行動，返回警告
            if status.action_required:
                return {
                    'warning': True,
                    'status': status.status,
                    'usage_percent': status.usage_percent,
                    'message': str(status)
                }
        
        return None
        
    except Exception as e:
        print(f"⚠️ AMS message hook warning: {e}")
        return None


def on_session_end(session_id: str, summary: str = None):
    """
    Session 結束時調用
    
    Args:
        session_id: Session ID
        summary: 對話摘要
    """
    try:
        ams = get_ams()
        
        # 結束 session 記錄
        ams.db.end_session(session_id, summary)
        
        # 自動同步記憶
        if ams.config.memory.auto_sync:
            ams.integration.memory_sync.sync_from_conversation(session_id)
        
        print(f"✅ AMS session {session_id[:8]}... ended")
        
    except Exception as e:
        print(f"⚠️ AMS session end warning: {e}")


# OpenClaw Skill 入口點
def skill_init():
    """Skill 初始化"""
    print("🧠 Alfred Memory System Skill loaded")


def skill_status():
    """返回 Skill 狀態"""
    try:
        ams = get_ams()
        stats = ams.get_stats()
        return {
            'status': 'active',
            'stats': stats
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }
