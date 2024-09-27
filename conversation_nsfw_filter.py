from typing import List, Optional
from pydantic import BaseModel

class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = []
        priority: int = 0  # Higher priority for this filter to execute early

    def __init__(self):
        self.type = "filter"
        self.name = "NSFW Filter"
        self.valves = self.Valves(
            pipelines=["*"],  # Connect to all pipelines
            priority=1,
        )
        # Define a list of NSFW keywords
        self.nsfw_keywords = ["keyword1", "keyword2", "explicit-term"]  # Add your NSFW keyword list here

    async def on_startup(self):
        print(f"NSFW Filter Pipeline started.")
        pass

    async def on_shutdown(self):
        print(f"NSFW Filter Pipeline stopped.")
        pass

    def contains_nsfw(self, user_message: str) -> bool:
        # Check if any of the NSFW keywords exist in the user's message
        return any(keyword.lower() in user_message.lower() for keyword in self.nsfw_keywords)

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        print(f"NSFW Filter inlet activated.")
        user_message = body["messages"][-1]["content"]

        # If NSFW content is detected, inject an instruction message for the AI
        if self.contains_nsfw(user_message):
            # Add an instruction for the AI in the conversation history
            ai_instruction_message = {
                'role': 'system',
                'content': 'If the user message contains inappropriate content, please respond with: "Sorry, I can’t provide a response to that."'
            }
            # Insert the instruction message before the user’s message
            body["messages"].insert(0, ai_instruction_message)

        # Pass the message to the AI (with the instruction injected if NSFW is detected)
        return body
