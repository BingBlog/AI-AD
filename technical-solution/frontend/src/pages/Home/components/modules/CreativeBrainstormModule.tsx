/**
 * 创意脑暴模块
 */
import { Button, Card, Typography, Row, Col } from "antd";
import {
  BulbOutlined,
  ArrowRightOutlined,
  AppstoreOutlined,
  StarOutlined,
} from "@ant-design/icons";
import styles from "../../index.module.less";

const { Title, Paragraph } = Typography;

const CreativeBrainstormModule: React.FC = () => {
  return (
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
          <BulbOutlined /> <strong>AI 创意生成引擎</strong> · 大模型语义检索 ·
          智能体智能推荐系统
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
  );
};

export default CreativeBrainstormModule;
