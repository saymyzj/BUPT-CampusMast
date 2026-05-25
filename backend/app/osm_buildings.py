from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.models.base import Base, SessionLocal, engine
from app.models.map import CampusBuilding

OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"
BUPT_BBOX = (39.95695, 116.34915, 39.96395, 116.35345)
OSM_ATTRIBUTION = "Contains information from OpenStreetMap, available under ODbL."

CODE_BY_NAME = {
    "北邮主楼": "BUPT_MAIN",
    "图书馆": "BUPT_LIBRARY",
    "学生1号公寓": "BUPT_DORM_1",
    "学生2号公寓": "BUPT_DORM_2",
    "学生3号公寓": "BUPT_DORM_3",
    "学生4号公寓": "BUPT_DORM_4",
    "学生5号公寓": "BUPT_DORM_5",
    "学生6号公寓": "BUPT_DORM_6",
    "学生8号公寓": "BUPT_DORM_8",
    "学生9号公寓": "BUPT_DORM_9",
    "学生10号公寓": "BUPT_DORM_10",
    "学生11号公寓": "BUPT_DORM_11",
    "学生13号公寓": "BUPT_DORM_13",
    "教一楼": "BUPT_TEACHING_1",
    "教二楼": "BUPT_TEACHING_2",
    "教三楼": "BUPT_TEACHING_3",
    "教四楼": "BUPT_TEACHING_4",
    "北邮体育馆": "BUPT_GYM",
    "综合食堂(新食堂)": "BUPT_CANTEEN",
    "北京邮电大学学生餐厅(老食堂)": "BUPT_OLD_CANTEEN",
    "北邮邮驿站": "BUPT_EXPRESS",
}

DEFAULT_OSM_BUILDINGS = [
    ("way", "253330141", "教二楼", 39.9591486, 116.3518614),
    ("way", "265030101", "学生发展中心", 39.9620792, 116.3516887),
    ("way", "265030104", "学生13号公寓", 39.9616656, 116.3490844),
    ("way", "265030105", "学生5号公寓", 39.9621906, 116.3496277),
    ("way", "265030106", "学生3号公寓", 39.9615343, 116.3496401),
    ("way", "265030107", "学生8号公寓", 39.9621956, 116.3504816),
    ("way", "265030108", "学生4号公寓", 39.9615442, 116.3505088),
    ("way", "265030109", "学生1号公寓", 39.9610779, 116.3496655),
    ("way", "265030110", "学生2号公寓", 39.9610952, 116.3505329),
    ("way", "344376259", "南区教学楼", 39.9579680, 116.3507066),
    ("way", "363833971", "教四楼", 39.9606006, 116.3501365),
    ("way", "399008788", "中国邮政储蓄银行（鸿通楼）", 39.9605959, 116.3491485),
    ("way", "399008789", "未来学习大楼", 39.9599308, 116.3521917),
    ("way", "399008979", "教一楼", 39.9606009, 116.3517972),
    ("way", "399008980", "行政办公楼", 39.9607390, 116.3517959),
    ("way", "399009424", "北邮体育馆", 39.9605273, 116.3539519),
    ("way", "399009425", "可信网络通信协同创新中心（创新楼）", 39.9590307, 116.3527959),
    ("way", "399013934", "综合食堂(新食堂)", 39.9625975, 116.3503929),
    ("way", "399013935", "学生9号公寓", 39.9629219, 116.3494957),
    ("way", "399013936", "学生11号公寓", 39.9633451, 116.3495453),
    ("way", "399015104", "学生6号公寓", 39.9632960, 116.3520652),
    ("way", "399015106", "学生活动中心", 39.9627355, 116.3511776),
    ("way", "399015107", "经管楼", 39.9633018, 116.3512631),
    ("way", "399017728", "综合服务楼", 39.9627861, 116.3518562),
    ("way", "399018200", "北京邮电大学学生餐厅(老食堂)", 39.9620096, 116.3529764),
    ("way", "399038562", "科学会堂", 39.9599277, 116.3528331),
    ("way", "399046289", "教三楼", 39.9590674, 116.3502433),
    ("way", "582551392", "北邮邮驿站", 39.9635241, 116.3511565),
    ("manual", "BUPT_MAIN", "北邮主楼", 39.96003, 116.35097),
    ("manual", "BUPT_LIBRARY", "图书馆", 39.96088, 116.35217),
    ("manual", "BUPT_DORM_10", "学生10号公寓", 39.95844, 116.35165),
]


def _code_for(osm_type: str, osm_id: str, name: str) -> str:
    if name in CODE_BY_NAME:
        return CODE_BY_NAME[name]
    if osm_type == "manual":
        return osm_id
    prefix = "OSM_REL" if osm_type == "relation" else "OSM_WAY"
    return f"{prefix}_{osm_id}"[:32]


def _payload(
    *,
    osm_type: str,
    osm_id: str,
    name: str,
    latitude: float,
    longitude: float,
    polygon: list[list[float]] | None = None,
) -> CampusBuilding:
    return CampusBuilding(
        code=_code_for(osm_type, osm_id, name),
        osm_type=None if osm_type == "manual" else osm_type,
        osm_id=None if osm_type == "manual" else osm_id,
        name=name,
        campus_zone="校本部",
        latitude=latitude,
        longitude=longitude,
        polygon_json=json.dumps(polygon, ensure_ascii=False) if polygon else None,
        is_active=True,
    )


def seed_default_buildings(db: Session) -> int:
    for osm_type, osm_id, name, latitude, longitude in DEFAULT_OSM_BUILDINGS:
        db.merge(_payload(osm_type=osm_type, osm_id=osm_id, name=name, latitude=latitude, longitude=longitude))
    db.commit()
    return len(DEFAULT_OSM_BUILDINGS)


def _overpass_query(bbox: tuple[float, float, float, float]) -> str:
    south, west, north, east = bbox
    return f"""
[out:json][timeout:25];
(
  way["building"]({south},{west},{north},{east});
  relation["building"]({south},{west},{north},{east});
);
out center geom tags;
""".strip()


def fetch_osm_buildings(
    *,
    bbox: tuple[float, float, float, float] = BUPT_BBOX,
    endpoint: str = OVERPASS_ENDPOINT,
) -> list[dict[str, Any]]:
    body = urlencode({"data": _overpass_query(bbox)}).encode()
    request = Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "CampusMast local OSM building importer",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode())
    return payload.get("elements", [])


def import_osm_buildings(db: Session, *, endpoint: str = OVERPASS_ENDPOINT) -> int:
    count = 0
    for element in fetch_osm_buildings(endpoint=endpoint):
        tags = element.get("tags") or {}
        name = tags.get("name:zh") or tags.get("name") or tags.get("name:en")
        center = element.get("center") or {}
        if not name or "lat" not in center or "lon" not in center:
            continue
        geometry = element.get("geometry") or []
        polygon = [[float(node["lat"]), float(node["lon"])] for node in geometry if "lat" in node and "lon" in node]
        db.merge(
            _payload(
                osm_type=str(element.get("type")),
                osm_id=str(element.get("id")),
                name=str(name),
                latitude=float(center["lat"]),
                longitude=float(center["lon"]),
                polygon=polygon or None,
            )
        )
        count += 1
    db.commit()
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Import BUPT campus buildings from OpenStreetMap Overpass API.")
    parser.add_argument("--endpoint", default=OVERPASS_ENDPOINT)
    parser.add_argument("--fallback", action="store_true", help="Use the bundled OSM snapshot instead of Overpass.")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine, checkfirst=True)
    db = SessionLocal()
    try:
        count = seed_default_buildings(db) if args.fallback else import_osm_buildings(db, endpoint=args.endpoint)
    finally:
        db.close()
    print(f"Imported {count} campus buildings. {OSM_ATTRIBUTION}")


if __name__ == "__main__":
    main()
