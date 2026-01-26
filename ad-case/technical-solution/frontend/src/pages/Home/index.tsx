/**
 * 首页
 */
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getStats } from "@/services/caseService";
import {
  HeroSection,
  WorkflowSection,
  CTASection,
  TechCapabilitiesSection,
} from "./components";
import ModulesSection from "./components/ModulesSection";
import styles from "./index.module.less";

const Home: React.FC = () => {
  // 获取统计数据
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: getStats,
    staleTime: 5 * 60 * 1000, // 5分钟
  });

  // 处理图片URL（将相对路径转换为完整URL）
  const processImageUrl = (url?: string): string | undefined => {
    if (!url) return undefined;

    // 如果是相对路径（以 /static/ 开头），在开发环境通过Vite代理访问
    if (url.startsWith("/static/")) {
      if (import.meta.env.DEV) {
        return url;
      } else {
        const backendUrl = import.meta.env.VITE_API_BASE_URL
          ? import.meta.env.VITE_API_BASE_URL.replace("/api", "")
          : "";
        return backendUrl ? `${backendUrl}${url}` : url;
      }
    }

    // 如果是完整URL，直接返回
    return url;
  };

  // 获取随机背景图片（从统计数据中随机选择一张）
  const randomBackgroundImage = useMemo(() => {
    const allImages: string[] = [];
    if (stats?.industries) {
      stats.industries.forEach((item) => {
        if (item.image) {
          const url = processImageUrl(item.image);
          if (url) allImages.push(url);
        }
      });
    }
    if (stats?.tags) {
      stats.tags.forEach((item) => {
        if (item.image) {
          const url = processImageUrl(item.image);
          if (url) allImages.push(url);
        }
      });
    }
    if (allImages.length > 0) {
      return allImages[Math.floor(Math.random() * allImages.length)];
    }
    return null;
  }, [stats]);

  return (
    <div className={styles.home}>
      <HeroSection
        stats={stats}
        backgroundImage={randomBackgroundImage || undefined}
      />
      <WorkflowSection />

      <ModulesSection
        stats={stats}
        statsLoading={statsLoading}
        processImageUrl={processImageUrl}
      />
      <CTASection />
      <TechCapabilitiesSection />
    </div>
  );
};

export default Home;
