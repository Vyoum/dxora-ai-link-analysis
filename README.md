# AI-Powered Website Link Analysis API

A production-minded FastAPI service for the Dxora/Chivox AI Python practical test. It fetches a public website, extracts useful visible content, asks an LLM for a grounded business analysis, and validates the model response against strict Pydantic schemas before returning it.

## What it analyzes

- Brand positioning against at least three plausible competitors
- Five cross-platform search queries with intent and audience (without invented search volume)
- SEO keywords, title/meta improvements, and supporting content
- Five services with explicit `website` or `inferred` evidence labels
- Primary/secondary audiences, segments, needs, locations, and interests

## Safety and reliability

- Accepts only HTTP(S) URLs and rejects credentials in URLs
- Resolves every hostname and blocks private, loopback, link-local, reserved, and localhost destinations
- Revalidates each redirect target to reduce SSRF risk
- Limits redirects, response bytes, extracted characters, and request duration
- Accepts only HTML responses and removes scripts, forms, navigation, and footer noise
- Uses Gemini JSON Schema mode and validates the result again with Pydantic
- Keeps credentials in environment variables; `.env` is git-ignored
- Returns clear 400/422/502/503 errors for unsafe input, invalid input, upstream failures, and missing configuration

## Architecture

```text
POST /link-analysis
        |
        v
public URL validator --> HTML fetcher --> BeautifulSoup cleaner
                                             |
                                             v
                                      structured Gemini call
                                             |
                                             v
                                      Pydantic validation --> JSON response
```

The layers are independently testable: URL validation, extraction, AI provider, orchestration, and HTTP API.

## Setup

Requires Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY to .env
uvicorn app.main:app --host 0.0.0.0 --port 4000
```

Open interactive documentation at `http://localhost:4000/docs` and health status at `http://localhost:4000/health`.

## API example

```bash
curl -X POST http://localhost:4000/link-analysis \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com"}'
```

Condensed response shape:

```json
{
  "success": true,
  "website": "https://example.com/",
  "brand": "Example Domain",
  "analysis": {
    "competitor_vs_brand": {
      "brand": {
        "name": "Example Domain",
        "overview": "...",
        "category": "...",
        "products_or_services": ["..."]
      },
      "competitors": [
        {"name": "...", "rationale": "...", "evidence_level": "inferred"}
      ],
      "strengths": ["..."],
      "weaknesses_or_gaps": ["..."],
      "brand_advantages": ["..."],
      "opportunities": ["..."]
    },
    "top_search_queries": {"note": "...", "queries": ["five structured query objects"]},
    "seo_improvements": {"primary_keywords": ["..."], "suggested_title": "..."},
    "top_services": {"services": ["five structured service objects"]},
    "target_audience": {"primary_audience": ["..."], "needs_and_challenges": ["..."]}
  }
}
```

The full contract is visible in Swagger and in [`app/schemas.py`](app/schemas.py).

## Model research and recommendation

Pricing checked on 17 November 2026 from the providers' official pages. Cost estimates assume roughly 12,000 input tokens and 3,000 output tokens per analysis. They exclude free tiers, caching, batch discounts, taxes, and optional web-grounding tools.

| Provider/model | Published standard price per 1M tokens (input/output) | Context / structured output | Estimated cost per analysis | Speed expectation* | Fit |
|---|---:|---|---:|---|---|
| Google Gemini 3.1 Flash-Lite | $0.25 / $1.50 | 1M input, 64K output; JSON Schema | ~$0.0075 | Low latency | **Selected:** low cost, generous context, native schema-constrained JSON, and a free development tier |
| OpenAI GPT-5.6 Luna | $0.20 / $1.20 | 1.05M context; structured outputs | ~$0.0060 | Low latency | Strong fallback where OpenAI infrastructure is already used |
| Anthropic Claude Haiku 5.5 | from $0.10 / $0.50 for prompts up to 100K | 1M context, 128K output; tool/schema workflows | ~$0.0027 | Provider labels it fastest | Lowest estimated token cost; would require a separate adapter and provider-specific validation |
| Anthropic Claude Sonnet 5.5 | $2.00 / $10.00 | 1M context, 128K output | ~$0.0540 | Provider labels it fast | Higher-cost quality option for harder or ambiguous websites |

\*Latency descriptions are provider positioning or engineering estimates, not benchmarks from this repository. A fair production decision should replay the same real-site evaluation set against each provider and measure p50/p95 latency, schema-valid rate, groundedness, and reviewer preference.

Official sources: [Google Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing), [Gemini 3 model guide](https://ai.google.dev/gemini-api/docs/gemini-3), [OpenAI API pricing](https://platform.openai.com/pricing/), [Anthropic model overview](https://platform.claude.com/docs/en/models/overview), and [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing).

### Why Gemini is the default

For this workload, extraction already supplies the evidence and the model mainly performs classification, summarization, and structured recommendation. Gemini 3.1 Flash-Lite gives sufficient context, low estimated cost, native JSON Schema output, and simple HTTP integration. Accuracy is not claimed from provider marketing: the Pydantic validation and evidence labels reduce failure impact, while a dedicated evaluation set is still required before production use.

Fallback strategy:

1. Retry one transient 429/5xx failure with jitter at the deployment layer.
2. Fall back to GPT-5.6 Luna through a future provider adapter if Gemini remains unavailable.
3. Never return unvalidated model text; fail clearly with 502 instead.
4. Cache by normalized URL plus content hash where freshness requirements allow it.

## Tests

```bash
pytest -q
```

The suite covers public URL acceptance, localhost/private/cloud-metadata blocking, redirect SSRF protection, visible-content cleaning, response schema validation, successful endpoint behavior, and malformed request rejection.

See [`docs/test-output.txt`](docs/test-output.txt) for the recorded local run.

## Limitations and next steps

- The current extractor analyzes the requested HTML page, not JavaScript-rendered DOM or a whole-site crawl.
- DNS is validated before HTTP connection, but a production deployment should also enforce egress controls to defend against DNS rebinding at the network layer.
- Competitor and service recommendations can be informed inferences, not independently verified market research; the API labels that distinction.
- Token counts and latency should be captured from live provider responses in production telemetry.
- A provider interface plus circuit breaker could make the documented fallback automatic.

## Project structure

```text
app/
  main.py                 # FastAPI routes and error mapping
  config.py               # Environment-backed settings
  schemas.py              # Request, response, and LLM schemas
  services/
    analysis_service.py   # Workflow orchestration
    website_extractor.py  # Safe fetch and clean extraction
    llm_service.py        # Gemini structured-output integration
  utils/validators.py     # URL and SSRF validation
tests/                    # API, extraction, and security tests
docs/test-output.txt      # Verification log
```
