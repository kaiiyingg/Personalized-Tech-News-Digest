from datetime import datetime
from typing import Optional

class Source:
    """
    Represents a content source (e.g., RSS feed) added by a user.
    Maps to the 'sources' database table.
    """
    def __init__(self,
                 id: int,
                 user_id: int,
                 name: str,
                 feed_url: str,
                 type: str,
                 created_at: datetime,
                 last_fetched_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        """
        Initializes a new Source object.

        Args:
            id (int): Unique identifier for the source.
            user_id (int): ID of the user who added this source.
            name (str): Human-readable name of the source.
            feed_url (str): The URL of the feed/API endpoint for the source.
            type (str): Type of source (e.g., 'rss', 'subreddit').
            last_fetched_at (Optional[datetime]): Timestamp of the last successful fetch.
            created_at (datetime): Timestamp when the source was added.
            updated_at (Optional[datetime]): Timestamp of the last update to the source details.
        """
        self.id = id
        self.user_id = user_id
        self.name = name
        self.feed_url = feed_url
        self.type = type
        self.last_fetched_at = last_fetched_at
        self.created_at = created_at if created_at is not None else datetime.now() # Default if not provided
        self.updated_at = updated_at

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name='{self.name}', user_id={self.user_id})>"