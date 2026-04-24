#!/usr/bin/env python3
"""
AMS CLI - Alfred Memory System 命令行工具

使用方式:
    python -m alfred_memory_system.cli [command] [options]
    
    或安裝後:
    ams [command] [options]
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

# 添加父目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alfred_memory_system import AMS, AMSConfig
from alfred_memory_system.core import ContextMonitor


def cmd_init(args):
    """初始化 AMS 系統"""
    ams = AMS()
    ams.initialize()
    return 0


def cmd_reset(args):
    """重置 AMS 系統"""
    if input("⚠️  This will delete all data. Are you sure? (yes/no): ").lower() != 'yes':
        print("Cancelled.")
        return 1
    
    ams = AMS()
    ams.reset()
    return 0


def cmd_status(args):
    """顯示系統狀態"""
    ams = AMS()
    ams.status()
    return 0


def cmd_context(args):
    """顯示 Context 監控報告"""
    monitor = ContextMonitor()
    print(monitor.generate_report(args.session))
    return 0


def cmd_memory_list(args):
    """列出記憶"""
    ams = AMS()
    memories = ams.db.list_memories(category=args.category, limit=args.limit)
    
    print(f"\n🧠 Memories (showing {len(memories)}):")
    print("-" * 60)
    
    for mem in memories:
        print(f"\n📌 [{mem['category']}] {mem['id'][:8]}")
        print(f"   Content: {mem['content'][:80]}...")
        print(f"   Confidence: {mem['confidence']:.2f} | Accessed: {mem['access_count']} times")
        print(f"   Created: {mem['created_at']}")
    
    return 0


def cmd_memory_add(args):
    """添加記憶"""
    import uuid
    
    ams = AMS()
    memory_id = str(uuid.uuid4())[:8]
    
    success = ams.db.add_memory(
        memory_id=memory_id,
        content=args.content,
        category=args.category,
        confidence=args.confidence or 1.0,
        tags=args.tags.split(',') if args.tags else None
    )
    
    if success:
        print(f"✅ Memory added: {memory_id}")
    else:
        print("❌ Failed to add memory")
    
    return 0 if success else 1


def cmd_memory_search(args):
    """搜索記憶"""
    ams = AMS()
    results = ams.db.search_memories(args.query, limit=args.limit)
    
    print(f"\n🔍 Search results for '{args.query}' ({len(results)} found):")
    print("-" * 60)
    
    for mem in results:
        print(f"\n📌 [{mem['category']}] {mem['id'][:8]}")
        print(f"   Content: {mem['content'][:100]}...")
        print(f"   Confidence: {mem['confidence']:.2f}")
    
    return 0


def cmd_skill_list(args):
    """列出 Skills"""
    ams = AMS()
    skills = ams.db.list_skills(auto_created_only=args.auto_only)
    
    print(f"\n🛠️  Skills (showing {len(skills)}):")
    print("-" * 60)
    
    for skill in skills:
        auto_tag = " [AUTO]" if skill['auto_created'] else ""
        print(f"\n🔧 {skill['name']}{auto_tag}")
        print(f"   Description: {skill['description'][:60]}...")
        print(f"   Usage: {skill['usage_count']} | Success: {skill['success_count']} | v{skill['version']}")
    
    return 0


def cmd_session_list(args):
    """列出會話"""
    ams = AMS()
    sessions = ams.db.list_sessions(limit=args.limit)
    
    print(f"\n💬 Sessions (showing {len(sessions)}):")
    print("-" * 60)
    
    for sess in sessions:
        print(f"\n📝 {sess['id'][:16]}...")
        print(f"   Platform: {sess['platform']} | Messages: {sess['message_count']}")
        print(f"   Started: {sess['start_time']}")
        if sess.get('summary'):
            print(f"   Summary: {sess['summary'][:60]}...")
    
    return 0


def cmd_learning_list(args):
    """列出學習記錄"""
    ams = AMS()
    learnings = ams.db.list_learnings(
        entry_type=args.type,
        status=args.status,
        limit=args.limit
    )
    
    print(f"\n📚 Learnings (showing {len(learnings)}):")
    print("-" * 60)
    
    for entry in learnings:
        status_icon = "✅" if entry['status'] == 'resolved' else "⏳"
        print(f"\n{status_icon} [{entry['type']}] {entry['id'][:8]}")
        print(f"   Content: {entry['content'][:80]}...")
        print(f"   Category: {entry['category']} | Status: {entry['status']}")
        print(f"   Created: {entry['created_at']}")
    
    return 0


def cmd_learning_add(args):
    """添加學習記錄"""
    import uuid
    
    ams = AMS()
    entry_id = str(uuid.uuid4())[:8]
    
    success = ams.db.add_learning(
        entry_id=entry_id,
        entry_type=args.type,
        content=args.content,
        category=args.category,
        status=args.status
    )
    
    if success:
        print(f"✅ Learning entry added: {entry_id}")
    else:
        print("❌ Failed to add learning entry")
    
    return 0 if success else 1


def cmd_project_list(args):
    """列出專案"""
    ams = AMS()
    projects = ams.db.list_projects(status=args.status, limit=args.limit)
    
    print(f"\n📁 Projects (showing {len(projects)}):")
    print("-" * 60)
    
    for proj in projects:
        status_icon = {
            'active': '🟢',
            'paused': '⏸️',
            'completed': '✅',
            'archived': '📦'
        }.get(proj['status'], '⚪')
        
        print(f"\n{status_icon} {proj['name']}")
        print(f"   Description: {proj.get('description', 'N/A')[:60]}...")
        print(f"   Status: {proj['status']} | Progress: {proj.get('progress_percent', 0)}%")
        print(f"   Priority: {proj.get('priority', 3)} | Updated: {proj['last_updated']}")
    
    return 0


def cmd_project_add(args):
    """添加專案"""
    import uuid
    
    ams = AMS()
    project_id = str(uuid.uuid4())[:8]
    
    success = ams.db.add_project(
        project_id=project_id,
        name=args.name,
        description=args.description,
        path=args.path,
        priority=args.priority
    )
    
    if success:
        print(f"✅ Project added: {args.name} (ID: {project_id})")
    else:
        print("❌ Failed to add project (name may already exist)")
    
    return 0 if success else 1


def cmd_sync(args):
    """同步記憶和專案"""
    from alfred_memory_system.integration import sync_all, sync_projects
    
    print("🔄 Starting sync...")
    
    if args.memory:
        print("\n📚 Syncing memory files...")
        result = sync_all(dry_run=args.dry_run)
        print(f"   Files scanned: {result['files_scanned']}")
        if 'database_sync' in result:
            print(f"   Added: {result['database_sync'].get('added', 0)}")
            print(f"   Skipped: {result['database_sync'].get('skipped', 0)}")
    
    if args.projects:
        print("\n📁 Syncing projects...")
        result = sync_projects(dry_run=args.dry_run)
        print(f"   Projects found: {result['projects_found']}")
        if 'database_sync' in result:
            print(f"   Added: {result['database_sync'].get('added', 0)}")
            print(f"   Updated: {result['database_sync'].get('updated', 0)}")
    
    print("\n✅ Sync completed")
    return 0


def cmd_analyze_task(args):
    """分析任務複雜度"""
    ams = AMS()
    
    steps = args.steps.split(',') if args.steps else []
    errors = args.errors.split(',') if args.errors else []
    
    analysis = ams.learning_engine.analyze_task(
        task_description=args.description,
        steps=steps,
        duration_minutes=args.duration,
        errors_encountered=errors,
        tool_calls_count=args.tool_calls
    )
    
    print("\n📊 Task Analysis:")
    print("-" * 60)
    print(f"Description: {analysis.task_description}")
    print(f"Complexity Score: {analysis.complexity_score}/100")
    print(f"Should Create Skill: {'Yes' if analysis.should_create_skill else 'No'}")
    
    if analysis.reasons:
        print("\nReasons:")
        for reason in analysis.reasons:
            print(f"   - {reason}")
    
    if analysis.should_create_skill and not args.dry_run:
        print("\n🛠️  Auto-creating skill...")
        skill = ams.learning_engine.auto_create_skill(analysis)
        if skill:
            print(f"✅ Skill created: {skill['name']}")
        else:
            print("❌ Failed to create skill")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Alfred Memory System (AMS) CLI v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    ams init                          # Initialize AMS
    ams status                        # Show system status
    ams context                       # Show context report
    
    # Memory Management
    ams memory list                   # List all memories
    ams memory add "User prefers dark mode" --category preference
    ams memory search "TradingBot"    # Search memories
    
    # Skill Management
    ams skill list                    # List skills
    
    # Session Management
    ams session list                  # List sessions
    
    # Learning Management
    ams learning list                 # List learning entries
    ams learning add "Fix for timeout issue" --type error
    
    # Project Management
    ams project list                  # List projects
    ams project add "TradingBot" --description "Automated trading system"
    
    # Sync
    ams sync --memory --projects      # Sync all
    ams sync --memory --dry-run       # Preview memory sync
    
    # Task Analysis
    ams analyze "Deploy system" --steps "step1,step2,step3" --duration 15 --tool-calls 8
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # init
    init_parser = subparsers.add_parser('init', help='Initialize AMS system')
    
    # reset
    reset_parser = subparsers.add_parser('reset', help='Reset AMS system (delete all data)')
    
    # status
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # context
    context_parser = subparsers.add_parser('context', help='Show context monitoring report')
    context_parser.add_argument('--session', '-s', help='Session ID')
    
    # memory
    memory_parser = subparsers.add_parser('memory', help='Memory management')
    memory_subparsers = memory_parser.add_subparsers(dest='memory_command')
    
    memory_list_parser = memory_subparsers.add_parser('list', help='List memories')
    memory_list_parser.add_argument('--category', '-c', help='Filter by category')
    memory_list_parser.add_argument('--limit', '-l', type=int, default=20, help='Limit results')
    
    memory_add_parser = memory_subparsers.add_parser('add', help='Add memory')
    memory_add_parser.add_argument('content', help='Memory content')
    memory_add_parser.add_argument('--category', '-c', default='general', help='Category')
    memory_add_parser.add_argument('--confidence', type=float, help='Confidence (0-1)')
    memory_add_parser.add_argument('--tags', '-t', help='Tags (comma-separated)')
    
    memory_search_parser = memory_subparsers.add_parser('search', help='Search memories')
    memory_search_parser.add_argument('query', help='Search query')
    memory_search_parser.add_argument('--limit', '-l', type=int, default=10, help='Limit results')
    
    # skill
    skill_parser = subparsers.add_parser('skill', help='Skill management')
    skill_subparsers = skill_parser.add_subparsers(dest='skill_command')
    
    skill_list_parser = skill_subparsers.add_parser('list', help='List skills')
    skill_list_parser.add_argument('--auto-only', action='store_true', help='Show only auto-created skills')
    
    # session
    session_parser = subparsers.add_parser('session', help='Session management')
    session_subparsers = session_parser.add_subparsers(dest='session_command')
    
    session_list_parser = session_subparsers.add_parser('list', help='List sessions')
    session_list_parser.add_argument('--limit', '-l', type=int, default=20, help='Limit results')
    
    # learning
    learning_parser = subparsers.add_parser('learning', help='Learning entries management')
    learning_subparsers = learning_parser.add_subparsers(dest='learning_command')
    
    learning_list_parser = learning_subparsers.add_parser('list', help='List learning entries')
    learning_list_parser.add_argument('--type', '-t', help='Filter by type')
    learning_list_parser.add_argument('--status', '-s', help='Filter by status')
    learning_list_parser.add_argument('--limit', '-l', type=int, default=20, help='Limit results')
    
    learning_add_parser = learning_subparsers.add_parser('add', help='Add learning entry')
    learning_add_parser.add_argument('content', help='Entry content')
    learning_add_parser.add_argument('--type', '-t', default='improvement', help='Entry type')
    learning_add_parser.add_argument('--category', '-c', default='general', help='Category')
    learning_add_parser.add_argument('--status', '-s', default='pending', help='Status')
    
    # project
    project_parser = subparsers.add_parser('project', help='Project management')
    project_subparsers = project_parser.add_subparsers(dest='project_command')
    
    project_list_parser = project_subparsers.add_parser('list', help='List projects')
    project_list_parser.add_argument('--status', '-s', help='Filter by status')
    project_list_parser.add_argument('--limit', '-l', type=int, default=20, help='Limit results')
    
    project_add_parser = project_subparsers.add_parser('add', help='Add project')
    project_add_parser.add_argument('name', help='Project name')
    project_add_parser.add_argument('--description', '-d', default='', help='Description')
    project_add_parser.add_argument('--path', '-p', help='Project path')
    project_add_parser.add_argument('--priority', type=int, default=3, help='Priority (1-5)')
    
    # sync
    sync_parser = subparsers.add_parser('sync', help='Sync memory and projects')
    sync_parser.add_argument('--memory', '-m', action='store_true', help='Sync memory files')
    sync_parser.add_argument('--projects', '-p', action='store_true', help='Sync projects')
    sync_parser.add_argument('--dry-run', '-n', action='store_true', help='Preview only')
    
    # analyze
    analyze_parser = subparsers.add_parser('analyze', help='Analyze task complexity')
    analyze_parser.add_argument('description', help='Task description')
    analyze_parser.add_argument('--steps', '-s', help='Steps (comma-separated)')
    analyze_parser.add_argument('--duration', '-d', type=float, default=0, help='Duration in minutes')
    analyze_parser.add_argument('--errors', '-e', help='Errors encountered (comma-separated)')
    analyze_parser.add_argument('--tool-calls', '-t', type=int, default=0, help='Tool calls count')
    analyze_parser.add_argument('--dry-run', '-n', action='store_true', help='Analyze only, do not create skill')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command
    try:
        if args.command == 'init':
            return cmd_init(args)
        elif args.command == 'reset':
            return cmd_reset(args)
        elif args.command == 'status':
            return cmd_status(args)
        elif args.command == 'context':
            return cmd_context(args)
        elif args.command == 'memory':
            if args.memory_command == 'list':
                return cmd_memory_list(args)
            elif args.memory_command == 'add':
                return cmd_memory_add(args)
            elif args.memory_command == 'search':
                return cmd_memory_search(args)
            else:
                memory_parser.print_help()
                return 1
        elif args.command == 'skill':
            if args.skill_command == 'list':
                return cmd_skill_list(args)
            else:
                skill_parser.print_help()
                return 1
        elif args.command == 'session':
            if args.session_command == 'list':
                return cmd_session_list(args)
            else:
                session_parser.print_help()
                return 1
        elif args.command == 'learning':
            if args.learning_command == 'list':
                return cmd_learning_list(args)
            elif args.learning_command == 'add':
                return cmd_learning_add(args)
            else:
                learning_parser.print_help()
                return 1
        elif args.command == 'project':
            if args.project_command == 'list':
                return cmd_project_list(args)
            elif args.project_command == 'add':
                return cmd_project_add(args)
            else:
                project_parser.print_help()
                return 1
        elif args.command == 'sync':
            return cmd_sync(args)
        elif args.command == 'analyze':
            return cmd_analyze_task(args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
