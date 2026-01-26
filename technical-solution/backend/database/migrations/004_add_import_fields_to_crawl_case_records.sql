-- 为 crawl_case_records 表添加导入相关字段
-- 创建时间：2026-01-18
-- 说明：添加已导入、导入状态、已验证三列，用于追踪案例的导入和验证状态

-- ============================================================
-- 添加导入相关字段
-- ============================================================

ALTER TABLE crawl_case_records
ADD COLUMN IF NOT EXISTS imported BOOLEAN DEFAULT FALSE, -- 已导入：是否已执行过导入动作
ADD COLUMN IF NOT EXISTS import_status VARCHAR(32), -- 导入状态：success（成功）或 failed（失败）
ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT FALSE; -- 已验证：在案例库中可以匹配到对应的案例

-- ============================================================
-- 添加约束和注释
-- ============================================================

-- 添加导入状态约束（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'valid_import_status' 
        AND conrelid = 'crawl_case_records'::regclass
    ) THEN
        ALTER TABLE crawl_case_records
        ADD CONSTRAINT valid_import_status 
        CHECK (import_status IS NULL OR import_status IN ('success', 'failed'));
    END IF;
END $$;

-- 添加注释
COMMENT ON COLUMN crawl_case_records.imported IS '已导入：是否已执行过导入动作';
COMMENT ON COLUMN crawl_case_records.import_status IS '导入状态：success（成功）或 failed（失败）';
COMMENT ON COLUMN crawl_case_records.verified IS '已验证：在案例库中可以匹配到对应的案例（通过 case_id 匹配）';

-- ============================================================
-- 创建索引
-- ============================================================

-- 导入状态索引（用于查询导入状态）
CREATE INDEX IF NOT EXISTS idx_crawl_case_records_imported ON crawl_case_records(imported);
CREATE INDEX IF NOT EXISTS idx_crawl_case_records_import_status ON crawl_case_records(import_status);
CREATE INDEX IF NOT EXISTS idx_crawl_case_records_verified ON crawl_case_records(verified);

-- 组合索引（用于查询已导入但未验证的案例）
CREATE INDEX IF NOT EXISTS idx_crawl_case_records_imported_verified ON crawl_case_records(imported, verified);
