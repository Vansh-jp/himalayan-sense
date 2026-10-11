import logging
from pathlib import Path
from typing import Any, Dict, Optional
import joblib
from app.ml.feature_engineering import extract_features_vector

logger = logging.getLogger(__name__)

_MODEL_CACHE: Optional[Dict[str, Any]] = None


def load_trained_model() -> Optional[Dict[str, Any]]:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    possible_paths = [
        Path("backend/app/ml/models/risk_model.joblib"),
        Path("app/ml/models/risk_model.joblib"),
        Path(__file__).parent / "models" / "risk_model.joblib",
    ]

    for p in possible_paths:
        if p.exists():
            try:
                _MODEL_CACHE = joblib.load(p)
                logger.info(f"Loaded ML model from {p}")
                return _MODEL_CACHE
            except Exception as e:
                logger.warning(f"Error loading model from {p}: {e}")

    return None


def predict_risk(features_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Predict high landslide/flash-flood risk within 24h from meteorological & terrain features."""
    artifact = load_trained_model()
    features_df = extract_features_vector(features_dict)

    if artifact and "model" in artifact:
        model = artifact["model"]
        model_name = artifact.get("model_name", "MLClassifier")
        try:
            prob = float(model.predict_proba(features_df)[0][1])
            is_high_risk = bool(prob >= 0.45)  # threshold prioritizing safety recall
            return {
                "available": True,
                "model_name": model_name,
                "model_version": f"ml_{model_name.lower()}_v1",
                "risk_probability": round(prob, 4),
                "is_high_risk": is_high_risk,
                "metrics": artifact.get("metrics", {}),
            }
        except Exception as e:
            logger.warning(f"Model prediction failed: {e}")

    # Heuristic fallback if model artifact is not loaded yet
    rain_24h = float(features_dict.get("rainfall_last_24h", 0.0))
    forecast = float(features_dict.get("forecast_rainfall_24h", 0.0))
    slope = float(features_dict.get("slope", 15.0))
    reports = int(features_dict.get("active_verified_reports", 0))

    fallback_score = min(1.0, (rain_24h * 0.005 + forecast * 0.005 + (slope / 60.0) * 0.2 + reports * 0.2))
    return {
        "available": False,
        "model_name": "heuristic_fallback",
        "model_version": "fallback_v1",
        "risk_probability": round(fallback_score, 4),
        "is_high_risk": bool(fallback_score >= 0.5),
        "metrics": {},
    }
