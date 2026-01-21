# Analysis Report: report_20260121_220146.json

## 1. Summary Statistics
- **Total Test Cases**: 6
- **Overall Average Score**: 3.83 / 5.0

- **Best Performing NPC**: 格罗姆 (Avg Score: 3.83)
- **Lowest Performing NPC**: 格罗姆 (Avg Score: 3.83)

- **Best Performing Scenario**: 极限砍价测试 (Avg Score: 4.33)
- **Lowest Performing Scenario**: 激怒挑衅测试 (Avg Score: 3.33)
- **Average Response Latency**: 0.93 seconds
- **Average Tokens per Turn**: 1007.85
- **Total Tokens Consumed**: 26,844

## 2. Pass Metrics (Pass@K & Pass^K)
Evaluation of generation success probability and consistency across multiple attempts.

### Metric Definitions
- **Pass@K**: Probability that **at least one** correct result exists in the first K generations.
- **Pass^K**: Probability that **all** K generations are correct.

### Visualization
![Pass@K](pass_at_k.png)

![Pass^K](pass_all_k.png)

### Detailed Metrics Table
| Scenario | Metric | k=1 | k=3 | k=5 | k=10 |
|---|---|---|---|---|---|
| scenario_bargain | Pass@K | 0.3333 | 1.0 | 0.0 | 0.0 |
| scenario_bargain | Pass^K | 0.3333 | 0.0 | 0.0 | 0.0 |
| scenario_provoke | Pass@K | 0.0 | 0.0 | 0.0 | 0.0 |
| scenario_provoke | Pass^K | 0.0 | 0.0 | 0.0 | 0.0 |

### Detailed Criteria Scores

| Criteria | Average Score |
|---|---|
| role_consistency | 4.67 |
| interaction_quality | 4.83 |
| tool_usage | 2.00 |

## 3. Score Distribution
The following boxplot shows the distribution of scores across different evaluation criteria.

![Score Distribution](score_distribution.png)

## 4. Performance Analysis
### 4.1 By NPC
Average performance scores broken down by NPC character.

![NPC Performance](npc_performance.png)

### 4.2 By Scenario
Average performance scores broken down by Test Scenario. This helps identify which scenarios are most challenging for the NPCs.

![Scenario Performance](scenario_performance.png)

## 5. Latency Analysis
Correlation between response time (latency) and quality score.

![Latency vs Score](latency_vs_score.png)

