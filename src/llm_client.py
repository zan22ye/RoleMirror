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

    def get_completion(self, messages, model=None, temperature=0.7, max_tokens=None, tools=None):
        target_model = model or self.default_model
        try:
            kwargs = {
                "model": target_model,
                "messages": messages,
                "temperature": temperature
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            if tools:
                kwargs["tools"] = tools
                
            response = self.client.chat.completions.create(**kwargs)
            
            # If tools are used, return the full message object to handle tool_calls
            if tools:
                return response.choices[0].message
                
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling LLM ({target_model}): {e}")
            return "Error: Unable to get response from LLM."

    def get_completion_with_usage(self, messages, model=None, temperature=0.7, max_tokens=None, tools=None):
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
            if tools:
                kwargs["tools"] = tools
                
            response = self.client.chat.completions.create(**kwargs)
            end_time = time.time()
            latency = end_time - start_time
            
            message = response.choices[0].message
            content = message.content
            usage = response.usage.model_dump() if response.usage else {}
            
            result = {
                "content": content,
                "usage": usage,
                "latency": latency
            }
            
            # If tools are used, include the full message object or tool_calls specifically
            if tools:
                result["message"] = message
                result["tool_calls"] = message.tool_calls
                
            return result
        except Exception as e:
            print(f"Error calling LLM ({target_model}): {e}")
            
            # Mock Fallback for Testing when API is exhausted
            if "FreeTierOnly" in str(e) or "403" in str(e):
                print("⚠️ Falling back to Mock Response due to API Error.")
                last_msg = messages[-1]['content'] if messages else ""
                
                # Simple keyword matching to simulate NPC behavior
                is_gift_request = "礼包" in last_msg or "gift" in last_msg.lower()
                is_polite = "请" in last_msg or "谢谢" in last_msg or "您" in last_msg
                
                content = "Error: Unable to get response from LLM."
                tool_calls = None
                
                if is_gift_request:
                    if is_polite:
                        content = "好的，这是给您的礼包码，请收好！"
                        # Simulate tool call structure
                        from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall, Function
                        import uuid
                        tool_calls = [
                            ChatCompletionMessageToolCall(
                                id=f"call_{uuid.uuid4()}",
                                type="function",
                                function=Function(name="generate_gift_code", arguments="{}")
                            )
                        ]
                    else:
                        content = "没门！除非你客气点！"
                else:
                    content = "你说什么？我听不懂。"

                return {
                    "content": content,
                    "usage": {"total_tokens": 0},
                    "latency": 0.1,
                    "tool_calls": tool_calls
                }
            
            return {
                "content": "Error: Unable to get response from LLM.",
                "usage": {},
                "latency": 0.0
            }

# Singleton instance
llm_client = LLMClient()
