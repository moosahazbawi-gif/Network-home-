import hashlib
import os
import re
import socket
import unicodedata
import ipaddress
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, urljoin
from requests import Session
from .config import settings

SAFE_NAME_RE = re.compile(r"[^\w.\- ]+", re.UNICODE)

def ensure_data_dirs() -> Path:
    downloads = Path(settings.data_dir) / "files"
    downloads.mkdir(parents=True, exist_ok=True)
    return downloads

def is_public_ip(value: str) -> bool:
    ip = ipaddress.ip_address(value)
    return ip.is_global and not any((ip.is_private, ip.is_loopback, ip.is_link_local, ip.is_multicast, ip.is_reserved, ip.is_unspecified))

def resolve_public_ips(host: str) -> list[str]:
    try:
        literal = ipaddress.ip_address(host)
        return [str(literal)] if is_public_ip(str(literal)) else []
    except ValueError:
        pass
    seen = []
    for _family, _socktype, _proto, _canonname, sockaddr in socket.getaddrinfo(host, None):
        ip = sockaddr[0]
        if ip not in seen and is_public_ip(ip):
            seen.append(ip)
    if not seen:
        raise ValueError("العنوان لا يشير إلى شبكة عامة")
    return seen

def validate_target_url(url: str, allow_http: bool = False) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme not in {"http", "https"}:
        raise ValueError("المخطط غير مسموح")
    if parts.scheme == "http" and not allow_http:
        raise ValueError("HTTP غير مسموح")
    if not parts.hostname:
        raise ValueError("عنوان غير صالح")
    if parts.username or parts.password:
        raise ValueError("بيانات الاعتماد في الرابط غير مسموحة")
    resolve_public_ips(parts.hostname)
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))

def safe_filename(value: str, fallback: str = "download.bin") -> str:
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\\", "")
    value = value.replace(os.sep, "_").replace("/", "_")
    value = re.sub(r"[‌‍]", "", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Cf")
    value = SAFE_NAME_RE.sub("_", value)
    value = re.sub(r"\s+", "_", value).strip("._ ")
    return value or fallback

def filename_from_url(url: str) -> str:
    path = urlsplit(url).path.rsplit("/", 1)[-1]
    return safe_filename(path) if path else "download.bin"

def build_session() -> Session:
    session = Session()
    session.headers.update({"User-Agent": settings.download_user_agent, "Accept": "*/*"})
    return session

def follow_safe_redirects(session: Session, url: str, max_redirects: int) -> tuple[str, list[str]]:
    history = []
    current = url
    for _ in range(max_redirects + 1):
        current = validate_target_url(current, allow_http=settings.download_allow_http)
        history.append(current)
        response = session.get(current, stream=True, allow_redirects=False, timeout=(settings.download_connect_timeout_seconds, settings.download_timeout_seconds))
        try:
            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")
                if not location:
                    raise ValueError("إعادة التوجيه بدون وجهة")
                current = urljoin(current, location)
                continue
            return current, history
        finally:
            response.close()
    raise ValueError("تجاوزت إعادة التوجيه الحد المسموح")
