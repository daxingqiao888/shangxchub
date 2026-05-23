#!/usr/bin/env python3
"""
百度图片源 - Playwright 版本
"""
import logging
from .collector import ImageCollector
from .browser import scrape_images

logger = logging.getLogger(__name__)


class BaiduSource:
    name = "baidu"
    display_name = "百度图片"

    def __init__(self, collector: ImageCollector):
        self.collector = collector

    def search(self, keyword, count=20):
        url = f"https://image.baidu.com/search/index?tn=baiduimage&word={keyword}"
        urls = scrape_images(url, keyword, count, {
            'img_selector': 'img.main_img, img[src*="http"]',
            'url_attr': 'src',
        }, timeout=30)

        results = []
        for i, url in enumerate(urls):
            if url and url.startswith('http') and not url.startswith('data:'):
                results.append({
                    'url': url,
                    'filename': f"baidu_{i:04d}.jpg",
                    'referer': 'https://image.baidu.com/',
                })
        return results