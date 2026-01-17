#!/usr/bin/env python3
"""
获取广告门API的最大条数
通过遍历分页直到返回空数据来确定最大条数
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.spider.api_client import AdquanAPIClient
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_max_cases(max_pages_to_check: int = 1000) -> dict:
    """
    获取广告门API的最大条数
    
    Args:
        max_pages_to_check: 最大检查页数（防止无限循环）
    
    Returns:
        包含最大条数信息的字典
    """
    client = AdquanAPIClient()
    
    print(f"开始检查最大条数...")
    print(f"每页大小: 15 个案例")
    print(f"最大检查页数: {max_pages_to_check}")
    print("-" * 60)
    
    total_items = 0
    last_page_with_data = 0
    empty_pages_count = 0
    
    # 从第0页开始遍历
    for page in range(max_pages_to_check):
        try:
            data = client.get_creative_list(page=page)
            
            if isinstance(data, dict) and 'data' in data:
                items = data['data'].get('items', [])
                
                if len(items) > 0:
                    total_items += len(items)
                    last_page_with_data = page
                    empty_pages_count = 0  # 重置空页计数
                    
                    if page % 10 == 0:  # 每10页打印一次进度
                        print(f"  第 {page} 页: {len(items)} 个案例，累计: {total_items} 个")
                else:
                    empty_pages_count += 1
                    if empty_pages_count >= 3:  # 连续3页为空，认为已到末尾
                        print(f"\n连续3页返回空数据，停止检查")
                        break
            else:
                print(f"  第 {page} 页返回数据格式异常")
                break
                
        except Exception as e:
            print(f"  第 {page} 页请求失败: {e}")
            break
    
    # 计算最大条数
    # 由于每页15个，最后一页可能不满15个
    # 最大条数 = (最后一页页码 + 1) * 15，但实际可能更少
    max_possible = (last_page_with_data + 1) * 15
    
    result = {
        'last_page_with_data': last_page_with_data,
        'total_items_found': total_items,
        'max_possible_items': max_possible,
        'items_per_page': 15,
        'note': 'API未返回total字段，通过遍历分页获取'
    }
    
    return result

def main():
    print("=" * 60)
    print("获取广告门API的最大条数")
    print("=" * 60)
    
    try:
        result = get_max_cases(max_pages_to_check=1000)
        
        print(f"\n结果:")
        print(f"  最后有数据的页码: {result['last_page_with_data']}")
        print(f"  累计找到的案例数: {result['total_items_found']}")
        print(f"  最大可能案例数: {result['max_possible_items']}")
        print(f"  每页大小: {result['items_per_page']}")
        
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()
        result = None
    
    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    
    if result:
        print(f"\n最大条数: 约 {result['total_items_found']} - {result['max_possible_items']} 个")
        print(f"(实际找到: {result['total_items_found']} 个)")
    
    # 保存结果到JSON文件
    if result:
        output_file = Path(__file__).parent.parent / 'data' / 'json' / 'max_cases_info.json'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n结果已保存到: {output_file}")
    print("=" * 60)

if __name__ == '__main__':
    main()
