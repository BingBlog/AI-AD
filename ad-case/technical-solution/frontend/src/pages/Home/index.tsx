/**
 * 首页
 */
import { useMemo } from "react";
import { Button, Card, Typography, Space, Spin, Row, Col } from "antd";
import {
  SearchOutlined,
  AppstoreOutlined,
  FilterOutlined,
  FileSearchOutlined,
  CloudDownloadOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ArrowRightOutlined,
  RocketOutlined,
  DatabaseOutlined,
  TagsOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getStats } from "@/services/caseService";
import WordCloud3D, { WordCloudItem } from "@/components/WordCloud3D";
import HeroSearchBox from "@/components/Search/HeroSearchBox";
import styles from "./index.module.less";

const { Title, Paragraph } = Typography;

const Home: React.FC = () => {
  const navigate = useNavigate();

  // 获取统计数据
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: getStats,
    staleTime: 5 * 60 * 1000, // 5分钟
  });

  // 处理图片URL（将相对路径转换为完整URL）
  const processImageUrl = (url?: string): string | undefined => {
    if (!url) return undefined;

    // 如果是相对路径（以 /static/ 开头），在开发环境通过Vite代理访问
    if (url.startsWith("/static/")) {
      if (import.meta.env.DEV) {
        return url;
      } else {
        const backendUrl = import.meta.env.VITE_API_BASE_URL
          ? import.meta.env.VITE_API_BASE_URL.replace("/api", "")
          : "";
        return backendUrl ? `${backendUrl}${url}` : url;
      }
    }

    // 如果是完整URL，直接返回
    return url;
  };

  // 转换行业数据为云图格式
  const industryItems: WordCloudItem[] = useMemo(() => {
    if (!stats?.industries) return [];
    return stats.industries.map((item) => ({
      name: item.name,
      count: item.count,
      image: processImageUrl(item.image),
    }));
  }, [stats?.industries]);

  // 转换标签数据为云图格式
  const tagItems: WordCloudItem[] = useMemo(() => {
    if (!stats?.tags) return [];
    return stats.tags.map((item) => ({
      name: item.name,
      count: item.count,
      image: processImageUrl(item.image),
    }));
  }, [stats?.tags]);

  // 处理云图项点击（跳转到案例列表页，并应用筛选）
  const handleIndustryClick = (item: WordCloudItem) => {
    navigate(`/cases?brand_industry=${encodeURIComponent(item.name)}`);
  };

  const handleTagClick = (item: WordCloudItem) => {
    navigate(`/cases?tags=${encodeURIComponent(item.name)}`);
  };

  // 获取随机背景图片（从统计数据中随机选择一张）
  const randomBackgroundImage = useMemo(() => {
    const allImages: string[] = [];
    if (stats?.industries) {
      stats.industries.forEach((item) => {
        if (item.image) {
          const url = processImageUrl(item.image);
          if (url) allImages.push(url);
        }
      });
    }
    if (stats?.tags) {
      stats.tags.forEach((item) => {
        if (item.image) {
          const url = processImageUrl(item.image);
          if (url) allImages.push(url);
        }
      });
    }
    if (allImages.length > 0) {
      return allImages[Math.floor(Math.random() * allImages.length)];
    }
    return null;
  }, [stats]);

  return (
    <div className={styles.home}>
      {/* Hero 区域 */}
      <div
        className={styles.hero}
        style={{
          backgroundImage: randomBackgroundImage
            ? `url(${randomBackgroundImage})`
            : undefined,
        }}>
        <div className={styles.heroOverlay}></div>
        <div className={styles.heroContent}>
          <div className={styles.heroBadge}>
            <span>AI驱动</span>
            <span className={styles.badgeDot}></span>
            <span>智能创意</span>
          </div>
          <Title level={1} className={styles.heroTitle}>
            发现无限创意灵感
            <span className={styles.heroSubtitle}>
              海量广告案例，一键触达全球顶尖营销智慧
            </span>
          </Title>
          <Paragraph className={styles.heroDescription}>
            <strong>百万级案例库</strong> · <strong>智能语义检索</strong> ·{" "}
            <strong>多维精准筛选</strong>
            <br />
            让每一个营销创意都成为爆款，让每一次方案设计都充满灵感
          </Paragraph>

          {/* 数据统计 */}
          {stats && (
            <div className={styles.heroStats}>
              <div className={styles.statItem}>
                <div className={styles.statNumber}>
                  {stats.total_cases.toLocaleString()}+
                </div>
                <div className={styles.statLabel}>精选案例</div>
              </div>
              <div className={styles.statDivider}></div>
              <div className={styles.statItem}>
                <div className={styles.statNumber}>
                  {stats.industries?.length || 0}
                </div>
                <div className={styles.statLabel}>行业覆盖</div>
              </div>
              <div className={styles.statDivider}></div>
              <div className={styles.statItem}>
                <div className={styles.statNumber}>
                  {stats.tags?.length || 0}
                </div>
                <div className={styles.statLabel}>创意标签</div>
              </div>
            </div>
          )}

          {/* Hero搜索框 */}
          <div className={styles.heroSearchBox}>
            <HeroSearchBox onSearch={() => navigate("/cases")} />
          </div>
        </div>
      </div>

      {/* 云图展示 */}
      <div className={styles.wordCloudSection}>
        <div className={styles.wordCloudContainer}>
          <Title level={2} className={styles.sectionTitle}>
            数据可视化
            <span
              style={{
                display: "block",
                fontSize: "24px",
                fontWeight: 400,
                color: "#94a3b8",
                marginTop: "12px",
              }}>
              探索行业趋势，发现创意热点
            </span>
          </Title>
          {statsLoading ? (
            <div className={styles.statsLoading}>
              <Spin size="large" />
            </div>
          ) : (
            <Row gutter={[24, 24]} className={styles.wordCloudsWrapper}>
              {/* 行业分类3D云图 */}
              <Col xs={24} lg={12}>
                <div className={styles.wordCloudWrapper}>
                  <WordCloud3D
                    items={industryItems}
                    title="行业分类"
                    onItemClick={handleIndustryClick}
                  />
                </div>
              </Col>

              {/* 标签3D云图 */}
              <Col xs={24} lg={12}>
                <div className={styles.wordCloudWrapper}>
                  <WordCloud3D
                    items={tagItems}
                    title="热门标签"
                    onItemClick={handleTagClick}
                  />
                </div>
              </Col>
            </Row>
          )}
        </div>
      </div>

      {/* 核心功能特性 */}
      <div className={styles.featuresSection}>
        <div className={styles.featuresContainer}>
          <Title level={2} className={styles.sectionTitle}>
            强大功能
            <span
              style={{
                display: "block",
                fontSize: "24px",
                fontWeight: 400,
                color: "#94a3b8",
                marginTop: "12px",
              }}>
              让创意检索变得简单高效
            </span>
          </Title>
          <Row gutter={[24, 24]} className={styles.featuresRow}>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <FileSearchOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  智能检索
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>秒级响应</strong>
                  ，关键词、语义、混合三种检索模式，让您快速找到心仪的创意案例
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>关键词全文搜索 - 精准匹配</li>
                  <li>语义理解检索 - 智能推荐</li>
                  <li>混合检索模式 - 最佳效果</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <FilterOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  多维筛选
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>7大筛选维度</strong>
                  ，品牌、行业、类型、地点、时间等，精准定位您需要的案例
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>品牌与行业筛选 - 快速定位</li>
                  <li>活动类型与地点 - 精准匹配</li>
                  <li>时间范围筛选 - 紧跟趋势</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <DatabaseOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  丰富案例库
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>百万级案例</strong>
                  ，覆盖全行业优质创意，每日更新，让您永远走在创意前沿
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>全行业覆盖 - 应有尽有</li>
                  <li>完整案例信息 - 深度解析</li>
                  <li>高清图片视频 - 素材丰富</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <CloudDownloadOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  任务管理
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>一键创建</strong>
                  爬取任务，实时监控进度，灵活控制采集流程，让数据收集变得简单
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>任务创建与配置 - 简单易用</li>
                  <li>实时进度监控 - 一目了然</li>
                  <li>任务控制与重试 - 智能管理</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <ThunderboltOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  快速响应
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>毫秒级响应</strong>
                  ，优化的算法和缓存机制，让每一次搜索都如丝般顺滑
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>毫秒级检索速度 - 极速体验</li>
                  <li>智能缓存机制 - 秒开结果</li>
                  <li>流畅交互体验 - 行云流水</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <TagsOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  标签体系
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>智能标签</strong>
                  分类体系，创意形式、内容主题、行业标签，快速发现相关案例
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>创意形式标签 - 精准分类</li>
                  <li>内容主题标签 - 深度挖掘</li>
                  <li>行业相关标签 - 快速关联</li>
                </ul>
              </Card>
            </Col>
          </Row>
        </div>
      </div>

      {/* 使用流程 */}
      <div className={styles.workflowSection}>
        <div className={styles.workflowContainer}>
          <Title level={2} className={styles.sectionTitle}>
            使用流程
            <span
              style={{
                display: "block",
                fontSize: "24px",
                fontWeight: 400,
                color: "#94a3b8",
                marginTop: "12px",
              }}>
              四步开启创意之旅
            </span>
          </Title>
          <Row gutter={[32, 32]} className={styles.workflowRow}>
            <Col xs={24} sm={12} md={6}>
              <div className={styles.workflowStep}>
                <div className={styles.stepNumber}>1</div>
                <div className={styles.stepIcon}>
                  <SearchOutlined />
                </div>
                <Title level={4} className={styles.stepTitle}>
                  搜索案例
                </Title>
                <Paragraph className={styles.stepDescription}>
                  输入关键词或自然语言，智能检索帮您秒速找到心仪案例
                </Paragraph>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div className={styles.workflowStep}>
                <div className={styles.stepNumber}>2</div>
                <div className={styles.stepIcon}>
                  <AppstoreOutlined />
                </div>
                <Title level={4} className={styles.stepTitle}>
                  浏览详情
                </Title>
                <Paragraph className={styles.stepDescription}>
                  查看高清图片、视频素材和完整案例信息，深度了解创意亮点
                </Paragraph>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div className={styles.workflowStep}>
                <div className={styles.stepNumber}>3</div>
                <div className={styles.stepIcon}>
                  <CheckCircleOutlined />
                </div>
                <Title level={4} className={styles.stepTitle}>
                  获取灵感
                </Title>
                <Paragraph className={styles.stepDescription}>
                  从顶尖案例中汲取创意精华，为您的营销方案注入无限灵感
                </Paragraph>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div className={styles.workflowStep}>
                <div className={styles.stepNumber}>4</div>
                <div className={styles.stepIcon}>
                  <RocketOutlined />
                </div>
                <Title level={4} className={styles.stepTitle}>
                  创建方案
                </Title>
                <Paragraph className={styles.stepDescription}>
                  结合海量案例灵感，创作出属于您的爆款营销方案
                </Paragraph>
              </div>
            </Col>
          </Row>
        </div>
      </div>

      {/* 快速入口 */}
      <div className={styles.ctaSection}>
        <Card className={styles.ctaCard}>
          <div className={styles.ctaContent}>
            <Title level={2} className={styles.ctaTitle}>
              准备开始你的创意之旅？
            </Title>
            <Paragraph className={styles.ctaDescription}>
              立即探索海量广告案例库，发现下一个爆款营销创意的灵感
            </Paragraph>
            <Space size="large">
              <Button
                type="primary"
                size="large"
                icon={<SearchOutlined />}
                onClick={() => navigate("/cases")}
                className={styles.ctaButton}>
                立即开始探索
                <ArrowRightOutlined />
              </Button>
              <Button
                size="large"
                icon={<CloudDownloadOutlined />}
                onClick={() => navigate("/crawl-tasks")}>
                管理收集任务
              </Button>
            </Space>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Home;
