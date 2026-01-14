# 数据管道脚本使用说明

## 脚本列表

### 1. crawl.py - 爬取脚本

爬取广告门案例数据并保存到 JSON 文件。

**基本用法**：

```bash
python scripts/crawl.py \
    --output-dir data/json \
    --batch-size 100 \
    --start-page 0 \
    --max-pages 10 \
    --case-type 3
```

**参数说明**：

- `--output-dir`: JSON 文件输出目录（默认: data/json）
- `--batch-size`: 每批保存的案例数量（默认: 100）
- `--start-page`: 起始页码（默认: 0）
- `--max-pages`: 最大页数（默认: 100）
- `--case-type`: 案例类型，0=全部, 3=精选案例（默认: 3）
- `--search-value`: 搜索关键词（可选）
- `--resume-file`: 断点续传文件路径（可选）
- `--no-resume`: 禁用断点续传
- `--delay-min`: 最小延迟时间（秒，默认: 2.0）
- `--delay-max`: 最大延迟时间（秒，默认: 5.0）

**示例**：

```bash
# 爬取精选案例，保存到 data/json 目录
python scripts/crawl.py --max-pages 5

# 爬取并禁用断点续传
python scripts/crawl.py --no-resume

# 自定义输出目录和批次大小
python scripts/crawl.py --output-dir data/cases --batch-size 50
```

### 2. import.py - 入库脚本

从 JSON 文件读取数据，生成向量，并批量入库。

**基本用法**：

```bash
python scripts/import.py \
    --db-name ad_case_db \
    --db-user postgres \
    --db-password your_password \
    --json-dir data/json
```

**参数说明**：

- `--json-file`: JSON 文件路径（如果指定，只导入该文件）
- `--json-dir`: JSON 文件目录（默认: data/json）
- `--pattern`: 文件匹配模式（默认: cases*batch*\*.json）
- `--db-host`: 数据库主机（默认: localhost）
- `--db-port`: 数据库端口（默认: 5432）
- `--db-name`: 数据库名称（必需）
- `--db-user`: 数据库用户（必需）
- `--db-password`: 数据库密码（必需）
- `--batch-size`: 批量入库大小（默认: 50）
- `--model-name`: 嵌入模型名称（默认: BAAI/bge-large-zh-v1.5）
- `--no-skip-existing`: 不跳过已存在的案例
- `--no-skip-invalid`: 不跳过无效的案例

**示例**：

```bash
# 导入目录中的所有JSON文件
python scripts/import.py \
    --db-name ad_case_db \
    --db-user postgres \
    --db-password password

# 导入单个JSON文件
python scripts/import.py \
    --db-name ad_case_db \
    --db-user postgres \
    --db-password password \
    --json-file data/json/cases_batch_0001.json

# 使用环境变量（推荐）
export DB_NAME=ad_case_db
export DB_USER=postgres
export DB_PASSWORD=password

python scripts/import.py \
    --db-name $DB_NAME \
    --db-user $DB_USER \
    --db-password $DB_PASSWORD
```

### 3. validate.py - 验证脚本

验证 JSON 文件中的数据质量。

**基本用法**：

```bash
python scripts/validate.py --json-dir data/json
```

**参数说明**：

- `--json-file`: JSON 文件路径（如果指定，只验证该文件）
- `--json-dir`: JSON 文件目录（默认: data/json）
- `--pattern`: 文件匹配模式（默认: cases*batch*\*.json）

**示例**：

```bash
# 验证目录中的所有JSON文件
python scripts/validate.py

# 验证单个JSON文件
python scripts/validate.py --json-file data/json/cases_batch_0001.json
```

## 完整工作流程

### 1. 爬取数据

```bash
# 第一步：爬取数据并保存到JSON
python scripts/crawl.py \
    --output-dir data/json \
    --batch-size 100 \
    --max-pages 10
```

### 2. 验证数据（可选）

```bash
# 第二步：验证数据质量
python scripts/validate.py --json-dir data/json
```

### 3. 导入数据库

```bash
# 第三步：导入到数据库
python scripts/import.py \
    --db-name ad_case_db \
    --db-user postgres \
    --db-password password \
    --json-dir data/json
```

## 注意事项

1. **断点续传**：爬取脚本默认支持断点续传，会跳过已爬取的案例
2. **数据验证**：入库前建议先运行验证脚本检查数据质量
3. **批量大小**：根据服务器性能调整 `--batch-size` 参数
4. **数据库连接**：确保数据库已创建并配置正确
5. **模型下载**：首次运行入库脚本会自动下载嵌入模型（约 1.2GB）

## 故障排查

### 爬取失败

- 检查网络连接
- 检查 CSRF Token 是否有效
- 调整延迟时间（`--delay-min` 和 `--delay-max`）

### 入库失败

- 检查数据库连接配置
- 检查数据库表结构是否正确
- 检查 JSON 文件格式是否正确
- 查看日志文件了解详细错误信息

### 向量生成失败

- 检查模型是否正确下载
- 检查内存是否足够（模型需要 2-3GB 内存）
- 检查文本内容是否为空
