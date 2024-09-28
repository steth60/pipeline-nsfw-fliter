"""
title: NSFW Content Filter Pipeline with Ollama Response Spoofing
author: your-name
date: 2023-10-10
version: 1.6
license: MIT
description: A pipeline filter that detects NSFW content in user messages and blocks them by spoofing an Ollama-like response.
requirements: requests
"""

from typing import List, Optional
from pydantic import BaseModel
import os
import requests
import json
import datetime

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

        # Model information for spoofing the response.
        model_name: str = "llama3.1"

    def __init__(self):
        self.type = "filter"
        self.name = "NSFW Content Filter with Ollama Response Spoofing"

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
            model_name=os.getenv("NSFW_MODEL_NAME", "llama3.1"),
        )

        # Removed the check for OPENAI_API_KEY in __init__ to allow module loading.

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
            # Check if OPENAI_API_KEY is set.
            if not self.valves.OPENAI_API_KEY:
                print("OpenAI API key is not set. Blocking message.")
                return self.generate_ollama_response(blocked=True)
            # Analyze the last user message.
            user_message = body["messages"][-1]["content"]
            is_safe = self.check_message_safety(user_message)

            if not is_safe:
                # Return the spoofed Ollama response.
                return self.generate_ollama_response(blocked=True)

        # If the message is safe or user's role is not in target_user_roles, allow it to proceed.
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

    def generate_ollama_response(self, blocked: bool = False) -> dict:
        # Generate a response that mimics Ollama's format.
        # If blocked is True, we return a response indicating that the message was blocked.
        from datetime import datetime, timezone

        # Generate a timestamp in ISO 8601 format with Z suffix.
        created_at = datetime.now(timezone.utc).isoformat()

        # Prepare the response data.
        response_data = []

        if blocked:
            # If the message is blocked, create a response that indicates processing but ends without content.
            # You can customize this as needed.
            # Example: Return the blocked_message as the final response.
            blocked_response = {
                "model": self.valves.model_name,
                "created_at": created_at,
                "response": self.valves.blocked_message,
                "done": True,
                "done_reason": "stop",
                "context": [],
                "total_duration": 0,
                "load_duration": 0,
                "prompt_eval_count": 0,
                "prompt_eval_duration": 0,
                "eval_count": 0,
                "eval_duration": 0
            }
            response_data.append(blocked_response)
        else:
            # If not blocked, this function should not be called with blocked=False.
            pass

        # Return the response as a list of JSON lines.
        response_lines = [json.dumps(item) for item in response_data]

        # Join the lines to form the final response.
        final_response = "\n".join(response_lines)

        # Return the final response in the expected format.
        return {
            "ollama_response": final_response,
            "stop": True  # Indicate that processing should stop here.
        }
