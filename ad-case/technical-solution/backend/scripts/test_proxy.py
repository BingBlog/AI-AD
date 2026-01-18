#!/usr/bin/env python3
"""
测试代理是否可以解决405问题
"""
import sys
import logging
from pathlib import Path

# 添加 backend 目录到路径
backend_root = Path(__file__).parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from services.spider.api_client import AdquanAPIClient
from services.spider.detail_parser import DetailPageParser

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_without_proxy():
    """测试不使用代理"""
    print("=" * 60)
    print("测试1: 不使用代理")
    print("=" * 60)
    
    try:
        client = AdquanAPIClient()
        print("✓ API客户端创建成功（无代理）")
        
        # 测试获取第一页
        print("\n尝试获取第一页数据...")
        data = client.get_creative_list(page=0)
        
        print(f"✓ 请求成功！")
        print(f"  状态码: 200")
        if isinstance(data, dict) and 'data' in data:
            items = data['data'].get('items', [])
            print(f"  获取到 {len(items)} 个案例")
            if items:
                print(f"  第一个案例ID: {items[0].get('id')}")
        return True
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        if "405" in str(e) or "Method Not Allowed" in str(e):
            print("  检测到405错误 - IP可能被封禁")
        return False


def test_with_proxy():
    """测试使用代理"""
    print("\n" + "=" * 60)
    print("测试2: 使用代理 http://127.0.0.1:7897")
    print("=" * 60)
    
    # 配置代理
    proxies = {
        'http': 'http://127.0.0.1:7897',
        'https': 'http://127.0.0.1:7897',
    }
    
    try:
        client = AdquanAPIClient(proxies=proxies)
        print("✓ API客户端创建成功（使用代理）")
        
        # 测试获取第一页
        print("\n尝试获取第一页数据...")
        data = client.get_creative_list(page=0)
        
        print(f"✓ 请求成功！")
        print(f"  状态码: 200")
        if isinstance(data, dict) and 'data' in data:
            items = data['data'].get('items', [])
            print(f"  获取到 {len(items)} 个案例")
            if items:
                print(f"  第一个案例ID: {items[0].get('id')}")
                print(f"  第一个案例标题: {items[0].get('title', 'N/A')[:50]}")
        
        # 测试详情页解析
        if items:
            print("\n测试详情页解析...")
            detail_url = items[0].get('url')
            if detail_url:
                parser = DetailPageParser(proxies=proxies)
                detail_data = parser.parse(detail_url)
                print(f"✓ 详情页解析成功")
                print(f"  标题: {detail_data.get('title', 'N/A')[:50]}")
                print(f"  描述长度: {len(detail_data.get('description', ''))} 字符")
        
        return True
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_pages_with_proxy():
    """测试使用代理获取多页数据"""
    print("\n" + "=" * 60)
    print("测试3: 使用代理获取多页数据（测试3页）")
    print("=" * 60)
    
    proxies = {
        'http': 'http://127.0.0.1:7897',
        'https': 'http://127.0.0.1:7897',
    }
    
    try:
        client = AdquanAPIClient(proxies=proxies)
        print("✓ API客户端创建成功（使用代理）")
        
        success_count = 0
        fail_count = 0
        
        for page in range(3):
            try:
                print(f"\n获取第 {page} 页...")
                data = client.get_creative_list(page=page)
                if isinstance(data, dict) and 'data' in data:
                    items = data['data'].get('items', [])
                    print(f"  ✓ 成功获取 {len(items)} 个案例")
                    success_count += 1
                else:
                    print(f"  ✗ 数据格式异常")
                    fail_count += 1
            except Exception as e:
                print(f"  ✗ 获取失败: {e}")
                fail_count += 1
        
        print(f"\n测试结果:")
        print(f"  成功: {success_count} 页")
        print(f"  失败: {fail_count} 页")
        
        return fail_count == 0
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("代理测试脚本")
    print("=" * 60)
    print("\n注意: 请确保代理服务正在运行 (http://127.0.0.1:7897)")
    print("如果代理未运行，测试2和测试3将失败\n")
    
    # 测试1: 不使用代理
    result1 = test_without_proxy()
    
    # 测试2: 使用代理
    result2 = test_with_proxy()
    
    # 测试3: 使用代理获取多页
    result3 = test_multiple_pages_with_proxy()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"测试1 (无代理): {'✓ 通过' if result1 else '✗ 失败'}")
    print(f"测试2 (有代理): {'✓ 通过' if result2 else '✗ 失败'}")
    print(f"测试3 (多页): {'✓ 通过' if result3 else '✗ 失败'}")
    
    if result2 and result3:
        print("\n✓ 代理测试成功！代理可以解决405问题")
        print("建议: 在爬虫任务中启用代理配置")
    elif not result1 and result2:
        print("\n✓ 代理有效！不使用代理时出现405错误，使用代理后成功")
        print("建议: 在爬虫任务中启用代理配置")
    elif result1:
        print("\n注意: 不使用代理也能成功，可能IP未被封禁")
    else:
        print("\n✗ 代理测试失败，请检查代理配置")


if __name__ == '__main__':
    main()
