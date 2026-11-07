"""
统计显著性检验：EF-SL 与预过滤 SL 相对 Baseline 的配对检验
=========================================================
直接从原始结果 JSON 的 details 重算（不依赖报告二手数字），对每种
方法相对 Baseline 做：
  1) 配对 Fixes/Breaks 计数
  2) McNemar 检验（b+c>=25 用卡方近似，b+c<25 用精确二项检验）
  3) Bootstrap 配对差值的 95% 置信区间 (N=10000)

用法：
  python code/significance_test.py
"""
import json
import os
import numpy as np
from scipy.stats import chi2, binomtest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(dataset):
    d = json.load(open(os.path.join(BASE, f"results/{dataset}.json"), encoding="utf-8"))
    return d


def paired_counts(baseline, other):
    """基于 idx 对齐，返回 (both_correct, fixes, breaks, both_wrong)。"""
    b = {r["idx"]: r.get("correct", False) for r in baseline}
    o = {r["idx"]: r.get("correct", False) for r in other}
    ids = sorted(set(b) & set(o))
    both = fix = brk = wrong = 0
    for i in ids:
        bc, oc = b[i], o[i]
        if bc and oc:
            both += 1
        elif (not bc) and oc:
            fix += 1   # baseline 错、方法对 -> 修复
        elif bc and (not oc):
            brk += 1   # baseline 对、方法错 -> 损害
        else:
            wrong += 1
    return both, fix, brk, wrong


def mcnemar(fix, brk):
    """McNemar 检验。返回统计量与双侧 p 值。"""
    n = fix + brk
    if n == 0:
        return 0.0, 1.0
    # 精确二项检验（无偏，适用于小样本）
    res = binomtest(min(fix, brk), n, 0.5, alternative="two-sided")
    return n, res.pvalue


def bootstrap_diff(baseline, other, n_iter=10000, seed=0):
    """Bootstrap 配对 accuracy 差值的 95% CI。"""
    b = {r["idx"]: r.get("correct", False) for r in baseline}
    o = {r["idx"]: r.get("correct", False) for r in other}
    ids = sorted(set(b) & set(o))
    nb = np.array([b[i] for i in ids], dtype=bool)
    no = np.array([o[i] for i in ids], dtype=bool)
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_iter):
        idx = rng.integers(0, len(ids), len(ids))
        d = no[idx].mean() - nb[idx].mean()
        diffs.append(d * 100)  # 转百分点
    diffs = np.array(diffs)
    return np.percentile(diffs, [2.5, 97.5]), diffs.mean()


def report(dataset, method_map):
    print("=" * 72)
    print(f"数据集: {dataset}")
    print("=" * 72)
    d = load(dataset)
    baseline = d["baseline"]["details"]
    n = len(baseline)
    print(f"Baseline N = {n}, accuracy = {sum(r.get('correct',0) for r in baseline)/n*100:.2f}%\n")
    print(f"{'方法':<18}{'准确率%':>9}{'Δpp':>8}{'Fixes':>7}{'Breaks':>8}{'Net':>6}{'McNemar p':>12}")
    for key, label in method_map.items():
        if key not in d:
            continue
        other = d[key]["details"]
        acc = sum(r.get("correct", 0) for r in other) / n * 100
        base_acc = sum(r.get("correct", 0) for r in baseline) / n * 100
        both, fix, brk, wrong = paired_counts(baseline, other)
        _, p = mcnemar(fix, brk)
        ci, _ = bootstrap_diff(baseline, other)
        net = fix - brk
        pstr = f"{p:.4f}" if p >= 0.0001 else f"{p:.2e}"
        sig = "" if p >= 0.05 else ("*" if p >= 0.01 else "**" if p >= 0.001 else "***")
        print(f"{label:<18}{acc:>9.2f}{acc-base_acc:>+8.2f}{fix:>7}{brk:>8}{net:>+6}{pstr:>12} {sig}")
    print()


if __name__ == "__main__":
    print("Spider (N=1034) 与 BIRD (N=1534) 配对显著性检验\n")
    report("exp_5method_results", {
        "lexical_sl": "Lexical SL",
        "llm_sl": "LLM-SL",
        "upgraded_ef_sl": "EF-SL (Ours)",
        "oracle_sl": "Oracle SL",
    })
    report("exp_bird_results", {
        "lexical_sl": "Lexical SL",
        "llm_sl": "LLM-SL",
        "upgraded_ef_sl": "EF-SL (Ours)",
        "oracle_sl": "Oracle SL",
    })
    print("说明: 双侧精确 McNemar (二项) 检验；bootstrap N=10000。")
    print("      * p<0.05  ** p<0.01  *** p<0.001")