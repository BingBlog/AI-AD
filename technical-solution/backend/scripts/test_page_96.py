#!/usr/bin/env python3
"""
测试获取第96页列表数据
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


def test_page_96():
    """测试获取第96页数据"""
    logger.info("=" * 80)
    logger.info("开始测试获取第96页数据")
    logger.info("=" * 80)
    
    try:
        # 创建API客户端
        logger.info("初始化API客户端...")
        client = AdquanAPIClient()
        
        # 内部页码是95（因为从0开始，96页对应内部页码95）
        internal_page = 95
        api_page = 96  # API实际使用的页码
        
        logger.info(f"测试参数:")
        logger.info(f"  - 内部页码: {internal_page}")
        logger.info(f"  - API页码: {api_page}")
        logger.info(f"  - 案例类型: 0 (全部)")
        
        # 获取第96页数据（内部页码95，case_type=0表示全部）
        logger.info(f"\n开始请求第{api_page}页数据...")
        data = client.get_creative_list(page=internal_page, case_type=0)
        
        logger.info("\n" + "=" * 80)
        logger.info("请求成功！")
        logger.info("=" * 80)
        
        # 解析结果
        if isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], dict):
                items = data['data'].get('items', [])
                logger.info(f"\n解析结果:")
                logger.info(f"  - 案例数量: {len(items)}")
                
                if items:
                    logger.info(f"\n前3个案例信息:")
                    for i, item in enumerate(items[:3], 1):
                        logger.info(f"\n案例 {i}:")
                        logger.info(f"  - ID: {item.get('id')}")
                        logger.info(f"  - 标题: {item.get('title')}")
                        logger.info(f"  - URL: {item.get('url')}")
                        logger.info(f"  - 评分: {item.get('score')}")
                        logger.info(f"  - 公司: {item.get('company_name')}")
                else:
                    logger.warning("⚠️ 未获取到任何案例数据")
            else:
                logger.warning(f"⚠️ 响应数据格式异常: {data}")
        else:
            logger.warning(f"⚠️ 响应数据不是字典格式: {type(data)}")
        
        logger.info("\n" + "=" * 80)
        logger.info("测试完成")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error("测试失败")
        logger.error("=" * 80)
        logger.error(f"错误: {e}")
        import traceback
        logger.error(f"异常堆栈:\n{traceback.format_exc()}")
        return False


if __name__ == '__main__':
    success = test_page_96()
    sys.exit(0 if success else 1)
