-- 爬取任务管理功能数据库迁移脚本
-- 创建时间：2024-01-XX
-- 说明：创建爬取任务相关的表结构

-- ============================================================
-- 1. 创建任务表（crawl_tasks）
-- ============================================================

CREATE TABLE IF NOT EXISTS crawl_tasks (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    data_source VARCHAR(64) NOT NULL,
    description TEXT,

    -- 任务配置
    start_page INTEGER NOT NULL,
    end_page INTEGER,
    case_type INTEGER,
    search_value VARCHAR(255),
    batch_size INTEGER DEFAULT 100,
    delay_min FLOAT DEFAULT 2.0,
    delay_max FLOAT DEFAULT 5.0,
    enable_resume BOOLEAN DEFAULT TRUE,

    -- 任务状态
    status VARCHAR(32) NOT NULL DEFAULT 'pending', -- pending, running, paused, completed, failed, cancelled, terminated
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    paused_at TIMESTAMP WITH TIME ZONE,

    -- 进度信息
    total_pages INTEGER,
    completed_pages INTEGER DEFAULT 0,
    current_page INTEGER,

    -- 统计信息
    total_crawled INTEGER DEFAULT 0,
    total_saved INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,
    batches_saved INTEGER DEFAULT 0,

    -- 性能指标
    avg_speed FLOAT, -- 平均爬取速度（案例/分钟）
    avg_delay FLOAT, -- 平均请求延迟（秒）
    error_rate FLOAT, -- 错误率

    -- 错误信息
    error_message TEXT,
    error_stack TEXT,

    -- 元数据
    created_by VARCHAR(64),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'paused', 'completed', 'failed', 'cancelled', 'terminated')),
    CONSTRAINT valid_pages CHECK (start_page >= 0 AND (end_page IS NULL OR end_page >= start_page)),
    CONSTRAINT valid_batch_size CHECK (batch_size > 0),
    CONSTRAINT valid_delay CHECK (delay_min >= 0 AND delay_max >= delay_min)
);

-- ============================================================
-- 2. 创建任务日志表（crawl_task_logs）
-- ============================================================

CREATE TABLE IF NOT EXISTS crawl_task_logs (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    level VARCHAR(16) NOT NULL, -- INFO, WARNING, ERROR
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES crawl_tasks(task_id) ON DELETE CASCADE,
    CONSTRAINT valid_level CHECK (level IN ('INFO', 'WARNING', 'ERROR', 'DEBUG'))
);

-- ============================================================
-- 3. 创建任务状态历史表（crawl_task_status_history）
-- ============================================================

CREATE TABLE IF NOT EXISTS crawl_task_status_history (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    previous_status VARCHAR(32),
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES crawl_tasks(task_id) ON DELETE CASCADE,
    CONSTRAINT valid_status_history CHECK (status IN ('pending', 'running', 'paused', 'completed', 'failed', 'cancelled', 'terminated'))
);

-- ============================================================
-- 4. 创建索引
-- ============================================================

-- crawl_tasks 表索引
CREATE INDEX IF NOT EXISTS idx_crawl_tasks_status ON crawl_tasks(status);
CREATE INDEX IF NOT EXISTS idx_crawl_tasks_created_at ON crawl_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_tasks_data_source ON crawl_tasks(data_source);
CREATE INDEX IF NOT EXISTS idx_crawl_tasks_task_id ON crawl_tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_crawl_tasks_started_at ON crawl_tasks(started_at DESC);

-- crawl_task_logs 表索引
CREATE INDEX IF NOT EXISTS idx_crawl_task_logs_task_id ON crawl_task_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_crawl_task_logs_level ON crawl_task_logs(level);
CREATE INDEX IF NOT EXISTS idx_crawl_task_logs_created_at ON crawl_task_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_task_logs_task_level ON crawl_task_logs(task_id, level);

-- crawl_task_status_history 表索引
CREATE INDEX IF NOT EXISTS idx_crawl_task_status_history_task_id ON crawl_task_status_history(task_id);
CREATE INDEX IF NOT EXISTS idx_crawl_task_status_history_created_at ON crawl_task_status_history(created_at DESC);

-- ============================================================
-- 5. 创建触发器函数（自动更新 updated_at）
-- ============================================================

CREATE OR REPLACE FUNCTION update_crawl_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_crawl_tasks_updated_at
    BEFORE UPDATE ON crawl_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_crawl_tasks_updated_at();

-- ============================================================
-- 6. 创建触发器函数（记录状态变更历史）
-- ============================================================

CREATE OR REPLACE FUNCTION record_crawl_task_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO crawl_task_status_history (task_id, status, previous_status, reason)
        VALUES (NEW.task_id, NEW.status, OLD.status, NULL);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_record_crawl_task_status_change
    AFTER UPDATE OF status ON crawl_tasks
    FOR EACH ROW
    EXECUTE FUNCTION record_crawl_task_status_change();
