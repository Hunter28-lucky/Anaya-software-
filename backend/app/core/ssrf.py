import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple, Optional
from app.core.config import settings


class SSRFValidationError(Exception):
    """Raised when a URL violates SSRF safety rules."""
    pass


BLOCKED_NETWORKS = [
    ipaddress.ip_network(net) for net in settings.BLOCKED_IPS_AND_RANGES
]


def is_ip_allowed(ip_str: str) -> bool:
    """
    Check if an IP address string is allowed (not in private, loopback, link-local, or cloud metadata ranges).
    """
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False

    # Check loopback, private, link-local, multicast, reserved
    if (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return False

    # Explicit subnet check
    for net in BLOCKED_NETWORKS:
        if ip in net:
            return False

    return True


def validate_and_resolve_url(raw_url: str) -> Tuple[str, str]:
    """
    Validates a URL for SSRF vulnerabilities:
    - Verifies scheme is http or https
    - Checks port is in allowed list
    - Resolves host DNS and checks that all resolved IP addresses are safe
    Returns normalized URL and resolved IP address.
    """
    if not raw_url or not isinstance(raw_url, str):
        raise SSRFValidationError("URL cannot be empty")

    url = raw_url.strip()
    if "://" in url:
        scheme_candidate = url.split("://")[0].lower()
        if scheme_candidate not in ("http", "https"):
            raise SSRFValidationError(f"Forbidden URL scheme: {scheme_candidate}. Only HTTP/HTTPS permitted.")
    else:
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise SSRFValidationError(f"Invalid URL structure: {e}")

    if parsed.scheme not in ("http", "https"):
        raise SSRFValidationError(f"Forbidden URL scheme: {parsed.scheme}. Only HTTP/HTTPS permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("Missing hostname in URL")

    # Reject cloud metadata special names
    forbidden_hostnames = {
        "metadata.google.internal",
        "instance-data",
        "localhost",
        "127.0.0.1",
        "::1",
    }
    if hostname.lower() in forbidden_hostnames:
        raise SSRFValidationError(f"Forbidden hostname: {hostname}")

    # Port check
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in settings.ALLOWED_PORTS:
        raise SSRFValidationError(f"Port {port} is not allowed. Allowed ports: {settings.ALLOWED_PORTS}")

    # Resolve IP via socket
    try:
        addr_info = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise SSRFValidationError(f"Failed to resolve DNS for hostname {hostname}: {e}")

    if not addr_info:
        raise SSRFValidationError(f"No address records found for hostname {hostname}")

    resolved_ip = None
    for entry in addr_info:
        sockaddr = entry[4]
        ip_candidate = sockaddr[0]
        if not is_ip_allowed(ip_candidate):
            raise SSRFValidationError(
                f"Hostname {hostname} resolves to prohibited IP address {ip_candidate} (SSRF protection)"
            )
        if not resolved_ip:
            resolved_ip = ip_candidate

    normalized_url = parsed.geturl()
    return normalized_url, resolved_ip
