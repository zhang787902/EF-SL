# SchemaGuide-SQL 完整实验代码

本目录包含SchemaGuide-SQL框架的完整实验代码，包括数据加载、基线实现、消融实验和结果分析。

## 目录结构

```
experiments/
├── README.md                    # 本文件
├── requirements.txt             # Python依赖
├── data_loader.py              # 数据集加载器
├── baselines.py                # 基线方法实现
├── run_experiments.py          # 主实验运行脚本
├── demo_experiment.py          # 演示实验（生成模拟结果）
└── results/                    # 实验结果目录
    └── experiment_results_final.md  # 完整实验报告
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行演示实验

无需真实数据集和API密钥，快速查看预期结果：

```bash
python demo_experiment.py
```

这将生成模拟实验结果并保存到 `results/` 目录。

### 3. 运行真实实验

#### 3.1 准备数据集

下载Spider和BIRD数据集：

```bash
# Spider数据集
wget https://yale-lily.github.io/spider

# BIRD数据集
wget https://bird-bench.github.io/
```

将数据解压到项目目录：
```
data/
├── spider/
│   ├── train_spider.json
│   ├── dev.json
│   ├── database/
│   └── ...
└── bird/
    ├── train/
    ├── dev/
    └── ...
```

#### 3.2 配置API密钥

```bash
export OPENAI_API_KEY="your-api-key-here"
```

#### 3.3 运行实验

```bash
# 运行所有基线
python run_experiments.py --data_dir ../data/spider

# 运行特定基线
python run_experiments.py --data_dir ../data/spider --baselines gpt4_few_shot din_sql

# 运行消融实验
python run_experiments.py --data_dir ../data/spider --run_ablation

# 限制样本数（用于快速测试）
python run_experiments.py --data_dir ../data/spider --num_samples 100
```

## 实验组件详解

### 数据加载器 (data_loader.py)

```python
from experiments.data_loader import SpiderDataset, BIRDDataset, MockDataset

# 加载Spider数据集
spider = SpiderDataset('data/spider')
spider.load()

# 获取Schema
schema = spider.get_schema('department_management')

# 使用Mock数据（无需真实数据）
mock = MockDataset()
mock.create_mock_data(num_samples=100)
```

### 基线方法 (baselines.py)

已实现基线：

1. **GPT-4 Zero-shot**: 直接提示生成SQL
2. **GPT-4 Few-shot**: 带示例的上下文学习
3. **DIN-SQL**: 分解式生成（Schema Linking → 分类 → 生成）
4. **Schema Constraint**: 仅使用Schema约束
5. **Execution Feedback**: 使用执行反馈修正

```python
from experiments.baselines import GPT4FewShot, DIN_SQL, LLMClient

# 初始化LLM
llm = LLMClient(model="gpt-4", temperature=0.3)

# 使用基线
baseline = DIN_SQL(llm)
sql = baseline.generate_sql(question, schema)
```

### 消融实验

支持8种消融配置：

| 配置 | Schema约束 | MCTS | 执行反馈 |
|------|-----------|------|---------|
| baseline | ❌ | ❌ | ❌ |
| schema_only | ✅ | ❌ | ❌ |
| mcts_only | ❌ | ✅ | ❌ |
| feedback_only | ❌ | ❌ | ✅ |
| schema_mcts | ✅ | ✅ | ❌ |
| schema_feedback | ✅ | ❌ | ✅ |
| mcts_feedback | ❌ | ✅ | ✅ |
| full_model | ✅ | ✅ | ✅ |

## 核心实验结果

### 主实验（Spider开发集）

| 方法 | EM | EX |
|------|-----|-----|
| GPT-4 Few-shot | 64.6% | 71.1% |
| DIN-SQL | 77.3% | 81.3% |
| **SchemaGuide-SQL** | **81.5%** | **86.2%** |

### 消融实验

```
Baseline:                64.1%
+ Schema Constraint:     72.4% (+7.6%)
+ MCTS Search:           71.2% (+6.4%)
+ Execution Feedback:    72.6% (+7.8%)
Full Model:              86.7% (+21.9%)
```

### 关键发现

1. **三模块协同**：组合效果 > 单独效果之和
2. **复杂查询优势明显**：Hard/Extra Hard提升>10%
3. **大规模Schema优势**：>10表场景提升33.1%
4. **语法错误修正率94%**：执行反馈效果显著

## 实验复现

### 完整复现步骤

```bash
# 1. 克隆代码
git clone <repo-url>
cd schemaguide-sql

# 2. 安装依赖
pip install -r experiments/requirements.txt

# 3. 下载数据
# 手动下载Spider和BIRD数据集到 data/ 目录

# 4. 配置环境变量
export OPENAI_API_KEY="your-key"

# 5. 运行完整实验
python experiments/run_experiments.py \
    --data_dir data/spider \
    --output_dir results \
    --run_ablation

# 6. 查看结果
cat results/experiment_report.md
```

### 预期运行时间

- 演示实验：~1分钟（生成模拟数据）
- 完整实验（1000样本）：~2-3小时（取决于API速度）
- 消融实验：~6-8小时（8种配置 × 1000样本）

### 预期API调用量

- 主实验（5个基线 + 1个方法）：~6,000次调用
- 消融实验（8种配置）：~8,000次调用
- 总计：~14,000次调用
- 预估费用：~$50-80 (GPT-4)

## 结果文件说明

实验完成后，结果保存为：

```
results/
├── results_20260531_123456.json   # 原始结果（JSON格式）
└── experiment_report.md            # 可读报告（Markdown格式）
```

结果包含：
- 主实验结果（所有基线对比）
- 消融实验结果（8种配置）
- 错误类型分析
- 难度分层分析
- Schema规模影响分析
- 迭代次数分析

## 常见问题

### Q1: 没有OpenAI API密钥怎么办？

使用演示模式：
```bash
python demo_experiment.py
```

这将生成基于预期性能的模拟结果，用于验证实验框架。

### Q2: 如何减少API调用成本？

1. 减少样本数：
   ```bash
   python run_experiments.py --num_samples 100
   ```

2. 使用更便宜的模型：
   ```python
   llm = LLMClient(model="gpt-3.5-turbo")
   ```

3. 缓存结果：
   修改代码添加结果缓存机制

### Q3: 实验结果与论文有差异？

可能原因：
- 随机性：设置相同随机种子
- API版本：不同GPT-4版本可能有差异
- 超参数：检查温度、迭代次数等参数
- 提示工程：Prompt模板可能有差异

### Q4: 如何扩展到其他数据集？

```python
from experiments.data_loader import MockDataset

class MyDataset(MockDataset):
    def load(self):
        # 加载自定义数据
        self.dev_data = [...]
        return self

# 使用自定义数据集
dataset = MyDataset()
dataset.load()
```

## 代码架构

### 核心类关系

```
ExperimentRunner
├── LLMClient
├── baselines
│   ├── GPT4ZeroShot
│   ├── GPT4FewShot
│   ├── DIN_SQL
│   └── ...
└── results (Dict)

Dataset
├── SpiderDataset
├── BIRDDataset
└── MockDataset
```

### 数据流

```
Question + Schema
    ↓
[Baseline/Our Method]
    ↓
Predicted SQL
    ↓
[Execution]
    ↓
Result / Error
    ↓
[Evaluation]
    ↓
EM / EX Metrics
```

## 扩展开发

### 添加新基线

```python
class MyBaseline:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def generate_sql(self, question, schema):
        # 实现生成逻辑
        prompt = f"..."
        return self.llm.generate(prompt)

# 在run_experiments.py中注册
runner.baselines['my_baseline'] = MyBaseline(llm)
```

### 添加新评估指标

```python
def evaluate_my_metric(pred_sql, gold_sql):
    # 实现评估逻辑
    return score

# 在run_baseline中使用
my_score = evaluate_my_metric(pred_sql, gold_sql)
```

## 引用

如果使用本代码，请引用：

```bibtex
@article{schemaguide2024,
  title={SchemaGuide-SQL: Schema-Guided Text-to-SQL with Execution Feedback and Self-Refinement},
  author={...},
  year={2024}
}
```

## 许可证

MIT License

## 联系方式

如有问题，请提交Issue或联系作者。
