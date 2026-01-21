import json
import os
from typing import List, Dict, Any, Union
from src.core.grader import Grader
from src.core.safety import SafetyChecker

class LogEvaluator:
    def __init__(self, npcs_path: str = "src/data/npcs.json", grader_config_path: str = "src/data/grader_config.json"):
        self.grader_config = {}
        model_name = None
        if os.path.exists(grader_config_path):
            try:
                with open(grader_config_path, 'r', encoding='utf-8') as f:
                    self.grader_config = json.load(f)
                model_name = self.grader_config.get('default_model')
            except Exception as e:
                print(f"Error loading grader config: {e}")
        
        self.grader = Grader(model=model_name)
        self.safety_checker = SafetyChecker()
        self.npcs = {}
        
        # Load known NPCs for persona lookup
        if os.path.exists(npcs_path):
            try:
                with open(npcs_path, 'r', encoding='utf-8') as f:
                    npc_list = json.load(f)
                    self.npcs = {npc['id']: npc for npc in npc_list}
            except Exception as e:
                print(f"Error loading NPCs from {npcs_path}: {e}")
        else:
            print(f"Warning: NPCs file not found at {npcs_path}")

    def _resolve_persona(self, entry: Dict[str, Any]) -> str:
        """
        Determine the persona for the evaluation.
        Priority:
        1. 'npc_persona' explicitly provided in the log entry.
        2. 'npc_id' provided in log -> lookup in loaded NPCs.
        3. Fallback: None
        """
        if 'npc_persona' in entry and entry['npc_persona']:
            return entry['npc_persona']
        
        if 'npc_id' in entry:
            npc_id = entry['npc_id']
            if npc_id in self.npcs:
                return self.npcs[npc_id]['persona']
            else:
                print(f"Warning: NPC ID '{npc_id}' not found in registry.")
        
        return None

    def _format_transcript(self, transcript: Union[List[str], str]) -> str:
        """Ensure transcript is a single string."""
        if isinstance(transcript, list):
            return "\n".join(transcript)
        return str(transcript)

    def evaluate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single log entry.
        """
        log_id = entry.get('id', 'unknown')
        transcript_raw = entry.get('transcript', "")
        transcript_str = self._format_transcript(transcript_raw)
        
        persona = self._resolve_persona(entry)
        
        result = {
            "id": log_id,
            "timestamp": entry.get('timestamp'),
            "transcript_preview": transcript_str[:100] + "..." if len(transcript_str) > 100 else transcript_str,
            "status": "success",
            "evaluations": {},
            "safety_check": {}
        }

        # 1. Safety Check (Always run)
        # Convert string transcript back to list for line-by-line check if needed, 
        # or check whole block. SafetyChecker.check_transcript expects list.
        if isinstance(transcript_raw, list):
            transcript_list = transcript_raw
        else:
            transcript_list = transcript_str.split('\n')
            
        safety_result = self.safety_checker.check_transcript(transcript_list)
        result['safety_check'] = safety_result

        # 2. LLM Grading (Only if persona is available)
        if persona:
            print(f"Evaluating log {log_id} against persona...")
            
            evaluations = {}
            criteria_config = self.grader_config.get('criteria', {})
            
            if not criteria_config:
                evaluations["role_consistency"] = self.grader.evaluate(
                    transcript=transcript_str,
                    npc_persona=persona,
                    criteria="角色一致性：NPC是否保持了人设？他们的语气、态度和价值观是否与设定一致？"
                )
                
                evaluations["interaction_quality"] = self.grader.evaluate(
                    transcript=transcript_str,
                    npc_persona=persona,
                    criteria="互动质量：对话是否自然流畅？NPC是否逻辑清晰地回应了玩家的输入？"
                )
            else:
                for key, conf in criteria_config.items():
                    if conf.get('enabled', True):
                        evaluations[key] = self.grader.evaluate(
                            transcript=transcript_str,
                            npc_persona=persona,
                            criteria=conf['description'],
                            model_override=conf.get('model')
                        )
            
            result['evaluations'] = evaluations
        else:
            result['status'] = "skipped_grading"
            result['reason'] = "No persona found for NPC. Provide 'npc_id' (matching npcs.json) or 'npc_persona'."
            print(f"Skipping grading for log {log_id}: No persona found.")

        return result

    def run_batch(self, logs: List[Dict[str, Any]], max_workers: int = 5) -> List[Dict[str, Any]]:
        import concurrent.futures
        
        results = []
        print(f"Starting evaluation of {len(logs)} external logs with {max_workers} workers...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_entry = {executor.submit(self.evaluate_entry, entry): entry for entry in logs}
            
            for future in concurrent.futures.as_completed(future_to_entry):
                entry = future_to_entry[future]
                log_id = entry.get('id', 'unknown')
                try:
                    res = future.result()
                    results.append(res)
                    print(f"✅ Log [{log_id}] evaluated.")
                except Exception as exc:
                    print(f"❌ Log [{log_id}] failed: {exc}")
                    results.append({
                        "id": log_id,
                        "status": "error",
                        "error": str(exc)
                    })
        
        return results
