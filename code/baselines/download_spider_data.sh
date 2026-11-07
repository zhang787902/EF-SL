#!/bin/bash
# Download Spider and BIRD datasets

set -e

echo "=========================================="
echo "Downloading Text-to-SQL Datasets"
echo "=========================================="
echo ""

mkdir -p datasets
cd datasets

# Download Spider
echo "[1/3] Downloading Spider dataset..."
if [ ! -d "spider" ]; then
    wget https://yale-lily.github.io/spider
    # Note: Actual download URL may vary, check official website
    echo "Please download Spider from: https://yale-lily.github.io/spider"
    echo "Extract to: datasets/spider/"
else
    echo "Spider directory already exists"
fi
echo ""

# Download BIRD
echo "[2/3] Downloading BIRD dataset..."
if [ ! -d "bird" ]; then
    echo "Please download BIRD from: https://bird-bench.github.io/"
    echo "Extract to: datasets/bird/"
else
    echo "BIRD directory already exists"
fi
echo ""

# Create sample data for quick testing
echo "[3/3] Creating sample test data..."
mkdir -p samples

echo "Sample datasets prepared!"
echo ""
echo "Directory structure:"
echo "  datasets/"
echo "    ├── spider/          # Spider dataset"
echo "    ├── bird/            # BIRD dataset"
echo "    └── samples/         # Sample test data"
echo ""
