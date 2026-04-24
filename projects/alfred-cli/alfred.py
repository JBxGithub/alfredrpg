#!/usr/bin/env python3
"""
Alfred CLI - 統一入口點
整合所有 AI 助理工具的生態系統

Author: 呀鬼 (Alfred)
Version: 1.0.0
Date: 2026-04-11
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

# 動態導入，處理模塊路徑
try:
    from analyzer import SkillAnalyzer
except ImportError:
    SkillAnalyzer = None

try:
    from skill_db import SkillDB
except ImportError:
    SkillDB = None

try:
    from metrics import PerformanceDashboard
except ImportError:
    PerformanceDashboard = None

try:
    from storage import SnippetsManager
except ImportError:
    SnippetsManager = None

try:
    from parser import WorkflowParser
    from executor import WorkflowExecutor
except ImportError:
    WorkflowParser = None
    WorkflowExecutor = None


class AlfredCLI:
    """Alfred 統一 CLI 入口"""
    
    def __init__(self):
        self.analyzer = SkillAnalyzer()
        self.router = SmartRouter()
        self.dashboard = PerformanceDashboard()
        self.snippets = SnippetsManager()
        self.workflows = WorkflowDesigner()
    
    def main(self):
        parser = argparse.ArgumentParser(
            prog='alfred',
            description='Alfred AI Assistant Ecosystem CLI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  alfred analyze skills                    # 分析技能生態
  alfred route "check trading status"      # 智能路由推薦
  alfred dashboard show                    # 顯示績效儀表板
  alfred snippet search "error handling"   # 搜索代碼片段
  alfred workflow run morning-routine      # 執行工作流
  alfred dev create my-skill               # 創建新技能
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='可用命令')
        
        # === analyze 命令 ===
        analyze_parser = subparsers.add_parser('analyze', help='分析工具')
        analyze_sub = analyze_parser.add_subparsers(dest='analyze_cmd')
        
        analyze_skills = analyze_sub.add_parser('skills', help='分析技能生態')
        analyze_skills.add_argument('--output', '-o', default='reports/skill-analysis.md')
        analyze_skills.add_argument('--format', choices=['md', 'json'], default='md')
        
        # === route 命令 ===
        route_parser = subparsers.add_parser('route', help='智能路由')
        route_parser.add_argument('query', help='查詢文本')
        route_parser.add_argument('--top', '-n', type=int, default=3, help='返回前 N 個結果')
        
        # === dashboard 命令 ===
        dashboard_parser = subparsers.add_parser('dashboard', help='績效儀表板')
        dashboard_sub = dashboard_parser.add_subparsers(dest='dashboard_cmd')
        
        dashboard_show = dashboard_sub.add_parser('show', help='顯示儀表板')
        dashboard_show.add_argument('--period', '-p', choices=['day', 'week', 'month'], default='week')
        dashboard_show.add_argument('--output', '-o', help='輸出到文件')
        
        dashboard_trend = dashboard_sub.add_parser('trend', help='顯示趨勢')
        dashboard_trend.add_argument('metric', choices=['tasks', 'success_rate', 'completion_time'])
        
        # === snippet 命令 ===
        snippet_parser = subparsers.add_parser('snippet', help='代碼片段管理')
        snippet_sub = snippet_parser.add_subparsers(dest='snippet_cmd')
        
        snippet_add = snippet_sub.add_parser('add', help='添加片段')
        snippet_add.add_argument('title', help='片段標題')
        snippet_add.add_argument('--lang', '-l', default='python', help='語言')
        snippet_add.add_argument('--tags', '-t', help='標籤（逗號分隔）')
        
        snippet_search = snippet_sub.add_parser('search', help='搜索片段')
        snippet_search.add_argument('query', help='搜索關鍵字')
        snippet_search.add_argument('--lang', '-l', help='過濾語言')
        snippet_search.add_argument('--insert', '-i', action='store_true', help='插入到剪貼簿')
        
        snippet_list = snippet_sub.add_parser('list', help='列出片段')
        snippet_list.add_argument('--lang', '-l', help='過濾語言')
        
        # === workflow 命令 ===
        workflow_parser = subparsers.add_parser('workflow', help='工作流管理')
        workflow_sub = workflow_parser.add_subparsers(dest='workflow_cmd')
        
        workflow_list = workflow_sub.add_parser('list', help='列出工作流')
        workflow_run = workflow_sub.add_parser('run', help='執行工作流')
        workflow_run.add_argument('name', help='工作流名稱')
        workflow_validate = workflow_sub.add_parser('validate', help='驗證工作流')
        workflow_validate.add_argument('file', help='YAML 文件路徑')
        
        # === dev 命令 ===
        dev_parser = subparsers.add_parser('dev', help='開發工具')
        dev_sub = dev_parser.add_subparsers(dest='dev_cmd')
        
        dev_create = dev_sub.add_parser('create', help='創建技能')
        dev_create.add_argument('name', help='技能名稱')
        dev_create.add_argument('--category', '-c', default='automation', help='分類')
        dev_create.add_argument('--description', '-d', help='描述')
        
        dev_validate = dev_sub.add_parser('validate', help='驗證技能')
        dev_validate.add_argument('path', help='技能路徑')
        
        # === status 命令 ===
        status_parser = subparsers.add_parser('status', help='顯示系統狀態')
        
        # 解析參數
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        # 執行對應命令
        self._execute_command(args)
    
    def _execute_command(self, args):
        """執行具體命令"""
        
        # === analyze 命令 ===
        if args.command == 'analyze':
            if args.analyze_cmd == 'skills':
                print("🔍 正在分析技能生態...")
                result = self.analyzer.analyze_all()
                if args.format == 'md':
                    self.analyzer.generate_markdown_report(result, args.output)
                else:
                    self.analyzer.generate_json_report(result, args.output)
                print(f"✅ 報告已生成: {args.output}")
        
        # === route 命令 ===
        elif args.command == 'route':
            print(f"🧭 正在為查詢尋找最佳技能: '{args.query}'")
            results = self.router.find_best_skills(args.query, top_n=args.top)
            print(f"\n找到 {len(results)} 個推薦技能:")
            for i, skill in enumerate(results, 1):
                print(f"\n{i}. {skill['name']}")
                print(f"   置信度: {skill['confidence']:.1%}")
                print(f"   原因: {skill['reason']}")
        
        # === dashboard 命令 ===
        elif args.command == 'dashboard':
            if args.dashboard_cmd == 'show':
                print("📊 生成績效儀表板...")
                report = self.dashboard.generate_report(period=args.period)
                if args.output:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(report)
                    print(f"✅ 報告已保存: {args.output}")
                else:
                    print(report)
            elif args.dashboard_cmd == 'trend':
                print(f"📈 生成 {args.metric} 趨勢...")
                trend = self.dashboard.get_trend(args.metric)
                self._print_trend_chart(trend)
        
        # === snippet 命令 ===
        elif args.command == 'snippet':
            if args.snippet_cmd == 'add':
                print(f"📝 添加代碼片段: {args.title}")
                snippet_id = self.snippets.add_snippet(
                    title=args.title,
                    language=args.lang,
                    tags=args.tags.split(',') if args.tags else []
                )
                print(f"✅ 片段已添加，ID: {snippet_id}")
            
            elif args.snippet_cmd == 'search':
                print(f"🔎 搜索: {args.query}")
                results = self.snippets.search(
                    query=args.query,
                    language=args.lang
                )
                if not results:
                    print("❌ 未找到匹配片段")
                    return
                
                print(f"\n找到 {len(results)} 個結果:")
                for i, s in enumerate(results, 1):
                    print(f"\n{i}. {s['title']} ({s['language']})")
                    print(f"   標籤: {', '.join(s['tags'])}")
                    if args.insert and i == 1:
                        self._copy_to_clipboard(s['code'])
                        print("   📋 已複製到剪貼簿")
            
            elif args.snippet_cmd == 'list':
                snippets = self.snippets.list_all(language=args.lang)
                print(f"📚 共有 {len(snippets)} 個片段:")
                for s in snippets:
                    print(f"  • {s['title']} ({s['language']})")
        
        # === workflow 命令 ===
        elif args.command == 'workflow':
            if args.workflow_cmd == 'list':
                workflows = self.workflows.list_all()
                print("📋 可用工作流:")
                for w in workflows:
                    print(f"  • {w['name']}: {w['description']}")
            
            elif args.workflow_cmd == 'run':
                print(f"🚀 執行工作流: {args.name}")
                result = self.workflows.run(args.name)
                if result['success']:
                    print(f"✅ 工作流執行成功 ({result['duration']:.1f}s)")
                else:
                    print(f"❌ 工作流執行失敗: {result['error']}")
            
            elif args.workflow_cmd == 'validate':
                print(f"🔍 驗證工作流: {args.file}")
                is_valid = self.workflows.validate(args.file)
                if is_valid:
                    print("✅ 工作流格式正確")
                else:
                    print("❌ 工作流格式錯誤")
        
        # === dev 命令 ===
        elif args.command == 'dev':
            if args.dev_cmd == 'create':
                print(f"🏗️  創建技能: {args.name}")
                skill_path = self._create_skill(
                    name=args.name,
                    category=args.category,
                    description=args.description
                )
                print(f"✅ 技能已創建: {skill_path}")
            
            elif args.dev_cmd == 'validate':
                print(f"🔍 驗證技能: {args.path}")
                result = self._validate_skill(args.path)
                if result['valid']:
                    print("✅ 技能驗證通過")
                else:
                    print("❌ 技能驗證失敗:")
                    for error in result['errors']:
                        print(f"   - {error}")
        
        # === status 命令 ===
        elif args.command == 'status':
            self._show_status()
    
    def _print_trend_chart(self, trend_data):
        """打印 ASCII 趨勢圖"""
        if not trend_data:
            print("無數據")
            return
        
        max_val = max(d['value'] for d in trend_data)
        min_val = min(d['value'] for d in trend_data)
        
        print("\n趨勢圖:")
        for d in trend_data:
            bar_len = int((d['value'] - min_val) / (max_val - min_val + 1) * 30)
            bar = "█" * bar_len
            print(f"{d['date']}: {bar} {d['value']:.1f}")
    
    def _copy_to_clipboard(self, text: str):
        """複製文本到剪貼簿"""
        try:
            import pyperclip
            pyperclip.copy(text)
        except ImportError:
            # Windows 備選方案
            import subprocess
            subprocess.run(['clip'], input=text.encode('utf-8'), check=True)
    
    def _create_skill(self, name: str, category: str, description: Optional[str]) -> str:
        """創建新技能"""
        from dev_assistant import SkillGenerator
        generator = SkillGenerator()
        return generator.create(name, category, description)
    
    def _validate_skill(self, path: str) -> dict:
        """驗證技能"""
        from dev_assistant import SkillValidator
        validator = SkillValidator()
        return validator.validate(path)
    
    def _show_status(self):
        """顯示系統狀態"""
        print("🤖 Alfred AI Ecosystem Status")
        print("=" * 50)
        
        # 技能統計
        skill_count = self.analyzer.get_skill_count()
        print(f"📦 已安裝技能: {skill_count}")
        
        # 片段統計
        snippet_count = self.snippets.count()
        print(f"📝 代碼片段: {snippet_count}")
        
        # 工作流統計
        workflow_count = len(self.workflows.list_all())
        print(f"⚙️  工作流: {workflow_count}")
        
        # 績效摘要
        perf = self.dashboard.get_summary()
        print(f"📊 本週任務: {perf['total_tasks']}")
        print(f"✅ 成功率: {perf['success_rate']:.1%}")
        
        print("=" * 50)


def main():
    """CLI 入口點"""
    cli = AlfredCLI()
    cli.main()


if __name__ == '__main__':
    main()
