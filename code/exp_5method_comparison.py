"""
5-Method Comparison Experiment on Spider Dev (N=1034)
Methods:
1. Baseline (no Schema Linking)
2. Lexical Schema Linking (keyword matching)
3. LLM-based Schema Linking (GPT-4o selects tables)
4. Execution-feedback SL (upgraded - precise schema refinement)
5. Oracle SL (using gold SQL tables - upper bound)
"""

import json
import sqlite3
import re
import os
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from openai import OpenAI
from datetime import datetime


def classify_difficulty(sql_str: str) -> str:
    sql = sql_str.lower()
    score = 0
    score += len(re.findall(r'\bjoin\b', sql)) * 2
    score += (sql.count('(select') + sql.count('( select')) * 3
    if 'group by' in sql: score += 1
    if 'having' in sql: score += 2
    if any(w in sql for w in ['except', 'intersect', 'union']): score += 3
    if 'order by' in sql and 'limit' in sql: score += 1
    if re.search(r'select.*\(select.*(?:count|avg|max|min|sum)', sql): score += 2
    if score == 0: return 'easy'
    elif score <= 2: return 'medium'
    elif score <= 5: return 'hard'
    else: return 'extra_hard'


class FiveMethodExperiment:
    def __init__(self, api_key: str, base_url: str, db_path: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.db_path = db_path

    # ========== Shared Utilities ==========

    def get_full_schema(self, db_id: str) -> str:
        try:
            conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
            cursor = conn.cursor()
            schema = []
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            for table in tables:
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    cols = [(c[1], c[2]) for c in cursor.fetchall()]
                    if cols:
                        col_defs = ", ".join(f"{n} {t}" for n, t in cols)
                        schema.append(f"CREATE TABLE {table} ({col_defs})")
                except: continue
            for table in tables:
                try:
                    cursor.execute(f"PRAGMA foreign_key_list({table})")
                    for fk in cursor.fetchall():
                        schema.append(f"FOREIGN KEY: {table}.{fk[3]} -> {fk[2]}.{fk[4]}")
                except: continue
            conn.close()
            return "\n".join(schema)
        except: return ""

    def get_filtered_schema(self, db_id: str, tables: List[str]) -> str:
        try:
            conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
            cursor = conn.cursor()
            schema = []
            for table in tables:
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    cols = [(c[1], c[2]) for c in cursor.fetchall()]
                    if cols:
                        col_defs = ", ".join(f"{n} {t}" for n, t in cols)
                        schema.append(f"CREATE TABLE {table} ({col_defs})")
                except: continue
            for table in tables:
                try:
                    cursor.execute(f"PRAGMA foreign_key_list({table})")
                    for fk in cursor.fetchall():
                        schema.append(f"FOREIGN KEY: {table}.{fk[3]} -> {fk[2]}.{fk[4]}")
                except: continue
            conn.close()
            return "\n".join(schema)
        except: return ""

    def get_all_tables(self, db_id: str) -> List[str]:
        try:
            conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tables
        except: return []

    def find_tables_with_column(self, column: str, db_id: str) -> List[str]:
        try:
            conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
            cursor = conn.cursor()
            result = []
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            for (table,) in cursor.fetchall():
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    if column in [row[1] for row in cursor.fetchall()]:
                        result.append(table)
                except: continue
            conn.close()
            return result
        except: return []

    def execute_sql(self, sql: str, db_id: str) -> Tuple[bool, Optional[List], Optional[str]]:
        try:
            conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            conn.close()
            return True, result, None
        except sqlite3.Error as e:
            return False, None, str(e)

    def evaluate_sql(self, pred_sql: str, gold_sql: str, db_id: str) -> bool:
        try:
            conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
            cursor = conn.cursor()
            cursor.execute(pred_sql)
            pred = cursor.fetchall()
            cursor.execute(gold_sql)
            gold = cursor.fetchall()
            conn.close()
            return sorted(pred) == sorted(gold)
        except: return False

    def generate_sql(self, question: str, schema: str, feedback_history: str = "") -> str:
        history_part = ""
        if feedback_history:
            history_part = f"\n\nPrevious attempts and errors:\n{feedback_history}"

        prompt = f"""Generate a single SQL query for this question based on the database schema.

Database Schema:
{schema}

Question: {question}
{history_part}
Output only the SQL query, no explanation:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Generate only the SQL query."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=500
            )
            sql = response.choices[0].message.content.strip()
            if "```sql" in sql:
                sql = sql.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql:
                sql = sql.split("```")[1].split("```")[0].strip()
            return sql
        except: return "SELECT 1"

    # ========== Method 1: Baseline (no SL) ==========

    def solve_baseline(self, question: str, db_id: str) -> str:
        schema = self.get_full_schema(db_id)
        return self.generate_sql(question, schema)

    # ========== Method 2: Lexical Schema Linking ==========

    def solve_lexical_sl(self, question: str, db_id: str) -> Tuple[str, List[str]]:
        schema = self.get_full_schema(db_id)
        all_tables = self.get_all_tables(db_id)
        question_lower = question.lower()

        linked = []
        for table in all_tables:
            # Table name match
            if table.lower() in question_lower:
                linked.append(table)
                continue
            # Column name match
            try:
                conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table})")
                for col in cursor.fetchall():
                    if col[1].lower() in question_lower:
                        linked.append(table)
                        break
                conn.close()
            except: continue

        if linked:
            filtered_schema = self.get_filtered_schema(db_id, linked)
        else:
            filtered_schema = schema

        sql = self.generate_sql(question, filtered_schema)
        return sql, linked

    # ========== Method 3: LLM-based Schema Linking ==========

    def solve_llm_sl(self, question: str, db_id: str) -> Tuple[str, List[str]]:
        all_tables = self.get_all_tables(db_id)

        # Step 1: Ask LLM to select relevant tables
        select_prompt = f"""Given a database with these tables: {', '.join(all_tables)}

And this question: "{question}"

Which tables are needed to answer this question? List only the table names, separated by commas.
Tables:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You select relevant database tables for SQL queries."},
                    {"role": "user", "content": select_prompt}
                ],
                temperature=0.0,
                max_tokens=200
            )
            selected_str = response.choices[0].message.content.strip()

            # Parse selected tables
            linked = []
            for table in all_tables:
                if table.lower() in selected_str.lower():
                    linked.append(table)

            if not linked:
                linked = all_tables  # fallback to all tables

        except:
            linked = all_tables

        # Step 2: Generate SQL with selected tables
        schema = self.get_filtered_schema(db_id, linked)
        sql = self.generate_sql(question, schema)
        return sql, linked

    # ========== Method 4: Upgraded Execution-feedback SL ==========

    def solve_upgraded_ef_sl(self, question: str, db_id: str, max_iter: int = 3) -> Tuple[str, int, List[str]]:
        """
        Upgraded EF-SL with precise schema refinement:
        - Iteration 1: Full schema -> generate SQL -> execute
        - If error: classify error type -> precisely add missing schema -> retry
        - If empty result: refine conditions -> retry
        - Track refined tables across iterations
        """
        refined_tables = []
        feedback_history = ""

        for iteration in range(1, max_iter + 1):
            # Build schema: use refined tables if available, else full
            if refined_tables:
                schema = self.get_filtered_schema(db_id, refined_tables)
            else:
                schema = self.get_full_schema(db_id)

            # Generate SQL with feedback
            sql = self.generate_sql(question, schema, feedback_history)

            # Execute
            success, result, error = self.execute_sql(sql, db_id)

            if success:
                if result and len(result) > 0:
                    return sql, iteration, refined_tables
                else:
                    # Empty result - might need to relax conditions
                    feedback_history += f"\nIter {iteration}: SQL returned 0 rows. The WHERE conditions may be too strict. Try relaxing conditions.\nSQL: {sql}\n"
                    # On empty result, try with full schema next iteration
                    if iteration == 1:
                        continue
                    else:
                        return sql, iteration, refined_tables
            else:
                # Error - classify and fix
                error_lower = error.lower()
                feedback_history += f"\nIter {iteration}: Error: {error}\nSQL: {sql}\n"

                if "no such table" in error_lower:
                    # Extract missing table name
                    match = re.search(r"no such table: (\w+)", error, re.I)
                    if match:
                        missing = match.group(1)
                        if missing not in refined_tables:
                            refined_tables.append(missing)

                elif "no such column" in error_lower:
                    # Find tables containing this column
                    match = re.search(r"no such column: (\w+)", error, re.I)
                    if match:
                        missing_col = match.group(1)
                        tables_with_col = self.find_tables_with_column(missing_col, db_id)
                        for t in tables_with_col:
                            if t not in refined_tables:
                                refined_tables.append(t)

                elif "ambiguous" in error_lower:
                    # Need to add table prefixes - include all tables
                    pass  # LLM should handle this with feedback

                # If refined_tables is empty, we need all tables for context
                if not refined_tables:
                    # Add tables referenced in the SQL
                    sql_tables = re.findall(r'FROM\s+(\w+)|JOIN\s+(\w+)', sql, re.I)
                    for t_pair in sql_tables:
                        t = t_pair[0] or t_pair[1]
                        if t and t not in refined_tables:
                            refined_tables.append(t)

        return sql, max_iter, refined_tables

    # ========== Method 5: Oracle Schema Linking ==========

    def solve_oracle_sl(self, question: str, db_id: str, gold_sql: str) -> Tuple[str, List[str]]:
        """
        Oracle SL: extract tables from gold SQL, then generate with only those tables.
        This represents the upper bound of what SL can achieve.
        """
        # Extract tables from gold SQL
        gold_tables = []
        matches = re.findall(r'FROM\s+(\w+)|JOIN\s+(\w+)', gold_sql, re.I)
        for m in matches:
            t = m[0] or m[1]
            if t and t not in gold_tables:
                gold_tables.append(t)

        # Also extract from subqueries
        sub_matches = re.findall(r'from\s+(\w+)|join\s+(\w+)', gold_sql.lower())
        for m in sub_matches:
            t = m[0] or m[1]
            if t and t not in gold_tables:
                gold_tables.append(t)

        # Validate tables exist in database
        all_tables = self.get_all_tables(db_id)
        gold_tables = [t for t in gold_tables if t in all_tables]

        # If no tables found, use all
        if not gold_tables:
            gold_tables = all_tables

        schema = self.get_filtered_schema(db_id, gold_tables)
        sql = self.generate_sql(question, schema)
        return sql, gold_tables

    # ========== Main Experiment Runner ==========

    def run_full_experiment(self, output_file: str, progress_file: str):
        """Run all 5 methods on complete Spider dev"""
        DEV_PATH = "spider_data/dev.json"

        with open(DEV_PATH, 'r', encoding='utf-8') as f:
            all_data = json.load(f)

        available_dbs = set(os.listdir(self.db_path))
        data = [d for d in all_data if d['db_id'] in available_dbs]

        # Add difficulty
        for item in data:
            item['_difficulty'] = classify_difficulty(item['query'])

        total = len(data)
        print(f"Total samples: {total}")

        # Load progress
        start_idx = 0
        results = {m: [] for m in ['baseline', 'lexical_sl', 'llm_sl', 'upgraded_ef_sl', 'oracle_sl']}

        if os.path.exists(progress_file):
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                start_idx = progress.get('last_processed', 0) + 1
                results = progress.get('results', results)
            print(f"Resuming from {start_idx}")

        for i in range(start_idx, total):
            sample = data[i]
            q = sample['question']
            gold = sample['query']
            db_id = sample['db_id']
            diff = sample['_difficulty']

            print(f"\n[{i+1}/{total}] [{diff}] {q[:50]}...")

            # 1. Baseline
            try:
                pred_base = self.solve_baseline(q, db_id)
                correct_base = self.evaluate_sql(pred_base, gold, db_id)
            except:
                pred_base, correct_base = "ERROR", False

            results['baseline'].append({
                'idx': i, 'question': q, 'gold': gold, 'pred': pred_base,
                'correct': correct_base, 'db_id': db_id, 'difficulty': diff
            })
            print(f"  Baseline:   {'PASS' if correct_base else 'FAIL'}")

            # 2. Lexical SL
            try:
                pred_lex, lex_tables = self.solve_lexical_sl(q, db_id)
                correct_lex = self.evaluate_sql(pred_lex, gold, db_id)
            except:
                pred_lex, correct_lex, lex_tables = "ERROR", False, []

            results['lexical_sl'].append({
                'idx': i, 'question': q, 'gold': gold, 'pred': pred_lex,
                'correct': correct_lex, 'linked_tables': lex_tables,
                'db_id': db_id, 'difficulty': diff
            })
            print(f"  LexicalSL:  {'PASS' if correct_lex else 'FAIL'} (tables: {len(lex_tables)})")

            # 3. LLM-based SL
            try:
                pred_llm, llm_tables = self.solve_llm_sl(q, db_id)
                correct_llm = self.evaluate_sql(pred_llm, gold, db_id)
            except:
                pred_llm, correct_llm, llm_tables = "ERROR", False, []

            results['llm_sl'].append({
                'idx': i, 'question': q, 'gold': gold, 'pred': pred_llm,
                'correct': correct_llm, 'linked_tables': llm_tables,
                'db_id': db_id, 'difficulty': diff
            })
            print(f"  LLM-SL:     {'PASS' if correct_llm else 'FAIL'} (tables: {len(llm_tables)})")

            # 4. Upgraded EF-SL
            try:
                pred_ef, iters, ef_tables = self.solve_upgraded_ef_sl(q, db_id)
                correct_ef = self.evaluate_sql(pred_ef, gold, db_id)
            except:
                pred_ef, correct_ef, iters, ef_tables = "ERROR", False, 0, []

            results['upgraded_ef_sl'].append({
                'idx': i, 'question': q, 'gold': gold, 'pred': pred_ef,
                'correct': correct_ef, 'iterations': iters, 'refined_tables': ef_tables,
                'db_id': db_id, 'difficulty': diff
            })
            print(f"  UpgradedEF: {'PASS' if correct_ef else 'FAIL'} (iter: {iters}, tables: {ef_tables})")

            # 5. Oracle SL
            try:
                pred_oracle, oracle_tables = self.solve_oracle_sl(q, db_id, gold)
                correct_oracle = self.evaluate_sql(pred_oracle, gold, db_id)
            except:
                pred_oracle, correct_oracle, oracle_tables = "ERROR", False, []

            results['oracle_sl'].append({
                'idx': i, 'question': q, 'gold': gold, 'pred': pred_oracle,
                'correct': correct_oracle, 'gold_tables': oracle_tables,
                'db_id': db_id, 'difficulty': diff
            })
            print(f"  OracleSL:   {'PASS' if correct_oracle else 'FAIL'} (tables: {oracle_tables})")

            # Save progress every 20 samples
            if (i + 1) % 20 == 0 or i == total - 1:
                progress = {
                    'last_processed': i,
                    'results': results,
                    'timestamp': datetime.now().isoformat()
                }
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress, f, ensure_ascii=False)

                # Print interim stats
                processed = i + 1
                for method in results:
                    correct = sum(1 for r in results[method] if r.get('correct'))
                    print(f"    {method}: {correct}/{processed} = {correct/processed*100:.1f}%")

        # Save final results
        final = {}
        for method in results:
            correct = sum(1 for r in results[method] if r.get('correct'))
            final[method] = {
                'correct': correct,
                'total': total,
                'accuracy': correct / total * 100,
                'details': results[method]
            }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final, f, ensure_ascii=False, indent=2)

        # Print final results
        print("\n" + "="*80)
        print("5-METHOD COMPARISON - FINAL RESULTS")
        print("="*80)
        for method in ['baseline', 'lexical_sl', 'llm_sl', 'upgraded_ef_sl', 'oracle_sl']:
            correct = final[method]['correct']
            acc = final[method]['accuracy']
            print(f"  {method:>18}: {correct:>4}/{total} = {acc:.2f}%")

        return final


if __name__ == "__main__":
    API_KEY = "sk-ogM3zt64JPjd2IRszE0R9pNs6E79NJTgZJy6RpCNyJoLeZiZ"
    BASE_URL = "https://api.vimsai.com/v1"
    MODEL = "gpt-4o"
    DB_PATH = "spider_data/database"

    exp = FiveMethodExperiment(API_KEY, BASE_URL, DB_PATH, MODEL)
    exp.run_full_experiment("exp_5method_results.json", "exp_5method_progress.json")
