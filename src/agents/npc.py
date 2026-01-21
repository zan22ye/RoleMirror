from src.agents.base import BaseAgent
from src.llm_client import llm_client

class MockNPC(BaseAgent):
    def __init__(self, name: str, persona: str, model: str = None, max_tokens: int = 150):
        super().__init__(name)
        self.persona = persona
        self.model = model
        self.max_tokens = max_tokens
        self.system_prompt = f"""你是一个游戏中的NPC。
名字: {name}
人设: {persona}

指令:
1. 始终保持角色人设，不要出戏。
2. 不要打破第四面墙。
3. 必须使用中文回答。
4. 回复要简短有力，符合口语习惯，不要长篇大论。
"""

    def chat(self, message: str) -> str:
        # Add user message to history (conceptually, for the NPC, the input is 'user')
        self.history.append({"role": "user", "content": message})

        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.history

        response_text = llm_client.get_completion(messages, model=self.model, max_tokens=self.max_tokens)

        # Add assistant response to history
        self.history.append({"role": "assistant", "content": response_text})
        
        return response_text

    def chat_with_stats(self, message: str) -> dict:
        """
        Returns a dict containing 'content', 'usage', and 'latency'.
        """
        # Add user message to history
        self.history.append({"role": "user", "content": message})

        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.history

        result = llm_client.get_completion_with_usage(messages, model=self.model, max_tokens=self.max_tokens)
        
        response_text = result['content']

        # Add assistant response to history
        self.history.append({"role": "assistant", "content": response_text})
        
        return result
