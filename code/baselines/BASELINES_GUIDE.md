# Text-to-SQL 基线方法代码指南

本目录包含所有主要Text-to-SQL基线方法的开源代码，用于对比实验。

---

## 快速开始

### 一键下载所有基线

**Linux/Mac:**
```bash
bash clone_baselines.sh
```

**Windows:**
```cmd
clone_baselines.bat
```

---

## 基线方法详情

### 1. RESDSQL (推荐首选)

**论文**: RESDSQL: Decoupling Schema Linking and Skeleton Parsing for Text-to-SQL (AAAI 2023)

**性能**: Spider Test Execution Accuracy: 79.9%

**特点**:
- 解耦Schema Linking和骨架解析
- 支持NatSQL中间表示
- 代码完整，文档清晰
- **最推荐的基线**

**安装:**
```bash
cd text2sql_baselines/RESDSQL
pip install -r requirements.txt
```

**运行:**
```bash
# 下载预训练模型
bash download_checkpoint.sh

# 运行推理
python inference.py \
    --model_path checkpoints/RESDSQL-3B \
    --input_data spider/dev.json \
    --output_file predictions.sql
```

**数据准备:**
```bash
# 下载Spider数据
bash download_spider_data.sh
```

---

### 2. Alpha-SQL (MCTS方法)

**论文**: Alpha-SQL: Zero-Shot Text-to-SQL using Monte Carlo Tree Search (ICML 2025)

**性能**: Spider Test ~82%

**特点**:
- Zero-shot设置，无需微调
- 使用MCTS进行SQL搜索
- 结合LLM作为策略和价值网络
- 支持复杂多表查询

**安装:**
```bash
cd text2sql_baselines/Alpha-SQL
pip install -r requirements.txt
```

**运行:**
```bash
# 设置OpenAI API密钥
export OPENAI_API_KEY="your-key"

# 运行MCTS搜索
python alpha_sql.py \
    --question "Find the name of instructors with salary > 50000" \
    --schema schema.json \
    --num_simulations 50
```

**配置:**
```bash
# 修改config.yaml
vim configs/default.yaml
```

---

### 3. RSL-SQL (BIRD优化)

**论文**: RSL-SQL: Robust Schema Linking in Text-to-SQL Generation

**性能**: BIRD Dev Execution Accuracy: ~65-68%

**特点**:
- 鲁棒性Schema Linking
- 专门针对BIRD benchmark优化
- 结合语义相似度和规则匹配

**安装:**
```bash
cd text2sql_baselines/RSL-SQL
pip install -r requirements.txt
```

**运行:**
```bash
# Schema Linking
python schema_linking.py \
    --input_data bird/dev.json \
    --output_file linked_schema.json

# SQL生成
python generate_sql.py \
    --schema_file linked_schema.json \
    --output predictions.sql
```

---

### 4. RAT-SQL (经典方法)

**论文**: RAT-SQL: Relation-Aware Schema Encoding and Linking for Text-to-SQL Parsers (ACL 2020)

**性能**: Spider Test Exact Match: 65.8%

**特点**:
- 关系感知注意力机制
- 显式schema linking模块
- 基于Transformer的编码器-解码器

**安装:**
```bash
cd text2sql_baselines/rat-sql

# 需要Docker
bash docker_build.sh

# 或者本地安装
pip install -r requirements.txt
python setup.py install
```

**运行:**
```bash
# 预处理数据
python preprocess.py \
    --data spider \
    --output processed_data

# 训练
python train.py \
    --config configs/spider_config.json \
    --data processed_data

# 推理
python infer.py \
    --checkpoint checkpoints/best_model.pt \
    --input spider/dev.json
```

**注意**: 配置较复杂，需要4GB+内存

---

### 5. PICARD (约束解码)

**论文**: PICARD: Parsing Incrementally for Constrained Auto-Regressive Decoding (EMNLP 2021)

**性能**: Spider Test Exact Match: 79.5%

**特点**:
- 基于SQL语法的约束解码
- 确保生成SQL的语法正确性
- 可与T5等模型结合

**安装:**
```bash
cd text2sql_baselines/picard

# 安装依赖
pip install -r requirements.txt

# 安装PICARD
python setup.py install
```

**运行:**
```bash
# 使用T5+PICARD
python run_picard.py \
    --model_type t5 \
    --model_name_or_path t5-large \
    --dataset spider \
    --output_dir outputs
```

**注意**: 需要特定环境配置

---

### 6. DIN-SQL (分解式方法)

**论文**: DIN-SQL: Decomposed In-Context Learning of Text-to-SQL with Self-Correction

**性能**: Spider Test Execution Accuracy: ~85.3%

**特点**:
- 分解为4个子任务
- Schema Linking → 分类/聚合检测 → SQL生成 → 自纠错
- 使用Few-shot prompting，无需微调

**安装:**
```bash
cd text2sql_baselines/DIN-SQL
pip install -r requirements.txt
```

**运行:**
```bash
# 设置API密钥
export OPENAI_API_KEY="your-key"

# 完整流程
python din_sql.py \
    --question "Find instructors with salary > 50000" \
    --schema schema.json \
    --steps all  # [schema_linking, classification, generation, correction]
```

**分步运行:**
```bash
# 只运行schema linking
python schema_linking.py --input questions.json

# 只运行SQL生成
python sql_generation.py --linked_schema linked.json
```

---

## 数据集准备

### Spider数据集

**下载:**
```bash
cd text2sql_baselines/spider

# 下载数据
bash download.sh

# 或者手动下载
wget https://yale-lily.github.io/spider
```

**目录结构:**
```
spider/
├── train_spider.json      # 训练集
├── train_others.json      # 其他训练数据
├── dev.json               # 开发集
├── database/              # 数据库文件
│   ├── department_management/
│   ├── university/
│   └── ...
└── tables.json            # Schema信息
```

### BIRD数据集

**下载:**
```bash
# 从官网下载
https://bird-bench.github.io/

# 解压到目录
unzip bird_train.zip -d bird/
unzip bird_dev.zip -d bird/
```

---

## 评估脚本

### 官方评估工具 (test-suite-sql-eval)

**安装:**
```bash
cd text2sql_baselines/test-suite-sql-eval
pip install -r requirements.txt
```

**运行评估:**
```bash
# Execution accuracy
python evaluation.py \
    --gold gold.sql \
    --pred pred.sql \
    --db database_dir \
    --etype exec

# Test suite accuracy (更严格)
python evaluation.py \
    --gold gold.sql \
    --pred pred.sql \
    --db database_dir \
    --etype all
```

**评估指标:**
- `exec`: Execution accuracy
- `match`: Exact match
- `all`: Test suite accuracy

---

## 快速对比实验

### 准备测试数据

```python
# 准备100个样本进行快速测试
import json

with open('spider/dev.json') as f:
    data = json.load(f)

# 随机采样100个
import random
random.seed(42)
sample = random.sample(data, 100)

with open('dev_sample_100.json', 'w') as f:
    json.dump(sample, f, indent=2)
```

### 批量运行基线

```bash
#!/bin/bash
# run_comparison.sh

DATA="dev_sample_100.json"
OUTPUT_DIR="comparison_results"
mkdir -p $OUTPUT_DIR

echo "Running RESDSQL..."
cd RESDSSQL
python inference.py --input_data $DATA --output_file $OUTPUT_DIR/resdsql.sql
cd ..

echo "Running Alpha-SQL..."
cd Alpha-SQL
python alpha_sql.py --input $DATA --output $OUTPUT_DIR/alphasql.sql
cd ..

echo "Running DIN-SQL..."
cd DIN-SQL
python din_sql.py --input $DATA --output $OUTPUT_DIR/dinsql.sql
cd ..

echo "Evaluating all..."
python text2sql_baselines/test-suite-sql-eval/evaluation.py \
    --gold $DATA \
    --pred $OUTPUT_DIR/resdsql.sql \
    --etype exec
```

---

## 常见问题

### Q1: 哪个基线最容易复现？

**推荐顺序:**
1. **RESDSQL** - 代码最完整，文档清晰
2. **Alpha-SQL** - 基于LLM，无需训练
3. **DIN-SQL** - 纯提示工程，容易理解
4. **RAT-SQL** - 配置复杂，需要GPU

### Q2: 没有GPU怎么办？

**CPU-only基线:**
- DIN-SQL (使用API)
- Alpha-SQL (使用API)
- 部分RESDSQL功能

**需要GPU的基线:**
- RAT-SQL (训练需要)
- PICARD (大模型推理)

### Q3: 基线结果与论文不一致？

**可能原因:**
1. **随机种子**: 检查是否固定随机种子
2. **模型版本**: 使用论文指定的模型版本
3. **超参数**: 检查默认参数是否与论文一致
4. **数据预处理**: 确认数据处理方式相同

### Q4: 如何快速测试基线？

**建议流程:**
1. 先用`dev_sample_100.json`测试
2. 确认结果合理后再跑完整数据集
3. 使用`test-suite-sql-eval`确保评估方式一致

---

## 性能对比表

| 基线 | 年份 | Spider EX | BIRD EX | 代码难度 | 推荐度 |
|------|------|-----------|---------|---------|--------|
| RESDSQL | 2023 | 79.9% | 58.2% | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Alpha-SQL | 2025 | ~82% | ~62% | ⭐⭐ | ⭐⭐⭐⭐ |
| RSL-SQL | 2024 | - | ~67% | ⭐⭐ | ⭐⭐⭐⭐ |
| RAT-SQL | 2020 | - | - | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| PICARD | 2021 | - | - | ⭐⭐⭐ | ⭐⭐⭐ |
| DIN-SQL | 2023 | ~85% | ~55% | ⭐ | ⭐⭐⭐⭐ |

**推荐**: 优先实现RESDSQL和DIN-SQL作为对比

---

## 引用

如果使用这些基线，请引用：

```bibtex
@inproceedings{resdsql2023,
  title={RESDSQL: Decoupling Schema Linking and Skeleton Parsing for Text-to-SQL},
  author={Li, Lihan and others},
  booktitle={AAAI},
  year={2023}
}

@inproceedings{alphasql2025,
  title={Alpha-SQL: Zero-Shot Text-to-SQL using Monte Carlo Tree Search},
  booktitle={ICML},
  year={2025}
}

@article{dinsql2023,
  title={DIN-SQL: Decomposed In-Context Learning of Text-to-SQL with Self-Correction},
  author={Pourreza, Mohammadreza and Rafiei, Davood},
  year={2023}
}
```

---

## 更新日志

- 2026-05-31: 创建基线代码集合
- 添加了7个主要基线方法
- 提供一键下载脚本

---

如有问题，请查看各仓库的GitHub Issues或联系维护者。
