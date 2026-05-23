#!/usr/bin/env python3
"""
通用媒体来源 - 基于配置的浏览器爬取源
"""
import re
import logging
from .browser import scrape_images as browser_scrape
from .collector import ImageCollector

logger = logging.getLogger(__name__)


class GenericSource:
    """通用媒体来源 - 用配置驱动"""

    def __init__(self, collector, source_key, source_config):
        self.collector = collector
        self.key = source_key
        self.config = source_config
        self.name = source_config['name']

    def search(self, keyword, count=20):
        url = self.config['url'].format(keyword=keyword)
        selector = self.config.get('selector', 'img[src*="http"]')
        proxy_needed = self.config.get('proxy', False)

        if proxy_needed:
            logger.info(f"{self.name}: 需要代理访问")

        urls = browser_scrape(
            url, keyword, count,
            selectors={'img_selector': selector, 'url_attr': 'src'},
            timeout=30
        )

        results = []
        for i, url in enumerate(urls):
            if not url or not url.startswith('http') or url.startswith('data:'):
                continue

            ext = self._guess_extension(url)
            filename = f"{self.key}_{i:04d}{ext}"

            results.append({
                'url': url,
                'filename': filename,
                'referer': self.config['url'].split('/')[0] + '//' + self.config['url'].split('/')[2],
                'title': keyword,
            })

        return results

    def _guess_extension(self, url):
        """根据URL猜测文件扩展名"""
        url_lower = url.split('?')[0].lower()
        for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg',
                     '.mp4', '.webm', '.mov', '.avi', '.mkv',
                     '.mp3', '.wav', '.ogg', '.pdf', '.ico']:
            if ext in url_lower:
                return ext
        return '.jpg'