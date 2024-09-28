"""
title: NSFW Content Filter Pipeline with Exact Ollama Response
author: your-name
date: 2023-10-10
version: 1.8
license: MIT
description: A pipeline filter that detects NSFW content in user messages and blocks them by returning an exact Ollama-like response.
requirements: requests
"""
from typing import List, Optional
from pydantic import BaseModel
import os
import requests
import json
from datetime import datetime, timezone, timedelta

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

        # Model information for the response.
        model_name: str = "llama3.1"

    def __init__(self):
        self.type = "filter"
        self.name = "NSFW Content Filter with Exact Ollama Response"

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
                # Return the exact Ollama response.
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
        # Generate a response that matches the exact Ollama format.
        # If blocked is True, we return a response indicating that the message was blocked.

        # Prepare the list to hold the response lines.
        response_lines = []

        if blocked:
            # Use the blocked_message to create the response tokens.
            response_text = self.valves.blocked_message
            tokens = response_text.split()

            # Generate a timestamp for each token.
            base_time = datetime.now(timezone.utc)
            time_increment = timedelta(milliseconds=40)  # 40 milliseconds between tokens.

            for index, token in enumerate(tokens):
                created_at = (base_time + index * time_increment).isoformat()
                response_line = {
                    "model": self.valves.model_name,
                    "created_at": created_at,
                    "response": token,
                    "done": False
                }
                response_lines.append(json.dumps(response_line))

            # Add the final line indicating completion.
            final_created_at = (base_time + len(tokens) * time_increment).isoformat()
            final_line = {
                "model": self.valves.model_name,
                "created_at": final_created_at,
                "response": "",
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
            response_lines.append(json.dumps(final_line))

            # Print the spoofed response in the console.
            print("Spoofed Ollama Response:")
            for line in response_lines:
                print(line)
        else:
            # If not blocked, this function should not be called with blocked=False.
            pass

        # Join the lines to form the final response.
        final_response = "\n".join(response_lines)

        # Return the final response as if it came from Ollama.
        return {
            "ollama_response": final_response,
            "stop": True  # Indicate that processing should stop here.
        }
