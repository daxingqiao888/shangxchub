#!/usr/bin/env python3
"""
500px 图片源 - Playwright 版本
（需科学上网）
"""
import logging
from .collector import ImageCollector
from .browser import scrape_images

logger = logging.getLogger(__name__)

PX500_API_URL = "https://api.500px.com/v1/photos"


class FiveHundredPxSource:
    name = "500px"
    display_name = "500px"

    def __init__(self, collector: ImageCollector, api_key=None):
        self.collector = collector
        self.api_key = api_key

    def search(self, keyword, count=20):
        if self.api_key:
            return self._api_search(keyword, count)

        url = f"https://500px.com/search?photo=true&q={keyword}&type=photos"
        urls = scrape_images(url, keyword, count, {
            'img_selector': 'img[src*="500px"], img[src*="images.500px"]',
            'url_attr': 'src',
        }, timeout=30)

        results = []
        for i, url in enumerate(urls):
            if url and url.startswith('http'):
                results.append({
                    'url': url,
                    'filename': f"500px_{i:04d}.jpg",
                    'referer': 'https://500px.com/',
                })
        return results

    def _api_search(self, keyword, count):
        results = []
        page = 1
        rpp = min(100, count)
        while len(results) < count:
            try:
                params = {
                    'term': keyword, 'page': page, 'rpp': rpp,
                    'sort': 'released', 'image_size': ['4', '5', '6'],
                    'exclude': 'NSFW', 'consumer_key': self.api_key
                }
                response = self.collector.session.get(PX500_API_URL, params=params, timeout=self.collector.timeout)
                if response.status_code == 200:
                    photos = response.json().get('photos', [])
                    if not photos:
                        break
                    for photo in photos:
                        if len(results) >= count:
                            break
                        images = photo.get('images', [])
                        img_url = None
                        for img in images:
                            if img.get('size') == 6:
                                img_url = img.get('url')
                                break
                        if not img_url and images:
                            img_url = images[0].get('url')
                        if img_url:
                            results.append({
                                'url': img_url,
                                'filename': f"500px_{photo.get('id')}.jpg",
                                'author': photo.get('user', {}).get('fullname'),
                                'referer': 'https://500px.com/'
                            })
                    page += 1
                    logger.info(f"500px API: 第{page-1}页, 累计{len(results)}张")
                else:
                    break
            except Exception as e:
                logger.error(f"500px API 失败: {str(e)}")
                break
        return results