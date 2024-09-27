from typing import List, Optional, Union
from pydantic import BaseModel

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

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Block the request before it is passed to the AI if NSFW content is detected."""
        # Print the incoming body for debugging purposes
        print(f"Incoming body: {body}")

        # Extract the user message from the body
        messages = body.get("messages", [])
        if not messages:
            raise ValueError("No messages found in the body.")

        # Get the last user message
        user_message = messages[-1]
        if not isinstance(user_message, dict):
            raise ValueError(f"Expected user_message to be a dictionary but got {type(user_message)}")

        # Ensure the user message contains the 'content' key and it's a string
        content = user_message.get("content", "")
        if not isinstance(content, str):
            raise ValueError("Expected 'content' to be a string.")

        # Check for NSFW content
        if self.contains_nsfw_content(content):
            # Block the prompt and log the blocked message
            print(f"Blocked message: {content} - Stopping AI processing.")
            raise Exception(self.valves.block_message)

        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """No modification needed at the outlet as the message is blocked before reaching AI."""
        return body
