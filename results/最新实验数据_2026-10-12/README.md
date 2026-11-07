# 最新实验数据（2026-10-12 最终版）

本文件夹存放 EF-SL 论文的**最新、已修正**的实验数据、代码、图、表，与项目目录中混杂的旧 bug 数据物理隔离。

> ⚠️ 项目目录（`OneDrive\Desktop\EF-SL_Execution_Feedback_Schema_Linking`）中仍存在旧数据文件（如 `*_buggy_backup.json`、`exp_5method_results.json` 旧版、`exp_bird_progress_buggy_backup.json` 等），**请勿使用**，以本文件夹为准。

## 目录结构

```
最新实验数据_2026-10-12/
├── 修改清单.md              ← 核心交付物：对照 EF-SL2.docx 的逐项修改清单
├── data/                    ← 权威结果 JSON
│   ├── exp_5method_results_fixed.json       Spider 修正后（N=1034，基线 68.76%）
│   ├── exp_5method_results_fixed_eval.json  Spider 新旧对比汇总
│   ├── exp_bird_results.json                BIRD 重做（N=1534，基线 51.24%）
│   ├── exp_cross_model_deepseek-v4-pro.json 跨模型：DeepSeek（N=400）
│   ├── exp_cross_model_glm-5.3.json         跨模型：GLM-5.3（N=400）
│   └── gpt4o_400_ref.json                   GPT-4o 同 400 样本对照
├── code/                    ← 关键脚本
│   ├── exp_5method_comparison.py      五方法对比实验
│   ├── exp_bird_5method.py            BIRD 重做实验
│   ├── exp_cross_model.py             跨模型实验
│   ├── fix_eval_and_significance.py   评估器 bug 修复 + McNemar 重算
│   ├── significance_test.py           显著性检验
│   ├── update_paper_spider_numbers.py 更新论文数字
│   ├── generate_all_figures_tables.py 原始绘图脚本（数据源为旧版）
│   └── generate_figures_tables_new.py 已改数据源的绘图脚本（本次用的）
├── figures/                 ← 重新生成的图（新数据，PNG + PDF）
│   ├── fig1_main_results.png/pdf           主结果
│   ├── fig2_difficulty_stratified.png/pdf  难度分层
│   ├── fig3_sl_damage_gradient.png/pdf     损害梯度
│   ├── fig4_dual_effect.png/pdf            双重效应 Fixes/Breaks
│   ├── fig5_efsl_iterations.png/pdf        迭代效率（数据不变）
│   ├── fig6_difficulty_heatmap.png/pdf     难度热力
│   ├── fig7_cross_dataset_comparison.png/pdf 跨数据集
│   └── fig8_paradigm_comparison.png/pdf    范式对比（非数据图）
└── tables/                  ← LaTeX 表格（已修正为权威数据）
    ├── table1_main_results.tex       主结果
    ├── table2_difficulty_spider.tex  难度分层
    ├── table3_fixes_breaks.tex       Fixes/Breaks
    ├── table4_cross_dataset.tex      跨数据集
    └── table5_method_comparison.tex  方法对比（无实验数据）
```

## 核心数据速览

### Spider Dev（N=1,034，修正后）
| Method | Acc. | Δ |
|---|---|---|
| Baseline | 68.76% | — |
| Lexical SL | 63.64% | −5.13 |
| LLM-SL | 65.67% | −3.09 |
| **EF-SL** | **69.05%** | **+0.29** (p=0.711) |
| Oracle SL | 72.82% | +4.06 |

### BIRD Dev（N=1,534，重做后）
| Method | Acc. | Δ |
|---|---|---|
| Baseline | 51.24% | — |
| Lexical SL | 45.50% | −5.74 |
| LLM-SL | 47.65% | −3.59 |
| **EF-SL** | **54.24%** | **+3.00** (p=3.3×10⁻⁷) |
| Oracle SL | 54.95% | +3.72 |

### 跨模型（Spider Dev 前 400 条，Δ vs 各自 Baseline）
| Method | GPT-4o | DeepSeek | GLM-5.3 |
|---|---|---|---|
| Lexical SL | −5.50 | −10.50 | −11.00 |
| LLM-SL | −6.25 | −3.25 | −0.75 |
| EF-SL | −0.75 (n.s.) | −3.50 (p=0.054) | −3.75 (p=0.067) |
| Oracle SL | +6.00 | +4.75 | +3.75 |

## 与旧版的三点关键差异

1. **Spider 微调**：评估器 NULL 排序 bug 修复后，基线 67.50% → 68.76%。
2. **BIRD 推翻**：原 1.04% 是 bug 假象，重做后 51.24%；EF-SL 从"无显著差异(+0.13% n.s.)"变为"**显著增益 +3.00%**"。
3. **新增跨模型验证**：预过滤损害跨模型稳健，但 EF-SL「安全」为 GPT-4o 特有。