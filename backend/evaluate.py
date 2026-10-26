"""Evaluate the SMS and URL detectors against the datasets in data/.

Usage: python evaluate.py [--url-sample N] [--seed S]

Note: the shipped models were trained on these same datasets, so scores here
are optimistic. Use a held-out set for an honest generalisation estimate.
"""
import argparse
import csv
import os
import random

from sklearn.metrics import classification_report, confusion_matrix

from services.detection import fusion_engine, sms_model, sms_vectorizer

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MALICIOUS_TYPES = {"phishing", "malware", "defacement"}


def evaluate_sms():
    rows = [line.rstrip("\n").split("\t", 1) for line in open(os.path.join(DATA_DIR, "sms_spam"), encoding="utf-8", errors="ignore") if "\t" in line]
    texts = [text for _, text in rows]
    truth = ["MALICIOUS" if label == "spam" else "SAFE" for label, _ in rows]
    raw = sms_model.predict(sms_vectorizer.transform(texts))
    pred = ["MALICIOUS" if str(p).lower() in {"spam", "1", "malicious"} else "SAFE" for p in raw]
    print(f"== SMS ({len(rows)} messages) ==")
    print(classification_report(truth, pred, digits=3))
    print(confusion_matrix(truth, pred, labels=["SAFE", "MALICIOUS"]))


def evaluate_urls(sample, seed):
    with open(os.path.join(DATA_DIR, "malicious_phish.csv"), encoding="utf-8", errors="ignore") as handle:
        rows = list(csv.DictReader(handle))
    random.Random(seed).shuffle(rows)
    rows = rows[:sample]
    truth = ["MALICIOUS" if row["type"] in MALICIOUS_TYPES else "SAFE" for row in rows]
    pred = [fusion_engine(row["url"])["label"] for row in rows]
    print(f"\n== URL fusion engine ({len(rows)} sampled URLs) ==")
    print(classification_report(truth, pred, digits=3))
    print(confusion_matrix(truth, pred, labels=["SAFE", "MALICIOUS"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url-sample", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    evaluate_sms()
    evaluate_urls(args.url_sample, args.seed)
