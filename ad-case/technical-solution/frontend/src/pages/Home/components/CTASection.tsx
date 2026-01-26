/**
 * CTA 区域组件
 */
import { Button, Card, Typography, Space } from "antd";
import {
  SearchOutlined,
  CloudDownloadOutlined,
  ArrowRightOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import styles from "../index.module.less";

const { Title, Paragraph } = Typography;

const CTASection: React.FC = () => {
  const navigate = useNavigate();

  return (
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
  );
};

export default CTASection;
