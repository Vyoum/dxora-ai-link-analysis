import socket

import pytest

from app.utils.validators import UnsafeUrlError, validate_public_url


async def public_resolver(host: str, port: int) -> list[tuple]:
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]


@pytest.mark.asyncio
async def test_accepts_public_https_url() -> None:
    assert await validate_public_url("https://example.com/path", public_resolver) == "https://example.com/path"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/admin",
        "http://10.0.0.8/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "http://localhost:8000/",
        "file:///etc/passwd",
    ],
)
async def test_rejects_unsafe_destinations(url: str) -> None:
    with pytest.raises(UnsafeUrlError):
        await validate_public_url(url, public_resolver)
