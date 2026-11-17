from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class LinkAnalysisRequest(BaseModel):
    url: HttpUrl


class BrandOverview(BaseModel):
    name: str
    overview: str
    category: str
    products_or_services: list[str]


class Competitor(BaseModel):
    name: str
    rationale: str
    evidence_level: Literal["website", "inferred"]


class CompetitorAnalysis(BaseModel):
    brand: BrandOverview
    competitors: list[Competitor] = Field(min_length=3)
    strengths: list[str]
    weaknesses_or_gaps: list[str]
    brand_advantages: list[str]
    opportunities: list[str]


class SearchQuery(BaseModel):
    query: str
    platforms: list[Literal["Google", "Facebook", "Instagram", "LinkedIn", "X"]]
    intent: str
    business_relevance: str
    target_audience: str


class SearchQueryAnalysis(BaseModel):
    note: str = "Qualitative recommendations only; no search-volume claims."
    queries: list[SearchQuery] = Field(min_length=5, max_length=5)


class SeoAnalysis(BaseModel):
    primary_keywords: list[str]
    secondary_keywords: list[str]
    long_tail_keywords: list[str]
    business_keywords: list[str]
    suggested_title: str
    suggested_meta_description: str = Field(max_length=170)
    supporting_pages_or_content: list[str]


class Service(BaseModel):
    service_name: str
    description: str
    target_industry_or_customer: str
    customer_benefit: str
    evidence_level: Literal["website", "inferred"]


class ServicesAnalysis(BaseModel):
    services: list[Service] = Field(min_length=5, max_length=5)


class AudienceProfile(BaseModel):
    primary_audience: list[str]
    secondary_audience: list[str]
    industry_segments: list[str]
    business_types: list[str]
    customer_profiles: list[str]
    locations: list[str]
    needs_and_challenges: list[str]
    interests: list[str]
    marketing_segments: list[str]


class AnalysisPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    competitor_vs_brand: CompetitorAnalysis
    top_search_queries: SearchQueryAnalysis
    seo_improvements: SeoAnalysis
    top_services: ServicesAnalysis
    target_audience: AudienceProfile


class LinkAnalysisResponse(BaseModel):
    success: Literal[True] = True
    website: str
    brand: str
    analysis: AnalysisPayload


class ExtractedWebsite(BaseModel):
    requested_url: str
    final_url: str
    title: str
    meta_description: str
    headings: list[str]
    text: str
