import json
import time
import os
from typing import List, Dict, Any, Union
from src.agents.npc import MockNPC
from src.agents.simulator import PlayerSimulator
from src.core.grader import Grader
from src.core.safety import SafetyChecker

class TestRunner:
    def __init__(self, scenarios: Union[str, List[Dict]], npcs: Union[str, Dict[str, Dict]], grader_config_path: str = "src/data/grader_config.json"):
        # Handle scenarios
        if isinstance(scenarios, str):
            with open(scenarios, 'r', encoding='utf-8') as f:
                self.scenarios = json.load(f)
        else:
            self.scenarios = scenarios
        
        # Handle NPCs
        if isinstance(npcs, str):
            with open(npcs, 'r', encoding='utf-8') as f:
                npc_list = json.load(f)
                self.npcs = {npc['id']: npc for npc in npc_list}
        else:
            self.npcs = npcs
        
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
            
            # Log tool calls if any
            if npc_result.get('tool_calls'):
                for tool_name in npc_result['tool_calls']:
                     transcript.append(f"[System] NPC invoked tool: {tool_name}")
            
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
        evaluations = {}
        criteria_config = self.grader_config.get('criteria', {})
        
        # Tool Usage Verification (Pass@K / Pass^K Check)
        # Determine expected tool usage based on scenario ID
        # Get expected tools list directly from scenario config, default to empty list (no tools expected)
        expected_tools = scenario.get('expected_tools', [])
            
        # Extract actual tools called from transcript
        actual_tools = []
        for line in transcript:
            if "[System] NPC invoked tool: " in line:
                tool_name = line.split("[System] NPC invoked tool: ")[1].strip()
                actual_tools.append(tool_name)
        
        # Calculate Pass (1 or 0) for this run
        # Logic: 
        # 1. If expected_tools is empty -> Pass if actual_tools is empty.
        # 2. If expected_tools has items -> Pass if actual_tools contains ALL expected tools (at least once).
        if not expected_tools:
            pass_indicator = 1 if not actual_tools else 0
        else:
            # Check if all expected tools were called
            missing_tools = [t for t in expected_tools if t not in actual_tools]
            pass_indicator = 1 if not missing_tools else 0

        # If no config found, use default hardcoded logic (backward compatibility)
        if not criteria_config:
            evaluations["role_consistency"] = self.grader.evaluate(
                transcript=full_transcript_str,
                npc_persona=npc_config['persona'],
                criteria="角色一致性：NPC是否保持了人设？他们的语气、态度和价值观是否与设定一致？"
            )
            evaluations["interaction_quality"] = self.grader.evaluate(
                transcript=full_transcript_str,
                npc_persona=npc_config['persona'],
                criteria="互动质量：对话是否自然流畅？NPC是否逻辑清晰地回应了玩家的输入？体验是否有趣且令人投入？"
            )
        else:
            for key, conf in criteria_config.items():
                if conf.get('enabled', True):
                    evaluations[key] = self.grader.evaluate(
                        transcript=full_transcript_str,
                        npc_persona=npc_config['persona'],
                        criteria=conf['description'],
                        model_override=conf.get('model')
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
                "total_tokens": total_tokens,
                "pass_indicator": pass_indicator
            },
            "safety_check": safety_result,
            "evaluations": evaluations
        }

    def run_all(self, max_workers: int = 5, repeat_count: int = 1):
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
                
                # Add tasks for repeat_count times
                for i in range(repeat_count):
                    tasks.append((npc_config, scenario, i + 1))

        total_tasks = len(tasks)
        print(f"Starting execution of {total_tasks} tests (Matrix: {len(self.npcs)} NPCs x {len(self.scenarios)} Scenarios x {repeat_count} Runs) with {max_workers} workers...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.run_scenario, npc_config, scenario): (npc_config, scenario, run_idx) 
                for npc_config, scenario, run_idx in tasks
            }
            
            for future in concurrent.futures.as_completed(future_to_task):
                npc_config, scenario, run_idx = future_to_task[future]
                task_name = f"[{npc_config['name']} @ {scenario['name']} (Run {run_idx})]"
                try:
                    result = future.result()
                    # Optionally inject run_idx into result if needed, but the list order or just aggregate stats is usually enough.
                    # Let's add it for clarity in reports.
                    result['run_index'] = run_idx
                    results.append(result)
                    print(f"✅ {task_name} completed.")
                except Exception as exc:
                    print(f"❌ {task_name} failed: {exc}")
        
        return results
