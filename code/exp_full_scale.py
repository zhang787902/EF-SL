"""
完整规模实验 (N=1034 Spider dev)
支持批量运行、断点续传、进度保存
"""

import json
import sqlite3
import re
import os
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field, asdict
from openai import OpenAI
from datetime import datetime


@dataclass
class ExecutionResult:
    success: bool
    result: Optional[List] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    empty_result: bool = False


@dataclass
class FeedbackIteration:
    iteration: int
    sql: str
    execution: ExecutionResult
    schema_adjustment: str
    linked_tables: List[str]


class SchemaLinkingExperiment:
    """完整的Schema Linking实验框架"""

    def __init__(self, api_key: str, base_url: str, db_path: str,
                 model: str = "gpt-4o", max_iterations: int = 3):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.db_path = db_path
        self.max_iterations = max_iterations

    def get_schema(self, db_id: str, linked_tables: Optional[List[str]] = None) -> str:
        """获取数据库schema"""
        try:
            conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
            cursor = conn.cursor()

            schema = []

            if linked_tables:
                tables = linked_tables
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    col_defs = []
                    for col in columns:
                        col_name = col[1]
                        col_type = col[2]
                        col_defs.append(f"{col_name} {col_type}")

                    if col_defs:
                        schema.append(f"CREATE TABLE {table} ({', '.join(col_defs)})")
                except:
                    continue

            conn.close()
            return "\n".join(schema)
        except Exception as e:
            return ""

    def execute_sql(self, sql: str, db_id: str) -> ExecutionResult:
        """执行SQL"""
        try:
            conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            conn.close()

            return ExecutionResult(
                success=True,
                result=result,
                empty_result=(len(result) == 0)
            )
        except sqlite3.Error as e:
            error_msg = str(e)
            error_type = self._classify_error(error_msg)
            return ExecutionResult(
                success=False,
                error_type=error_type,
                error_message=error_msg
            )

    def _classify_error(self, error_msg: str) -> str:
        """分类错误"""
        error_lower = error_msg.lower()
        if "no such column" in error_lower:
            return "COLUMN_NOT_FOUND"
        elif "no such table" in error_lower:
            return "TABLE_NOT_FOUND"
        elif "ambiguous column" in error_lower:
            return "AMBIGUOUS_COLUMN"
        elif "syntax error" in error_lower:
            return "SYNTAX_ERROR"
        else:
            return "OTHER_ERROR"

    def analyze_error(self, sql: str, error: ExecutionResult, db_id: str) -> Tuple[List[str], str]:
        """分析错误并调整schema"""
        if error.success:
            return [], "success"

        if error.error_type == "TABLE_NOT_FOUND":
            match = re.search(r"no such table: (\w+)", error.error_message, re.I)
            if match:
                missing_table = match.group(1)
                return [missing_table], f"add_missing_table:{missing_table}"
            potential_tables = re.findall(r"FROM\s+(\w+)|JOIN\s+(\w+)", sql, re.I)
            tables = [t[0] or t[1] for t in potential_tables if t[0] or t[1]]
            return tables, "add_potential_tables"

        elif error.error_type == "COLUMN_NOT_FOUND":
            match = re.search(r"no such column: (\w+)", error.error_message, re.I)
            if match:
                missing_col = match.group(1)
                tables_with_col = self._find_tables_with_column(missing_col, db_id)
                return tables_with_col, f"add_tables_with_column:{missing_col}"

        return [], "full_schema"

    def _find_tables_with_column(self, column: str, db_id: str) -> List[str]:
        """查找包含列的表"""
        try:
            conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
            cursor = conn.cursor()
            tables_with_col = []

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [row[1] for row in cursor.fetchall()]
                    if column in columns:
                        tables_with_col.append(table)
                except:
                    continue

            conn.close()
            return tables_with_col
        except:
            return []

    def generate_sql(self, question: str, schema: str, history: List[FeedbackIteration] = None) -> str:
        """生成SQL"""
        history_str = ""
        if history:
            history_str = "\n\nPrevious attempts:\n"
            for h in history[-2:]:  # 只保留最近2次
                history_str += f"\nAttempt {h.iteration}:\n"
                history_str += f"SQL: {h.sql}\n"
                if h.execution.success:
                    history_str += "Result: Success\n"
                else:
                    history_str += f"Error: {h.execution.error_type}\n"

        prompt = f"""Generate SQL for this question based on the schema.

Schema:
{schema}

Question: {question}
{history_str}

SQL:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a SQL expert."},
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
        except Exception as e:
            return "SELECT 1"

    def solve_with_feedback(self, question: str, db_id: str) -> Tuple[str, List[FeedbackIteration]]:
        """使用Execution-feedback解决"""
        history = []
        current_tables = []

        for iteration in range(1, self.max_iterations + 1):
            schema = self.get_schema(db_id, current_tables) if current_tables else self.get_schema(db_id)
            sql = self.generate_sql(question, schema, history)
            execution = self.execute_sql(sql, db_id)

            history.append(FeedbackIteration(
                iteration=iteration,
                sql=sql,
                execution=execution,
                schema_adjustment="initial" if iteration == 1 else history[-1].schema_adjustment,
                linked_tables=current_tables.copy()
            ))

            if execution.success and not execution.empty_result:
                return sql, history

            new_tables, adjustment = self.analyze_error(sql, execution, db_id)

            if adjustment == "success":
                return sql, history

            if new_tables:
                current_tables = list(set(current_tables + new_tables))

            history[-1].schema_adjustment = adjustment

        return history[-1].sql, history

    def solve_baseline(self, question: str, db_id: str) -> str:
        """Baseline方法（无SL）"""
        schema = self.get_schema(db_id)
        return self.generate_sql(question, schema)

    def solve_static_sl(self, question: str, db_id: str) -> Tuple[str, List[str]]:
        """Static Schema Linking方法"""
        # 简单的关键词匹配
        schema = self.get_schema(db_id)
        tables = self._lexical_schema_linking(question, schema)

        if tables:
            filtered_schema = self.get_schema(db_id, tables)
        else:
            filtered_schema = schema

        sql = self.generate_sql(question, filtered_schema)
        return sql, tables

    def _lexical_schema_linking(self, question: str, schema: str) -> List[str]:
        """简单的关键词匹配SL"""
        question_lower = question.lower()
        tables = []

        # 从schema中提取表名
        for line in schema.split('\n'):
            if line.startswith('CREATE TABLE'):
                match = re.search(r'CREATE TABLE (\w+)', line)
                if match:
                    table_name = match.group(1)
                    # 检查表名或相关关键词是否在问题中
                    if table_name.lower() in question_lower:
                        tables.append(table_name)
                    else:
                        # 检查列名
                        cols_match = re.search(r'\((.*)\)', line)
                        if cols_match:
                            cols = cols_match.group(1).split(',')
                            for col in cols:
                                col_name = col.strip().split()[0].lower()
                                if col_name in question_lower:
                                    tables.append(table_name)
                                    break

        return list(set(tables))

    def evaluate_sql(self, pred_sql: str, gold_sql: str, db_id: str) -> bool:
        """评估SQL"""
        try:
            conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
            cursor = conn.cursor()

            cursor.execute(pred_sql)
            pred_result = cursor.fetchall()

            cursor.execute(gold_sql)
            gold_result = cursor.fetchall()

            conn.close()

            pred_sorted = sorted(pred_result) if pred_result else []
            gold_sorted = sorted(gold_result) if gold_result else []

            return pred_sorted == gold_sorted
        except:
            return False


def run_full_experiment():
    """运行完整实验"""
    # 配置
    API_KEY = "sk-ogM3zt64JPjd2IRszE0R9pNs6E79NJTgZJy6RpCNyJoLeZiZ"
    BASE_URL = "https://api.vimsai.com/v1"
    MODEL = "gpt-4o"
    DB_PATH = "spider_data/database"
    DEV_PATH = "spider_data/dev.json"

    # 输出文件
    OUTPUT_FILE = "exp_full_results.json"
    PROGRESS_FILE = "exp_full_progress.json"

    # 加载数据
    print("Loading Spider dev data...")
    with open(DEV_PATH, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    # 过滤有数据库的样本
    available_dbs = set(os.listdir(DB_PATH))
    data = [d for d in all_data if d['db_id'] in available_dbs]
    print(f"Total samples with DB: {len(data)}")

    # 加载进度
    start_idx = 0
    results = {"baseline": [], "static_sl": [], "execution_feedback": []}

    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            progress = json.load(f)
            start_idx = progress.get('last_processed', 0) + 1
            results = progress.get('results', results)
        print(f"Resuming from sample {start_idx}")

    # 初始化实验
    exp = SchemaLinkingExperiment(API_KEY, BASE_URL, DB_PATH, MODEL)

    # 运行实验
    total = len(data)
    correct_baseline = sum(1 for r in results["baseline"] if r.get('correct', False))
    correct_static = sum(1 for r in results["static_sl"] if r.get('correct', False))
    correct_ef = sum(1 for r in results["execution_feedback"] if r.get('correct', False))

    print(f"\nRunning experiments on {total} samples...")
    print(f"Current progress: Baseline={correct_baseline}, StaticSL={correct_static}, EF={correct_ef}")

    for i in range(start_idx, total):
        sample = data[i]
        print(f"\n[{i+1}/{total}] {sample['question'][:60]}...")

        question = sample['question']
        gold_sql = sample['query']
        db_id = sample['db_id']

        # Baseline
        try:
            pred_base = exp.solve_baseline(question, db_id)
            correct_base = exp.evaluate_sql(pred_base, gold_sql, db_id)
        except Exception as e:
            pred_base = "ERROR"
            correct_base = False

        results["baseline"].append({
            "idx": i,
            "question": question,
            "gold": gold_sql,
            "pred": pred_base,
            "correct": correct_base,
            "db_id": db_id
        })
        print(f"  Baseline: {'PASS' if correct_base else 'FAIL'}")

        # Static SL
        try:
            pred_static, linked_tables = exp.solve_static_sl(question, db_id)
            correct_static = exp.evaluate_sql(pred_static, gold_sql, db_id)
        except Exception as e:
            pred_static = "ERROR"
            linked_tables = []
            correct_static = False

        results["static_sl"].append({
            "idx": i,
            "question": question,
            "gold": gold_sql,
            "pred": pred_static,
            "correct": correct_static,
            "linked_tables": linked_tables,
            "db_id": db_id
        })
        print(f"  StaticSL: {'PASS' if correct_static else 'FAIL'} (tables: {linked_tables})")

        # Execution-feedback SL
        try:
            pred_ef, history = exp.solve_with_feedback(question, db_id)
            correct_ef = exp.evaluate_sql(pred_ef, gold_sql, db_id)
            iterations = len(history)
        except Exception as e:
            pred_ef = "ERROR"
            correct_ef = False
            iterations = 0

        results["execution_feedback"].append({
            "idx": i,
            "question": question,
            "gold": gold_sql,
            "pred": pred_ef,
            "correct": correct_ef,
            "iterations": iterations,
            "db_id": db_id
        })
        print(f"  EF-SL: {'PASS' if correct_ef else 'FAIL'} (iter: {iterations})")

        # 更新统计
        if correct_base:
            correct_baseline += 1
        if correct_static:
            correct_static += 1
        if correct_ef:
            correct_ef += 1

        # 保存进度
        if (i + 1) % 10 == 0 or i == total - 1:
            progress = {
                "last_processed": i,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False)

            # 打印当前统计
            processed = i + 1
            print(f"\n  Progress: {processed}/{total} ({processed/total*100:.1f}%)")
            print(f"  Baseline: {correct_baseline/processed*100:.1f}% ({correct_baseline}/{processed})")
            print(f"  StaticSL: {correct_static/processed*100:.1f}% ({correct_static}/{processed})")
            print(f"  EF-SL:    {correct_ef/processed*100:.1f}% ({correct_ef}/{processed})")

    # 保存最终结果
    final_results = {
        "total_samples": total,
        "baseline": {
            "correct": correct_baseline,
            "accuracy": correct_baseline / total * 100,
            "details": results["baseline"]
        },
        "static_sl": {
            "correct": correct_static,
            "accuracy": correct_static / total * 100,
            "details": results["static_sl"]
        },
        "execution_feedback": {
            "correct": correct_ef,
            "accuracy": correct_ef / total * 100,
            "details": results["execution_feedback"]
        }
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)

    print("\n" + "="*60)
    print("FULL SCALE EXPERIMENT COMPLETED")
    print("="*60)
    print(f"Total samples: {total}")
    print(f"Baseline: {correct_baseline}/{total} = {correct_baseline/total*100:.1f}%")
    print(f"StaticSL: {correct_static}/{total} = {correct_static/total*100:.1f}%")
    print(f"EF-SL:    {correct_ef}/{total} = {correct_ef/total*100:.1f}%")
    print("="*60)

    return final_results


if __name__ == "__main__":
    run_full_experiment()
