/**
 * 首页
 */
import { Button, Card, Typography, Space } from 'antd';
import { SearchOutlined, AppstoreOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import styles from './index.module.less';

const { Title, Paragraph } = Typography;

const Home: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className={styles.home}>
      <div className={styles.hero}>
        <Title level={1}>广告案例库</Title>
        <Paragraph className={styles.description}>
          快速检索和浏览优质广告创意案例，为您的方案设计提供灵感
        </Paragraph>
        <Space size="large">
          <Button
            type="primary"
            size="large"
            icon={<SearchOutlined />}
            onClick={() => navigate('/cases')}
          >
            开始检索
          </Button>
          <Button
            size="large"
            icon={<AppstoreOutlined />}
            onClick={() => navigate('/cases')}
          >
            浏览案例
          </Button>
        </Space>
      </div>

      <div className={styles.features}>
        <Card title="快速检索" className={styles.featureCard}>
          <Paragraph>支持关键词搜索、多维度筛选，快速找到相关案例</Paragraph>
        </Card>
        <Card title="丰富案例" className={styles.featureCard}>
          <Paragraph>涵盖多个行业和品牌的优质广告创意案例</Paragraph>
        </Card>
        <Card title="详细信息" className={styles.featureCard}>
          <Paragraph>提供完整的案例信息，包括图片、视频等素材</Paragraph>
        </Card>
      </div>
    </div>
  );
};

export default Home;
