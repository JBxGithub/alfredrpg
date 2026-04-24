#!/usr/bin/env python3
"""
Hermes CLI - PowerShell-style command line interface
Windows-optimized CLI for Hermes Memory System
"""

import argparse
import sys
import os
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.memory_manager import MemoryManager
from core.session_store import SessionStore
from core.skill_manager import SkillManager
from core.learning_engine import LearningEngine
from utils.windows_scheduler import WindowsScheduler

import yaml


class HermesCLI:
    """Hermes 命令行界面"""
    
    def __init__(self):
        self.config = self._load_config()
        self.memory = None
        self.sessions = None
        self.skills = None
        self.learning = None
        self.scheduler = None
    
    def _load_config(self):
        """加載配置"""
        config_path = Path.home() / "openclaw_workspace" / "projects" / "hermes-memory-system" / "config" / "hermes_config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _init_components(self):
        """初始化組件"""
        if self.memory is None:
            self.memory = MemoryManager()
        if self.sessions is None:
            db_path = os.path.expandvars(self.config['paths']['database_file'])
            self.sessions = SessionStore(db_path)
        if self.skills is None:
            skills_dir = os.path.expandvars(self.config['paths']['skills_dir'])
            self.skills = SkillManager(skills_dir)
        if self.learning is None:
            self.learning = LearningEngine(self.config, self.memory, self.sessions, self.skills)
        if self.scheduler is None:
            self.scheduler = WindowsScheduler(self.config)
    
    def cmd_memory(self, args):
        """記憶管理命令"""
        self._init_components()
        
        if args.action == 'add':
            success, msg = self.memory.add(args.content, args.category, args.target)
            print(msg)
        
        elif args.action == 'search':
            results = self.memory.search(args.query, args.target)
            for r in results:
                print(f"[{r['source']}] {r['content']}")
        
        elif args.action == 'stats':
            stats = self.memory.get_stats()
            print(f"MEMORY.md: {stats['memory']['current']}/{stats['memory']['max']} ({stats['memory']['usage_percent']}%)")
            print(f"USER.md: {stats['user']['current']}/{stats['user']['max']} ({stats['user']['usage_percent']}%)")
        
        elif args.action == 'remove':
            success, msg = self.memory.remove(args.pattern, args.target)
            print(msg)
    
    def cmd_session(self, args):
        """會話管理命令"""
        self._init_components()
        
        if args.action == 'search':
            results = self.sessions.search(args.query, args.limit)
            for r in results:
                print(f"[{r['session_title']}] {r['content'][:100]}...")
        
        elif args.action == 'list':
            sessions = self.sessions.get_recent_sessions(args.limit)
            for s in sessions:
                print(f"{s.session_id[:8]}... - {s.title or 'Untitled'} ({s.message_count} messages)")
        
        elif args.action == 'stats':
            stats = self.sessions.get_stats()
            print(f"Total sessions: {stats['total_sessions']}")
            print(f"Total messages: {stats['total_messages']}")
            print(f"Today: {stats['today_messages']} messages")
    
    def cmd_skill(self, args):
        """技能管理命令"""
        self._init_components()
        
        if args.action == 'list':
            skills = self.skills.list_skills(args.category)
            for s in skills:
                print(f"{s['name']} - {s['description'][:60]}...")
        
        elif args.action == 'create':
            skill = self.skills.create_skill(
                args.name, args.description, args.content,
                args.category, args.tags.split(',') if args.tags else []
            )
            print(f"Created skill: {skill.name}")
        
        elif args.action == 'search':
            results = self.skills.search_skills(args.query)
            for r in results:
                print(f"{r['name']} ({r['category']})")
    
    def cmd_nudge(self, args):
        """提醒管理命令"""
        self._init_components()
        
        if args.action == 'setup':
            success = self.scheduler.create_nudge_task(args.time, args.frequency)
            if success:
                print(f"Nudge task created: {args.frequency} at {args.time}")
            else:
                print("Failed to create nudge task")
        
        elif args.action == 'list':
            tasks = self.scheduler.list_tasks()
            for t in tasks:
                print(f"{t['name']} - Next: {t['next_run']} - {t['status']}")
        
        elif args.action == 'now':
            nudge = self.learning.generate_nudge()
            if nudge:
                print(f"[{nudge['type']}] {nudge['title']}")
                print(nudge['content'])
                print(f"Action: {nudge['action']}")
            else:
                print("No nudge needed at this time.")
    
    def cmd_stats(self, args):
        """統計命令"""
        self._init_components()
        
        print("=== Hermes Memory System Stats ===")
        print()
        
        # 記憶統計
        mem_stats = self.memory.get_stats()
        print("Memory:")
        print(f"  MEMORY.md: {mem_stats['memory']['usage_percent']}% full")
        print(f"  USER.md: {mem_stats['user']['usage_percent']}% full")
        print()
        
        # 會話統計
        sess_stats = self.sessions.get_stats()
        print("Sessions:")
        print(f"  Total: {sess_stats['total_sessions']}")
        print(f"  Messages: {sess_stats['total_messages']}")
        print()
        
        # 技能統計
        skill_stats = self.skills.get_skill_stats()
        print("Skills:")
        print(f"  Total: {skill_stats['total_skills']}")
        print(f"  Categories: {', '.join(skill_stats['by_category'].keys())}")
        print()
        
        # 學習統計
        learning_stats = self.learning.get_learning_stats()
        print("Learning:")
        print(f"  Tasks analyzed: {learning_stats['tasks_analyzed']}")
        print(f"  Auto-created skills: {learning_stats['skills_auto_created']}")


def main():
    """主入口"""
    cli = HermesCLI()
    
    parser = argparse.ArgumentParser(description='Hermes Memory System CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Memory 命令
    mem_parser = subparsers.add_parser('memory', help='Memory management')
    mem_parser.add_argument('action', choices=['add', 'search', 'stats', 'remove'])
    mem_parser.add_argument('--content', '-c', help='Content to add')
    mem_parser.add_argument('--query', '-q', help='Search query')
    mem_parser.add_argument('--pattern', '-p', help='Pattern to remove')
    mem_parser.add_argument('--category', default='general')
    mem_parser.add_argument('--target', default='memory', choices=['memory', 'user'])
    mem_parser.set_defaults(func=cli.cmd_memory)
    
    # Session 命令
    sess_parser = subparsers.add_parser('session', help='Session management')
    sess_parser.add_argument('action', choices=['search', 'list', 'stats'])
    sess_parser.add_argument('--query', '-q')
    sess_parser.add_argument('--limit', '-l', type=int, default=10)
    sess_parser.set_defaults(func=cli.cmd_session)
    
    # Skill 命令
    skill_parser = subparsers.add_parser('skill', help='Skill management')
    skill_parser.add_argument('action', choices=['list', 'create', 'search'])
    skill_parser.add_argument('--name', '-n')
    skill_parser.add_argument('--description', '-d')
    skill_parser.add_argument('--content', '-c')
    skill_parser.add_argument('--category', default='general')
    skill_parser.add_argument('--tags', '-t')
    skill_parser.add_argument('--query', '-q')
    skill_parser.set_defaults(func=cli.cmd_skill)
    
    # Nudge 命令
    nudge_parser = subparsers.add_parser('nudge', help='Nudge management')
    nudge_parser.add_argument('action', choices=['setup', 'list', 'now'])
    nudge_parser.add_argument('--time', default='09:00')
    nudge_parser.add_argument('--frequency', default='daily', choices=['daily', 'weekly', 'hourly'])
    nudge_parser.set_defaults(func=cli.cmd_nudge)
    
    # Stats 命令
    stats_parser = subparsers.add_parser('stats', help='Show all stats')
    stats_parser.set_defaults(func=cli.cmd_stats)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == '__main__':
    main()
