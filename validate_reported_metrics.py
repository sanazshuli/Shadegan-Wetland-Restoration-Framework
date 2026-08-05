"""Verify metrics reported for the restoration-strategy confusion matrix.

This script verifies the numerical values shown in the manuscript figure.
It does not reproduce model training and it is not an independent field validation.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "data" / "reported_restoration_confusion_matrix.csv"


def expand_labels(confusion: np.ndarray) -> tuple[list[int], list[int]]:
    """Expand a confusion matrix to paired actual/predicted label arrays."""
    actual: list[int] = []
    predicted: list[int] = []
    for actual_idx in range(confusion.shape[0]):
        for predicted_idx in range(confusion.shape[1]):
            count = int(confusion[actual_idx, predicted_idx])
            actual.extend([actual_idx] * count)
            predicted.extend([predicted_idx] * count)
    return actual, predicted


def main() -> int:
    if not MATRIX_PATH.exists():
        print(f"ERROR: Missing matrix file: {MATRIX_PATH}", file=sys.stderr)
        return 1

    frame = pd.read_csv(MATRIX_PATH, index_col=0)
    confusion = frame.to_numpy(dtype=int)

    if confusion.shape[0] != confusion.shape[1]:
        print("ERROR: Confusion matrix must be square.", file=sys.stderr)
        return 1

    total = int(confusion.sum())
    if total == 0:
        print("ERROR: Confusion matrix contains no samples.", file=sys.stderr)
        return 1

    accuracy = float(np.trace(confusion) / total)
    actual, predicted = expand_labels(confusion)
    kappa = float(cohen_kappa_score(actual, predicted))

    support = confusion.sum(axis=1)
    result = pd.DataFrame(
        {
            "class": frame.index,
            "validation_support": support,
        }
    )

    print("Reported restoration-strategy validation matrix")
    print(frame)
    print()
    print(f"Samples: {total}")
    print(f"Overall accuracy: {accuracy:.4f} ({accuracy * 100:.1f}%)")
    print(f"Cohen's Kappa: {kappa:.4f}")
    print()
    print("Class support")
    print(result.to_string(index=False))

    unsupported = result.loc[result["validation_support"] == 0, "class"].tolist()
    if unsupported:
        print()
        print(
            "WARNING: The following class(es) have zero validation support: "
            + ", ".join(unsupported)
        )
        print(
            "The reported metrics should not be interpreted as independent "
            "validation of all five strategy classes."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
