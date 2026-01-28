#!/usr/bin/env python3
"""
对比测试：测试 case_type=0 和 case_type=3 的区别
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.spider.api_client import AdquanAPIClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def test_comparison():
    """对比测试 case_type=0 和 case_type=3"""
    logger.info("=" * 80)
    logger.info("对比测试：case_type=0 vs case_type=3")
    logger.info("=" * 80)
    
    internal_page = 95  # 内部页码95对应API页码96
    
    test_cases = [
        {"case_type": 0, "name": "全部案例 (typeclass=0)"},
        {"case_type": 3, "name": "案例类型3 (typeclass=3)"},
    ]
    
    results = {}
    
    for test_case in test_cases:
        case_type = test_case["case_type"]
        name = test_case["name"]
        
        logger.info("\n" + "=" * 80)
        logger.info(f"测试: {name}")
        logger.info("=" * 80)
        
        try:
            client = AdquanAPIClient()
            data = client.get_creative_list(page=internal_page, case_type=case_type)
            
            # 分析返回数据
            result = {
                "success": True,
                "data_type": type(data).__name__,
                "has_data": False,
                "items_count": 0,
                "response_format": None,
            }
            
            if isinstance(data, dict):
                result["keys"] = list(data.keys())
                
                if 'data' in data:
                    data_content = data['data']
                    if isinstance(data_content, str):
                        result["response_format"] = "HTML"
                        result["data_length"] = len(data_content)
                        # HTML格式需要解析
                        from services.spider.list_page_html_parser import ListPageHTMLParser
                        parser = ListPageHTMLParser(base_url='https://www.adquan.com')
                        items = parser.parse_html(data_content)
                        result["items_count"] = len(items)
                        result["has_data"] = len(items) > 0
                    elif isinstance(data_content, dict):
                        result["response_format"] = "JSON"
                        items = data_content.get('items', [])
                        result["items_count"] = len(items)
                        result["has_data"] = len(items) > 0
                        result["data_keys"] = list(data_content.keys())
            
            results[case_type] = result
            
            logger.info(f"\n测试结果:")
            logger.info(f"  - 响应格式: {result['response_format']}")
            logger.info(f"  - 案例数量: {result['items_count']}")
            logger.info(f"  - 是否有数据: {'是' if result['has_data'] else '否'}")
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
            results[case_type] = {
                "success": False,
                "error": str(e)
            }
    
    # 对比结果
    logger.info("\n" + "=" * 80)
    logger.info("对比结果总结")
    logger.info("=" * 80)
    
    for case_type, result in results.items():
        logger.info(f"\ncase_type={case_type}:")
        if result.get("success"):
            logger.info(f"  - 响应格式: {result.get('response_format')}")
            logger.info(f"  - 案例数量: {result.get('items_count')}")
            logger.info(f"  - 是否有数据: {'是' if result.get('has_data') else '否'}")
        else:
            logger.error(f"  - 测试失败: {result.get('error')}")
    
    return results


if __name__ == '__main__':
    results = test_comparison()
    sys.exit(0)
