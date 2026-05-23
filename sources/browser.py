#!/usr/bin/env python3
"""
Playwright 浏览器爬取工具 - 支持代理
"""
import asyncio
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PwTimeoutError

logger = logging.getLogger(__name__)

_cached_browser_path = None
_cached_proxy = None
_config_mtime = 0
_event_loop = None


def _load_proxy():
    """从配置文件加载代理设置，自动检测系统代理（缓存结果）"""
    global _cached_proxy, _config_mtime
    config_path = Path(__file__).parent.parent / 'config.json'
    if config_path.exists():
        mtime = config_path.stat().st_mtime
        if _cached_proxy is not None and mtime == _config_mtime:
            return _cached_proxy
        _config_mtime = mtime
        try:
            data = json.loads(config_path.read_text(encoding='utf-8'))
            proxy = data.get('proxy', {})
            if proxy.get('enabled'):
                if proxy.get('server'):
                    _cached_proxy = proxy
                    return _cached_proxy
                from utils.proxy import get_proxy_url
                auto = get_proxy_url()
                if auto:
                    _cached_proxy = {'server': auto}
                    return _cached_proxy
        except:
            pass
    _cached_proxy = None
    return None


def _find_browser():
    """查找可用的浏览器：Playwright Chromium → 系统 Chrome → 系统 Edge（缓存结果）"""
    global _cached_browser_path
    if _cached_browser_path is not None:
        return _cached_browser_path
    if _cached_browser_path is False:
        return None
    system_browsers = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
    ]
    for path in system_browsers:
        if Path(path).exists():
            _cached_browser_path = path
            return path
    _cached_browser_path = False
    return None


def _get_event_loop():
    """获取或创建复用的 asyncio event loop"""
    global _event_loop
    if _event_loop is None or _event_loop.is_closed():
        _event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_event_loop)
    return _event_loop


async def _scrape_images(url, keyword, count, selectors, timeout=30):
    results = []
    proxy = _load_proxy()

    async with async_playwright() as p:
        launch_args = {'headless': True}

        # 优先使用系统浏览器（无需安装 Playwright Chromium）
        browser_path = _find_browser()
        if browser_path:
            launch_args['executable_path'] = browser_path

        if proxy:
            launch_args['proxy'] = {'server': proxy['server']}
            if proxy.get('username'):
                launch_args['proxy']['username'] = proxy['username']
            if proxy.get('password'):
                launch_args['proxy']['password'] = proxy['password']

        browser = await p.chromium.launch(**launch_args)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            await page.goto(url, timeout=timeout * 1000, wait_until='domcontentloaded')
            await page.wait_for_timeout(2000)

            # 滚动加载更多图片
            for _ in range(3):
                await page.evaluate('window.scrollBy(0, window.innerHeight)')
                await page.wait_for_timeout(1000)

            img_selector = selectors.get('img_selector', 'img')
            url_attr = selectors.get('url_attr', 'src')

            images = await page.query_selector_all(img_selector)
            seen = set()

            for img in images:
                if len(results) >= count:
                    break
                try:
                    url_val = await img.get_attribute(url_attr)
                    if not url_val:
                        url_val = await img.get_attribute('src')
                    if not url_val or url_val.startswith('data:') or url_val.startswith('javascript:'):
                        continue
                    if url_val.startswith('http') and url_val not in seen:
                        seen.add(url_val)
                        results.append(url_val)
                except:
                    continue

            logger.info(f"浏览器爬取: 找到 {len(results)} 个图片")

        except PwTimeoutError:
            logger.error(f"页面加载超时: {url}")
        except Exception as e:
            logger.error(f"浏览器爬取失败: {str(e)}")
        finally:
            await browser.close()

    return results


def scrape_images(url, keyword, count, selectors=None, timeout=30):
    if selectors is None:
        selectors = {'img_selector': 'img', 'url_attr': 'src'}
    loop = _get_event_loop()
    return loop.run_until_complete(_scrape_images(url, keyword, count, selectors, timeout))