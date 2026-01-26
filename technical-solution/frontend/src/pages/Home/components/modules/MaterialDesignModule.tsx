/**
 * 物料设计模块
 */
import { Button, Card, Typography, Row, Col } from "antd";
import {
  PictureOutlined,
  ArrowRightOutlined,
  FileTextOutlined,
  ExperimentOutlined,
} from "@ant-design/icons";
import styles from "../../index.module.less";

const { Title, Paragraph } = Typography;

const MaterialDesignModule: React.FC = () => {
  return (
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
  );
};

export default MaterialDesignModule;
