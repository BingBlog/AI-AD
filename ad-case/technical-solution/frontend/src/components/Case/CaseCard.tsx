/**
 * 案例卡片组件
 */
import { Card, Tag, Rate, Space, Typography, Tooltip } from 'antd';
import { HeartOutlined, CalendarOutlined, LinkOutlined, EnvironmentOutlined, BankOutlined, BuildOutlined } from '@ant-design/icons';
import type { CaseSearchResult } from '@/types/case';
import { formatDate } from '@/utils/format';
import styles from './CaseCard.module.less';

const { Title, Text, Paragraph } = Typography;

interface CaseCardProps {
  caseData: CaseSearchResult;
  query?: string;
}

const CaseCard: React.FC<CaseCardProps> = ({ caseData, query }) => {
  const handleClick = () => {
    // 直接跳转到广告门的详情页
    if (caseData.source_url) {
      window.open(caseData.source_url, '_blank');
    }
  };

  // 高亮关键词
  const highlightText = (text: string, keyword?: string): React.ReactNode => {
    if (!keyword || !text) return text;
    // 转义特殊字符
    const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(${escapedKeyword})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark key={index}>{part}</mark>
      ) : (
        part
      )
    );
  };

  // 截取文本到指定字符数（支持中文字符）
  const truncateToChars = (text: string, maxChars: number): string => {
    if (!text || text.length <= maxChars) return text;
    return text.slice(0, maxChars) + '...';
  };

  // 获取描述文本（100字）
  const getDescriptionText = (): string => {
    if (!caseData.description) return '';
    return truncateToChars(caseData.description, 100);
  };

  // 判断描述是否需要截断
  const isDescriptionTruncated = (): boolean => {
    return caseData.description ? caseData.description.length > 100 : false;
  };

  return (
    <Card
      hoverable
      className={styles.caseCard}
      onClick={handleClick}
    >
      <div className={styles.content}>
        <div className={styles.titleRow}>
          <Title level={5} className={styles.title} ellipsis={{ rows: 2 }}>
            {query ? highlightText(caseData.title, query) : caseData.title}
          </Title>
          {caseData.source_url && (
            <LinkOutlined className={styles.externalLink} />
          )}
        </div>

        <div className={styles.meta}>
          <Space size="small" wrap>
            {caseData.brand_name && (
              <Tag color="blue" icon={<BankOutlined />}>{caseData.brand_name}</Tag>
            )}
            {caseData.brand_industry && (
              <Tag color="green">{caseData.brand_industry}</Tag>
            )}
            {caseData.activity_type && (
              <Tag color="orange">{caseData.activity_type}</Tag>
            )}
            {caseData.location && (
              <Tag color="purple" icon={<EnvironmentOutlined />}>{caseData.location}</Tag>
            )}
            {caseData.company_name && (
              <Tag color="cyan">{caseData.company_name}</Tag>
            )}
            {caseData.agency_name && (
              <Tag color="geekblue" icon={<BuildOutlined />}>{caseData.agency_name}</Tag>
            )}
          </Space>
        </div>

        {caseData.description && (
          <Tooltip
            title={isDescriptionTruncated() ? caseData.description : undefined}
            placement="topLeft"
            mouseEnterDelay={0.5}
            overlayStyle={{ 
              maxWidth: '800px',
              maxHeight: '300px',
              overflowY: 'auto',
              wordBreak: 'break-word',
              whiteSpace: 'pre-wrap'
            }}
          >
            <Paragraph
              className={styles.description}
              type="secondary"
            >
              {query
                ? highlightText(
                    getDescriptionText(),
                    query
                  )
                : getDescriptionText()}
            </Paragraph>
          </Tooltip>
        )}

        <div className={styles.tags}>
          {caseData.tags.slice(0, 3).map((tag) => (
            <Tag key={tag} size="small">
              {tag}
            </Tag>
          ))}
          {caseData.tags.length > 3 && (
            <Text type="secondary" className={styles.moreTags}>
              +{caseData.tags.length - 3}
            </Text>
          )}
        </div>

        <div className={styles.footer}>
          <div className={styles.footerContent}>
            {(caseData.score || caseData.score_decimal) && (
              <div className={styles.footerItem}>
                {/* 星星数量基于 score（5分制），如果不存在则基于 score_decimal 计算 */}
                {caseData.score ? (
                  <Rate disabled defaultValue={caseData.score} size="small" />
                ) : caseData.score_decimal ? (
                  <Rate 
                    disabled 
                    value={Math.round(parseFloat(caseData.score_decimal) / 2)} 
                    size="small" 
                  />
                ) : null}
                {/* 优先显示 score_decimal（10分制），更精确 */}
                {caseData.score_decimal ? (
                  <Text type="secondary" className={styles.score}>
                    {caseData.score_decimal}
                  </Text>
                ) : caseData.score ? (
                  <Text type="secondary" className={styles.score}>
                    {caseData.score}/5
                  </Text>
                ) : null}
              </div>
            )}
            {caseData.publish_time && (
              <div className={styles.footerItem}>
                <CalendarOutlined />
                <Text type="secondary" className={styles.date}>
                  {formatDate(caseData.publish_time)}
                </Text>
              </div>
            )}
            <div className={styles.footerItem}>
              <HeartOutlined />
              <Text type="secondary">{caseData.favourite}</Text>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default CaseCard;
