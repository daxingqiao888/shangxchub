#!/usr/bin/env python3
"""
图片下载核心模块
"""
import io
import json
import hashlib
import time
import logging
from datetime import datetime
from pathlib import Path
import requests

logger = logging.getLogger(__name__)


class ImageCollector:
    """图片采集器核心类"""

    def __init__(self, storage_path, max_retries=3, timeout=30):
        self.storage_path = Path(storage_path)
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # 从配置文件加载代理设置
        self._load_proxy()

    def _load_proxy(self):
        """从项目配置文件加载代理设置，未配置时自动检测系统代理"""
        project_config = Path(__file__).parent.parent / 'config.json'
        if project_config.exists():
            try:
                data = json.loads(project_config.read_text(encoding='utf-8'))
                proxy = data.get('proxy', {})
                if proxy.get('enabled'):
                    if proxy.get('server'):
                        server = proxy['server']
                    else:
                        from utils.proxy import get_proxy_url
                        server = get_proxy_url()
                    if server:
                        auth_prefix = ''
                        if proxy.get('username'):
                            auth_prefix = f"{proxy['username']}:{proxy.get('password', '')}@"
                        scheme = server.split('://')[0] if '://' in server else 'http'
                        proxy_url = f"{scheme}://{auth_prefix}{server.split('://', 1)[-1]}" if '://' in server else server
                        self.session.proxies.update({'http': proxy_url, 'https': proxy_url})
                        logger.info(f"已启用下载代理: {server}")
            except Exception as e:
                logger.warning(f"代理配置加载失败: {e}")

    def compute_hash(self, file_path):
        """计算文件MD5哈希用于去重"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def is_duplicate(self, file_path):
        """检查文件是否已存在（通过哈希）"""
        if not file_path.exists():
            return False
        hash_file = file_path.with_suffix(file_path.suffix + '.hash')
        if not hash_file.exists():
            return False
        file_hash = self.compute_hash(file_path)
        stored_hash = hash_file.read_text().strip()
        return stored_hash == file_hash

    def save_hash(self, file_path):
        """保存文件哈希"""
        file_hash = self.compute_hash(file_path)
        hash_file = file_path.with_suffix(file_path.suffix + '.hash')
        hash_file.write_text(file_hash)

    def download_image(self, url, filename, keyword, source, referer=None):
        """下载单张图片"""
        orig_referer = self.session.headers.get('Referer')
        if referer:
            self.session.headers['Referer'] = referer

        try:
            for attempt in range(self.max_retries):
                try:
                    response = self.session.get(url, timeout=self.timeout, stream=True)
                    response.raise_for_status()

                    # 创建关键词文件夹
                    keyword_folder = self.storage_path / keyword
                    keyword_folder.mkdir(parents=True, exist_ok=True)

                    # 文件名添加来源和日期
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                    date_str = datetime.now().strftime("%Y%m%d")
                    new_filename = f"{keyword}_{source}_{url_hash}_{date_str}{Path(filename).suffix}"
                    file_path = keyword_folder / new_filename

                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    self.save_hash(file_path)

                    source_info = {
                        "filename": new_filename,
                        "keyword": keyword,
                        "source": source,
                        "url": url,
                        "download_date": datetime.now().isoformat(),
                        "local_path": str(file_path)
                    }

                    # 追加模式写入日志（避免 O(n^2) 全量读取）
                    log_file = keyword_folder / f"{source}_downloads.json"
                    entry = json.dumps(source_info, ensure_ascii=False)
                    if log_file.exists():
                        with open(log_file, 'r+', encoding='utf-8') as lf:
                            lf.seek(0, io.SEEK_END)
                            pos = lf.tell()
                            if pos > 2:
                                lf.seek(pos - 1)
                                lf.write(',\n  ' + entry + '\n]')
                            else:
                                lf.write('[\n  ' + entry + '\n]')
                    else:
                        log_file.write_text('[\n  ' + entry + '\n]', encoding='utf-8')

                    logger.info(f"✓ 下载成功: {new_filename}")
                    return file_path, source_info

                except Exception as e:
                    logger.warning(f"下载失败 (尝试 {attempt + 1}/{self.max_retries}): {url} - {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
        finally:
            if orig_referer:
                self.session.headers['Referer'] = orig_referer
            elif 'Referer' in self.session.headers:
                del self.session.headers['Referer']

        return None, None


def create_folders(keyword, base_path):
    """创建分类文件夹"""
    folder = Path(base_path) / keyword
    folder.mkdir(parents=True, exist_ok=True)
    return folder