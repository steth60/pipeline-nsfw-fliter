from typing import List, Optional
from pydantic import BaseModel
from utils.pipelines.main import get_last_user_message

class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]  # Apply filter to all pipelines
        priority: int = 0  # Priority level of the filter
        blocked_words: List[str] = ["explicit", "NSFW", "inappropriate"]  # Default NSFW keywords
        block_message: str = "[Request blocked due to NSFW content]"  # Block message to show in error

    def __init__(self):
        self.type = "filter"
        self.name = "NSFW Blocker"
        self.valves = self.Valves()

    def contains_nsfw_content(self, message: str) -> bool:
        """Check if any of the blocked keywords are present in the message."""
        return any(keyword.lower() in message.lower() for keyword in self.valves.blocked_words)

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Block the request if NSFW content is detected in the user's message."""
        messages = body.get("messages", [])
        user_message = get_last_user_message(messages)

        if user_message and self.contains_nsfw_content(user_message["content"]):
            # Block the request and raise an exception
            raise Exception(self.valves.block_message)

        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """No need to modify the outlet if we are blocking NSFW requests at the inlet stage."""
        return body
