# Hybrid Classification — concise reference

TechPulse blends a fast keyword filter with optional zero-shot AI classification (Hugging Face) for uncertain cases.

Core decision flow
- Hard reject (fast): 2+ reject keywords OR 3+ price mentions → reject immediately
- Hard accept (fast): 4+ tech keywords AND 0 reject keywords → accept by keywords
- Uncertain: otherwise → call Hugging Face zero-shot
  - If AI confidence >= 0.75 → accept
  - If AI confidence <= 0.30 → reject
  - If AI unavailable or times out → keyword fallback rules

Key constants (follow code in `src/services/content_service.py`)
- HF API endpoint: router.huggingface.co
- HF token: set `HF_TOKEN` in `.env` to enable AI
- High confidence threshold: 0.75
- Low confidence threshold: 0.30
- API call delay / rate limit: 0.5s between calls

Why hybrid?
- Saves API calls by resolving 70–90% of articles via keywords
- Provides better accuracy on ambiguous titles/summaries
- Logs decision metadata for transparency and debugging

Quick tests
- Keyword-only run: leave `HF_TOKEN` unset and run ingestion
- AI-enabled run: set `HF_TOKEN` then run ingestion

See `src/services/content_service.py` for implementation details and `HYBRID_CLASSIFICATION.md` in the repo for extended examples.
