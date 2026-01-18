# 爬取任务数据库表结构分析与映射关系

## 1. 表结构概览

当前爬取任务系统共有 **7 个核心数据表**，分为两个功能模块：

### 1.1 爬取任务模块（5 个表）

- `crawl_tasks` - 爬取任务主表
- `crawl_task_logs` - 任务日志表
- `crawl_task_status_history` - 任务状态历史表
- `crawl_list_pages` - 列表页爬取记录表（新增）
- `crawl_case_records` - 案例爬取记录表（新增）

### 1.2 数据导入模块（2 个表）

- `task_imports` - 任务导入记录表
- `task_import_errors` - 任务导入错误记录表

---

## 2. 详细表结构分析

### 2.1 crawl_tasks（爬取任务主表）

**表用途**：存储爬取任务的核心信息，包括配置、状态、进度和统计信息。

#### 字段分类

| 分类         | 字段名            | 类型                     | 约束                        | 说明                                                                   |
| ------------ | ----------------- | ------------------------ | --------------------------- | ---------------------------------------------------------------------- |
| **主键标识** | `id`              | BIGSERIAL                | PRIMARY KEY                 | 数据库自增主键                                                         |
|              | `task_id`         | VARCHAR(64)              | UNIQUE NOT NULL             | 任务唯一标识，格式：`task_{uuid}`                                      |
| **基本信息** | `name`            | VARCHAR(255)             | NOT NULL                    | 任务名称                                                               |
|              | `data_source`     | VARCHAR(64)              | NOT NULL                    | 数据源标识（如："adquan"）                                             |
|              | `description`     | TEXT                     |                             | 任务描述                                                               |
| **任务配置** | `start_page`      | INTEGER                  | NOT NULL, >= 0              | 起始页码                                                               |
|              | `end_page`        | INTEGER                  | >= start_page               | 结束页码                                                               |
|              | `case_type`       | INTEGER                  |                             | 案例类型筛选                                                           |
|              | `search_value`    | VARCHAR(255)             |                             | 搜索关键词                                                             |
|              | `batch_size`      | INTEGER                  | DEFAULT 100, > 0            | 批次大小（每批保存的案例数）                                           |
|              | `delay_min`       | FLOAT                    | DEFAULT 2.0, >= 0           | 最小请求延迟（秒）                                                     |
|              | `delay_max`       | FLOAT                    | DEFAULT 5.0, >= delay_min   | 最大请求延迟（秒）                                                     |
|              | `enable_resume`   | BOOLEAN                  | DEFAULT TRUE                | 是否启用断点续传                                                       |
| **任务状态** | `status`          | VARCHAR(32)              | NOT NULL, DEFAULT 'pending' | 任务状态：pending/running/paused/completed/failed/cancelled/terminated |
| **时间信息** | `created_at`      | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP   | 创建时间                                                               |
|              | `started_at`      | TIMESTAMP WITH TIME ZONE |                             | 开始执行时间                                                           |
|              | `completed_at`    | TIMESTAMP WITH TIME ZONE |                             | 完成时间                                                               |
|              | `paused_at`       | TIMESTAMP WITH TIME ZONE |                             | 暂停时间                                                               |
|              | `updated_at`      | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP   | 更新时间（触发器自动更新）                                             |
| **进度信息** | `total_pages`     | INTEGER                  |                             | 总页数                                                                 |
|              | `completed_pages` | INTEGER                  | DEFAULT 0                   | 已完成页数                                                             |
|              | `current_page`    | INTEGER                  |                             | 当前页码                                                               |
| **统计信息** | `total_crawled`   | INTEGER                  | DEFAULT 0                   | 总爬取案例数                                                           |
|              | `total_saved`     | INTEGER                  | DEFAULT 0                   | 总保存案例数                                                           |
|              | `total_failed`    | INTEGER                  | DEFAULT 0                   | 总失败案例数                                                           |
|              | `batches_saved`   | INTEGER                  | DEFAULT 0                   | 已保存批次数                                                           |
| **性能指标** | `avg_speed`       | FLOAT                    |                             | 平均爬取速度（案例/分钟）                                              |
|              | `avg_delay`       | FLOAT                    |                             | 平均请求延迟（秒）                                                     |
|              | `error_rate`      | FLOAT                    |                             | 错误率（0-1 之间）                                                     |
| **错误信息** | `error_message`   | TEXT                     |                             | 错误消息                                                               |
|              | `error_stack`     | TEXT                     |                             | 错误堆栈                                                               |
| **元数据**   | `created_by`      | VARCHAR(64)              |                             | 创建者标识                                                             |

#### 状态枚举值说明

- `pending` - 等待中：任务已创建，等待执行
- `running` - 运行中：任务正在执行
- `paused` - 已暂停：任务被暂停，可恢复
- `completed` - 已完成：任务成功完成
- `failed` - 已失败：任务执行失败
- `cancelled` - 已取消：任务被取消（未开始执行）
- `terminated` - 已终止：任务被强制终止（执行中被中断）

#### 索引

- `idx_crawl_tasks_status` - 状态索引（用于查询特定状态的任务）
- `idx_crawl_tasks_created_at` - 创建时间索引（用于排序）
- `idx_crawl_tasks_data_source` - 数据源索引（用于按数据源筛选）
- `idx_crawl_tasks_task_id` - 任务 ID 索引（唯一索引）
- `idx_crawl_tasks_started_at` - 开始时间索引（用于排序）

---

### 2.2 crawl_task_logs（任务日志表）

**表用途**：记录任务执行过程中的详细日志信息，用于问题排查和监控。

#### 字段分类

| 分类         | 字段名       | 类型                     | 约束                                | 说明                               |
| ------------ | ------------ | ------------------------ | ----------------------------------- | ---------------------------------- |
| **主键**     | `id`         | BIGSERIAL                | PRIMARY KEY                         | 数据库自增主键                     |
| **关联**     | `task_id`    | VARCHAR(64)              | NOT NULL, FK → crawl_tasks(task_id) | 任务 ID，外键关联                  |
| **日志内容** | `level`      | VARCHAR(16)              | NOT NULL                            | 日志级别：INFO/WARNING/ERROR/DEBUG |
|              | `message`    | TEXT                     | NOT NULL                            | 日志消息                           |
|              | `details`    | JSONB                    |                                     | 详细信息（JSON 格式）              |
| **时间**     | `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP           | 日志创建时间                       |

#### 日志级别说明

- `INFO` - 信息：正常执行信息
- `WARNING` - 警告：需要注意但不影响执行的问题
- `ERROR` - 错误：执行错误
- `DEBUG` - 调试：调试信息

#### 索引

- `idx_crawl_task_logs_task_id` - 任务 ID 索引
- `idx_crawl_task_logs_level` - 日志级别索引
- `idx_crawl_task_logs_created_at` - 创建时间索引（用于排序）
- `idx_crawl_task_logs_task_level` - 任务 ID+级别联合索引（用于查询特定任务的特定级别日志）

#### 外键关系

- `task_id` → `crawl_tasks(task_id)` ON DELETE CASCADE
  - 删除任务时，自动删除所有相关日志

---

### 2.3 crawl_task_status_history（任务状态历史表）

**表用途**：记录任务状态变更历史，由数据库触发器自动创建，用于审计和追踪。

#### 字段分类

| 分类         | 字段名            | 类型                     | 约束                                | 说明              |
| ------------ | ----------------- | ------------------------ | ----------------------------------- | ----------------- |
| **主键**     | `id`              | BIGSERIAL                | PRIMARY KEY                         | 数据库自增主键    |
| **关联**     | `task_id`         | VARCHAR(64)              | NOT NULL, FK → crawl_tasks(task_id) | 任务 ID，外键关联 |
| **状态信息** | `status`          | VARCHAR(32)              | NOT NULL                            | 新状态            |
|              | `previous_status` | VARCHAR(32)              |                                     | 之前的状态        |
|              | `reason`          | TEXT                     |                                     | 状态变更原因      |
| **时间**     | `created_at`      | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP           | 状态变更时间      |

#### 触发器机制

当 `crawl_tasks.status` 字段更新时，触发器 `trigger_record_crawl_task_status_change` 自动执行：

```sql
CREATE TRIGGER trigger_record_crawl_task_status_change
    AFTER UPDATE OF status ON crawl_tasks
    FOR EACH ROW
    EXECUTE FUNCTION record_crawl_task_status_change();
```

触发器函数会检查状态是否变化，如果变化则自动插入一条历史记录。

#### 索引

- `idx_crawl_task_status_history_task_id` - 任务 ID 索引
- `idx_crawl_task_status_history_created_at` - 创建时间索引（用于排序）

#### 外键关系

- `task_id` → `crawl_tasks(task_id)` ON DELETE CASCADE
  - 删除任务时，自动删除所有相关状态历史

---

### 2.4 task_imports（任务导入记录表）

**表用途**：记录将爬取数据从 JSON 文件导入到数据库的导入任务信息。

#### 字段分类

| 分类         | 字段名             | 类型                     | 约束                                | 说明                                                      |
| ------------ | ------------------ | ------------------------ | ----------------------------------- | --------------------------------------------------------- |
| **主键标识** | `id`               | BIGSERIAL                | PRIMARY KEY                         | 数据库自增主键                                            |
|              | `import_id`        | VARCHAR(64)              | UNIQUE NOT NULL                     | 导入任务唯一标识                                          |
| **关联**     | `task_id`          | VARCHAR(64)              | NOT NULL, FK → crawl_tasks(task_id) | 关联的爬取任务 ID                                         |
| **导入配置** | `import_mode`      | VARCHAR(32)              | NOT NULL                            | 导入模式：full（全部）/selective（选择性）                |
|              | `selected_batches` | JSONB                    |                                     | 选择的批次文件列表（仅当 import_mode="selective" 时使用） |
|              | `skip_existing`    | BOOLEAN                  | DEFAULT TRUE                        | 是否跳过已存在的案例                                      |
|              | `update_existing`  | BOOLEAN                  | DEFAULT FALSE                       | 是否更新已存在的案例                                      |
|              | `generate_vectors` | BOOLEAN                  | DEFAULT TRUE                        | 是否生成向量                                              |
|              | `skip_invalid`     | BOOLEAN                  | DEFAULT TRUE                        | 是否跳过无效案例                                          |
|              | `batch_size`       | INTEGER                  | DEFAULT 50                          | 导入批次大小                                              |
| **导入状态** | `status`           | VARCHAR(32)              | NOT NULL, DEFAULT 'pending'         | 导入状态：pending/running/completed/failed/cancelled      |
| **时间信息** | `started_at`       | TIMESTAMP WITH TIME ZONE |                                     | 开始时间                                                  |
|              | `completed_at`     | TIMESTAMP WITH TIME ZONE |                                     | 完成时间                                                  |
|              | `cancelled_at`     | TIMESTAMP WITH TIME ZONE |                                     | 取消时间                                                  |
|              | `created_at`       | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP           | 创建时间                                                  |
|              | `updated_at`       | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP           | 更新时间                                                  |
| **进度信息** | `total_cases`      | INTEGER                  | DEFAULT 0                           | 总案例数                                                  |
|              | `loaded_cases`     | INTEGER                  | DEFAULT 0                           | 已加载案例数                                              |
|              | `valid_cases`      | INTEGER                  | DEFAULT 0                           | 有效案例数                                                |
|              | `invalid_cases`    | INTEGER                  | DEFAULT 0                           | 无效案例数                                                |
|              | `existing_cases`   | INTEGER                  | DEFAULT 0                           | 已存在案例数                                              |
|              | `imported_cases`   | INTEGER                  | DEFAULT 0                           | 已导入案例数                                              |
|              | `failed_cases`     | INTEGER                  | DEFAULT 0                           | 失败案例数                                                |
|              | `current_file`     | VARCHAR(255)             |                                     | 当前处理的文件                                            |
| **结果信息** | `duration_seconds` | INTEGER                  |                                     | 耗时（秒）                                                |
|              | `error_message`    | TEXT                     |                                     | 错误消息                                                  |
|              | `error_stack`      | TEXT                     |                                     | 错误堆栈                                                  |

#### 导入模式说明

- `full` - 全部导入：导入任务的所有批次文件
- `selective` - 选择性导入：只导入 `selected_batches` 中指定的批次文件

#### 索引

- `idx_task_imports_task_id` - 任务 ID 索引（用于查询任务的导入记录）
- `idx_task_imports_status` - 状态索引（用于查询特定状态的导入任务）
- `idx_task_imports_created_at` - 创建时间索引（用于排序）
- `idx_task_imports_import_id` - 导入 ID 索引（唯一索引）

#### 外键关系

- `task_id` → `crawl_tasks(task_id)` ON DELETE CASCADE
  - 删除爬取任务时，自动删除所有相关导入记录

---

### 2.5 task_import_errors（任务导入错误记录表）

**表用途**：记录导入过程中每个案例的错误详情，用于问题分析和重试。

#### 字段分类

| 分类         | 字段名          | 类型                     | 约束                                   | 说明                                                   |
| ------------ | --------------- | ------------------------ | -------------------------------------- | ------------------------------------------------------ |
| **主键**     | `id`            | BIGSERIAL                | PRIMARY KEY                            | 数据库自增主键                                         |
| **关联**     | `import_id`     | VARCHAR(64)              | NOT NULL, FK → task_imports(import_id) | 导入任务 ID，外键关联                                  |
| **错误信息** | `file_name`     | VARCHAR(255)             |                                        | 出错的批次文件名                                       |
|              | `case_id`       | INTEGER                  |                                        | 出错的案例 ID                                          |
|              | `error_type`    | VARCHAR(64)              |                                        | 错误类型：validation_error/database_error/vector_error |
|              | `error_message` | TEXT                     | NOT NULL                               | 错误消息                                               |
|              | `error_details` | JSONB                    |                                        | 错误详情（JSON 格式）                                  |
| **时间**     | `created_at`    | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP              | 错误记录时间                                           |

#### 错误类型说明

- `validation_error` - 验证错误：案例数据不符合验证规则
- `database_error` - 数据库错误：插入数据库时出错
- `vector_error` - 向量错误：生成向量时出错

#### 索引

- `idx_task_import_errors_import_id` - 导入 ID 索引（用于查询特定导入任务的错误）
- `idx_task_import_errors_case_id` - 案例 ID 索引（用于查询特定案例的错误）

#### 外键关系

- `import_id` → `task_imports(import_id)` ON DELETE CASCADE
  - 删除导入任务时，自动删除所有相关错误记录

---

### 2.6 crawl_list_pages（列表页爬取记录表）

**表用途**：记录每个列表页的爬取结果，用于精确追踪列表页爬取状态和实现精确重试。

#### 字段分类

| 分类           | 字段名             | 类型                     | 约束                                | 说明                                             |
| -------------- | ------------------ | ------------------------ | ----------------------------------- | ------------------------------------------------ |
| **主键**       | `id`               | BIGSERIAL                | PRIMARY KEY                         | 数据库自增主键                                   |
| **关联**       | `task_id`          | VARCHAR(64)              | NOT NULL, FK → crawl_tasks(task_id) | 任务 ID，外键关联                                |
| **列表页标识** | `page_number`      | INTEGER                  | NOT NULL                            | 页码（从 0 开始）                                |
| **爬取状态**   | `status`           | VARCHAR(32)              | NOT NULL                            | 状态：success/failed/skipped/pending             |
| **错误信息**   | `error_message`    | TEXT                     |                                     | 错误消息                                         |
|                | `error_type`       | VARCHAR(64)              |                                     | 错误类型：network_error/parse_error/api_error 等 |
| **爬取结果**   | `items_count`      | INTEGER                  | DEFAULT 0                           | 获取到的案例数量                                 |
|                | `crawled_at`       | TIMESTAMP WITH TIME ZONE |                                     | 爬取时间                                         |
|                | `duration_seconds` | FLOAT                    |                                     | 爬取耗时（秒）                                   |
| **重试信息**   | `retry_count`      | INTEGER                  | DEFAULT 0                           | 重试次数                                         |
|                | `last_retry_at`    | TIMESTAMP WITH TIME ZONE |                                     | 最后重试时间                                     |
| **元数据**     | `created_at`       | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP           | 创建时间                                         |
|                | `updated_at`       | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP           | 更新时间                                         |

#### 状态枚举值说明

- `pending` - 等待中：列表页爬取已开始，等待结果
- `success` - 成功：列表页爬取成功
- `failed` - 失败：列表页爬取失败
- `skipped` - 跳过：列表页被跳过（如已爬取过）

#### 错误类型说明

- `network_error` - 网络错误：网络请求失败
- `parse_error` - 解析错误：响应数据解析失败
- `api_error` - API 错误：API 返回错误状态码
- `timeout_error` - 超时错误：请求超时

#### 索引

- `idx_crawl_list_pages_task_id` - 任务 ID 索引（用于查询任务的列表页记录）
- `idx_crawl_list_pages_status` - 状态索引（用于查询特定状态的列表页）
- `idx_crawl_list_pages_task_status` - 任务 ID+状态联合索引（用于查询任务的失败列表页）

#### 唯一约束

- `unique_task_page` - `(task_id, page_number)` 唯一约束，确保每个任务的每个页码只有一条记录

#### 外键关系

- `task_id` → `crawl_tasks(task_id)` ON DELETE CASCADE
  - 删除任务时，自动删除所有相关列表页记录

---

### 2.7 crawl_case_records（案例爬取记录表）

**表用途**：记录每个案例的爬取结果，用于精确追踪案例爬取状态和实现精确重试。

#### 字段分类

| 分类         | 字段名                 | 类型                     | 约束                                | 说明                                                    |
| ------------ | ---------------------- | ------------------------ | ----------------------------------- | ------------------------------------------------------- |
| **主键**     | `id`                   | BIGSERIAL                | PRIMARY KEY                         | 数据库自增主键                                          |
| **关联**     | `task_id`              | VARCHAR(64)              | NOT NULL, FK → crawl_tasks(task_id) | 任务 ID，外键关联                                       |
|              | `list_page_id`         | BIGINT                   | FK → crawl_list_pages(id)           | 列表页记录 ID，外键关联（可为 NULL）                    |
| **案例标识** | `case_id`              | INTEGER                  |                                     | 原始案例 ID                                             |
|              | `case_url`             | TEXT                     |                                     | 案例 URL                                                |
|              | `case_title`           | VARCHAR(500)             |                                     | 案例标题                                                |
| **爬取状态** | `status`               | VARCHAR(32)              | NOT NULL                            | 状态：success/failed/skipped/validation_failed/pending  |
| **错误信息** | `error_message`        | TEXT                     |                                     | 错误消息                                                |
|              | `error_type`           | VARCHAR(64)              |                                     | 错误类型：network_error/parse_error/validation_error 等 |
|              | `error_stack`          | TEXT                     |                                     | 详细错误堆栈                                            |
| **爬取结果** | `crawled_at`           | TIMESTAMP WITH TIME ZONE |                                     | 爬取时间                                                |
|              | `duration_seconds`     | FLOAT                    |                                     | 爬取耗时（秒）                                          |
| **数据质量** | `has_detail_data`      | BOOLEAN                  | DEFAULT FALSE                       | 是否成功获取详情页数据                                  |
|              | `has_validation_error` | BOOLEAN                  | DEFAULT FALSE                       | 是否有验证错误                                          |
|              | `validation_errors`    | JSONB                    |                                     | 验证错误详情（JSON 格式）                               |
| **保存状态** | `saved_to_json`        | BOOLEAN                  | DEFAULT FALSE                       | 是否已保存到 JSON 文件                                  |
|              | `batch_file_name`      | VARCHAR(255)             |                                     | 保存到的批次文件名                                      |
| **重试信息** | `retry_count`          | INTEGER                  | DEFAULT 0                           | 重试次数                                                |
|              | `last_retry_at`        | TIMESTAMP WITH TIME ZONE |                                     | 最后重试时间                                            |
| **元数据**   | `created_at`           | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP           | 创建时间                                                |
|              | `updated_at`           | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP           | 更新时间                                                |

#### 状态枚举值说明

- `pending` - 等待中：案例爬取已开始，等待结果
- `success` - 成功：案例爬取成功
- `failed` - 失败：案例爬取失败（网络错误、解析错误等）
- `skipped` - 跳过：案例被跳过（如已爬取过）
- `validation_failed` - 验证失败：案例数据验证失败

#### 错误类型说明

- `network_error` - 网络错误：网络请求失败
- `parse_error` - 解析错误：详情页解析失败
- `validation_error` - 验证错误：数据验证失败
- `timeout_error` - 超时错误：请求超时

#### 索引

- `idx_crawl_case_records_task_id` - 任务 ID 索引（用于查询任务的案例记录）
- `idx_crawl_case_records_list_page_id` - 列表页 ID 索引（用于查询列表页的案例）
- `idx_crawl_case_records_status` - 状态索引（用于查询特定状态的案例）
- `idx_crawl_case_records_task_status` - 任务 ID+状态联合索引（用于查询任务的失败案例）
- `idx_crawl_case_records_case_id` - 案例 ID 索引（用于查询特定案例的记录）

#### 唯一约束

- `unique_task_case` - `(task_id, case_id)` 唯一约束，确保每个任务的每个案例只有一条记录

#### 外键关系

- `task_id` → `crawl_tasks(task_id)` ON DELETE CASCADE
  - 删除任务时，自动删除所有相关案例记录
- `list_page_id` → `crawl_list_pages(id)` ON DELETE SET NULL
  - 删除列表页记录时，将案例记录的 `list_page_id` 设置为 NULL（保留案例记录）

---

## 3. 表之间的映射关系

### 3.1 ER 关系图

```
┌─────────────────────────────────────────────────────────────┐
│                    crawl_tasks (主表)                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ id (PK)                                              │  │
│  │ task_id (UNIQUE)                                     │  │
│  │ name, data_source, description                       │  │
│  │ status, created_at, started_at, completed_at         │  │
│  │ total_crawled, total_saved, total_failed             │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┬───────────────┬──────────────┐
        │               │               │               │              │
        │               │               │               │              │
┌───────▼───────┐ ┌─────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│crawl_task_   │ │crawl_task_ │ │crawl_list_ │ │crawl_case_ │ │task_imports│
│logs          │ │status_     │ │pages       │ │records     │ │            │
│              │ │history     │ │            │ │            │ │            │
│task_id (FK)  │ │task_id (FK)│ │task_id (FK)│ │task_id (FK)│ │task_id (FK)│
│level         │ │status      │ │page_number │ │list_page_  │ │import_id   │
│message       │ │previous_   │ │status      │ │id (FK)     │ │status      │
│details       │ │status      │ │items_count │ │case_id     │ │total_cases │
│created_at    │ │created_at  │ │error_msg   │ │status      │ │imported_   │
└──────────────┘ └────────────┘ └────────────┘ │error_msg   │ │cases      │
                                               │saved_to_   │ └─────┬─────┘
                                               │json        │       │
                                               │batch_file  │       │ import_id (FK)
                                               └────────────┘       │
                                                                    │
                                                            ┌───────▼────────┐
                                                            │task_import_    │
                                                            │errors          │
                                                            │                │
                                                            │import_id (FK)  │
                                                            │case_id         │
                                                            │error_type      │
                                                            │error_message   │
                                                            └────────────────┘
```

### 3.2 关系映射表

| 主表               | 从表                        | 关联字段                  | 关系类型 | 级联操作 | 说明                                     |
| ------------------ | --------------------------- | ------------------------- | -------- | -------- | ---------------------------------------- |
| `crawl_tasks`      | `crawl_task_logs`           | `task_id` → `task_id`     | 一对多   | CASCADE  | 一个任务有多条日志                       |
| `crawl_tasks`      | `crawl_task_status_history` | `task_id` → `task_id`     | 一对多   | CASCADE  | 一个任务有多条状态历史（触发器自动创建） |
| `crawl_tasks`      | `crawl_list_pages`          | `task_id` → `task_id`     | 一对多   | CASCADE  | 一个任务有多个列表页记录                 |
| `crawl_tasks`      | `crawl_case_records`        | `task_id` → `task_id`     | 一对多   | CASCADE  | 一个任务有多个案例记录                   |
| `crawl_list_pages` | `crawl_case_records`        | `id` → `list_page_id`     | 一对多   | SET NULL | 一个列表页有多个案例记录                 |
| `crawl_tasks`      | `task_imports`              | `task_id` → `task_id`     | 一对多   | CASCADE  | 一个爬取任务可以有多个导入任务           |
| `task_imports`     | `task_import_errors`        | `import_id` → `import_id` | 一对多   | CASCADE  | 一个导入任务有多条错误记录               |

### 3.3 数据流向

```
1. 创建爬取任务
   └─> crawl_tasks (创建记录)
       └─> crawl_task_status_history (自动创建：pending)

2. 开始执行任务
   └─> crawl_tasks.status = 'running'
       └─> crawl_task_status_history (自动创建：pending → running)
       └─> crawl_task_logs (记录开始日志)

3. 执行爬取
   ├─> 获取列表页
   │   ├─> crawl_list_pages (创建记录：status=pending)
   │   ├─> 调用API获取数据
   │   ├─> crawl_list_pages (更新：status=success/failed, items_count, duration)
   │   └─> 返回案例列表项
   │
   └─> 遍历每个案例
       ├─> crawl_case_records (创建记录：status=pending, list_page_id)
       ├─> 解析详情页
       │   ├─> 成功: crawl_case_records (更新：status=success, has_detail_data=true)
       │   └─> 失败: crawl_case_records (更新：status=failed, error_message, error_type)
       ├─> 验证数据
       │   ├─> 通过: crawl_case_records (更新：has_validation_error=false)
       │   └─> 失败: crawl_case_records (更新：status=validation_failed, validation_errors)
       ├─> 保存到批次
       └─> 保存批次时: crawl_case_records (更新：saved_to_json=true, batch_file_name)

   └─> crawl_task_logs (记录进度日志)
   └─> crawl_tasks (更新进度：total_crawled, current_page等，可从数据库聚合计算)

4. 任务完成/失败
   └─> crawl_tasks.status = 'completed'/'failed'
       └─> crawl_task_status_history (自动创建状态变更记录)
       └─> crawl_task_logs (记录完成/失败日志)

5. 创建导入任务
   └─> task_imports (创建记录，关联到 crawl_tasks.task_id)

6. 执行导入
   └─> task_imports (更新进度：imported_cases等)
   └─> task_import_errors (记录导入错误，关联到 task_imports.import_id)

7. 导入完成/失败
   └─> task_imports.status = 'completed'/'failed'
```

### 3.4 关键关联查询示例

#### 查询任务及其所有日志

```sql
SELECT t.*, l.level, l.message, l.created_at
FROM crawl_tasks t
LEFT JOIN crawl_task_logs l ON t.task_id = l.task_id
WHERE t.task_id = 'task_xxx'
ORDER BY l.created_at DESC;
```

#### 查询任务的状态变更历史

```sql
SELECT h.*
FROM crawl_task_status_history h
WHERE h.task_id = 'task_xxx'
ORDER BY h.created_at ASC;
```

#### 查询任务的所有导入记录

```sql
SELECT i.*, COUNT(e.id) as error_count
FROM task_imports i
LEFT JOIN task_import_errors e ON i.import_id = e.import_id
WHERE i.task_id = 'task_xxx'
GROUP BY i.id;
```

#### 查询导入任务的错误详情

```sql
SELECT e.*
FROM task_import_errors e
WHERE e.import_id = 'import_xxx'
ORDER BY e.created_at DESC;
```

#### 查询任务的失败列表页

```sql
SELECT lp.*
FROM crawl_list_pages lp
WHERE lp.task_id = 'task_xxx' AND lp.status = 'failed'
ORDER BY lp.page_number ASC;
```

#### 查询列表页的所有案例记录

```sql
SELECT cr.*
FROM crawl_case_records cr
WHERE cr.list_page_id = 123
ORDER BY cr.created_at ASC;
```

#### 查询任务的失败案例

```sql
SELECT cr.*
FROM crawl_case_records cr
WHERE cr.task_id = 'task_xxx' AND cr.status IN ('failed', 'validation_failed')
ORDER BY cr.created_at DESC;
```

#### 查询任务的统计信息（从数据库聚合）

```sql
SELECT
    t.task_id,
    COUNT(DISTINCT lp.id) as total_list_pages,
    COUNT(DISTINCT CASE WHEN lp.status = 'success' THEN lp.id END) as success_list_pages,
    COUNT(DISTINCT CASE WHEN lp.status = 'failed' THEN lp.id END) as failed_list_pages,
    COUNT(DISTINCT cr.id) as total_cases,
    COUNT(DISTINCT CASE WHEN cr.status = 'success' THEN cr.id END) as success_cases,
    COUNT(DISTINCT CASE WHEN cr.status = 'failed' THEN cr.id END) as failed_cases,
    COUNT(DISTINCT CASE WHEN cr.status = 'validation_failed' THEN cr.id END) as validation_failed_cases,
    COUNT(DISTINCT CASE WHEN cr.saved_to_json = TRUE THEN cr.id END) as saved_cases
FROM crawl_tasks t
LEFT JOIN crawl_list_pages lp ON t.task_id = lp.task_id
LEFT JOIN crawl_case_records cr ON t.task_id = cr.task_id
WHERE t.task_id = 'task_xxx'
GROUP BY t.task_id;
```

---

## 4. 字段映射关系总结

### 4.1 任务生命周期字段映射

| 阶段       | crawl_tasks 字段                                  | 相关表                                                      | 说明                                         |
| ---------- | ------------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------- |
| **创建**   | `created_at`, `status='pending'`                  | `crawl_task_status_history`                                 | 自动记录状态变更                             |
| **开始**   | `started_at`, `status='running'`                  | `crawl_task_logs`, `crawl_task_status_history`              | 记录开始时间和状态变更                       |
| **执行中** | `current_page`, `total_crawled`, `total_saved`    | `crawl_task_logs`, `crawl_list_pages`, `crawl_case_records` | 实时更新进度和日志，记录列表页和案例状态     |
| **暂停**   | `paused_at`, `status='paused'`                    | `crawl_task_status_history`                                 | 记录暂停时间和状态变更                       |
| **完成**   | `completed_at`, `status='completed'`              | `crawl_task_logs`, `crawl_task_status_history`              | 记录完成时间和最终统计（可从数据库聚合计算） |
| **失败**   | `error_message`, `error_stack`, `status='failed'` | `crawl_task_logs`, `crawl_task_status_history`              | 记录错误信息和状态变更                       |

### 4.2 列表页爬取字段映射

| 阶段       | crawl_list_pages 字段                            | 相关表               | 说明                   |
| ---------- | ------------------------------------------------ | -------------------- | ---------------------- |
| **开始**   | `created_at`, `status='pending'`                 | -                    | 创建列表页记录         |
| **执行中** | `crawled_at`, `duration_seconds`                 | -                    | 记录爬取时间和耗时     |
| **成功**   | `status='success'`, `items_count`                | `crawl_case_records` | 记录成功状态和案例数量 |
| **失败**   | `status='failed'`, `error_message`, `error_type` | -                    | 记录失败状态和错误信息 |
| **重试**   | `retry_count`, `last_retry_at`                   | -                    | 记录重试次数和时间     |

### 4.3 案例爬取字段映射

| 阶段           | crawl_case_records 字段                                         | 相关表             | 说明                       |
| -------------- | --------------------------------------------------------------- | ------------------ | -------------------------- |
| **开始**       | `created_at`, `status='pending'`, `list_page_id`                | `crawl_list_pages` | 创建案例记录，关联到列表页 |
| **解析详情页** | `has_detail_data`, `crawled_at`, `duration_seconds`             | -                  | 记录详情页解析结果         |
| **成功**       | `status='success'`                                              | -                  | 记录成功状态               |
| **失败**       | `status='failed'`, `error_message`, `error_type`, `error_stack` | -                  | 记录失败状态和错误信息     |
| **验证**       | `has_validation_error`, `validation_errors`                     | -                  | 记录验证结果               |
| **验证失败**   | `status='validation_failed'`                                    | -                  | 记录验证失败状态           |
| **保存**       | `saved_to_json`, `batch_file_name`                              | -                  | 记录保存状态和批次文件名   |
| **重试**       | `retry_count`, `last_retry_at`                                  | -                  | 记录重试次数和时间         |

### 4.4 统计字段计算关系

| 统计项           | 计算方式                               | 相关字段/表                                                                                   |
| ---------------- | -------------------------------------- | --------------------------------------------------------------------------------------------- |
| **成功率**       | `total_saved / total_crawled`          | `crawl_tasks.total_saved`, `crawl_tasks.total_crawled`<br>或从 `crawl_case_records` 聚合计算  |
| **错误率**       | `total_failed / total_crawled`         | `crawl_tasks.total_failed`, `crawl_tasks.total_crawled`<br>或从 `crawl_case_records` 聚合计算 |
| **进度百分比**   | `completed_pages / total_pages * 100`  | `crawl_tasks.completed_pages`, `crawl_tasks.total_pages`<br>或从 `crawl_list_pages` 聚合计算  |
| **平均速度**     | `total_crawled / duration_minutes`     | `crawl_tasks.total_crawled`, `crawl_tasks.started_at`, `crawl_tasks.completed_at`             |
| **列表页成功率** | `COUNT(status='success') / COUNT(*)`   | 从 `crawl_list_pages` 聚合计算                                                                |
| **案例成功率**   | `COUNT(status='success') / COUNT(*)`   | 从 `crawl_case_records` 聚合计算                                                              |
| **保存率**       | `COUNT(saved_to_json=true) / COUNT(*)` | 从 `crawl_case_records` 聚合计算                                                              |

### 4.5 导入任务字段映射

| 阶段       | task_imports 字段                                 | 相关表               | 说明               |
| ---------- | ------------------------------------------------- | -------------------- | ------------------ |
| **创建**   | `created_at`, `status='pending'`                  | -                    | 创建导入任务       |
| **开始**   | `started_at`, `status='running'`                  | -                    | 开始导入           |
| **执行中** | `current_file`, `imported_cases`, `failed_cases`  | `task_import_errors` | 实时更新进度和错误 |
| **完成**   | `completed_at`, `status='completed'`              | `task_import_errors` | 记录完成统计       |
| **失败**   | `error_message`, `error_stack`, `status='failed'` | `task_import_errors` | 记录错误详情       |

---

## 5. 数据一致性保证

### 5.1 触发器机制

1. **自动更新 `updated_at`**

   - 表：`crawl_tasks`
   - 触发器：`trigger_update_crawl_tasks_updated_at`
   - 作用：每次更新记录时自动更新 `updated_at` 字段

2. **自动记录状态变更历史**
   - 表：`crawl_tasks` → `crawl_task_status_history`
   - 触发器：`trigger_record_crawl_task_status_change`
   - 作用：当 `status` 字段变化时，自动插入一条历史记录

### 5.2 外键约束

所有外键都设置了适当的级联操作，确保：

- **CASCADE 删除**：
  - 删除任务时，自动删除所有相关日志、状态历史、列表页记录、案例记录、导入记录
  - 删除导入任务时，自动删除所有相关错误记录
- **SET NULL 删除**：
  - 删除列表页记录时，将案例记录的 `list_page_id` 设置为 NULL（保留案例记录，避免数据丢失）
- 保证数据完整性，避免孤立记录

### 5.3 数据校验约束

- `crawl_tasks.status`：CHECK 约束，确保状态值合法
- `crawl_task_logs.level`：CHECK 约束，确保日志级别合法
- `crawl_list_pages.status`：CHECK 约束，确保列表页状态值合法
- `crawl_case_records.status`：CHECK 约束，确保案例状态值合法
- `task_imports.status`：CHECK 约束，确保导入状态合法
- `task_imports.import_mode`：CHECK 约束，确保导入模式合法

### 5.4 唯一约束

- `crawl_list_pages(task_id, page_number)`：确保每个任务的每个页码只有一条记录
- `crawl_case_records(task_id, case_id)`：确保每个任务的每个案例只有一条记录

---

## 6. 索引优化策略

### 6.1 查询场景索引

| 查询场景         | 索引                                                                   | 表                   |
| ---------------- | ---------------------------------------------------------------------- | -------------------- |
| 按状态查询任务   | `idx_crawl_tasks_status`                                               | `crawl_tasks`        |
| 按数据源查询任务 | `idx_crawl_tasks_data_source`                                          | `crawl_tasks`        |
| 按时间排序任务   | `idx_crawl_tasks_created_at`, `idx_crawl_tasks_started_at`             | `crawl_tasks`        |
| 查询任务日志     | `idx_crawl_task_logs_task_id`, `idx_crawl_task_logs_task_level`        | `crawl_task_logs`    |
| 查询任务的列表页 | `idx_crawl_list_pages_task_id`, `idx_crawl_list_pages_task_status`     | `crawl_list_pages`   |
| 查询失败列表页   | `idx_crawl_list_pages_status`, `idx_crawl_list_pages_task_status`      | `crawl_list_pages`   |
| 查询任务的案例   | `idx_crawl_case_records_task_id`, `idx_crawl_case_records_task_status` | `crawl_case_records` |
| 查询列表页的案例 | `idx_crawl_case_records_list_page_id`                                  | `crawl_case_records` |
| 查询失败案例     | `idx_crawl_case_records_status`, `idx_crawl_case_records_task_status`  | `crawl_case_records` |
| 查询特定案例记录 | `idx_crawl_case_records_case_id`                                       | `crawl_case_records` |
| 查询导入记录     | `idx_task_imports_task_id`, `idx_task_imports_status`                  | `task_imports`       |
| 查询导入错误     | `idx_task_import_errors_import_id`, `idx_task_import_errors_case_id`   | `task_import_errors` |

### 6.2 联合索引

- `idx_crawl_task_logs_task_level`：用于查询特定任务的特定级别日志
- `idx_crawl_list_pages_task_status`：用于查询特定任务的特定状态列表页（如失败的列表页）
- `idx_crawl_case_records_task_status`：用于查询特定任务的特定状态案例（如失败的案例）
- 其他表主要使用单字段索引，因为查询场景相对简单

---

## 7. 总结

### 7.1 表设计特点

1. **层次清晰**：主表（crawl_tasks）→ 子表（logs, history, list_pages, case_records, imports）→ 错误表（errors）
2. **关联明确**：所有表都通过外键明确关联到主表，列表页和案例之间也有明确的关联关系
3. **自动维护**：使用触发器和外键约束自动维护数据一致性
4. **可追溯性**：通过日志表、状态历史表、列表页记录表和案例记录表提供完整的操作追溯能力
5. **精确重试**：通过列表页和案例记录表，可以精确重试失败的列表页或案例，无需重新爬取整个任务

### 7.2 数据完整性保证

- ✅ 外键约束确保关联数据的一致性
- ✅ CHECK 约束确保字段值的合法性
- ✅ 触发器自动维护状态历史和更新时间
- ✅ CASCADE 删除确保不会产生孤立数据

### 7.3 查询性能优化

- ✅ 关键字段都建立了索引
- ✅ 联合索引优化常见查询场景
- ✅ 时间字段索引支持排序查询

### 7.4 扩展性考虑

当前表结构支持：

- ✅ 多数据源（通过 `data_source` 字段）
- ✅ 多任务并发（通过 `task_id` 唯一标识）
- ✅ 多导入任务（一个爬取任务可以有多个导入任务）
- ✅ 详细错误追踪（通过错误表记录每个案例的错误）
- ✅ 精确重试机制（通过列表页和案例记录表，可以精确重试失败的列表页或案例）
- ✅ 细粒度监控（可以监控每个列表页和每个案例的爬取状态）

---

## 8. 新增表说明

### 8.1 新增表的作用

根据 `crawl-task-optimization.md` 中的优化方案，已新增以下两个表：

1. **`crawl_list_pages`** - 列表页爬取记录表 ✅ **已实现**

   - 用于记录每个列表页的爬取结果
   - 解决无法精确重试失败列表页的问题
   - 提供列表页级别的详细监控和统计

2. **`crawl_case_records`** - 案例爬取记录表 ✅ **已实现**
   - 用于记录每个案例的爬取结果
   - 解决无法精确重试失败案例的问题
   - 提供案例级别的详细监控和统计

### 8.2 优化效果

这两个表的加入实现了以下优化：

- ✅ **可观测性提升**：可以查看每个列表页和每个案例的爬取状态和结果
- ✅ **重试效率提升**：可以精确重试失败的列表页或案例，无需重新爬取整个任务
- ✅ **问题定位能力提升**：可以快速定位哪些列表页或案例失败了，失败原因是什么
- ✅ **统计准确性提升**：可以从数据库聚合计算准确的统计信息，而不依赖 JSON 文件
