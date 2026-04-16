"""Input validation for config flow (no blocking I/O — DNS is exercised by the probe request)."""

from __future__ import annotations

import ipaddress
import re
from typing import Any

import voluptuous as vol


_METADATA_IPV4 = ipaddress.ip_address("169.254.169.254")

# Hostnames on typical LANs / mDNS; IPs are handled via ipaddress.
_HOST_LABEL = re.compile(r"(?i)[a-z0-9][a-z0-9._-]{0,252}$")


def _is_cloud_metadata_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if ip.version == 4:
        return ip == _METADATA_IPV4
    mapped = ip.ipv4_mapped
    return mapped == _METADATA_IPV4 if mapped is not None else False


def validate_mikiled_host(value: Any) -> str:
    """Normalize and validate a hostname or IP for the device URL."""
    if not isinstance(value, str):
        raise vol.Invalid("invalid_host")

    host = value.strip()
    if not host or len(host) > 253:
        raise vol.Invalid("invalid_host")

    if any(c in host for c in "\x00\r\n\t /@\\#?\"'<>|&;`$()[]{}"):
        raise vol.Invalid("invalid_host")

    if ".." in host:
        raise vol.Invalid("invalid_host")

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        if len(host) > 1 and host.startswith("."):
            raise vol.Invalid("invalid_host")
        if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", host):
            raise vol.Invalid("invalid_host")
        if not _HOST_LABEL.match(host):
            raise vol.Invalid("invalid_host")
        return host

    if _is_cloud_metadata_ip(ip):
        raise vol.Invalid("blocked_host")

    return host


def validate_mikiled_port(value: Any) -> int:
    """TCP port in a sensible range for HTTP services."""
    try:
        port = int(value)
    except (TypeError, ValueError) as err:
        raise vol.Invalid("invalid_port") from err
    if not 1 <= port <= 65535:
        raise vol.Invalid("invalid_port")
    return port


def is_safe_hex_color(value: str) -> bool:
    """Return True if value is six hex digits (device API format without #)."""
    return bool(re.fullmatch(r"[0-9A-Fa-f]{6}", value))
