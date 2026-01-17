# PostgreSQL GUI 客户端推荐

## 快速预览数据库内容的工具

### 1. **TablePlus** ⭐ 推荐（macOS 最佳体验）

- **特点**：界面美观，操作流畅，支持多种数据库
- **价格**：免费版有限制，付费版 $89（一次性）
- **安装**：
  ```bash
  brew install --cask tableplus
  ```
- **优点**：
  - 界面现代化，用户体验好
  - 快速预览数据
  - 支持 SQL 查询
  - 支持多种数据库（PostgreSQL, MySQL, SQLite 等）

### 2. **Postico** ⭐ macOS 专用

- **特点**：专为 macOS 设计，轻量级，界面简洁
- **价格**：免费版有限制，付费版 $49（一次性）
- **安装**：
  ```bash
  brew install --cask postico
  ```
- **优点**：
  - macOS 原生体验
  - 轻量快速
  - 专注于 PostgreSQL
  - 界面简洁美观

### 3. **DBeaver** ⭐ 免费开源

- **特点**：功能全面，跨平台，完全免费
- **价格**：完全免费（开源）
- **安装**：
  ```bash
  brew install --cask dbeaver-community
  ```
- **优点**：
  - 完全免费
  - 功能强大
  - 支持几乎所有数据库
  - 社区版功能已足够

### 4. **pgAdmin**（PostgreSQL 官方工具）

- **特点**：PostgreSQL 官方维护，功能全面
- **价格**：完全免费
- **安装**：
  ```bash
  brew install --cask pgadmin4
  ```
- **优点**：
  - 官方工具，功能完整
  - 完全免费
  - 支持高级管理功能
- **缺点**：
  - 界面相对传统
  - 启动较慢

### 5. **DataGrip**（JetBrains 出品）

- **特点**：功能强大，IDE 风格
- **价格**：付费（$199/年，有学生/开源免费）
- **安装**：
  ```bash
  brew install --cask datagrip
  ```
- **优点**：
  - 强大的 SQL 编辑功能
  - 智能代码补全
  - 集成版本控制
  - 支持多种数据库

## 快速连接信息

连接当前数据库时，使用以下信息：

```
主机: localhost
端口: 5432
数据库: ad_case_db
用户: bing
密码: (空，直接回车)
```

## 推荐选择

**如果只是快速预览数据**：

- **TablePlus** 或 **Postico** - 界面美观，操作简单

**如果需要免费且功能全面**：

- **DBeaver** - 完全免费，功能强大

**如果需要官方工具**：

- **pgAdmin** - PostgreSQL 官方维护

## 快速安装命令

```bash
# TablePlus（推荐）
brew install --cask tableplus

# Postico（macOS 专用）
brew install --cask postico

# DBeaver（免费开源）
brew install --cask dbeaver-community

# pgAdmin（官方工具）
brew install --cask pgadmin4
```

## 查看数据示例

安装后，连接数据库，可以执行以下 SQL 查看数据：

```sql
-- 查看所有案例
SELECT case_id, title, brand_name, brand_industry
FROM ad_cases
LIMIT 10;

-- 查看有向量的案例数量
SELECT COUNT(*) as total, COUNT(combined_vector) as with_vector
FROM ad_cases;

-- 查看案例详情
SELECT case_id, title, description, brand_name, tags, images
FROM ad_cases
WHERE case_id = 291696;
```
