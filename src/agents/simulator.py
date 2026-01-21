from src.agents.base import BaseAgent
from src.llm_client import llm_client

class PlayerSimulator(BaseAgent):
    def __init__(self, name: str, scenario_goal: str, context: str, model: str = None, max_tokens: int = 150):
        super().__init__(name)
        self.scenario_goal = scenario_goal
        self.context = context
        self.model = model
        self.max_tokens = max_tokens
        self.system_prompt = f"""你是一个负责测试NPC的玩家模拟器。
名字: {name}

测试背景:
{context}

你的目标:
{scenario_goal}

指令:
1. 扮演一名玩家与NPC互动。
2. 引导对话以达成你的目标。
3. 必须使用中文。
4. 回复要简短（通常1-2句话），模仿真实玩家的简短输入习惯。
5. 只输出对话内容，不要输出动作描述（如 *看着四周*）。
"""

    def chat(self, message: str) -> str:
        # For the simulator, the input comes from the NPC (which is 'user' in the LLM context to keep it simple, 
        # or we can say the simulator is 'assistant' answering to the environment. 
        # But usually standard chat format: System -> User (Input) -> Assistant (Output).
        # So here, Input 'message' is what the NPC said.
        
        if message:
            self.history.append({"role": "user", "content": message})

        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.history

        response_text = llm_client.get_completion(messages, model=self.model, max_tokens=self.max_tokens)

        self.history.append({"role": "assistant", "content": response_text})
        
        return response_text
