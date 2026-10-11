import math
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.zone import Zone
from app.schemas.zone import ZoneCreate, ZoneUpdate


def get_zone(db: Session, zone_id: UUID) -> Optional[Zone]:
    return db.query(Zone).filter(Zone.id == zone_id).first()


def get_zone_by_name(db: Session, name: str) -> Optional[Zone]:
    return db.query(Zone).filter(Zone.name == name).first()


def get_zones(db: Session, skip: int = 0, limit: int = 100) -> List[Zone]:
    return db.query(Zone).offset(skip).limit(limit).all()


def create_zone(db: Session, zone_in: ZoneCreate) -> Zone:
    zone = Zone(**zone_in.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


def update_zone(db: Session, db_zone: Zone, zone_in: ZoneUpdate) -> Zone:
    update_data = zone_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_zone, field, value)
    db.commit()
    db.refresh(db_zone)
    return db_zone


def is_point_in_polygon(lat: float, lon: float, coordinates: list) -> bool:
    """Ray casting point-in-polygon test. Coordinates format: [[lon, lat], ...]"""
    inside = False
    n = len(coordinates)
    if n < 3:
        return False
    p1x, p1y = coordinates[0][0], coordinates[0][1]
    for i in range(1, n + 1):
        p2x, p2y = coordinates[i % n][0], coordinates[i % n][1]
        if min(p1y, p2y) < lat <= max(p1y, p2y):
            if lon <= max(p1x, p2x):
                x_inters = (lat - p1y) * (p2x - p1x) / (p2y - p1y + 1e-12) + p1x
                if p1x == p2x or lon <= x_inters:
                    inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_zone_for_coordinates(db: Session, lat: float, lon: float) -> Optional[Zone]:
    zones = db.query(Zone).all()
    if not zones:
        return None

    # 1. Try exact polygon match
    for zone in zones:
        geo = zone.boundary_geojson or {}
        geometry = geo.get("geometry", geo)
        coords = geometry.get("coordinates", [])
        geom_type = geometry.get("type", "")

        if geom_type == "Polygon" and coords:
            ring = coords[0]
            if is_point_in_polygon(lat, lon, ring):
                return zone
        elif geom_type == "MultiPolygon" and coords:
            for poly in coords:
                if poly and is_point_in_polygon(lat, lon, poly[0]):
                    return zone

    # 2. Nearest centroid fallback
    nearest_zone = min(
        zones,
        key=lambda z: haversine_distance(lat, lon, z.latitude, z.longitude),
    )
    return nearest_zone
