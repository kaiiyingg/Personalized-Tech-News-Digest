# For WSL: Go to python env (.venv) + type PYTHONPATH=./ pytest tests/ in terminal to run tests
import pytest 
from src.services.content_service import assign_topic, create_content_item, cleanup_old_articles
from datetime import datetime

def test_assign_topic_ai():
    title = "OpenAI launches new GPT-4 model"
    summary = "The latest breakthrough in artificial intelligence."
    topic = assign_topic(title, summary)
    assert isinstance(topic, str)
    assert topic == "Artificial Intelligence (AI) & Machine Learning (ML)"

def test_assign_topic_devops():
    title = "AWS Lambda now supports container images"
    summary = "Cloud computing and DevOps made easier."
    topic = assign_topic(title, summary)
    assert isinstance(topic, str)
    assert topic == "Cloud Computing & DevOps"

def test_assign_topic_other():
    title = "Random news"
    summary = "Nothing related to tech."
    topic = assign_topic(title, summary)
    assert topic in [
        "Other",
        "Big Tech & Industry Trends",
        "Tech Culture & Work"
    ]

@pytest.mark.skip(reason="Requires database connection and valid source_id")
def test_create_content_item():
    # Replace with a valid source_id from your database
    source_id = 1
    title = "Test Article"
    summary = "This is a test summary for the article."
    article_url = "https://example.com/test-article"
    published_at = datetime.now()
    content = create_content_item(source_id, title, summary, article_url, published_at)
    assert content is not None
    assert content.title == title
    assert content.article_url == article_url

@pytest.mark.skip(reason="Requires database connection and content data")
def test_cleanup_old_articles():
    result = cleanup_old_articles()
    assert isinstance(result, dict)
    assert "action_taken" in result
