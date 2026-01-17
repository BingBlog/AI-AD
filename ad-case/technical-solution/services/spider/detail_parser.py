#!/usr/bin/env python3
"""
详情页解析器
负责从广告门详情页HTML中提取完整的案例信息
"""

import requests
from bs4 import BeautifulSoup, NavigableString
import logging
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class DetailPageParser:
    """详情页解析器类"""
    
    def __init__(self, session: Optional[requests.Session] = None, base_url: str = 'https://m.adquan.com'):
        """
        初始化详情页解析器
        
        Args:
            session: requests.Session实例，如果为None则创建新的
            base_url: 基础URL，用于转换相对路径
        """
        self.session = session or requests.Session()
        self.base_url = base_url
        
        # 设置默认请求头
        if not hasattr(self.session, 'headers') or not self.session.headers:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            })
    
    def parse(self, url: str) -> Dict[str, Any]:
        """
        解析详情页，返回结构化数据
        
        Args:
            url: 详情页URL
            
        Returns:
            包含案例信息的字典
        """
        try:
            logger.info(f"开始解析详情页: {url}")
            
            # 获取HTML
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取各字段
            result = {
                'source_url': url,
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'main_image': self._extract_main_image(soup),
                'images': self._extract_images(soup),
                'video_url': self._extract_video(soup),
                'author': self._extract_author(soup),
                'publish_time': self._extract_publish_time(soup),
                'brand_name': None,  # 将从agent区域提取
                'brand_industry': None,
                'activity_type': None,
                'location': None,
                'tags': [],
                'agency_name': None,
            }
            
            # 提取agent区域的信息
            agent_info = self._extract_agent_info(soup)
            result.update(agent_info)
            
            logger.info(f"成功解析详情页: {url}, 标题: {result['title']}")
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"请求详情页失败 {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"解析详情页失败 {url}: {e}")
            raise
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """提取标题"""
        # 优先级1: meta og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return self._clean_text(og_title.get('content'))
        
        # 优先级2: h3#title
        h3_title = soup.find('h3', id='title')
        if h3_title:
            return self._clean_text(h3_title.get_text())
        
        # 优先级3: title标签
        title_tag = soup.find('title')
        if title_tag:
            title_text = self._clean_text(title_tag.get_text())
            # 去除 " | 广告门" 后缀
            title_text = re.sub(r'\s*\|\s*广告门\s*$', '', title_text)
            return title_text
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """
        提取描述（最高优先级：从new_neirong提取）
        """
        # 最高优先级：从new_neirong提取
        new_neirong = soup.find('div', class_='new_neirong')
        if new_neirong:
            description = self._extract_text_from_new_neirong(new_neirong)
            if description:
                return description
        
        # 备用方案：从meta og:description提取
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return self._clean_text(og_desc.get('content'))
        
        return None
    
    def _extract_text_from_new_neirong(self, new_neirong) -> Optional[str]:
        """
        从new_neirong容器中提取文字内容（忽略图片和视频）
        提取所有标签中的文字（包括section、div等）
        
        Args:
            new_neirong: BeautifulSoup元素对象
            
        Returns:
            提取的文字内容
        """
        # 创建副本以避免修改原始对象
        soup_copy = BeautifulSoup(str(new_neirong), 'html.parser')
        new_neirong_copy = soup_copy.find('div', class_='new_neirong')
        if not new_neirong_copy:
            return None
        
        # 移除图片、iframe、水印等
        for tag in new_neirong_copy.find_all(['img', 'iframe']):
            tag.decompose()
        
        for tag in new_neirong_copy.find_all(class_=lambda x: x and 'hidden-watermark' in x):
            tag.decompose()
        
        # 移除script和style标签
        for tag in new_neirong_copy.find_all(['script', 'style']):
            tag.decompose()
        
        # 移除空的section和div标签（但保留有内容的）
        for tag in new_neirong_copy.find_all(['section', 'div']):
            if not tag.get_text(strip=True):
                tag.decompose()
        
        # 提取所有p标签的文本（p标签是最主要的文本容器）
        text_parts = []
        seen_texts = set()  # 用于去重
        
        # 首先提取所有p标签（包括嵌套的）
        for p_tag in new_neirong_copy.find_all('p'):
            text = self._extract_text_from_p_tag(p_tag)
            if text and text not in seen_texts:
                # 过滤掉水印文本
                if '本文来源于广告门' not in text and 'adquan.com' not in text:
                    text_parts.append(text)
                    seen_texts.add(text)
        
        # 如果没有找到p标签，或者需要补充其他块级元素的文本
        # 检查是否有其他包含文本的块级元素（如section中的直接文本节点）
        if not text_parts:
            # 提取所有直接子元素的文本
            for child in new_neirong_copy.children:
                if hasattr(child, 'name') and child.name:
                    text = self._extract_text_from_element(child)
                    if text:
                        cleaned = text.strip()
                        if cleaned and cleaned not in seen_texts:
                            if '本文来源于广告门' not in cleaned and 'adquan.com' not in cleaned:
                                text_parts.append(cleaned)
                                seen_texts.add(cleaned)
        
        # 如果仍然没有内容，尝试提取所有文本（作为最后的手段）
        if not text_parts:
            all_text = new_neirong_copy.get_text(separator='\n', strip=True)
            if all_text:
                # 按段落分割
                paragraphs = [p.strip() for p in all_text.split('\n') if p.strip()]
                for para in paragraphs:
                    if para not in seen_texts:
                        if '本文来源于广告门' not in para and 'adquan.com' not in para:
                            text_parts.append(para)
                            seen_texts.add(para)
        
        if text_parts:
            description = '\n\n'.join(text_parts)
            # 再次过滤水印文本
            description = re.sub(r'\s*本文来源于广告门.*$', '', description, flags=re.IGNORECASE | re.MULTILINE)
            description = re.sub(r'\s*adquan\.com.*$', '', description, flags=re.IGNORECASE | re.MULTILINE)
            # 清理多余的空行
            description = re.sub(r'\n{3,}', '\n\n', description)
            return self._clean_text(description)
        
        return None
    
    def _extract_text_from_p_tag(self, p_tag) -> str:
        """
        从p标签中提取文本，保持内联标签（如em、strong、span）的文本
        正确处理<br>标签，将其转换为换行
        """
        if not p_tag:
            return ''
        
        # 先处理<br>标签，将其替换为换行符
        # 创建一个副本
        p_copy = BeautifulSoup(str(p_tag), 'html.parser').find('p')
        if not p_copy:
            return ''
        
        # 将<br>和<br/>标签替换为换行符
        for br in p_copy.find_all('br'):
            br.replace_with('\n')
        
        # 获取文本，使用换行符作为分隔符（对于块级元素）
        # 对于内联元素，使用空格
        text = p_copy.get_text(separator=' ', strip=False)
        
        # 清理多余的空白字符，但保留换行
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def _extract_text_from_element(self, element) -> str:
        """
        递归提取元素中的文字内容（忽略包含图片/视频/水印的节点）
        """
        block_tags = {
            'p', 'section', 'div', 'article', 'aside', 'blockquote',
            'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'table', 'thead', 'tbody', 'tr', 'th', 'td'
        }
        
        inline_join_tags = {'span', 'strong', 'em', 'b', 'i', 'u', 'small', 'sup', 'sub'}
        
        if isinstance(element, NavigableString):
            text = str(element).strip()
            if not text:
                return ''
            if '本文来源于广告门' in text or 'adquan.com' in text:
                return ''
            return text
        
        if not hasattr(element, 'name'):
            return ''
        
        if element.name in ('script', 'style'):
            return ''
        
        if element.name in ('img', 'iframe'):
            return ''
        
        if 'hidden-watermark' in element.get('class', []):
            return ''
        
        collected_texts = []
        for child in element.children:
            child_text = self._extract_text_from_element(child)
            if child_text:
                collected_texts.append(child_text)
        
        if not collected_texts:
            return ''
        
        if element.name == 'br':
            return ''
        
        if element.name in block_tags:
            return '\n'.join(collected_texts)
        
        if element.name in inline_join_tags:
            return ' '.join(collected_texts)
        
        return ' '.join(collected_texts)
    
    def _extract_main_image(self, soup: BeautifulSoup) -> Optional[str]:
        """提取主图"""
        # 优先级1: meta og:image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return self._normalize_url(og_image.get('content'))
        
        # 优先级2: case_title_pic
        title_pic = soup.find('img', class_='case_title_pic')
        if title_pic and title_pic.get('src'):
            return self._normalize_url(title_pic.get('src'))
        
        return None
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """提取图片集合"""
        images = []
        
        # 1. 从new_neirong中提取图片
        new_neirong = soup.find('div', class_='new_neirong')
        if new_neirong:
            for img in new_neirong.find_all('img'):
                src = img.get('src')
                if src:
                    normalized_url = self._normalize_url(src)
                    if normalized_url and self._is_valid_image_url(normalized_url):
                        images.append(normalized_url)
        
        # 2. 从swiper-container中提取图片
        swiper = soup.find('div', class_='swiper-container')
        if swiper:
            for slide in swiper.find_all('div', class_='swiper-slide'):
                img = slide.find('img')
                if img and img.get('src'):
                    normalized_url = self._normalize_url(img.get('src'))
                    if normalized_url and self._is_valid_image_url(normalized_url):
                        images.append(normalized_url)
        
        # 去重
        images = list(dict.fromkeys(images))  # 保持顺序的去重
        
        return images
    
    def _extract_video(self, soup: BeautifulSoup) -> Optional[str]:
        """提取视频URL"""
        # 从new_neirong中查找iframe
        new_neirong = soup.find('div', class_='new_neirong')
        if new_neirong:
            iframe = new_neirong.find('iframe')
            if iframe and iframe.get('src'):
                return iframe.get('src')
        
        # 从整个页面查找
        iframe = soup.find('iframe')
        if iframe and iframe.get('src'):
            return iframe.get('src')
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """提取作者"""
        case_info = soup.find('div', class_='case_info')
        if case_info:
            span_01 = case_info.find('span', class_='span_01')
            if span_01:
                return self._clean_text(span_01.get_text())
        return None
    
    def _extract_publish_time(self, soup: BeautifulSoup) -> Optional[str]:
        """提取发布时间"""
        case_info = soup.find('div', class_='case_info')
        if case_info:
            span_02 = case_info.find('span', class_='span_02')
            if span_02:
                time_text = self._clean_text(span_02.get_text())
                # 验证时间格式 (YYYY-MM-DD)
                if re.match(r'^\d{4}-\d{2}-\d{2}', time_text):
                    return time_text
        return None
    
    def _extract_agent_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        从agent区域提取相关信息（行业、标签、品牌等）
        
        Returns:
            包含相关信息的字典
        """
        result = {
            'brand_industry': None,
            'activity_type': None,
            'location': None,
            'tags': [],
            'brand_name': None,
            'agency_name': None,
        }
        
        agent = soup.find('div', class_='agent', id='list1')
        if not agent:
            return result
        
        # 提取所属行业
        industry_elem = self._find_agent_field(agent, '所属行业')
        if industry_elem:
            industry_link = industry_elem.find('a', {'data-class': 'industry'})
            if industry_link:
                result['brand_industry'] = self._clean_text(
                    industry_link.get('data-name') or industry_link.get_text()
                )
        
        # 提取形式类别（活动类型）
        type_elem = self._find_agent_field(agent, '形式类别')
        if type_elem:
            type_link = type_elem.find('a', {'data-class': 'typeclass'})
            if type_link:
                result['activity_type'] = self._clean_text(
                    type_link.get('data-name') or type_link.get_text()
                )
        
        # 提取所在地区
        area_elem = self._find_agent_field(agent, '所在地区')
        if area_elem:
            area_link = area_elem.find('a', {'data-class': 'area'})
            if area_link:
                result['location'] = self._clean_text(
                    area_link.get('data-name') or area_link.get_text()
                )
        
        # 提取标签
        tag_elem = self._find_agent_field(agent, '标签')
        if tag_elem:
            tag_links = tag_elem.find_all('a', class_='pr2')
            tags = []
            for tag_link in tag_links:
                tag_name = self._clean_text(
                    tag_link.get('data-name') or tag_link.get_text()
                )
                if tag_name:
                    tags.append(tag_name)
            result['tags'] = tags
        
        # 提取时间（如果agent区域有时间）
        time_elem = self._find_agent_field(agent, '时间')
        if time_elem:
            time_span = time_elem.find('span', class_='pr1')
            if time_span:
                time_text = self._clean_text(time_span.get_text())
                if re.match(r'^\d{4}-\d{2}-\d{2}', time_text):
                    # 如果publish_time还没有，使用这个时间
                    if 'publish_time' not in result or not result.get('publish_time'):
                        result['publish_time'] = time_text
        
        # 查找品牌/广告主（可能在agent区域，但结构可能不同）
        # 注意：根据实际HTML结构，品牌信息可能在agent区域的其他位置
        # 这里需要根据实际情况调整
        
        return result
    
    def _find_agent_field(self, agent, field_name: str):
        """在agent区域中查找指定字段的容器"""
        # 查找包含指定文本的p标签
        p_tags = agent.find_all('p')
        for p in p_tags:
            if field_name in p.get_text():
                # 返回p标签的父div
                parent = p.parent
                if parent and parent.name == 'div':
                    return parent
        return None
    
    def _clean_text(self, text: str) -> str:
        """清洗文本"""
        if not text:
            return ''
        
        # 去除HTML实体编码
        text = text.replace('&ldquo;', '"').replace('&rdquo;', '"')
        text = text.replace('&lsquo;', "'").replace('&rsquo;', "'")
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        
        # 去除多余空白字符
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _normalize_url(self, url: str) -> Optional[str]:
        """规范化URL"""
        if not url:
            return None
        
        # 去除追踪参数
        url = url.split('?')[0]
        url = url.split('#')[0]
        
        # 如果是相对路径，转换为绝对路径
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('/'):
            url = urljoin(self.base_url, url)
        elif not url.startswith('http'):
            url = urljoin(self.base_url, '/' + url)
        
        return url
    
    def _is_valid_image_url(self, url: str) -> bool:
        """检查是否是有效的图片URL"""
        if not url:
            return False
        
        # 过滤占位图和图标
        invalid_patterns = [
            r'/images/close.*\.png',
            r'/images/.*ico.*\.png',
            r'/images/nav.*\.png',
            r'/images/user.*\.jpg',
            r'logo.*\.(png|jpg)',
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # 检查是否是图片格式
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in image_extensions)


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("详情页解析器测试")
    print("=" * 60)
    
    try:
        parser = DetailPageParser()
        
        # 测试URL（使用之前分析的案例）
        test_url = 'https://m.adquan.com/creative/detail/291696'
        
        print(f"\n测试URL: {test_url}")
        print("-" * 60)
        
        # 解析详情页
        result = parser.parse(test_url)
        
        print("\n解析结果:")
        print("-" * 60)
        print(f"标题: {result.get('title')}")
        print(f"\n描述长度: {len(result.get('description', ''))} 字符")
        if result.get('description'):
            print(f"描述预览: {result.get('description')[:200]}...")
        print(f"\n主图: {result.get('main_image')}")
        print(f"\n图片数量: {len(result.get('images', []))}")
        if result.get('images'):
            print(f"前3张图片:")
            for i, img in enumerate(result['images'][:3], 1):
                print(f"  [{i}] {img}")
        print(f"\n视频: {result.get('video_url')}")
        print(f"\n作者: {result.get('author')}")
        print(f"\n发布时间: {result.get('publish_time')}")
        print(f"\n所属行业: {result.get('brand_industry')}")
        print(f"\n形式类别: {result.get('activity_type')}")
        print(f"\n所在地区: {result.get('location')}")
        print(f"\n标签: {result.get('tags')}")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

