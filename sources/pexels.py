#!/usr/bin/env python3
"""
Pexels 图片源 - Playwright 版本
"""
import logging
from .collector import ImageCollector
from .browser import scrape_images

logger = logging.getLogger(__name__)

PEXELS_API_URL = "https://api.pexels.com/v1/search"


class PexelsSource:
    name = "pexels"
    display_name = "Pexels"

    def __init__(self, collector: ImageCollector, api_key=None):
        self.collector = collector
        self.api_key = api_key
        if api_key:
            collector.session.headers['Authorization'] = api_key

    def search(self, keyword, count=20):
        if self.api_key:
            return self._api_search(keyword, count)

        url = f"https://www.pexels.com/search/{keyword}/"
        urls = scrape_images(url, keyword, count, {
            'img_selector': 'img[src*="images.pexels.com"]',
            'url_attr': 'src',
        }, timeout=30)

        results = []
        for i, url in enumerate(urls):
            if url and 'images.pexels.com' in url:
                clean_url = url.split('?')[0] + '?w=1200&h=800&fit=crop'
                results.append({
                    'url': clean_url,
                    'filename': f"pexels_{i:04d}.jpg",
                    'referer': 'https://www.pexels.com/',
                })
        return results

    def _api_search(self, keyword, count):
        results = []
        page = 1
        per_page = min(80, count)
        while len(results) < count:
            try:
                params = {'query': keyword, 'page': page, 'per_page': per_page, 'orientation': 'landscape'}
                response = self.collector.session.get(PEXELS_API_URL, params=params, timeout=self.collector.timeout)
                if response.status_code == 200:
                    photos = response.json().get('photos', [])
                    if not photos:
                        break
                    for photo in photos:
                        if len(results) >= count:
                            break
                        src = photo.get('src', {})
                        img_url = src.get('large2x') or src.get('large') or src.get('medium')
                        if img_url:
                            results.append({
                                'url': img_url,
                                'filename': f"{photo.get('id', 'pexels')}.jpg",
                                'author': photo.get('photographer'),
                                'referer': 'https://www.pexels.com/'
                            })
                    page += 1
                    logger.info(f"Pexels API: 第{page-1}页, 累计{len(results)}张")
                else:
                    break
            except Exception as e:
                logger.error(f"Pexels API 失败: {str(e)}")
                break
        return results