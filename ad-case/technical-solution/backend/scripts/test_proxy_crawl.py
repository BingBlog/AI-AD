#!/usr/bin/env python3
"""
使用代理测试爬虫功能
用于验证代理是否可以解决405问题
"""
import sys
import os
import logging
from pathlib import Path

# 添加 backend 目录到路径
backend_root = Path(__file__).parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

# 设置代理环境变量（如果未设置）
if not os.environ.get('HTTP_PROXY'):
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
if not os.environ.get('HTTPS_PROXY'):
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'

from services.pipeline.crawl_stage import CrawlStage
from app.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    print("=" * 60)
    print("使用代理测试爬虫功能")
    print("=" * 60)
    
    # 获取代理配置
    proxies = {
        'http': 'http://127.0.0.1:7897',
        'https': 'http://127.0.0.1:7897',
    }
    
    print(f"\n代理配置: {proxies}")
    print("注意: 请确保代理服务正在运行 (http://127.0.0.1:7897)\n")
    
    # 创建测试输出目录
    test_output_dir = Path("data/json/test_proxy_crawl")
    test_output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 创建 CrawlStage 实例（使用代理）
        crawl_stage = CrawlStage(
            output_dir=test_output_dir,
            batch_size=5,  # 小批次用于测试
            delay_range=(2, 3),
            enable_resume=False,
            proxies=proxies
        )
        
        print("✓ CrawlStage 创建成功（使用代理）")
        
        # 测试爬取2页数据
        print("\n开始爬取测试（2页数据）...")
        stats = crawl_stage.crawl(
            start_page=0,
            max_pages=2,
            case_type=3,
            search_value='',
            skip_existing=False
        )
        
        print("\n" + "=" * 60)
        print("爬取结果")
        print("=" * 60)
        print(f"总爬取数: {stats.get('total_crawled', 0)}")
        print(f"总保存数: {stats.get('total_saved', 0)}")
        print(f"总失败数: {stats.get('total_failed', 0)}")
        print(f"保存批次数: {stats.get('batches_saved', 0)}")
        
        if stats.get('total_failed', 0) == 0 and stats.get('total_crawled', 0) > 0:
            print("\n✓ 测试成功！代理可以正常工作")
            print("建议: 在环境变量中设置代理配置，或修改 .env 文件")
        else:
            print("\n✗ 测试失败，请检查代理配置和网络连接")
            
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
