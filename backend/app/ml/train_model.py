from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from xgboost import XGBClassifier

from app.ml.feature_engineering import FEATURE_COLUMNS


def generate_synthetic_dataset(n_samples: int = 1500) -> pd.DataFrame:
    """Generate time-ordered synthetic meteorological and terrain records for Dehradun."""
    np.random.seed(42)
    start_date = datetime(2025, 5, 1, tzinfo=timezone.utc)
    dates = [start_date + timedelta(hours=i * 6) for i in range(n_samples)]

    # Monsoon seasonality factor (June to September)
    monsoon_factor = np.array([
        1.8 if d.month in [6, 7, 8, 9] else 0.3 for d in dates
    ])

    rainfall_last_3h = np.maximum(0, np.random.exponential(scale=4.0 * monsoon_factor, size=n_samples))
    rainfall_last_24h = np.maximum(0, rainfall_last_3h * 2.5 + np.random.exponential(scale=12.0 * monsoon_factor, size=n_samples))
    rainfall_last_72h = np.maximum(0, rainfall_last_24h * 1.8 + np.random.exponential(scale=15.0 * monsoon_factor, size=n_samples))
    forecast_rainfall_24h = np.maximum(0, rainfall_last_24h * 0.7 + np.random.exponential(scale=10.0 * monsoon_factor, size=n_samples))
    max_hourly_rainfall = rainfall_last_3h * 0.6 + np.random.uniform(0, 15, size=n_samples)

    # Terrain features
    slope = np.random.uniform(5.0, 50.0, size=n_samples)  # steep slope > 30 deg has high landslide risk
    elevation = np.random.uniform(450.0, 2200.0, size=n_samples)
    distance_to_river = np.random.exponential(scale=600.0, size=n_samples)
    road_density = np.random.uniform(0.5, 6.0, size=n_samples)
    historical_incident_count = np.random.poisson(lam=2.5, size=n_samples)
    active_verified_reports = np.random.poisson(lam=0.4, size=n_samples)

    # Risk probability formulation based on scientific landslide thresholds
    # High rainfall + steep slope + river proximity + past incidents -> risk trigger
    risk_score_raw = (
        0.025 * rainfall_last_24h
        + 0.015 * forecast_rainfall_24h
        + 0.03 * max_hourly_rainfall
        + 0.04 * np.maximum(0, slope - 25)
        + 0.0008 * elevation
        - 0.0005 * distance_to_river
        + 0.15 * active_verified_reports
        + 0.05 * np.minimum(5, historical_incident_count)
        - 2.8  # bias
    )
    prob = 1.0 / (1.0 + np.exp(-risk_score_raw))
    # Add minor noise
    prob = np.clip(prob + np.random.normal(0, 0.05, size=n_samples), 0.0, 1.0)
    labels = (prob >= 0.45).astype(int)

    df = pd.DataFrame({
        "timestamp": [d.isoformat() for d in dates],
        "rainfall_last_3h": np.round(rainfall_last_3h, 2),
        "rainfall_last_24h": np.round(rainfall_last_24h, 2),
        "rainfall_last_72h": np.round(rainfall_last_72h, 2),
        "forecast_rainfall_24h": np.round(forecast_rainfall_24h, 2),
        "max_hourly_rainfall": np.round(max_hourly_rainfall, 2),
        "slope": np.round(slope, 2),
        "elevation": np.round(elevation, 1),
        "distance_to_river": np.round(distance_to_river, 1),
        "road_density": np.round(road_density, 2),
        "historical_incident_count": historical_incident_count,
        "active_verified_reports": active_verified_reports,
        "high_risk_event_within_24h": labels,
    })
    return df


def train_and_evaluate_models():
    print("[HimalayaSense ML] Generating training dataset...")
    df = generate_synthetic_dataset(n_samples=1600)

    # Save dataset to data/sample/
    sample_path = Path("data/sample/synthetic_landslide_data.csv")
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(sample_path, index=False)
    print(f"[HimalayaSense ML] Dataset saved to {sample_path} ({len(df)} records)")

    # Time-based split: 80% train, 20% test
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df["high_risk_event_within_24h"]
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df["high_risk_event_within_24h"]

    print(f"[HimalayaSense ML] Train size: {len(X_train)}, Test size: {len(X_test)}")
    print(f"[HimalayaSense ML] Target balance - Train: {y_train.mean():.2%}, Test: {y_test.mean():.2%}")

    # 1. Random Forest Classifier
    rf_model = RandomForestClassifier(
        n_estimators=150,
        max_depth=8,
        min_samples_split=4,
        class_weight="balanced",
        random_state=42,
    )
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    rf_probs = rf_model.predict_proba(X_test)[:, 1]

    rf_metrics = {
        "model": "RandomForest",
        "accuracy": round(float(accuracy_score(y_test, rf_preds)), 4),
        "precision": round(float(precision_score(y_test, rf_preds, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, rf_preds, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, rf_preds, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, rf_probs)), 4),
        "confusion_matrix": confusion_matrix(y_test, rf_preds).tolist(),
    }

    # 2. XGBoost Classifier
    scale_pos = (len(y_train) - sum(y_train)) / (sum(y_train) + 1e-5)
    xgb_model = XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        scale_pos_weight=scale_pos,
        eval_metric="logloss",
        random_state=42,
    )
    xgb_model.fit(X_train, y_train)
    xgb_preds = xgb_model.predict(X_test)
    xgb_probs = xgb_model.predict_proba(X_test)[:, 1]

    xgb_metrics = {
        "model": "XGBoost",
        "accuracy": round(float(accuracy_score(y_test, xgb_preds)), 4),
        "precision": round(float(precision_score(y_test, xgb_preds, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, xgb_preds, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, xgb_preds, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, xgb_probs)), 4),
        "confusion_matrix": confusion_matrix(y_test, xgb_preds).tolist(),
    }

    print("\n[HimalayaSense ML] Evaluation Results:")
    print("--------------------------------------------------")
    print(f"RandomForest -> Recall: {rf_metrics['recall']}, F1: {rf_metrics['f1']}, ROC-AUC: {rf_metrics['roc_auc']}")
    print(f"XGBoost      -> Recall: {xgb_metrics['recall']}, F1: {xgb_metrics['f1']}, ROC-AUC: {xgb_metrics['roc_auc']}")
    print("--------------------------------------------------")

    # Select best model: prioritize Recall because missing a landslide is catastrophic
    if xgb_metrics["recall"] > rf_metrics["recall"] or (
        xgb_metrics["recall"] == rf_metrics["recall"] and xgb_metrics["f1"] >= rf_metrics["f1"]
    ):
        best_model = xgb_model
        best_metrics = xgb_metrics
    else:
        best_model = rf_model
        best_metrics = rf_metrics

    print(f"[HimalayaSense ML] Selected Best Model: {best_metrics['model']} (Prioritizing Recall)")

    # Save best model artifact
    save_dir = Path("backend/app/ml/models")
    save_dir.mkdir(parents=True, exist_ok=True)
    model_file = save_dir / "risk_model.joblib"

    artifact = {
        "model": best_model,
        "model_name": best_metrics["model"],
        "feature_names": FEATURE_COLUMNS,
        "metrics": best_metrics,
        "rf_metrics": rf_metrics,
        "xgb_metrics": xgb_metrics,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    joblib.dump(artifact, model_file)
    print(f"[HimalayaSense ML] Saved model to {model_file}")

    # Also save metadata json
    meta_file = save_dir / "model_metrics.json"
    with open(meta_file, "w") as f:
        json.dump(
            {
                "best_model": best_metrics,
                "rf_metrics": rf_metrics,
                "xgb_metrics": xgb_metrics,
                "feature_names": FEATURE_COLUMNS,
            },
            f,
            indent=2,
        )

    return artifact


if __name__ == "__main__":
    train_and_evaluate_models()
