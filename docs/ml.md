# HimalayaSense Machine Learning Engine

## 1. Objective

Provide probabilistic decision support for severe landslide or flash-flood events within a 24-hour forward window across Dehradun sub-zones.

## 2. Feature Vector

| Feature | Unit / Type | Description |
|---|---|---|
| `rainfall_last_3h` | mm | Short-burst antecedent precipitation |
| `rainfall_last_24h` | mm | Cumulative 24-hour rainfall |
| `rainfall_last_72h` | mm | Antecedent saturation index (72 hours) |
| `forecast_rainfall_24h` | mm | Next 24-hour precipitation forecast from Open-Meteo |
| `max_hourly_rainfall` | mm/h | Maximum peak intensity in the last 24 hours |
| `slope` | degrees | Local terrain gradient |
| `elevation` | meters | Altitude above sea level |
| `distance_to_river` | meters | Proximity to seasonal rivers (Song, Rispana, Bindal) |
| `road_density` | km/km² | Human cuts and infrastructure load on hillslope |
| `historical_incident_count` | integer | Past recorded landslides/blockages |
| `active_verified_reports` | integer | Citizen incident reports currently verified |

Target variable: `high_risk_event_within_24h` (0 or 1).

## 3. Training & Validation

- **Split Methodology**: Time-ordered train/test split (80% train, 20% test). Avoids lookahead bias from random shuffling in temporal meteorological systems.
- **Algorithms Compared**:
  1. `RandomForestClassifier` (`n_estimators=150`, `class_weight='balanced'`)
  2. `XGBClassifier` (`scale_pos_weight` tuned for class imbalance, `learning_rate=0.08`)
- **Metric Priority**: High **Recall** is prioritized over Precision. In disaster warning, a false negative (unwarned landslide causing casualties) carries catastrophic consequence compared to a precautionary false alert.

## 4. Current Performance Metrics

- **Selected Model**: `XGBoost`
- **Recall**: `0.7907` (vs RandomForest `0.7209`)
- **F1-Score**: `0.8000`
- **ROC-AUC**: `0.9793`
- **Model Artifact Path**: `backend/app/ml/models/risk_model.joblib`
- **Dataset Path**: `data/sample/synthetic_landslide_data.csv`

## 5. Integration

The inference module `app.ml.predict.predict_risk` is embedded into the zone risk assessment lifecycle (`app.services.risk_service.calculate_zone_risk`). Whenever the ML classifier detects elevated risk probability (>0.45), the zone's status is promoted and detailed in the assessment explanation breakdown.
