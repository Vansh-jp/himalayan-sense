from datetime import datetime, timedelta, timezone
import json
import uuid
from sqlalchemy.orm import Session
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.crud.crud_alert import create_alert
from app.crud.crud_incident import create_incident, update_incident_status
from app.crud.crud_risk import create_risk_assessment
from app.crud.crud_user import create_user, get_user_by_email
from app.crud.crud_weather import create_weather_readings_batch
from app.crud.crud_zone import create_zone, get_zone_by_name
from app.models.user import User
from app.models.zone import Zone
from app.schemas.alert import AlertCreate
from app.schemas.incident import IncidentCreate
from app.schemas.risk import RiskAssessmentCreate
from app.schemas.user import UserCreate
from app.schemas.weather import WeatherReadingCreate
from app.schemas.zone import ZoneCreate

DEMO_ZONES_DATA = [
    {
        "name": "Sahastradhara Foothills",
        "district": "Dehradun",
        "state": "Uttarakhand",
        "zone_type": "ward",
        "latitude": 30.3860,
        "longitude": 78.1300,
        "terrain_susceptibility_score": 0.85,
        "historical_incident_count": 9,
        "boundary_geojson": {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [78.115, 30.370],
                    [78.145, 30.370],
                    [78.150, 30.405],
                    [78.118, 30.405],
                    [78.115, 30.370],
                ]],
            },
            "properties": {"name": "Sahastradhara Foothills", "risk_type": "landslide"},
        },
    },
    {
        "name": "Rajpur Road - Mussoorie Ascent",
        "district": "Dehradun",
        "state": "Uttarakhand",
        "zone_type": "route",
        "latitude": 30.3820,
        "longitude": 78.0780,
        "terrain_susceptibility_score": 0.78,
        "historical_incident_count": 7,
        "boundary_geojson": {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [78.060, 30.365],
                    [78.095, 30.365],
                    [78.100, 30.410],
                    [78.065, 30.410],
                    [78.060, 30.365],
                ]],
            },
            "properties": {"name": "Rajpur Road - Mussoorie Ascent", "risk_type": "landslide"},
        },
    },
    {
        "name": "Maldevta - Song River Valley",
        "district": "Dehradun",
        "state": "Uttarakhand",
        "zone_type": "village",
        "latitude": 30.3180,
        "longitude": 78.1250,
        "terrain_susceptibility_score": 0.82,
        "historical_incident_count": 8,
        "boundary_geojson": {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [78.100, 30.295],
                    [78.150, 30.295],
                    [78.155, 30.340],
                    [78.105, 30.340],
                    [78.100, 30.295],
                ]],
            },
            "properties": {"name": "Maldevta - Song River Valley", "risk_type": "flood"},
        },
    },
    {
        "name": "Rispana Corridor (Deepnagar)",
        "district": "Dehradun",
        "state": "Uttarakhand",
        "zone_type": "ward",
        "latitude": 30.3080,
        "longitude": 78.0620,
        "terrain_susceptibility_score": 0.65,
        "historical_incident_count": 6,
        "boundary_geojson": {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [78.045, 30.290],
                    [78.080, 30.290],
                    [78.085, 30.330],
                    [78.050, 30.330],
                    [78.045, 30.290],
                ]],
            },
            "properties": {"name": "Rispana Corridor", "risk_type": "flood"},
        },
    },
    {
        "name": "Clock Tower & Paltan Bazaar",
        "district": "Dehradun",
        "state": "Uttarakhand",
        "zone_type": "ward",
        "latitude": 30.3255,
        "longitude": 78.0435,
        "terrain_susceptibility_score": 0.30,
        "historical_incident_count": 4,
        "boundary_geojson": {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [78.030, 30.315],
                    [78.060, 30.315],
                    [78.060, 30.340],
                    [78.030, 30.340],
                    [78.030, 30.315],
                ]],
            },
            "properties": {"name": "Clock Tower & Paltan Bazaar", "risk_type": "road_block"},
        },
    },
    {
        "name": "Bindal River / Patel Nagar",
        "district": "Dehradun",
        "state": "Uttarakhand",
        "zone_type": "ward",
        "latitude": 30.3120,
        "longitude": 78.0220,
        "terrain_susceptibility_score": 0.55,
        "historical_incident_count": 5,
        "boundary_geojson": {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [78.005, 30.295],
                    [78.035, 30.295],
                    [78.040, 30.330],
                    [78.010, 30.330],
                    [78.005, 30.295],
                ]],
            },
            "properties": {"name": "Bindal River / Patel Nagar", "risk_type": "flood"},
        },
    },
    {
        "name": "Prem Nagar - Chakrata Road",
        "district": "Dehradun",
        "state": "Uttarakhand",
        "zone_type": "route",
        "latitude": 30.3420,
        "longitude": 77.9650,
        "terrain_susceptibility_score": 0.38,
        "historical_incident_count": 3,
        "boundary_geojson": {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [77.940, 30.320],
                    [77.985, 30.320],
                    [77.990, 30.365],
                    [77.945, 30.365],
                    [77.940, 30.320],
                ]],
            },
            "properties": {"name": "Prem Nagar - Chakrata Road", "risk_type": "unsafe_route"},
        },
    },
    {
        "name": "Clement Town / Subhash Nagar",
        "district": "Dehradun",
        "state": "Uttarakhand",
        "zone_type": "ward",
        "latitude": 30.2680,
        "longitude": 78.0060,
        "terrain_susceptibility_score": 0.20,
        "historical_incident_count": 1,
        "boundary_geojson": {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [77.985, 30.250],
                    [78.030, 30.250],
                    [78.035, 30.285],
                    [77.990, 30.285],
                    [77.985, 30.250],
                ]],
            },
            "properties": {"name": "Clement Town / Subhash Nagar", "risk_type": "road_block"},
        },
    },
]


def seed_database():
    print("[Seed] Initializing database...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Seed Users
        admin_email = "admin@himalayasense.local"
        admin_user = get_user_by_email(db, admin_email)
        if not admin_user:
            admin_user = create_user(
                db,
                UserCreate(
                    name="State Disaster Management Authority (Admin)",
                    email=admin_email,
                    password="Admin@12345",
                    phone="+91-135-2710334",
                    role="admin",
                    district="Dehradun",
                ),
            )
            print(f"[Seed] Created admin: {admin_email}")

        citizen_email_1 = "citizen@himalayasense.local"
        citizen_1 = get_user_by_email(db, citizen_email_1)
        if not citizen_1:
            citizen_1 = create_user(
                db,
                UserCreate(
                    name="Aarav Sharma",
                    email=citizen_email_1,
                    password="Citizen@12345",
                    phone="+91-9876543210",
                    role="citizen",
                    district="Dehradun",
                ),
            )
            print(f"[Seed] Created citizen: {citizen_email_1}")

        citizen_email_2 = "priya.rawat@himalayasense.local"
        citizen_2 = get_user_by_email(db, citizen_email_2)
        if not citizen_2:
            citizen_2 = create_user(
                db,
                UserCreate(
                    name="Priya Rawat",
                    email=citizen_email_2,
                    password="Citizen@12345",
                    phone="+91-9876501234",
                    role="citizen",
                    district="Dehradun",
                ),
            )
            print(f"[Seed] Created citizen: {citizen_email_2}")

        # 2. Seed Zones
        zones_map: dict[str, Zone] = {}
        for zdata in DEMO_ZONES_DATA:
            existing = get_zone_by_name(db, zdata["name"])
            if not existing:
                existing = create_zone(db, ZoneCreate(**zdata))
                print(f"[Seed] Created zone: {existing.name}")
            zones_map[existing.name] = existing

        # 3. Seed Weather Readings for past 7 days (hourly points sampled every 6h)
        now = datetime.now(timezone.utc)
        for zone in zones_map.values():
            readings = []
            # High precipitation in Sahastradhara & Maldevta (monsoon simulation)
            is_wet_zone = "Sahastradhara" in zone.name or "Maldevta" in zone.name or "Rajpur" in zone.name
            base_precip = 18.0 if is_wet_zone else 2.0

            for h in range(7 * 24, 0, -6):
                pt_time = now - timedelta(hours=h)
                precip = round(max(0.0, base_precip + (h % 5) * 4.5 - 2.0), 1)
                readings.append(
                    WeatherReadingCreate(
                        zone_id=zone.id,
                        timestamp=pt_time,
                        precipitation_mm=precip,
                        temperature_c=round(24.0 - (h % 4), 1),
                        humidity=round(75.0 + (h % 3) * 5, 1),
                        wind_speed=round(8.0 + (h % 4), 1),
                        forecast_precipitation_24h_mm=round(75.0 if is_wet_zone else 12.0, 1),
                        source="open-meteo",
                    )
                )
            create_weather_readings_batch(db, readings)
        print("[Seed] Seeded 7 days of weather readings for all 8 zones")

        # 4. Seed 25 Sample Incidents
        sample_incidents = [
            # Sahastradhara (severe landslide zone)
            {
                "zone": "Sahastradhara Foothills",
                "user": citizen_1,
                "category": "landslide",
                "severity": "high",
                "status": "verified",
                "description": "Massive boulder slide blocking Sahastradhara main approach road near turn 4.",
                "landmark": "Turn 4 near sulphur spring viewpoint",
                "lat": 30.3872,
                "lon": 78.1315,
                "admin_note": "Verified by SDRF team. Earthmovers deployed.",
            },
            {
                "zone": "Sahastradhara Foothills",
                "user": citizen_2,
                "category": "landslide",
                "severity": "high",
                "status": "in_progress",
                "description": "Loose soil and small rocks continuously falling from upper cliff face.",
                "landmark": "Near ITBP camp link road",
                "lat": 30.3845,
                "lon": 78.1280,
                "admin_note": "PCC retaining wall damaged. Traffic diverted.",
            },
            {
                "zone": "Sahastradhara Foothills",
                "user": citizen_1,
                "category": "unsafe_route",
                "severity": "medium",
                "status": "submitted",
                "description": "Road shoulder eroded after midnight downpour. Risk of collapse.",
                "landmark": "Kempty tributary culvert",
                "lat": 30.3890,
                "lon": 78.1340,
                "admin_note": None,
            },
            # Maldevta (severe flood zone)
            {
                "zone": "Maldevta - Song River Valley",
                "user": citizen_2,
                "category": "flood",
                "severity": "high",
                "status": "verified",
                "description": "Song river overflowing natural embankments. Road inundated under 3 feet water.",
                "landmark": "Maldevta main bridge approach",
                "lat": 30.3195,
                "lon": 78.1265,
                "admin_note": "Evacuation advisory issued for low-lying huts.",
            },
            {
                "zone": "Maldevta - Song River Valley",
                "user": citizen_1,
                "category": "flood",
                "severity": "high",
                "status": "verified",
                "description": "Debris flow mixed with mud rushing across residential lane.",
                "landmark": "Seri village pathway",
                "lat": 30.3160,
                "lon": 78.1210,
                "admin_note": "SDRF deployed.",
            },
            {
                "zone": "Maldevta - Song River Valley",
                "user": citizen_2,
                "category": "flood",
                "severity": "medium",
                "status": "verified",
                "description": "Culvert blocked by tree trunks, causing localized flash flooding.",
                "landmark": "Bhimawala junction",
                "lat": 30.3210,
                "lon": 78.1290,
                "admin_note": "JCB on site clearing debris.",
            },
            # Rajpur Road
            {
                "zone": "Rajpur Road - Mussoorie Ascent",
                "user": citizen_1,
                "category": "landslide",
                "severity": "high",
                "status": "verified",
                "description": "Fresh mudslide covering two lanes near Kuthalgate toll.",
                "landmark": "Kuthalgate barrier",
                "lat": 30.3835,
                "lon": 78.0792,
                "admin_note": "One-way traffic operational now.",
            },
            {
                "zone": "Rajpur Road - Mussoorie Ascent",
                "user": citizen_2,
                "category": "road_block",
                "severity": "medium",
                "status": "resolved",
                "description": "Uprooted pine tree blocking the downhill lane.",
                "landmark": "Near Old Rajpur police chowki",
                "lat": 30.3790,
                "lon": 78.0750,
                "admin_note": "Tree cleared and wood removed by forest dept.",
            },
            {
                "zone": "Rajpur Road - Mussoorie Ascent",
                "user": citizen_1,
                "category": "unsafe_route",
                "severity": "medium",
                "status": "in_progress",
                "description": "Severe potholes and water gushing on the asphalt surface.",
                "landmark": "Diversion bend near hotel",
                "lat": 30.3850,
                "lon": 78.0810,
                "admin_note": "PWD notified for patch repair.",
            },
            # Rispana Corridor
            {
                "zone": "Rispana Corridor (Deepnagar)",
                "user": citizen_2,
                "category": "flood",
                "severity": "high",
                "status": "verified",
                "description": "Rispana nullah overflowing into roadside shanties after torrential rain.",
                "landmark": "Deepnagar low bridge",
                "lat": 30.3090,
                "lon": 78.0635,
                "admin_note": "Relief camp set up in nearby school.",
            },
            {
                "zone": "Rispana Corridor (Deepnagar)",
                "user": citizen_1,
                "category": "unsafe_route",
                "severity": "low",
                "status": "resolved",
                "description": "Stagnant drainage water creating hazardous bike skidding.",
                "landmark": "Chander Nagar crossing",
                "lat": 30.3060,
                "lon": 78.0590,
                "admin_note": "Drain unclogged by municipal team.",
            },
            # Bindal River
            {
                "zone": "Bindal River / Patel Nagar",
                "user": citizen_2,
                "category": "flood",
                "severity": "medium",
                "status": "submitted",
                "description": "Bindal bridge retaining wall cracking under strong water currents.",
                "landmark": "Patel Nagar bridge pier",
                "lat": 30.3130,
                "lon": 78.0235,
                "admin_note": None,
            },
            {
                "zone": "Bindal River / Patel Nagar",
                "user": citizen_1,
                "category": "road_block",
                "severity": "medium",
                "status": "resolved",
                "description": "Submerged road section cleared of silt.",
                "landmark": "Lakkhibagh railway crossing underpass",
                "lat": 30.3110,
                "lon": 78.0210,
                "admin_note": "Pumped out and reopened.",
            },
            # Clock Tower
            {
                "zone": "Clock Tower & Paltan Bazaar",
                "user": citizen_1,
                "category": "road_block",
                "severity": "low",
                "status": "resolved",
                "description": "Traffic jam due to broken storm sewer grill.",
                "landmark": "Opposite Gandhi Park",
                "lat": 30.3260,
                "lon": 78.0440,
                "admin_note": "Replaced grate cover.",
            },
            {
                "zone": "Clock Tower & Paltan Bazaar",
                "user": citizen_2,
                "category": "other",
                "severity": "low",
                "status": "rejected",
                "description": "Pothole in front of sweet shop.",
                "landmark": "Paltan Bazaar entry",
                "lat": 30.3248,
                "lon": 78.0425,
                "admin_note": "Duplicate of existing municipal ticket.",
            },
            # Prem Nagar
            {
                "zone": "Prem Nagar - Chakrata Road",
                "user": citizen_1,
                "category": "unsafe_route",
                "severity": "medium",
                "status": "submitted",
                "description": "Heavy gravel spread across blind curve after heavy showers.",
                "landmark": "Nanda Ki Chowki",
                "lat": 30.3435,
                "lon": 77.9670,
                "admin_note": None,
            },
            {
                "zone": "Prem Nagar - Chakrata Road",
                "user": citizen_2,
                "category": "road_block",
                "severity": "low",
                "status": "resolved",
                "description": "Stalled truck on wet road cleared.",
                "landmark": "Prem Nagar main market",
                "lat": 30.3410,
                "lon": 77.9630,
                "admin_note": "Towed to side.",
            },
            # Clement Town
            {
                "zone": "Clement Town / Subhash Nagar",
                "user": citizen_1,
                "category": "road_block",
                "severity": "low",
                "status": "resolved",
                "description": "Water accumulated on highway side lane.",
                "landmark": "Near Graphic Era gate",
                "lat": 30.2690,
                "lon": 78.0070,
                "admin_note": "Water receded naturally.",
            },
            {
                "zone": "Clement Town / Subhash Nagar",
                "user": citizen_2,
                "category": "unsafe_route",
                "severity": "low",
                "status": "submitted",
                "description": "Street lights defunct during storm.",
                "landmark": "Post Office road",
                "lat": 30.2670,
                "lon": 78.0050,
                "admin_note": None,
            },
            # Extra incidents for count
            {
                "zone": "Sahastradhara Foothills",
                "user": citizen_2,
                "category": "road_block",
                "severity": "high",
                "status": "verified",
                "description": "Mud sludge deposited over 50 meters of mountain road.",
                "landmark": "Culvert 3",
                "lat": 30.3880,
                "lon": 78.1320,
                "admin_note": "Bulldozer active on site.",
            },
            {
                "zone": "Maldevta - Song River Valley",
                "user": citizen_1,
                "category": "flood",
                "severity": "high",
                "status": "in_progress",
                "description": "Water entered ground floors of 6 houses near river curve.",
                "landmark": "Song riverside bend",
                "lat": 30.3175,
                "lon": 78.1240,
                "admin_note": "Residents moved to relief camp.",
            },
        ]

        for inc_data in sample_incidents:
            zone_obj = zones_map[inc_data["zone"]]
            inc_in = IncidentCreate(
                category=inc_data["category"],
                description=inc_data["description"],
                latitude=inc_data["lat"],
                longitude=inc_data["lon"],
                landmark=inc_data["landmark"],
                severity=inc_data["severity"],
                photo_url=None,
                zone_id=zone_obj.id,
            )
            created_inc = create_incident(db, inc_in, user_id=inc_data["user"].id)
            if inc_data["status"] != "submitted":
                update_incident_status(
                    db,
                    created_inc,
                    status=inc_data["status"],
                    admin_note=inc_data["admin_note"],
                )
        print(f"[Seed] Created {len(sample_incidents)} sample incidents")

        # 5. Evaluate and seed Risk Assessments for all zones
        from app.services.risk_service import calculate_zone_risk
        for zone in zones_map.values():
            assessment = calculate_zone_risk(db, zone)
            print(f"[Seed] Zone '{zone.name}' -> Level: {assessment.risk_level.upper()}, Score: {assessment.risk_score}")

        # 6. Seed Sample Alerts
        sample_alerts = [
            {
                "zone": zones_map["Sahastradhara Foothills"],
                "title": "Severe Landslide Emergency Alert — Sahastradhara Foothills",
                "message": "Continuous heavy rainfall (>75mm) and 2 verified active landslides. High danger of rockfalls on Sahastradhara route. Avoid travel.",
                "risk_level": "red",
                "channel": "in_app",
            },
            {
                "zone": zones_map["Maldevta - Song River Valley"],
                "title": "High Flash-Flood Warning — Maldevta & Song River",
                "message": "Song river swelling past warning threshold. Low lying embankments flooded. SDRF deployed.",
                "risk_level": "orange",
                "channel": "in_app",
            },
            {
                "zone": zones_map["Rajpur Road - Mussoorie Ascent"],
                "title": "High Landslide Warning — Rajpur Road",
                "message": "Debris falls reported near Kuthalgate. Drive cautiously and watch for falling stones.",
                "risk_level": "orange",
                "channel": "in_app",
            },
            {
                "zone": zones_map["Rispana Corridor (Deepnagar)"],
                "title": "Urban Flood Advisory — Rispana River Corridor",
                "message": "Moderate overflow of Rispana storm channel. Avoid driving across submerged culverts.",
                "risk_level": "yellow",
                "channel": "in_app",
            },
        ]

        for sa in sample_alerts:
            create_alert(
                db,
                AlertCreate(
                    zone_id=sa["zone"].id,
                    title=sa["title"],
                    message=sa["message"],
                    risk_level=sa["risk_level"],
                    channel=sa["channel"],
                    status="sent",
                ),
            )
        print(f"[Seed] Seeded {len(sample_alerts)} emergency alerts")

    finally:
        db.close()

    print("[Seed] Seeding completed successfully.")


if __name__ == "__main__":
    seed_database()
