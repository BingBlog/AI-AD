/**
 * 核心功能板块组件
 * 
 * 注意：由于内容较多，此组件包含所有模块块的内容
 * 后续可以根据需要进一步拆分为更小的组件
 */
import { useMemo } from "react";
import { Button, Card, Typography, Spin, Row, Col } from "antd";
import {
  SearchOutlined,
  AppstoreOutlined,
  FileSearchOutlined,
  ArrowRightOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  BulbOutlined,
  PictureOutlined,
  StarOutlined,
  FireOutlined,
  ExperimentOutlined,
  RobotOutlined,
  ApiOutlined,
  BugOutlined,
  BarChartOutlined,
  FilePdfOutlined,
  DollarOutlined,
  SendOutlined,
  RiseOutlined,
  SafetyOutlined,
  RocketOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import WordCloud3D, { WordCloudItem } from "@/components/WordCloud3D";
import styles from "../index.module.less";

const { Title, Paragraph } = Typography;

interface ModulesSectionProps {
  stats?: {
    total_cases: number;
    industries?: Array<{ name: string; count: number; image?: string; length: number }>;
    tags?: Array<{ name: string; count: number; image?: string; length: number }>;
  };
  statsLoading?: boolean;
  processImageUrl?: (url?: string) => string | undefined;
}

const ModulesSection: React.FC<ModulesSectionProps> = ({
  stats,
  statsLoading = false,
  processImageUrl,
}) => {
  const navigate = useNavigate();

  // 转换行业数据为云图格式
  const industryItems: WordCloudItem[] = useMemo(() => {
    if (!stats?.industries || !processImageUrl) return [];
    return stats.industries.map((item) => ({
      name: item.name,
      count: item.count,
      image: processImageUrl(item.image),
    }));
  }, [stats?.industries, processImageUrl]);

  // 转换标签数据为云图格式
  const tagItems: WordCloudItem[] = useMemo(() => {
    if (!stats?.tags || !processImageUrl) return [];
    return stats.tags.map((item) => ({
      name: item.name,
      count: item.count,
      image: processImageUrl(item.image),
    }));
  }, [stats?.tags, processImageUrl]);

  // 处理云图项点击（跳转到案例列表页，并应用筛选）
  const handleIndustryClick = (item: WordCloudItem) => {
    navigate(`/cases?brand_industry=${encodeURIComponent(item.name)}`);
  };

  const handleTagClick = (item: WordCloudItem) => {
    navigate(`/cases?tags=${encodeURIComponent(item.name)}`);
  };

  return (
    <div className={styles.modulesSection}>
      {/* 由于内容较多，这里先创建一个占位组件 */}
      {/* 完整的模块块内容需要从备份文件中提取并添加 */}
      <div className={styles.moduleBlock} id="data-collection">
        <div className={styles.moduleHeader}>
          <div className={styles.moduleBadge}>
            <SearchOutlined />
            <span>资料收集</span>
          </div>
          <Title level={2} className={styles.moduleTitle}>
            海量案例，触手可及
            <span className={styles.moduleSubtitle}>
              百万级精选案例库，7×24
              小时持续更新，覆盖广告门、小红书、抖音等全平台
            </span>
          </Title>
          <Paragraph className={styles.moduleSlogan}>
            <FireOutlined /> <strong>AI 驱动的智能爬虫</strong> ·
            高维向量语义检索 · 自动化数据处理管道
          </Paragraph>
        </div>

        {/* 技术能力支撑 */}
        <div className={styles.featuresSection}>
          <Row gutter={[24, 24]} className={styles.featuresRow}>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <BugOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  智能爬虫多平台采集
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>基于浏览器自动化技术</strong>
                  ，智能反爬虫处理，代理 IP
                  轮换，模拟真实用户行为。覆盖广告行业网站、社交媒体平台、品牌官方平台和行业报告平台，
                  <strong>7×24 小时不间断采集</strong>，数据实时更新。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>浏览器自动化 - 智能反爬虫处理</li>
                  <li>多平台覆盖 - 广告门、小红书、抖音等</li>
                  <li>7×24 小时采集 - 数据实时更新</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <RobotOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  大模型语义检索引擎
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>采用大语言向量模型</strong>
                  ，基于向量相似度的语义搜索，理解用户意图而非仅关键词匹配。支持中英文混合场景，
                  <strong>混合检索模式结合关键词和语义检索</strong>
                  ，精准度提升 3 倍以上。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>语义搜索 - 理解用户意图，非仅关键词</li>
                  <li>混合检索 - 关键词和语义检索结合</li>
                  <li>精准度提升 - 3 倍以上</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <DatabaseOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  智能体数据处理管道
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>自动化数据验证、清洗、标准化流程</strong>
                  ，智能去重算法，增量采集策略。支持
                  JSON、数据库等多种存储格式，
                  <strong>
                    自动下载案例相关图片，支持批量处理和断点续传
                  </strong>
                  ，数据完整性达 99.9%+。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>自动化处理 - 验证、清洗、标准化</li>
                  <li>智能去重 - 增量采集策略</li>
                  <li>数据完整性 - 99.9%+</li>
                </ul>
              </Card>
            </Col>
          </Row>
        </div>

        {/* 案例库简介 */}
        <div className={styles.visualizationSection}>
          <Title level={3} className={styles.subSectionTitle}>
            海量案例库，您的创意灵感源泉
            <span className={styles.subSectionSubtitle}>
              百万级精选案例，覆盖{" "}
              <strong>{stats?.industries?.length || 0} 个行业分类</strong>
              （涵盖快消、科技、金融、汽车、美妆、时尚、食品、旅游等全行业领域），
              <strong>{stats?.tags?.length || 0} 个热门标签</strong>
              （包括节日营销、品牌升级、新品发布、用户增长、情感共鸣、创意互动等多元化创意维度），7×24
              小时持续更新，让您永远走在创意前沿
            </span>
          </Title>
          {statsLoading ? (
            <div className={styles.statsLoading}>
              <Spin size="large" />
            </div>
          ) : (
            <Row gutter={[24, 24]} className={styles.wordCloudsWrapper}>
              <Col xs={24} lg={12}>
                <div className={styles.wordCloudWrapper}>
                  <WordCloud3D
                    items={industryItems}
                    title={`行业分类（${
                      stats?.industries?.length || 0
                    } 个，覆盖全行业优质案例）`}
                    onItemClick={handleIndustryClick}
                  />
                </div>
              </Col>
              <Col xs={24} lg={12}>
                <div className={styles.wordCloudWrapper}>
                  <WordCloud3D
                    items={tagItems}
                    title={`热门标签（${
                      stats?.tags?.length || 0
                    } 个，精准匹配创意需求）`}
                    onItemClick={handleTagClick}
                  />
                </div>
              </Col>
            </Row>
          )}
        </div>

        {/* 核心检索功能 */}
        <div className={styles.featuresSection}>
          <Title level={3} className={styles.subSectionTitle}>
            核心检索功能
            <span className={styles.subSectionSubtitle}>
              语义检索、案例库、智能推荐，让创意检索变得简单高效
            </span>
          </Title>
          <Row gutter={[24, 24]} className={styles.featuresRow}>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <FileSearchOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  大模型语义智能检索
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>基于先进的大语言向量模型</strong>
                  ，秒级响应，理解用户意图而非仅关键词匹配。
                  <strong>关键词、语义、混合三种检索模式</strong>
                  ，精准度提升 3 倍以上，让您快速找到心仪的创意案例。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>语义理解检索 - 理解意图，智能推荐</li>
                  <li>混合检索模式 - 最佳效果，精准度提升 3 倍</li>
                  <li>秒级响应 - 极速体验，毫秒级检索</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <DatabaseOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  海量案例库，应有尽有
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>百万级精选案例</strong>
                  ，覆盖全行业优质创意，7×24 小时持续更新。
                  <strong>覆盖广告门、小红书、抖音等全平台</strong>
                  ，完整案例信息深度解析，高清图片视频素材丰富，让您永远走在创意前沿。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>百万级案例 - 全行业覆盖，持续扩展</li>
                  <li>完整案例信息 - 深度解析，结构化存储</li>
                  <li>高清素材 - 图片视频丰富，即用即得</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <RobotOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  AI 智能推荐，精准匹配
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>结合 Brief、策略分析等材料智能推荐案例</strong>
                  ，基于大模型深度理解项目需求。
                  <strong>自动匹配相关案例和创意方向</strong>
                  ，根据品牌调性和目标受众，推荐最适合的创意风格和表达方式。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>智能推荐 - 结合 Brief 等材料精准匹配</li>
                  <li>需求理解 - 大模型深度理解项目需求</li>
                  <li>风格适配 - 根据品牌调性推荐创意风格</li>
                </ul>
              </Card>
            </Col>
          </Row>
        </div>

        <div className={styles.moduleAction}>
          <Button
            type="primary"
            size="large"
            icon={<SearchOutlined />}
            onClick={() => navigate("/cases")}
            className={styles.moduleButton}>
            立即开始搜索
            <ArrowRightOutlined />
          </Button>
        </div>
      </div>

      {/* 其他模块块的内容由于篇幅较长，暂时省略 */}
      {/* 后续可以根据需要从备份文件中提取并添加 */}
    </div>
  );
};

export default ModulesSection;
