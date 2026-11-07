# EF-SL: Execution-Feedback-driven Schema Linking

Code and results for the paper "EF-SL: Execution-feedback-driven schema linking that preserves information while reducing noise in Text-to-SQL" submitted to Information Processing & Management.

## Structure

- `code/` - Experiment scripts (5-method comparison, EF-SL algorithm, significance tests)
- `results/` - Raw JSON results and analysis outputs
- `*.py` - Top-level experiment scripts

## Key Scripts

- `exp_5method_comparison.py` - Five-method controlled ablation (Spider)
- `exp_bird_5method.py` - Five-method controlled ablation (BIRD)
- `exp2_execution_feedback_sl.py` - EF-SL algorithm implementation
- `significance_test.py` - Paired McNemar test and bootstrap analysis
- `fix_eval_and_significance.py` - Evaluation fixes and significance computation

## Datasets

The experiments use Spider Dev (N=1,034) and BIRD Dev (N=1,534) benchmarks.
Due to size constraints, database files are not included in this repository.
Download Spider from https://yale-lily.github.io/spider and BIRD from https://bird-bench.github.io/.

## License

MIT License
