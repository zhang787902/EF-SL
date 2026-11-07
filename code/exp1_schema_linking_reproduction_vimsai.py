"""
实验1: Schema Linking失效复现实验 (VimsAI API版本)
目标: 验证原论文发现(-6.7%)
API: https://api.vimsai.com (OpenAI兼容)
"""

import json
import sqlite3
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
from openai import OpenAI

@dataclass
class SchemaLinkingResult:
    """Schema Linking结果"""
    linked_tables: List[str]
    linked_columns: List[str]
    confidence: Dict[str, float]


class SchemaLinkingReproductionExp:
    """
    复现实验: Schema Linking效果验证
    使用VimsAI API (OpenAI兼容)
    """

    def __init__(self, api_key: str, base_url: str, db_path: str, model: str = "gpt-4o"):
        """
        初始化实验

        Args:
            api_key: API密钥
            base_url: API基础URL (如 https://api.vimsai.com/v1)
            db_path: Spider数据库路径
            model: 模型名称 (默认 gpt-4o)
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.db_path = db_path

    def get_schema(self, db_id: str) -> str:
        """获取数据库完整schema"""
        conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
        cursor = conn.cursor()

        schema = []
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
        for name, sql in cursor.fetchall():
            if sql:
                schema.append(sql)
        conn.close()
        return "\n".join(schema)

    def lexical_schema_linking(self, question: str, schema: str, top_k: int = 3) -> SchemaLinkingResult:
        """
        词法级别的Schema Linking (与原论文一致)
        基于关键词匹配检索相关表和列
        """
        # 解析schema
        tables = self._parse_schema(schema)

        # 提取问题关键词
        keywords = set(re.findall(r'\b[a-zA-Z_]+\b', question.lower()))

        # 计算相似度
        scores = []
        for table_name, columns in tables.items():
            table_score = self._compute_similarity(table_name, keywords)
            column_scores = {col: self._compute_similarity(col, keywords) for col in columns}
            scores.append((table_name, table_score, column_scores))

        # 选择Top-K表
        scores.sort(key=lambda x: x[1], reverse=True)
        linked_tables = [s[0] for s in scores[:top_k]]

        # 选择相关列
        linked_columns = []
        for table_name, _, col_scores in scores[:top_k]:
            for col, score in col_scores.items():
                if score > 0.3:  # 阈值
                    linked_columns.append(f"{table_name}.{col}")

        return SchemaLinkingResult(
            linked_tables=linked_tables,
            linked_columns=linked_columns,
            confidence={t: s for t, s, _ in scores[:top_k]}
        )

    def _parse_schema(self, schema: str) -> Dict[str, List[str]]:
        """解析schema字符串"""
        tables = {}
        current_table = None

        for line in schema.split('\n'):
            # 匹配CREATE TABLE
            match = re.search(r'CREATE TABLE\s+(\w+)', line, re.IGNORECASE)
            if match:
                current_table = match.group(1)
                tables[current_table] = []
            # 匹配列定义
            elif current_table and '(' in line:
                col_match = re.search(r'(\w+)\s+\w+', line.strip())
                if col_match and col_match.group(1).upper() not in ['PRIMARY', 'FOREIGN', 'UNIQUE']:
                    tables[current_table].append(col_match.group(1))

        return tables

    def _compute_similarity(self, text: str, keywords: set) -> float:
        """计算文本与关键词的相似度"""
        text_tokens = set(text.lower().split('_'))
        overlap = len(text_tokens & keywords)
        return overlap / max(len(text_tokens), len(keywords), 1)

    def build_prompt(self, question: str, schema: str,
                     sl_result: SchemaLinkingResult = None,
                     mode: str = "baseline") -> str:
        """
        构建prompt

        Args:
            mode: "baseline" | "static_sl" | "full_schema"
        """
        if mode == "baseline":
            # 基线: 只给问题，不给schema或简要给
            prompt = f"""Generate a SQL query to answer the following question:

Question: {question}

Database Schema:
{schema[:500]}...  # 截断，只给部分

SQL:"""

        elif mode == "static_sl":
            # 静态Schema Linking: 只给检索到的相关表/列
            linked_schema = self._build_linked_schema(sl_result)
            prompt = f"""Generate a SQL query to answer the following question:

Question: {question}

Relevant Schema (identified by Schema Linking):
{linked_schema}

SQL:"""

        elif mode == "full_schema":
            # 完整schema
            prompt = f"""Generate a SQL query to answer the following question:

Question: {question}

Complete Database Schema:
{schema}

SQL:"""

        return prompt

    def _build_linked_schema(self, sl_result: SchemaLinkingResult) -> str:
        """构建链接后的schema描述"""
        lines = ["Linked Tables:"]
        for table in sl_result.linked_tables:
            lines.append(f"  - {table}")

        lines.append("\nLinked Columns:")
        for col in sl_result.linked_columns[:20]:  # 限制数量
            lines.append(f"  - {col}")

        return "\n".join(lines)

    def generate_sql(self, prompt: str) -> str:
        """调用LLM生成SQL (OpenAI API格式)"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Generate SQL queries based on the given question and schema."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0
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
            return ""

    def evaluate_sql(self, pred_sql: str, gold_sql: str, db_id: str) -> bool:
        """评估SQL正确性（执行匹配）"""
        conn = sqlite3.connect(f"{self.db_path}/{db_id}/{db_id}.sqlite")
        cursor = conn.cursor()

        try:
            cursor.execute(pred_sql)
            pred_result = cursor.fetchall()

            cursor.execute(gold_sql)
            gold_result = cursor.fetchall()

            conn.close()
            return set(pred_result) == set(gold_result)
        except Exception as e:
            conn.close()
            return False

    def run_experiment(self, data: List[Dict], sample_size: int = 30) -> Dict:
        """
        运行复现实验

        Args:
            data: Spider dev set samples
            sample_size: 样本数量（与原论文一致）
        """
        import random
        import os
        random.seed(42)

        # 过滤出本地存在数据库的样本
        available_dbs = set()
        for db_dir in os.listdir(self.db_path):
            db_file = f"{self.db_path}/{db_dir}/{db_dir}.sqlite"
            if os.path.exists(db_file):
                available_dbs.add(db_dir)
        print(f"Available databases: {available_dbs}")

        # 只使用本地有数据库的样本
        data = [d for d in data if d['db_id'] in available_dbs]
        print(f"Filtered to {len(data)} samples with local databases")

        samples = random.sample(data, min(sample_size, len(data)))

        results = {
            "baseline": {"correct": 0, "total": 0, "details": []},
            "static_sl": {"correct": 0, "total": 0, "details": []},
            "full_schema": {"correct": 0, "total": 0, "details": []}
        }

        for i, sample in enumerate(samples):
            print(f"\n[{i+1}/{len(samples)}] Processing: {sample['question'][:50]}...")

            question = sample['question']
            gold_sql = sample['query']
            db_id = sample['db_id']

            schema = self.get_schema(db_id)

            # 1. Baseline (无SL)
            prompt_base = self.build_prompt(question, schema, mode="baseline")
            pred_base = self.generate_sql(prompt_base)
            correct_base = self.evaluate_sql(pred_base, gold_sql, db_id)
            results["baseline"]["correct"] += int(correct_base)
            results["baseline"]["total"] += 1
            results["baseline"]["details"].append({
                "question": question,
                "gold": gold_sql,
                "pred": pred_base,
                "correct": correct_base
            })
            print(f"  Baseline: {'PASS' if correct_base else 'FAIL'}")

            # 2. Static Schema Linking
            sl_result = self.lexical_schema_linking(question, schema)
            prompt_sl = self.build_prompt(question, schema, sl_result, mode="static_sl")
            pred_sl = self.generate_sql(prompt_sl)
            correct_sl = self.evaluate_sql(pred_sl, gold_sql, db_id)
            results["static_sl"]["correct"] += int(correct_sl)
            results["static_sl"]["total"] += 1
            results["static_sl"]["details"].append({
                "question": question,
                "gold": gold_sql,
                "pred": pred_sl,
                "correct": correct_sl,
                "linked_tables": sl_result.linked_tables
            })
            print(f"  Static SL: {'[OK]' if correct_sl else '[X]'} (linked: {sl_result.linked_tables})")

            # 3. Full Schema (可选)
            # prompt_full = self.build_prompt(question, schema, mode="full_schema")
            # ...

        # 计算准确率
        for mode in results:
            if results[mode]["total"] > 0:
                results[mode]["accuracy"] = results[mode]["correct"] / results[mode]["total"]

        return results

    def print_results(self, results: Dict):
        """打印实验结果"""
        print("\n" + "="*60)
        print("实验结果: Schema Linking效果验证")
        print("="*60)

        base_acc = results["baseline"].get("accuracy", 0)
        sl_acc = results["static_sl"].get("accuracy", 0)

        print(f"\nBaseline (无SL):     {base_acc:.1%} ({results['baseline']['correct']}/{results['baseline']['total']})")
        print(f"Static SL:           {sl_acc:.1%} ({results['static_sl']['correct']}/{results['static_sl']['total']})")
        print(f"\n差异 (SL - Baseline): {sl_acc - base_acc:+.1%}")

        if sl_acc < base_acc:
            print("\n[WARNING]  发现: Schema Linking降低了性能（复现原论文发现）")
        else:
            print("\n[OK] Schema Linking提升了性能（与原论文发现不同）")

        print("\n" + "="*60)


def load_spider_data(dev_path: str, num_samples: int = 100) -> List[Dict]:
    """加载Spider dev数据"""
    with open(dev_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data[:num_samples]


if __name__ == "__main__":
    # ==================== 配置区域 ====================
    # VimsAI API配置
    API_KEY = "sk-ogM3zt64JPjd2IRszE0R9pNs6E79NJTgZJy6RpCNyJoLeZiZ"
    BASE_URL = "https://api.vimsai.com/v1"  # 注意需要/v1后缀
    MODEL = "gpt-4o"  # 或其他可用模型

    # Spider数据路径 (使用真实数据)
    DB_PATH = "spider_data/database"  # Spider数据库路径
    DEV_PATH = "spider_data/dev.json"  # dev.json路径

    # 实验参数
    SAMPLE_SIZE = 50  # 使用真实数据，增加样本量
    # =================================================

    print("="*60)
    print("Schema Linking复现实验 (VimsAI API)")
    print("="*60)
    print(f"API: {BASE_URL}")
    print(f"Model: {MODEL}")
    print(f"Sample Size: {SAMPLE_SIZE}")
    print("="*60)

    # 加载数据
    print("\nLoading Spider dev data...")
    data = load_spider_data(DEV_PATH, num_samples=100)
    print(f"Loaded {len(data)} samples")

    # 初始化实验
    print("\nInitializing experiment...")
    exp = SchemaLinkingReproductionExp(API_KEY, BASE_URL, DB_PATH, MODEL)

    # 运行实验
    print(f"\nRunning experiment with N={SAMPLE_SIZE}...")
    results = exp.run_experiment(data, sample_size=SAMPLE_SIZE)

    # 输出结果
    exp.print_results(results)

    # 保存结果
    output_file = "exp1_results_vimsai.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_file}")

    # 提示下一步
    print("\n" + "="*60)
    print("下一步:")
    print("  1. 运行分析: python exp1_result_analysis.py exp1_results_vimsai.json")
    print("  2. 检查可视化结果")
    print("="*60)
