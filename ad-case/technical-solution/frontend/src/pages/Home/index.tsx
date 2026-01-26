/**
 * 首页
 */
import { useMemo } from "react";
import { Button, Card, Typography, Space, Spin, Row, Col } from "antd";
import {
  SearchOutlined,
  AppstoreOutlined,
  FileSearchOutlined,
  CloudDownloadOutlined,
  ArrowRightOutlined,
  RocketOutlined,
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
            AI驱动的广告营销创意平台
            <span className={styles.heroSubtitle}>
              基于大模型、智能体、爬虫技术，让创意方案生成效率提升 5-10 倍
            </span>
          </Title>
          <Paragraph className={styles.heroDescription}>
            <strong>大模型能力</strong> · <strong>智能体自动化</strong> ·{" "}
            <strong>智能爬虫</strong>
            <br />从 Brief 解读到方案撰写，从创意脑暴到物料投放，全流程 AI 赋能
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

      {/* 完整工作流程 */}
      <div className={styles.workflowSection}>
        <div className={styles.workflowContainer}>
          <Title level={2} className={styles.sectionTitle}>
            一站式全流程赋能
            <span
              style={{
                display: "block",
                fontSize: "24px",
                fontWeight: 400,
                color: "#94a3b8",
                marginTop: "12px",
              }}>
              从 Brief 解读到物料投放，八步完成全流程，AI 赋能每一步
            </span>
          </Title>
          <Row gutter={[32, 40]} className={styles.workflowRow}>
            <Col xs={24} sm={12} md={6} lg={3}>
              <div
                className={styles.workflowStep}
                onClick={() => {
                  const element = document.getElementById("brief-analysis");
                  element?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                  });
                }}>
                <div className={styles.stepNumber}>1</div>
                <Title level={3} className={styles.stepTitle}>
                  Brief解读
                </Title>
                <div className={styles.stepCoreFeature}>多模态 AI 文档解析</div>
                <div className={styles.stepComparison}>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>传统时代：</span>
                    <span className={styles.comparisonText}>
                      人工逐字阅读，耗时数小时
                    </span>
                  </div>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>AI 时代：</span>
                    <span className={styles.comparisonText}>
                      AI 多模态解析，快速完成
                    </span>
                  </div>
                </div>
                <Paragraph className={styles.stepDescription}>
                  支持 PDF、Word、Excel、PPT 等多种格式
                </Paragraph>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6} lg={3}>
              <div
                className={styles.workflowStep}
                onClick={() => {
                  const element = document.getElementById("data-collection");
                  element?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                  });
                }}>
                <div className={styles.stepNumber}>2</div>
                <Title level={3} className={styles.stepTitle}>
                  资料收集
                </Title>
                <div className={styles.stepCoreFeature}>
                  智能爬虫 + 语义检索
                </div>
                <div className={styles.stepComparison}>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>传统时代：</span>
                    <span className={styles.comparisonText}>
                      手动搜索，效率低，覆盖不全
                    </span>
                  </div>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>AI 时代：</span>
                    <span className={styles.comparisonText}>
                      智能爬虫 + 语义检索，百万级案例库
                    </span>
                  </div>
                </div>
                <Paragraph className={styles.stepDescription}>
                  7×24 小时自动采集，全平台覆盖
                </Paragraph>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6} lg={3}>
              <div
                className={styles.workflowStep}
                onClick={() => {
                  const element = document.getElementById("strategy-analysis");
                  element?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                  });
                }}>
                <div className={styles.stepNumber}>3</div>
                <Title level={3} className={styles.stepTitle}>
                  策略分析
                </Title>
                <div className={styles.stepCoreFeature}>
                  大模型知识推理 + 智能体自动化分析
                </div>
                <div className={styles.stepComparison}>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>传统时代：</span>
                    <span className={styles.comparisonText}>
                      依赖经验，主观性强
                    </span>
                  </div>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>AI 时代：</span>
                    <span className={styles.comparisonText}>
                      大模型知识推理，五维度洞察
                    </span>
                  </div>
                </div>
                <Paragraph className={styles.stepDescription}>
                  快速完成策略制定，数据驱动决策
                </Paragraph>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6} lg={3}>
              <div
                className={styles.workflowStep}
                onClick={() => {
                  const element = document.getElementById(
                    "creative-brainstorm"
                  );
                  element?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                  });
                }}>
                <div className={styles.stepNumber}>4</div>
                <Title level={3} className={styles.stepTitle}>
                  创意脑暴
                </Title>
                <div className={styles.stepCoreFeature}>
                  大模型内容生成 + 语义检索
                </div>
                <div className={styles.stepComparison}>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>传统时代：</span>
                    <span className={styles.comparisonText}>
                      靠灵感，方向单一
                    </span>
                  </div>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>AI 时代：</span>
                    <span className={styles.comparisonText}>
                      AI 创意生成，快速产出多个方向
                    </span>
                  </div>
                </div>
                <Paragraph className={styles.stepDescription}>
                  结合海量案例库，多元化创意灵感
                </Paragraph>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6} lg={3}>
              <div
                className={styles.workflowStep}
                onClick={() => {
                  const element = document.getElementById("proposal-writing");
                  element?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                  });
                }}>
                <div className={styles.stepNumber}>5</div>
                <Title level={3} className={styles.stepTitle}>
                  方案撰写
                </Title>
                <div className={styles.stepCoreFeature}>
                  大模型内容生成 + 智能体报告生成
                </div>
                <div className={styles.stepComparison}>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>传统时代：</span>
                    <span className={styles.comparisonText}>
                      重复劳动，1-2 周完成
                    </span>
                  </div>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>AI 时代：</span>
                    <span className={styles.comparisonText}>
                      智能体自动生成，快速完成
                    </span>
                  </div>
                </div>
                <Paragraph className={styles.stepDescription}>
                  自动生成完整整合营销全案
                </Paragraph>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6} lg={3}>
              <div
                className={styles.workflowStep}
                onClick={() => {
                  const element = document.getElementById("proposal-bidding");
                  element?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                  });
                }}>
                <div className={styles.stepNumber}>6</div>
                <Title level={3} className={styles.stepTitle}>
                  竞标提案
                </Title>
                <div className={styles.stepCoreFeature}>
                  大模型内容生成 + 智能体智能预算计算
                </div>
                <div className={styles.stepComparison}>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>传统时代：</span>
                    <span className={styles.comparisonText}>
                      预算计算易出错，反复核对
                    </span>
                  </div>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>AI 时代：</span>
                    <span className={styles.comparisonText}>
                      智能体智能预算计算，自动生成明细
                    </span>
                  </div>
                </div>
                <Paragraph className={styles.stepDescription}>
                  快速完成专业竞标提案，准确无误
                </Paragraph>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6} lg={3}>
              <div
                className={styles.workflowStep}
                onClick={() => {
                  const element = document.getElementById("material-design");
                  element?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                  });
                }}>
                <div className={styles.stepNumber}>7</div>
                <Title level={3} className={styles.stepTitle}>
                  物料设计
                </Title>
                <div className={styles.stepCoreFeature}>
                  大模型内容生成 + 语义检索参考案例
                </div>
                <div className={styles.stepComparison}>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>传统时代：</span>
                    <span className={styles.comparisonText}>
                      沟通成本高，反复修改
                    </span>
                  </div>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>AI 时代：</span>
                    <span className={styles.comparisonText}>
                      语义检索参考案例，快速生成设计规范
                    </span>
                  </div>
                </div>
                <Paragraph className={styles.stepDescription}>
                  快速完成设计需求文档，减少沟通成本
                </Paragraph>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6} lg={3}>
              <div
                className={styles.workflowStep}
                onClick={() => {
                  const element = document.getElementById("material-delivery");
                  element?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                  });
                }}>
                <div className={styles.stepNumber}>8</div>
                <Title level={3} className={styles.stepTitle}>
                  物料投放
                </Title>
                <div className={styles.stepCoreFeature}>
                  大模型知识推理 + 智能体智能合规检查
                </div>
                <div className={styles.stepComparison}>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>传统时代：</span>
                    <span className={styles.comparisonText}>
                      制定繁琐，合规风险高
                    </span>
                  </div>
                  <div className={styles.comparisonItem}>
                    <span className={styles.comparisonLabel}>AI 时代：</span>
                    <span className={styles.comparisonText}>
                      智能体智能合规检查，自动生成投放计划
                    </span>
                  </div>
                </div>
                <Paragraph className={styles.stepDescription}>
                  快速完成投放计划制定，降低合规风险
                </Paragraph>
              </div>
            </Col>
          </Row>
        </div>
      </div>

      {/* 核心功能板块 */}
      <div className={styles.modulesSection}>
        {/* 1. 资料收集板块 */}
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

        {/* 2. Brief解读板块 */}
        <div className={styles.moduleBlock} id="brief-analysis">
          <div className={styles.moduleHeader}>
            <div className={styles.moduleBadge}>
              <FileTextOutlined />
              <span>Brief解读</span>
            </div>
            <Title level={2} className={styles.moduleTitle}>
              AI 秒懂 Brief，创意秒生成
              <span className={styles.moduleSubtitle}>
                多模态文档智能解析，数分钟完成 Brief 解读，自动化程度达 80%+
              </span>
            </Title>
            <Paragraph className={styles.moduleSlogan}>
              <StarOutlined /> <strong>多模态 AI 文档解析</strong> ·
              大模型深度理解 · 智能体工作流引擎
            </Paragraph>
          </div>

          {/* 核心功能 */}
          <Row gutter={[24, 24]} className={styles.featuresRow}>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <FileTextOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  智能体多模态文档处理
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>
                    支持 PDF、Word、Excel、PPT、图片、音频、视频等 10+ 种格式
                  </strong>
                  ，基于 OCR、ASR、图像识别等 AI
                  技术，自动提取文本、表格、图表、图片等结构化信息。
                  <strong>文档质量智能检测</strong>
                  ，识别清晰度、完整性、可读性，确保解析质量。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>多格式支持 - 10+ 种文档格式智能解析</li>
                  <li>AI 技术提取 - OCR、ASR、图像识别</li>
                  <li>质量检测 - 清晰度、完整性、可读性</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <RobotOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  大模型智能解读引擎
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>基于大语言模型的深度语义理解</strong>
                  ，自动提取九大核心信息（背景、目标、任务等），深层需求挖掘和痛点识别。
                  <strong>
                    自动识别 Point A（现状）和 Point B（目标）的转变路径
                  </strong>
                  ，生成结构化分析报告。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>深度语义理解 - 大语言模型驱动</li>
                  <li>九大核心信息 - 自动提取和结构化</li>
                  <li>需求挖掘 - 深层痛点和需求识别</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <ApiOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  智能体智能工作流引擎
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>
                    基于标准化流程（Brief 解读六步法）自动编排工作流
                  </strong>
                  ，每个节点的输入输出验证和状态跟踪。
                  <strong>异常情况自动识别和预警</strong>
                  ，支持人工干预和协同工作，版本管理和修改历史追踪。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>自动编排工作流 - 标准化流程</li>
                  <li>节点验证跟踪 - 输入输出验证</li>
                  <li>异常处理 - 自动识别和预警</li>
                </ul>
              </Card>
            </Col>
          </Row>

          <div className={styles.moduleAction}>
            <Button
              size="large"
              icon={<FileTextOutlined />}
              onClick={() => {
                console.log("跳转到brief解读");
              }}
              className={styles.moduleButtonSecondary}>
              开始Brief解读
              <ArrowRightOutlined />
            </Button>
          </div>
        </div>

        {/* 3. 策略分析板块 */}
        <div className={styles.moduleBlock} id="strategy-analysis">
          <div className={styles.moduleHeader}>
            <div className={styles.moduleBadge}>
              <BarChartOutlined />
              <span>策略分析</span>
            </div>
            <Title level={2} className={styles.moduleTitle}>
              洞察无限，策略有方
              <span className={styles.moduleSubtitle}>
                AI 驱动的五维度洞察分析，1-2 天完成策略制定，效率提升 5-10 倍
              </span>
            </Title>
            <Paragraph className={styles.moduleSlogan}>
              <BarChartOutlined /> <strong>AI 驱动的五维度洞察</strong> ·
              大模型知识推理 · 智能体自动化分析引擎
            </Paragraph>
          </div>

          {/* 核心功能 */}
          <Row gutter={[24, 24]} className={styles.featuresRow}>
            <Col xs={24} sm={12} lg={12}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <BarChartOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  大模型五维度洞察分析
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>基于大语言模型的深度知识推理</strong>
                  ，自动生成 PEST+SWOT
                  分析框架。覆盖环境洞察（政治、经济、社会、技术）、行业洞察、企业洞察、竞品洞察、消费者洞察五大维度。
                  <strong>智能对比分析竞品策略和差异化定位</strong>
                  ，量化评估项目风险和可行性。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>五维度洞察 - 环境、行业、企业、竞品、消费者</li>
                  <li>PEST+SWOT 分析 - 自动生成分析框架</li>
                  <li>竞品分析 - 智能对比和差异化定位</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={12}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <RobotOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  智能体自动化策略制定
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>基于 NLP 技术自动提取和分析关键信息</strong>
                  ，确定"对谁说"、"说什么"、"怎么说"三大核心策略。
                  <strong>自动生成多维度洞察结论和策略建议</strong>
                  ，基于数据驱动的决策支持，生成专业报告（PDF、Word、PPT
                  等格式）。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>NLP 信息提取 - 自动提取关键信息</li>
                  <li>三大核心策略 - 对谁说、说什么、怎么说</li>
                  <li>专业报告生成 - PDF、Word、PPT 等格式</li>
                </ul>
              </Card>
            </Col>
          </Row>

          <div className={styles.moduleAction}>
            <Button
              size="large"
              icon={<BarChartOutlined />}
              onClick={() => {
                console.log("跳转到策略分析");
              }}
              className={styles.moduleButtonSecondary}>
              开始策略分析
              <ArrowRightOutlined />
            </Button>
          </div>
        </div>

        {/* 4. 创意脑暴板块 */}
        <div className={styles.moduleBlock} id="creative-brainstorm">
          <div className={styles.moduleHeader}>
            <div className={styles.moduleBadge}>
              <BulbOutlined />
              <span>创意脑暴</span>
            </div>
            <Title level={2} className={styles.moduleTitle}>
              创意无限，灵感迸发
              <span className={styles.moduleSubtitle}>
                AI 创意生成引擎，数小时完成创意脑暴，快速生成多个创意方向
              </span>
            </Title>
            <Paragraph className={styles.moduleSlogan}>
              <BulbOutlined /> <strong>AI 创意生成引擎</strong> · 大模型语义检索
              · 智能体智能推荐系统
            </Paragraph>
          </div>

          {/* 核心功能 */}
          <Row gutter={[24, 24]} className={styles.featuresRow}>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <BulbOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  大模型核心概念生成
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>基于策略分析自动生成核心创意主题（Big Idea）</strong>
                  ，生成多个创意方向和执行细节，提供丰富的创意选择。
                  <strong>基于行业最佳实践和成功案例</strong>
                  ，生成主广告语、故事脚本等，智能推荐适配的内容形式和风格。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>核心概念生成 - Big Idea 自动提炼</li>
                  <li>多方向创意 - 丰富的创意选择</li>
                  <li>智能推荐 - 适配的内容形式和风格</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <AppstoreOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  语义检索创意灵感库
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>基于向量相似度的语义检索</strong>
                  ，快速找到相似成功案例，为创意提供参考和灵感。
                  <strong>智能分析案例的创意形式、风格特点</strong>
                  ，辅助创意方向选择，支持短视频、图文、H5、直播等多种内容形式。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>语义检索 - 向量相似度匹配</li>
                  <li>案例分析 - 创意形式和风格分析</li>
                  <li>多形式支持 - 短视频、图文、H5、直播</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <StarOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  智能体智能推荐系统
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>基于历史数据和用户行为智能推荐</strong>
                  ，相关创意案例和策略自动匹配。
                  <strong>根据品牌调性和目标受众</strong>
                  ，推荐最适合的创意风格和表达方式，支持幽默、情感、故事、反差、新奇、UGC
                  等多种风格。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>智能推荐 - 基于历史数据和用户行为</li>
                  <li>自动匹配 - 创意案例和策略匹配</li>
                  <li>多风格支持 - 幽默、情感、故事等</li>
                </ul>
              </Card>
            </Col>
          </Row>

          <div className={styles.moduleAction}>
            <Button
              size="large"
              icon={<BulbOutlined />}
              onClick={() => {
                console.log("跳转到创意脑暴");
              }}
              className={styles.moduleButtonSecondary}>
              开始创意脑暴
              <ArrowRightOutlined />
            </Button>
          </div>
        </div>

        {/* 5. 方案撰写板块 */}
        <div className={styles.moduleBlock} id="proposal-writing">
          <div className={styles.moduleHeader}>
            <div className={styles.moduleBadge}>
              <FilePdfOutlined />
              <span>方案撰写</span>
            </div>
            <Title level={2} className={styles.moduleTitle}>
              方案一键生成，专业即得
              <span className={styles.moduleSubtitle}>
                AI 全案生成引擎，1-2 天完成方案撰写，效率提升 5-10 倍
              </span>
            </Title>
            <Paragraph className={styles.moduleSlogan}>
              <FilePdfOutlined /> <strong>AI 全案生成引擎</strong> · 智能体
              报告生成 · 智能方案优化
            </Paragraph>
          </div>

          {/* 核心功能 */}
          <Row gutter={[24, 24]} className={styles.featuresRow}>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <FilePdfOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  大模型整合营销全案生成
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>自动生成完整的整合营销传播全案文档</strong>
                  ，包含简报、洞察、策略、概念、创意、媒介、排期、效果、预算等所有标准模块。
                  <strong>基于行业最佳实践优化方案结构和表达逻辑</strong>
                  ，智能生成视觉化内容描述，支持信息图和图表生成。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>全案文档生成 - 包含所有标准模块</li>
                  <li>方案优化 - 基于行业最佳实践</li>
                  <li>视觉化内容 - 信息图和图表生成</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <BarChartOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  智能体报告生成引擎
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>基于分析结果动态生成专业报告</strong>
                  （PPT、PDF、Word 等格式），标准化报告模板和自定义模板支持。
                  <strong>自动生成图表、仪表板等可视化内容</strong>
                  ，使用信息图、图表等可视化方式呈现方案，增强视觉冲击力。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>多格式报告 - PPT、PDF、Word 等</li>
                  <li>模板支持 - 标准化和自定义模板</li>
                  <li>可视化内容 - 图表、仪表板自动生成</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <StarOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  智能体工作流整合引擎
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>自动整合前述步骤的所有输出</strong>
                  ，形成完整方案，确保方案结构完整性和逻辑一致性。
                  <strong>版本管理和修改历史追踪</strong>
                  ，自动引用第三方数据支撑结论，增强方案的专业性和说服力。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>自动整合 - 所有步骤输出整合</li>
                  <li>版本管理 - 修改历史追踪</li>
                  <li>数据支撑 - 自动引用第三方数据</li>
                </ul>
              </Card>
            </Col>
          </Row>

          <div className={styles.moduleAction}>
            <Button
              size="large"
              icon={<FilePdfOutlined />}
              onClick={() => {
                console.log("跳转到方案撰写");
              }}
              className={styles.moduleButtonSecondary}>
              开始方案撰写
              <ArrowRightOutlined />
            </Button>
          </div>
        </div>

        {/* 6. 竞标提案板块 */}
        <div className={styles.moduleBlock} id="proposal-bidding">
          <div className={styles.moduleHeader}>
            <div className={styles.moduleBadge}>
              <DollarOutlined />
              <span>竞标提案</span>
            </div>
            <Title level={2} className={styles.moduleTitle}>
              提案秒出，胜券在握
              <span className={styles.moduleSubtitle}>
                AI 提案生成引擎，半天完成竞标提案，效率提升 6-10 倍
              </span>
            </Title>
            <Paragraph className={styles.moduleSlogan}>
              <DollarOutlined /> <strong>AI 提案生成引擎</strong> ·
              大模型知识推理 · 智能体智能预算计算
            </Paragraph>
          </div>

          {/* 核心功能 */}
          <Row gutter={[24, 24]} className={styles.featuresRow}>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <FilePdfOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  大模型提案包装引擎
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>自动将方案转化为专业的竞标提案文档</strong>
                  ，智能生成公司介绍、案例展示、团队介绍等内容。
                  <strong>自动突出方案亮点和竞争优势</strong>
                  ，增强差异化呈现，支持 PPT、PDF 等多种格式导出。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>提案文档生成 - 自动转化为专业文档</li>
                  <li>内容智能生成 - 公司介绍、案例展示</li>
                  <li>多格式导出 - PPT、PDF 等格式</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <DollarOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  智能体智能预算计算
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>
                    基于行业标准和历史数据，智能生成合理的预算分配建议
                  </strong>
                  。自动生成预算明细表，包含各项费用拆分（内容制作、渠道投放、KOL
                  合作等）、折扣和税费计算，
                  <strong>减少人工计算错误，提高准确性</strong>。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>智能预算分配 - 基于行业标准和历史数据</li>
                  <li>预算明细表 - 自动生成，包含折扣和税费</li>
                  <li>准确性提升 - 减少人工计算错误</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <RiseOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  大模型知识推理 KPI
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>基于案例库数据，生成可信的效果承诺和 KPI 指标</strong>
                  。智能生成 KPI
                  指标和预期效果描述，设定清晰的营销目标和传播目标，包括曝光量、点击率、转化率、ROI
                  等指标。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>KPI 指标生成 - 基于案例库数据</li>
                  <li>效果承诺 - 可信的预期效果</li>
                  <li>多维度指标 - 曝光量、点击率、转化率、ROI</li>
                </ul>
              </Card>
            </Col>
          </Row>

          <div className={styles.moduleAction}>
            <Button
              size="large"
              icon={<DollarOutlined />}
              onClick={() => {
                console.log("跳转到竞标提案");
              }}
              className={styles.moduleButtonSecondary}>
              开始竞标提案
              <ArrowRightOutlined />
            </Button>
          </div>
        </div>

        {/* 7. 物料设计板块 */}
        <div className={styles.moduleBlock} id="material-design">
          <div className={styles.moduleHeader}>
            <div className={styles.moduleBadge}>
              <PictureOutlined />
              <span>物料设计</span>
            </div>
            <Title level={2} className={styles.moduleTitle}>
              设计规范，一键生成
              <span className={styles.moduleSubtitle}>
                AI 设计规范生成，数小时完成设计需求文档，效率提升 3-5 倍
              </span>
            </Title>
            <Paragraph className={styles.moduleSlogan}>
              <PictureOutlined /> <strong>AI 设计规范生成</strong> ·
              大模型语义检索 · 智能体自动化生成
            </Paragraph>
          </div>

          {/* 核心功能 */}
          <Row gutter={[24, 24]} className={styles.featuresRow}>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <PictureOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  大模型设计规范生成
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>基于品牌调性和创意方案，自动生成视觉设计规范</strong>
                  ，智能生成色彩、字体、版式规范建议。
                  <strong>自动生成设计需求文档</strong>
                  ，包含完整的视觉风格指引、色彩、字体、版式规范、尺寸规格要求、文案内容和参考案例。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>设计规范生成 - 基于品牌调性和创意方案</li>
                  <li>需求文档生成 - 完整的视觉风格指引</li>
                  <li>规范建议 - 色彩、字体、版式规范</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <FileTextOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  语义检索参考案例库
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>基于语义检索快速找到相关参考案例</strong>
                  ，为设计提供灵感。
                  <strong>智能分析成功案例的设计风格和元素</strong>
                  ，辅助设计规范制定，支持多维度检索和引用，减少设计师与策略团队的沟通成本。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>语义检索 - 快速找到相关参考案例</li>
                  <li>风格分析 - 智能分析设计风格和元素</li>
                  <li>沟通成本 - 减少反复沟通</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <ExperimentOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  智能体自动化物料生成
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>根据媒介规划自动生成物料清单</strong>
                  ，包含尺寸规格要求。
                  <strong>支持基于设计规范生成初步设计稿</strong>
                  （可选功能），加速设计迭代，支持海报、视频、H5、落地页等多种物料类型。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>物料清单生成 - 根据媒介规划自动生成</li>
                  <li>初步设计稿 - 基于设计规范生成（可选）</li>
                  <li>多物料类型 - 海报、视频、H5、落地页</li>
                </ul>
              </Card>
            </Col>
          </Row>

          <div className={styles.moduleAction}>
            <Button
              size="large"
              icon={<PictureOutlined />}
              onClick={() => {
                console.log("跳转到物料设计");
              }}
              className={styles.moduleButtonSecondary}>
              开始物料设计
              <ArrowRightOutlined />
            </Button>
          </div>
        </div>

        {/* 8. 物料投放板块 */}
        <div className={styles.moduleBlock} id="material-delivery">
          <div className={styles.moduleHeader}>
            <div className={styles.moduleBadge}>
              <SendOutlined />
              <span>物料投放</span>
            </div>
            <Title level={2} className={styles.moduleTitle}>
              投放策略，智能规划
              <span className={styles.moduleSubtitle}>
                AI 投放策略引擎，半天完成投放计划制定，效率提升 4-6 倍
              </span>
            </Title>
            <Paragraph className={styles.moduleSlogan}>
              <SendOutlined /> <strong>AI 投放策略引擎</strong> · 智能体
              自动化生成 · 智能合规检查
            </Paragraph>
          </div>

          {/* 核心功能 */}
          <Row gutter={[24, 24]} className={styles.featuresRow}>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <BarChartOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  大模型投放策略规划
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>基于历史数据和案例库，智能推荐渠道组合策略</strong>
                  （自有媒体、付费媒体、赢得媒体）。
                  <strong>智能生成投放节奏规划</strong>
                  （预热期、爆发期、持续期），基于数据驱动的预算分配建议，自动生成投放计划表（甘特图）。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>渠道组合策略 - 智能推荐自有、付费、赢得媒体</li>
                  <li>投放节奏规划 - 预热期、爆发期、持续期</li>
                  <li>投放计划表 - 自动生成甘特图</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <SafetyOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  智能体智能合规检查
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>自动检查广告法合规性，避免违规内容</strong>
                  。基于规则引擎和知识库，识别潜在合规风险，
                  <strong>生成各渠道的投放需求文档</strong>
                  ，提供合规性检查报告，降低违规风险，避免法律问题。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>合规性检查 - 自动检查广告法合规</li>
                  <li>风险识别 - 基于规则引擎和知识库</li>
                  <li>合规报告 - 降低违规风险</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <RiseOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  智能体效果监测优化
                </Title>
                <Paragraph className={styles.featureDescription}>
                  <strong>自动生成数据监测模板</strong>
                  ，支持实时数据分析，设定监测指标（曝光量、点击率、转化率、ROI
                  等）。<strong>基于历史投放数据和效果，提供优化建议</strong>
                  ，智能推荐最佳投放时机和渠道组合，持续优化投放效果和 ROI。
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>数据监测模板 - 自动生成，实时分析</li>
                  <li>优化建议 - 基于历史数据和效果</li>
                  <li>持续优化 - 智能推荐最佳时机和渠道</li>
                </ul>
              </Card>
            </Col>
          </Row>

          <div className={styles.moduleAction}>
            <Button
              size="large"
              icon={<SendOutlined />}
              onClick={() => {
                console.log("跳转到物料投放");
              }}
              className={styles.moduleButtonSecondary}>
              开始物料投放
              <ArrowRightOutlined />
            </Button>
          </div>
        </div>

        {/* 创意设计板块（保留原有，但简化） */}
        <div className={styles.moduleBlock} id="creative-design">
          <div className={styles.moduleHeader}>
            <div className={styles.moduleBadge}>
              <BulbOutlined />
              <span>创意设计</span>
            </div>
            <Title level={2} className={styles.moduleTitle}>
              灵感无限，设计无界
              <span className={styles.moduleSubtitle}>
                从概念到视觉，AI助力你的每一个创意想法落地成真
              </span>
            </Title>
            <Paragraph className={styles.moduleSlogan}>
              <ExperimentOutlined /> <strong>AI辅助设计</strong> · 灵感激发 ·
              快速迭代
            </Paragraph>
          </div>

          <Row gutter={[24, 24]} className={styles.featuresRow}>
            <Col xs={24} sm={12} lg={12}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <BulbOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  创意灵感生成
                </Title>
                <Paragraph className={styles.featureDescription}>
                  输入关键词或描述，AI生成多种创意方向和视觉风格，激发无限灵感
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>AI 创意生成 - 多种创意方向</li>
                  <li>视觉风格 - 自动生成视觉风格</li>
                  <li>灵感激发 - 无限创意可能</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={12}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <AppstoreOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  设计方案优化
                </Title>
                <Paragraph className={styles.featureDescription}>
                  基于案例库最佳实践，智能优化设计方案，让创意更符合市场趋势
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>最佳实践 - 基于案例库</li>
                  <li>智能优化 - 设计方案优化</li>
                  <li>市场趋势 - 符合市场趋势</li>
                </ul>
              </Card>
            </Col>
          </Row>

          <div className={styles.moduleAction}>
            <Button
              size="large"
              icon={<BulbOutlined />}
              onClick={() => {
                console.log("跳转到创意设计");
              }}
              className={styles.moduleButtonSecondary}>
              开始创意设计
              <ArrowRightOutlined />
            </Button>
          </div>
        </div>

        {/* 物料生成板块 */}
        <div className={styles.moduleBlock} id="material-generation">
          <div className={styles.moduleHeader}>
            <div className={styles.moduleBadge}>
              <PictureOutlined />
              <span>物料生成</span>
            </div>
            <Title level={2} className={styles.moduleTitle}>
              一键生成，秒出物料
              <span className={styles.moduleSubtitle}>
                从文案到视觉，从海报到视频，AI帮你快速产出高质量营销物料
              </span>
            </Title>
            <Paragraph className={styles.moduleSlogan}>
              <RocketOutlined /> <strong>智能生成</strong> · 批量产出 · 即用即得
            </Paragraph>
          </div>

          <Row gutter={[24, 24]} className={styles.featuresRow}>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <PictureOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  海报设计
                </Title>
                <Paragraph className={styles.featureDescription}>
                  输入主题和风格，AI自动生成多款海报设计，支持多种尺寸和格式
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>AI 海报生成 - 多款设计自动生成</li>
                  <li>多尺寸支持 - 支持多种尺寸和格式</li>
                  <li>主题风格 - 输入主题和风格即可</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <FileTextOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  文案创作
                </Title>
                <Paragraph className={styles.featureDescription}>
                  基于品牌调性和目标受众，AI生成多套文案方案，涵盖标题、正文、Slogan
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>多套文案方案 - AI 自动生成</li>
                  <li>品牌调性 - 基于品牌调性生成</li>
                  <li>完整文案 - 标题、正文、Slogan</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <Card className={styles.featureCard} hoverable>
                <div className={styles.featureIcon}>
                  <RocketOutlined />
                </div>
                <Title level={4} className={styles.featureTitle}>
                  批量生成
                </Title>
                <Paragraph className={styles.featureDescription}>
                  一次配置，批量生成多种物料，支持多平台适配，大幅提升工作效率
                </Paragraph>
                <ul className={styles.featureList}>
                  <li>批量生成 - 一次配置，批量产出</li>
                  <li>多平台适配 - 支持多平台适配</li>
                  <li>效率提升 - 大幅提升工作效率</li>
                </ul>
              </Card>
            </Col>
          </Row>

          <div className={styles.moduleAction}>
            <Button
              size="large"
              icon={<PictureOutlined />}
              onClick={() => {
                console.log("跳转到物料生成");
              }}
              className={styles.moduleButtonSecondary}>
              开始生成物料
              <ArrowRightOutlined />
            </Button>
          </div>
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

      {/* 核心技术能力板块 */}
      <div className={styles.techCapabilitiesSection}>
        <div className={styles.techCapabilitiesContainer}>
          <div className={styles.sectionHeader}>
            <Title level={2} className={styles.sectionTitle}>
              核心技术能力
              <span className={styles.sectionSubtitle}>
                三大核心技术，为平台功能提供语义理解、工作流编排、数据采集等核心能力
              </span>
            </Title>
          </div>
          <Row gutter={[32, 32]} className={styles.techCapabilitiesRow}>
            <Col xs={24} md={8}>
              <Card className={styles.techCapabilityCard} hoverable>
                <div className={styles.techCapabilityIcon}>
                  <RobotOutlined />
                </div>
                <Title level={3} className={styles.techCapabilityTitle}>
                  大模型能力
                </Title>
                <Paragraph className={styles.techCapabilityDescription}>
                  使用大语言模型进行语义理解与检索
                </Paragraph>
                <ul className={styles.techCapabilityList}>
                  <li>语义理解与检索 - 高维向量模型</li>
                  <li>内容生成与优化 - 智能解读、策略分析</li>
                  <li>知识推理与决策 - 需求挖掘、风险评估</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card className={styles.techCapabilityCard} hoverable>
                <div className={styles.techCapabilityIcon}>
                  <ApiOutlined />
                </div>
                <Title level={3} className={styles.techCapabilityTitle}>
                  智能体能力
                </Title>
                <Paragraph className={styles.techCapabilityDescription}>
                  智能工作流引擎、多模态文档处理、自动化分析引擎
                </Paragraph>
                <ul className={styles.techCapabilityList}>
                  <li>智能工作流引擎 - 自动编排、节点控制</li>
                  <li>多模态文档处理 - PDF、Word、Excel 等</li>
                  <li>自动化分析引擎 - NLP 信息提取</li>
                </ul>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card className={styles.techCapabilityCard} hoverable>
                <div className={styles.techCapabilityIcon}>
                  <BugOutlined />
                </div>
                <Title level={3} className={styles.techCapabilityTitle}>
                  爬虫能力
                </Title>
                <Paragraph className={styles.techCapabilityDescription}>
                  多平台数据采集、智能爬取策略、数据处理管道
                </Paragraph>
                <ul className={styles.techCapabilityList}>
                  <li>多平台数据采集 - 广告门、小红书等</li>
                  <li>智能爬取策略 - 反爬虫处理、代理轮换</li>
                  <li>数据处理管道 - 验证、清洗、存储</li>
                </ul>
              </Card>
            </Col>
          </Row>
        </div>
      </div>
    </div>
  );
};

export default Home;
