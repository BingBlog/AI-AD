/**
 * Brief解读模块
 */
import { Button, Card, Typography, Row, Col } from "antd";
import {
  FileTextOutlined,
  ArrowRightOutlined,
  RobotOutlined,
  ApiOutlined,
  StarOutlined,
} from "@ant-design/icons";
import styles from "../../index.module.less";

const { Title, Paragraph } = Typography;

const BriefAnalysisModule: React.FC = () => {
  return (
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
  );
};

export default BriefAnalysisModule;
