# Smart Article Cleanup System

## Overview

The TechPulse platform now includes an intelligent article cleanup system that automatically manages content freshness while preserving user favorites and preventing the website from becoming empty.

## How It Works

### Automated Execution
- **Trigger**: AWS CloudWatch Events schedule (currently every 1 hour)
- **Location**: Integrated into the Ingestion Orchestrator Lambda function
- **Sequence**: Cleanup runs BEFORE new content ingestion

### Smart Decision Logic

The cleanup system follows intelligent rules to ensure optimal user experience:

#### 1. Fresh Content Available (≥10 new articles today)
- **Action**: Remove articles older than 24 hours
- **Reason**: Sufficient fresh content to replace old articles
- **Preservation**: All user-liked articles remain regardless of age

#### 2. Limited Fresh Content (1-9 new articles today)
- **Action**: Conservative cleanup - remove articles older than 48 hours
- **Reason**: Some fresh content available, but extend retention period
- **Preservation**: All user-liked articles remain regardless of age

#### 3. No Fresh Content (0 new articles today)
- **Action**: Skip cleanup entirely
- **Reason**: Prevent website from becoming empty
- **Preservation**: All articles retained to maintain content availability

### Database Queries

The system performs these checks before cleanup:

```sql
-- Check fresh articles from today
SELECT COUNT(*) FROM content 
WHERE DATE(published_at) = CURRENT_DATE
AND id NOT IN (
    SELECT DISTINCT content_id 
    FROM user_content_interactions 
    WHERE is_liked = true
);

-- Check total available articles (excluding favorites)
SELECT COUNT(*) FROM content 
WHERE id NOT IN (
    SELECT DISTINCT content_id 
    FROM user_content_interactions 
    WHERE is_liked = true
);
```

## Benefits

### 1. **Always Fresh Content**
- Users see the latest articles when available
- Old articles automatically removed when fresh content exists
- Daily content refresh maintains relevance

### 2. **Favorites Preservation**
- User-liked articles never deleted regardless of age
- Personal collections remain intact
- No data loss for important saved content

### 3. **Empty Site Prevention**
- Intelligent fallback when no fresh content is available
- Maintains user experience during RSS feed downtime
- Graceful degradation of service

### 4. **Resource Optimization**
- Database storage automatically managed
- Improved query performance with smaller content tables
- Reduced hosting costs over time

## Monitoring & Logging

### CloudWatch Logs
The Lambda function logs detailed cleanup results:

```
=== Lambda Smart Cleanup Results ===
Fresh articles today: 15
Total available: 45
Action: cleanup_performed
Reason: Fresh content available (15 new articles)
Articles removed: 28
========================================
```

### Result Structure
```json
{
  "fresh_today": 15,
  "total_available": 45,
  "deleted_count": 28,
  "action_taken": "cleanup_performed",
  "reason": "Fresh content available (15 new articles)"
}
```

## Configuration

### Minimum Article Threshold
- **Current Setting**: 10 articles
- **Purpose**: Ensures sufficient content before cleanup
- **Adjustable**: Modify `MIN_ARTICLES` in Lambda function

### Cleanup Schedule
- **Current Setting**: Every 1 hour via CloudWatch Events
- **Configurable**: Update `ScheduleExpression` in `infra/ingestion.yaml`
- **Examples**:
  - `rate(1 hour)` - Every hour
  - `rate(6 hours)` - Every 6 hours
  - `cron(0 2 * * ? *)` - Daily at 2 AM UTC

### Retention Periods
- **Standard**: 24 hours when fresh content available
- **Conservative**: 48 hours when limited fresh content
- **Emergency**: Indefinite when no fresh content

## Integration with Existing System

### Lambda Functions
1. **Ingestion Orchestrator**: Runs cleanup before content ingestion
2. **Content Processor**: Continues normal RSS feed processing
3. **No Changes Required**: Existing functionality preserved

### Database Schema
- **No Changes**: Works with existing table structure
- **Relationships**: Respects user_content_interactions for favorites
- **Indexes**: Benefits from existing database indexes

### Application Code
- **Minimal Changes**: Flash messages updated for consistency
- **API Compatibility**: All existing endpoints work unchanged
- **User Experience**: Transparent to end users

## Deployment

### Automatic Deployment
The smart cleanup is deployed through your existing AWS infrastructure:

1. **Lambda Package**: Updated orchestrator function
2. **CloudFormation**: No template changes required
3. **Schedule**: Uses existing CloudWatch Events rule
4. **Permissions**: Uses existing IAM roles

### Manual Testing
For development/testing purposes, the cleanup logic can be tested locally:

```python
from src.services.content_service import cleanup_old_articles
result = cleanup_old_articles()
print(result)
```

## Troubleshooting

### Common Issues

1. **No Articles Being Cleaned**
   - Check if fresh content is being ingested
   - Verify CloudWatch Events trigger is active
   - Review Lambda function logs

2. **Too Aggressive Cleanup**
   - Increase minimum article threshold
   - Extend retention periods
   - Check fresh content detection logic

3. **Favorites Being Deleted**
   - Verify user_content_interactions table integrity
   - Check is_liked column values
   - Review SQL query logic

### Debug Information
Monitor these metrics:
- Fresh articles count per day
- Total cleanup operations
- Articles preserved vs. removed
- User favorite counts

## Future Enhancements

### Potential Improvements
1. **User Preferences**: Allow users to set personal retention periods
2. **Topic-Based Cleanup**: Different retention for different topics
3. **Engagement-Based**: Preserve articles with high user interaction
4. **Machine Learning**: Predict optimal cleanup timing

### Performance Optimizations
1. **Batch Processing**: Process cleanup in chunks for large datasets
2. **Async Operations**: Use SQS for cleanup operations
3. **Caching**: Cache cleanup decisions temporarily
4. **Indexing**: Optimize database queries for cleanup operations
