/**
 * 竞标提案模块
 */
import { Button, Card, Typography, Row, Col } from "antd";
import {
  DollarOutlined,
  ArrowRightOutlined,
  FilePdfOutlined,
  RiseOutlined,
} from "@ant-design/icons";
import styles from "../../index.module.less";

const { Title, Paragraph } = Typography;

const ProposalBiddingModule: React.FC = () => {
  return (
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
          <DollarOutlined /> <strong>AI 提案生成引擎</strong> · 大模型知识推理
          · 智能体智能预算计算
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
  );
};

export default ProposalBiddingModule;
