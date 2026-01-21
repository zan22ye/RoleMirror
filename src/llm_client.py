import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.default_model = os.getenv("LLM_MODEL", "qwen-plus") # Defaulting to qwen-plus as flash might be too weak for complex instructions, but user can override
        
        if not self.api_key:
            print("Warning: DASHSCOPE_API_KEY or OPENAI_API_KEY not found.")
            
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def get_completion(self, messages, model=None, temperature=0.7, max_tokens=None):
        target_model = model or self.default_model
        try:
            kwargs = {
                "model": target_model,
                "messages": messages,
                "temperature": temperature
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
                
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling LLM ({target_model}): {e}")
            return "Error: Unable to get response from LLM."

    def get_completion_with_usage(self, messages, model=None, temperature=0.7, max_tokens=None):
        """Returns content along with usage statistics and latency."""
        import time
        start_time = time.time()
        
        target_model = model or self.default_model
        try:
            kwargs = {
                "model": target_model,
                "messages": messages,
                "temperature": temperature
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
                
            response = self.client.chat.completions.create(**kwargs)
            end_time = time.time()
            latency = end_time - start_time
            
            content = response.choices[0].message.content
            usage = response.usage.model_dump() if response.usage else {}
            
            return {
                "content": content,
                "usage": usage,
                "latency": latency
            }
        except Exception as e:
            print(f"Error calling LLM ({target_model}): {e}")
            return {
                "content": "Error: Unable to get response from LLM.",
                "usage": {},
                "latency": 0.0
            }

# Singleton instance
llm_client = LLMClient()
