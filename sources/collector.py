#!/usr/bin/env python3
"""
图片下载核心模块
"""
import os
import json
import hashlib
import time
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
        file_hash = self.compute_hash(file_path)
        hash_file = file_path.with_suffix(file_path.suffix + '.hash')
        if hash_file.exists():
            stored_hash = hash_file.read_text().strip()
            return stored_hash == file_hash
        return False

    def save_hash(self, file_path):
        """保存文件哈希"""
        file_hash = self.compute_hash(file_path)
        hash_file = file_path.with_suffix(file_path.suffix + '.hash')
        hash_file.write_text(file_hash)

    def download_image(self, url, filename, keyword, source, referer=None):
        """下载单张图片"""
        if referer:
            self.session.headers['Referer'] = referer

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, stream=True)
                response.raise_for_status()

                # 创建关键词文件夹
                keyword_folder = self.storage_path / keyword
                keyword_folder.mkdir(parents=True, exist_ok=True)

                # 保存图片
                file_path = keyword_folder / filename

                # 检查是否重复（通过URLHash方式，避免重复下载）
                url_hash = hashlib.md5(url.encode()).hexdigest()[:12]

                # 文件名添加来源和日期
                date_str = datetime.now().strftime("%Y%m%d")
                new_filename = f"{keyword}_{source}_{url_hash}_{date_str}{Path(filename).suffix}"
                file_path = keyword_folder / new_filename

                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                self.save_hash(file_path)

                # 记录来源信息
                source_info = {
                    "filename": new_filename,
                    "keyword": keyword,
                    "source": source,
                    "url": url,
                    "download_date": datetime.now().isoformat(),
                    "local_path": str(file_path)
                }

                # 保存来源记录
                log_file = keyword_folder / f"{source}_downloads.json"

                logs = []
                if log_file.exists():
                    try:
                        logs = json.loads(log_file.read_text(encoding='utf-8'))
                    except:
                        logs = []
                logs.append(source_info)
                log_file.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding='utf-8')

                logger.info(f"✓ 下载成功: {new_filename}")
                return file_path, source_info

            except Exception as e:
                logger.warning(f"下载失败 (尝试 {attempt + 1}/{self.max_retries}): {url} - {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

        return None, None


def create_folders(keyword, base_path):
    """创建分类文件夹"""
    folder = Path(base_path) / keyword
    folder.mkdir(parents=True, exist_ok=True)
    return folder