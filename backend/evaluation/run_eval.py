"""
run_eval.py
Script đánh giá độ chính xác của LLM Intent Classifier
trên bộ 60 câu kiểm thử thực tế (nâng cao).

Chạy:
    python -m backend.evaluation.run_eval
    hoặc:
    python backend/evaluation/run_eval.py

Output:
  - Bảng kết quả chi tiết từng câu (in ra terminal)
  - Tóm tắt: Overall Accuracy, Per-category Accuracy, Avg latency
  - File CSV: backend/evaluation/results.csv (dùng cho báo cáo)
"""
import sys
import os
import time
import csv
from datetime import datetime

# Đảm bảo import được từ thư mục gốc
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))))

from backend.orchestrator.llm_classifier import classify_with_llm
from backend.evaluation.test_cases import TEST_CASES

# ──────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────

def _status_icon(correct: bool) -> str:
    return "✅" if correct else "❌"

def _pad(text: str, width: int) -> str:
    """Cắt hoặc pad chuỗi để canh cột Terminal."""
    text = str(text)
    if len(text) > width:
        return text[:width - 1] + "…"
    return text.ljust(width)

# ──────────────────────────────────────────────────────────
# CORE: Chạy từng test case
# ──────────────────────────────────────────────────────────

def run_evaluation() -> dict:
    """
    Chạy toàn bộ 25 test cases qua LLM Classifier.

    Returns:
        {
            "results":   list[dict],  # kết quả từng câu
            "summary":   dict,        # accuracy tổng và theo category
            "timestamp": str,
        }
    """
    results = []

    print("\n" + "="*80)
    print("  ĐÁNH GIÁ HỆ THỐNG CHATBOT ĐIỆN TỬ — LLM INTENT CLASSIFIER")
    print(f"  Thời gian chạy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Số test cases:  {len(TEST_CASES)}")
    print("="*80)

    # Header bảng
    print(f"\n{'ID':>3}  {'Câu hỏi':<42}  {'Expected':<9}  {'Got':<9}  {'Conf':<7}  {'OK':>3}  {'ms':>5}")
    print("-" * 80)

    for tc in TEST_CASES:
        query        = tc["query"]
        expected_int = tc["intent"]
        expected_sub = tc["sub_intent"]

        # Gọi LLM Classifier (không có conversation history để đo độc lập)
        t0 = time.time()
        result = classify_with_llm(query)
        latency_ms = int((time.time() - t0) * 1000)

        got_intent = result.get("intent",     "unknown")
        got_sub    = result.get("sub_intents", [])
        confidence = result.get("confidence", "?")

        intent_correct = (got_intent == expected_int)
        icon           = _status_icon(intent_correct)

        # In dòng kết quả
        print(
            f"{tc['id']:>3}  "
            f"{_pad(query, 42)}  "
            f"{_pad(expected_int, 9)}  "
            f"{_pad(got_intent, 9)}  "
            f"{_pad(confidence, 7)}  "
            f"{icon:>3}  "
            f"{latency_ms:>5}"
        )

        results.append({
            "id":              tc["id"],
            "query":           query,
            "expected_intent": expected_int,
            "expected_sub":    expected_sub,
            "got_intent":      got_intent,
            "got_sub":         ", ".join(got_sub) if got_sub else "",
            "got_hint":        result.get("product_hint") or "",
            "confidence":      confidence,
            "intent_correct":  intent_correct,
            "latency_ms":      latency_ms,
            "note":            tc.get("note", ""),
        })

    # ──────────────────────────────────────────────────────
    # TÍNH ACCURACY
    # ──────────────────────────────────────────────────────
    total   = len(results)
    correct = sum(1 for r in results if r["intent_correct"])
    avg_lat = sum(r["latency_ms"] for r in results) / total

    # Accuracy theo từng category
    categories = ["greeting", "tool", "hybrid", "rag", "unknown"]
    cat_stats = {}
    for cat in categories:
        cat_cases = [r for r in results if r["expected_intent"] == cat]
        if cat_cases:
            cat_correct = sum(1 for r in cat_cases if r["intent_correct"])
            cat_stats[cat] = {
                "total":    len(cat_cases),
                "correct":  cat_correct,
                "accuracy": cat_correct / len(cat_cases) * 100,
            }

    summary = {
        "total":          total,
        "correct":        correct,
        "accuracy":       correct / total * 100,
        "avg_latency_ms": avg_lat,
        "per_category":   cat_stats,
    }

    # ──────────────────────────────────────────────────────
    # IN SUMMARY
    # ──────────────────────────────────────────────────────
    print("\n" + "="*80)
    print("  KẾT QUẢ TỔNG HỢP")
    print("="*80)
    print(f"  Tổng số câu hỏi : {total}")
    print(f"  Phân loại đúng  : {correct}/{total}")
    print(f"  Độ chính xác    : {summary['accuracy']:.1f}%")
    print(f"  Thời gian TB    : {avg_lat:.0f} ms/câu")

    print("\n  Độ chính xác theo từng nhóm:")
    print(f"  {'Nhóm':<12}  {'Đúng/Tổng':<11}  {'Accuracy':>9}")
    print("  " + "-" * 36)
    for cat, stat in cat_stats.items():
        bar_len = int(stat["accuracy"] / 10)
        bar = "█" * bar_len + "░" * (10 - bar_len)
        print(
            f"  {cat:<12}  "
            f"{stat['correct']}/{stat['total']:<10}  "
            f"{stat['accuracy']:>6.1f}%  {bar}"
        )

    # Các câu bị phân loại sai
    wrong = [r for r in results if not r["intent_correct"]]
    if wrong:
        print(f"\n  ⚠️  {len(wrong)} câu phân loại SAI:")
        for r in wrong:
            print(f"    [{r['id']:02d}] \"{r['query']}\"")
            print(f"          Expected: {r['expected_intent']} → Got: {r['got_intent']}")
    else:
        print("\n  🎉 Tất cả câu đều được phân loại đúng!")

    print("="*80)

    return {
        "results":   results,
        "summary":   summary,
        "timestamp": datetime.now().isoformat(),
    }

# ──────────────────────────────────────────────────────────
# XUẤT CSV
# ──────────────────────────────────────────────────────────

def export_csv(eval_output: dict, output_path: str = None):
    """Xuất kết quả chi tiết ra file CSV để đưa vào báo cáo."""
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "results.csv"
        )

    fieldnames = [
        "id", "query", "expected_intent", "got_intent", "intent_correct",
        "confidence", "got_hint", "latency_ms", "note",
    ]

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in eval_output["results"]:
            row["intent_correct"] = "ĐÚNG" if row["intent_correct"] else "SAI"
            writer.writerow(row)

    # Thêm dòng summary ở cuối
    with open(output_path, "a", newline="", encoding="utf-8-sig") as f:
        f.write("\n")
        f.write(f"Tổng,,,,,,,{eval_output['summary']['accuracy']:.1f}%,,\n")

    print(f"\n  📄 Đã xuất CSV: {output_path}")
    return output_path


# ──────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    output = run_evaluation()
    export_csv(output)
