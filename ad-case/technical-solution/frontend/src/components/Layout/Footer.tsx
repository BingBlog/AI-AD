/**
 * 页脚组件
 */
import { Layout } from 'antd';
import styles from './index.module.less';

const { Footer: AntFooter } = Layout;

const Footer: React.FC = () => {
  return (
    <AntFooter className={styles.footer}>
      <div className={styles.footerContent}>
        <p>© 2024 广告案例库. All rights reserved.</p>
      </div>
    </AntFooter>
  );
};

export default Footer;
