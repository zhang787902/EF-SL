"""
Baseline Methods for Text-to-SQL
"""
import os
from typing import Dict, List, Optional
import openai


class LLMClient:
    """Base LLM client"""

    def __init__(self, model: str = "gpt-4", temperature: float = 0.3):
        self.model = model
        self.temperature = temperature
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key

    def generate(self, prompt: str, temperature: Optional[float] = None) -> str:
        """Generate text using LLM"""
        if not self.api_key:
            # Mock response for testing without API
            return self._mock_generate(prompt)

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Generate SQL queries based on the given question and schema."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=512
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"API error: {e}")
            return self._mock_generate(prompt)

    def _mock_generate(self, prompt: str) -> str:
        """Mock generation for testing without API"""
        # Extract question and schema from prompt
        if "SELECT" in prompt.upper():
            # Simple heuristic: return a basic SELECT
            return "SELECT * FROM instructor WHERE salary > 50000"
        return "SELECT * FROM instructor"


class GPT4ZeroShot:
    """GPT-4 Zero-shot baseline"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate_sql(self, question: str, schema: Dict) -> str:
        """Generate SQL using zero-shot prompting"""
        prompt = f"""Convert the following question to SQL.

Question: {question}

Generate the SQL query:"""

        return self.llm.generate(prompt)


class GPT4FewShot:
    """GPT-4 Few-shot baseline"""

    def __init__(self, llm_client: LLMClient, examples: Optional[List[Dict]] = None):
        self.llm = llm_client
        self.examples = examples or self._default_examples()

    def _default_examples(self) -> List[Dict]:
        """Default few-shot examples"""
        return [
            {
                'question': 'Find the name of instructors with salary greater than 50000',
                'sql': 'SELECT name FROM instructor WHERE salary > 50000'
            },
            {
                'question': 'What are the distinct departments?',
                'sql': 'SELECT DISTINCT dept_name FROM instructor'
            }
        ]

    def _format_schema(self, schema: Dict) -> str:
        """Format schema for prompt"""
        lines = []
        for table_name, table_info in schema.get('tables', {}).items():
            lines.append(f"Table: {table_name}")
            for col in table_info.get('columns', []):
                pk = " [PK]" if col.get('is_pk') else ""
                lines.append(f"  - {col['name']}: {col['type']}{pk}")
        return '\n'.join(lines)

    def generate_sql(self, question: str, schema: Dict) -> str:
        """Generate SQL using few-shot prompting"""
        prompt = "Here are some examples:\n\n"

        for i, example in enumerate(self.examples, 1):
            prompt += f"Example {i}:\n"
            prompt += f"Question: {example['question']}\n"
            prompt += f"SQL: {example['sql']}\n\n"

        prompt += f"""Database Schema:
{self._format_schema(schema)}

Question: {question}

Generate the SQL query:"""

        return self.llm.generate(prompt)


class DIN_SQL:
    """DIN-SQL: Decomposed In-Context Learning"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def _format_schema(self, schema: Dict) -> str:
        """Format schema for prompt"""
        lines = []
        for table_name, table_info in schema.get('tables', {}).items():
            lines.append(f"Table: {table_name}")
            for col in table_info.get('columns', []):
                lines.append(f"  - {col['name']}: {col['type']}")
        return '\n'.join(lines)

    def schema_linking(self, question: str, schema: Dict) -> List[str]:
        """Step 1: Schema Linking"""
        prompt = f"""Identify which tables and columns are mentioned or implied in the question.

Database Schema:
{self._format_schema(schema)}

Question: {question}

List the relevant tables and columns:"""

        response = self.llm.generate(prompt, temperature=0.1)
        # Parse response to extract tables and columns
        return response.split('\n')

    def classify_query(self, question: str) -> Dict:
        """Step 2: Query Classification"""
        prompt = f"""Classify the SQL query type for this question:

Question: {question}

Categories:
1. Simple SELECT
2. Aggregation (COUNT, SUM, AVG, etc.)
3. JOIN required
4. Nested query
5. GROUP BY required

Classification:"""

        response = self.llm.generate(prompt, temperature=0.1)
        return {'classification': response.strip()}

    def generate_sql(self, question: str, schema: Dict) -> str:
        """Step 3: SQL Generation with decomposition"""
        # Get schema linking
        linked_items = self.schema_linking(question, schema)

        # Get query classification
        classification = self.classify_query(question)

        # Generate SQL
        prompt = f"""Generate SQL based on:

Question: {question}

Relevant Schema Items:
{chr(10).join(linked_items)}

Query Type: {classification['classification']}

Database Schema:
{self._format_schema(schema)}

Generate the SQL query:"""

        return self.llm.generate(prompt)


class SchemaConstraintBaseline:
    """Baseline with only Schema constraints (no MCTS, no feedback)"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def _format_schema_enhanced(self, schema: Dict) -> str:
        """Format schema with detailed constraints"""
        lines = ["Database Schema:\n"]

        for table_name, table_info in schema.get('tables', {}).items():
            lines.append(f"Table: {table_name}")

            # Columns with constraints
            for col in table_info.get('columns', []):
                constraints = []
                if col.get('is_pk'):
                    constraints.append("PRIMARY KEY")
                constraints.append(col['type'])
                constraint_str = f" [{', '.join(constraints)}]" if constraints else ""
                lines.append(f"  - {col['name']}{constraint_str}")

            # Primary keys
            if table_info.get('primary_keys'):
                lines.append(f"  Primary Keys: {', '.join(table_info['primary_keys'])}")

            # Foreign keys
            for fk in table_info.get('foreign_keys', []):
                lines.append(f"  FK: {fk['from_col']} -> {fk['to_table']}.{fk['to_col']}")

            # Sample data
            if table_info.get('sample_data'):
                lines.append("  Sample Data:")
                for row in table_info['sample_data'][:2]:
                    lines.append(f"    {row}")

            lines.append("")

        # Relationships
        if schema.get('relationships'):
            lines.append("Relationships:")
            for rel in schema['relationships']:
                lines.append(f"  - {rel[0]}.{rel[1]} -> {rel[2]}.{rel[3]}")

        return '\n'.join(lines)

    def generate_sql(self, question: str, schema: Dict) -> str:
        """Generate SQL with enhanced schema information"""
        prompt = f"""{self._format_schema_enhanced(schema)}

User Question: {question}

Guidelines:
1. Use table aliases (e.g., T1, T2)
2. Only use tables and columns from the schema
3. Ensure JOIN conditions match foreign key relationships
4. Use aggregate functions correctly with GROUP BY

Generate the SQL query:"""

        return self.llm.generate(prompt, temperature=0.3)


class ExecutionFeedbackBaseline:
    """Baseline with Schema constraints + Execution feedback (no MCTS)"""

    def __init__(self, llm_client: LLMClient, max_iterations: int = 3):
        self.llm = llm_client
        self.max_iterations = max_iterations
        self.schema_baseline = SchemaConstraintBaseline(llm_client)

    def execute_sql(self, sql: str, db_path: str) -> tuple:
        """Safely execute SQL and return result or error"""
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA query_only = ON")
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            conn.close()
            return result, None
        except Exception as e:
            return None, str(e)

    def generate_feedback(self, error: str, sql: str) -> str:
        """Generate feedback from error"""
        error_lower = error.lower()

        if 'syntax error' in error_lower or 'near' in error_lower:
            return f"Syntax error: {error}. Check SQL keywords and parentheses."
        elif 'no such table' in error_lower:
            return f"Table error: {error}. Check table names."
        elif 'no such column' in error_lower:
            return f"Column error: {error}. Check column names and table prefixes."
        elif 'ambiguous' in error_lower:
            return f"Ambiguous column: {error}. Add table name prefix."
        else:
            return f"Execution error: {error}. Please fix."

    def refine_sql(self, question: str, schema: Dict, failed_sql: str, feedback: str) -> str:
        """Refine SQL based on feedback"""
        prompt = f"""Fix the SQL query based on the error.

Question: {question}

Previous SQL:
```sql
{failed_sql}
```

Error: {feedback}

Generate the corrected SQL:"""

        return self.llm.generate(prompt, temperature=0.1)

    def generate_sql(self, question: str, schema: Dict, db_path: str = None) -> Dict:
        """Generate SQL with execution feedback loop"""
        # Initial generation
        sql = self.schema_baseline.generate_sql(question, schema)

        iterations = []

        for i in range(self.max_iterations):
            # Execute
            result, error = self.execute_sql(sql, db_path) if db_path else (None, None)

            iterations.append({
                'iteration': i + 1,
                'sql': sql,
                'error': error,
                'success': error is None
            })

            if error is None:
                break

            # Generate feedback and refine
            feedback = self.generate_feedback(error, sql)
            sql = self.refine_sql(question, schema, sql, feedback)

        return {
            'sql': sql,
            'iterations': iterations,
            'success': iterations[-1]['success'] if iterations else False
        }
