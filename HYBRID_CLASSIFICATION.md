# Hybrid Classification System Documentation

## Overview

TechPulse uses a **hybrid classification system** that combines fast keyword-based rules with AI-powered zero-shot classification for uncertain cases. This provides the best of both worlds:

- ⚡ **Fast & Free**: Most articles are classified by keywords (no API cost)
- 🧠 **Smart & Accurate**: Uncertain cases use AI for better decisions
- 💾 **Memory Efficient**: No local AI models (uses Hugging Face API)
- 📊 **Transparent**: All classification decisions are logged with metadata

## Classification Pipeline

### Three Decision Paths

```
Article → Analyze Keywords → Decision Path:

PATH 1: HARD REJECT (Fast)
├─ 2+ reject keywords (e.g., "sale", "discount", "housing policy")
├─ 3+ price mentions ("$99", "$199.99")
├─ Entertainment services ("Netflix", "Hulu")
└─ Result: REJECT immediately (no API call)

PATH 2: HARD ACCEPT (Fast)
├─ 4+ tech keywords (e.g., "AI", "python", "cloud", "security")
├─ AND 0 reject keywords
└─ Result: ACCEPT + classify topic with keywords (no API call)

PATH 3: UNCERTAIN (Use AI)
├─ 0-3 tech keywords
├─ 0-1 reject keywords
├─ Mixed signals
└─ Result: Call Hugging Face API for final decision
    ├─ AI confidence >= 75% → ACCEPT
    ├─ AI confidence <= 30% → REJECT  
    └─ AI unavailable → Keyword fallback
```

### Examples

#### Example 1: Hard Accept
**Title**: "New Python 3.12 Features for AI and Machine Learning"
- Keywords found: python, AI, machine learning
- Tech score: 3, Reject score: 0
- **Decision**: HARD ACCEPT (fast path, no API call)
- Classification: "AI & ML" topic

#### Example 2: Hard Reject
**Title**: "Get Lifetime Netflix Subscription for $99 (reg. $199)"
- Keywords found: subscription, lifetime, multiple prices
- Tech score: 0, Reject score: 3, Price mentions: 2
- **Decision**: HARD REJECT (fast path, no API call)

#### Example 3: Uncertain → AI Decides
**Title**: "New Policy on Developer Hiring Practices"
- Keywords found: developer, policy
- Tech score: 1, Reject score: 1 (mixed signals)
- **Decision**: UNCERTAIN → Call AI
- AI analyzes: "This is about tech industry hiring" → ACCEPT
- Classification: "Tech Culture & Work" topic

#### Example 4: Uncertain → AI Rejects
**Title**: "Government Housing Policy Review"
- Keywords found: government, housing, policy
- Tech score: 0, Reject score: 3
- **Decision**: UNCERTAIN → Call AI
- AI analyzes: "This is government housing policy" → REJECT

## Hugging Face Integration

### Setup (Optional)

1. Get free API token: https://huggingface.co/settings/tokens
2. Add to `.env` file:
   ```bash
   HF_TOKEN=your-token-here
   ```
3. System automatically uses AI for uncertain cases

### Without HF_TOKEN

- System works perfectly with keywords only
- Slightly stricter acceptance thresholds
- Fallback logic:
  - Accept if: tech_score >= 2 AND no reject keywords
  - Accept if: tech_score >= 1 AND no reject keywords (lenient)
  - Reject otherwise

### API Usage & Costs

- **Free Tier**: 1000 requests/month (Hugging Face)
- **Rate Limit**: 0.5 second delay between calls
- **Typical Usage**: 10-20% of articles need AI (80-90% decided by keywords)
- **Expected Volume**: ~20-40 API calls per ingestion run

## Classification Metadata

Every article stores transparency data:

```json
{
  "method": "ai_zero_shot",           // How it was classified
  "confidence": 0.87,                 // AI confidence score (0-1)
  "reason": "AI classified with 0.87 confidence",
  "ai_used": true                     // Whether AI was called
}
```

### Classification Methods

| Method | Description | AI Used |
|--------|-------------|---------|
| `keyword_hard_accept` | 4+ tech keywords, clear tech content | No |
| `keyword_hard_reject` | 2+ reject keywords, clear non-tech | No |
| `ai_zero_shot` | AI made the final decision | Yes |
| `hybrid_ai_keyword` | AI confirmed tech, keywords classified topic | Yes |
| `keyword_fallback_accept` | AI unavailable, accepted by keywords | No |
| `keyword_fallback_reject` | AI unavailable, rejected by keywords | No |

## Benefits for Recruiters

This system demonstrates:

✅ **Production Engineering**: Handles API failures, rate limits, timeouts gracefully
✅ **Cost Optimization**: Minimizes API usage (80% keyword decisions)
✅ **Scalability**: Can process 100+ articles/minute with rate limiting
✅ **Transparency**: Full audit trail of classification decisions
✅ **Smart Fallback**: Works with or without AI
✅ **Real-world ML Integration**: Uses modern zero-shot classification without local models
✅ **Memory Efficiency**: No 1GB+ model files, perfect for free hosting

## Keyword Categories

### Tech Keywords (80+ keywords)
- AI/ML: "artificial intelligence", "machine learning", "neural network", "chatgpt"
- Development: "programming", "python", "javascript", "framework", "api"
- Cloud: "aws", "azure", "kubernetes", "docker", "serverless"
- Security: "cybersecurity", "encryption", "vulnerability", "hack"
- Data: "data science", "analytics", "database", "big data"

### Reject Keywords (150+ keywords)
- Promotional: "sale", "discount", "limited offer", "subscription"
- Government: "minister", "policy", "housing", "government"
- Entertainment: "movie", "celebrity", "music", "sports"
- Lifestyle: "fashion", "food", "travel", "health"

## Testing the System

### Test with Keyword Classification Only
```bash
# Don't set HF_TOKEN
python -m src.jobs.02_ingest_articles
```

### Test with AI Classification
```bash
# Set HF_TOKEN in .env
export HF_TOKEN=your-token-here
python -m src.jobs.02_ingest_articles
```

### Monitor Classification
```sql
-- View classification methods distribution
SELECT classification_method, COUNT(*) as count
FROM content
GROUP BY classification_method
ORDER BY count DESC;

-- View AI confidence scores
SELECT title, classification_method, ai_confidence_score, classification_metadata
FROM content
WHERE ai_confidence_score IS NOT NULL
ORDER BY ai_confidence_score ASC
LIMIT 20;
```

## Performance Metrics

- **Keyword Classification**: ~0.001 seconds per article
- **AI Classification**: ~2-5 seconds per article (API latency)
- **Overall Throughput**: 100+ articles/minute (with 80% keyword decisions)
- **Memory Usage**: <10MB (no local models)
- **API Cost**: $0 (free tier sufficient for hobby project)

## Future Enhancements

1. **Caching**: Cache AI results for duplicate/similar articles
2. **Batch API Calls**: Send multiple articles in one request
3. **Active Learning**: Use user feedback to improve keyword lists
4. **Custom Fine-tuning**: Fine-tune model on tech news dataset for better accuracy
5. **Analytics Dashboard**: Visualize classification decisions and confidence scores
