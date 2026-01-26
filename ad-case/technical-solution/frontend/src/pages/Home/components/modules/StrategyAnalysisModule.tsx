/**
 * 策略分析模块
 */
import { Button, Card, Typography, Row, Col } from "antd";
import {
  BarChartOutlined,
  ArrowRightOutlined,
  RobotOutlined,
} from "@ant-design/icons";
import styles from "../../index.module.less";

const { Title, Paragraph } = Typography;

const StrategyAnalysisModule: React.FC = () => {
  return (
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
              ，基于数据驱动的决策支持，生成专业报告（PDF、Word、PPT 等格式）。
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
  );
};

export default StrategyAnalysisModule;
