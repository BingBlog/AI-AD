/**
 * 布局组件
 */
import { Layout as AntLayout } from 'antd';
import Header from './Header';
import Footer from './Footer';
import styles from './index.module.less';

const { Content } = AntLayout;

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <AntLayout className={styles.layout}>
      <Header />
      <Content className={styles.content}>{children}</Content>
      <Footer />
    </AntLayout>
  );
};

export default Layout;
