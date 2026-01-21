import json
import time
from typing import List, Dict, Any
from src.agents.npc import MockNPC
from src.agents.simulator import PlayerSimulator
from src.core.grader import Grader

class TestRunner:
    def __init__(self, scenarios_path: str, npcs_path: str = "src/data/npcs.json"):
        with open(scenarios_path, 'r', encoding='utf-8') as f:
            self.scenarios = json.load(f)
        
        with open(npcs_path, 'r', encoding='utf-8') as f:
            self.npcs = {npc['id']: npc for npc in json.load(f)}
            
        self.grader = Grader()

    def run_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        print(f"Running Scenario: {scenario['name']}...")
        
        # 1. Initialize Agents
        npc_id = scenario['npc_id']
        npc_config = self.npcs.get(npc_id)
        
        if not npc_config:
            raise ValueError(f"NPC with ID '{npc_id}' not found in NPC database.")

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
        
        # 2. Run Conversation Loop
        # Initial trigger: Simulator speaks first usually to start the test context
        last_response = "" # Empty initially
        
        for turn in range(max_turns):
            # Player turn
            player_msg = simulator.chat(last_response)
            transcript.append(f"Player: {player_msg}")
            print(f"  Player: {player_msg}")

            # NPC turn
            npc_msg = npc.chat(player_msg)
            transcript.append(f"NPC: {npc_msg}")
            print(f"  NPC: {npc_msg}")
            
            last_response = npc_msg
            
        full_transcript_str = "\n".join(transcript)

        # 3. Grading
        # We grade on two dimensions: Role Consistency and Interaction Quality
        
        print("  Evaluating...")
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

        return {
            "scenario_id": scenario['id'],
            "scenario_name": scenario['name'],
            "transcript": transcript,
            "evaluations": {
                "role_consistency": consistency_eval,
                "interaction_quality": quality_eval
            }
        }

    def run_all(self):
        results = []
        for scenario in self.scenarios:
            result = self.run_scenario(scenario)
            results.append(result)
            print("-" * 50)
        return results
