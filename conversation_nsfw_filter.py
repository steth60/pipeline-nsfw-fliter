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

        # If NSFW content is detected, return a fake AI response and don't send the message to the actual AI
        if self.contains_nsfw(user_message):
            # Create a fake response as if the AI generated it
            fake_response = {
                'status': 'success',  # Add a status to indicate success
                'model': body.get('model'),
                'messages': [
                    {'role': 'assistant', 'content': 'Sorry, I can’t provide a response to that.'}
                ],
                'stream': False,
                'max_tokens': body.get('max_tokens', 50),
                'chat_id': body.get('chat_id'),
                'metadata': body.get('metadata', {}),
            }
            return fake_response

        # Otherwise, pass the message through unchanged (it goes to the AI if no NSFW content)
        return body
