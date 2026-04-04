import pytest
import pandas as pd

from ml.train_model import split_chronologically


# ── helpers ──────────────────────────────────────────────────────────────────


def make_frame(n: int) -> pd.DataFrame:
    return pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=n),
        "value": range(n),
    })


# ── split_chronologically ────────────────────────────────────────────────────


def test_split_default_ratio():
    train, test = split_chronologically(make_frame(10))
    assert len(train) == 8
    assert len(test) == 2


def test_split_custom_test_size():
    train, test = split_chronologically(make_frame(10), test_size=0.3)
    assert len(train) == 7
    assert len(test) == 3


def test_split_preserves_all_rows():
    frame = make_frame(20)
    train, test = split_chronologically(frame)
    assert len(train) + len(test) == 20


def test_split_train_rows_come_before_test_rows():
    """Chronological split: all training values must precede test values."""
    frame = make_frame(10)
    train, test = split_chronologically(frame)
    assert train["value"].max() < test["value"].min()


def test_split_exactly_two_rows():
    train, test = split_chronologically(make_frame(2))
    assert len(train) == 1
    assert len(test) == 1


def test_split_large_frame():
    train, test = split_chronologically(make_frame(100))
    assert len(train) == 80
    assert len(test) == 20


def test_split_returns_independent_copies():
    """Mutating the original frame should not affect the returned splits."""
    frame = make_frame(10)
    train, test = split_chronologically(frame)
    original_first = train["value"].iloc[0]
    frame["value"] = -1
    assert train["value"].iloc[0] == original_first


def test_split_invalid_test_size_zero_raises():
    with pytest.raises(ValueError, match="test_size"):
        split_chronologically(make_frame(10), test_size=0)


def test_split_invalid_test_size_one_raises():
    with pytest.raises(ValueError, match="test_size"):
        split_chronologically(make_frame(10), test_size=1)


def test_split_invalid_test_size_negative_raises():
    with pytest.raises(ValueError, match="test_size"):
        split_chronologically(make_frame(10), test_size=-0.1)


def test_split_invalid_test_size_greater_than_one_raises():
    with pytest.raises(ValueError, match="test_size"):
        split_chronologically(make_frame(10), test_size=1.5)


def test_split_fewer_than_two_rows_raises():
    with pytest.raises(ValueError, match="at least two"):
        split_chronologically(make_frame(1))


def test_split_empty_frame_raises():
    with pytest.raises(ValueError, match="at least two"):
        split_chronologically(make_frame(0))
