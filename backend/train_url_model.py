"""Retrain the URL classifier on normalised URLs plus bare-host samples.

Usage: python train_url_model.py [--no-save]

Splits by host so near-duplicate URLs of one site never straddle train/test,
then reports held-out metrics and a check on well-known bare domains.
"""
import argparse
import os
import pickle

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import GroupShuffleSplit
from sklearn.svm import LinearSVC

from services.url_features import host_of, normalize_url_for_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "ml_models")
HOST_SAMPLES_PER_CLASS = 60000
SEED = 42

KNOWN_GOOD = [
    "github.com", "https://github.com", "https://www.bbc.co.uk/news", "wikipedia.org",
    "https://en.wikipedia.org/wiki/Python", "https://www.google.com", "https://www.amazon.com/dp/B01",
    "stackoverflow.com", "https://www.linkedin.com/in/someone", "nytimes.com", "https://www.reddit.com/r/python",
    "https://www.microsoft.com/en-us", "apple.com", "https://www.youtube.com/watch?v=abc", "mozilla.org",
]


def build_frame():
    df = pd.read_csv(os.path.join(BASE_DIR, "data", "malicious_phish.csv")).dropna()
    df["url"] = df["url"].map(normalize_url_for_model)
    df = df[df["url"] != ""].drop_duplicates("url")
    df["host"] = df["url"].map(host_of)

    # Bare-host samples teach the model what a plain domain looks like. Skip
    # hosts seen under conflicting labels (e.g. a site with benign and malware pages).
    labels_per_host = df.groupby("host")["type"].nunique()
    clean_hosts = df[df["host"].isin(labels_per_host[labels_per_host == 1].index)]
    bare = (
        clean_hosts.drop_duplicates("host")
        .groupby("type", group_keys=False)
        .apply(lambda g: g.sample(min(len(g), HOST_SAMPLES_PER_CLASS), random_state=SEED))
    )
    bare = bare.assign(url=bare["host"])
    return pd.concat([df, bare], ignore_index=True).drop_duplicates("url")


def main(save):
    df = build_frame()
    print("rows:", len(df)); print(df["type"].value_counts())

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED)
    train_idx, test_idx = next(splitter.split(df, groups=df["host"]))
    train, test = df.iloc[train_idx], df.iloc[test_idx]

    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 5), max_features=10000)
    x_train = vectorizer.fit_transform(train["url"])
    model = CalibratedClassifierCV(LinearSVC(), cv=3).fit(x_train, train["type"])

    pred = model.predict(vectorizer.transform(test["url"]))
    print("\n== held-out, 4-class ==")
    print(classification_report(test["type"], pred, digits=3))

    is_bad = lambda s: (s != "benign").map({True: "MALICIOUS", False: "SAFE"})
    print("== held-out, binary ==")
    print(classification_report(is_bad(test["type"]), is_bad(pd.Series(pred, index=test.index)), digits=3))

    bare_test = test[test["url"] == test["host"]]
    print("bare-host held-out binary:")
    print(classification_report(is_bad(bare_test["type"]), is_bad(pd.Series(model.predict(vectorizer.transform(bare_test["url"])), index=bare_test.index)), digits=3))

    benign_col = list(model.classes_).index("benign")
    print("== well-known sites, P(malicious) ==")
    for url in KNOWN_GOOD:
        p = 1 - model.predict_proba(vectorizer.transform([normalize_url_for_model(url)]))[0][benign_col]
        print(f"{p*100:5.1f}%  {url}")

    if save:
        with open(os.path.join(MODEL_DIR, "url_ml_model.pkl"), "wb") as f:
            pickle.dump(model, f)
        with open(os.path.join(MODEL_DIR, "url_tfidf.pkl"), "wb") as f:
            pickle.dump(vectorizer, f)
        print("saved models")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-save", action="store_true")
    main(save=not parser.parse_args().no_save)
