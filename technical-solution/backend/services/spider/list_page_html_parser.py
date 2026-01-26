#!/usr/bin/env python3
"""
列表页 HTML 解析器
负责解析新接口返回的 HTML 字符串，提取案例列表
"""

import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class ListPageHTMLParser:
    """列表页 HTML 解析器类"""
    
    def __init__(self, base_url: str = 'https://www.adquan.com'):
        """
        初始化解析器
        
        Args:
            base_url: 基础 URL，用于转换相对路径
        """
        self.base_url = base_url
    
    def parse_html(self, html: str) -> List[Dict[str, Any]]:
        """
        解析 HTML 字符串，返回案例列表
        
        Args:
            html: HTML 字符串
        
        Returns:
            案例列表，每个案例是一个字典，格式与旧接口保持一致
        """
        if not html or not html.strip():
            logger.warning("HTML 内容为空")
            return []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            articles = soup.find_all('div', class_='article_1')
            
            if not articles:
                logger.warning("未找到 article_1 元素，可能 HTML 结构已变化")
                return []
            
            cases = []
            for idx, article in enumerate(articles):
                try:
                    case = self._parse_article(article)
                    if case:
                        cases.append(case)
                except Exception as e:
                    logger.error(f"解析第 {idx + 1} 个案例时发生错误: {e}")
                    continue
            
            logger.info(f"成功解析 {len(cases)} 个案例")
            return cases
            
        except Exception as e:
            logger.error(f"解析 HTML 时发生错误: {e}")
            raise
    
    def _parse_article(self, article: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        解析单个 article_1 元素
        
        Returns:
            案例字典，格式与旧接口保持一致
        """
        # 提取基本信息
        title = self._extract_title(article)
        url = self._extract_url(article)
        thumb = self._extract_thumb(article)
        publish_time = self._extract_publish_time(article)
        score = self._extract_score(article)
        companies = self._extract_companies(article)
        
        # 如果没有标题或URL，跳过这个案例
        if not title or not url:
            logger.warning(f"案例缺少必要信息（title={title}, url={url}），跳过")
            return None
        
        # 从 URL 中提取 case_id
        case_id = self._extract_case_id_from_url(url)
        
        # 计算 score（从 score_decimal 计算，用于展示星级评分）
        # score = score_decimal / 2，保留一位小数
        calculated_score = None
        if score is not None:
            try:
                calculated_score = round(score / 2.0, 1)
            except (TypeError, ValueError):
                pass
        
        # 构建返回数据，格式与旧接口保持一致
        case = {
            'id': case_id,
            'title': title,
            'url': url,
            'thumb': thumb or '',
            'score': calculated_score if calculated_score is not None else 0,
            'score_decimal': f"{score:.1f}" if score else '0.0',
            'favourite': 0,  # 新接口HTML中可能没有收藏数
            'company_name': companies[0]['name'] if companies else '',
            'company_logo': companies[0]['logo'] if companies else '',
            'vip_img': '',  # 新接口HTML中可能没有VIP标识
        }
        
        return case
    
    def _extract_title(self, article: BeautifulSoup) -> Optional[str]:
        """提取标题"""
        # 优先级 1: article_2_p
        title_elem = article.find('p', class_='article_2_p')
        if title_elem:
            title = title_elem.get_text(strip=True)
            if title:
                return title
        
        # 优先级 2: article_1_fu 中的第一个 p（可能是标题或描述）
        fu_elem = article.find('div', class_='article_1_fu')
        if fu_elem:
            first_p = fu_elem.find('p')
            if first_p:
                title = first_p.get_text(strip=True)
                if title:
                    return title
        
        return None
    
    def _extract_url(self, article: BeautifulSoup) -> Optional[str]:
        """提取案例链接"""
        # 优先级 1: article_2_href
        href_elem = article.find('a', class_='article_2_href')
        if href_elem and href_elem.get('href'):
            url = href_elem.get('href')
            return urljoin(self.base_url, url)
        
        # 优先级 2: article_1 中的第一个 a 标签
        first_a = article.find('a')
        if first_a and first_a.get('href'):
            url = first_a.get('href')
            # 检查是否是 article URL
            if '/article/' in url:
                return urljoin(self.base_url, url)
        
        return None
    
    def _extract_thumb(self, article: BeautifulSoup) -> Optional[str]:
        """提取缩略图"""
        img_elem = article.find('img', class_='article_1_img')
        if img_elem and img_elem.get('src'):
            return img_elem.get('src')
        return None
    
    def _extract_publish_time(self, article: BeautifulSoup) -> Optional[str]:
        """提取发布时间"""
        fu_elem = article.find('div', class_='article_1_fu')
        if fu_elem:
            # 查找所有 p 标签
            p_tags = fu_elem.find_all('p')
            # 通常日期在最后一个 p 标签中
            for p_tag in reversed(p_tags):
                date_text = p_tag.get_text(strip=True)
                # 格式: 2026/01/23
                if re.match(r'\d{4}/\d{2}/\d{2}', date_text):
                    return date_text.replace('/', '-')  # 转换为 2026-01-23
        return None
    
    def _extract_score(self, article: BeautifulSoup) -> Optional[float]:
        """提取评分"""
        article_3 = article.find('div', class_='article_3')
        if article_3:
            # 查找包含评分的元素
            # 可能是 <normal>6.0分</normal> 或 <normal>暂无</normal>
            normal_elem = article_3.find('normal')
            if normal_elem:
                score_text = normal_elem.get_text(strip=True)
                # 处理"暂无"情况
                if '暂无' in score_text or not score_text:
                    return None
                # 提取数字（可能是 "6.0分" 或 "6.0"）
                match = re.search(r'(\d+\.?\d*)', score_text)
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        pass
        return None
    
    def _extract_companies(self, article: BeautifulSoup) -> List[Dict[str, str]]:
        """
        提取公司信息
        
        Returns:
            公司列表，每个公司包含 logo 和 name
        """
        companies = []
        
        # 查找 article_3 中的公司 logo
        article_3 = article.find('div', class_='article_3')
        if article_3:
            company_imgs = article_3.find_all('img', class_='article_3_img')
            for img in company_imgs:
                company = {
                    'logo': img.get('src', ''),
                    'name': img.get('alt', '') or '',  # alt 属性可能包含公司名
                }
                # 如果 alt 为空，尝试从 hover 区域提取
                if not company['name']:
                    company['name'] = self._extract_company_name_from_hover(article, img)
                companies.append(company)
        
        return companies
    
    def _extract_company_name_from_hover(self, article: BeautifulSoup, img: BeautifulSoup) -> str:
        """从 hover 区域提取公司名称"""
        # 查找 hover_one 区域
        hover_one = article.find('div', class_='hover_one')
        if hover_one:
            # 查找包含该图片的公司信息
            img_src = img.get('src', '')
            if img_src:
                # 查找包含相同图片的链接
                company_link = hover_one.find('a', href=True)
                if company_link:
                    # 查找链接中的 span 标签（通常包含公司名）
                    span = company_link.find('span')
                    if span:
                        return span.get_text(strip=True)
        return ''
    
    def _extract_case_id_from_url(self, url: str) -> Optional[int]:
        """从 URL 中提取 case_id（返回整数类型）"""
        # URL 格式: https://www.adquan.com/article/358273
        # 或: /article/358273
        match = re.search(r'/article/(\d+)', url)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                logger.warning(f"无法将 case_id 转换为整数: {match.group(1)}")
                return None
        return None
