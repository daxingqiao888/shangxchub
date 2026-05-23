#!/usr/bin/env python3
"""
Unsplash 图片源 - Playwright 版本
"""
import logging
from .collector import ImageCollector
from .browser import scrape_images

logger = logging.getLogger(__name__)

UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"


class UnsplashSource:
    name = "unsplash"
    display_name = "Unsplash"

    def __init__(self, collector: ImageCollector, api_key=None):
        self.collector = collector
        self.api_key = api_key
        if api_key:
            collector.session.headers['Authorization'] = f'Client-ID {api_key}'

    def search(self, keyword, count=20):
        if self.api_key:
            return self._api_search(keyword, count)

        url = f"https://unsplash.com/s/photos/{keyword}"
        urls = scrape_images(url, keyword, count, {
            'img_selector': 'img[src*="images.unsplash.com"]',
            'url_attr': 'src',
        }, timeout=30)

        results = []
        for i, url in enumerate(urls):
            if url and 'images.unsplash.com' in url:
                clean_url = url.split('?')[0] + '?w=1200&q=80'
                results.append({
                    'url': clean_url,
                    'filename': f"unsplash_{i:04d}.jpg",
                    'referer': 'https://unsplash.com/',
                })
        return results

    def _api_search(self, keyword, count):
        results = []
        page = 1
        per_page = min(30, count)
        while len(results) < count:
            try:
                params = {'query': keyword, 'page': page, 'per_page': per_page, 'orientation': 'landscape'}
                response = self.collector.session.get(UNSPLASH_API_URL, params=params, timeout=self.collector.timeout)
                if response.status_code == 200:
                    photos = response.json().get('results', [])
                    if not photos:
                        break
                    for photo in photos:
                        if len(results) >= count:
                            break
                        urls = photo.get('urls', {})
                        img_url = urls.get('regular') or urls.get('small')
                        if img_url:
                            results.append({
                                'url': img_url,
                                'filename': f"{photo.get('id', 'unsplash')}.jpg",
                                'author': photo.get('user', {}).get('name'),
                                'referer': 'https://unsplash.com/'
                            })
                    page += 1
                    logger.info(f"Unsplash API: 第{page-1}页, 累计{len(results)}张")
                else:
                    break
            except Exception as e:
                logger.error(f"Unsplash API 失败: {str(e)}")
                break
        return results