/**
 * 案例列表组件
 */
import { Row, Col, Empty, Spin } from 'antd';
import type { CaseSearchResult } from '@/types/case';
import CaseCard from './CaseCard';

interface CaseListProps {
  cases: CaseSearchResult[];
  loading?: boolean;
  query?: string;
}

const CaseList: React.FC<CaseListProps> = ({ cases, loading, query }) => {
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (cases.length === 0) {
    return (
      <Empty
        description="暂无案例数据"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  return (
    <Row gutter={[16, 16]}>
      {cases.map((caseItem) => (
        <Col
          key={caseItem.case_id}
          xs={24}
          sm={12}
          md={12}
          lg={8}
          xl={6}
        >
          <CaseCard caseData={caseItem} query={query} />
        </Col>
      ))}
    </Row>
  );
};

export default CaseList;
