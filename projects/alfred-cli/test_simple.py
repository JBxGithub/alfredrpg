#!/usr/bin/env python3
"""
簡化版 AAT 測試
"""

import sys
from pathlib import Path

# 添加路徑
PROJECTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECTS_DIR / "skill-analyzer" / "src"))

# 測試導入
try:
    from analyzer import SkillAnalyzer
    print("✅ SkillAnalyzer 導入成功")
    
    # 測試功能
    analyzer = SkillAnalyzer()
    print("✅ SkillAnalyzer 初始化成功")
    
    # 測試分析
    test_skills = [
        {'name': 'test-skill-1', 'category': 'automation', 'version': '1.0.0', 'size': 1000, 'path': '/path/1'},
        {'name': 'test-skill-2', 'category': 'automation', 'version': '1.0.0', 'size': 2000, 'path': '/path/2'},
        {'name': 'test-skill-3', 'category': 'data', 'version': 'unknown', 'size': 500, 'path': '/path/3'},
    ]
    
    result = analyzer.analyze(test_skills)
    print(f"✅ 分析完成: {result['total_skills']} 個技能")
    print(f"✅ 分類: {list(result['categories'].keys())}")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()

print("\n🧪 測試完成!")
