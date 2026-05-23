#!/usr/bin/env python3
"""
网盘管理器 - 自动检测、安装、链接网盘同步目录
"""
import os
import time
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PUBLIC_DIR = Path.home() / '媒体采集'

# 网盘定义：名称, 应用路径, 可能的同步目录
CLOUD_DRIVES = {
    'chinamobile': {
        'name': '中国移动云盘',
        'app': '/Applications/中国移动云盘.app',
        'bundle_id': 'com.cmic.mcloudForMacOSV2',
        'install_url': 'https://yun.139.com/',
        'sync_dirs': [
            '~/移动云盘',
            '~/和彩云',
            '~/ChinaMobileCloud',
        ],
    },
    'baidu': {
        'name': '百度网盘',
        'app': '/Applications/BaiduNetdisk_mac.app',
        'bundle_id': 'com.baidu.BaiduNetdisk-mac',
        'install_url': 'https://pan.baidu.com/download',
        'sync_dirs': [
            '~/百度网盘',
            '~/BaiduNetdisk',
            '~/Documents/BaiduNetdisk',
        ],
    },
    'onedrive': {
        'name': 'OneDrive',
        'app': '/Applications/OneDrive.app',
        'bundle_id': 'com.microsoft.OneDrive',
        'install_url': 'https://onedrive.live.com/about/download/',
        'sync_dirs': [
            '~/OneDrive',
            '~/Library/CloudStorage/OneDrive-Personal',
        ],
    },
    'icloud': {
        'name': 'iCloud 云盘',
        'app': None,  # 系统内置
        'bundle_id': None,
        'install_url': None,
        'sync_dirs': [
            '~/Library/Mobile Documents/com~apple~CloudDocs',
            '~/iCloud Drive',
            '~/iCloud 云盘（归档）',
            '~/Library/CloudStorage/iCloudDrive',
        ],
    },
    'nutstore': {
        'name': '坚果云',
        'app': '/Applications/Nutstore.app',
        'bundle_id': 'com.nutstore.Nutstore',
        'install_url': 'https://www.jianguoyun.com/s/downloads',
        'sync_dirs': [
            '~/坚果云',
            '~/Nutstore',
        ],
    },
    'dropbox': {
        'name': 'Dropbox',
        'app': '/Applications/Dropbox.app',
        'bundle_id': 'com.getdropbox.dropbox',
        'install_url': 'https://www.dropbox.com/downloading',
        'sync_dirs': [
            '~/Dropbox',
            '~/Library/CloudStorage/Dropbox',
        ],
    },
    'aliyun': {
        'name': '阿里云盘',
        'app': '/Applications/阿里云盘.app',
        'bundle_id': None,
        'install_url': 'https://www.aliyundrive.com/download',
        'sync_dirs': [
            '~/阿里云盘',
            '~/AliyunDrive',
        ],
    },
}


def _run(cmd):
    """执行命令"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except:
        return ''


class CloudDriveManager:
    """网盘管理器"""

    def __init__(self):
        self.public_dir = PUBLIC_DIR
        self.public_dir.mkdir(parents=True, exist_ok=True)
        self._drives_cache = None
        self._cache_time = 0

    def list_drives(self):
        """列出所有网盘及其状态（缓存 5 秒 TTL）"""
        now = time.time()
        if self._drives_cache is not None and now - self._cache_time < 5:
            return self._drives_cache

        drives = []
        for key, info in CLOUD_DRIVES.items():
            drive = {
                'key': key,
                'name': info['name'],
                'installed': self._is_installed(info),
                'sync_dir': None,
                'linked': False,
            }
            if drive['installed']:
                drive['sync_dir'] = self._find_sync_dir(info)
                drive['linked'] = self._check_link(key)
            drives.append(drive)
        self._drives_cache = drives
        self._cache_time = now
        return drives

    def _is_installed(self, info):
        """检查网盘是否已安装"""
        if info.get('app') and Path(info['app']).exists():
            return True
        if info.get('bundle_id'):
            bid = info["bundle_id"]
            result = _run(['mdfind', f'kMDItemCFBundleIdentifier == "{bid}"'])
            if result:
                return True
        # 检查同步目录是否存在
        for d in info.get('sync_dirs', []):
            if Path(d).expanduser().exists():
                return True
        return False

    def _find_sync_dir(self, info):
        """查找网盘的同步目录"""
        for d in info.get('sync_dirs', []):
            expanded = Path(d).expanduser()
            if expanded.exists() and expanded.is_dir():
                return str(expanded)
        return None

    def _check_link(self, key):
        """检查公共目录下是否已有链接"""
        link_path = self.public_dir / key
        return link_path.is_symlink()

    def setup_link(self, key):
        """设置网盘同步链接"""
        info = CLOUD_DRIVES.get(key)
        if not info:
            return False, "未知网盘类型"

        if not self._is_installed(info):
            return False, f"{info['name']} 未安装，请先安装"

        sync_dir = self._find_sync_dir(info)
        if not sync_dir:
            # 尝试创建默认同步目录
            for d in info.get('sync_dirs', []):
                expanded = Path(d).expanduser()
                expanded.mkdir(parents=True, exist_ok=True)
                sync_dir = str(expanded)
                logger.info(f"创建网盘同步目录: {sync_dir}")
                break

        if not sync_dir:
            return False, f"无法确定 {info['name']} 的同步目录"

        # 在公共目录下创建链接
        link_path = self.public_dir / key
        if os.path.lexists(str(link_path)):
            if link_path.is_symlink() or link_path.is_file():
                link_path.unlink()
            elif link_path.is_dir():
                import shutil
                shutil.rmtree(link_path)
            else:
                return False, f"{link_path} 已存在且无法处理"

        try:
            link_path.symlink_to(sync_dir)
            logger.info(f"创建链接: {link_path} -> {sync_dir}")
            return True, str(link_path)
        except Exception as e:
            logger.error(f"创建链接失败: {e}")
            return False, f"链接创建失败: {e}"

    def open_app(self, key):
        """打开网盘应用"""
        info = CLOUD_DRIVES.get(key)
        if not info:
            return False

        if info.get('app') and Path(info['app']).exists():
            subprocess.run(['open', info['app']])
            return True
        elif info.get('bundle_id'):
            bid = info["bundle_id"]
            result = _run(['mdfind', f'kMDItemCFBundleIdentifier == "{bid}"', '-name', '.app'])
            if result:
                app_path = result.split('\n')[0]
                subprocess.run(['open', app_path])
                return True
        return False

    def open_install(self, key):
        """打开网盘安装页面"""
        info = CLOUD_DRIVES.get(key)
        if not info:
            return False
        url = info.get('install_url')
        if url:
            subprocess.run(['open', url])
            return True
        return False

    def get_public_dir(self):
        """获取公共目录路径"""
        return str(self.public_dir)