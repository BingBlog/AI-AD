/**
 * 头部组件
 */
import { Layout } from 'antd';
import { useNavigate } from 'react-router-dom';
import { SemanticSearchBox } from '@/components/Search';
import styles from './index.module.less';

const { Header: AntHeader } = Layout;

const Header: React.FC = () => {
  const navigate = useNavigate();

  const handleSearch = () => {
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
          <SemanticSearchBox onSearch={handleSearch} compact />
        </div>
      </div>
    </AntHeader>
  );
};

export default Header;
