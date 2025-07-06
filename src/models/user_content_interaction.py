from datetime import datetime
from typing import Optional

class UserContentInteraction:
    """
    Represents a user's interaction with a specific content item.
    Maps to the 'user_content_interactions' database table.
    """
    def __init__(self,
                 user_id: int,
                 content_item_id: int,
                 is_read: bool = False,
                 is_saved: bool = False,
                 feedback_rating: int = 0, # -1 for dislike, 0 for neutral, 1 for like
                 interaction_at: Optional[datetime] = None):
        """
        Initializes a new UserContentInteraction object.

        Args:
            user_id (int): The ID of the user.
            content_item_id (int): The ID of the content item.
            is_read (bool): True if the content is marked as read by the user.
            is_saved (bool): True if the content is marked as saved by the user.
            feedback_rating (int): User's feedback (-1: dislike, 0: neutral, 1: like).
            interaction_at (Optional[datetime]): Timestamp of the last interaction.
        """
        self.user_id = user_id
        self.content_item_id = content_item_id
        self.is_read = is_read
        self.is_saved = is_saved
        self.feedback_rating = feedback_rating
        self.interaction_at = interaction_at if interaction_at is not None else datetime.now()

    def __repr__(self) -> str:
        return (f"<UserContentInteraction(user_id={self.user_id}, "
                f"content_item_id={self.content_item_id}, "
                f"read={self.is_read}, saved={self.is_saved}, "
                f"feedback={self.feedback_rating})>")