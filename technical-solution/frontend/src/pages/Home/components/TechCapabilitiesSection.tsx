/**
 * 核心技术能力板块组件
 */
import { Card, Typography, Row, Col } from "antd";
import { RobotOutlined, ApiOutlined, BugOutlined } from "@ant-design/icons";
import styles from "../index.module.less";

const { Title, Paragraph } = Typography;

const TechCapabilitiesSection: React.FC = () => {
  return (
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
  );
};

export default TechCapabilitiesSection;
