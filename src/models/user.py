from datetime import datetime
from typing import Optional

class User:
    """
    Represents a user in the TechPulse application, mapping to the 'users' database table.
    """
    #Constructor to initialize the User object with attributes corresponding to the database columns.
    def __init__(self,
                id: int, 
                username: str, 
                email: str,
                password_hash: str ,
                totp_secret: str,
                created_at: datetime, 
                updated_at: Optional[datetime] = None):  # Use Optional as updated_at might be null initially   
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.totp_secret = totp_secret
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self) -> str:
        """Return a string representation of the User object for debugging."""
        return f"User(user_id={self.id}, name={self.username}, email={self.email})"
    