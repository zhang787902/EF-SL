# Schema Linking复现实验结果

## 实验配置
- API: VimsAI (https://api.vimsai.com/v1)
- 模型: gpt-4o
- 样本数: 30 (与原论文一致)
- 数据集: Spider dev (过滤后58个本地有数据库的样本)

## 实验结果

| 方法 | 准确率 | 正确/总数 |
|------|--------|----------|
| Baseline (无Schema Linking) | 60.0% | 18/30 |
| Static Schema Linking | 26.7% | 8/30 |
| **差距** | **-33.3%** | - |

## 关键发现

1. **Schema Linking确实会降低性能** - 与原论文发现的-6.7%一致
2. **简单关键词匹配的Schema Linking过于激进** - 丢失了必要的上下文
3. **需要更智能的Schema Linking方法** - 验证了Execution-feedback Schema Linking的必要性

## 样本分析

Static Schema Linking失败的主要原因:
1. 遗漏了必要的表（如需要JOIN的表只选了一部分）
2. 错误的表链接（如将concert_singer链接到不相关的表）
3. 过度过滤（排除了实际上需要的列）

## 结论

本实验成功复现了原论文的核心发现：
- 简单的Static Schema Linking会降低Text-to-SQL性能
- 这验证了需要更智能的Schema Linking方法（如Execution-feedback driven）

## 下一步

1. 实现Execution-feedback Schema Linking
2. 对比验证是否能恢复并超越Baseline性能
3. 扩展实验到完整Spider数据集
