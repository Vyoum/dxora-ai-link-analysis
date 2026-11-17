import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit


class UnsafeUrlError(ValueError):
    pass


Resolver = Callable[[str, int], Awaitable[list[tuple]]]


async def _system_resolver(host: str, port: int) -> list[tuple]:
    return await asyncio.to_thread(socket.getaddrinfo, host, port, type=socket.SOCK_STREAM)


def _is_public(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return bool(ip.is_global)


async def validate_public_url(url: str, resolver: Resolver = _system_resolver) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError("Only http and https URLs are supported")
    if not parsed.hostname or parsed.username or parsed.password:
        raise UnsafeUrlError("URL must contain a public hostname and no credentials")
    if len(url) > 2048:
        raise UnsafeUrlError("URL is too long")

    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost"):
        raise UnsafeUrlError("Local network destinations are not allowed")

    try:
        literal_ip = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        literal_ip = None
    if literal_ip is not None and not literal_ip.is_global:
        raise UnsafeUrlError("Private or reserved IP destinations are not allowed")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        records = await resolver(host, port)
    except OSError as exc:
        raise UnsafeUrlError("Hostname could not be resolved") from exc
    addresses = {record[4][0] for record in records}
    if not addresses or any(not _is_public(address) for address in addresses):
        raise UnsafeUrlError("Hostname resolves to a non-public destination")
    return url
