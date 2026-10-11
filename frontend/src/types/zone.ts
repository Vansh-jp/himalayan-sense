import type { RiskLevel } from '../utils/riskHelpers';

export interface ZoneGeometry {
  type: 'Polygon' | 'MultiPolygon';
  coordinates: number[][][] | number[][][][];
}

export interface Zone {
  id: string;
  name: string;
  district: string;
  state: string;
  zone_type: 'ward' | 'route' | 'village';
  latitude: number;
  longitude: number;
  boundary_geojson: {
    type: 'Feature';
    geometry: ZoneGeometry;
    properties?: Record<string, unknown>;
  };
  terrain_susceptibility_score: number;
  historical_incident_count: number;
  current_risk?: {
    risk_score: number;
    risk_level: RiskLevel;
    risk_type: string;
    model_version: string;
    explanation: {
      metrics: {
        rainfall_24h_mm: number;
        forecast_24h_mm: number;
        terrain_susceptibility: number;
        historical_incidents: number;
        active_verified_incidents: number;
      };
      primary_hazard: string;
      override_applied?: string | null;
    };
    assessed_at: string;
  };
}