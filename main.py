import os
import json
import argparse
from datetime import datetime
from src.core.runner import TestRunner

def main():
    parser = argparse.ArgumentParser(description="RoleMirror: NPC Dialogue Evaluation System")
    parser.add_argument("--scenarios", type=str, default="src/data/scenarios.json", help="Path to scenarios JSON file")
    parser.add_argument("--npcs", type=str, default="src/data/npcs.json", help="Path to NPCs JSON file")
    parser.add_argument("--output", type=str, default="reports", help="Directory to save reports")
    parser.add_argument("--concurrency", type=int, default=5, help="Number of concurrent scenarios to run")
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)

    print("Initializing RoleMirror Evaluation System...")
    runner = TestRunner(args.scenarios, args.npcs)
    
    start_time = datetime.now()
    results = runner.run_all(max_workers=args.concurrency)
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    
    # Generate Report
    report_data = {
        "timestamp": start_time.isoformat(),
        "duration_seconds": duration,
        "total_scenarios": len(results),
        "results": results
    }
    
    report_filename = f"report_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
    report_path = os.path.join(args.output, report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
        
    print(f"\nEvaluation Complete! Report saved to: {report_path}")

if __name__ == "__main__":
    main()
