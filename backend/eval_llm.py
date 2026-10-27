"""Compare ML-only, LLM+RAG-only and fused detection on a random SMS sample.

Usage: python eval_llm.py [--n 60] [--seed 7]
Needs Ollama running locally. The SMS model was trained on this dataset, so ML
numbers are optimistic; the LLM never saw it.
"""
import argparse
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.detection import sms_model, sms_vectorizer
from services.llm_detector import llm_assess, llm_scam_probability
from services.rag_service import retrieve_context

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sms_spam")


def metrics(name, truth, pred):
    tp = sum(t and p for t, p in zip(truth, pred)); fp = sum((not t) and p for t, p in zip(truth, pred))
    fn = sum(t and (not p) for t, p in zip(truth, pred)); tn = len(truth) - tp - fp - fn
    prec = tp / (tp + fp) if tp + fp else 0; rec = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
    print(f"{name:34s} acc={(tp+tn)/len(truth):.3f} prec={prec:.3f} recall={rec:.3f} f1={f1:.3f}  (FP={fp} FN={fn})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=60); ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rows = [l.rstrip("\n").split("\t", 1) for l in open(DATA, encoding="utf-8", errors="ignore") if "\t" in l]
    rnd = random.Random(args.seed)
    spam = rnd.sample([r for r in rows if r[0] == "spam"], args.n // 2)
    ham = rnd.sample([r for r in rows if r[0] == "ham"], args.n - args.n // 2)
    sample = spam + ham; rnd.shuffle(sample)

    truth, ml, llm, failed, t0 = [], [], [], 0, time.time()
    for label, text in sample:
        ml_p = float(sms_model.predict_proba(sms_vectorizer.transform([text]))[0][1]) * 100
        a = llm_assess(text, context=retrieve_context(text, k=3), signals={"ml_scam_probability": round(ml_p)})
        if a is None:
            failed += 1; continue
        truth.append(label == "spam"); ml.append(ml_p); llm.append(llm_scam_probability(a))
    print(f"{len(truth)} scored, {failed} LLM failures, {(time.time()-t0)/max(1,len(sample)):.1f}s per message\n")

    metrics("ML only (>=50)", truth, [p >= 50 for p in ml])
    metrics("LLM+RAG only (>=50)", truth, [p >= 50 for p in llm])
    for w in (0.3, 0.5, 0.7):
        metrics(f"weighted {w:.1f} ML + {1-w:.1f} LLM (>=50)", truth, [w * m + (1 - w) * l >= 50 for m, l in zip(ml, llm)])
    metrics("max(ML, LLM) (>=50)", truth, [max(m, l) >= 50 for m, l in zip(ml, llm)])
