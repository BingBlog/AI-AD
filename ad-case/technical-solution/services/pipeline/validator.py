#!/usr/bin/env python3
"""
数据验证器
验证案例数据的完整性和正确性
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CaseValidator:
    """案例数据验证器"""
    
    def __init__(self):
        """初始化验证器"""
        self.required_fields = ['case_id', 'title', 'source_url']
        self.optional_fields = [
            'description', 'author', 'publish_time',
            'brand_name', 'brand_industry', 'activity_type', 'location', 'tags',
            'main_image', 'images', 'video_url',
            'score', 'score_decimal', 'favourite',
            'company_name', 'company_logo', 'agency_name'
        ]
    
    def validate_case(self, case: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        验证单个案例数据
        
        Args:
            case: 案例数据字典
            
        Returns:
            (is_valid, error_message)
        """
        # 1. 检查必需字段
        for field in self.required_fields:
            if field not in case or not case[field]:
                return False, f"缺少必需字段: {field}"
        
        # 2. 验证case_id
        case_id = case.get('case_id')
        if not isinstance(case_id, int) or case_id <= 0:
            return False, f"无效的case_id: {case_id}"
        
        # 3. 验证title
        title = case.get('title', '').strip()
        if not title or len(title) < 2:
            return False, f"标题太短或为空: {title}"
        if len(title) > 500:
            return False, f"标题过长: {len(title)} 字符"
        
        # 4. 验证source_url
        source_url = case.get('source_url', '').strip()
        if not source_url:
            return False, "source_url为空"
        if not self._is_valid_url(source_url):
            return False, f"无效的URL格式: {source_url}"
        
        # 5. 验证publish_time（如果存在）
        publish_time = case.get('publish_time')
        if publish_time:
            if not self._is_valid_date(publish_time):
                return False, f"无效的日期格式: {publish_time}"
        
        # 6. 验证score（如果存在）
        score = case.get('score')
        if score is not None:
            if not isinstance(score, int) or score < 1 or score > 5:
                return False, f"无效的评分: {score}，应在1-5之间"
        
        # 7. 验证score_decimal（如果存在）
        score_decimal = case.get('score_decimal')
        if score_decimal:
            if not self._is_valid_score_decimal(score_decimal):
                return False, f"无效的评分小数: {score_decimal}"
        
        # 8. 验证favourite（如果存在）
        favourite = case.get('favourite')
        if favourite is not None:
            if not isinstance(favourite, int) or favourite < 0:
                return False, f"无效的收藏数: {favourite}"
        
        # 9. 验证images（如果存在）
        images = case.get('images')
        if images:
            if not isinstance(images, list):
                return False, "images必须是列表"
            for img_url in images:
                if not isinstance(img_url, str) or not self._is_valid_url(img_url):
                    return False, f"无效的图片URL: {img_url}"
        
        # 10. 验证tags（如果存在）
        tags = case.get('tags')
        if tags:
            if not isinstance(tags, list):
                return False, "tags必须是列表"
            for tag in tags:
                if not isinstance(tag, str) or not tag.strip():
                    return False, f"无效的标签: {tag}"
        
        return True, None
    
    def validate_batch(self, cases: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        批量验证案例数据
        
        Args:
            cases: 案例数据列表
            
        Returns:
            (valid_cases, invalid_cases)
        """
        valid_cases = []
        invalid_cases = []
        
        for case in cases:
            is_valid, error = self.validate_case(case)
            if is_valid:
                valid_cases.append(case)
            else:
                invalid_case = case.copy()
                invalid_case['validation_error'] = error
                invalid_cases.append(invalid_case)
                logger.warning(f"案例验证失败 [case_id={case.get('case_id')}]: {error}")
        
        logger.info(f"批量验证完成: 有效={len(valid_cases)}, 无效={len(invalid_cases)}")
        
        return valid_cases, invalid_cases
    
    def _is_valid_url(self, url: str) -> bool:
        """验证URL格式"""
        if not url or not isinstance(url, str):
            return False
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))
    
    def _is_valid_date(self, date_str: str) -> bool:
        """验证日期格式（YYYY-MM-DD）"""
        if not date_str or not isinstance(date_str, str):
            return False
        
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def _is_valid_score_decimal(self, score_decimal: str) -> bool:
        """验证评分小数格式（如 "9.5"）"""
        if not score_decimal or not isinstance(score_decimal, str):
            return False
        
        try:
            score = float(score_decimal)
            return 0.0 <= score <= 10.0
        except ValueError:
            return False
    
    def get_validation_summary(self, valid_cases: List[Dict], invalid_cases: List[Dict]) -> Dict[str, Any]:
        """
        获取验证摘要
        
        Args:
            valid_cases: 有效案例列表
            invalid_cases: 无效案例列表
            
        Returns:
            验证摘要字典
        """
        total = len(valid_cases) + len(invalid_cases)
        valid_count = len(valid_cases)
        invalid_count = len(invalid_cases)
        
        # 统计错误类型
        error_types = {}
        for invalid_case in invalid_cases:
            error = invalid_case.get('validation_error', '未知错误')
            error_types[error] = error_types.get(error, 0) + 1
        
        return {
            'total': total,
            'valid': valid_count,
            'invalid': invalid_count,
            'valid_rate': valid_count / total if total > 0 else 0,
            'error_types': error_types
        }


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    validator = CaseValidator()
    
    # 测试用例
    test_cases = [
        {
            'case_id': 291696,
            'title': '测试案例',
            'source_url': 'https://m.adquan.com/creative/detail/291696',
            'publish_time': '2020-02-14'
        },
        {
            'case_id': 0,  # 无效的case_id
            'title': '测试',
            'source_url': 'invalid-url'
        },
        {
            'case_id': 123456,
            'title': '',  # 空标题
            'source_url': 'https://m.adquan.com/creative/detail/123456'
        }
    ]
    
    valid, invalid = validator.validate_batch(test_cases)
    
    print(f"有效案例: {len(valid)}")
    print(f"无效案例: {len(invalid)}")
    
    for case in invalid:
        print(f"  - case_id={case.get('case_id')}: {case.get('validation_error')}")

