-- 爬取任务优化功能数据库迁移脚本
-- 创建时间：2024-01-XX
-- 说明：创建列表页爬取记录表和案例爬取记录表，用于精确追踪爬取状态和实现精确重试

-- ============================================================
-- 1. 创建列表页爬取记录表（crawl_list_pages）
-- ============================================================

CREATE TABLE IF NOT EXISTS crawl_list_pages (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    page_number INTEGER NOT NULL,
    
    -- 爬取状态
    status VARCHAR(32) NOT NULL, -- success, failed, skipped, pending
    error_message TEXT,
    error_type VARCHAR(64), -- network_error, parse_error, api_error, timeout_error
    
    -- 爬取结果
    items_count INTEGER DEFAULT 0, -- 获取到的案例数量
    crawled_at TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT, -- 爬取耗时（秒）
    
    -- 重试信息
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (task_id) REFERENCES crawl_tasks(task_id) ON DELETE CASCADE,
    CONSTRAINT valid_status CHECK (status IN ('success', 'failed', 'skipped', 'pending')),
    CONSTRAINT unique_task_page UNIQUE (task_id, page_number)
);

-- ============================================================
-- 2. 创建案例爬取记录表（crawl_case_records）
-- ============================================================

CREATE TABLE IF NOT EXISTS crawl_case_records (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    list_page_id BIGINT, -- 关联到 crawl_list_pages.id
    
    -- 案例标识
    case_id INTEGER, -- 原始案例ID
    case_url TEXT,
    case_title VARCHAR(500),
    
    -- 爬取状态
    status VARCHAR(32) NOT NULL, -- success, failed, skipped, validation_failed, pending
    error_message TEXT,
    error_type VARCHAR(64), -- network_error, parse_error, validation_error, timeout_error
    error_stack TEXT, -- 详细错误堆栈
    
    -- 爬取结果
    crawled_at TIMESTAMP WITH TIME ZONE,
    duration_seconds FLOAT, -- 爬取耗时（秒）
    
    -- 数据质量
    has_detail_data BOOLEAN DEFAULT FALSE, -- 是否成功获取详情页数据
    has_validation_error BOOLEAN DEFAULT FALSE, -- 是否有验证错误
    validation_errors JSONB, -- 验证错误详情
    
    -- 保存状态
    saved_to_json BOOLEAN DEFAULT FALSE, -- 是否已保存到JSON文件
    batch_file_name VARCHAR(255), -- 保存到的批次文件名
    
    -- 重试信息
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (task_id) REFERENCES crawl_tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (list_page_id) REFERENCES crawl_list_pages(id) ON DELETE SET NULL,
    CONSTRAINT valid_status CHECK (status IN ('success', 'failed', 'skipped', 'validation_failed', 'pending')),
    CONSTRAINT unique_task_case UNIQUE (task_id, case_id)
);

-- ============================================================
-- 3. 创建索引
-- ============================================================

-- crawl_list_pages 表索引
CREATE INDEX IF NOT EXISTS idx_crawl_list_pages_task_id ON crawl_list_pages(task_id);
CREATE INDEX IF NOT EXISTS idx_crawl_list_pages_status ON crawl_list_pages(status);
CREATE INDEX IF NOT EXISTS idx_crawl_list_pages_task_status ON crawl_list_pages(task_id, status);

-- crawl_case_records 表索引
CREATE INDEX IF NOT EXISTS idx_crawl_case_records_task_id ON crawl_case_records(task_id);
CREATE INDEX IF NOT EXISTS idx_crawl_case_records_list_page_id ON crawl_case_records(list_page_id);
CREATE INDEX IF NOT EXISTS idx_crawl_case_records_status ON crawl_case_records(status);
CREATE INDEX IF NOT EXISTS idx_crawl_case_records_task_status ON crawl_case_records(task_id, status);
CREATE INDEX IF NOT EXISTS idx_crawl_case_records_case_id ON crawl_case_records(case_id);

-- ============================================================
-- 4. 创建触发器函数（自动更新 updated_at）
-- ============================================================

-- crawl_list_pages 表的 updated_at 触发器
CREATE OR REPLACE FUNCTION update_crawl_list_pages_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_crawl_list_pages_updated_at
    BEFORE UPDATE ON crawl_list_pages
    FOR EACH ROW
    EXECUTE FUNCTION update_crawl_list_pages_updated_at();

-- crawl_case_records 表的 updated_at 触发器
CREATE OR REPLACE FUNCTION update_crawl_case_records_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_crawl_case_records_updated_at
    BEFORE UPDATE ON crawl_case_records
    FOR EACH ROW
    EXECUTE FUNCTION update_crawl_case_records_updated_at();
