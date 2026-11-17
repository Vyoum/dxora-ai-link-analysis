from app.schemas import LinkAnalysisResponse
from app.services.llm_service import GeminiLLMService
from app.services.website_extractor import WebsiteExtractor


class AnalysisService:
    def __init__(self, extractor: WebsiteExtractor, llm: GeminiLLMService) -> None:
        self.extractor = extractor
        self.llm = llm

    async def analyze(self, url: str) -> LinkAnalysisResponse:
        website = await self.extractor.extract(url)
        analysis = await self.llm.analyze(website)
        return LinkAnalysisResponse(
            website=website.final_url,
            brand=analysis.competitor_vs_brand.brand.name,
            analysis=analysis,
        )
