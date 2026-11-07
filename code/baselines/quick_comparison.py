#!/usr/bin/env python3
"""
Quick comparison script for running multiple baselines on sample data
"""
import os
import sys
import json
import subprocess
import time
from pathlib import Path


BASELINES = {
    'resdsql': {
        'dir': 'RESDSQL',
        'script': 'inference.py',
        'args': ['--input_data', '{input}', '--output_file', '{output}']
    },
    'alphasql': {
        'dir': 'Alpha-SQL',
        'script': 'alpha_sql.py',
        'args': ['--input', '{input}', '--output', '{output}']
    },
    'dinsql': {
        'dir': 'DIN-SQL',
        'script': 'din_sql.py',
        'args': ['--input', '{input}', '--output', '{output}']
    }
}


def run_baseline(baseline_name: str, input_file: str, output_dir: str):
    """Run a single baseline"""
    if baseline_name not in BASELINES:
        print(f"Unknown baseline: {baseline_name}")
        return None

    config = BASELINES[baseline_name]
    baseline_dir = Path('text2sql_baselines') / config['dir']

    if not baseline_dir.exists():
        print(f"Baseline not found: {baseline_dir}")
        print(f"Please run: bash clone_baselines.sh")
        return None

    output_file = Path(output_dir) / f"{baseline_name}_predictions.sql"

    # Format arguments
    args = [arg.format(input=input_file, output=str(output_file))
            for arg in config['args']]

    cmd = ['python', config['script']] + args

    print(f"\nRunning {baseline_name}...")
    print(f"Command: {' '.join(cmd)}")

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            cwd=baseline_dir,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"✓ {baseline_name} completed in {elapsed:.1f}s")
            return {
                'baseline': baseline_name,
                'output': str(output_file),
                'time': elapsed,
                'success': True
            }
        else:
            print(f"✗ {baseline_name} failed")
            print(result.stderr)
            return {
                'baseline': baseline_name,
                'success': False,
                'error': result.stderr
            }

    except subprocess.TimeoutExpired:
        print(f"✗ {baseline_name} timed out")
        return {
            'baseline': baseline_name,
            'success': False,
            'error': 'Timeout'
        }
    except Exception as e:
        print(f"✗ {baseline_name} error: {e}")
        return {
            'baseline': baseline_name,
            'success': False,
            'error': str(e)
        }


def evaluate_predictions(gold_file: str, pred_file: str, db_dir: str = None):
    """Evaluate predictions using test-suite-sql-eval"""
    eval_script = Path('text2sql_baselines/test-suite-sql-eval/evaluation.py')

    if not eval_script.exists():
        print("Evaluation script not found")
        return None

    cmd = [
        'python', str(eval_script),
        '--gold', gold_file,
        '--pred', pred_file,
        '--etype', 'exec'
    ]

    if db_dir:
        cmd.extend(['--db', db_dir])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        # Parse output for accuracy
        output = result.stdout
        print(f"Evaluation output:\n{output}")

        return output

    except Exception as e:
        print(f"Evaluation error: {e}")
        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Quick baseline comparison')
    parser.add_argument('--input', type=str, default='sample_test.json',
                       help='Input test file')
    parser.add_argument('--baselines', nargs='+',
                       default=['resdsql', 'alphasql', 'dinsql'],
                       help='Baselines to run')
    parser.add_argument('--output-dir', type=str, default='comparison_results',
                       help='Output directory')
    parser.add_argument('--db-dir', type=str, default='spider/database',
                       help='Database directory')

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 60)
    print("Quick Baseline Comparison")
    print("=" * 60)
    print(f"Input: {args.input}")
    print(f"Baselines: {', '.join(args.baselines)}")
    print(f"Output: {args.output_dir}")
    print("=" * 60)

    # Run each baseline
    results = []
    for baseline in args.baselines:
        result = run_baseline(baseline, args.input, args.output_dir)
        if result:
            results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for r in results:
        status = "✓" if r.get('success') else "✗"
        time_str = f"{r.get('time', 0):.1f}s" if r.get('time') else "N/A"
        print(f"{status} {r['baseline']:15s} {time_str:>10s}")

    # Save results
    summary_file = Path(args.output_dir) / 'comparison_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {summary_file}")


if __name__ == "__main__":
    main()
