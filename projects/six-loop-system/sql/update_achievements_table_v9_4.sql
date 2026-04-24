-- 更新 achievements 表以支持 V9.4 功能
-- 運行此腳本更新數據庫表結構

-- 檢查並添加新列
DO $$
BEGIN
    -- 添加盈利減倉 L1 次數列
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='achievements' AND column_name='partial_exits_l1') THEN
        ALTER TABLE achievements ADD COLUMN partial_exits_l1 INTEGER DEFAULT 0;
        RAISE NOTICE 'Added column: partial_exits_l1';
    END IF;
    
    -- 添加盈利減倉 L2 次數列
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='achievements' AND column_name='partial_exits_l2') THEN
        ALTER TABLE achievements ADD COLUMN partial_exits_l2 INTEGER DEFAULT 0;
        RAISE NOTICE 'Added column: partial_exits_l2';
    END IF;
    
    -- 添加 V9.4 評分列
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='achievements' AND column_name='v94_score') THEN
        ALTER TABLE achievements ADD COLUMN v94_score DECIMAL(5,2) DEFAULT 0;
        RAISE NOTICE 'Added column: v94_score';
    END IF;
    
    -- 添加已執行操作列 (用於學習記錄)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='learning_logs' AND column_name='actions_taken') THEN
        ALTER TABLE learning_logs ADD COLUMN actions_taken JSONB DEFAULT '[]'::jsonb;
        RAISE NOTICE 'Added column: actions_taken to learning_logs';
    END IF;
END $$;

-- 創建索引以優化查詢
CREATE INDEX IF NOT EXISTS idx_achievements_v94_score ON achievements(v94_score);
CREATE INDEX IF NOT EXISTS idx_achievements_partial_exits ON achievements(partial_exits_l1, partial_exits_l2);

-- 驗證更新
SELECT 
    column_name, 
    data_type,
    column_default
FROM information_schema.columns 
WHERE table_name = 'achievements' 
AND column_name IN ('partial_exits_l1', 'partial_exits_l2', 'v94_score')
ORDER BY column_name;
