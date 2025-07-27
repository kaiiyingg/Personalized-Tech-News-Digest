from datetime import datetime
from typing import Optional

class Source:
    """
    Represents an RSS source in the database.
    Maps to the 'sources' database table.
    """
    def __init__(self,
                 id: int,
                 name: str,
                 feed_url: str,
                 last_fetched_at: Optional[datetime] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        """
        Initializes a new Source object.

        Args:
            id (int): Unique identifier for the source.
            name (str): Human-readable name of the RSS source.
            feed_url (str): The URL of the RSS feed.
            last_fetched_at (Optional[datetime]): Timestamp of the last successful fetch.
            created_at (Optional[datetime]): Timestamp when the source was added.
            updated_at (Optional[datetime]): Timestamp of the last update to the source details.
        """
        self.id = id
        self.name = name
        self.feed_url = feed_url
        self.last_fetched_at = last_fetched_at
        self.created_at = created_at if created_at is not None else datetime.now()
        self.updated_at = updated_at

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name='{self.name}')>"