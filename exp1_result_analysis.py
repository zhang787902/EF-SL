"""
实验1结果分析脚本
用于深入分析Schema Linking实验结果
"""

import json
from collections import defaultdict
import matplotlib.pyplot as plt


class ExperimentAnalyzer:
    """实验结果分析器"""

    def __init__(self, results_path: str):
        with open(results_path, 'r') as f:
            self.results = json.load(f)

    def basic_stats(self):
        """基础统计"""
        print("="*60)
        print("基础统计")
        print("="*60)

        for mode in ["baseline", "static_sl"]:
            data = self.results[mode]
            correct = data['correct']
            total = data['total']
            accuracy = correct / total if total > 0 else 0

            print(f"\n{mode.upper()}:")
            print(f"  正确数: {correct}/{total}")
            print(f"  准确率: {accuracy:.1%}")

        base_acc = self.results['baseline']['correct'] / self.results['baseline']['total']
        sl_acc = self.results['static_sl']['correct'] / self.results['static_sl']['total']
        diff = sl_acc - base_acc

        print(f"\n关键发现:")
        print(f"  准确率差异: {diff:+.1%}")
        if diff < -0.05:
            print(f"  ✓ 成功复现原论文发现 (Schema Linking降低性能)")
        elif diff > 0.05:
            print(f"  ✗ Schema Linking提升了性能 (与原论文不同)")
        else:
            print(f"  ~ 效果不明显 (差异<5%)")

    def error_analysis(self):
        """错误分析"""
        print("\n" + "="*60)
        print("错误模式分析")
        print("="*60)

        # 对比baseline正确但SL错误的样本
        baseline_details = self.results['baseline']['details']
        sl_details = self.results['static_sl']['details']

        degradation_cases = []
        for i, (base, sl) in enumerate(zip(baseline_details, sl_details)):
            if base['correct'] and not sl['correct']:
                degradation_cases.append({
                    'index': i,
                    'question': base['question'],
                    'gold': base['gold'],
                    'baseline_pred': base['pred'],
                    'sl_pred': sl['pred'],
                    'linked_tables': sl.get('linked_tables', [])
                })

        print(f"\n性能退化案例数: {len(degradation_cases)}")

        if degradation_cases:
            print("\n典型退化案例 (前3个):")
            for case in degradation_cases[:3]:
                print(f"\n  问题: {case['question']}")
                print(f"  链接的表: {case['linked_tables']}")
                print(f"  Baseline预测: {case['baseline_pred'][:80]}...")
                print(f"  SL预测: {case['sl_pred'][:80]}...")

        # 对比baseline错误但SL正确的样本
        improvement_cases = []
        for i, (base, sl) in enumerate(zip(baseline_details, sl_details)):
            if not base['correct'] and sl['correct']:
                improvement_cases.append({
                    'index': i,
                    'question': base['question']
                })

        print(f"\n性能提升案例数: {len(improvement_cases)}")

    def table_linking_analysis(self):
        """表链接分析"""
        print("\n" + "="*60)
        print("Schema Linking质量分析")
        print("="*60)

        sl_details = self.results['static_sl']['details']

        # 统计链接表数量分布
        table_counts = defaultdict(int)
        for detail in sl_details:
            tables = detail.get('linked_tables', [])
            table_counts[len(tables)] += 1

        print("\n链接表数量分布:")
        for count, freq in sorted(table_counts.items()):
            print(f"  {count}个表: {freq}次 ({freq/len(sl_details):.1%})")

        # 分析链接表数量与准确率的关系
        print("\n链接表数量 vs 准确率:")
        for num_tables in sorted(table_counts.keys()):
            cases = [d for d in sl_details if len(d.get('linked_tables', [])) == num_tables]
            if cases:
                acc = sum(d['correct'] for d in cases) / len(cases)
                print(f"  {num_tables}个表: {acc:.1%} ({sum(d['correct'] for d in cases)}/{len(cases)})")

    def generate_report(self):
        """生成完整报告"""
        print("\n" + "="*60)
        print("实验1完整分析报告")
        print("="*60)

        self.basic_stats()
        self.error_analysis()
        self.table_linking_analysis()

        # 与原论文对比
        print("\n" + "="*60)
        print("与原论文对比")
        print("="*60)

        base_acc = self.results['baseline']['correct'] / self.results['baseline']['total']
        sl_acc = self.results['static_sl']['correct'] / self.results['static_sl']['total']
        diff = sl_acc - base_acc

        print(f"\n原论文报告:")
        print(f"  Baseline: 28.0%")
        print(f"  Static SL: 21.3%")
        print(f"  差异: -6.7%")

        print(f"\n本实验结果:")
        print(f"  Baseline: {base_acc:.1%}")
        print(f"  Static SL: {sl_acc:.1%}")
        print(f"  差异: {diff:+.1%}")

        diff_from_paper = abs(diff - (-0.067))
        print(f"\n与原论文差异: {diff_from_paper:.1%}")

        if diff_from_paper < 0.03:
            print("  ✓ 高度一致 (<3%)")
        elif diff_from_paper < 0.05:
            print("  ~ 基本一致 (<5%)")
        else:
            print("  ⚠ 差异较大 (>5%)")

    def visualize_results(self, save_path: str = "exp1_visualization.png"):
        """可视化结果"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # 1. 准确率对比柱状图
        ax1 = axes[0, 0]
        modes = ['Baseline', 'Static SL']
        base_acc = self.results['baseline']['correct'] / self.results['baseline']['total']
        sl_acc = self.results['static_sl']['correct'] / self.results['static_sl']['total']
        accs = [base_acc, sl_acc]

        bars = ax1.bar(modes, accs, color=['#3498db', '#e74c3c'])
        ax1.set_ylabel('Accuracy')
        ax1.set_title('Schema Linking Effect')
        ax1.set_ylim([0, max(accs) * 1.2])

        # 添加数值标签
        for bar, acc in zip(bars, accs):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{acc:.1%}',
                    ha='center', va='bottom')

        # 2. 正确/错误饼图
        ax2 = axes[0, 1]
        total_correct = self.results['baseline']['correct']
        total_wrong = self.results['baseline']['total'] - total_correct
        ax2.pie([total_correct, total_wrong],
                labels=['Correct', 'Wrong'],
                autopct='%1.1f%%',
                colors=['#2ecc71', '#e74c3c'])
        ax2.set_title('Baseline Performance')

        # 3. 混淆矩阵样式对比
        ax3 = axes[1, 0]
        baseline_details = self.results['baseline']['details']
        sl_details = self.results['static_sl']['details']

        both_correct = sum(1 for b, s in zip(baseline_details, sl_details) if b['correct'] and s['correct'])
        both_wrong = sum(1 for b, s in zip(baseline_details, sl_details) if not b['correct'] and not s['correct'])
        base_correct_sl_wrong = sum(1 for b, s in zip(baseline_details, sl_details) if b['correct'] and not s['correct'])
        base_wrong_sl_correct = sum(1 for b, s in zip(baseline_details, sl_details) if not b['correct'] and s['correct'])

        categories = ['Both\nCorrect', 'Both\nWrong', 'Base✓\nSL✗', 'Base✗\nSL✓']
        values = [both_correct, both_wrong, base_correct_sl_wrong, base_wrong_sl_correct]
        colors = ['#2ecc71', '#95a5a6', '#e74c3c', '#3498db']

        bars = ax3.bar(categories, values, color=colors)
        ax3.set_ylabel('Count')
        ax3.set_title('Performance Comparison')

        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val}',
                    ha='center', va='bottom')

        # 4. 差异分析
        ax4 = axes[1, 1]
        diff = sl_acc - base_acc
        colors_diff = ['#e74c3c' if diff < 0 else '#2ecc71']
        bars = ax4.bar(['Accuracy\nDifference'], [abs(diff)], color=colors_diff)
        ax4.set_ylabel('Difference')
        ax4.set_title(f'SL Effect: {diff:+.1%}')
        ax4.axhline(y=0.067, color='gray', linestyle='--', label='Paper: -6.7%')
        ax4.legend()

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"\n可视化结果已保存: {save_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python exp1_result_analysis.py <results.json>")
        print("Example: python exp1_result_analysis.py exp1_results.json")
        sys.exit(1)

    results_path = sys.argv[1]

    # 创建分析器
    analyzer = ExperimentAnalyzer(results_path)

    # 生成报告
    analyzer.generate_report()

    # 生成可视化（如果安装了matplotlib）
    try:
        analyzer.visualize_results()
    except ImportError:
        print("\n注意: 未安装matplotlib，跳过可视化")
        print("安装命令: pip install matplotlib")
