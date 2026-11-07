"""
Text-to-SQL Dataset Loader
Supports Spider and BIRD datasets
"""
import json
import sqlite3
import os
from typing import Dict, List, Tuple, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpiderDataset:
    """Spider dataset loader"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.train_data = []
        self.dev_data = []
        self.test_data = []

    def load(self):
        """Load Spider dataset"""
        logger.info("Loading Spider dataset...")

        # Load train set
        train_file = os.path.join(self.data_dir, "train_spider.json")
        if os.path.exists(train_file):
            with open(train_file, 'r', encoding='utf-8') as f:
                self.train_data = json.load(f)

        # Load dev set
        dev_file = os.path.join(self.data_dir, "dev.json")
        if os.path.exists(dev_file):
            with open(dev_file, 'r', encoding='utf-8') as f:
                self.dev_data = json.load(f)

        logger.info(f"Loaded {len(self.train_data)} train, {len(self.dev_data)} dev examples")
        return self

    def get_schema(self, db_id: str) -> Dict:
        """Get database schema"""
        db_path = os.path.join(self.data_dir, "database", db_id, f"{db_id}.sqlite")

        if not os.path.exists(db_path):
            return {}

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        schema = {
            'db_id': db_id,
            'tables': {},
            'relationships': []
        }

        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = []
            primary_keys = []

            for row in cursor.fetchall():
                cid, name, dtype, notnull, default, pk = row
                columns.append({
                    'name': name,
                    'type': dtype,
                    'is_pk': pk == 1
                })
                if pk == 1:
                    primary_keys.append(name)

            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table});")
            foreign_keys = []
            for row in cursor.fetchall():
                id, seq, ref_table, from_col, to_col, on_update, on_delete, match = row
                foreign_keys.append({
                    'from_table': table,
                    'from_col': from_col,
                    'to_table': ref_table,
                    'to_col': to_col
                })
                schema['relationships'].append((table, from_col, ref_table, to_col))

            # Get sample data
            cursor.execute(f"SELECT * FROM {table} LIMIT 3;")
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
            sample_data = [dict(zip(col_names, row)) for row in rows]

            schema['tables'][table] = {
                'columns': columns,
                'primary_keys': primary_keys,
                'foreign_keys': foreign_keys,
                'sample_data': sample_data
            }

        conn.close()
        return schema


class BIRDDataset:
    """BIRD dataset loader"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.train_data = []
        self.dev_data = []

    def load(self):
        """Load BIRD dataset"""
        logger.info("Loading BIRD dataset...")

        # Load train set
        train_file = os.path.join(self.data_dir, "train", "train.json")
        if os.path.exists(train_file):
            with open(train_file, 'r', encoding='utf-8') as f:
                self.train_data = json.load(f)

        # Load dev set
        dev_file = os.path.join(self.data_dir, "dev", "dev.json")
        if os.path.exists(dev_file):
            with open(dev_file, 'r', encoding='utf-8') as f:
                self.dev_data = json.load(f)

        logger.info(f"Loaded {len(self.train_data)} train, {len(self.dev_data)} dev examples")
        return self


class MockDataset:
    """Mock dataset for testing when real data is not available"""

    def __init__(self):
        self.train_data = []
        self.dev_data = []

    def create_mock_data(self, num_samples: int = 100):
        """Create mock Spider-like data for testing"""
        logger.info(f"Creating {num_samples} mock samples...")

        templates = [
            {
                'question': 'Find the name of instructors whose salary is greater than 50000',
                'query': 'SELECT name FROM instructor WHERE salary > 50000',
                'db_id': 'mock_db_1',
                'difficulty': 'easy'
            },
            {
                'question': 'What are the distinct departments of instructors?',
                'query': 'SELECT DISTINCT dept_name FROM instructor',
                'db_id': 'mock_db_1',
                'difficulty': 'easy'
            },
            {
                'question': 'Find the name and budget of the department with the most employees',
                'query': 'SELECT T1.name, T1.budget FROM department AS T1 JOIN employee AS T2 ON T1.id = T2.dept_id GROUP BY T1.id ORDER BY COUNT(*) DESC LIMIT 1',
                'db_id': 'mock_db_2',
                'difficulty': 'hard'
            },
            {
                'question': 'What is the average salary of instructors in the Computer Science department?',
                'query': 'SELECT AVG(salary) FROM instructor WHERE dept_name = "Comp. Sci."',
                'db_id': 'mock_db_1',
                'difficulty': 'medium'
            },
            {
                'question': 'List all courses taught by instructors from the Physics department',
                'query': 'SELECT T1.title FROM course AS T1 JOIN teaches AS T2 ON T1.course_id = T2.course_id JOIN instructor AS T3 ON T2.id = T3.id WHERE T3.dept_name = "Physics"',
                'db_id': 'mock_db_3',
                'difficulty': 'hard'
            }
        ]

        for i in range(num_samples):
            template = templates[i % len(templates)]
            sample = template.copy()
            sample['question_id'] = f'q{i}'
            self.dev_data.append(sample)

        return self

    def get_schema(self, db_id: str) -> Dict:
        """Get mock schema"""
        schemas = {
            'mock_db_1': {
                'db_id': 'mock_db_1',
                'tables': {
                    'instructor': {
                        'columns': [
                            {'name': 'ID', 'type': 'TEXT', 'is_pk': True},
                            {'name': 'name', 'type': 'TEXT', 'is_pk': False},
                            {'name': 'dept_name', 'type': 'TEXT', 'is_pk': False},
                            {'name': 'salary', 'type': 'INTEGER', 'is_pk': False}
                        ],
                        'primary_keys': ['ID'],
                        'foreign_keys': [],
                        'sample_data': [
                            {'ID': '10101', 'name': 'Smith', 'dept_name': 'Comp. Sci.', 'salary': 65000}
                        ]
                    }
                },
                'relationships': []
            },
            'mock_db_2': {
                'db_id': 'mock_db_2',
                'tables': {
                    'department': {
                        'columns': [
                            {'name': 'id', 'type': 'INTEGER', 'is_pk': True},
                            {'name': 'name', 'type': 'TEXT', 'is_pk': False},
                            {'name': 'budget', 'type': 'INTEGER', 'is_pk': False}
                        ],
                        'primary_keys': ['id'],
                        'foreign_keys': [],
                        'sample_data': []
                    },
                    'employee': {
                        'columns': [
                            {'name': 'id', 'type': 'INTEGER', 'is_pk': True},
                            {'name': 'dept_id', 'type': 'INTEGER', 'is_pk': False},
                            {'name': 'name', 'type': 'TEXT', 'is_pk': False}
                        ],
                        'primary_keys': ['id'],
                        'foreign_keys': [{'from_table': 'employee', 'from_col': 'dept_id',
                                        'to_table': 'department', 'to_col': 'id'}],
                        'sample_data': []
                    }
                },
                'relationships': [('employee', 'dept_id', 'department', 'id')]
            },
            'mock_db_3': {
                'db_id': 'mock_db_3',
                'tables': {
                    'course': {
                        'columns': [
                            {'name': 'course_id', 'type': 'TEXT', 'is_pk': True},
                            {'name': 'title', 'type': 'TEXT', 'is_pk': False},
                            {'name': 'dept_name', 'type': 'TEXT', 'is_pk': False}
                        ],
                        'primary_keys': ['course_id'],
                        'foreign_keys': [],
                        'sample_data': []
                    },
                    'teaches': {
                        'columns': [
                            {'name': 'id', 'type': 'TEXT', 'is_pk': True},
                            {'name': 'course_id', 'type': 'TEXT', 'is_pk': False}
                        ],
                        'primary_keys': [],
                        'foreign_keys': [],
                        'sample_data': []
                    },
                    'instructor': {
                        'columns': [
                            {'name': 'id', 'type': 'TEXT', 'is_pk': True},
                            {'name': 'name', 'type': 'TEXT', 'is_pk': False},
                            {'name': 'dept_name', 'type': 'TEXT', 'is_pk': False}
                        ],
                        'primary_keys': ['id'],
                        'foreign_keys': [],
                        'sample_data': []
                    }
                },
                'relationships': [
                    ('teaches', 'course_id', 'course', 'course_id'),
                    ('teaches', 'id', 'instructor', 'id')
                ]
            }
        }

        return schemas.get(db_id, schemas['mock_db_1'])


def normalize_sql(sql: str) -> str:
    """Normalize SQL for comparison"""
    sql = sql.lower().strip()
    sql = ' '.join(sql.split())  # Remove extra spaces
    sql = sql.replace('"', "'")
    return sql


def evaluate_execution_match(pred_sql: str, gold_sql: str, db_path: str) -> bool:
    """Evaluate if two SQLs produce the same result"""
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA query_only = ON")

        cursor = conn.cursor()

        # Execute predicted SQL
        cursor.execute(pred_sql)
        pred_result = cursor.fetchall()

        # Execute gold SQL
        cursor.execute(gold_sql)
        gold_result = cursor.fetchall()

        conn.close()

        # Compare results (order-agnostic)
        if len(pred_result) != len(gold_result):
            return False

        pred_sorted = sorted(pred_result)
        gold_sorted = sorted(gold_result)

        return pred_sorted == gold_sorted

    except Exception as e:
        return False


def evaluate_exact_match(pred_sql: str, gold_sql: str) -> bool:
    """Evaluate exact SQL string match"""
    return normalize_sql(pred_sql) == normalize_sql(gold_sql)
