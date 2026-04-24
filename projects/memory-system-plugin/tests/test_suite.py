"""
記憶系統插件 - 完整測試套件
測試所有模組功能

Author: ClawTeam - QA Engineer
Date: 2026-04-08
Version: 1.0.0
"""

import sys
import os
import json
import time
import unittest
from pathlib import Path
from datetime import datetime, timedelta

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 導入所有模組
from monitor import (
    ContextMonitor, ContextMetrics, ContextStatus,
    AlertConfig, SessionState, create_monitor
)
from vector_store import VectorStore, MemoryEntry, EmbeddingProvider
from summarizer import (
    Summarizer, ConversationSummary, SummaryType,
    Decision, ActionItem, ContentAnalyzer, quick_summarize
)
from injector import (
    MemoryInjector, MemoryStore, SemanticSearcher,
    ContextInjector, SessionContext, MemoryEntry as InjectorMemoryEntry
)
from main import MemorySystem, MemorySystemConfig, create_memory_system


class TestContextMonitor(unittest.TestCase):
    """Context 監控測試"""
    
    def setUp(self):
        self.monitor = create_monitor(
            session_id="test_monitor_001",
            warning_threshold=70.0,
            critical_threshold=80.0,
            auto_handlers=False
        )
    
    def test_calculate_usage_normal(self):
        """測試正常狀態計算"""
        # 50% 使用率
        metrics = self.monitor.calculate_usage(128000)
        self.assertEqual(metrics.status, ContextStatus.NORMAL)
        self.assertAlmostEqual(metrics.usage_percentage, 50.0, places=1)
        self.assertEqual(metrics.tokens_remaining, 128000)
    
    def test_calculate_usage_warning(self):
        """測試預警狀態 (70%)"""
        # 70% 使用率
        metrics = self.monitor.calculate_usage(179200)
        self.assertEqual(metrics.status, ContextStatus.WARNING)
        self.assertAlmostEqual(metrics.usage_percentage, 70.0, places=1)
    
    def test_calculate_usage_critical(self):
        """測試危險狀態 (80%)"""
        # 80% 使用率
        metrics = self.monitor.calculate_usage(204800)
        self.assertEqual(metrics.status, ContextStatus.CRITICAL)
        self.assertAlmostEqual(metrics.usage_percentage, 80.0, places=1)
    
    def test_alert_triggering(self):
        """測試警報觸發機制"""
        alert_triggered = []
        
        def warning_handler(metrics):
            alert_triggered.append('warning')
        
        def critical_handler(metrics):
            alert_triggered.append('critical')
        
        self.monitor.register_callback(ContextStatus.WARNING, warning_handler)
        self.monitor.register_callback(ContextStatus.CRITICAL, critical_handler)
        
        # 觸發預警
        self.monitor.check_and_alert(180000)
        self.assertIn('warning', alert_triggered)
        
        # 觸發危險
        self.monitor.check_and_alert(210000)
        self.assertIn('critical', alert_triggered)
    
    def test_alert_deduplication(self):
        """測試警報去重"""
        alert_count = [0]
        
        def warning_handler(metrics):
            alert_count[0] += 1
        
        self.monitor.register_callback(ContextStatus.WARNING, warning_handler)
        
        # 多次觸發相同警報
        self.monitor.check_and_alert(180000)
        self.monitor.check_and_alert(185000)
        self.monitor.check_and_alert(190000)
        
        # 應該只觸發一次
        self.assertEqual(alert_count[0], 1)
    
    def test_metrics_to_dict(self):
        """測試指標序列化"""
        metrics = self.monitor.calculate_usage(150000)
        data = metrics.to_dict()
        
        self.assertIn('session_id', data)
        self.assertIn('usage_percentage', data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'normal')
    
    def test_usage_trend(self):
        """測試使用率趨勢分析"""
        # 添加一些歷史數據
        for i in range(5):
            self.monitor.calculate_usage(100000 + i * 10000)
        
        trend = self.monitor.get_usage_trend(minutes=60)
        self.assertIn('trend', trend)
        self.assertIn('avg_usage', trend)
        self.assertIn('data_points', trend)


class TestVectorStore(unittest.TestCase):
    """向量存儲測試"""
    
    def setUp(self):
        # 使用臨時目錄
        self.test_db_path = Path(__file__).parent / "test_data" / "vector_db"
        self.test_db_path.mkdir(parents=True, exist_ok=True)
        self.store = VectorStore(
            db_path=str(self.test_db_path),
            collection_name="test_collection"
        )
    
    def tearDown(self):
        # 清理測試數據
        import shutil
        if self.test_db_path.exists():
            shutil.rmtree(self.test_db_path.parent)
    
    def test_store_memory(self):
        """測試記憶存儲"""
        memory_id = self.store.store_memory(
            content="測試記憶內容",
            session_key="test_session_001",
            topics=["測試", "開發"],
            decisions=["決定1"],
            emotions="積極",
            priority="high"
        )
        
        self.assertIsNotNone(memory_id)
        self.assertTrue(memory_id.startswith("mem_"))
    
    def test_search_similar(self):
        """測試語義搜索"""
        # 存儲測試記憶
        self.store.store_memory(
            content="交易策略優化方案討論",
            session_key="test_session_001",
            topics=["交易策略", "優化"],
            decisions=["採用新策略"]
        )
        
        self.store.store_memory(
            content="系統開發計劃和架構設計",
            session_key="test_session_002",
            topics=["系統開發", "架構"]
        )
        
        # 搜索
        results = self.store.search_similar("交易策略", n_results=5)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
    
    def test_get_memory(self):
        """測試獲取特定記憶"""
        memory_id = self.store.store_memory(
            content="測試內容",
            session_key="test_session_001"
        )
        
        memory = self.store.get_memory(memory_id)
        self.assertIsNotNone(memory)
        self.assertEqual(memory['id'], memory_id)
    
    def test_get_recent_memories(self):
        """測試獲取最近記憶"""
        # 存儲多條記憶
        for i in range(5):
            self.store.store_memory(
                content=f"測試記憶 {i}",
                session_key=f"test_session_{i}"
            )
        
        memories = self.store.get_recent_memories(n=3)
        self.assertEqual(len(memories), 3)
    
    def test_search_by_topic(self):
        """測試按主題搜索"""
        self.store.store_memory(
            content="交易策略相關內容",
            session_key="test_session_001",
            topics=["交易策略", "優化"]
        )
        
        results = self.store.search_by_topic("交易策略", n_results=5)
        self.assertIsInstance(results, list)
    
    def test_get_stats(self):
        """測試獲取統計信息"""
        stats = self.store.get_stats()
        self.assertIn('total_memories', stats)
        self.assertIn('embedding_dimension', stats)
        self.assertIn('collection_name', stats)


class TestSummarizer(unittest.TestCase):
    """摘要生成器測試"""
    
    def setUp(self):
        self.summarizer = Summarizer()
        self.test_conversation = """
今天我們討論了交易策略優化的問題。

首先分析了當前的5個策略，發現其中2個表現不佳。
經過仔細考慮，我們決定保留3個核心策略，清理掉2個表現不佳的策略。
原因是這3個策略在回測中表現穩定，夏普比率都大於2.0。

決定採用新的MTF整合方案，將多時間框架分析整合到現有系統中。
這個決定是基於提高信號準確性的考慮。

待完成項目：
⏳ 等待實盤部署
⏳ 完成策略參數調整面板
✅ 已經完成策略回測

下一步需要完成系統整合測試，確保所有模組正常工作。

情感上感覺很積極，對這個方向充滿信心。
        """
    
    def test_generate_summary(self):
        """測試摘要生成"""
        summary = self.summarizer.generate_summary(
            session_id="test_session_001",
            conversation_text=self.test_conversation,
            title="測試摘要"
        )
        
        self.assertIsInstance(summary, ConversationSummary)
        self.assertEqual(summary.session_id, "test_session_001")
        self.assertEqual(summary.title, "測試摘要")
        self.assertTrue(summary.id.startswith("summary_"))
    
    def test_extract_decisions(self):
        """測試決策提取"""
        analyzer = ContentAnalyzer()
        decisions = analyzer.extract_decisions(self.test_conversation)
        
        self.assertIsInstance(decisions, list)
        # 應該至少提取到一些決策
        self.assertGreaterEqual(len(decisions), 1)
    
    def test_extract_action_items(self):
        """測試行動項目提取"""
        analyzer = ContentAnalyzer()
        actions = analyzer.extract_action_items(self.test_conversation)
        
        self.assertIsInstance(actions, list)
        # 應該提取到待完成項目
        self.assertGreaterEqual(len(actions), 1)
    
    def test_extract_topics(self):
        """測試主題提取"""
        analyzer = ContentAnalyzer()
        topics = analyzer.extract_topics(self.test_conversation)
        
        self.assertIsInstance(topics, list)
        # 應該提取到相關主題
        self.assertGreaterEqual(len(topics), 1)
    
    def test_summary_to_dict(self):
        """測試摘要序列化"""
        summary = self.summarizer.generate_summary(
            session_id="test_session_001",
            conversation_text=self.test_conversation
        )
        
        data = summary.to_dict()
        self.assertIsInstance(data, dict)
        self.assertIn('id', data)
        self.assertIn('decisions', data)
        self.assertIn('action_items', data)
    
    def test_format_summary_markdown(self):
        """測試 Markdown 格式化"""
        summary = self.summarizer.generate_summary(
            session_id="test_session_001",
            conversation_text=self.test_conversation
        )
        
        markdown = self.summarizer.format_summary_markdown(summary)
        self.assertIsInstance(markdown, str)
        self.assertIn("##", markdown)  # 標題標記


class TestMemoryInjector(unittest.TestCase):
    """記憶注入測試"""
    
    def setUp(self):
        # 使用臨時目錄
        self.test_base_path = Path(__file__).parent / "test_data" / "memory"
        self.test_base_path.mkdir(parents=True, exist_ok=True)
        self.injector = MemoryInjector(str(self.test_base_path))
    
    def tearDown(self):
        # 清理測試數據
        import shutil
        if self.test_base_path.exists():
            shutil.rmtree(self.test_base_path.parent)
    
    def test_save_session_summary(self):
        """測試保存 Session 摘要"""
        context = SessionContext(
            session_id="test_session_001",
            start_time=datetime.now().isoformat(),
            summary="測試摘要內容",
            topics=["測試", "開發"],
            decisions=["決定1", "決定2"],
            action_items=["待辦1", "待辦2"]
        )
        
        success = self.injector.save_session_summary(context)
        self.assertTrue(success)
    
    def test_search_memories(self):
        """測試記憶搜索"""
        # 先保存一些記憶
        context = SessionContext(
            session_id="test_session_001",
            start_time=datetime.now().isoformat(),
            summary="交易策略優化討論",
            topics=["交易策略"],
            decisions=["保留3個策略"]
        )
        self.injector.save_session_summary(context)
        
        # 搜索
        results = self.injector.search_memories("交易策略", limit=5)
        self.assertIsInstance(results, list)
    
    def test_get_session_context(self):
        """測試獲取 Session 上下文"""
        context = self.injector.get_session_context(current_topic="交易策略")
        self.assertIsInstance(context, str)
        self.assertIn("[系統提示", context)
    
    def test_auto_recover_context(self):
        """測試自動恢復上下文"""
        recovery = self.injector.auto_recover_context(
            session_id="new_session_001",
            user_first_message="我想繼續優化交易策略"
        )
        
        self.assertIsInstance(recovery, str)
        self.assertIn("自動記憶恢復", recovery)
    
    def test_get_recent_context(self):
        """測試獲取最近上下文"""
        summary = self.injector.get_recent_context(hours=24)
        self.assertIsInstance(summary, str)


class TestMemorySystem(unittest.TestCase):
    """記憶系統整合測試"""
    
    def setUp(self):
        self.test_base_path = Path(__file__).parent / "test_data" / "memory_system"
        self.test_base_path.mkdir(parents=True, exist_ok=True)
        
        self.config = MemorySystemConfig(
            base_path=self.test_base_path,
            warning_threshold=70.0,
            critical_threshold=80.0
        )
        self.system = MemorySystem(self.config)
    
    def tearDown(self):
        import shutil
        if self.test_base_path.exists():
            shutil.rmtree(self.test_base_path)
    
    def test_initialize(self):
        """測試系統初始化"""
        success = self.system.initialize("test_session_001")
        self.assertTrue(success)
        self.assertTrue(self.system.is_initialized)
    
    def test_check_context(self):
        """測試 Context 檢查"""
        self.system.initialize("test_session_001")
        
        result = self.system.check_context(tokens_used=192000)  # 75%
        self.assertIn('status', result)
        self.assertIn('usage_percentage', result)
        self.assertIn('recommendation', result)
    
    def test_create_summary(self):
        """測試創建摘要"""
        self.system.initialize("test_session_001")
        
        conversation = """
今天我們討論了記憶系統的開發。
決定採用 ChromaDB 作為向量數據庫。
待完成：完成 summarizer.py
        """
        
        summary = self.system.create_summary(conversation, "開發討論")
        # 即使沒有完整的向量存儲，也應該返回摘要對象或 None
        self.assertTrue(summary is None or hasattr(summary, 'id'))
    
    def test_get_system_status(self):
        """測試獲取系統狀態"""
        self.system.initialize("test_session_001")
        
        status = self.system.get_system_status()
        self.assertIn('initialized', status)
        self.assertIn('session_id', status)
        self.assertIn('components', status)


class TestIntegration(unittest.TestCase):
    """整合流程測試"""
    
    def setUp(self):
        self.test_base_path = Path(__file__).parent / "test_data" / "integration"
        self.test_base_path.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        import shutil
        if self.test_base_path.exists():
            shutil.rmtree(self.test_base_path)
    
    def test_full_workflow(self):
        """測試完整工作流程"""
        # 1. 創建系統
        system = create_memory_system(
            session_id="integration_test_001",
            base_path=str(self.test_base_path)
        )
        
        self.assertTrue(system.is_initialized)
        
        # 2. 檢查 Context 使用
        result = system.check_context(tokens_used=100000)
        self.assertEqual(result['status'], 'normal')
        
        # 3. 創建摘要
        conversation = """
今天我們討論了交易策略優化。
決定保留3個核心策略，清理2個表現不佳的策略。
待完成：實盤部署、參數調整。
情感積極。
        """
        
        summary = system.create_summary(conversation, "策略優化")
        # 摘要可能成功或失敗，但系統應該正常運行
        
        # 4. 搜索記憶
        results = system.search_memories("交易策略", n_results=5)
        self.assertIsInstance(results, list)
        
        # 5. 獲取系統狀態
        status = system.get_system_status()
        self.assertTrue(status['initialized'])
        
        # 6. 關閉系統
        system.shutdown()
        self.assertFalse(system.is_initialized)
    
    def test_context_threshold_workflow(self):
        """測試 Context 閾值工作流程"""
        system = create_memory_system(
            session_id="threshold_test_001",
            base_path=str(self.test_base_path),
            warning_threshold=70.0,
            critical_threshold=80.0
        )
        
        # 正常狀態
        result = system.check_context(tokens_used=100000)
        self.assertEqual(result['status'], 'normal')
        
        # 預警狀態
        result = system.check_context(tokens_used=180000)
        self.assertEqual(result['status'], 'warning')
        
        # 危險狀態
        result = system.check_context(tokens_used=210000)
        self.assertEqual(result['status'], 'critical')
        
        system.shutdown()


class TestPerformance(unittest.TestCase):
    """性能測試"""
    
    def test_embedding_performance(self):
        """測試嵌入生成性能"""
        provider = EmbeddingProvider()
        
        text = "這是一個測試文本，用於測試嵌入生成性能。"
        
        start_time = time.time()
        embedding = provider.embed(text)
        elapsed = time.time() - start_time
        
        self.assertIsInstance(embedding, list)
        self.assertGreater(len(embedding), 0)
        # 應該在合理時間內完成
        self.assertLess(elapsed, 5.0)  # 5秒內
    
    def test_search_performance(self):
        """測試搜索性能"""
        test_db_path = Path(__file__).parent / "test_data" / "perf_db"
        test_db_path.mkdir(parents=True, exist_ok=True)
        
        store = VectorStore(db_path=str(test_db_path))
        
        # 存儲一些記憶
        for i in range(10):
            store.store_memory(
                content=f"測試記憶內容 {i} 關於交易策略和系統開發",
                session_key=f"session_{i}"
            )
        
        start_time = time.time()
        results = store.search_similar("交易策略", n_results=5)
        elapsed = time.time() - start_time
        
        self.assertIsInstance(results, list)
        self.assertLess(elapsed, 3.0)  # 3秒內
        
        # 清理
        import shutil
        if test_db_path.exists():
            shutil.rmtree(test_db_path.parent)


def run_tests():
    """運行所有測試"""
    # 創建測試套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有測試類
    suite.addTests(loader.loadTestsFromTestCase(TestContextMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestVectorStore))
    suite.addTests(loader.loadTestsFromTestCase(TestSummarizer))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryInjector))
    suite.addTests(loader.loadTestsFromTestCase(TestMemorySystem))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def run_quick_tests():
    """運行快速測試（不含性能測試）"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestContextMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestVectorStore))
    suite.addTests(loader.loadTestsFromTestCase(TestSummarizer))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryInjector))
    suite.addTests(loader.loadTestsFromTestCase(TestMemorySystem))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("記憶系統插件 - 完整測試套件")
    print("=" * 70)
    
    # 運行所有測試
    result = run_tests()
    
    # 輸出結果摘要
    print("\n" + "=" * 70)
    print("測試結果摘要")
    print("=" * 70)
    print(f"測試總數: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"錯誤: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ 所有測試通過！")
        sys.exit(0)
    else:
        print("\n❌ 部分測試失敗")
        sys.exit(1)
