#!/usr/bin/env python3
"""
Bing Images 图片源 - Playwright 浏览器版本
"""
import logging
from .collector import ImageCollector
from .browser import scrape_images

logger = logging.getLogger(__name__)


class BingSource:
    name = "bing"
    display_name = "Bing Images"

    def __init__(self, collector: ImageCollector):
        self.collector = collector

    def search(self, keyword, count=20):
        url = f"https://cn.bing.com/images/search?q={keyword}"
        selectors = {
            'img_selector': 'img.mimg',
            'url_attr': 'src',
        }
        urls = scrape_images(url, keyword, count, selectors, timeout=30)

        results = []
        for i, url in enumerate(urls):
            if url and url.startswith('http'):
                results.append({
                    'url': url,
                    'filename': f"bing_{i:04d}.jpg",
                    'referer': 'https://cn.bing.com/',
                    'title': keyword,
                })
        return results