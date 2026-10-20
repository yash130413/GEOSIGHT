"""Metric maths used by Training/evaluate_models.py."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Training"))
from evaluate_models import metrics_from_confusion  # noqa: E402


def test_metrics_from_confusion_matches_hand_calculation():
    # rows = truth, cols = prediction
    cm = np.array([[8, 2],
                   [1, 9]])
    m = metrics_from_confusion(cm, ["Non-Road", "Road"])
    road = m["per_class"]["Road"]
    assert road["precision"] == pytest.approx(9 / 11 * 100, abs=0.01)
    assert road["recall"] == pytest.approx(9 / 10 * 100, abs=0.01)
    assert road["iou"] == pytest.approx(9 / 12 * 100, abs=0.01)
    assert m["pixel_accuracy"] == pytest.approx(17 / 20 * 100, abs=0.01)


def test_class_with_no_pixels_does_not_crash():
    cm = np.array([[5, 0], [0, 0]])
    m = metrics_from_confusion(cm, ["A", "B"])
    assert m["per_class"]["B"]["precision"] == 0.0
