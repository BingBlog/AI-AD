/**
 * 工作流程区域组件
 */
import { useEffect, useRef } from "react";
import { Typography } from "antd";
import styles from "../index.module.less";

const { Title, Paragraph } = Typography;

const WorkflowSection: React.FC = () => {
  const workflowScrollRef = useRef<HTMLDivElement>(null);

  // Hover自动滚动逻辑
  useEffect(() => {
    const scrollContainer = workflowScrollRef.current;
    if (!scrollContainer) return;

    const steps = scrollContainer.querySelectorAll(`.${styles.workflowStep}`);
    let autoScrollTimer: NodeJS.Timeout | null = null;
    let scrollDirection: "left" | "right" | null = null;

    const updateGradientVisibility = () => {
      const scrollLeft = scrollContainer.scrollLeft;
      const scrollWidth = scrollContainer.scrollWidth;
      const clientWidth = scrollContainer.clientWidth;

      // 更新data属性用于CSS选择器
      if (scrollLeft > 10) {
        scrollContainer.setAttribute("data-scroll-left", "true");
      } else {
        scrollContainer.removeAttribute("data-scroll-left");
      }

      if (scrollLeft < scrollWidth - clientWidth - 10) {
        scrollContainer.setAttribute("data-scroll-right", "true");
      } else {
        scrollContainer.removeAttribute("data-scroll-right");
      }
    };

    const handleStepHover = (step: Element) => {
      const containerWidth = scrollContainer.offsetWidth;
      const stepElement = step as HTMLElement;
      const stepRect = stepElement.getBoundingClientRect();
      const containerRect = scrollContainer.getBoundingClientRect();
      const stepCenter =
        stepRect.left + stepRect.width / 2 - containerRect.left;
      const containerCenter = containerWidth / 2;

      // 清除之前的定时器
      if (autoScrollTimer) {
        clearInterval(autoScrollTimer);
      }

      // 判断滚动方向
      if (stepCenter < containerCenter - 100) {
        scrollDirection = "left";
      } else if (stepCenter > containerCenter + 100) {
        scrollDirection = "right";
      } else {
        scrollDirection = null;
        return;
      }

      // 自动滚动
      autoScrollTimer = setInterval(() => {
        if (scrollDirection === "left") {
          scrollContainer.scrollBy({ left: -2, behavior: "auto" });
        } else if (scrollDirection === "right") {
          scrollContainer.scrollBy({ left: 2, behavior: "auto" });
        }
        updateGradientVisibility();
      }, 16); // 约60fps
    };

    const handleStepLeave = () => {
      if (autoScrollTimer) {
        clearInterval(autoScrollTimer);
        autoScrollTimer = null;
      }
      scrollDirection = null;
    };

    // 监听滚动事件更新遮罩
    scrollContainer.addEventListener("scroll", updateGradientVisibility);
    updateGradientVisibility(); // 初始化

    steps.forEach((step) => {
      step.addEventListener("mouseenter", () => handleStepHover(step));
      step.addEventListener("mouseleave", handleStepLeave);
    });

    return () => {
      scrollContainer.removeEventListener("scroll", updateGradientVisibility);
      steps.forEach((step) => {
        step.removeEventListener("mouseenter", () => handleStepHover(step));
        step.removeEventListener("mouseleave", handleStepLeave);
      });
      if (autoScrollTimer) {
        clearInterval(autoScrollTimer);
      }
    };
  }, []);

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    element?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const workflowSteps = [
    {
      number: 1,
      title: "Brief解读",
      coreFeature: "多模态 AI 文档解析",
      traditional: "人工逐字阅读，耗时数小时",
      ai: "AI 多模态解析，快速完成",
      description: "支持 PDF、Word、Excel、PPT 等多种格式",
      targetId: "brief-analysis",
    },
    {
      number: 2,
      title: "资料收集",
      coreFeature: "智能爬虫 + 语义检索",
      traditional: "手动搜索，效率低，覆盖不全",
      ai: "智能爬虫 + 语义检索，百万级案例库",
      description: "7×24 小时自动采集，全平台覆盖",
      targetId: "data-collection",
    },
    {
      number: 3,
      title: "策略分析",
      coreFeature: "大模型知识推理 + 智能体自动化分析",
      traditional: "依赖经验，主观性强",
      ai: "大模型知识推理，五维度洞察",
      description: "快速完成策略制定，数据驱动决策",
      targetId: "strategy-analysis",
    },
    {
      number: 4,
      title: "创意脑暴",
      coreFeature: "大模型内容生成 + 语义检索",
      traditional: "靠灵感，方向单一",
      ai: "AI 创意生成，快速产出多个方向",
      description: "结合海量案例库，多元化创意灵感",
      targetId: "creative-brainstorm",
    },
    {
      number: 5,
      title: "方案撰写",
      coreFeature: "大模型内容生成 + 智能体报告生成",
      traditional: "重复劳动，1-2 周完成",
      ai: "智能体自动生成，快速完成",
      description: "自动生成完整整合营销全案",
      targetId: "proposal-writing",
    },
    {
      number: 6,
      title: "竞标提案",
      coreFeature: "大模型内容生成 + 智能体智能预算计算",
      traditional: "预算计算易出错，反复核对",
      ai: "智能体智能预算计算，自动生成明细",
      description: "快速完成专业竞标提案，准确无误",
      targetId: "proposal-bidding",
    },
    {
      number: 7,
      title: "物料设计",
      coreFeature: "大模型内容生成 + 语义检索参考案例",
      traditional: "沟通成本高，反复修改",
      ai: "语义检索参考案例，快速生成设计规范",
      description: "快速完成设计需求文档，减少沟通成本",
      targetId: "material-design",
    },
    {
      number: 8,
      title: "物料投放",
      coreFeature: "大模型知识推理 + 智能体智能合规检查",
      traditional: "制定繁琐，合规风险高",
      ai: "智能体智能合规检查，自动生成投放计划",
      description: "快速完成投放计划制定，降低合规风险",
      targetId: "material-delivery",
    },
  ];

  return (
    <div className={styles.workflowSection}>
      <div className={styles.workflowContainer}>
        <Title level={2} className={styles.sectionTitle}>
          一站式全流程赋能
          <span
            style={{
              display: "block",
              fontSize: "24px",
              fontWeight: 400,
              color: "#94a3b8",
              marginTop: "12px",
            }}>
            从 Brief 解读到物料投放，八步完成全流程，AI 赋能每一步
          </span>
        </Title>

        {/* 横向滚动容器 */}
        <div className={styles.workflowScrollWrapper}>
          {/* 左侧渐变遮罩 */}
          <div className={styles.scrollGradientLeft}></div>

          {/* 滚动容器 */}
          <div
            className={styles.workflowScrollContainer}
            ref={workflowScrollRef}>
            <div className={styles.workflowStepsWrapper}>
              {workflowSteps.map((step) => (
                <div
                  key={step.number}
                  className={styles.workflowStep}
                  onClick={() => scrollToSection(step.targetId)}>
                  <div className={styles.stepNumber}>{step.number}</div>
                  <Title level={3} className={styles.stepTitle}>
                    {step.title}
                  </Title>
                  <div className={styles.stepCoreFeature}>
                    {step.coreFeature}
                  </div>
                  <div className={styles.stepComparison}>
                    <div className={styles.comparisonItem}>
                      <span className={styles.comparisonLabel}>传统时代：</span>
                      <span className={styles.comparisonText}>
                        {step.traditional}
                      </span>
                    </div>
                    <div className={styles.comparisonItem}>
                      <span className={styles.comparisonLabel}>AI 时代：</span>
                      <span className={styles.comparisonText}>{step.ai}</span>
                    </div>
                  </div>
                  <Paragraph className={styles.stepDescription}>
                    {step.description}
                  </Paragraph>
                </div>
              ))}
            </div>
          </div>

          {/* 右侧渐变遮罩 */}
          <div className={styles.scrollGradientRight}></div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowSection;
