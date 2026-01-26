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
        # 支持字符串类型的 case_id（向后兼容），自动转换为整数
        if isinstance(case_id, str):
            try:
                case_id = int(case_id)
            except ValueError:
                return False, f"无效的case_id: {case.get('case_id')}（无法转换为整数）"
        # 验证必须是正整数
        if not isinstance(case_id, int) or case_id <= 0:
            return False, f"无效的case_id: {case.get('case_id')}"
        
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
        # score 是整数评分（0-5），可以为 NULL
        score = case.get('score')
        if score is not None:
            try:
                if isinstance(score, str):
                    score_value = float(score)
                elif isinstance(score, (int, float)):
                    score_value = float(score)
                else:
                    return False, f"无效的评分类型: {type(score)}"
                
                # score 应该在 0.0 到 5.0 之间
                if not (0.0 <= score_value <= 5.0):
                    return False, f"无效的评分: {score}，应在0.0-5.0之间"
            except (ValueError, TypeError):
                return False, f"无效的评分: {score}，无法转换为数字"
        
        # 7. 验证score_decimal（如果存在）
        score_decimal = case.get('score_decimal')
        if score_decimal is not None:
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
    
    def _is_valid_score_decimal(self, score_decimal) -> bool:
        """验证评分小数格式（如 "9.5" 或 9.5 或 10）"""
        if score_decimal is None:
            return False
        
        # 支持字符串和数字类型
        try:
            if isinstance(score_decimal, str):
                score = float(score_decimal)
            elif isinstance(score_decimal, (int, float)):
                score = float(score_decimal)
            else:
                return False
            
            # 允许 0.0 到 10.0 之间的值（包括 10.0）
            # 使用 math.isclose 来处理浮点数精度问题，或者直接使用 <= 比较
            # 对于整数 10，float(10) = 10.0，所以 10.0 <= 10.0 应该为 True
            return 0.0 <= score <= 10.0
        except (ValueError, TypeError):
            return False
    
    def format_case(self, case: Dict[str, Any], normalize: bool = True) -> Dict[str, Any]:
        """
        格式化案例数据，将数据转换为可以入库的格式
        
        Args:
            case: 案例数据字典
            normalize: 是否进行数据规范化（将非法值转为默认值或NULL）
            
        Returns:
            格式化后的案例数据字典
        """
        formatted_case = case.copy()
        
        # 1. 格式化 case_id（确保是整数）
        case_id = formatted_case.get('case_id')
        if case_id is not None:
            try:
                if isinstance(case_id, str):
                    formatted_case['case_id'] = int(case_id)
                elif not isinstance(case_id, int):
                    formatted_case['case_id'] = int(case_id)
            except (ValueError, TypeError):
                if normalize:
                    # 如果无法转换，设为 None（但验证时会失败）
                    formatted_case['case_id'] = None
                pass
        
        # 2. 格式化 score（0-5 整数，非法值转为 NULL）
        score = formatted_case.get('score')
        if score is not None:
            try:
                if isinstance(score, str):
                    score_value = float(score)
                elif isinstance(score, (int, float)):
                    score_value = float(score)
                else:
                    score_value = None
                
                if score_value is not None:
                    # 转换为整数（四舍五入）
                    score_int = int(round(score_value))
                    # 检查范围：0-5
                    if 0 <= score_int <= 5:
                        formatted_case['score'] = score_int
                    else:
                        # 超出范围，转为 NULL
                        if normalize:
                            formatted_case['score'] = None
                        else:
                            formatted_case['score'] = score_int
                else:
                    if normalize:
                        formatted_case['score'] = None
            except (ValueError, TypeError):
                if normalize:
                    formatted_case['score'] = None
        
        # 3. 格式化 favourite（确保是非负整数）
        favourite = formatted_case.get('favourite')
        if favourite is not None:
            try:
                if isinstance(favourite, str):
                    favourite_value = int(favourite)
                elif isinstance(favourite, (int, float)):
                    favourite_value = int(favourite)
                else:
                    favourite_value = None
                
                if favourite_value is not None:
                    if favourite_value < 0:
                        if normalize:
                            formatted_case['favourite'] = 0
                        else:
                            formatted_case['favourite'] = favourite_value
                    else:
                        formatted_case['favourite'] = favourite_value
                else:
                    if normalize:
                        formatted_case['favourite'] = 0
            except (ValueError, TypeError):
                if normalize:
                    formatted_case['favourite'] = 0
        
        # 4. 格式化 publish_time（确保是 YYYY-MM-DD 格式）
        publish_time = formatted_case.get('publish_time')
        if publish_time and isinstance(publish_time, str):
            # 尝试解析日期，如果格式不对，保持原值（验证时会失败）
            try:
                datetime.strptime(publish_time, '%Y-%m-%d')
            except ValueError:
                # 尝试其他格式
                pass
        
        # 5. 确保 images 和 tags 是列表
        if 'images' in formatted_case and not isinstance(formatted_case['images'], list):
            if normalize:
                formatted_case['images'] = []
            else:
                formatted_case['images'] = []
        
        if 'tags' in formatted_case and not isinstance(formatted_case['tags'], list):
            if normalize:
                formatted_case['tags'] = []
            else:
                formatted_case['tags'] = []
        
        # 6. 截断字符串字段以符合数据库约束
        def truncate_string(value: Any, max_length: int) -> Optional[str]:
            """截断字符串到指定长度"""
            if value is None:
                return None
            if isinstance(value, str):
                return value[:max_length] if len(value) > max_length else value
            return str(value)[:max_length] if len(str(value)) > max_length else str(value)
        
        # 根据数据库表结构截断字段
        formatted_case['title'] = truncate_string(formatted_case.get('title'), 500)  # VARCHAR(500)
        formatted_case['author'] = truncate_string(formatted_case.get('author'), 100)  # VARCHAR(100)
        formatted_case['brand_name'] = truncate_string(formatted_case.get('brand_name'), 200)  # VARCHAR(200)
        formatted_case['brand_industry'] = truncate_string(formatted_case.get('brand_industry'), 100)  # VARCHAR(100)
        formatted_case['activity_type'] = truncate_string(formatted_case.get('activity_type'), 100)  # VARCHAR(100)
        formatted_case['location'] = truncate_string(formatted_case.get('location'), 100)  # VARCHAR(100)
        formatted_case['score_decimal'] = truncate_string(formatted_case.get('score_decimal'), 10)  # VARCHAR(10)
        formatted_case['company_name'] = truncate_string(formatted_case.get('company_name'), 200)  # VARCHAR(200)
        formatted_case['agency_name'] = truncate_string(formatted_case.get('agency_name'), 200)  # VARCHAR(200)
        
        return formatted_case
    
    def format_batch(self, cases: List[Dict[str, Any]], normalize: bool = True) -> List[Dict[str, Any]]:
        """
        批量格式化案例数据
        
        Args:
            cases: 案例数据列表
            normalize: 是否进行数据规范化
            
        Returns:
            格式化后的案例数据列表
        """
        formatted_cases = []
        for case in cases:
            formatted_case = self.format_case(case, normalize=normalize)
            formatted_cases.append(formatted_case)
        
        return formatted_cases
    
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

