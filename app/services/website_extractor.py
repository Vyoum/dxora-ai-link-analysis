from __future__ import annotations

from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.schemas import ExtractedWebsite
from app.utils.validators import Resolver, UnsafeUrlError, _system_resolver, validate_public_url


class WebsiteFetchError(RuntimeError):
    pass


class WebsiteExtractor:
    def __init__(
        self,
        timeout_seconds: float = 15,
        max_download_bytes: int = 2_000_000,
        max_content_chars: int = 24_000,
        resolver: Resolver = _system_resolver,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_download_bytes = max_download_bytes
        self.max_content_chars = max_content_chars
        self.resolver = resolver
        self.transport = transport

    async def extract(self, requested_url: str) -> ExtractedWebsite:
        current_url = await validate_public_url(requested_url, self.resolver)
        headers = {"User-Agent": "DxoraLinkAnalyzer/1.0 (+technical evaluation)"}
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers=headers,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                for _ in range(6):
                    response = await client.get(current_url)
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise WebsiteFetchError("Redirect response has no destination")
                        current_url = await validate_public_url(urljoin(current_url, location), self.resolver)
                        continue
                    response.raise_for_status()
                    break
                else:
                    raise WebsiteFetchError("Too many redirects")
        except UnsafeUrlError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise WebsiteFetchError(f"Website could not be fetched: {exc}") from exc

        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type:
            raise WebsiteFetchError("URL did not return HTML content")
        if len(response.content) > self.max_download_bytes:
            raise WebsiteFetchError("Website response is too large")

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        meta = soup.find("meta", attrs={"name": lambda value: value and value.lower() == "description"})
        meta_description = str(meta.get("content", "")).strip() if meta else ""
        headings = [node.get_text(" ", strip=True) for node in soup.find_all(["h1", "h2", "h3"])]
        for node in soup.find_all(["script", "style", "noscript", "svg", "form", "nav", "footer"]):
            node.decompose()
        blocks = [node.get_text(" ", strip=True) for node in soup.find_all(["h1", "h2", "h3", "p", "li"])]
        cleaned = "\n".join(dict.fromkeys(block for block in blocks if block))
        return ExtractedWebsite(
            requested_url=requested_url,
            final_url=current_url,
            title=title,
            meta_description=meta_description,
            headings=[heading for heading in headings if heading][:100],
            text=cleaned[: self.max_content_chars],
        )
