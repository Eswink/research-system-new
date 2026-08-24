"""M12 Reference Research 实验代码（真实容器内执行）。

实验：低资源文本分类对比 — baseline(TF-IDF) vs candidate(hash-embedding)，
两者都接 LogisticRegression 风格线性分类器。

设计约束（M12 Scope / SA-1R 供应链纪律）：
- 纯 Python 标准库实现，无第三方依赖（sandbox 镜像 python:3.12-slim
  不含 scikit-learn；不引入未 pin 的 package install）；
- 输入数据在实验代码内确定性生成（可复现种子；20 类新闻语料子集模拟），
  benchmark leakage 由固定 train/test 划分避免（seed 固定切分，candidate
  与 baseline 共用同一划分）；
- 输出 `experiment_result.json`（对齐 experiment_run_output_v1 schema），
  同时输出 baseline/candidate 双分支 metrics，供 Before/After 对比。
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import time
from collections import Counter

# ---------------------------------------------------------------------------
# 1. 数据：确定性生成的低资源文本分类语料（20 类子集，每类 25 训练 + 10 测试）
# ---------------------------------------------------------------------------


def _make_vocab(seed: int, size: int) -> list[str]:
    rng = random.Random(seed)
    words: set[str] = set()
    while len(words) < size:
        word = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(4, 10)))
        words.add(word)
    return sorted(words)


def _make_class_words(seed: int, n_words: int) -> list[str]:
    rng = random.Random(seed)
    words: set[str] = set()
    while len(words) < n_words:
        word = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(4, 10)))
        words.add(word)
    return sorted(words)


def _make_doc(rng: random.Random, vocab: list[str], n_words: int) -> list[str]:
    return [rng.choice(vocab) for _ in range(n_words)]


def build_dataset(
    seed: int = 7,
    n_classes: int = 20,
    train_per_class: int = 25,
    test_per_class: int = 10,
):
    shared = _make_vocab(seed, 150)
    class_words = [_make_class_words(seed + 500 + label, 20) for label in range(n_classes)]
    docs: list[tuple[str, int]] = []
    for label in range(n_classes):
        class_rng = random.Random(seed + label)
        class_pool = class_words[label] + shared
        for _ in range(train_per_class):
            docs.append((" ".join(_make_doc(class_rng, class_pool, 30)), label))
    for label in range(n_classes):
        class_rng = random.Random(seed + 1000 + label)
        class_pool = class_words[label] + shared
        for _ in range(test_per_class):
            docs.append((" ".join(_make_doc(class_rng, class_pool, 30)), label))
    train = docs[: n_classes * train_per_class]
    test = docs[n_classes * train_per_class :]
    return train, test


# ---------------------------------------------------------------------------
# 2. 特征表示：TF-IDF（bag-of-words 加 IDF 权重）与 hash-embedding（固定维）
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    return text.split()


def tfidf_features(docs: list[tuple[str, int]], vocab_size: int = 1024) -> list[list[float]]:
    """确定性 TF-IDF：词 hash 到固定桶，IDF 用 log((1+N)/(1+df))+1。"""
    n = len(docs)
    df: Counter[str] = Counter()
    tokenized = [_tokenize(text) for text, _ in docs]
    for tokens in tokenized:
        for word in set(tokens):
            df[word] += 1
    idf: dict[str, float] = {}
    for word, count in df.items():
        idf[word] = math.log((1 + n) / (1 + count)) + 1
    features: list[list[float]] = []
    for tokens in tokenized:
        tf = Counter(tokens)
        total = sum(tf.values()) or 1
        vector = [0.0] * vocab_size
        for word, count in tf.items():
            bucket = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16) % vocab_size
            vector[bucket] += (count / total) * idf.get(word, 0.0)
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        features.append([v / norm for v in vector])
    return features


def hash_embedding_features(docs: list[tuple[str, int]], dim: int = 256) -> list[list[float]]:
    """确定性 hash-embedding：word 双 hash 符号哈希累加，L2 归一化。"""
    features: list[list[float]] = []
    for text, _ in docs:
        vector = [0.0] * dim
        for word in _tokenize(text):
            h1 = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            sign = 1 if h1 % 2 == 0 else -1
            bucket = h1 % dim
            vector[bucket] += sign
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        features.append([v / norm for v in vector])
    return features


# ---------------------------------------------------------------------------
# 3. 分类器：线性 Softmax 训练（确定性梯度，固定 seed）与预测
# ---------------------------------------------------------------------------


class LinearSoftmax:
    """确定性线性分类器：SGD 固定 seed + 固定轮数，无第三方依赖。"""

    def __init__(
        self,
        n_features: int,
        n_classes: int,
        seed: int,
        lr: float = 0.3,
        epochs: int = 12,
    ):
        rng = random.Random(seed)
        self.w = [[rng.gauss(0, 0.01) for _ in range(n_features)] for _ in range(n_classes)]
        self.lr = lr
        self.epochs = epochs

    def fit(self, x: list[list[float]], y: list[int]) -> None:
        n = len(x)
        for _ in range(self.epochs):
            for i in range(n):
                scores = [sum(wj * xj for wj, xj in zip(row, x[i])) for row in self.w]
                m = max(scores)
                exp = [math.exp(s - m) for s in scores]
                total = sum(exp)
                probs = [e / total for e in exp]
                for c in range(len(self.w)):
                    scale = probs[c] - (1 if c == y[i] else 0)
                    for j in range(len(self.w[c])):
                        self.w[c][j] -= self.lr * scale * x[i][j]

    def predict(self, x: list[float]) -> int:
        scores = [sum(wj * xj for wj, xj in zip(row, x)) for row in self.w]
        return max(range(len(scores)), key=lambda c: scores[c])


def evaluate(model: LinearSoftmax, x: list[list[float]], y: list[int]) -> dict[str, float]:
    correct = sum(1 for xi, yi in zip(x, y) if model.predict(xi) == yi)
    return {"accuracy": correct / len(y), "n_test": len(y)}


# ---------------------------------------------------------------------------
# 4. 主流程：双分支对照实验，输出 experiment_result.json
# ---------------------------------------------------------------------------


def main() -> None:
    seed = 7
    train, test = build_dataset(seed=seed)
    y_train = [label for _, label in train]
    y_test = [label for _, label in test]

    results: dict[str, object] = {}

    # baseline: TF-IDF + LinearSoftmax
    start = time.monotonic()
    x_train_tf = tfidf_features(train)
    x_test_tf = tfidf_features(test)
    tf_time = time.monotonic() - start
    model_tf = LinearSoftmax(len(x_train_tf[0]), 20, seed=seed)
    model_tf.fit(x_train_tf, y_train)
    tf_metrics = evaluate(model_tf, x_test_tf, y_test)
    results["baseline"] = {
        "method": "tfidf+linear_softmax",
        "metrics": tf_metrics,
        "feature_time_s": round(tf_time, 4),
        "n_features": len(x_train_tf[0]),
    }

    # candidate: hash-embedding + LinearSoftmax
    start = time.monotonic()
    x_train_emb = hash_embedding_features(train)
    x_test_emb = hash_embedding_features(test)
    emb_time = time.monotonic() - start
    model_emb = LinearSoftmax(len(x_train_emb[0]), 20, seed=seed)
    model_emb.fit(x_train_emb, y_train)
    emb_metrics = evaluate(model_emb, x_test_emb, y_test)
    results["candidate"] = {
        "method": "hash_embedding+linear_softmax",
        "metrics": emb_metrics,
        "feature_time_s": round(emb_time, 4),
        "n_features": len(x_train_emb[0]),
    }

    payload = {
        "experiment_run_id": os.environ.get("EXPERIMENT_RUN_ID", "M12-REFERENCE-RUN"),
        "status": "SUCCEEDED",
        "artifact_refs": ["experiment_result.json"],
        "metrics": {
            "baseline_accuracy": results["baseline"]["metrics"]["accuracy"],
            "candidate_accuracy": results["candidate"]["metrics"]["accuracy"],
            "baseline_feature_time_s": results["baseline"]["feature_time_s"],
            "candidate_feature_time_s": results["candidate"]["feature_time_s"],
            "n_train": len(train),
            "n_test": len(test),
        },
        "results": results,
        "seed": seed,
    }
    with open("experiment_result.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, sort_keys=True)
    print("baseline_accuracy=", results["baseline"]["metrics"]["accuracy"])
    print("candidate_accuracy=", results["candidate"]["metrics"]["accuracy"])


if __name__ == "__main__":
    main()
