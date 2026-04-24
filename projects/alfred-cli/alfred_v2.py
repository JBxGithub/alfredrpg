#!/usr/bin/env python3
"""
Alfred CLI v2 - 修正版
統一入口點，直接使用各工具模塊
"""

import sys
import os
from pathlib import Path
from typing import Optional
import argparse

# 添加所有項目到路徑
PROJECTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECTS_DIR / "skill-analyzer" / "src"))
sys.path.insert(0, str(PROJECTS_DIR / "smart-router" / "src"))
sys.path.insert(0, str(PROJECTS_DIR / "performance-dashboard" / "src"))
sys.path.insert(0, str(PROJECTS_DIR / "snippets-pro" / "src"))
sys.path.insert(0, str(PROJECTS_DIR / "workflow-designer" / "src"))
sys.path.insert(0, str(PROJECTS_DIR / "skill-dev-assistant" / "src"))


def cmd_analyze_skills(args):
    """分析技能生態"""
    try:
        from analyzer import SkillAnalyzer
        from scanner import SkillScanner
        from reporter import SkillReporter
        
        print("🔍 掃描技能目錄...")
        scanner = SkillScanner()
        skills = scanner.scan()
        
        if not skills:
            print("⚠️ 未找到技能")
            return
        
        print(f"✅ 找到 {len(skills)} 個技能")
        
        print("📊 分析技能數據...")
        analyzer = SkillAnalyzer()
        result = analyzer.analyze(skills)
        
        print("\n📈 分析結果:")
        print(f"  總技能數: {result['total_skills']}")
        print(f"  分類數量: {len(result['categories'])}")
        
        for category, skill_list in result['categories'].items():
            print(f"\n  📁 {category}: {len(skill_list)} 個")
            for skill in skill_list[:3]:  # 只顯示前3個
                print(f"    - {skill}")
            if len(skill_list) > 3:
                print(f"    ... 還有 {len(skill_list) - 3} 個")
        
        # 保存報告
        reporter = SkillReporter()
        md_path, json_path = reporter.save_report(result)
        print(f"\n💾 報告已保存:")
        print(f"  Markdown: {md_path}")
        print(f"  JSON: {json_path}")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


def cmd_dashboard_show(args):
    """顯示績效儀表板"""
    try:
        from dashboard import PerformanceDashboard
        
        print("📊 生成績效報告...")
        dashboard = PerformanceDashboard()
        
        # 模擬數據（實際應從數據庫讀取）
        report = dashboard.generate_report(period=args.period)
        
        print(f"\n📈 {args.period} 報告:")
        print(f"  任務完成: {report.get('tasks_completed', 0)}")
        print(f"  成功率: {report.get('success_rate', 0):.1%}")
        print(f"  平均響應時間: {report.get('avg_response_time', 0):.2f}s")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")


def cmd_snippet_search(args):
    """搜索代碼片段"""
    try:
        from snippets_manager import SnippetsManager
        
        print(f"🔍 搜索: {args.keyword}")
        manager = SnippetsManager()
        results = manager.search(args.keyword)
        
        if not results:
            print("⚠️ 未找到相關片段")
            return
        
        print(f"\n✅ 找到 {len(results)} 個片段:")
        for i, snippet in enumerate(results[:5], 1):
            print(f"\n  {i}. {snippet.get('title', 'Untitled')}")
            print(f"     語言: {snippet.get('language', 'unknown')}")
            print(f"     描述: {snippet.get('description', 'N/A')[:50]}...")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")


def cmd_route(args):
    """智能路由推薦"""
    try:
        from router import SmartRouter
        
        print(f"🧭 路由查詢: {args.query}")
        router = SmartRouter()
        results = router.find_best_skills(args.query, top_n=args.top)
        
        if not results:
            print("⚠️ 未找到匹配技能")
            return
        
        print(f"\n✅ 找到 {len(results)} 個推薦技能:")
        for i, skill in enumerate(results, 1):
            print(f"\n  {i}. {skill['name']} (匹配度: {skill['score']})")
            print(f"     分類: {skill['category']}")
            print(f"     描述: {skill['description']}")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


def cmd_workflow_list(args):
    """列出工作流"""
    try:
        from executor import WorkflowExecutor
        
        print("📋 工作流列表:")
        executor = WorkflowExecutor()
        workflows = executor.list_workflows()
        
        if not workflows:
            print("⚠️ 未找到工作流")
            return
        
        for wf in workflows:
            print(f"  - {wf}")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")


def cmd_workflow_run(args):
    """執行工作流"""
    try:
        from executor import WorkflowExecutor
        
        executor = WorkflowExecutor()
        result = executor.execute(args.name)
        
        if result['success']:
            print(f"\n✅ 工作流執行完成: {result['steps_completed']}/{result['total_steps']} 步驟")
        else:
            print(f"\n❌ 工作流執行失敗")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


def cmd_dev_create(args):
    """創建新技能"""
    try:
        from skill_generator import SkillGenerator
        
        print(f"🔨 創建技能: {args.name}")
        generator = SkillGenerator()
        path = generator.create(args.name, category=args.category)
        
        print(f"✅ 技能已創建: {path}")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")


def main():
    parser = argparse.ArgumentParser(
        prog='alfred',
        description='Alfred AI Assistant Ecosystem CLI v2',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # analyze 命令
    analyze_parser = subparsers.add_parser('analyze', help='分析工具')
    analyze_sub = analyze_parser.add_subparsers(dest='subcommand')
    analyze_skills = analyze_sub.add_parser('skills', help='分析技能生態')
    analyze_skills.set_defaults(func=cmd_analyze_skills)
    
    # dashboard 命令
    dashboard_parser = subparsers.add_parser('dashboard', help='績效儀表板')
    dashboard_sub = dashboard_parser.add_subparsers(dest='subcommand')
    dashboard_show = dashboard_sub.add_parser('show', help='顯示儀表板')
    dashboard_show.add_argument('--period', '-p', choices=['day', 'week', 'month'], default='week')
    dashboard_show.set_defaults(func=cmd_dashboard_show)
    
    # snippet 命令
    snippet_parser = subparsers.add_parser('snippet', help='代碼片段')
    snippet_sub = snippet_parser.add_subparsers(dest='subcommand')
    snippet_search = snippet_sub.add_parser('search', help='搜索片段')
    snippet_search.add_argument('keyword', help='搜索關鍵字')
    snippet_search.set_defaults(func=cmd_snippet_search)
    
    # route 命令
    route_parser = subparsers.add_parser('route', help='智能路由')
    route_parser.add_argument('query', help='查詢文本')
    route_parser.add_argument('--top', '-n', type=int, default=3, help='返回前 N 個結果')
    route_parser.set_defaults(func=cmd_route)
    
    # workflow 命令
    workflow_parser = subparsers.add_parser('workflow', help='工作流')
    workflow_sub = workflow_parser.add_subparsers(dest='subcommand')
    
    workflow_list = workflow_sub.add_parser('list', help='列出工作流')
    workflow_list.set_defaults(func=cmd_workflow_list)
    
    workflow_run = workflow_sub.add_parser('run', help='執行工作流')
    workflow_run.add_argument('name', help='工作流名稱')
    workflow_run.set_defaults(func=cmd_workflow_run)
    
    # dev 命令
    dev_parser = subparsers.add_parser('dev', help='開發工具')
    dev_sub = dev_parser.add_subparsers(dest='subcommand')
    dev_create = dev_sub.add_parser('create', help='創建技能')
    dev_create.add_argument('name', help='技能名稱')
    dev_create.add_argument('--category', '-c', default='general', help='技能分類')
    dev_create.set_defaults(func=cmd_dev_create)
    
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
