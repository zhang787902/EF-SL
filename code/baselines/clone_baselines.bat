@echo off
REM Clone Text-to-SQL baseline repositories (Windows version)
REM Run: clone_baselines.bat

echo ==========================================
echo Cloning Text-to-SQL Baseline Repositories
echo ==========================================
echo.

REM Create directory for baselines
if not exist "text2sql_baselines" mkdir text2sql_baselines
cd text2sql_baselines

REM 1. RESDSQL (AAAI 2023)
echo [1/8] Cloning RESDSQL...
if not exist "RESDSQL" (
    git clone https://github.com/RUCKBReasoning/RESDSQL.git
    echo [OK] RESDSQL cloned
) else (
    echo [OK] RESDSQL already exists, pulling latest...
    cd RESDSQL
    git pull
    cd ..
)
echo.

REM 2. Alpha-SQL (ICML 2025)
echo [2/8] Cloning Alpha-SQL...
if not exist "Alpha-SQL" (
    git clone https://github.com/HKUSTDial/Alpha-SQL.git
    echo [OK] Alpha-SQL cloned
) else (
    echo [OK] Alpha-SQL already exists, pulling latest...
    cd Alpha-SQL
    git pull
    cd ..
)
echo.

REM 3. RSL-SQL (BIRD optimized)
echo [3/8] Cloning RSL-SQL...
if not exist "RSL-SQL" (
    git clone https://github.com/Laqcce-cao/RSL-SQL.git
    echo [OK] RSL-SQL cloned
) else (
    echo [OK] RSL-SQL already exists, pulling latest...
    cd RSL-SQL
    git pull
    cd ..
)
echo.

REM 4. RAT-SQL (ACL 2020)
echo [4/8] Cloning RAT-SQL...
if not exist "rat-sql" (
    git clone https://github.com/microsoft/rat-sql.git
    echo [OK] RAT-SQL cloned
) else (
    echo [OK] RAT-SQL already exists, pulling latest...
    cd rat-sql
    git pull
    cd ..
)
echo.

REM 5. PICARD (EMNLP 2021)
echo [5/8] Cloning PICARD...
if not exist "picard" (
    git clone https://github.com/ElementAI/picard.git
    echo [OK] PICARD cloned
) else (
    echo [OK] PICARD already exists, pulling latest...
    cd picard
    git pull
    cd ..
)
echo.

REM 6. DIN-SQL
echo [6/8] Cloning DIN-SQL...
if not exist "DIN-SQL" (
    git clone https://github.com/MohammadrezaPourreza/DIN-SQL.git
    echo [OK] DIN-SQL cloned
) else (
    echo [OK] DIN-SQL already exists, pulling latest...
    cd DIN-SQL
    git pull
    cd ..
)
echo.

REM 7. Spider Dataset
echo [7/8] Cloning Spider dataset...
if not exist "spider" (
    git clone https://github.com/taoyds/spider.git
    echo [OK] Spider cloned
) else (
    echo [OK] Spider already exists, pulling latest...
    cd spider
    git pull
    cd ..
)
echo.

REM 8. Test Suite Evaluation
echo [8/8] Cloning test-suite-sql-eval...
if not exist "test-suite-sql-eval" (
    git clone https://github.com/taoyds/test-suite-sql-eval.git
    echo [OK] test-suite-sql-eval cloned
) else (
    echo [OK] test-suite-sql-eval already exists, pulling latest...
    cd test-suite-sql-eval
    git pull
    cd ..
)
echo.

echo ==========================================
echo Cloning Complete!
echo ==========================================
echo.
echo Downloaded repositories:
echo   1. RESDSQL/        - AAAI 2023, Execution Acc: 79.9%%
echo   2. Alpha-SQL/      - ICML 2025, MCTS-based
echo   3. RSL-SQL/        - BIRD optimized
echo   4. rat-sql/        - ACL 2020
echo   5. picard/         - EMNLP 2021
echo   6. DIN-SQL/        - Decomposed ICL
echo   7. spider/         - Dataset
echo   8. test-suite-sql-eval/ - Evaluation
echo.
echo Next steps:
echo   1. Check each repo's README for setup instructions
echo   2. Download Spider dataset from Yale website
echo   3. Install dependencies
echo   4. Run evaluation scripts
echo.

pause
