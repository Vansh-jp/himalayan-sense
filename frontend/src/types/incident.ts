export type IncidentCategory = 'landslide' | 'flood' | 'road_block' | 'unsafe_route' | 'other';
export type IncidentSeverity = 'low' | 'medium' | 'high';
export type IncidentStatus = 'submitted' | 'verified' | 'in_progress' | 'resolved' | 'rejected';

export interface Incident {
  id: string;
  user_id: string;
  zone_id?: string | null;
  category: IncidentCategory;
  description: string;
  photo_url?: string | null;
  latitude: number;
  longitude: number;
  landmark?: string | null;
  severity: IncidentSeverity;
  status: IncidentStatus;
  admin_note?: string | null;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
}

export interface IncidentCreatePayload {
  category: IncidentCategory;
  description: string;
  latitude: number;
  longitude: number;
  landmark?: string;
  severity: IncidentSeverity;
  zone_id?: string;
  photo?: File;
}