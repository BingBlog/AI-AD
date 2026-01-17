/**
 * 头部组件
 */
import { Layout, Input, Button } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useSearchStore } from '@/store/searchStore';
import styles from './index.module.less';

const { Header: AntHeader } = Layout;

const Header: React.FC = () => {
  const navigate = useNavigate();
  const { query, setQuery } = useSearchStore();

  const handleSearch = (value: string) => {
    setQuery(value);
    // 如果不在案例列表页，则跳转
    if (window.location.pathname !== '/cases') {
      navigate('/cases');
    }
  };

  return (
    <AntHeader className={styles.header}>
      <div className={styles.headerContent}>
        <div className={styles.logo} onClick={() => navigate('/')}>
          广告案例库
        </div>
        <div className={styles.searchBox}>
          <Input.Search
            placeholder="搜索案例..."
            allowClear
            enterButton={<Button type="primary" icon={<SearchOutlined />}>搜索</Button>}
            size="large"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onSearch={handleSearch}
            style={{ width: '100%' }}
          />
        </div>
      </div>
    </AntHeader>
  );
};

export default Header;
