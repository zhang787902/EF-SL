"""
用「修复后的评估器」重算 Spider 全量 1034 的正确性与显著性
==========================================================
背景：原 exp_5method_comparison.py 的 evaluate_sql 用 `sorted(pred)==sorted(gold)`，
当结果行含 None 与 str 混排时会抛 TypeError 被吞掉→恒判 False。这造成 Spider
主实验 ~1.3% 的假阴性（远小于 BIRD，但需纠正）。

本脚本：
1) 用集合比较 + None/float 规范化，逐条重算 5 方法的 correct 标志；
2) 写出修正版 results/exp_5method_results_fixed.json；
3) 重算配对 McNemar 精确检验 + bootstrap 95% CI。

用法：python code/fix_eval_and_significance.py
"""
import json
import os
import sqlite3
import numpy as np
from scipy.stats import binomtest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "code/spider_data/database")
SRC = os.path.join(BASE, "results/exp_5method_results.json")
OUT = os.path.join(BASE, "results/exp_5method_results_fixed.json")


def _nc(v):
    if v is None:
        return None
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def eval_fixed(pred, gold, db_id):
    p = os.path.join(DB, db_id, f"{db_id}.sqlite")
    if not os.path.exists(p):
        return False
    try:
        conn = sqlite3.connect(p)
        cur = conn.cursor()
        cur.execute(pred); P = cur.fetchall()
        cur.execute(gold); G = cur.fetchall()
        conn.close()
        return {tuple(_nc(c) for c in r) for r in P} == {tuple(_nc(c) for c in r) for r in G}
    except Exception:
        return False


def paired(baseline, other):
    b = {r["idx"]: r["correct"] for r in baseline}
    o = {r["idx"]: r["correct"] for r in other}
    ids = sorted(set(b) & set(o))
    fix = sum(1 for i in ids if not b[i] and o[i])
    brk = sum(1 for i in ids if b[i] and not o[i])
    both = sum(1 for i in ids if b[i] and o[i])
    wrong = sum(1 for i in ids if not b[i] and not o[i])
    return ids, fix, brk, both, wrong


def main():
    src = json.load(open(SRC, encoding="utf-8"))
    fixed = {}
    for method in ["baseline", "lexical_sl", "llm_sl", "upgraded_ef_sl", "oracle_sl"]:
        dets = src[method]["details"]
        new_dets = []
        for d in dets:
            nd = dict(d)
            nd["correct"] = eval_fixed(d["pred"], d["gold"], d["db_id"])
            new_dets.append(nd)
        n = len(new_dets)
        c = sum(1 for d in new_dets if d["correct"])
        fixed[method] = {"correct": c, "total": n, "accuracy": c / n * 100, "details": new_dets}
    json.dump(fixed, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"修正版已写入 {os.path.relpath(OUT, BASE)}")

    # 显著性报告
    baseline = fixed["baseline"]["details"]
    n = len(baseline)
    base_acc = sum(r["correct"] for r in baseline) / n * 100
    print(f"\nBaseline N={n}, accuracy={base_acc:.2f}%")
    print(f"{'方法':<16}{'准确率%':>9}{'Δpp':>8}{'Fixes':>7}{'Breaks':>8}{'Net':>6}{'McNemar p':>12}")
    for key, label in [("lexical_sl", "Lexical SL"), ("llm_sl", "LLM-SL"),
                       ("upgraded_ef_sl", "EF-SL (Ours)"), ("oracle_sl", "Oracle SL")]:
        other = fixed[key]["details"]
        acc = sum(r["correct"] for r in other) / n * 100
        ids, fix, brk, both, wrong = paired(baseline, other)
        m = fix + brk
        p = binomtest(min(fix, brk), m, 0.5, alternative="two-sided").pvalue if m else 1.0
        pstr = f"{p:.4f}" if p >= 1e-4 else f"{p:.2e}"
        sig = "" if p >= 0.05 else ("*" if p >= 0.01 else "**" if p >= 0.001 else "***")
        print(f"{label:<16}{acc:>9.2f}{acc-base_acc:>+8.2f}{fix:>7}{brk:>8}{fix-brk:>+6}{pstr:>12} {sig}")

    # bootstrap CI
    rng = np.random.default_rng(0)
    ids_all = [r["idx"] for r in baseline]
    ib = {r["idx"]: r["correct"] for r in baseline}
    print("\nBootstrap 95% CI (Δpp):")
    for key, label in [("lexical_sl", "Lexical SL"), ("llm_sl", "LLM-SL"),
                       ("upgraded_ef_sl", "EF-SL (Ours)"), ("oracle_sl", "Oracle SL")]:
        io = {r["idx"]: r["correct"] for r in fixed[key]["details"]}
        nb = np.array([ib[i] for i in ids_all], dtype=bool)
        no = np.array([io[i] for i in ids_all], dtype=bool)
        diffs = []
        for _ in range(10000):
            idx = rng.integers(0, len(ids_all), len(ids_all))
            diffs.append((no[idx].mean() - nb[idx].mean()) * 100)
        diffs = np.array(diffs)
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        print(f"  {label:<16} [{lo:+.2f}, {hi:+.2f}] mean={diffs.mean():+.2f}")


if __name__ == "__main__":
    main()