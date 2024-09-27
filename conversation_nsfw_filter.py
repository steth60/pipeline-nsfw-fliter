"""
title: NSFW Content Filter Pipeline
author: your-name
date: 2023-10-10
version: 1.3
license: MIT
description: A pipeline filter that detects NSFW content in user messages and blocks them.
requirements: requests
"""

from typing import List, Optional
from pydantic import BaseModel
import os
import requests

class Pipeline:
    class Valves(BaseModel):
        # List of target pipeline IDs (models) that this filter will be connected to.
        # Use ["*"] to connect to all pipelines.
        pipelines: List[str] = ["*"]

        # Assign a priority level to the filter pipeline.
        # The lower the number, the higher the priority.
        priority: int = 0

        # Valves specific to the NSFW content filter.
        target_user_roles: List[str] = ["user"]

        # Custom parameters for the NSFW filter.
        OPENAI_API_KEY: str = ""
        threshold: float = 0.5
        blocked_message: str = "Your message was blocked because it contains inappropriate content."

    def __init__(self):
        self.type = "filter"
        self.name = "NSFW Content Filter"

        # Initialize valves with default values or environment variables.
        self.valves = self.Valves(
            pipelines=os.getenv("NSFW_PIPELINES", "*").split(","),
            priority=int(os.getenv("NSFW_PRIORITY", 0)),
            target_user_roles=os.getenv("NSFW_TARGET_USER_ROLES", "user").split(","),
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
            threshold=float(os.getenv("NSFW_THRESHOLD", 0.5)),
            blocked_message=os.getenv(
                "NSFW_BLOCKED_MESSAGE",
                "Your message was blocked because it contains inappropriate content."
            ),
        )

        if not self.valves.OPENAI_API_KEY:
            raise ValueError(
                "OpenAI API key is not set. Please set the OPENAI_API_KEY in the valves configuration or as an environment variable."
            )

    async def on_startup(self):
        # This function is called when the server starts.
        print(f"{self.name} pipeline started.")

    async def on_shutdown(self):
        # This function is called when the server stops.
        print(f"{self.name} pipeline stopped.")

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        print(f"Inlet called in {self.name}.")
        # Check if the user's role is in target_user_roles.
        user_role = user.get("role", "user") if user else "user"
        if user_role in self.valves.target_user_roles:
            # Analyze the last user message.
            user_message = body["messages"][-1]["content"]
            is_safe = self.check_message_safety(user_message)

            if not is_safe:
                # Return the blocked message.
                return {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": self.valves.blocked_message
                        }
                    ],
                    "stop": True  # Indicate that processing should stop here.
                }

        # If the message is safe, allow it to proceed.
        return body

    def check_message_safety(self, message: str) -> bool:
        # Use OpenAI's Moderation API to check for NSFW content.
        headers = {
            "Authorization": f"Bearer {self.valves.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "input": message
        }
        try:
            response = requests.post(
                "https://api.openai.com/v1/moderations",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error during OpenAI Moderation API call: {e}")
            # In case of an error, consider the message unsafe to be cautious.
            return False

        # Get the highest category score.
        category_scores = result["results"][0]["category_scores"]
        highest_score = max(category_scores.values())

        print(f"Message: '{message}' | Highest Category Score: {highest_score}")

        # Check if the highest score exceeds the threshold.
        if highest_score >= self.valves.threshold:
            return False  # Message is not safe.
        return True  # Message is safe.
