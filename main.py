import os
import json
import argparse
from datetime import datetime
from src.core.runner import TestRunner
from src.core.metrics import calculate_pass_at_k, calculate_pass_all_k

def main():
    parser = argparse.ArgumentParser(description="RoleMirror: NPC Dialogue Evaluation System")
    parser.add_argument("--scenarios", type=str, default="src/data/scenarios.json", help="Path to scenarios JSON file")
    parser.add_argument("--npcs", type=str, default="src/data/npcs.json", help="Path to NPCs JSON file")
    parser.add_argument("--output", type=str, default="reports", help="Directory to save reports")
    parser.add_argument("--concurrency", type=int, default=5, help="Number of concurrent scenarios to run")
    parser.add_argument("--repeat", type=int, default=1, help="Number of times to repeat each scenario (default: 1)")
    parser.add_argument("--npc", type=str, help="ID of the specific NPC to test (optional)")
    parser.add_argument("--scenario", type=str, help="ID of the specific Scenario to test (optional)")
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)

    print("Initializing RoleMirror Evaluation System...")
    
    # Load Data
    with open(args.scenarios, 'r', encoding='utf-8') as f:
        scenarios = json.load(f)
    
    with open(args.npcs, 'r', encoding='utf-8') as f:
        all_npcs = json.load(f)
        npcs = {n['id']: n for n in all_npcs}

    # Filter NPC if specified
    if args.npc:
        if args.npc in npcs:
            npcs = {args.npc: npcs[args.npc]}
            print(f"Filtering tests for NPC: {args.npc}")
        else:
            print(f"Error: NPC '{args.npc}' not found. Available NPCs: {list(npcs.keys())}")
            return

    # Filter Scenario if specified
    if args.scenario:
        filtered_scenarios = [s for s in scenarios if s['id'] == args.scenario]
        if filtered_scenarios:
            scenarios = filtered_scenarios
            print(f"Filtering tests for Scenario: {args.scenario}")
        else:
            available_scenarios = [s['id'] for s in scenarios]
            print(f"Error: Scenario '{args.scenario}' not found. Available Scenarios: {available_scenarios}")
            return

    runner = TestRunner(scenarios, npcs)
    
    start_time = datetime.now()
    results = runner.run_all(max_workers=args.concurrency, repeat_count=args.repeat)
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    
    # Generate Report
    # Calculate Pass@K and Pass^K Metrics
    pass_k_metrics = {}
    
    # K values to evaluate
    k_values = [1, 3, 5, 10]
    
    # Group results by scenario
    scenario_groups = {}
    for res in results:
        s_id = res['scenario_id']
        if s_id not in scenario_groups:
            scenario_groups[s_id] = []
        scenario_groups[s_id].append(res)
        
    for s_id, group in scenario_groups.items():
        total_runs = len(group)
        passed_runs = sum(1 for r in group if r['metrics'].get('pass_indicator') == 1)
        
        pass_rate = passed_runs / total_runs if total_runs > 0 else 0
        
        metrics = {
            "total_runs": total_runs,
            "passed_runs": passed_runs,
            "pass_rate": round(pass_rate, 2),
            "pass_at_k": {},
            "pass_all_k": {}
        }
        
        for k in k_values:
            metrics["pass_at_k"][str(k)] = round(calculate_pass_at_k(total_runs, passed_runs, k), 4)
            metrics["pass_all_k"][str(k)] = round(calculate_pass_all_k(total_runs, passed_runs, k), 4)
            
        pass_k_metrics[s_id] = metrics

    report_data = {
        "timestamp": start_time.isoformat(),
        "duration_seconds": duration,
        "total_scenarios": len(results),
        "pass_metrics": pass_k_metrics,
        "results": results
    }
    
    report_filename = f"report_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
    report_path = os.path.join(args.output, report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
        
    print(f"\nEvaluation Complete! Report saved to: {report_path}")

if __name__ == "__main__":
    main()
