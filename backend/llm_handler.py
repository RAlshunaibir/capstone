import os
from groq import Groq

class LLMHandler:
    def __init__(self, api_key, chat_config):
        self.client = Groq(api_key=api_key)
        self.chat_config = chat_config

    def generate_response(self, context):
        messages = [
            {"role": "system", "content": self.chat_config["system_prompt"]},
            {"role": "user", "content": context}
        ]
        response = self.client.chat.completions.create(
            model=self.chat_config["model"],
            messages=messages,
            temperature=self.chat_config["temperature"],
            max_tokens=self.chat_config["max_tokens"]
        )
        return response.choices[0].message.content 