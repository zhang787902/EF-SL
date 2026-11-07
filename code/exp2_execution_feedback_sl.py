"""
实验2: Execution-feedback Driven Schema Linking
核心创新: 通过执行反馈动态调整Schema Linking，避免预过滤
"""

import json
import sqlite3
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from openai import OpenAI
import traceback


@dataclass
class ExecutionResult:
    """SQL执行结果"""
    success: bool
    result: Optional[List] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    empty_result: bool = False


@dataclass
class FeedbackIteration:
    """单次迭代记录"""
    iteration: int
    sql: str
    execution: ExecutionResult
    schema_adjustment: str
    linked_tables: List[str]


class ExecutionFeedbackSL:
    """
    Execution-feedback driven Schema Linking
    核心思想: 先执行，根据错误反馈调整Schema，再重试
    """

    def __init__(self, api_key: str, base_url: str, db_path: str,
                 model: str = "gpt-4o", max_iterations: int = 3):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.db_path = db_path
        self.max_iterations = max_iterations

    def get_schema(self, db_id: str, linked_tables: Optional[List[str]] = None) -> str:
        """获取数据库schema，可选只返回linked_tables"""
        conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
        cursor = conn.cursor()

        schema = []

        # 获取所有表或指定表
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

                schema.append(f"CREATE TABLE {table} ({', '.join(col_defs)})")
            except Exception as e:
                continue

        # 获取外键关系
        for table in tables:
            try:
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                fks = cursor.fetchall()
                for fk in fks:
                    from_col = fk[3]
                    to_table = fk[2]
                    to_col = fk[4]
                    schema.append(
                        f"-- Foreign Key: {table}.{from_col} -> {to_table}.{to_col}")
            except Exception as e:
                continue

        conn.close()
        return "\n".join(schema)

    def execute_sql(self, sql: str, db_id: str) -> ExecutionResult:
        """执行SQL并返回结果"""
        conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
        cursor = conn.cursor()

        try:
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
            error_type = self._classify_error(error_msg, sql)
            conn.close()

            return ExecutionResult(
                success=False,
                error_type=error_type,
                error_message=error_msg
            )

    def _classify_error(self, error_msg: str, sql: str) -> str:
        """分类SQL错误类型"""
        error_lower = error_msg.lower()

        if "no such column" in error_lower:
            return "COLUMN_NOT_FOUND"
        elif "no such table" in error_lower:
            return "TABLE_NOT_FOUND"
        elif "ambiguous column" in error_lower:
            return "AMBIGUOUS_COLUMN"
        elif "syntax error" in error_lower:
            return "SYNTAX_ERROR"
        elif "misuse" in error_lower:
            return "MISUSE"
        else:
            return "OTHER_ERROR"

    def analyze_error(self, question: str, sql: str, error: ExecutionResult,
                      current_schema: str, db_id: str) -> Tuple[List[str], str]:
        """
        分析错误并决定Schema调整策略
        返回: (需要添加的表列表, 调整策略描述)
        """
        if error.success:
            if error.empty_result:
                # 执行成功但结果为空，可能需要检查条件
                return [], "empty_result"
            return [], "success"

        # 根据错误类型决定策略
        if error.error_type == "TABLE_NOT_FOUND":
            # 提取缺失的表名
            match = re.search(r"no such table: (\w+)", error.error_message, re.I)
            if match:
                missing_table = match.group(1)
                return [missing_table], f"add_missing_table:{missing_table}"

            # 尝试从SQL中提取可能的表名
            potential_tables = self._extract_potential_tables(sql)
            return potential_tables, "add_potential_tables"

        elif error.error_type == "COLUMN_NOT_FOUND":
            # 列不存在，需要检查包含该列的表
            match = re.search(r"no such column: (\w+)", error.error_message, re.I)
            if match:
                missing_col = match.group(1)
                # 获取所有包含该列的表
                tables_with_col = self._find_tables_with_column(missing_col, db_id)
                return tables_with_col, f"add_tables_with_column:{missing_col}"

        elif error.error_type == "AMBIGUOUS_COLUMN":
            # 列歧义，需要添加表前缀
            return [], "need_table_prefix"

        # 默认策略：添加所有表
        return [], "full_schema"

    def _extract_potential_tables(self, sql: str) -> List[str]:
        """从SQL中提取可能的表名"""
        # 简单的正则匹配
        patterns = [
            r"FROM\s+(\w+)",
            r"JOIN\s+(\w+)",
            r"INTO\s+(\w+)",
        ]
        tables = []
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.I)
            tables.extend(matches)
        return list(set(tables))

    def _find_tables_with_column(self, column: str, db_id: str) -> List[str]:
        """查找包含指定列的所有表"""
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

    def generate_sql(self, question: str, schema: str, history: List[FeedbackIteration] = None) -> str:
        """生成SQL，可选包含历史迭代信息"""

        history_str = ""
        if history:
            history_str = "\n\nPrevious attempts:\n"
            for h in history:
                history_str += f"\nAttempt {h.iteration}:\n"
                history_str += f"SQL: {h.sql}\n"
                if h.execution.success:
                    history_str += f"Result: Success (rows: {len(h.execution.result) if h.execution.result else 0})\n"
                else:
                    history_str += f"Error: {h.execution.error_type} - {h.execution.error_message}\n"
                history_str += f"Adjustment: {h.schema_adjustment}\n"

        prompt = f"""You are an expert SQL generator. Given a natural language question and database schema, generate the correct SQL query.

Database Schema:
{schema}

Question: {question}
{history_str}

Generate only the SQL query without any explanation.
SQL:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Generate accurate SQL queries based on the schema and question."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=500
            )
            sql = response.choices[0].message.content.strip()
            # 提取SQL代码块
            if "```sql" in sql:
                sql = sql.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql:
                sql = sql.split("```")[1].split("```")[0].strip()
            return sql
        except Exception as e:
            print(f"Generation error: {type(e).__name__}")
            return "SELECT 1"

    def solve_with_feedback(self, question: str, db_id: str) -> Tuple[str, List[FeedbackIteration]]:
        """
        使用Execution-feedback解决Text-to-SQL
        返回: (最终SQL, 迭代历史)
        """
        history = []
        current_tables = []  # 初始为空，使用完整schema

        for iteration in range(1, self.max_iterations + 1):
            # 获取当前schema
            if current_tables:
                schema = self.get_schema(db_id, current_tables)
            else:
                schema = self.get_schema(db_id)

            # 生成SQL
            sql = self.generate_sql(question, schema, history)

            # 执行SQL
            execution = self.execute_sql(sql, db_id)

            # 记录迭代
            iteration_record = FeedbackIteration(
                iteration=iteration,
                sql=sql,
                execution=execution,
                schema_adjustment="initial" if iteration == 1 else history[-1].schema_adjustment,
                linked_tables=current_tables.copy()
            )
            history.append(iteration_record)

            # 检查是否成功
            if execution.success and not execution.empty_result:
                return sql, history

            # 分析错误并调整schema
            new_tables, adjustment = self.analyze_error(
                question, sql, execution, schema, db_id
            )

            if adjustment == "success":
                return sql, history

            # 更新linked tables
            if new_tables:
                current_tables = list(set(current_tables + new_tables))

            # 更新最后一条记录的adjustment
            history[-1].schema_adjustment = adjustment

        # 返回最后一次尝试的SQL
        return history[-1].sql, history

    def run_experiment(self, data: List[Dict], sample_size: int = 50) -> Dict:
        """运行完整实验"""
        import random
        random.seed(42)
        samples = random.sample(data, min(sample_size, len(data)))

        results = {
            "execution_feedback_sl": {
                "correct": 0,
                "total": 0,
                "details": [],
                "avg_iterations": 0
            }
        }

        total_iterations = 0

        for i, sample in enumerate(samples):
            print(f"\n[{i+1}/{len(samples)}] Processing: {sample['question'][:50]}...")

            question = sample['question']
            gold_sql = sample['query']
            db_id = sample['db_id']

            # Execution-feedback SL
            pred_sql, history = self.solve_with_feedback(question, db_id)
            correct = self.evaluate_sql(pred_sql, gold_sql, db_id)

            results["execution_feedback_sl"]["correct"] += int(correct)
            results["execution_feedback_sl"]["total"] += 1
            results["execution_feedback_sl"]["details"].append({
                "question": question,
                "gold": gold_sql,
                "pred": pred_sql,
                "correct": correct,
                "iterations": len(history),
                "history": [
                    {
                        "iteration": h.iteration,
                        "sql": h.sql,
                        "success": h.execution.success,
                        "error_type": h.execution.error_type,
                        "adjustment": h.schema_adjustment
                    } for h in history
                ]
            })

            total_iterations += len(history)
            print(f"  EF-SL: {'PASS' if correct else 'FAIL'} (iterations: {len(history)})")

        # 计算平均迭代次数
        if results["execution_feedback_sl"]["total"] > 0:
            results["execution_feedback_sl"]["avg_iterations"] = (
                total_iterations / results["execution_feedback_sl"]["total"]
            )

        return results

    def evaluate_sql(self, pred_sql: str, gold_sql: str, db_id: str) -> bool:
        """评估SQL正确性"""
        try:
            conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
            cursor = conn.cursor()

            cursor.execute(pred_sql)
            pred_result = cursor.fetchall()

            cursor.execute(gold_sql)
            gold_result = cursor.fetchall()

            conn.close()

            # 排序后比较
            pred_sorted = sorted(pred_result) if pred_result else []
            gold_sorted = sorted(gold_result) if gold_result else []

            return pred_sorted == gold_sorted
        except Exception as e:
            return False

    def print_results(self, results: Dict):
        """打印实验结果"""
        ef_results = results["execution_feedback_sl"]
        ef_acc = ef_results["correct"] / ef_results["total"] * 100

        print("\n" + "="*60)
        print("Execution-feedback Schema Linking 实验结果")
        print("="*60)
        print(f"Execution-feedback SL: {ef_acc:.1f}% ({ef_results['correct']}/{ef_results['total']})")
        print(f"平均迭代次数: {ef_results['avg_iterations']:.2f}")
        print("="*60)


def load_spider_data(dev_path: str, num_samples: int = 100) -> List[Dict]:
    """加载Spider dev数据"""
    with open(dev_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data[:num_samples]


if __name__ == "__main__":
    # 配置
    API_KEY = "sk-ogM3zt64JPjd2IRszE0R9pNs6E79NJTgZJy6RpCNyJoLeZiZ"
    BASE_URL = "https://api.vimsai.com/v1"
    MODEL = "gpt-4o"
    DB_PATH = "spider_data/database"
    DEV_PATH = "spider_data/dev.json"
    SAMPLE_SIZE = 50

    print("="*60)
    print("实验2: Execution-feedback Schema Linking")
    print("="*60)
    print(f"Model: {MODEL}")
    print(f"Sample Size: {SAMPLE_SIZE}")
    print(f"Max Iterations: 3")
    print("="*60)

    # 加载数据
    print("\nLoading Spider dev data...")
    data = load_spider_data(DEV_PATH, num_samples=100)

    # 过滤有数据库的样本
    import os
    available_dbs = set(os.listdir(DB_PATH))
    data = [d for d in data if d['db_id'] in available_dbs]
    print(f"Filtered to {len(data)} samples with local databases")

    # 初始化实验
    print("\nInitializing experiment...")
    exp = ExecutionFeedbackSL(API_KEY, BASE_URL, DB_PATH, MODEL)

    # 运行实验
    print(f"\nRunning experiment with N={SAMPLE_SIZE}...")
    results = exp.run_experiment(data, sample_size=SAMPLE_SIZE)

    # 输出结果
    exp.print_results(results)

    # 保存结果
    output_file = "exp2_execution_feedback_sl.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_file}")

    print("\n" + "="*60)
    print("下一步:")
    print("  1. 对比实验1和实验2结果")
    print("  2. 分析迭代次数分布")
    print("="*60)
