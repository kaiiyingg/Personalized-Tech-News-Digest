from datetime import datetime
from typing import Optional

class Content:
    """
    Represents a piece of content (e.g., article, post) fetched from a source.
    Maps to the 'content' database table.
    """
    def __init__(self,
                 id: int,
                 source_id: int,
                 title: str,
                 summary: str,
                 article_url: str,
                 published_at: Optional[datetime],
                 ingested_at: datetime,
                 updated_at: Optional[datetime] = None,
                 topic: Optional[str] = None):
        """
        Initializes a new Content object.
        
        Args:
            id (int): Unique identifier for the content item.
            source_id (int): ID of the source from which this content was fetched (foreign key).
            title (str): Title of the content (e.g., article title, video title).
            summary (str): A summary or short description of the content.
            article_url (str): The unique URL where the original content can be accessed.
            published_at (Optional[datetime]): The original publication timestamp of the content. Can be None.
            ingested_at (datetime): The timestamp when this content was first pulled/ingested by the system.
            updated_at (Optional[datetime]): The timestamp of the last update to this content record within the system.
        """
        self.id = id
        self.source_id = source_id
        self.title = title
        self.summary = summary
        self.article_url = article_url
        self.published_at = published_at
        self.ingested_at = ingested_at
        self.updated_at = updated_at # This will be set by DB trigger
        self.topic = topic

    def __repr__(self) -> str:
        """
        Provides a string representation of the Content object for debugging.
        """
        return f"<Content(id={self.id}, title='{self.title[:30]}...', source_id={self.source_id}, topic={self.topic})>"