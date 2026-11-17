from __future__ import annotations

import json

import httpx

from app.schemas import AnalysisPayload, ExtractedWebsite


class LLMConfigurationError(RuntimeError):
    pass


class LLMResponseError(RuntimeError):
    pass


SYSTEM_PROMPT = """You are a careful website strategy analyst. Use only the supplied page content.
Return JSON matching the provided schema. Never invent traffic, keyword volume, market share, pricing,
customers, or factual competitor claims. Mark conclusions not explicitly stated on the website as
inferred. Return exactly five search queries and five services. Competitors must be plausible category
alternatives, each labeled inferred unless the website itself names them. Keep the analysis concise,
specific, and commercially useful."""


class GeminiLLMService:
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, api_key: str | None, model: str, timeout_seconds: float = 45) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def analyze(self, website: ExtractedWebsite) -> AnalysisPayload:
        if not self.api_key:
            raise LLMConfigurationError("GEMINI_API_KEY is not configured")
        prompt = (
            f"Analyze this extracted website.\nURL: {website.final_url}\nTitle: {website.title}\n"
            f"Meta description: {website.meta_description}\nHeadings: {website.headings}\n"
            f"Visible content:\n{website.text}"
        )
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
                "responseJsonSchema": AnalysisPayload.model_json_schema(),
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    self.endpoint.format(model=self.model),
                    params={"key": self.api_key},
                    json=body,
                )
                response.raise_for_status()
                data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return AnalysisPayload.model_validate(json.loads(text))
        except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
            raise LLMResponseError("The AI provider returned an invalid or unavailable response") from exc
