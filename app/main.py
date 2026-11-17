from fastapi import Depends, FastAPI, HTTPException

from app.config import get_settings
from app.schemas import LinkAnalysisRequest, LinkAnalysisResponse
from app.services.analysis_service import AnalysisService
from app.services.llm_service import GeminiLLMService, LLMConfigurationError, LLMResponseError
from app.services.website_extractor import WebsiteExtractor, WebsiteFetchError
from app.utils.validators import UnsafeUrlError

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Extracts public website content and returns a schema-validated AI business analysis.",
)


def get_analysis_service() -> AnalysisService:
    return AnalysisService(
        extractor=WebsiteExtractor(
            timeout_seconds=settings.request_timeout_seconds,
            max_download_bytes=settings.max_download_bytes,
            max_content_chars=settings.max_content_chars,
        ),
        llm=GeminiLLMService(
            api_key=settings.gemini_api_key,
            model=settings.llm_model,
        ),
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/link-analysis", response_model=LinkAnalysisResponse)
async def link_analysis(
    request: LinkAnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> LinkAnalysisResponse:
    try:
        return await service.analyze(str(request.url))
    except UnsafeUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WebsiteFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
