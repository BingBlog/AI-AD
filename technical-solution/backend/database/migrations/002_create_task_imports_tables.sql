-- 数据导入功能数据库迁移脚本
-- 创建时间：2024-01-XX
-- 说明：创建任务导入相关的表结构

-- ============================================================
-- 1. 创建任务导入记录表（task_imports）
-- ============================================================

CREATE TABLE IF NOT EXISTS task_imports (
    id BIGSERIAL PRIMARY KEY,
    import_id VARCHAR(64) UNIQUE NOT NULL,
    task_id VARCHAR(64) NOT NULL,

    -- 导入配置
    import_mode VARCHAR(32) NOT NULL, -- "full" | "selective"
    selected_batches JSONB, -- 选择的批次文件列表（仅当 import_mode="selective" 时使用）
    skip_existing BOOLEAN DEFAULT TRUE,
    update_existing BOOLEAN DEFAULT FALSE,
    generate_vectors BOOLEAN DEFAULT TRUE,
    skip_invalid BOOLEAN DEFAULT TRUE,
    batch_size INTEGER DEFAULT 50,

    -- 导入状态
    status VARCHAR(32) NOT NULL DEFAULT 'pending', -- pending, running, completed, failed, cancelled
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,

    -- 进度信息
    total_cases INTEGER DEFAULT 0,
    loaded_cases INTEGER DEFAULT 0,
    valid_cases INTEGER DEFAULT 0,
    invalid_cases INTEGER DEFAULT 0,
    existing_cases INTEGER DEFAULT 0,
    imported_cases INTEGER DEFAULT 0,
    failed_cases INTEGER DEFAULT 0,
    current_file VARCHAR(255),

    -- 结果信息
    duration_seconds INTEGER,
    error_message TEXT,
    error_stack TEXT,

    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT valid_import_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_import_mode CHECK (import_mode IN ('full', 'selective')),
    CONSTRAINT fk_task_imports_task_id FOREIGN KEY (task_id) REFERENCES crawl_tasks(task_id) ON DELETE CASCADE
);

-- ============================================================
-- 2. 创建任务导入错误记录表（task_import_errors）
-- ============================================================

CREATE TABLE IF NOT EXISTS task_import_errors (
    id BIGSERIAL PRIMARY KEY,
    import_id VARCHAR(64) NOT NULL,
    file_name VARCHAR(255),
    case_id INTEGER,
    error_type VARCHAR(64), -- "validation_error", "database_error", "vector_error"
    error_message TEXT NOT NULL,
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_task_import_errors_import_id FOREIGN KEY (import_id) REFERENCES task_imports(import_id) ON DELETE CASCADE
);

-- ============================================================
-- 3. 创建索引
-- ============================================================

-- task_imports 表索引
CREATE INDEX IF NOT EXISTS idx_task_imports_task_id ON task_imports(task_id);
CREATE INDEX IF NOT EXISTS idx_task_imports_status ON task_imports(status);
CREATE INDEX IF NOT EXISTS idx_task_imports_created_at ON task_imports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_task_imports_import_id ON task_imports(import_id);

-- task_import_errors 表索引
CREATE INDEX IF NOT EXISTS idx_task_import_errors_import_id ON task_import_errors(import_id);
CREATE INDEX IF NOT EXISTS idx_task_import_errors_case_id ON task_import_errors(case_id);
