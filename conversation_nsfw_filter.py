from typing import List, Optional
from pydantic import BaseModel
from schemas import OpenAIChatMessage
from utils.pipelines.main import get_last_user_message, get_last_assistant_message

class NSFWFilterPipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]  # Apply filter to all pipelines
        priority: int = 0  # Priority level of the filter

    def __init__(self):
        self.type = "filter"
        self.name = "NSFW Filter"
        self.valves = self.Valves()
        self.blocked_keywords = ["explicit", "inappropriate", "NSFW"]  # Add NSFW keywords here

    def contains_nsfw_content(self, message: str) -> bool:
        # Simple check if any of the blocked keywords appear in the message
        return any(keyword.lower() in message.lower() for keyword in self.blocked_keywords)

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        messages = body.get("messages", [])
        user_message = get_last_user_message(messages)

        if user_message and self.contains_nsfw_content(user_message["content"]):
            # Modify or block the user's NSFW message
            for message in reversed(messages):
                if message["role"] == "user":
                    message["content"] = "[Content blocked due to NSFW]"
                    break

        body["messages"] = messages
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        messages = body.get("messages", [])
        assistant_message = get_last_assistant_message(messages)

        if assistant_message and self.contains_nsfw_content(assistant_message["content"]):
            # Modify or block the assistant's NSFW message
            for message in reversed(messages):
                if message["role"] == "assistant":
                    message["content"] = "[Response blocked due to NSFW]"
                    break

        body["messages"] = messages
        return body
