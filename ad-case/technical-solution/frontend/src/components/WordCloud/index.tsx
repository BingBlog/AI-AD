/**
 * 云图组件
 */
import { useEffect, useRef, useState } from "react";
import { Typography } from "antd";
import styles from "./index.module.less";

const { Text } = Typography;

export interface WordCloudItem {
  name: string;
  count: number;
  image?: string;
}

interface WordCloudProps {
  items: WordCloudItem[];
  title: string;
  onItemClick?: (item: WordCloudItem) => void;
}

const WordCloud: React.FC<WordCloudProps> = ({ items, title, onItemClick }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [maxCount, setMaxCount] = useState(0);
  const [minCount, setMinCount] = useState(0);

  useEffect(() => {
    if (items.length === 0) return;

    const counts = items.map((item) => item.count);
    setMaxCount(Math.max(...counts));
    setMinCount(Math.min(...counts));
  }, [items]);

  // 计算字体大小（基于数量）
  const getFontSize = (count: number) => {
    if (maxCount === minCount) return 16;
    const ratio = (count - minCount) / (maxCount - minCount);
    // 字体大小范围：14px - 36px
    return 14 + ratio * 22;
  };

  // 生成更好的位置分布（使用螺旋布局）
  const generatePositions = (count: number) => {
    const positions: Array<{ x: number; y: number }> = [];
    const centerX = 50;
    const centerY = 50;
    const angleStep = (2 * Math.PI) / count;
    const radiusStep = 15;

    for (let i = 0; i < count; i++) {
      const angle = i * angleStep;
      const radius = 20 + (i % 3) * radiusStep;
      const x = centerX + radius * Math.cos(angle) + (Math.random() - 0.5) * 10;
      const y = centerY + radius * Math.sin(angle) + (Math.random() - 0.5) * 10;

      // 确保位置在合理范围内
      positions.push({
        x: Math.max(5, Math.min(95, x)),
        y: Math.max(5, Math.min(95, y)),
      });
    }

    return positions;
  };

  const positions = generatePositions(items.length);

  return (
    <div className={styles.wordCloudContainer}>
      <div className={styles.wordCloudTitle}>{title}</div>
      <div ref={containerRef} className={styles.wordCloud}>
        {items.map((item, index) => {
          const fontSize = getFontSize(item.count);
          const position = positions[index] || { x: 50, y: 50 };
          const animationDelay = index * 0.05;

          return (
            <div
              key={`${item.name}-${index}`}
              className={styles.wordCloudItem}
              style={{
                fontSize: `${fontSize}px`,
                left: `${position.x}%`,
                top: `${position.y}%`,
                animationDelay: `${animationDelay}s`,
                backgroundImage: item.image ? `url(${item.image})` : undefined,
              }}
              onClick={() => onItemClick?.(item)}>
              <div className={styles.wordCloudContent}>
                <Text className={styles.wordCloudText}>{item.name}</Text>
                <Text className={styles.wordCloudCount}>({item.count})</Text>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default WordCloud;
