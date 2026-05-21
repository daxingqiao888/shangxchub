#!/usr/bin/env python3
"""
图片采集测试脚本
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sources import ImageCollector
from sources.unsplash import UnsplashSource
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

keyword = "猫咪"
count = 3
storage_path = "/Users/keyangzhi/Downloads/test_images"

collector = ImageCollector(storage_path)

# 使用 Unsplash 备用方案（无API Key）
source = UnsplashSource(collector)
print(f"搜索关键词: {keyword}")
print(f"使用来源: {source.display_name}")

images = source.search(keyword, count)
print(f"找到 {len(images)} 张图片")

for i, img in enumerate(images):
    print(f"下载 {i+1}/{len(images)}... url={img['url'][:80]}...")
    path, info = collector.download_image(
        url=img['url'],
        filename=img['filename'],
        keyword=keyword,
        source='unsplash'
    )
    if path:
        print(f"  ✓ 保存到: {path}")
    else:
        print(f"  ✗ 下载失败")

print("测试完成!")