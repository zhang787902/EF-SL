"""
5-Method Comparison Experiment on BIRD Dev (N=1534)
Adapted from exp_5method_comparison.py for BIRD dataset
Key differences from Spider:
1. BIRD has 'evidence' field for domain knowledge
2. BIRD uses _template.sqlite naming
3. BIRD difficulty: simple/moderate/challenging
4. BIRD databases are larger (avg ~10 tables, some >100K rows)
"""

import json
import sqlite3
import re
import os
import sys
import time
import threading

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(errors='replace')
    sys.stderr.reconfigure(errors='replace')
from typing import List, Dict, Tuple, Optional
from openai import OpenAI

# ========== Configuration ==========
API_KEY = "sk-ogM3zt64JPjd2IRszE0R9pNs6E79NJTgZJy6RpCNyJoLeZiZ"
BASE_URL = "https://api.vimsai.com/v1"
MODEL = "gpt-4o"
DB_PATH = "bird_data/database"
DEV_PATH = "bird_data/data/dev_20251106-00000-of-00001.json"
PROGRESS_FILE = "exp_bird_progress.json"
RESULTS_FILE = "exp_bird_results.json"

def classify_difficulty_bird(diff_str: str) -> str:
    """Map BIRD difficulty to our scheme"""
    mapping = {
        'simple': 'easy',
        'moderate': 'medium',
        'challenging': 'hard',
    }
    return mapping.get(diff_str, 'medium')

def get_db_path(db_id: str) -> str:
    """Find the correct SQLite file for a BIRD database"""
    db_dir = f"{DB_PATH}/{db_id}"
    if not os.path.exists(db_dir):
        return None
    # Try template name first
    template_path = f"{db_dir}/{db_id}_template.sqlite"
    if os.path.exists(template_path):
        return template_path
    # Try standard name
    standard_path = f"{db_dir}/{db_id}.sqlite"
    if os.path.exists(standard_path):
        return standard_path
    # Try any .sqlite file
    for f in os.listdir(db_dir):
        if f.endswith('.sqlite'):
            return f"{db_dir}/{f}"
    return None


class BirdExperiment:
    def __init__(self):
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        self.model = MODEL

        # Load dev data
        with open(DEV_PATH, 'r', encoding='utf-8') as f:
            self.dev_data = json.load(f)
        print(f"Loaded {len(self.dev_data)} BIRD dev samples")

        # Schema cache to avoid repeated DB reads
        self._schema_cache = {}
        self._tables_cache = {}
        self._filtered_schema_cache = {}

    def get_full_schema(self, db_id: str) -> str:
        if db_id in self._schema_cache:
            return self._schema_cache[db_id]
        db_file = get_db_path(db_id)
        if not db_file:
            return ""
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            schema = []
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            for table in tables:
                try:
                    cursor.execute(f'PRAGMA table_info("{table}")')
                    cols = [(c[1], c[2]) for c in cursor.fetchall()]
                    if cols:
                        col_defs = ", ".join(f"{n} {t}" for n, t in cols)
                        schema.append(f"CREATE TABLE {table} ({col_defs})")
                except:
                    continue
            for table in tables:
                try:
                    cursor.execute(f'PRAGMA foreign_key_list("{table}")')
                    for fk in cursor.fetchall():
                        schema.append(f"FOREIGN KEY: {table}.{fk[3]} -> {fk[2]}.{fk[4]}")
                except:
                    continue
            conn.close()
            result = "\n".join(schema)
            self._schema_cache[db_id] = result
            return result
        except:
            self._schema_cache[db_id] = ""
            return ""

    def get_filtered_schema(self, db_id: str, tables: List[str]) -> str:
        cache_key = f"{db_id}:{','.join(sorted(tables))}"
        if cache_key in self._filtered_schema_cache:
            return self._filtered_schema_cache[cache_key]
        db_file = get_db_path(db_id)
        if not db_file:
            return ""
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            schema = []
            for table in tables:
                try:
                    cursor.execute(f'PRAGMA table_info("{table}")')
                    cols = [(c[1], c[2]) for c in cursor.fetchall()]
                    if cols:
                        col_defs = ", ".join(f"{n} {t}" for n, t in cols)
                        schema.append(f"CREATE TABLE {table} ({col_defs})")
                except:
                    continue
            for table in tables:
                try:
                    cursor.execute(f'PRAGMA foreign_key_list("{table}")')
                    for fk in cursor.fetchall():
                        schema.append(f"FOREIGN KEY: {table}.{fk[3]} -> {fk[2]}.{fk[4]}")
                except:
                    continue
            conn.close()
            result = "\n".join(schema)
            self._filtered_schema_cache[cache_key] = result
            return result
        except:
            self._filtered_schema_cache[cache_key] = ""
            return ""

    def get_all_tables(self, db_id: str) -> List[str]:
        if db_id in self._tables_cache:
            return self._tables_cache[db_id]
        db_file = get_db_path(db_id)
        if not db_file:
            return []
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            self._tables_cache[db_id] = tables
            return tables
        except:
            self._tables_cache[db_id] = []
            return []

    def execute_sql(self, sql: str, db_id: str, timeout: int = 15) -> Tuple[bool, Optional[List], Optional[str]]:
        db_file = get_db_path(db_id)
        if not db_file:
            return False, None, "Database not found"
        try:
            conn = sqlite3.connect(db_file, timeout=5)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA busy_timeout = 3000")
            result_holder = [None]
            error_holder = [None]
            def run_query():
                try:
                    cursor.execute(sql)
                    result_holder[0] = cursor.fetchall()
                except Exception as e:
                    error_holder[0] = str(e)
            t = threading.Thread(target=run_query)
            t.start()
            t.join(timeout=timeout)
            if t.is_alive():
                conn.close()
                return False, None, "Query timeout"
            if error_holder[0]:
                conn.close()
                return False, None, error_holder[0]
            conn.close()
            return True, result_holder[0], None
        except sqlite3.Error as e:
            return False, None, str(e)

    def evaluate_sql(self, pred_sql: str, gold_sql: str, db_id: str, timeout: int = 15) -> bool:
        db_file = get_db_path(db_id)
        if not db_file:
            return False
        try:
            conn = sqlite3.connect(db_file, timeout=5)
            cursor = conn.cursor()
            result_holder = [None, None]
            error_flag = [False]
            def run_eval():
                try:
                    cursor.execute(pred_sql)
                    result_holder[0] = cursor.fetchall()
                    cursor.execute(gold_sql)
                    result_holder[1] = cursor.fetchall()
                except Exception:
                    error_flag[0] = True
            t = threading.Thread(target=run_eval)
            t.start()
            t.join(timeout=timeout)
            if t.is_alive() or error_flag[0]:
                conn.close()
                return False
            conn.close()
            return sorted(result_holder[0]) == sorted(result_holder[1])
        except:
            return False

    def generate_sql(self, question: str, schema: str, evidence: str = "",
                     feedback_history: str = "") -> str:
        evidence_part = f"\n\nHint/Evidence: {evidence}" if evidence else ""
        history_part = f"\n\nPrevious attempts and errors:\n{feedback_history}" if feedback_history else ""

        prompt = f"""Generate a single SQL query for this question based on the database schema.

Database Schema:
{schema}
{evidence_part}

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
                max_tokens=500,
                timeout=60
            )
            sql = response.choices[0].message.content.strip()
            if "```sql" in sql:
                sql = sql.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql:
                sql = sql.split("```")[1].split("```")[0].strip()
            return sql
        except:
            return "SELECT 1"

    # ========== 5 Methods (same logic as Spider, adapted for BIRD) ==========

    def solve_baseline(self, question: str, db_id: str, evidence: str = "") -> str:
        schema = self.get_full_schema(db_id)
        return self.generate_sql(question, schema, evidence)

    def solve_lexical_sl(self, question: str, db_id: str, evidence: str = "") -> Tuple[str, List[str]]:
        schema = self.get_full_schema(db_id)
        all_tables = self.get_all_tables(db_id)
        question_lower = question.lower()
        if evidence:
            question_lower += " " + evidence.lower()

        linked = []
        # Use schema text for column matching instead of DB queries
        schema_lower = schema.lower()
        for table in all_tables:
            if table.lower() in question_lower:
                linked.append(table)
                continue
            # Check if any column name from this table appears in the question
            # Parse CREATE TABLE statement to find column names
            table_pattern = f"CREATE TABLE {table} ("
            idx = schema_lower.find(table_pattern.lower())
            if idx >= 0:
                start = idx + len(table_pattern)
                end = schema_lower.find(')', start)
                if end > start:
                    col_section = schema_lower[start:end]
                    for part in col_section.split(','):
                        col_name = part.strip().split()[0]
                        if col_name in question_lower:
                            linked.append(table)
                            break

        filtered_schema = self.get_filtered_schema(db_id, linked) if linked else schema
        sql = self.generate_sql(question, filtered_schema, evidence)
        return sql, linked

    def solve_llm_sl(self, question: str, db_id: str, evidence: str = "") -> Tuple[str, List[str]]:
        all_tables = self.get_all_tables(db_id)
        evidence_hint = f"\nHint: {evidence}" if evidence else ""

        select_prompt = f"""Given a database with these tables: {', '.join(all_tables)}

And this question: "{question}"{evidence_hint}

Which tables are needed to answer this question? List only the table names, separated by commas.
Tables:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You select relevant database tables for SQL queries."},
                    {"role": "user", "content": select_prompt}
                ],
                timeout=60,
                temperature=0.0,
                max_tokens=200
            )
            selected_str = response.choices[0].message.content.strip()
            linked = []
            for table in all_tables:
                if table.lower() in selected_str.lower():
                    linked.append(table)
            if not linked:
                linked = all_tables
        except:
            linked = all_tables

        schema = self.get_filtered_schema(db_id, linked)
        sql = self.generate_sql(question, schema, evidence)
        return sql, linked

    def solve_ef_sl(self, question: str, db_id: str, evidence: str = "",
                    max_iter: int = 3) -> Tuple[str, int, List[str]]:
        refined_tables = []
        feedback_history = ""

        for iteration in range(1, max_iter + 1):
            if refined_tables:
                schema = self.get_filtered_schema(db_id, refined_tables)
            else:
                schema = self.get_full_schema(db_id)

            sql = self.generate_sql(question, schema, evidence, feedback_history)
            success, result, error = self.execute_sql(sql, db_id)

            if success and result:
                return sql, iteration, refined_tables

            if error:
                missing = re.findall(r'no such (?:column|table)[:\s]+(\w+)', error, re.IGNORECASE)
                for m in missing:
                    db_file = get_db_path(db_id)
                    if db_file:
                        try:
                            conn = sqlite3.connect(db_file)
                            cursor = conn.cursor()
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                            for (t,) in cursor.fetchall():
                                try:
                                    cursor.execute(f'PRAGMA table_info("{t}")')
                                    if m in [c[1] for c in cursor.fetchall()]:
                                        if t not in refined_tables:
                                            refined_tables.append(t)
                                except:
                                    pass
                            conn.close()
                        except:
                            pass
                feedback = f"Iteration {iteration}: SQL error: {error}. Fix the query."
            else:
                feedback = f"Iteration {iteration}: Empty result. Try LEFT JOIN or relax conditions."

            feedback_history += f"\n{feedback}\nPrevious SQL: {sql}\n"

        return sql, max_iter, refined_tables

    def solve_oracle_sl(self, question: str, gold_sql: str, db_id: str,
                        evidence: str = "") -> Tuple[str, List[str]]:
        all_tables = self.get_all_tables(db_id)
        gold_tables = []
        for table in all_tables:
            pattern = r'\b' + re.escape(table) + r'\b'
            if re.search(pattern, gold_sql, re.IGNORECASE):
                gold_tables.append(table)

        if not gold_tables:
            schema = self.get_full_schema(db_id)
        else:
            schema = self.get_filtered_schema(db_id, gold_tables)

        sql = self.generate_sql(question, schema, evidence)
        return sql, gold_tables

    # ========== Main Run Loop ==========

    def run(self, resume: bool = True):
        # Load progress
        progress = {
            'last_processed': -1,
            'results': {
                'baseline': [],
                'lexical_sl': [],
                'llm_sl': [],
                'upgraded_ef_sl': [],
                'oracle_sl': []
            }
        }
        if resume and os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            print(f"Resuming from sample {progress['last_processed'] + 1}")

        start = progress['last_processed'] + 1
        total = len(self.dev_data)

        for idx in range(start, total):
            sample = self.dev_data[idx]
            question = sample['question']
            gold_sql = sample['SQL']
            db_id = sample['db_id']
            evidence = sample.get('evidence', '')
            difficulty = classify_difficulty_bird(sample.get('difficulty', 'moderate'))

            print(f"\n[{idx+1}/{total}] [{difficulty}] {question[:60]}...")

            # Check DB exists
            if not get_db_path(db_id):
                print(f"  DB not found: {db_id}, skipping")
                for m in ['baseline', 'lexical_sl', 'llm_sl', 'upgraded_ef_sl', 'oracle_sl']:
                    progress['results'][m].append({
                        'idx': idx, 'question': question, 'gold': gold_sql,
                        'pred': 'SKIP', 'correct': False, 'db_id': db_id,
                        'difficulty': difficulty
                    })
                progress['last_processed'] = idx
                if (idx + 1) % 20 == 0:
                    self._save_progress(progress)
                continue

            # Method 1: Baseline
            pred_base = self.solve_baseline(question, db_id, evidence)
            correct_base = self.evaluate_sql(pred_base, gold_sql, db_id)
            progress['results']['baseline'].append({
                'idx': idx, 'question': question, 'gold': gold_sql,
                'pred': pred_base, 'correct': correct_base, 'db_id': db_id,
                'difficulty': difficulty
            })
            print(f"  Baseline:   {'PASS' if correct_base else 'FAIL'}")

            # Method 2: Lexical SL
            pred_lex, linked_lex = self.solve_lexical_sl(question, db_id, evidence)
            correct_lex = self.evaluate_sql(pred_lex, gold_sql, db_id)
            progress['results']['lexical_sl'].append({
                'idx': idx, 'question': question, 'gold': gold_sql,
                'pred': pred_lex, 'correct': correct_lex, 'linked_tables': linked_lex,
                'db_id': db_id, 'difficulty': difficulty
            })
            print(f"  LexicalSL:  {'PASS' if correct_lex else 'FAIL'} (tables: {len(linked_lex)})")

            # Method 3: LLM-SL
            pred_llm, linked_llm = self.solve_llm_sl(question, db_id, evidence)
            correct_llm = self.evaluate_sql(pred_llm, gold_sql, db_id)
            progress['results']['llm_sl'].append({
                'idx': idx, 'question': question, 'gold': gold_sql,
                'pred': pred_llm, 'correct': correct_llm, 'linked_tables': linked_llm,
                'db_id': db_id, 'difficulty': difficulty
            })
            print(f"  LLM-SL:     {'PASS' if correct_llm else 'FAIL'} (tables: {len(linked_llm)})")

            # Method 4: EF-SL
            pred_ef, ef_iter, refined = self.solve_ef_sl(question, db_id, evidence)
            correct_ef = self.evaluate_sql(pred_ef, gold_sql, db_id)
            progress['results']['upgraded_ef_sl'].append({
                'idx': idx, 'question': question, 'gold': gold_sql,
                'pred': pred_ef, 'correct': correct_ef, 'iterations': ef_iter,
                'refined_tables': refined, 'db_id': db_id, 'difficulty': difficulty
            })
            print(f"  UpgradedEF: {'PASS' if correct_ef else 'FAIL'} (iter: {ef_iter}, refined: {refined})")

            # Method 5: Oracle SL
            pred_oracle, gold_tables = self.solve_oracle_sl(question, gold_sql, db_id, evidence)
            correct_oracle = self.evaluate_sql(pred_oracle, gold_sql, db_id)
            progress['results']['oracle_sl'].append({
                'idx': idx, 'question': question, 'gold': gold_sql,
                'pred': pred_oracle, 'correct': correct_oracle, 'gold_tables': gold_tables,
                'db_id': db_id, 'difficulty': difficulty
            })
            print(f"  OracleSL:   {'PASS' if correct_oracle else 'FAIL'} (tables: {gold_tables})")

            progress['last_processed'] = idx

            # Save progress every 20 samples
            if (idx + 1) % 20 == 0:
                self._save_progress(progress)
                # Print running totals
                for m in ['baseline', 'lexical_sl', 'llm_sl', 'upgraded_ef_sl', 'oracle_sl']:
                    n_done = len(progress['results'][m])
                    n_correct = sum(1 for r in progress['results'][m] if r.get('correct', False))
                    print(f"    {m}: {n_correct}/{n_done} = {n_correct/n_done*100:.1f}%")

        # Save final results
        self._save_progress(progress)
        self._save_results(progress)
        print("\n=== BIRD EXPERIMENT COMPLETE ===")

    def _save_progress(self, progress):
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def _save_results(self, progress):
        results = {}
        for method in ['baseline', 'lexical_sl', 'llm_sl', 'upgraded_ef_sl', 'oracle_sl']:
            details = progress['results'][method]
            correct = sum(1 for r in details if r.get('correct', False))
            total = len(details)
            results[method] = {
                'correct': correct,
                'total': total,
                'accuracy': correct / total * 100 if total > 0 else 0,
                'details': details
            }
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Results saved to {RESULTS_FILE}")


if __name__ == '__main__':
    exp = BirdExperiment()
    exp.run(resume=True)
