"""
Demo Experiment - Simulates realistic experiment results
This script generates synthetic but realistic experimental results
for demonstration purposes.
"""
import json
import random
import numpy as np
from datetime import datetime
import os

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)


def generate_mock_results():
    """Generate realistic mock experimental results"""

    # Define baseline configurations
    baselines = {
        'gpt4_zero_shot': {
            'name': 'GPT-4 Zero-shot',
            'base_em': 0.55,
            'base_ex': 0.58,
            'std': 0.05
        },
        'gpt4_few_shot': {
            'name': 'GPT-4 Few-shot',
            'base_em': 0.62,
            'base_ex': 0.65,
            'std': 0.04
        },
        'din_sql': {
            'name': 'DIN-SQL',
            'base_em': 0.78,
            'base_ex': 0.82,
            'std': 0.03
        },
        'schema_constraint': {
            'name': 'Schema Constraint Only',
            'base_em': 0.68,
            'base_ex': 0.72,
            'std': 0.04
        },
        'execution_feedback': {
            'name': 'Execution Feedback Only',
            'base_em': 0.75,
            'base_ex': 0.79,
            'std': 0.03
        }
    }

    # Generate main results
    main_results = {}
    print("=" * 70)
    print("GENERATING EXPERIMENTAL RESULTS")
    print("=" * 70)
    print("\n[1] Main Results - Baseline Comparison")
    print("-" * 70)

    for key, config in baselines.items():
        em = config['base_em'] + np.random.normal(0, config['std'])
        ex = config['base_ex'] + np.random.normal(0, config['std'])

        # Clip to [0, 1]
        em = max(0, min(1, em))
        ex = max(0, min(1, ex))

        main_results[key] = {
            'name': config['name'],
            'em_accuracy': round(em, 3),
            'ex_accuracy': round(ex, 3),
            'time': round(random.uniform(2.0, 5.0), 1)
        }

        print(f"{config['name']:30s} EM: {em*100:5.1f}%  EX: {ex*100:5.1f}%")

    # Add our method (SchemaGuide-SQL)
    main_results['schemaguide_sql'] = {
        'name': 'SchemaGuide-SQL (Ours)',
        'em_accuracy': 0.815,
        'ex_accuracy': 0.862,
        'time': 3.8
    }
    print(f"{'SchemaGuide-SQL (Ours)':30s} EM: {81.5:5.1f}%  EX: {86.2:5.1f}%")

    # Ablation study
    print("\n[2] Ablation Study")
    print("-" * 70)

    ablation_configs = [
        ('baseline', 'Baseline (GPT-4 Few-shot)', 0.648),
        ('schema_only', '+ Schema Constraint', 0.731),
        ('mcts_only', '+ MCTS Search', 0.708),
        ('feedback_only', '+ Execution Feedback', 0.755),
        ('schema_mcts', 'Schema + MCTS', 0.788),
        ('schema_feedback', 'Schema + Feedback', 0.835),
        ('mcts_feedback', 'MCTS + Feedback', 0.798),
        ('full_model', 'Full Model', 0.862)
    ]

    ablation_results = {}
    for key, name, base_ex in ablation_configs:
        ex = base_ex + np.random.normal(0, 0.015)
        ex = max(0, min(1, ex))

        ablation_results[key] = {
            'name': name,
            'ex_accuracy': round(ex, 3),
            'improvement': round((ex - 0.648) * 100, 1)
        }

        print(f"{name:40s} EX: {ex*100:5.1f}%  (+", end="")
        print(f"{(ex - 0.648)*100:4.1f}%)")

    # Error type analysis
    print("\n[3] Error Type Analysis")
    print("-" * 70)

    error_types = [
        ('Syntax Error', 0.235, 0.021, 91.1),
        ('JOIN Error', 0.312, 0.087, 72.1),
        ('Aggregation Error', 0.189, 0.053, 72.0),
        ('Column Not Found', 0.154, 0.032, 79.2),
        ('Table Not Found', 0.086, 0.014, 83.7),
        ('Runtime Error', 0.024, 0.008, 66.7)
    ]

    error_analysis = {}
    for error_name, initial, final, fix_rate in error_types:
        # Add small random variation
        initial_var = initial + np.random.normal(0, 0.01)
        final_var = final + np.random.normal(0, 0.005)
        fix_rate_var = fix_rate + np.random.normal(0, 2)

        error_analysis[error_name.lower().replace(' ', '_')] = {
            'name': error_name,
            'initial_error_rate': round(max(0, initial_var), 3),
            'final_error_rate': round(max(0, final_var), 3),
            'fix_success_rate': round(max(0, min(100, fix_rate_var)), 1)
        }

        print(f"{error_name:25s} Initial: {initial_var*100:5.1f}%  Final: {final_var*100:5.1f}%  Fix: {fix_rate_var:4.1f}%")

    # Difficulty analysis
    print("\n[4] Results by Difficulty")
    print("-" * 70)

    difficulties = ['easy', 'medium', 'hard', 'extra_hard']

    difficulty_results = {
        'gpt4_few_shot': {'easy': 0.85, 'medium': 0.72, 'hard': 0.58, 'extra_hard': 0.42},
        'din_sql': {'easy': 0.92, 'medium': 0.85, 'hard': 0.75, 'extra_hard': 0.62},
        'schemaguide_sql': {'easy': 0.942, 'medium': 0.887, 'hard': 0.793, 'extra_hard': 0.685}
    }

    for method, results in difficulty_results.items():
        print(f"\n{method}:")
        for diff in difficulties:
            acc = results[diff] + np.random.normal(0, 0.02)
            acc = max(0, min(1, acc))
            print(f"  {diff:15s}: {acc*100:5.1f}%")

    # Schema size analysis
    print("\n[5] Schema Size Impact")
    print("-" * 70)

    schema_sizes = [
        ('1-3 tables', 312, 0.821, 0.913),
        ('4-6 tables', 428, 0.685, 0.876),
        ('7-10 tables', 198, 0.543, 0.824),
        ('>10 tables', 96, 0.417, 0.750)
    ]

    schema_size_results = []
    for size_range, count, baseline, ours in schema_sizes:
        baseline_var = baseline + np.random.normal(0, 0.02)
        ours_var = ours + np.random.normal(0, 0.02)
        improvement = (ours_var - baseline_var) * 100

        schema_size_results.append({
            'size_range': size_range,
            'count': count,
            'baseline_ex': round(max(0, baseline_var), 3),
            'ours_ex': round(max(0, ours_var), 3),
            'improvement': round(improvement, 1)
        })

        print(f"{size_range:15s} (n={count:3d})  Baseline: {baseline_var*100:5.1f}%  Ours: {ours_var*100:5.1f}%  (+{improvement:4.1f}%)")

    # Iteration analysis
    print("\n[6] Iteration Count Analysis")
    print("-" * 70)

    iteration_results = [
        (1, 0.788, 1.0, 2.3),
        (2, 0.835, 1.4, 3.1),
        (3, 0.862, 1.7, 3.8),
        (5, 0.865, 1.9, 4.5),
        (10, 0.866, 2.1, 5.2)
    ]

    iteration_data = []
    for max_iter, ex, avg_iter, time_sec in iteration_results:
        ex_var = ex + np.random.normal(0, 0.01)
        iteration_data.append({
            'max_iterations': max_iter,
            'ex_accuracy': round(max(0, ex_var), 3),
            'avg_iterations': avg_iter,
            'avg_time': time_sec
        })

        print(f"Max {max_iter:2d} iterations: EX={ex_var*100:5.1f}%  Avg Iter={avg_iter:.1f}  Time={time_sec:.1f}s")

    # Compile all results
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'main_results': main_results,
        'ablation_study': ablation_results,
        'error_analysis': error_analysis,
        'difficulty_analysis': difficulty_results,
        'schema_size_analysis': schema_size_results,
        'iteration_analysis': iteration_data,
        'summary': {
            'best_ex_accuracy': 0.862,
            'improvement_over_baseline': 21.4,
            'schema_constraint_contribution': 8.3,
            'mcts_contribution': 5.7,
            'execution_feedback_contribution': 12.1
        }
    }

    return all_results


def save_results(results, output_dir='results'):
    """Save results to files"""
    os.makedirs(output_dir, exist_ok=True)

    # Save as JSON
    json_file = os.path.join(output_dir, 'experiment_results.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Results saved to: {json_file}")

    # Generate markdown report
    md_file = os.path.join(output_dir, 'experiment_report.md')
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# SchemaGuide-SQL Experimental Results\n\n")
        f.write(f"Generated: {results['timestamp']}\n\n")

        # Summary
        f.write("## Summary\n\n")
        summary = results['summary']
        f.write(f"- **Best Execution Accuracy**: {summary['best_ex_accuracy']*100:.1f}%\n")
        f.write(f"- **Improvement over Baseline**: +{summary['improvement_over_baseline']:.1f}%\n")
        f.write(f"- **Schema Constraint Contribution**: +{summary['schema_constraint_contribution']:.1f}%\n")
        f.write(f"- **MCTS Contribution**: +{summary['mcts_contribution']:.1f}%\n")
        f.write(f"- **Execution Feedback Contribution**: +{summary['execution_feedback_contribution']:.1f}%\n\n")

        # Main results table
        f.write("## Main Results\n\n")
        f.write("| Method | Exact Match | Execution Accuracy | Time (s) |\n")
        f.write("|--------|-------------|-------------------|----------|\n")

        for key, data in results['main_results'].items():
            f.write(f"| {data['name']} | {data['em_accuracy']*100:.1f}% | {data['ex_accuracy']*100:.1f}% | {data['time']:.1f} |\n")

        # Ablation study
        f.write("\n## Ablation Study\n\n")
        f.write("| Configuration | Execution Accuracy | Improvement |\n")
        f.write("|---------------|-------------------|-------------|\n")

        for key, data in results['ablation_study'].items():
            f.write(f"| {data['name']} | {data['ex_accuracy']*100:.1f}% | +{data['improvement']:.1f}% |\n")

        # Error analysis
        f.write("\n## Error Type Analysis\n\n")
        f.write("| Error Type | Initial Rate | Final Rate | Fix Success Rate |\n")
        f.write("|------------|--------------|------------|------------------|\n")

        for key, data in results['error_analysis'].items():
            f.write(f"| {data['name']} | {data['initial_error_rate']*100:.1f}% | {data['final_error_rate']*100:.1f}% | {data['fix_success_rate']:.1f}% |\n")

        # Difficulty analysis
        f.write("\n## Results by Difficulty\n\n")
        f.write("| Method | Easy | Medium | Hard | Extra Hard |\n")
        f.write("|--------|------|--------|------|------------|\n")

        for method, data in results['difficulty_analysis'].items():
            f.write(f"| {method} | {data['easy']*100:.1f}% | {data['medium']*100:.1f}% | {data['hard']*100:.1f}% | {data['extra_hard']*100:.1f}% |\n")

        # Schema size analysis
        f.write("\n## Schema Size Impact\n\n")
        f.write("| Schema Size | Count | Baseline | Ours | Improvement |\n")
        f.write("|-------------|-------|----------|------|-------------|\n")

        for data in results['schema_size_analysis']:
            f.write(f"| {data['size_range']} | {data['count']} | {data['baseline_ex']*100:.1f}% | {data['ours_ex']*100:.1f}% | +{data['improvement']:.1f}% |\n")

        # Iteration analysis
        f.write("\n## Iteration Count Analysis\n\n")
        f.write("| Max Iterations | EX Accuracy | Avg Iterations | Time (s) |\n")
        f.write("|----------------|-------------|----------------|----------|\n")

        for data in results['iteration_analysis']:
            f.write(f"| {data['max_iterations']} | {data['ex_accuracy']*100:.1f}% | {data['avg_iterations']:.1f} | {data['avg_time']:.1f} |\n")

    print(f"✓ Report saved to: {md_file}")

    return json_file, md_file


def print_summary(results):
    """Print summary of results"""
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    summary = results['summary']
    print(f"\nBest Execution Accuracy:     {summary['best_ex_accuracy']*100:.1f}%")
    print(f"Improvement over Baseline:   +{summary['improvement_over_baseline']:.1f}%")
    print(f"\nModule Contributions:")
    print(f"  Schema Constraint:         +{summary['schema_constraint_contribution']:.1f}%")
    print(f"  MCTS Search:               +{summary['mcts_contribution']:.1f}%")
    print(f"  Execution Feedback:        +{summary['execution_feedback_contribution']:.1f}%")

    print("\n" + "=" * 70)
    print("All results generated successfully!")
    print("=" * 70)


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("SCHEMAGUIDE-SQL EXPERIMENT DEMO")
    print("=" * 70)
    print("\nThis script generates realistic experimental results")
    print("based on the expected performance of the SchemaGuide-SQL framework.")
    print("\nNote: To run with real data and LLM API, use run_experiments.py")
    print("=" * 70)

    # Generate results
    results = generate_mock_results()

    # Save results
    json_file, md_file = save_results(results)

    # Print summary
    print_summary(results)

    print(f"\nNext steps:")
    print(f"1. Review the results: {md_file}")
    print(f"2. Use these as reference for your actual experiments")
    print(f"3. Run real experiments with: python run_experiments.py")


if __name__ == "__main__":
    main()
