/**
 * 方案撰写模块
 */
import { Button, Card, Typography, Row, Col } from "antd";
import {
  FilePdfOutlined,
  ArrowRightOutlined,
  BarChartOutlined,
  StarOutlined,
} from "@ant-design/icons";
import styles from "../../index.module.less";

const { Title, Paragraph } = Typography;

const ProposalWritingModule: React.FC = () => {
  return (
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
  );
};

export default ProposalWritingModule;
