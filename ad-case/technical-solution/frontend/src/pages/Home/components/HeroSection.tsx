/**
 * Hero 区域组件
 */
import { Typography } from "antd";
import { useNavigate } from "react-router-dom";
import HeroSearchBox from "@/components/Search/HeroSearchBox";
import styles from "../index.module.less";

const { Title, Paragraph } = Typography;

interface HeroSectionProps {
  stats?: {
    total_cases: number;
    industries?: Array<{ length: number }>;
    tags?: Array<{ length: number }>;
  };
  backgroundImage?: string;
}

const HeroSection: React.FC<HeroSectionProps> = ({
  stats,
  backgroundImage,
}) => {
  const navigate = useNavigate();

  return (
    <div
      className={styles.hero}
      style={{
        backgroundImage: backgroundImage
          ? `url(${backgroundImage})`
          : undefined,
      }}>
      <div className={styles.heroOverlay}></div>
      <div className={styles.heroContent}>
        <div className={styles.heroBadge}>
          <span>AI驱动</span>
          <span className={styles.badgeDot}></span>
          <span>智能创意</span>
        </div>
        <Title level={1} className={styles.heroTitle}>
          AI驱动的广告营销创意平台
          <span className={styles.heroSubtitle}>
            基于大模型、智能体、爬虫技术，让创意方案生成效率提升 5-10 倍
          </span>
        </Title>
        <Paragraph className={styles.heroDescription}>
          <strong>大模型能力</strong> · <strong>智能体自动化</strong> ·{" "}
          <strong>智能爬虫</strong>
          <br />从 Brief 解读到方案撰写，从创意脑暴到物料投放，全流程 AI 赋能
        </Paragraph>

        {/* 数据统计 */}
        {stats && (
          <div className={styles.heroStats}>
            <div className={styles.statItem}>
              <div className={styles.statNumber}>
                {stats.total_cases.toLocaleString()}+
              </div>
              <div className={styles.statLabel}>精选案例</div>
            </div>
            <div className={styles.statDivider}></div>
            <div className={styles.statItem}>
              <div className={styles.statNumber}>
                {stats.industries?.length || 0}
              </div>
              <div className={styles.statLabel}>行业覆盖</div>
            </div>
            <div className={styles.statDivider}></div>
            <div className={styles.statItem}>
              <div className={styles.statNumber}>{stats.tags?.length || 0}</div>
              <div className={styles.statLabel}>创意标签</div>
            </div>
          </div>
        )}

        {/* Hero搜索框 */}
        <div className={styles.heroSearchBox}>
          <HeroSearchBox onSearch={() => navigate("/cases")} />
        </div>
      </div>
    </div>
  );
};

export default HeroSection;
