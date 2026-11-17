from fastapi.testclient import TestClient

from app.main import app, get_analysis_service
from app.schemas import AnalysisPayload, LinkAnalysisResponse


SAMPLE_ANALYSIS = {
    "competitor_vs_brand": {
        "brand": {
            "name": "Acme AI",
            "overview": "Workflow automation for small teams.",
            "category": "Business automation",
            "products_or_services": ["Workflow automation"],
        },
        "competitors": [
            {"name": "Zapier", "rationale": "Workflow automation alternative", "evidence_level": "inferred"},
            {"name": "Make", "rationale": "Visual automation alternative", "evidence_level": "inferred"},
            {"name": "n8n", "rationale": "Technical automation alternative", "evidence_level": "inferred"},
        ],
        "strengths": ["Clear time-saving proposition"],
        "weaknesses_or_gaps": ["No case studies in extracted content"],
        "brand_advantages": ["Small-team focus"],
        "opportunities": ["Publish use-case pages"],
    },
    "top_search_queries": {
        "note": "Qualitative recommendations only; no search-volume claims.",
        "queries": [
            {
                "query": f"small team automation {i}",
                "platforms": ["Google", "LinkedIn"],
                "intent": "commercial investigation",
                "business_relevance": "Matches the core service",
                "target_audience": "Small operations teams",
            }
            for i in range(1, 6)
        ],
    },
    "seo_improvements": {
        "primary_keywords": ["team automation"],
        "secondary_keywords": ["workflow software"],
        "long_tail_keywords": ["workflow automation for small teams"],
        "business_keywords": ["automation platform"],
        "suggested_title": "Acme AI | Workflow Automation for Small Teams",
        "suggested_meta_description": "Automate repetitive workflows and help your small team save time with Acme AI.",
        "supporting_pages_or_content": ["Automation use cases"],
    },
    "top_services": {
        "services": [
            {
                "service_name": f"Automation service {i}",
                "description": "Automates a recurring workflow.",
                "target_industry_or_customer": "Small teams",
                "customer_benefit": "Saves time",
                "evidence_level": "inferred",
            }
            for i in range(1, 6)
        ]
    },
    "target_audience": {
        "primary_audience": ["Small operations teams"],
        "secondary_audience": ["Founders"],
        "industry_segments": ["Technology"],
        "business_types": ["SMBs"],
        "customer_profiles": ["Time-constrained operators"],
        "locations": ["Not specified on website"],
        "needs_and_challenges": ["Repetitive work"],
        "interests": ["Productivity"],
        "marketing_segments": ["Automation-aware SMBs"],
    },
}


class FakeAnalysisService:
    async def analyze(self, url: str) -> LinkAnalysisResponse:
        return LinkAnalysisResponse(
            website=url,
            brand="Acme AI",
            analysis=AnalysisPayload.model_validate(SAMPLE_ANALYSIS),
        )


def test_link_analysis_returns_structured_result() -> None:
    app.dependency_overrides[get_analysis_service] = lambda: FakeAnalysisService()
    try:
        response = TestClient(app).post("/link-analysis", json={"url": "https://example.com"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["brand"] == "Acme AI"
    assert len(body["analysis"]["top_search_queries"]["queries"]) == 5


def test_rejects_malformed_url_before_service_call() -> None:
    response = TestClient(app).post("/link-analysis", json={"url": "not-a-url"})
    assert response.status_code == 422
