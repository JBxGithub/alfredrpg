"""
AMS Integration Test Suite
Alfred Memory System 整合測試

運行方式:
    python test_ams_integration.py

測試內容:
1. 數據庫 Schema 更新 (learnings, projects 表)
2. Memory Manager 功能
3. Skill Manager 功能
4. Learning Engine 功能
5. Summarizer 功能 (可選)
6. OpenClaw Hook 功能
7. Memory Sync 功能
8. Project Tracker 功能
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 確保可以找到 AMS
sys.path.insert(0, str(Path.home() / "openclaw_workspace"))

try:
    from alfred_memory_system import AMS, AMSConfig
    from alfred_memory_system.core import (
        MemoryManager, SkillManager, LearningEngine, Summarizer
    )
    from alfred_memory_system.integration import (
        OpenClawHook, MemorySync, ProjectTracker
    )
    TEST_IMPORTS = True
except ImportError as e:
    print(f"❌ Import Error: {e}")
    TEST_IMPORTS = False


class TestResult:
    """測試結果"""
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message


class AMSTestSuite:
    """AMS 測試套件"""
    
    def __init__(self):
        self.results = []
        self.temp_dir = None
        self.ams = None
    
    def setup(self):
        """測試前設置"""
        print("="*60)
        print("🧪 AMS Integration Test Suite")
        print("="*60)
        print()
        
        # 創建臨時目錄
        self.temp_dir = tempfile.mkdtemp(prefix="ams_test_")
        print(f"📁 Temp directory: {self.temp_dir}")
        
        # 創建測試配置
        self.config = AMSConfig()
        self.config.storage.db_path = os.path.join(self.temp_dir, "test.db")
        self.config.workspace_path = self.temp_dir
        self.config.skills_path = os.path.join(self.temp_dir, "skills")
        
        # 初始化 AMS
        try:
            self.ams = AMS(self.config)
            self.ams.initialize()
            print("✅ AMS initialized")
        except Exception as e:
            print(f"❌ Failed to initialize AMS: {e}")
            raise
        
        print()
    
    def teardown(self):
        """測試後清理"""
        print()
        print("="*60)
        print("🧹 Cleaning up...")
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"✅ Removed temp directory: {self.temp_dir}")
        
        print("="*60)
    
    def run_test(self, test_name: str, test_func):
        """運行單個測試"""
        try:
            print(f"📝 Testing: {test_name}...", end=" ")
            test_func()
            result = TestResult(test_name, True)
            print("✅ PASS")
        except AssertionError as e:
            result = TestResult(test_name, False, str(e))
            print(f"❌ FAIL: {e}")
        except Exception as e:
            result = TestResult(test_name, False, f"Exception: {e}")
            print(f"❌ ERROR: {e}")
        
        self.results.append(result)
        return result
    
    # ==================== 測試函數 ====================
    
    def test_database_schema(self):
        """測試數據庫 Schema"""
        stats = self.ams.get_stats()
        
        # 檢查新表是否存在
        assert 'total_learnings' in stats, "learnings table not found"
        assert 'total_projects' in stats, "projects table not found"
        
        # 測試 learnings 表
        entry_id = self.ams.db.add_learning(
            entry_id="test001",
            entry_type="error",
            content="Test error content",
            category="test"
        )
        assert entry_id, "Failed to add learning entry"
        
        # 測試 projects 表
        import uuid
        project_id = str(uuid.uuid4())[:8]
        success = self.ams.db.add_project(
            project_id=project_id,
            name="Test Project",
            description="Test description",
            status="active"
        )
        assert success, "Failed to add project"
    
    def test_memory_manager(self):
        """測試 Memory Manager"""
        mm = self.ams.memory_manager
        
        # 測試添加記憶
        success, msg = mm.add("Test memory content", category="test")
        assert success, f"Failed to add memory: {msg}"
        
        # 測試搜索
        results = mm.search("Test")
        assert len(results) > 0, "Search returned no results"
        
        # 測試統計
        stats = mm.get_stats()
        assert 'memory' in stats, "Memory stats not found"
        assert 'user' in stats, "User stats not found"
    
    def test_skill_manager(self):
        """測試 Skill Manager"""
        sm = self.ams.skill_manager
        
        # 測試創建技能
        skill = sm.create_skill(
            name="test-skill",
            description="Test skill description",
            content="# Test Skill\n\nThis is a test.",
            category="test"
        )
        assert skill is not None, "Failed to create skill"
        assert skill.name == "test-skill", "Skill name mismatch"
        
        # 測試獲取技能
        retrieved = sm.get_skill("test-skill")
        assert retrieved is not None, "Failed to retrieve skill"
        
        # 測試列出技能
        skills = sm.list_skills()
        assert len(skills) > 0, "No skills found"
    
    def test_learning_engine(self):
        """測試 Learning Engine"""
        le = self.ams.learning_engine
        
        # 測試任務分析
        analysis = le.analyze_task(
            task_description="Test complex task",
            steps=["step1", "step2", "step3", "step4", "step5"],
            duration_minutes=15,
            errors_encountered=["error1"],
            tool_calls_count=8
        )
        assert analysis is not None, "Analysis failed"
        assert analysis.complexity_score > 0, "Complexity score is 0"
        
        # 測試添加學習記錄
        entry_id = le.add_learning(
            entry_type="improvement",
            content="Test improvement suggestion",
            category="test"
        )
        assert entry_id, "Failed to add learning entry"
        
        # 測試獲取學習記錄
        learnings = le.get_learnings()
        assert len(learnings) > 0, "No learnings found"
    
    def test_summarizer(self):
        """測試 Summarizer（可選功能）"""
        # 創建一個未啟用的 summarizer
        summarizer = Summarizer(enabled=False)
        
        # 測試未啟用時返回 None
        result = summarizer.generate_summary(
            session_id="test",
            conversation_text="Test conversation"
        )
        assert result is None, "Summarizer should return None when disabled"
        
        # 測試啟用的 summarizer
        summarizer_enabled = Summarizer(enabled=True)
        conversation = """
今天我們決定採用新的交易策略。
原因是回測結果顯示夏普比率大於2.0。

待完成：
⏳ 部署到實盤
✅ 完成回測

下一步需要完成系統整合。
"""
        summary = summarizer_enabled.generate_summary(
            session_id="test_session",
            conversation_text=conversation,
            title="測試摘要"
        )
        assert summary is not None, "Failed to generate summary"
        assert summary.title, "Summary has no title"
    
    def test_openclaw_hook(self):
        """測試 OpenClaw Hook"""
        hook = OpenClawHook(enabled=True)
        
        # 測試狀態獲取
        status = hook.get_status()
        assert 'enabled' in status, "Status missing 'enabled'"
        
        # 測試 Context 檢查
        messages = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there!'}
        ]
        result = hook.check_context(messages)
        assert result is not None, "Context check failed"
        assert 'usage_percent' in result, "Result missing usage_percent"
    
    def test_memory_sync(self):
        """測試 Memory Sync"""
        sync = MemorySync(
            workspace_path=self.temp_dir,
            db_manager=self.ams.db
        )
        
        # 測試掃描（應該為空）
        files = sync.scan_memory_files(days=7)
        assert isinstance(files, list), "Scan should return a list"
        
        # 測試統計
        stats = sync.get_memory_stats()
        assert 'memory_dir' in stats, "Stats missing memory_dir"
    
    def test_project_tracker(self):
        """測試 Project Tracker"""
        tracker = ProjectTracker(
            workspace_path=self.temp_dir,
            db_manager=self.ams.db
        )
        
        # 測試掃描（應該為空）
        projects = tracker.scan_project_files()
        assert isinstance(projects, list), "Scan should return a list"
        
        # 測試統計
        stats = tracker.get_stats()
        assert 'total_projects' in stats, "Stats missing total_projects"
    
    def test_ams_status(self):
        """測試 AMS 狀態顯示"""
        # 這個測試主要是確保 status() 不會拋出異常
        try:
            self.ams.status()
        except Exception as e:
            raise AssertionError(f"status() raised exception: {e}")
    
    # ==================== 運行所有測試 ====================
    
    def run_all_tests(self):
        """運行所有測試"""
        if not TEST_IMPORTS:
            print("❌ Cannot run tests due to import errors")
            return False
        
        self.setup()
        
        try:
            # 數據庫測試
            self.run_test("Database Schema (learnings & projects)", self.test_database_schema)
            
            # 核心組件測試
            self.run_test("Memory Manager", self.test_memory_manager)
            self.run_test("Skill Manager", self.test_skill_manager)
            self.run_test("Learning Engine", self.test_learning_engine)
            self.run_test("Summarizer (Optional)", self.test_summarizer)
            
            # 整合模組測試
            self.run_test("OpenClaw Hook", self.test_openclaw_hook)
            self.run_test("Memory Sync", self.test_memory_sync)
            self.run_test("Project Tracker", self.test_project_tracker)
            
            # 整體測試
            self.run_test("AMS Status Display", self.test_ams_status)
        
        finally:
            self.teardown()
        
        # 打印結果摘要
        self.print_summary()
        
        # 返回是否全部通過
        return all(r.passed for r in self.results)
    
    def print_summary(self):
        """打印測試結果摘要"""
        print()
        print("="*60)
        print("📊 Test Results Summary")
        print("="*60)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        
        for result in self.results:
            icon = "✅" if result.passed else "❌"
            print(f"{icon} {result.name}")
            if not result.passed and result.message:
                print(f"   Error: {result.message}")
        
        print()
        print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
        
        if failed == 0:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {failed} test(s) failed")
        
        print("="*60)


def main():
    """主函數"""
    suite = AMSTestSuite()
    success = suite.run_all_tests()
    
    # 返回退出碼
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
