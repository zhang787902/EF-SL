#!/bin/bash
# Clone Text-to-SQL baseline repositories
# Run: bash clone_baselines.sh

set -e

echo "=========================================="
echo "Cloning Text-to-SQL Baseline Repositories"
echo "=========================================="
echo ""

# Create directory for baselines
mkdir -p text2sql_baselines
cd text2sql_baselines

# 1. RESDSQL (AAAI 2023)
echo "[1/8] Cloning RESDSQL..."
if [ ! -d "RESDSQL" ]; then
    git clone https://github.com/RUCKBReasoning/RESDSQL.git
    echo "✓ RESDSQL cloned"
else
    echo "✓ RESDSQL already exists, pulling latest..."
    cd RESDSQL && git pull && cd ..
fi
echo ""

# 2. Alpha-SQL (ICML 2025)
echo "[2/8] Cloning Alpha-SQL..."
if [ ! -d "Alpha-SQL" ]; then
    git clone https://github.com/HKUSTDial/Alpha-SQL.git
    echo "✓ Alpha-SQL cloned"
else
    echo "✓ Alpha-SQL already exists, pulling latest..."
    cd Alpha-SQL && git pull && cd ..
fi
echo ""

# 3. RSL-SQL (BIRD optimized)
echo "[3/8] Cloning RSL-SQL..."
if [ ! -d "RSL-SQL" ]; then
    git clone https://github.com/Laqcce-cao/RSL-SQL.git
    echo "✓ RSL-SQL cloned"
else
    echo "✓ RSL-SQL already exists, pulling latest..."
    cd RSL-SQL && git pull && cd ..
fi
echo ""

# 4. RAT-SQL (ACL 2020)
echo "[4/8] Cloning RAT-SQL..."
if [ ! -d "rat-sql" ]; then
    git clone https://github.com/microsoft/rat-sql.git
    echo "✓ RAT-SQL cloned"
else
    echo "✓ RAT-SQL already exists, pulling latest..."
    cd rat-sql && git pull && cd ..
fi
echo ""

# 5. PICARD (EMNLP 2021)
echo "[5/8] Cloning PICARD..."
if [ ! -d "picard" ]; then
    git clone https://github.com/ElementAI/picard.git
    echo "✓ PICARD cloned"
else
    echo "✓ PICARD already exists, pulling latest..."
    cd picard && git pull && cd ..
fi
echo ""

# 6. DIN-SQL (Student reproduction)
echo "[6/8] Cloning DIN-SQL reproduction..."
if [ ! -d "DIN-SQL" ]; then
    git clone https://github.com/MohammadrezaPourreza/DIN-SQL.git
    echo "✓ DIN-SQL cloned"
else
    echo "✓ DIN-SQL already exists, pulling latest..."
    cd DIN-SQL && git pull && cd ..
fi
echo ""

# 7. Spider Dataset and Evaluation
echo "[7/8] Cloning Spider dataset..."
if [ ! -d "spider" ]; then
    git clone https://github.com/taoyds/spider.git
    echo "✓ Spider cloned"
else
    echo "✓ Spider already exists, pulling latest..."
    cd spider && git pull && cd ..
fi
echo ""

# 8. Test Suite SQL Evaluation (Official evaluation)
echo "[8/8] Cloning test-suite-sql-eval..."
if [ ! -d "test-suite-sql-eval" ]; then
    git clone https://github.com/taoyds/test-suite-sql-eval.git
    echo "✓ test-suite-sql-eval cloned"
else
    echo "✓ test-suite-sql-eval already exists, pulling latest..."
    cd test-suite-sql-eval && git pull && cd ..
fi
echo ""

echo "=========================================="
echo "Cloning Complete!"
echo "=========================================="
echo ""
echo "Downloaded repositories:"
echo "  1. RESDSQL/        - AAAI 2023, Execution Acc: 79.9%"
echo "  2. Alpha-SQL/      - ICML 2025, MCTS-based"
echo "  3. RSL-SQL/        - BIRD optimized, Robust Schema Linking"
echo "  4. rat-sql/        - ACL 2020, Relation-aware encoding"
echo "  5. picard/         - EMNLP 2021, Constrained decoding"
echo "  6. DIN-SQL/        - Decomposed In-Context Learning"
echo "  7. spider/         - Dataset and baselines"
echo "  8. test-suite-sql-eval/ - Official evaluation script"
echo ""
echo "Next steps:"
echo "  1. Check each repo's README for setup instructions"
echo "  2. Download Spider dataset from Yale website"
echo "  3. Install dependencies for each baseline"
echo "  4. Run evaluation scripts"
echo ""
