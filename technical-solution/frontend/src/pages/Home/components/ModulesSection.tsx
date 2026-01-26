/**
 * 核心功能板块组件
 */
import styles from "../index.module.less";
import {
  DataCollectionModule,
  BriefAnalysisModule,
  StrategyAnalysisModule,
  CreativeBrainstormModule,
  ProposalWritingModule,
  ProposalBiddingModule,
  MaterialDesignModule,
  MaterialDeliveryModule,
} from "./modules";

interface ModulesSectionProps {
  stats?: {
    total_cases: number;
    industries?: Array<{
      name: string;
      count: number;
      image?: string;
      length: number;
    }>;
    tags?: Array<{
      name: string;
      count: number;
      image?: string;
      length: number;
    }>;
  };
  statsLoading?: boolean;
  processImageUrl?: (url?: string) => string | undefined;
}

const ModulesSection: React.FC<ModulesSectionProps> = ({
  stats,
  statsLoading = false,
  processImageUrl,
}) => {
  return (
    <div className={styles.modulesSection}>
      <DataCollectionModule
        stats={stats}
        statsLoading={statsLoading}
        processImageUrl={processImageUrl}
      />
      <BriefAnalysisModule />
      <StrategyAnalysisModule />
      <CreativeBrainstormModule />
      <ProposalWritingModule />
      <ProposalBiddingModule />
      <MaterialDesignModule />
      <MaterialDeliveryModule />
    </div>
  );
};

export default ModulesSection;
