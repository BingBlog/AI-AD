-- 广告案例库数据库初始化脚本（临时版本，不包含向量字段）
-- 数据库：ad_case_db
-- PostgreSQL 12+

-- ============================================================
-- 1. 创建主表：ad_cases（不包含向量字段）
-- ============================================================

CREATE TABLE IF NOT EXISTS ad_cases (
    -- 主键和标识
    id BIGSERIAL PRIMARY KEY,
    case_id INTEGER UNIQUE NOT NULL,  -- 原始案例ID（来自爬虫）

    -- 基础信息
    source_url TEXT NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,  -- 长文本描述
    author VARCHAR(100),
    publish_time DATE,

    -- 媒体资源
    main_image TEXT,
    images JSONB DEFAULT '[]'::jsonb,  -- 图片URL数组
    video_url TEXT,

    -- 分类信息
    brand_name VARCHAR(200),
    brand_industry VARCHAR(100),
    activity_type VARCHAR(100),
    location VARCHAR(100),
    tags JSONB DEFAULT '[]'::jsonb,  -- 标签数组

    -- 评分与互动
    score INTEGER CHECK (score >= 1 AND score <= 5),
    score_decimal VARCHAR(10),  -- 如 "9.5"
    favourite INTEGER DEFAULT 0,

    -- 公司信息
    company_name VARCHAR(200),
    company_logo TEXT,
    agency_name VARCHAR(200),

    -- 全文检索字段（用于关键词检索）
    title_tsvector tsvector,  -- 标题全文检索向量
    description_tsvector tsvector,  -- 描述全文检索向量
    combined_tsvector tsvector,  -- 标题+描述组合全文检索向量

    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT valid_case_id CHECK (case_id > 0)
);

-- ============================================================
-- 2. 创建索引
-- ============================================================

-- B-Tree 索引（用于精确匹配和排序）
CREATE UNIQUE INDEX IF NOT EXISTS idx_ad_cases_case_id ON ad_cases(case_id);
CREATE INDEX IF NOT EXISTS idx_ad_cases_brand_industry ON ad_cases(brand_industry);
CREATE INDEX IF NOT EXISTS idx_ad_cases_activity_type ON ad_cases(activity_type);
CREATE INDEX IF NOT EXISTS idx_ad_cases_location ON ad_cases(location);
CREATE INDEX IF NOT EXISTS idx_ad_cases_publish_time ON ad_cases(publish_time DESC);
CREATE INDEX IF NOT EXISTS idx_ad_cases_score ON ad_cases(score DESC);
CREATE INDEX IF NOT EXISTS idx_ad_cases_favourite ON ad_cases(favourite DESC);
CREATE INDEX IF NOT EXISTS idx_ad_cases_brand_name ON ad_cases(brand_name);
CREATE INDEX IF NOT EXISTS idx_ad_cases_industry_type ON ad_cases(brand_industry, activity_type);
CREATE INDEX IF NOT EXISTS idx_ad_cases_industry_location ON ad_cases(brand_industry, location);

-- GIN 索引（用于全文检索）
CREATE INDEX IF NOT EXISTS idx_ad_cases_title_tsvector ON ad_cases USING GIN(title_tsvector);
CREATE INDEX IF NOT EXISTS idx_ad_cases_description_tsvector ON ad_cases USING GIN(description_tsvector);
CREATE INDEX IF NOT EXISTS idx_ad_cases_combined_tsvector ON ad_cases USING GIN(combined_tsvector);

-- JSONB 索引（用于数组字段查询）
CREATE INDEX IF NOT EXISTS idx_ad_cases_tags_gin ON ad_cases USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_ad_cases_images_gin ON ad_cases USING GIN(images);

-- ============================================================
-- 3. 创建触发器函数（自动更新全文检索向量）
-- ============================================================

-- 创建函数：更新全文检索向量
CREATE OR REPLACE FUNCTION update_tsvector()
RETURNS TRIGGER AS $$
BEGIN
    -- 使用默认的 simple 配置（中文分词插件稍后安装）
    NEW.title_tsvector := to_tsvector('simple', COALESCE(NEW.title, ''));
    NEW.description_tsvector := to_tsvector('simple', COALESCE(NEW.description, ''));
    NEW.combined_tsvector := 
        setweight(to_tsvector('simple', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('simple', COALESCE(NEW.description, '')), 'B');

    -- 更新 updated_at
    NEW.updated_at := CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
DROP TRIGGER IF EXISTS trigger_update_tsvector ON ad_cases;
CREATE TRIGGER trigger_update_tsvector
    BEFORE INSERT OR UPDATE ON ad_cases
    FOR EACH ROW
    EXECUTE FUNCTION update_tsvector();

-- ============================================================
-- 4. 创建辅助表（可选）
-- ============================================================

-- 品牌表
CREATE TABLE IF NOT EXISTS brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    industry VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_brands_name ON brands(name);
CREATE INDEX IF NOT EXISTS idx_brands_industry ON brands(industry);

-- 行业表
CREATE TABLE IF NOT EXISTS industries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    parent_id INTEGER REFERENCES industries(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_industries_name ON industries(name);
CREATE INDEX IF NOT EXISTS idx_industries_parent ON industries(parent_id);

-- 标签表
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    usage_count INTEGER DEFAULT 0,  -- 使用次数
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
CREATE INDEX IF NOT EXISTS idx_tags_usage_count ON tags(usage_count DESC);

-- 案例标签关联表
CREATE TABLE IF NOT EXISTS case_tags (
    case_id INTEGER REFERENCES ad_cases(case_id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (case_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_case_tags_case_id ON case_tags(case_id);
CREATE INDEX IF NOT EXISTS idx_case_tags_tag_id ON case_tags(tag_id);

-- ============================================================
-- 完成
-- ============================================================

COMMENT ON TABLE ad_cases IS '广告案例主表（向量字段稍后添加）';
