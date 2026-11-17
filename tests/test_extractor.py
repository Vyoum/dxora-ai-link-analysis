import socket

import httpx
import pytest

from app.services.website_extractor import WebsiteExtractor
from app.utils.validators import UnsafeUrlError


async def public_resolver(host: str, port: int) -> list[tuple]:
    if host == "internal.example":
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", port))]
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]


@pytest.mark.asyncio
async def test_extracts_clean_visible_content() -> None:
    html = """
    <html><head><title>Acme AI</title><meta name="description" content="Useful automation"></head>
    <body><nav>Ignore nav</nav><h1>Automation for teams</h1><p>Save time every week.</p>
    <script>secret = true</script><footer>Ignore footer</footer></body></html>
    """
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, headers={"content-type": "text/html"}, text=html)
    )
    result = await WebsiteExtractor(resolver=public_resolver, transport=transport).extract("https://example.com")
    assert result.title == "Acme AI"
    assert result.meta_description == "Useful automation"
    assert "Automation for teams" in result.text
    assert "secret" not in result.text
    assert "Ignore footer" not in result.text


@pytest.mark.asyncio
async def test_validates_redirect_target_against_ssrf() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(302, headers={"location": "http://internal.example/private"})
    )
    with pytest.raises(UnsafeUrlError):
        await WebsiteExtractor(resolver=public_resolver, transport=transport).extract("https://example.com")
