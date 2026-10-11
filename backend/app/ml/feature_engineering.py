from typing import Any, Dict, List
import numpy as np
import pandas as pd

FEATURE_COLUMNS: List[str] = [
    "rainfall_last_3h",
    "rainfall_last_24h",
    "rainfall_last_72h",
    "forecast_rainfall_24h",
    "max_hourly_rainfall",
    "slope",
    "elevation",
    "distance_to_river",
    "road_density",
    "historical_incident_count",
    "active_verified_reports",
]


def extract_features_vector(data: Dict[str, Any]) -> pd.DataFrame:
    """Prepare a single sample DataFrame aligned with model features."""
    row = {
        "rainfall_last_3h": float(data.get("rainfall_last_3h", 0.0)),
        "rainfall_last_24h": float(data.get("rainfall_last_24h", 0.0)),
        "rainfall_last_72h": float(data.get("rainfall_last_72h", 0.0)),
        "forecast_rainfall_24h": float(data.get("forecast_rainfall_24h", 0.0)),
        "max_hourly_rainfall": float(data.get("max_hourly_rainfall", 0.0)),
        "slope": float(data.get("slope", 15.0)),  # slope in degrees
        "elevation": float(data.get("elevation", 650.0)),  # meters
        "distance_to_river": float(data.get("distance_to_river", 500.0)),  # meters
        "road_density": float(data.get("road_density", 2.5)),  # km/km2
        "historical_incident_count": int(data.get("historical_incident_count", 0)),
        "active_verified_reports": int(data.get("active_verified_reports", 0)),
    }
    return pd.DataFrame([row], columns=FEATURE_COLUMNS)
