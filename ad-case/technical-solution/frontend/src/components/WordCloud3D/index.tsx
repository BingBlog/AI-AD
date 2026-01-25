/**
 * 3D球面词云组件
 * 词云项分布在3D球面上，球体缓慢旋转，词项有轻微浮动效果
 */
import { useRef, useState, useMemo, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import {
  Text,
  OrbitControls,
  Stars,
  PerspectiveCamera,
} from "@react-three/drei";
import * as THREE from "three";
import styles from "./index.module.less";

export interface WordCloudItem {
  name: string;
  count: number;
  image?: string;
}

interface WordCloud3DProps {
  items: WordCloudItem[];
  title: string;
  onItemClick?: (item: WordCloudItem) => void;
  onFrontItemChange?: (item: WordCloudItem | null) => void;
}

interface WordItemProps {
  item: WordCloudItem;
  index: number;
  totalItems: number;
  position: [number, number, number]; // 球面上的位置
  radius: number; // 距离中心的半径
  scale: number;
  countRatio: number; // count的重要性比例 (0-1)
  onClick: () => void;
  onHover: (hovered: boolean) => void;
  onPositionUpdate?: (idx: number, z: number, isVisible: boolean) => void;
}

/**
 * 斐波那契球面分布算法
 * 在球面上均匀分布点
 */
function fibonacciSphere(n: number, index: number): [number, number, number] {
  const goldenAngle = Math.PI * (3 - Math.sqrt(5)); // 黄金角度
  const theta = goldenAngle * index;
  const y = 1 - (2 * index) / n; // y坐标从1到-1
  const radius = Math.sqrt(1 - y * y);
  const x = Math.cos(theta) * radius;
  const z = Math.sin(theta) * radius;
  return [x, y, z];
}

/**
 * 根据count和位置计算颜色
 * 重要词汇使用主题色渐变，次要词汇使用中性色
 */
function getColor(countRatio: number, z: number, hovered: boolean): string {
  // 位置比例（前方更亮，z值越大越靠前）
  const positionRatio = Math.max(0, Math.min(1, (z + 3) / 6));

  if (hovered) {
    // 悬停时使用更亮的主题色
    return "#4f46e5"; // 更深的indigo
  }

  // 重要性比例
  if (countRatio > 0.7) {
    // 重要词汇：indigo → purple 渐变
    const r = 99 + positionRatio * 40;
    const g = 102 + positionRatio * 30;
    const b = 241 - positionRatio * 20;
    return `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;
  } else if (countRatio > 0.4) {
    // 中等词汇：浅色主题色
    const r = 129 + positionRatio * 30;
    const g = 140 + positionRatio * 20;
    const b = 248 - positionRatio * 15;
    return `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;
  } else {
    // 次要词汇：中性色
    const r = 148 + positionRatio * 50;
    const g = 163 + positionRatio * 30;
    const b = 184 + positionRatio * 20;
    return `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;
  }
}

// 单个词云项组件
function WordItem({
  item,
  index,
  position,
  radius,
  scale,
  countRatio,
  onClick,
  onHover,
  onPositionUpdate,
}: WordItemProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);
  const basePositionRef = useRef<THREE.Vector3>(
    new THREE.Vector3(...position).multiplyScalar(radius)
  );
  const floatPhase = useRef(Math.random() * Math.PI * 2); // 随机相位，让浮动错开
  const currentZRef = useRef(basePositionRef.current.z); // 存储当前Z坐标用于颜色计算
  const [currentColor, setCurrentColor] = useState(() =>
    getColor(countRatio, basePositionRef.current.z, false)
  );

  useFrame((state) => {
    if (!meshRef.current) return;

    const time = state.clock.elapsedTime;

    // 球体旋转：绕Y轴缓慢旋转（30-40秒/圈）
    const rotationSpeed = 0.025; // 旋转速度（弧度/秒），约25秒/圈
    const rotationAngle = time * rotationSpeed;

    // 计算旋转后的位置
    const rotatedX =
      basePositionRef.current.x * Math.cos(rotationAngle) -
      basePositionRef.current.z * Math.sin(rotationAngle);
    const rotatedZ =
      basePositionRef.current.x * Math.sin(rotationAngle) +
      basePositionRef.current.z * Math.cos(rotationAngle);
    const rotatedY = basePositionRef.current.y;

    // 浮动效果：在球面法线方向轻微浮动
    // 重要词汇浮动更小，更稳定
    const baseFloatAmplitude = 0.3;
    const floatAmplitude = baseFloatAmplitude * (1 - countRatio * 0.5); // 重要词汇浮动更小
    const floatSpeed = 0.5; // 浮动速度
    const floatOffset =
      Math.sin(time * floatSpeed + floatPhase.current) * floatAmplitude;

    // 计算法线方向（从中心指向当前位置）
    const normal = new THREE.Vector3(rotatedX, rotatedY, rotatedZ).normalize();
    const floatX = rotatedX + normal.x * floatOffset;
    const floatY = rotatedY + normal.y * floatOffset;
    const floatZ = rotatedZ + normal.z * floatOffset;

    // 设置位置
    meshRef.current.position.set(floatX, floatY, floatZ);

    // 更新Z坐标引用
    currentZRef.current = floatZ;

    // 更新颜色（根据位置和hovered状态）
    const newColor = getColor(countRatio, floatZ, hovered);
    // 使用函数式更新避免闭包问题
    setCurrentColor((_prevColor) => newColor);

    // 让词项始终面向相机（相机在 0, 0, 8）
    meshRef.current.lookAt(0, 0, 8);

    // 根据Z坐标（前后位置）调整透明度，而不是距离
    // 前方的词项（Z值大）更清晰，后方的词项（Z值小）更透明
    const zRange = 6; // Z坐标范围
    const normalizedZ = Math.max(
      0,
      Math.min(1, (floatZ + zRange / 2) / zRange)
    );

    // 重要词汇基础透明度更高
    const baseOpacity = 0.6 + countRatio * 0.2; // 0.6-0.8
    const opacityRange = 0.3; // 透明度变化范围
    const minOpacity = baseOpacity - opacityRange * 0.5;
    const opacity = minOpacity + normalizedZ * opacityRange;

    // 悬停时增加透明度和亮度
    const finalOpacity = hovered ? Math.min(opacity + 0.15, 1.0) : opacity;

    // 更新透明度
    if (meshRef.current) {
      meshRef.current.traverse((child) => {
        if (child instanceof THREE.Mesh && child.material) {
          const material = child.material as THREE.MeshBasicMaterial;
          material.opacity = finalOpacity;
          material.transparent = true;
          material.needsUpdate = true;
        }
      });
    }

    // 悬停时放大（重要词汇放大更明显）
    const hoverScale = hovered ? 1.3 + countRatio * 0.1 : 1.0; // 1.3-1.4
    meshRef.current.scale.setScalar(scale * hoverScale);

    // 更新位置信息（用于背景检测）
    const isInVisibleRange = floatZ < 2 && finalOpacity > 0.6; // 在前方且足够清晰
    onPositionUpdate?.(index, floatZ, isInVisibleRange);
  });

  // 根据count调整字体大小（重要词汇更大）
  const baseFontSize = 0.3;
  const fontSizeRange = 0.4;
  const fontSize = baseFontSize + countRatio * fontSizeRange; // 0.3-0.7

  // 颜色使用state，会在useFrame中动态更新
  // 当hovered状态改变时，也更新颜色
  useEffect(() => {
    const newColor = getColor(countRatio, currentZRef.current, hovered);
    setCurrentColor(newColor);
  }, [hovered, countRatio]);

  const color = currentColor;

  // 截取文本：超过10个字符的截取并加省略号
  const displayText = useMemo(() => {
    const text = `${item.name} (${item.count})`;
    if (text.length > 10) {
      return text.substring(0, 10) + "...";
    }
    return text;
  }, [item.name, item.count]);

  return (
    <mesh
      ref={meshRef}
      visible={true}
      onClick={onClick}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHovered(true);
        onHover(true);
      }}
      onPointerOut={(e) => {
        e.stopPropagation();
        setHovered(false);
        onHover(false);
      }}>
      <Text
        fontSize={fontSize}
        color={color}
        anchorX="center"
        anchorY="middle"
        outlineWidth={hovered ? 0.04 : 0.025}
        outlineColor={hovered ? "#1e293b" : "#0f172a"}>
        {displayText}
      </Text>
    </mesh>
  );
}

// 3D场景内容
function SceneContent({
  items,
  onItemClick,
  onFrontItemChange,
}: {
  items: WordCloudItem[];
  onItemClick?: (item: WordCloudItem) => void;
  onFrontItemChange?: (item: WordCloudItem | null) => void;
}) {
  const groupRef = useRef<THREE.Group>(null);

  // 存储每个WordItem的当前位置信息（用于背景检测）
  const itemPositionsRef = useRef<
    Map<
      number,
      {
        currentZ: number;
        item: WordCloudItem;
        isVisible: boolean;
      }
    >
  >(new Map());

  // 计算最大最小count值
  const { maxCount, minCount } = useMemo(() => {
    if (items.length === 0) return { maxCount: 0, minCount: 0 };
    const counts = items.map((item) => item.count);
    return {
      maxCount: Math.max(...counts),
      minCount: Math.min(...counts),
    };
  }, [items]);

  // 计算词项在球面上的位置和半径
  const itemPositions = useMemo(() => {
    if (items.length === 0) return [];

    const baseRadius = 3; // 基础半径（减小，让词项更靠近相机）
    const radiusRange = 1.5; // 半径变化范围

    return items.map((item, index) => {
      // 使用斐波那契球面分布
      const [x, y, z] = fibonacciSphere(items.length, index);

      // 根据count调整半径：重要词汇更靠近相机（半径更小）
      const countRatio =
        maxCount === minCount
          ? 0.5
          : (item.count - minCount) / (maxCount - minCount);
      const radius = baseRadius + (1 - countRatio) * radiusRange; // 重要词汇半径更小

      // 计算实际位置
      const position: [number, number, number] = [
        x * radius,
        y * radius,
        z * radius,
      ];

      // 基础scale，会根据countRatio在WordItem中调整字体大小
      const scale = 1.0;

      return {
        position,
        radius,
        scale,
        countRatio, // 传递countRatio给WordItem
      };
    });
  }, [items, maxCount, minCount]);

  // 检测最前方的项（用于背景切换）
  const lastCheckTime = useRef(0);
  const lastFrontItemIndex = useRef(-1);
  const backgroundRotationIndex = useRef(0);

  useFrame(() => {
    if (!onFrontItemChange || items.length === 0) return;

    const now = Date.now();
    if (now - lastCheckTime.current < 300) return; // 每300ms检测一次
    lastCheckTime.current = now;

    // 从itemPositionsRef中获取所有可见项的位置信息
    let frontItem: WordCloudItem | null = null;
    let minZ = Infinity;
    let frontItemIndex = -1;

    itemPositionsRef.current.forEach((data, index) => {
      if (data.isVisible && data.currentZ < minZ) {
        minZ = data.currentZ;
        frontItem = data.item;
        frontItemIndex = index;
      }
    });

    // 如果找到最前方的项，使用它
    if (frontItem && frontItemIndex !== lastFrontItemIndex.current) {
      lastFrontItemIndex.current = frontItemIndex;
      onFrontItemChange(frontItem);
    } else if (!frontItem) {
      // 如果没有最前方的项，循环切换背景（确保背景一直变化）
      backgroundRotationIndex.current =
        (backgroundRotationIndex.current + 1) % items.length;
      const rotationItem = items[backgroundRotationIndex.current];
      if (rotationItem) {
        onFrontItemChange(rotationItem);
      }
    }
  });

  return (
    <>
      {/* 星空背景 */}
      <Stars radius={15} depth={50} count={3000} factor={4} fade speed={1} />

      {/* 环境光 */}
      <ambientLight intensity={0.4} />
      <pointLight position={[10, 10, 10]} intensity={1.2} color="#ffffff" />
      <pointLight position={[-10, -10, -10]} intensity={0.8} color="#667eea" />
      <pointLight position={[0, 10, 0]} intensity={0.6} color="#764ba2" />

      {/* 聚光灯效果 */}
      <spotLight
        position={[0, 0, 10]}
        angle={0.3}
        penumbra={1}
        intensity={0.5}
        color="#667eea"
      />

      {/* 词云组 - 3D球面分布 */}
      <group ref={groupRef}>
        {items.map((item, index) => {
          const { position, radius, scale, countRatio } = itemPositions[index];

          return (
            <WordItem
              key={`${item.name}-${index}`}
              item={item}
              index={index}
              totalItems={items.length}
              position={position}
              radius={radius}
              scale={scale}
              countRatio={countRatio}
              onClick={() => onItemClick?.(item)}
              onHover={() => {}}
              onPositionUpdate={(
                idx: number,
                z: number,
                isVisible: boolean
              ) => {
                itemPositionsRef.current.set(idx, {
                  currentZ: z,
                  item: items[idx],
                  isVisible: isVisible,
                });
              }}
            />
          );
        })}
      </group>
    </>
  );
}

const WordCloud3D: React.FC<WordCloud3DProps> = ({
  items,
  title,
  onItemClick,
  onFrontItemChange,
}) => {
  const [backgroundImage, setBackgroundImage] = useState<string | null>(null);

  // 处理最前方项变化，更新背景
  const handleFrontItemChange = (item: WordCloudItem | null) => {
    if (item?.image) {
      setBackgroundImage(item.image);
    }
    onFrontItemChange?.(item);
  };

  return (
    <div className={styles.wordCloud3DContainer}>
      <div className={styles.wordCloudTitle}>{title}</div>
      <div
        className={styles.wordCloud3D}
        style={{
          backgroundImage: backgroundImage
            ? `url(${backgroundImage})`
            : undefined,
        }}>
        <Canvas gl={{ alpha: true, antialias: true }}>
          <PerspectiveCamera makeDefault position={[0, 0, 8]} fov={75} />
          <SceneContent
            items={items}
            onItemClick={onItemClick}
            onFrontItemChange={handleFrontItemChange}
          />
          <OrbitControls
            enableZoom={false}
            enablePan={false}
            enableRotate={false}
            autoRotate={false}
          />
        </Canvas>
      </div>
    </div>
  );
};

export default WordCloud3D;
