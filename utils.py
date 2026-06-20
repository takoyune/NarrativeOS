import socket
import ipaddress
import contextlib
from urllib.parse import urlparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()

_logger = logging.getLogger('narrative_os')
_logger.setLevel(logging.INFO)
_handler = RotatingFileHandler(BASE_DIR / 'narrative_os.log', maxBytes=2*1024*1024, backupCount=1, encoding='utf-8')
_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
_logger.addHandler(_handler)
logging.getLogger("uvicorn.access").addHandler(_handler)
logging.getLogger("uvicorn.error").addHandler(_handler)

def log_event(level: str, message: str):
    lvl = getattr(logging, level.upper(), logging.INFO)
    _logger.log(lvl, message)


BLANK_MAIN_MD_TEMPLATE = """# Main

Title Japan: []
Title Indonesia: []
Title Inggris : []
Title Romanji: []
Volume: []
Author: []
Artist: []
Genres: []
Translator: []
EPUB Compiler : [TakoYune]
Primary Title: [id]

Cover : []

Table of Content[
]
"""

@contextlib.contextmanager
def pin_dns(host, ip):
    _orig_getaddrinfo = socket.getaddrinfo

    def _pinned_getaddrinfo(req_host, port, family=0, type=0, proto=0, flags=0):
        if req_host == host:
            return _orig_getaddrinfo(ip, port, family, type, proto, flags)
        return _orig_getaddrinfo(req_host, port, family, type, proto, flags)
    
    socket.getaddrinfo = _pinned_getaddrinfo
    try:
        yield
    finally:
        socket.getaddrinfo = _orig_getaddrinfo

def get_safe_ip_and_host(url: str):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return None, None
        host = parsed.hostname
        if not host: 
            return None, None
        if host in ('localhost', '127.0.0.1', '::1', '0.0.0.0'):
            return None, None
            
        ip_str = socket.gethostbyname(host)
        ip_obj = ipaddress.ip_address(ip_str)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast:
            return None, None
        return ip_str, host
    except Exception:
        return None, None
