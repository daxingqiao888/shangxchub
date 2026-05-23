#!/usr/bin/env python3
"""代理检测工具 - 自动探测 macOS 系统代理和本地代理端口"""
import subprocess
import logging

logger = logging.getLogger(__name__)

# 常见本地代理端口 (Clash, V2Ray, Shadowsocks 等)
COMMON_PROXY_PORTS = [
    ('127.0.0.1', 7890),   # Clash 默认
    ('127.0.0.1', 7891),   # Clash 备用
    ('127.0.0.1', 1087),   # Shadowsocks
    ('localhost', 1080),   # SOCKS5 通用
    ('127.0.0.1', 8118),   # Privoxy
    ('127.0.0.1', 8080),   # HTTP 通用
]


def detect_system_proxy():
    """自动检测 macOS 系统 HTTP 代理设置"""
    try:
        result = subprocess.run(
            ['networksetup', '-listallnetworkservices'],
            capture_output=True, text=True, timeout=5
        )
        services = [s.strip() for s in result.stdout.split('\n')[1:]
                    if s.strip() and not s.startswith('*')]

        for svc in services:
            for proxy_type in ['-getwebproxy', '-getsecurewebproxy']:
                r = subprocess.run(
                    ['networksetup', proxy_type, svc],
                    capture_output=True, text=True, timeout=5
                )
                out = r.stdout
                if 'Enabled: Yes' in out:
                    server = ''
                    port = ''
                    for line in out.split('\n'):
                        if line.startswith('Server:'):
                            server = line.split(':', 1)[1].strip()
                        if line.startswith('Port:'):
                            port = line.split(':', 1)[1].strip()
                    if server and port:
                        proxy_url = f'http://{server}:{port}'
                        logger.info(f'检测到系统代理: {proxy_url} ({svc})')
                        return proxy_url
    except Exception:
        pass
    return None


def detect_local_proxy():
    """检测常见本地代理端口是否可用"""
    import socket
    for host, port in COMMON_PROXY_PORTS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                proxy_url = f'http://{host}:{port}'
                logger.info(f'检测到本地代理: {proxy_url}')
                return proxy_url
        except Exception:
            continue
    return None


def get_proxy_url():
    """获取代理 URL：优先系统代理 → 本地代理端口 → None"""
    proxy = detect_system_proxy()
    if proxy:
        return proxy
    return detect_local_proxy()
