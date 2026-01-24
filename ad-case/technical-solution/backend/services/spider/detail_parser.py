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
from .proxy_manager import ProxyManager

logger = logging.getLogger(__name__)


class DetailPageParser:
    """详情页解析器类"""
    
    def __init__(self, session: Optional[requests.Session] = None, base_url: str = 'https://m.adquan.com',
                 proxy_manager: Optional[ProxyManager] = None):
        """
        初始化详情页解析器
        
        Args:
            session: requests.Session实例，如果为None则创建新的
            base_url: 基础URL，用于转换相对路径
            proxy_manager: 代理管理器实例（可选）
        """
        self.session = session or requests.Session()
        self.base_url = base_url
        self.proxy_manager = proxy_manager
        
        # 设置默认请求头（使用PC端User-Agent以获取完整信息）
        if not hasattr(self.session, 'headers') or not self.session.headers:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
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
            
            # 检测是PC端还是移动端URL，并转换为PC端URL以获取完整信息
            normalized_url = self._normalize_url_to_pc(url)
            
            # 获取HTML
            try:
                response = self.session.get(normalized_url, timeout=30)
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                # 记录成功的请求
                if self.proxy_manager:
                    self.proxy_manager.record_request(success=True)
            except Exception as e:
                # 记录失败的请求并处理错误
                if self.proxy_manager:
                    self.proxy_manager.handle_error(e)
                raise
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 检测页面类型（PC端或移动端）
            is_pc_page = self._is_pc_page(soup)
            
            # 提取各字段
            result = {
                'source_url': url,  # 保留原始URL
                'title': self._extract_title(soup, is_pc_page),
                'description': self._extract_description(soup),
                'main_image': self._extract_main_image(soup, is_pc_page),
                'images': self._extract_images(soup),
                'video_url': self._extract_video(soup),
                'author': self._extract_author(soup, is_pc_page),
                'publish_time': self._extract_publish_time(soup, is_pc_page),
                'brand_name': None,  # 将从agent区域提取
                'brand_industry': None,
                'activity_type': None,
                'location': None,
                'tags': [],
                'agency_name': None,
            }
            
            # 提取agent区域的信息（支持PC端和移动端）
            agent_info = self._extract_agent_info(soup, is_pc_page)
            result.update(agent_info)
            
            logger.info(f"成功解析详情页: {url}, 标题: {result['title']}")
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"请求详情页失败 {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"解析详情页失败 {url}: {e}")
            raise
    
    def _normalize_url_to_pc(self, url: str) -> str:
        """将URL转换为PC端URL"""
        if 'm.adquan.com' in url:
            # 移动端URL转换为PC端
            url = url.replace('m.adquan.com', 'www.adquan.com')
        elif 'www.adquan.com' not in url and 'adquan.com' in url:
            # 确保使用www
            url = url.replace('adquan.com', 'www.adquan.com')
        return url
    
    def _is_pc_page(self, soup: BeautifulSoup) -> bool:
        """检测是否是PC端页面"""
        # PC端通常有articleContent或特定的PC端结构
        if soup.find('div', class_='articleContent'):
            return True
        # 移动端通常有new_neirong
        if soup.find('div', class_='new_neirong'):
            return False
        # 默认根据URL判断
        return True
    
    def _extract_title(self, soup: BeautifulSoup, is_pc_page: bool = False) -> Optional[str]:
        """提取标题"""
        # 优先级1: meta og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return self._clean_text(og_title.get('content'))
        
        # 优先级2: h3#title (移动端)
        h3_title = soup.find('h3', id='title')
        if h3_title:
            return self._clean_text(h3_title.get_text())
        
        # 优先级3: PC端标题（通常在h1或特定的标题容器中）
        if is_pc_page:
            # 尝试查找PC端的标题元素
            title_selectors = [
                ('h1', {}),
                ('h2', {'class': 'title'}),
                ('div', {'class': 'title'}),
            ]
            for tag_name, attrs in title_selectors:
                title_elem = soup.find(tag_name, attrs)
                if title_elem:
                    title_text = self._clean_text(title_elem.get_text())
                    if title_text and len(title_text) > 5:
                        return title_text
        
        # 优先级4: title标签
        title_tag = soup.find('title')
        if title_tag:
            title_text = self._clean_text(title_tag.get_text())
            # 去除 " | 广告门" 后缀
            title_text = re.sub(r'\s*\|\s*广告门\s*$', '', title_text)
            return title_text
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """
        提取描述（支持多种内容容器）
        """
        # 优先级1: 从new_neirong提取（移动端）
        new_neirong = soup.find('div', class_='new_neirong')
        if new_neirong:
            description = self._extract_text_from_content_container(new_neirong)
            if description:
                return description
        
        # 优先级2: 从articleContent提取（PC端）
        article_content = soup.find('div', class_='articleContent')
        if article_content:
            description = self._extract_text_from_content_container(article_content)
            if description:
                return description
        
        # 优先级3: 尝试查找其他可能的内容容器
        content_selectors = [
            ('div', {'class': 'content'}),
            ('div', {'class': 'article-content'}),
            ('div', {'class': 'post-content'}),
            ('article', {}),
            ('section', {'class': 'content'}),
        ]
        
        for tag_name, attrs in content_selectors:
            container = soup.find(tag_name, attrs)
            if container:
                description = self._extract_text_from_content_container(container)
                if description:
                    return description
        
        # 备用方案：从meta og:description提取
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return self._clean_text(og_desc.get('content'))
        
        return None
    
    def _extract_text_from_content_container(self, container) -> Optional[str]:
        """
        从内容容器中提取文字内容（通用方法，支持new_neirong、articleContent等）
        """
        return self._extract_text_from_new_neirong(container)
    
    def _extract_text_from_new_neirong(self, container) -> Optional[str]:
        """
        从内容容器中提取文字内容（忽略图片和视频）
        提取所有标签中的文字（包括section、div等）
        支持 new_neirong、articleContent 等多种容器
        
        Args:
            container: BeautifulSoup元素对象（可以是new_neirong、articleContent等）
            
        Returns:
            提取的文字内容
        """
        # 创建副本以避免修改原始对象
        soup_copy = BeautifulSoup(str(container), 'html.parser')
        # 获取容器本身（不再假设容器有特定的类名）
        container_copy = soup_copy.find(container.name, class_=container.get('class'))
        if not container_copy:
            # 如果找不到，尝试获取第一个div或section
            container_copy = soup_copy.find(['div', 'section', 'article'])
        if not container_copy:
            return None
        
        # 移除图片、iframe、水印等
        for tag in container_copy.find_all(['img', 'iframe']):
            tag.decompose()
        
        for tag in container_copy.find_all(class_=lambda x: x and 'hidden-watermark' in x):
            tag.decompose()
        
        # 移除script和style标签
        for tag in container_copy.find_all(['script', 'style']):
            tag.decompose()
        
        # 移除空的section和div标签（但保留有内容的）
        for tag in container_copy.find_all(['section', 'div']):
            if not tag.get_text(strip=True):
                tag.decompose()
        
        # 提取所有文本内容（包括p标签和其他块级元素）
        # 使用更全面的策略：递归提取所有文本段落，保持原有顺序
        text_parts = []
        seen_texts = set()  # 用于去重
        
        # 策略1: 递归遍历所有直接子元素，按DOM顺序提取文本
        def extract_text_from_children(parent, collected_parts, collected_seen):
            """递归提取子元素中的文本"""
            for child in parent.children:
                if not hasattr(child, 'name') or not child.name:
                    # 文本节点
                    text = str(child).strip()
                    if text and len(text) >= 5:
                        if text not in collected_seen:
                            if '本文来源于广告门' not in text and 'adquan.com' not in text:
                                collected_parts.append(text)
                                collected_seen.add(text)
                    continue
                
                # 跳过不需要的元素
                if child.name in ('script', 'style', 'img', 'iframe'):
                    continue
                
                if 'hidden-watermark' in child.get('class', []):
                    continue
                
                # 如果是块级元素，提取其文本
                block_tags = {'p', 'section', 'div', 'article', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
                if child.name in block_tags:
                    if child.name == 'p':
                        text = self._extract_text_from_p_tag(child)
                    else:
                        text = self._extract_text_from_element(child)
                    
                    if text:
                        cleaned = text.strip()
                        if cleaned and len(cleaned) >= 5:
                            # 检查是否与已有文本重复
                            if cleaned not in collected_seen:
                                # 检查是否是已有文本的子串或包含已有文本
                                is_duplicate = False
                                to_remove = None
                                for existing in collected_seen:
                                    # 如果新文本是已有文本的子串，且已有文本更长，跳过新文本
                                    if cleaned in existing and len(existing) > len(cleaned) * 1.2:
                                        is_duplicate = True
                                        break
                                    # 如果已有文本是新文本的子串，且新文本更长，标记为需要替换
                                    if existing in cleaned and len(cleaned) > len(existing) * 1.2:
                                        to_remove = existing
                                        break
                                
                                if to_remove and to_remove in collected_parts:
                                    collected_parts.remove(to_remove)
                                    collected_seen.discard(to_remove)
                                
                                if not is_duplicate:
                                    if '本文来源于广告门' not in cleaned and 'adquan.com' not in cleaned:
                                        collected_parts.append(cleaned)
                                        collected_seen.add(cleaned)
                else:
                    # 对于非块级元素，递归处理其子元素
                    extract_text_from_children(child, collected_parts, collected_seen)
        
        # 从根元素开始递归提取
        extract_text_from_children(container_copy, text_parts, seen_texts)
        
        # 策略2: 如果仍然没有内容，尝试提取所有文本（作为最后的手段）
        if not text_parts:
            all_text = container_copy.get_text(separator='\n', strip=True)
            if all_text:
                # 按段落分割
                paragraphs = [p.strip() for p in all_text.split('\n') if p.strip()]
                for para in paragraphs:
                    # 只保留有意义的段落（至少5个字符）
                    if para and len(para) >= 5 and para not in seen_texts:
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
    
    def _extract_main_image(self, soup: BeautifulSoup, is_pc_page: bool = False) -> Optional[str]:
        """提取主图"""
        # 优先级1: meta og:image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return self._normalize_url(og_image.get('content'))
        
        # 优先级2: case_title_pic (移动端)
        title_pic = soup.find('img', class_='case_title_pic')
        if title_pic and title_pic.get('src'):
            return self._normalize_url(title_pic.get('src'))
        
        # 优先级3: PC端主图（通常在文章内容的第一张图片）
        if is_pc_page:
            article_content = soup.find('div', class_='articleContent')
            if article_content:
                first_img = article_content.find('img')
                if first_img and first_img.get('src'):
                    return self._normalize_url(first_img.get('src'))
        
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
    
    def _extract_author(self, soup: BeautifulSoup, is_pc_page: bool = False) -> Optional[str]:
        """提取作者"""
        # 移动端
        case_info = soup.find('div', class_='case_info')
        if case_info:
            span_01 = case_info.find('span', class_='span_01')
            if span_01:
                author = self._clean_text(span_01.get_text())
                if author:
                    return author
        
        # PC端：从meta标签提取
        meta_author = soup.find('meta', {'name': 'author'})
        if meta_author and meta_author.get('content'):
            author = self._clean_text(meta_author.get('content'))
            if author and author != '广告门':
                return author
        
        return None
    
    def _extract_publish_time(self, soup: BeautifulSoup, is_pc_page: bool = False) -> Optional[str]:
        """提取发布时间"""
        # 移动端
        case_info = soup.find('div', class_='case_info')
        if case_info:
            span_02 = case_info.find('span', class_='span_02')
            if span_02:
                time_text = self._clean_text(span_02.get_text())
                # 验证时间格式 (YYYY-MM-DD)
                if re.match(r'^\d{4}-\d{2}-\d{2}', time_text):
                    return time_text
        
        # PC端：从页面中查找发布时间
        if is_pc_page:
            # 查找包含"发布时间"或"发布时间："的文本
            time_patterns = [
                r'发布时间[：:]\s*(\d{4}-\d{2}-\d{2})',
                r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})',
            ]
            
            # 在页面文本中搜索
            page_text = soup.get_text()
            for pattern in time_patterns:
                match = re.search(pattern, page_text)
                if match:
                    time_str = match.group(1)
                    # 只提取日期部分（YYYY-MM-DD）
                    date_match = re.match(r'(\d{4}-\d{2}-\d{2})', time_str)
                    if date_match:
                        return date_match.group(1)
            
            # 尝试从特定的时间元素中提取
            time_elements = soup.find_all(string=re.compile(r'\d{4}-\d{2}-\d{2}'))
            for time_elem in time_elements:
                time_text = self._clean_text(str(time_elem))
                if re.match(r'^\d{4}-\d{2}-\d{2}', time_text):
                    return time_text[:10]  # 只取日期部分
        
        return None
    
    def _extract_agent_info(self, soup: BeautifulSoup, is_pc_page: bool = False) -> Dict[str, Any]:
        """
        从agent区域提取相关信息（行业、标签、品牌等）
        支持PC端和移动端两种页面结构
        
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
        
        # PC端：从"案例信息"区域提取
        if is_pc_page:
            pc_info = self._extract_pc_case_info(soup)
            if pc_info:
                result.update(pc_info)
        
        # 移动端：从agent区域提取
        agent = soup.find('div', class_='agent', id='list1')
        if agent:
            # 提取所属行业
            industry_elem = self._find_agent_field(agent, '所属行业')
            if industry_elem:
                industry_link = industry_elem.find('a', {'data-class': 'industry'})
                if industry_link:
                    result['brand_industry'] = result['brand_industry'] or self._clean_text(
                        industry_link.get('data-name') or industry_link.get_text()
                    )
            
            # 提取形式类别（活动类型）
            type_elem = self._find_agent_field(agent, '形式类别')
            if type_elem:
                type_link = type_elem.find('a', {'data-class': 'typeclass'})
                if type_link:
                    result['activity_type'] = result['activity_type'] or self._clean_text(
                        type_link.get('data-name') or type_link.get_text()
                    )
            
            # 提取所在地区
            area_elem = self._find_agent_field(agent, '所在地区')
            if area_elem:
                area_link = area_elem.find('a', {'data-class': 'area'})
                if area_link:
                    result['location'] = result['location'] or self._clean_text(
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
                if tags:
                    result['tags'] = tags
        
        return result
    
    def _extract_pc_case_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        从PC端"案例信息"区域提取信息
        
        根据网页内容，PC端的案例信息区域包含：
        - 行业：互联网
        - 类型：平面
        - 地区：中国大陆
        - 时间：2023
        """
        result = {
            'brand_industry': None,
            'activity_type': None,
            'location': None,
            'tags': [],
        }
        
        # 查找"案例信息"区域
        # 可能的容器：包含"案例信息"文本的div
        case_info_containers = [
            soup.find('div', string=re.compile('案例信息')),
            soup.find('h3', string=re.compile('案例信息')),
            soup.find('h4', string=re.compile('案例信息')),
        ]
        
        case_info_section = None
        for container in case_info_containers:
            if container:
                # 找到包含"案例信息"的元素，向上或向下查找信息区域
                case_info_section = container.find_parent() or container.find_next_sibling()
                if case_info_section:
                    break
        
        # 如果没有找到，尝试查找包含这些关键词的区域
        if not case_info_section:
            # 查找包含"行业"、"类型"、"地区"等关键词的区域
            page_text = soup.get_text()
            if '行业：' in page_text or '类型：' in page_text or '地区：' in page_text:
                # 查找包含这些信息的div
                all_divs = soup.find_all('div')
                for div in all_divs:
                    div_text = div.get_text()
                    if '行业：' in div_text or '类型：' in div_text:
                        case_info_section = div
                        break
        
        if case_info_section:
            section_text = case_info_section.get_text()
            
            # 提取行业
            industry_match = re.search(r'行业[：:]\s*([^\n\r]+)', section_text)
            if industry_match:
                result['brand_industry'] = self._clean_text(industry_match.group(1))
            
            # 提取类型（活动类型）
            type_match = re.search(r'类型[：:]\s*([^\n\r]+)', section_text)
            if type_match:
                result['activity_type'] = self._clean_text(type_match.group(1))
            
            # 提取地区
            area_match = re.search(r'地区[：:]\s*([^\n\r]+)', section_text)
            if area_match:
                result['location'] = self._clean_text(area_match.group(1))
            
            # 提取标签（如果有）
            # PC端标签可能在页面其他地方，这里先提取文本中的标签
            
        # 备用方案：直接从页面文本中提取
        if not result['brand_industry'] or not result['activity_type'] or not result['location']:
            page_text = soup.get_text()
            
            # 行业
            if not result['brand_industry']:
                industry_match = re.search(r'行业[：:]\s*([^\n\r]+)', page_text)
                if industry_match:
                    result['brand_industry'] = self._clean_text(industry_match.group(1))
            
            # 类型
            if not result['activity_type']:
                type_match = re.search(r'类型[：:]\s*([^\n\r]+)', page_text)
                if type_match:
                    result['activity_type'] = self._clean_text(type_match.group(1))
            
            # 地区
            if not result['location']:
                area_match = re.search(r'地区[：:]\s*([^\n\r]+)', page_text)
                if area_match:
                    result['location'] = self._clean_text(area_match.group(1))
        
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

