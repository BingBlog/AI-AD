/**
 * 物料投放模块
 */
import { Button, Card, Typography, Row, Col } from "antd";
import {
  SendOutlined,
  ArrowRightOutlined,
  BarChartOutlined,
  SafetyOutlined,
  RiseOutlined,
} from "@ant-design/icons";
import styles from "../../index.module.less";

const { Title, Paragraph } = Typography;

const MaterialDeliveryModule: React.FC = () => {
  return (
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
          <SendOutlined /> <strong>AI 投放策略引擎</strong> · 智能体 自动化生成
          · 智能合规检查
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
  );
};

export default MaterialDeliveryModule;
