import argparse
import json
import os
from datetime import datetime
from src.core.log_evaluator import LogEvaluator

def main():
    parser = argparse.ArgumentParser(description="RoleMirror: External Log Evaluation Tool")
    parser.add_argument("input_file", help="Path to JSON file containing logs")
    parser.add_argument("--npcs", default="src/data/npcs.json", help="Path to NPCs definition file")
    parser.add_argument("--output", default="reports", help="Directory to save reports")
    parser.add_argument("--concurrency", type=int, default=5, help="Number of concurrent evaluations")
    
    args = parser.parse_args()

    # Validate input
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        return

    # Load logs
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
            if not isinstance(logs, list):
                print("Error: Input JSON must be a list of log objects.")
                return
    except Exception as e:
        print(f"Error parsing input file: {e}")
        return

    # Run Evaluation
    print("Initializing Log Evaluator...")
    evaluator = LogEvaluator(npcs_path=args.npcs)
    
    start_time = datetime.now()
    results = evaluator.run_batch(logs, max_workers=args.concurrency)
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    
    # Generate Report
    report_data = {
        "timestamp": start_time.isoformat(),
        "duration_seconds": duration,
        "total_logs": len(results),
        "input_file": args.input_file,
        "results": results
    }
    
    os.makedirs(args.output, exist_ok=True)
    report_filename = f"log_eval_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
    report_path = os.path.join(args.output, report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
        
    print(f"\nEvaluation Complete! Report saved to: {report_path}")

if __name__ == "__main__":
    main()
