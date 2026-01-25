-- ============================================================
-- 迁移脚本：更新 score 字段约束
-- 将 score 字段约束从 1-5 改为 0-5，并允许 NULL
-- ============================================================

-- 1. 删除旧的约束
ALTER TABLE ad_cases DROP CONSTRAINT IF EXISTS ad_cases_score_check;

-- 2. 添加新的约束：允许 0-5 或 NULL
ALTER TABLE ad_cases ADD CONSTRAINT ad_cases_score_check 
    CHECK (score IS NULL OR (score >= 0 AND score <= 5));

-- 3. 添加注释说明
COMMENT ON COLUMN ad_cases.score IS '评分（0-5之间的整数，可以为NULL）';
