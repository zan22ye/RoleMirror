import argparse
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any
import platform

# Set font for Chinese support
system = platform.system()
if system == 'Windows':
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
elif system == 'Darwin': # macOS
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
else: # Linux
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

def load_report(filepath: str) -> Dict[str, Any]:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def flatten_data(report_data: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    results = report_data.get('results', [])
    
    for entry in results:
        row = {
            'id': entry.get('id'),
            'npc_name': entry.get('npc_name', 'Unknown'),
            'scenario_name': entry.get('scenario_name', 'Unknown'),
            'status': entry.get('status')
        }
        
        # Extract metrics if available
        metrics = entry.get('metrics', {})
        if metrics:
            row['avg_latency'] = metrics.get('avg_latency_seconds')
            row['avg_tokens'] = metrics.get('avg_tokens_per_turn')
            row['total_tokens'] = metrics.get('total_tokens')
            
        # Extract evaluations
        evaluations = entry.get('evaluations', {})
        if evaluations:
            total_score = 0
            count = 0
            for criteria, details in evaluations.items():
                score = details.get('score')
                if score is not None:
                    row[f'score_{criteria}'] = score
                    total_score += score
                    count += 1
            
            if count > 0:
                row['average_score'] = total_score / count
        
        rows.append(row)
        
    return pd.DataFrame(rows)

def plot_score_distributions(df: pd.DataFrame, output_dir: str):
    """Boxplot of scores for each criteria"""
    score_cols = [c for c in df.columns if c.startswith('score_')]
    if not score_cols:
        return
    
    plt.figure(figsize=(10, 6))
    
    # Rename columns for better display
    plot_df = df[score_cols].rename(columns=lambda x: x.replace('score_', ''))
    
    sns.boxplot(data=plot_df)
    plt.title('Score Distribution by Criteria')
    plt.ylabel('Score (1-5)')
    plt.xlabel('Criteria')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'score_distribution.png'))
    plt.close()

def plot_npc_performance(df: pd.DataFrame, output_dir: str):
    """Bar chart of average scores by NPC"""
    if 'average_score' not in df.columns or 'npc_name' not in df.columns:
        return
        
    plt.figure(figsize=(12, 6))
    
    # Group by NPC and calculate mean
    npc_scores = df.groupby('npc_name')['average_score'].mean().sort_values(ascending=False)
    
    sns.barplot(x=npc_scores.index, y=npc_scores.values)
    plt.title('Average Performance Score by NPC')
    plt.ylabel('Average Score')
    plt.xlabel('NPC')
    plt.xticks(rotation=45)
    plt.ylim(0, 5.5) # Scores are 1-5
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'npc_performance.png'))
    plt.close()

def plot_scenario_performance(df: pd.DataFrame, output_dir: str):
    """Bar chart of average scores by Scenario"""
    if 'average_score' not in df.columns or 'scenario_name' not in df.columns:
        return
        
    plt.figure(figsize=(12, 6))
    
    # Group by Scenario and calculate mean
    scenario_scores = df.groupby('scenario_name')['average_score'].mean().sort_values(ascending=False)
    
    sns.barplot(x=scenario_scores.index, y=scenario_scores.values, palette='viridis')
    plt.title('Average Performance Score by Scenario')
    plt.ylabel('Average Score')
    plt.xlabel('Scenario')
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 5.5)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'scenario_performance.png'))
    plt.close()

def plot_latency_vs_score(df: pd.DataFrame, output_dir: str):
    """Scatter plot of Latency vs Average Score"""
    if 'avg_latency' not in df.columns or 'average_score' not in df.columns:
        return
    
    # Filter out NaNs
    plot_df = df.dropna(subset=['avg_latency', 'average_score'])
    if plot_df.empty:
        return

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=plot_df, x='avg_latency', y='average_score', hue='npc_name', style='scenario_name', s=100)
    
    plt.title('Response Latency vs. Quality Score')
    plt.xlabel('Average Latency (seconds)')
    plt.ylabel('Average Evaluation Score')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'latency_vs_score.png'))
    plt.close()

def plot_pass_metrics(pass_metrics: Dict[str, Any], output_dir: str):
    """Generates bar charts for Pass@K and Pass^K metrics."""
    if not pass_metrics:
        return

    # Prepare data
    rows = []
    for s_id, metrics in pass_metrics.items():
        # Pass@K
        for k, val in metrics.get('pass_at_k', {}).items():
            rows.append({'Scenario': s_id, 'K': f'k={k}', 'Score': val, 'Metric': 'Pass@K'})
        # Pass^K
        for k, val in metrics.get('pass_all_k', {}).items():
            rows.append({'Scenario': s_id, 'K': f'k={k}', 'Score': val, 'Metric': 'Pass^K'})
            
    if not rows:
        return
        
    df = pd.DataFrame(rows)
    
    # 1. Plot Pass@K
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df[df['Metric'] == 'Pass@K'], x='Scenario', y='Score', hue='K', palette='Blues_d')
    plt.title('Pass@K Performance by Scenario')
    plt.ylabel('Probability')
    plt.xlabel('Scenario')
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 1.1)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'pass_at_k.png'))
    plt.close()

    # 2. Plot Pass^K
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df[df['Metric'] == 'Pass^K'], x='Scenario', y='Score', hue='K', palette='Greens_d')
    plt.title('Pass^K Performance by Scenario')
    plt.ylabel('Probability')
    plt.xlabel('Scenario')
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 1.1)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'pass_all_k.png'))
    plt.close()

def generate_markdown_report(df: pd.DataFrame, pass_metrics: Dict[str, Any], output_dir: str, report_name: str):
    """Generates a Markdown report with statistics and images."""
    md_path = os.path.join(output_dir, 'analysis_report.md')
    
    # Calculate statistics
    total_cases = len(df)
    avg_score = df['average_score'].mean() if 'average_score' in df.columns else 0
    
    npc_stats = ""
    if 'npc_name' in df.columns and 'average_score' in df.columns:
        npc_means = df.groupby('npc_name')['average_score'].mean().sort_values(ascending=False)
        best_npc = npc_means.index[0]
        worst_npc = npc_means.index[-1]
        npc_stats = f"""
- **Best Performing NPC**: {best_npc} (Avg Score: {npc_means.iloc[0]:.2f})
- **Lowest Performing NPC**: {worst_npc} (Avg Score: {npc_means.iloc[-1]:.2f})
"""

    scenario_stats = ""
    if 'scenario_name' in df.columns and 'average_score' in df.columns:
        scenario_means = df.groupby('scenario_name')['average_score'].mean().sort_values(ascending=False)
        best_scenario = scenario_means.index[0]
        worst_scenario = scenario_means.index[-1]
        scenario_stats = f"""
- **Best Performing Scenario**: {best_scenario} (Avg Score: {scenario_means.iloc[0]:.2f})
- **Lowest Performing Scenario**: {worst_scenario} (Avg Score: {scenario_means.iloc[-1]:.2f})
"""

    latency_stats = ""
    if 'avg_latency' in df.columns:
        avg_lat = df['avg_latency'].mean()
        latency_stats = f"- **Average Response Latency**: {avg_lat:.2f} seconds"

    # Token Usage Stats
    token_stats = ""
    if 'avg_tokens' in df.columns and 'total_tokens' in df.columns:
        avg_tok = df['avg_tokens'].mean()
        total_tok = df['total_tokens'].sum()
        token_stats = f"""
- **Average Tokens per Turn**: {avg_tok:.2f}
- **Total Tokens Consumed**: {total_tok:,}
"""

    # Criteria Stats
    criteria_stats = ""
    score_cols = [c for c in df.columns if c.startswith('score_')]
    if score_cols:
        criteria_stats = "### Detailed Criteria Scores\n\n| Criteria | Average Score |\n|---|---|\n"
        for col in score_cols:
            criteria_name = col.replace('score_', '')
            avg_criteria_score = df[col].mean()
            criteria_stats += f"| {criteria_name} | {avg_criteria_score:.2f} |\n"
        criteria_stats += "\n"

    # Write Markdown
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# Analysis Report: {report_name}\n\n")
        
        f.write("## 1. Summary Statistics\n")
        f.write(f"- **Total Test Cases**: {total_cases}\n")
        f.write(f"- **Overall Average Score**: {avg_score:.2f} / 5.0\n")
        f.write(npc_stats)
        f.write(scenario_stats)
        f.write(latency_stats)
        f.write(token_stats + "\n")
        
        # New Pass Metrics Section
        if pass_metrics:
            f.write("## 2. Pass Metrics (Pass@K & Pass^K)\n")
            f.write("Evaluation of generation success probability and consistency across multiple attempts.\n\n")
            f.write("### Metric Definitions\n")
            f.write("- **Pass@K**: Probability that **at least one** correct result exists in the first K generations.\n")
            f.write("- **Pass^K**: Probability that **all** K generations are correct.\n\n")
            
            f.write("### Visualization\n")
            f.write("![Pass@K](pass_at_k.png)\n\n")
            f.write("![Pass^K](pass_all_k.png)\n\n")
            
            f.write("### Detailed Metrics Table\n")
            f.write("| Scenario | Metric | k=1 | k=3 | k=5 | k=10 |\n")
            f.write("|---|---|---|---|---|---|\n")
            
            for s_id, metrics in pass_metrics.items():
                # Pass@K Row
                pk = metrics.get('pass_at_k', {})
                row_pk = f"| {s_id} | Pass@K | {pk.get('1', '-')} | {pk.get('3', '-')} | {pk.get('5', '-')} | {pk.get('10', '-')} |\n"
                f.write(row_pk)
                # Pass^K Row
                pck = metrics.get('pass_all_k', {})
                row_pck = f"| {s_id} | Pass^K | {pck.get('1', '-')} | {pck.get('3', '-')} | {pck.get('5', '-')} | {pck.get('10', '-')} |\n"
                f.write(row_pck)
            f.write("\n")

        if criteria_stats:
            f.write(criteria_stats)

        f.write("## 3. Score Distribution\n")
        f.write("The following boxplot shows the distribution of scores across different evaluation criteria.\n\n")
        f.write("![Score Distribution](score_distribution.png)\n\n")
        
        f.write("## 4. Performance Analysis\n")
        
        f.write("### 4.1 By NPC\n")
        f.write("Average performance scores broken down by NPC character.\n\n")
        f.write("![NPC Performance](npc_performance.png)\n\n")
        
        f.write("### 4.2 By Scenario\n")
        f.write("Average performance scores broken down by Test Scenario. This helps identify which scenarios are most challenging for the NPCs.\n\n")
        f.write("![Scenario Performance](scenario_performance.png)\n\n")
        
        if 'avg_latency' in df.columns and not df['avg_latency'].isna().all():
            f.write("## 5. Latency Analysis\n")
            f.write("Correlation between response time (latency) and quality score.\n\n")
            f.write("![Latency vs Score](latency_vs_score.png)\n\n")
            
    print(f"Generated Markdown report at {md_path}")

def main():
    parser = argparse.ArgumentParser(description="Analyze RoleMirror Evaluation Reports")
    parser.add_argument('input_file', help="Path to the JSON report file")
    parser.add_argument('--output', '-o', help="Directory to save plots (default: same as report filename)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: File {args.input_file} not found.")
        return

    # Determine output directory
    if args.output:
        output_dir = args.output
    else:
        # Default: Use report filename (without extension) as folder name inside 'report_analysis'
        base_name = os.path.splitext(os.path.basename(args.input_file))[0]
        output_dir = os.path.join(os.getcwd(), 'report_analysis', base_name)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Loading report from {args.input_file}...")
    data = load_report(args.input_file)
    
    print("Processing data...")
    df = flatten_data(data)
    
    if df.empty:
        print("No data found in report.")
        return
        
    print(f"Loaded {len(df)} records. Columns: {list(df.columns)}")
    
    # Save processed CSV for reference
    csv_path = os.path.join(output_dir, 'processed_data.csv')
    df.to_csv(csv_path, index=False)
    print(f"Saved processed data to {csv_path}")
    
    print("Generating visualizations...")
    
    # Set style
    sns.set_theme(style="whitegrid")
    
    # 1. Score Distribution
    try:
        plot_score_distributions(df, output_dir)
        print("Generated score_distribution.png")
    except Exception as e:
        print(f"Failed to plot score distributions: {e}")

    # 2. NPC Performance
    try:
        plot_npc_performance(df, output_dir)
        print("Generated npc_performance.png")
    except Exception as e:
        print(f"Failed to plot NPC performance: {e}")

    # 3. Scenario Performance
    try:
        plot_scenario_performance(df, output_dir)
        print("Generated scenario_performance.png")
    except Exception as e:
        print(f"Failed to plot Scenario performance: {e}")

    # 4. Latency vs Score
    try:
        plot_latency_vs_score(df, output_dir)
        print("Generated latency_vs_score.png")
    except Exception as e:
        print(f"Failed to plot Latency vs Score: {e}")

    # 5. Pass Metrics Plots
    pass_metrics = data.get('pass_metrics', {})
    try:
        plot_pass_metrics(pass_metrics, output_dir)
        print("Generated pass metrics plots")
    except Exception as e:
        print(f"Failed to plot Pass metrics: {e}")
    
    # 6. Markdown Report
    try:
        report_name = os.path.basename(args.input_file)
        generate_markdown_report(df, pass_metrics, output_dir, report_name)
    except Exception as e:
        print(f"Failed to generate Markdown report: {e}")
        
    print(f"Analysis complete! Check {output_dir} for results.")

if __name__ == "__main__":
    main()
