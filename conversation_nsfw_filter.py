from typing import List, Optional
from pydantic import BaseModel

class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]
        priority: int = 0
        blocked_words: List[str] = ["explicit", "NSFW", "inappropriate"]
        block_message: str = "[Content blocked due to NSFW]"

    def __init__(self):
        self.type = "filter"
        self.name = "NSFW Filter with Admin Configuration"
        self.valves = self.Valves()

    def contains_nsfw_content(self, message: str) -> bool:
        return any(keyword.lower() in message.lower() for keyword in self.valves.blocked_words)

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        messages = body.get("messages", [])
        for message in messages:
            if message["role"] == "user" and self.contains_nsfw_content(message["content"]):
                message["content"] = self.valves.block_message
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        messages = body.get("messages", [])
        for message in messages:
            if message["role"] == "assistant" and self.contains_nsfw_content(message["content"]):
                message["content"] = self.valves.block_message
        return body
