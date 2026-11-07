# SchemaGuide-SQL Ablation Study Results

Generated: 2026-06-01T10:26:48.288609

## Ablation Study Results

| Configuration | EM Accuracy | API Calls | Time (s) |
|---------------|-------------|-----------|----------|
| Baseline (Few-shot) | 85.0% | 0 | 67.0 |
| + Schema Constraint | 80.0% | 0 | 64.5 |
| + Schema + MCTS | 70.0% | 0 | 694.1 |
| + Schema + MCTS + Feedback | 70.0% | 0 | 608.5 |

## Target Results (from paper)

| Configuration | Target EM |
|---------------|-----------|
| Baseline (GPT-4 + Few-shot) | 64.8% |
| + Schema Constraint | 73.1% |
| + MCTS Search | 78.8% |
| + Execution Feedback | 86.2% |
