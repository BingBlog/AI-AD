# 数据库配置说明

## 数据库信息

- **数据库名称**：`ad_case_db`
- **PostgreSQL 版本**：14.18
- **pgvector 版本**：0.8.0
- **数据库用户**：`postgres`（或当前系统用户）

## 已创建的表

1. **ad_cases** - 案例主表（包含向量字段和全文检索字段）
2. **brands** - 品牌表
3. **industries** - 行业表
4. **tags** - 标签表
5. **case_tags** - 案例标签关联表

## 已创建的索引

- **B-Tree 索引**：用于精确匹配和排序
- **GIN 索引**：用于全文检索和 JSONB 查询
- **HNSW 索引**：用于向量相似度搜索

## 已创建的触发器

- **trigger_update_tsvector**：自动更新全文检索向量字段

## 连接信息

### 本地连接

```bash
psql -U postgres -d ad_case_db
# 或
psql -d ad_case_db
```

### Python 连接配置

```python
db_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ad_case_db',
    'user': 'postgres',  # 或你的系统用户名
    'password': ''  # 如果设置了密码，填写密码
}
```

## 验证数据库

```bash
# 检查表是否存在
psql -d ad_case_db -c "\dt"

# 检查向量扩展
psql -d ad_case_db -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

# 检查表结构
psql -d ad_case_db -c "\d ad_cases"
```

## 下一步

数据库已准备就绪，可以开始导入数据：

```bash
cd backend
python scripts/import.py \
    --db-name ad_case_db \
    --db-user postgres \
    --db-password '' \
    --json-dir data/json
```

## 注意事项

1. **中文分词**：当前使用 PostgreSQL 默认的 `simple` 配置。如需更好的中文分词效果，可以安装 `zhparser` 或 `pg_jieba` 插件。

2. **向量索引**：HNSW 索引会在数据导入后自动创建。如果数据量很大，可以在导入完成后手动创建其他向量字段的索引。

3. **性能优化**：根据实际数据量，可以调整索引参数（如 HNSW 的 `m` 和 `ef_construction` 参数）。
