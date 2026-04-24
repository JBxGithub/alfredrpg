#!/usr/bin/env python3
"""
六循環系統 - 自適應學習系統啟動器
簡化版啟動腳本
"""

import sys
import os

# 添加到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adaptive_learning_system import AdaptiveLearningSystem, main

if __name__ == "__main__":
    main()
