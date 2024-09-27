import os
from typing import List, Optional
from pydantic import BaseModel
from schemas import OpenAIChatMessage


class NSFWFilterPipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]  # Apply filter to all pipelines
        priority: int = 0  # Priority level of the filter
        # Custom valves to configure the blocked words and custom messages
        blocked_words: List[str] = []
        block_message: str = "[Content blocked due to NSFW]"

    def __init__(self):
        self.type = "filter"
        self.name = "NSFW Filter with Custom Values"

        # Allow setting blocked words and custom block message via environment variables
        blocked_words_env = os.getenv("BLOCKED_WORDS", "explicit,inappropriate,NSFW").split(",")
        block_message_env = os.getenv("BLOCK_MESSAGE", "[Content blocked due to NSFW]")

        self.valves = self.Valves(
            **{
                "pipelines": os.getenv("CONVERSATION_TURN_PIPELINES", "*").split(","),
                "blocked_words": blocked_words_env,
                "block_message": block_message_env,
            }
        )

    def contains_nsfw_content(self, message: str) -> bool:
        """Check if any of the blocked keywords are present in the message."""
        return any(keyword.lower() in message.lower() for keyword in self.valves.blocked_words)

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Intercept and modify user messages before sending them to the LLM."""
        messages = body.get("messages", [])
        user_message = get_last_user_message(messages)

        if user_message and self.contains_nsfw_content(user_message["content"]):
            # Modify the user's NSFW message with a custom block message
            for message in reversed(messages):
                if message["role"] == "user":
                    message["content"] = self.valves.block_message
                    break

        body["messages"] = messages
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Intercept and modify LLM responses before sending them to the user."""
        messages = body["messages"]
        assistant_message = get_last_assistant_message(messages)

        if assistant_message and self.contains_nsfw_content(assistant_message["content"]):
            # Modify the assistant's NSFW message with a custom block message
            for message in reversed(messages):
                if message["role"] == "assistant":
                    message["content"] = self.valves.block_message
                    break

        body["messages"] = messages
        return body
