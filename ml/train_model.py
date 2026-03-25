from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

try:
    from ml.feature_engineering import FEATURE_COLUMNS, prepare_training_frame
except ModuleNotFoundError:
    from feature_engineering import FEATURE_COLUMNS, prepare_training_frame


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "daily.csv"
MODEL_PATH = Path(__file__).resolve().parent / "irrigation_model.joblib"
TEST_SIZE = 0.2


def split_chronologically(frame: pd.DataFrame, test_size: float = TEST_SIZE) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")

    if len(frame) < 2:
        raise ValueError("Need at least two rows to create a train/test split")

    split_index = int(len(frame) * (1 - test_size))
    split_index = min(max(split_index, 1), len(frame) - 1)
    return frame.iloc[:split_index].copy(), frame.iloc[split_index:].copy()


def main() -> None:
    prepared_frame = prepare_training_frame(pd.read_csv(DATASET_PATH))
    train_frame, test_frame = split_chronologically(prepared_frame)

    X_train = train_frame[FEATURE_COLUMNS]
    y_train = train_frame["irrigate"]
    X_test = test_frame[FEATURE_COLUMNS]
    y_test = test_frame["irrigate"]

    model = RandomForestClassifier(
        n_estimators=200,
        min_samples_leaf=5,
        class_weight="balanced_subsample",
        random_state=42,
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    joblib.dump(
        {
            "model": model,
            "feature_columns": FEATURE_COLUMNS,
            "label_name": "irrigate",
            "label_source": "heuristic deficit threshold",
            "threshold_mm": 1.5,
        },
        MODEL_PATH,
    )

    print(f"Model trained successfully and saved to {MODEL_PATH}")
    print(
        "Warning: labels are generated from a deficit rule, so these metrics only measure "
        "agreement with that rule and not real-world irrigation outcomes."
    )
    print(
        "Train range:",
        train_frame["Date"].min().date(),
        "to",
        train_frame["Date"].max().date(),
    )
    print(
        "Test range:",
        test_frame["Date"].min().date(),
        "to",
        test_frame["Date"].max().date(),
    )
    print("Features:", ", ".join(FEATURE_COLUMNS))
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred))


if __name__ == "__main__":
    main()
