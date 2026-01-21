from typing import Dict, Any
from pydantic import BaseModel, Field
from src.llm_client import llm_client
import json

class GradeResult(BaseModel):
    score: int = Field(..., description="Score from 1 to 5")
    reasoning: str = Field(..., description="Explanation for the score")
    evidence: str = Field(..., description="Quote from the conversation supporting the score")

class Grader:
    def __init__(self, model: str = None):
        self.model = model

    def evaluate(self, transcript: str, npc_persona: str, criteria: str) -> Dict[str, Any]:
        prompt = f"""你是一位专家级的对话质量评估员。

任务：
评估以下玩家与NPC之间的角色扮演对话。
请根据提供的【评测标准】，重点关注NPC的表现。

NPC人设：
{npc_persona}

评测标准：
{criteria}

对话记录：
{transcript}

指令：
1. 给出评分，范围从 1 (非常差) 到 5 (优秀)。
2. 提供具体的评分理由。
3. 必须引用对话记录中的具体原文作为“证据”来支持你的判断。
4. 严格按照以下 JSON 格式输出：
{{
  "score": int,
  "reasoning": "string",
  "evidence": "string"
}}
"""
        messages = [{"role": "system", "content": "你是一位严格的评估员。请只输出有效的JSON格式。"}, 
                    {"role": "user", "content": prompt}]
        
        response_text = llm_client.get_completion(messages, model=self.model)
        
        # Simple cleanup to ensure JSON parsing if LLM adds markdown blocks
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            result = json.loads(clean_text)
            return result
        except json.JSONDecodeError:
            print(f"Failed to parse grader response: {response_text}")
            return {
                "score": 0,
                "reasoning": "Failed to parse grader response",
                "evidence": ""
            }
