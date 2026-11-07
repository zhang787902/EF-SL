#!/usr/bin/env python3
"""
Prepare sample test data from Spider dataset for quick baseline testing
"""
import json
import random
import argparse
import os


def prepare_sample(input_file: str, output_file: str, num_samples: int = 100, seed: int = 42):
    """Prepare a sample subset from Spider dev set"""

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Set random seed for reproducibility
    random.seed(seed)

    # Sample uniformly across difficulty levels if available
    if num_samples >= len(data):
        sample = data
    else:
        sample = random.sample(data, num_samples)

    # Save sample
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample, f, indent=2, ensure_ascii=False)

    print(f"Created sample with {len(sample)} examples")
    print(f"Saved to: {output_file}")

    # Print statistics
    db_ids = set([item.get('db_id', 'unknown') for item in sample])
    print(f"Databases: {len(db_ids)}")
    print(f"Sample DBs: {list(db_ids)[:5]}")

    return sample


def main():
    parser = argparse.ArgumentParser(description='Prepare sample test data')
    parser.add_argument('--input', type=str, default='spider/dev.json',
                       help='Input Spider dev file')
    parser.add_argument('--output', type=str, default='sample_test.json',
                       help='Output sample file')
    parser.add_argument('--num', type=int, default=100,
                       help='Number of samples')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        print("Please download Spider dataset first:")
        print("  bash download_spider_data.sh")
        return

    prepare_sample(args.input, args.output, args.num, args.seed)


if __name__ == "__main__":
    main()
