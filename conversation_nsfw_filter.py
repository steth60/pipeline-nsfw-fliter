from typing import List, Optional, Union
from pydantic import BaseModel
from utils.pipelines.main import get_last_user_message

class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]  # Apply filter to all pipelines
        priority: int = 0  # Priority level of the filter
        blocked_words: List[str] = ["explicit", "NSFW", "inappropriate", "porn"]  # Default NSFW keywords
        block_message: str = "[Request blocked due to detected NSFW content]"  # Message to return when blocked

    def __init__(self):
        self.type = "filter"
        self.name = "NSFW Blocker to Stop AI Processing"
        self.valves = self.Valves()

    def contains_nsfw_content(self, message: str) -> bool:
        """Check if any of the blocked keywords are present in the message."""
        return any(keyword.lower() in message.lower() for keyword in self.valves.blocked_words)

    async def inlet(self, body: Union[dict, str], user: Optional[dict] = None) -> dict:
        """Block the request before it is passed to the AI if NSFW content is detected."""
        # Debugging output to understand the structure of 'body'
        print(f"Incoming body (type: {type(body)}): {body}")

        # If body is a string, raise an error as we expect a dictionary
        if isinstance(body, str):
            raise ValueError("Body is a string. Expected a dictionary with 'messages'.")

        # Ensure 'body' is a dictionary
        if not isinstance(body, dict):
            raise ValueError(f"Expected body to be a dictionary but got {type(body)}")

        # Extract messages and check its type
        messages = body.get("messages", [])
        if not isinstance(messages, list):
            raise ValueError(f"Expected 'messages' to be a list but got {type(messages)}")

        # Get the last user message
        user_message = get_last_user_message(messages)

        if user_message and self.contains_nsfw_content(user_message["content"]):
            # Block the prompt and log the blocked message
            print(f"Blocked message: {user_message['content']} - Stopping AI processing.")
            raise Exception(self.valves.block_message)

        return body  # Only return the body if no NSFW content is detected

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """No modification needed at the outlet as the message is blocked before reaching AI."""
        return body
