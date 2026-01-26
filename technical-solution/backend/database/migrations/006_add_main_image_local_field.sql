-- 为 ad_cases 表添加 main_image_local 字段
-- 创建时间：2026-01-18
-- 说明：添加本地图片路径字段，用于存储下载到本地的图片路径

-- ============================================================
-- 添加本地图片路径字段
-- ============================================================

ALTER TABLE ad_cases
ADD COLUMN IF NOT EXISTS main_image_local TEXT; -- 本地图片路径，如: /static/images/297041/main_image.png

-- ============================================================
-- 添加注释
-- ============================================================

COMMENT ON COLUMN ad_cases.main_image_local IS '本地图片路径：下载到本地服务器后的图片访问路径，格式为 /static/images/{case_id}/main_image.{ext}';

-- ============================================================
-- 创建索引（可选，用于查询有本地图片的案例）
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_ad_cases_main_image_local ON ad_cases(main_image_local) WHERE main_image_local IS NOT NULL;
