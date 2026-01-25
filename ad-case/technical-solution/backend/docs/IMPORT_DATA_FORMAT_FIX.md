# 数据导入格式化修复说明

## 问题描述

在数据导入过程中，发现以下问题：

1. `score` 字段的数据库约束为 1-5，但实际数据中可能包含 0 或超出范围的值
2. 导入配置默认 `skip_existing=True` 和 `skip_invalid=True`，导致错误被隐藏
3. 缺少数据格式化功能，无法将非法值转换为可入库的格式

## 解决方案

### 1. 修改数据库约束

**文件**: `database/migrations/005_update_score_constraint.sql`

将 `score` 字段约束从 `score >= 1 AND score <= 5` 改为 `score IS NULL OR (score >= 0 AND score <= 5)`，允许：

- 0-5 之间的整数值
- NULL 值

### 2. 增加数据格式化功能

**文件**: `services/pipeline/validator.py`

新增 `format_case()` 和 `format_batch()` 方法，支持：

- 将非法的 `score` 值（超出 0-5 范围）转为 NULL
- 将浮点数 `score` 转换为整数（四舍五入）
- 格式化其他字段（`favourite`、`case_id` 等）

### 3. 在导入阶段应用格式化

**文件**: `services/pipeline/import_stage.py`

- 新增 `normalize_data` 参数（默认 `True`）
- 在验证前先进行数据格式化
- 调整默认配置：`skip_existing=False`、`skip_invalid=False`

### 4. 更新 API Schema

**文件**: `app/schemas/task_import.py`

- 新增 `normalize_data` 字段（默认 `True`）
- 调整默认值：`skip_existing=False`、`skip_invalid=False`

### 5. 更新导入执行器

**文件**: `app/services/import_task_executor.py`

- 传递 `normalize_data` 参数到 `ImportStage`
- 更新方法签名以支持新参数

## 使用方法

### 运行数据库迁移

```bash
cd backend
source venv/bin/activate
psql -d ad_case_db -f database/migrations/005_update_score_constraint.sql
```

### 导入数据时的配置

通过 API 启动导入时，可以设置以下参数：

```json
{
  "import_mode": "full",
  "skip_existing": false, // 默认 false，显示所有错误
  "skip_invalid": false, // 默认 false，显示所有错误
  "normalize_data": true, // 默认 true，规范化数据
  "batch_size": 50
}
```

### 数据格式化规则

1. **score 字段**：

   - 浮点数 → 四舍五入为整数
   - 超出 0-5 范围 → 转为 NULL
   - 无法转换的值 → 转为 NULL

2. **favourite 字段**：

   - 负数 → 转为 0
   - 无法转换的值 → 转为 0

3. **case_id 字段**：
   - 字符串 → 转换为整数
   - 无法转换的值 → 保持原值（验证时会失败）

## 验证

运行诊断脚本检查导入状态：

```bash
python scripts/diagnose_unverified_cases.py <task_id>
```

## 注意事项

1. 数据格式化是可选的，通过 `normalize_data` 参数控制
2. 格式化不会修复所有数据问题，只是将明显非法的值转为默认值或 NULL
3. 建议在导入前先运行格式化，以便发现和修复数据问题
4. 如果 `normalize_data=False`，非法值会保持原样，可能导致导入失败
