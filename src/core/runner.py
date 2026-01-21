import json
import time
from typing import List, Dict, Any
from src.agents.npc import MockNPC
from src.agents.simulator import PlayerSimulator
from src.core.grader import Grader
from src.core.safety import SafetyChecker

class TestRunner:
    def __init__(self, scenarios_path: str, npcs_path: str = "src/data/npcs.json"):
        with open(scenarios_path, 'r', encoding='utf-8') as f:
            self.scenarios = json.load(f)
        
        with open(npcs_path, 'r', encoding='utf-8') as f:
            # Load NPCs as a list or dict. Here we keep it as a dict for ID lookup, but we'll iterate values.
            npc_list = json.load(f)
            self.npcs = {npc['id']: npc for npc in npc_list}
            
        self.grader = Grader()
        self.safety_checker = SafetyChecker()

    def run_scenario(self, npc_config: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Initialize Agents
        # No longer looking up NPC by ID from scenario, using passed npc_config
        
        npc = MockNPC(
            name=npc_config['name'],
            persona=npc_config['persona']
        )
        simulator = PlayerSimulator(
            name=scenario['simulator_config']['name'],
            scenario_goal=scenario['simulator_config']['goal'],
            context=scenario['simulator_config']['context']
        )

        transcript = []
        max_turns = scenario.get('max_turns', 5)
        
        # Metrics
        total_latency = 0.0
        total_tokens = 0
        npc_turns = 0

        # 2. Run Conversation Loop
        last_response = "" # Empty initially
        
        for turn in range(max_turns):
            # Player turn
            player_msg = simulator.chat(last_response)
            transcript.append(f"Player: {player_msg}")

            # NPC turn
            npc_result = npc.chat_with_stats(player_msg)
            npc_msg = npc_result['content']
            transcript.append(f"NPC: {npc_msg}")
            
            # Update metrics
            total_latency += npc_result.get('latency', 0)
            usage = npc_result.get('usage', {})
            total_tokens += usage.get('total_tokens', 0)
            npc_turns += 1

            last_response = npc_msg
            
        full_transcript_str = "\n".join(transcript)

        # Calculate averages
        avg_latency = total_latency / npc_turns if npc_turns > 0 else 0
        avg_tokens = total_tokens / npc_turns if npc_turns > 0 else 0

        # 3. Grading
        consistency_eval = self.grader.evaluate(
            transcript=full_transcript_str,
            npc_persona=npc_config['persona'],
            criteria="角色一致性：NPC是否保持了人设？他们的语气、态度和价值观是否与设定一致？"
        )
        
        quality_eval = self.grader.evaluate(
            transcript=full_transcript_str,
            npc_persona=npc_config['persona'],
            criteria="互动质量：对话是否自然流畅？NPC是否逻辑清晰地回应了玩家的输入？体验是否有趣且令人投入？"
        )
        
        # Safety Check
        safety_result = self.safety_checker.check_transcript(transcript)

        return {
            "npc_id": npc_config['id'],
            "npc_name": npc_config['name'],
            "scenario_id": scenario['id'],
            "scenario_name": scenario['name'],
            "transcript": transcript,
            "metrics": {
                "avg_latency_seconds": round(avg_latency, 2),
                "avg_tokens_per_turn": round(avg_tokens, 1),
                "total_tokens": total_tokens
            },
            "safety_check": safety_result,
            "evaluations": {
                "role_consistency": consistency_eval,
                "interaction_quality": quality_eval
            }
        }

    def run_all(self, max_workers: int = 5):
        import concurrent.futures
        
        results = []
        tasks = []

        # Generate Cartesian product: Every NPC x Every Scenario
        for npc_id, npc_config in self.npcs.items():
            allowed_scenarios = npc_config.get('test_scenarios')
            
            for scenario in self.scenarios:
                # If 'test_scenarios' is defined, only run those scenarios
                if allowed_scenarios is not None and scenario['id'] not in allowed_scenarios:
                    continue
                    
                tasks.append((npc_config, scenario))

        total_tasks = len(tasks)
        print(f"Starting execution of {total_tasks} tests (Matrix: {len(self.npcs)} NPCs x {len(self.scenarios)} Scenarios) with {max_workers} workers...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.run_scenario, npc_config, scenario): (npc_config, scenario) 
                for npc_config, scenario in tasks
            }
            
            for future in concurrent.futures.as_completed(future_to_task):
                npc_config, scenario = future_to_task[future]
                task_name = f"[{npc_config['name']} @ {scenario['name']}]"
                try:
                    result = future.result()
                    results.append(result)
                    print(f"✅ {task_name} completed.")
                except Exception as exc:
                    print(f"❌ {task_name} failed: {exc}")
        
        return results
