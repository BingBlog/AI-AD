#!/usr/bin/env python3
"""
测试详情页爬取功能
爬取列表页第一页的数据，解析每个案例的详情页，并保存到JSON文件
"""

import json
import logging
import time
from pathlib import Path
from services.spider.api_client import AdquanAPIClient
from services.spider.detail_parser import DetailPageParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    print("=" * 60)
    print("详情页爬取测试")
    print("=" * 60)
    
    # 创建输出目录
    output_dir = Path('data/json')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. 创建API客户端，获取列表页数据
        print("\n【步骤1】获取列表页第一页数据...")
        api_client = AdquanAPIClient()
        list_data = api_client.get_creative_list(page=0, case_type=3)  # 3=精选案例
        
        if not isinstance(list_data, dict) or 'data' not in list_data:
            print("✗ 获取列表数据失败")
            return
        
        items = list_data['data'].get('items', [])
        print(f"✓ 获取到 {len(items)} 个案例")
        
        if not items:
            print("✗ 列表为空，无法继续")
            return
        
        # 2. 创建详情页解析器（使用API客户端的Session）
        print("\n【步骤2】初始化详情页解析器...")
        detail_parser = DetailPageParser(session=api_client.session)
        print("✓ 详情页解析器初始化完成")
        
        # 3. 遍历每个案例，解析详情页
        print(f"\n【步骤3】开始解析详情页（共 {len(items)} 个案例）...")
        print("-" * 60)
        
        all_cases = []
        success_count = 0
        fail_count = 0
        
        for i, item in enumerate(items, 1):
            case_url = item.get('url')
            case_title = item.get('title', '未知标题')
            
            if not case_url:
                logger.warning(f"[{i}/{len(items)}] 跳过：没有URL")
                fail_count += 1
                continue
            
            print(f"\n[{i}/{len(items)}] 解析: {case_title}")
            print(f"  URL: {case_url}")
            
            try:
                # 解析详情页
                detail_data = detail_parser.parse(case_url)
                
                # 合并列表页和详情页的数据
                merged_data = {
                    # 列表页数据
                    'case_id': item.get('id'),
                    'score': item.get('score'),
                    'score_decimal': item.get('score_decimal'),
                    'favourite': item.get('favourite'),
                    'company_name': item.get('company_name'),
                    'company_logo': item.get('company_logo'),
                    'thumb': item.get('thumb'),
                    # 详情页数据
                    **detail_data
                }
                
                all_cases.append(merged_data)
                success_count += 1
                
                print(f"  ✓ 解析成功")
                print(f"    标题: {merged_data.get('title')}")
                print(f"    描述长度: {len(merged_data.get('description', ''))} 字符")
                print(f"    图片数: {len(merged_data.get('images', []))}")
                
                # 请求延迟，避免过快
                if i < len(items):  # 最后一个不需要延迟
                    time.sleep(2)  # 延迟2秒
                    
            except Exception as e:
                logger.error(f"  ✗ 解析失败: {e}")
                fail_count += 1
                # 即使失败也保存基本信息
                all_cases.append({
                    'case_id': item.get('id'),
                    'url': case_url,
                    'title': case_title,
                    'error': str(e),
                    'score': item.get('score'),
                    'score_decimal': item.get('score_decimal'),
                    'favourite': item.get('favourite'),
                })
                continue
        
        # 4. 保存到JSON文件
        print(f"\n【步骤4】保存数据到JSON文件...")
        print("-" * 60)
        
        output_file = output_dir / 'cases_page_0.json'
        
        output_data = {
            'total': len(all_cases),
            'success': success_count,
            'failed': fail_count,
            'cases': all_cases
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 数据已保存到: {output_file}")
        print(f"  总案例数: {len(all_cases)}")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
        
        # 5. 显示统计信息
        print(f"\n【统计信息】")
        print("-" * 60)
        print(f"总案例数: {len(all_cases)}")
        print(f"成功解析: {success_count}")
        print(f"解析失败: {fail_count}")
        
        if all_cases:
            # 统计有描述的案例数
            with_desc = sum(1 for case in all_cases if case.get('description'))
            print(f"有完整描述: {with_desc}")
            
            # 统计有图片的案例数
            with_images = sum(1 for case in all_cases if case.get('images'))
            print(f"有图片集合: {with_images}")
            
            # 统计有视频的案例数
            with_video = sum(1 for case in all_cases if case.get('video_url'))
            print(f"有视频: {with_video}")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()


