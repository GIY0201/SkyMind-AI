"""공역 구역 관리."""

import math

from models.common import Position3D, ZoneType
from models.airspace import AirspaceZone


class AirspaceManager:
    """공역 구역 관리자.

    GeoJSON Polygon 기반으로 공역 구역을 관리하고,
    특정 좌표가 어떤 구역에 속하는지 판정한다.
    """

    def __init__(self) -> None:
        self._zones: dict[str, AirspaceZone] = {}

    def add_zone(self, zone: AirspaceZone) -> None:
        """공역 구역 추가."""
        self._zones[zone.zone_id] = zone

    def remove_zone(self, zone_id: str) -> bool:
        """공역 구역 제거. 성공 시 True."""
        return self._zones.pop(zone_id, None) is not None

    def get_zone(self, zone_id: str) -> AirspaceZone | None:
        """구역 ID로 조회."""
        return self._zones.get(zone_id)

    def list_zones(self, active_only: bool = True) -> list[AirspaceZone]:
        """모든 구역 조회."""
        zones = list(self._zones.values())
        if active_only:
            zones = [z for z in zones if z.active]
        return zones

    def get_zone_at(self, position: Position3D) -> list[AirspaceZone]:
        """특정 좌표가 속하는 모든 공역 구역 반환."""
        result = []
        for zone in self._zones.values():
            if not zone.active:
                continue
            if not (zone.floor_altitude_m <= position.alt_m <= zone.ceiling_altitude_m):
                continue
            if self._point_in_polygon(position.lat, position.lon, zone.geometry):
                result.append(zone)
        return result

    def is_flyable(self, position: Position3D) -> bool:
        """해당 좌표에서 비행 가능 여부 판정.

        RESTRICTED 구역 내부이면 비행 불가.
        """
        zones = self.get_zone_at(position)
        for zone in zones:
            if zone.zone_type == ZoneType.RESTRICTED:
                return False
        return True

    def requires_clearance(self, position: Position3D) -> bool:
        """해당 좌표에서 비행 승인이 필요한지 판정."""
        zones = self.get_zone_at(position)
        for zone in zones:
            if zone.zone_type == ZoneType.CONTROLLED:
                return True
        return False

    def get_zone_type_at(self, position: Position3D) -> ZoneType:
        """해당 좌표의 가장 제한적인 공역 등급 반환.

        우선순위: RESTRICTED > EMERGENCY_ONLY > CONTROLLED > FREE
        """
        zones = self.get_zone_at(position)
        if not zones:
            return ZoneType.FREE

        priority = {
            ZoneType.RESTRICTED: 0,
            ZoneType.EMERGENCY_ONLY: 1,
            ZoneType.CONTROLLED: 2,
            ZoneType.FREE: 3,
        }
        return min(zones, key=lambda z: priority[z.zone_type]).zone_type

    @staticmethod
    def _point_in_polygon(lat: float, lon: float, geometry: dict) -> bool:
        """Ray casting 알고리즘으로 점이 GeoJSON Polygon 내부인지 판정.

        Args:
            lat: 위도.
            lon: 경도.
            geometry: GeoJSON geometry 객체 {"type": "Polygon", "coordinates": [[[lon, lat], ...]]}.

        Returns:
            내부이면 True.
        """
        if geometry.get("type") != "Polygon":
            return False

        coordinates = geometry.get("coordinates", [])
        if not coordinates:
            return False

        # GeoJSON은 [longitude, latitude] 순서
        ring = coordinates[0]  # 외곽 링만 사용
        n = len(ring)
        inside = False

        j = n - 1
        for i in range(n):
            xi, yi = ring[i][0], ring[i][1]  # lon, lat
            xj, yj = ring[j][0], ring[j][1]

            if ((yi > lat) != (yj > lat)) and (
                lon < (xj - xi) * (lat - yi) / (yj - yi) + xi
            ):
                inside = not inside
            j = i

        return inside


def _circle_polygon(center_lat: float, center_lon: float, radius_m: float, n: int = 32) -> dict:
    """원형 GeoJSON Polygon 생성."""
    coords = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        dlat = (radius_m / 111320) * math.cos(angle)
        dlon = (radius_m / (111320 * math.cos(math.radians(center_lat)))) * math.sin(angle)
        coords.append([round(center_lon + dlon, 6), round(center_lat + dlat, 6)])
    coords.append(coords[0])  # 폐합
    return {"type": "Polygon", "coordinates": [coords]}


def create_korean_airspace_zones() -> list[AirspaceZone]:
    """한국 실제 공역 데이터 기반 구역 생성.

    P73, R75, 공항 관제권, 자유비행 구역 등을 포함한다.

    Returns:
        한국 공역 구역 리스트.
    """
    zones = [
        # ── 비행금지구역 (RESTRICTED) ──
        # P73A: 서울 중심 비행금지구역 (용산~종로)
        AirspaceZone(
            zone_id="P73A",
            name="P73A 서울 비행금지구역",
            zone_type=ZoneType.RESTRICTED,
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [126.955, 37.545], [126.975, 37.540], [126.995, 37.545],
                    [127.010, 37.555], [127.010, 37.575], [126.995, 37.585],
                    [126.975, 37.590], [126.955, 37.585], [126.940, 37.575],
                    [126.940, 37.555], [126.955, 37.545],
                ]],
            },
            floor_altitude_m=0,
            ceiling_altitude_m=400,
            restrictions=["P73A 비행금지구역", "국방부 고시", "상시 적용"],
        ),
        # P73B: 서울 확장 비행금지구역 (마포~성동, 150m 이하)
        AirspaceZone(
            zone_id="P73B",
            name="P73B 서울 확장 금지구역",
            zone_type=ZoneType.RESTRICTED,
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [126.920, 37.535], [126.960, 37.530], [127.000, 37.530],
                    [127.030, 37.535], [127.040, 37.555], [127.040, 37.580],
                    [127.030, 37.600], [127.000, 37.605], [126.960, 37.605],
                    [126.920, 37.600], [126.910, 37.580], [126.910, 37.555],
                    [126.920, 37.535],
                ]],
            },
            floor_altitude_m=0,
            ceiling_altitude_m=150,
            restrictions=["P73B 확장 금지구역", "150m 이하 비행금지"],
        ),
        # R75: 용산 대통령실 비행금지 (반경 1.5km 원형)
        AirspaceZone(
            zone_id="R75",
            name="R75 대통령실 비행금지",
            zone_type=ZoneType.RESTRICTED,
            geometry=_circle_polygon(37.5299, 126.9648, 1500),
            floor_altitude_m=0,
            ceiling_altitude_m=400,
            restrictions=["R75 대통령실 비행금지구역", "상시 적용", "위반 시 군사 대응"],
        ),
        # 김포공항 관제권
        AirspaceZone(
            zone_id="GIMPO-CTR",
            name="김포공항 관제권",
            zone_type=ZoneType.RESTRICTED,
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [126.760, 37.545], [126.775, 37.540], [126.800, 37.540],
                    [126.820, 37.545], [126.825, 37.555], [126.825, 37.570],
                    [126.820, 37.580], [126.800, 37.585], [126.775, 37.585],
                    [126.760, 37.580], [126.755, 37.570], [126.755, 37.555],
                    [126.760, 37.545],
                ]],
            },
            floor_altitude_m=0,
            ceiling_altitude_m=400,
            restrictions=["김포공항 관제권", "AIP 게시", "비인가 비행 금지"],
        ),
        # 인천국제공항 관제권
        AirspaceZone(
            zone_id="INCHEON-CTR",
            name="인천공항 관제권",
            zone_type=ZoneType.RESTRICTED,
            geometry=_circle_polygon(37.4602, 126.4407, 5000),
            floor_altitude_m=0,
            ceiling_altitude_m=400,
            restrictions=["인천공항 관제권", "반경 5km", "비인가 비행 금지"],
        ),

        # ── 관제구역 (CONTROLLED) ──
        # 서울 도심 관제구역
        AirspaceZone(
            zone_id="CTRL-SEOUL",
            name="서울 도심 관제구역",
            zone_type=ZoneType.CONTROLLED,
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [126.900, 37.530], [126.950, 37.520], [127.000, 37.520],
                    [127.050, 37.530], [127.060, 37.560], [127.060, 37.590],
                    [127.050, 37.610], [127.000, 37.620], [126.950, 37.620],
                    [126.900, 37.610], [126.890, 37.590], [126.890, 37.560],
                    [126.900, 37.530],
                ]],
            },
            floor_altitude_m=0,
            ceiling_altitude_m=200,
            restrictions=["서울 도심 관제구역", "비행 전 승인 필요", "200m 이하"],
        ),

        # ── 자유비행구역 (FREE) ──
        # 한강 자유비행 회랑 (김포~잠실 한강 따라)
        AirspaceZone(
            zone_id="FREE-HANGANG",
            name="한강 자유비행 회랑",
            zone_type=ZoneType.FREE,
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [126.830, 37.525], [126.870, 37.518], [126.910, 37.515],
                    [126.950, 37.517], [126.980, 37.519], [127.020, 37.518],
                    [127.060, 37.520], [127.100, 37.522],
                    [127.100, 37.530], [127.060, 37.528], [127.020, 37.526],
                    [126.980, 37.527], [126.950, 37.525], [126.910, 37.523],
                    [126.870, 37.526], [126.830, 37.533],
                    [126.830, 37.525],
                ]],
            },
            floor_altitude_m=30,
            ceiling_altitude_m=150,
            restrictions=["한강 자유비행 회랑", "30~150m 고도 제한", "주간 비행만 허용"],
        ),
        # 여의도공원 자유비행구역
        AirspaceZone(
            zone_id="FREE-YEOUIDO",
            name="여의도공원 자유비행",
            zone_type=ZoneType.FREE,
            geometry=_circle_polygon(37.5264, 126.9245, 500),
            floor_altitude_m=30,
            ceiling_altitude_m=100,
            restrictions=["여의도공원 자유비행구역", "100m 이하"],
        ),
        # 난지한강공원 자유비행구역
        AirspaceZone(
            zone_id="FREE-NANJI",
            name="난지한강공원 자유비행",
            zone_type=ZoneType.FREE,
            geometry=_circle_polygon(37.5667, 126.8722, 600),
            floor_altitude_m=30,
            ceiling_altitude_m=100,
            restrictions=["난지한강공원 자유비행구역", "100m 이하"],
        ),
    ]
    return zones


def create_seoul_default_zones() -> list[AirspaceZone]:
    """서울 수도권 기본 공역 구역 생성 (테스트/개발용).

    Returns:
        기본 공역 구역 리스트.
    """
    zones = [
        # 김포공항 주변 — 비행 금지
        AirspaceZone(
            zone_id="RESTRICT-001",
            name="김포공항 비행금지구역",
            zone_type=ZoneType.RESTRICTED,
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [126.78, 37.57], [126.82, 37.57],
                    [126.82, 37.59], [126.78, 37.59],
                    [126.78, 37.57],
                ]],
            },
            floor_altitude_m=0,
            ceiling_altitude_m=400,
        ),
        # 용산 대통령실 주변 — 비행 금지
        AirspaceZone(
            zone_id="RESTRICT-002",
            name="용산 비행금지구역",
            zone_type=ZoneType.RESTRICTED,
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [126.97, 37.53], [126.99, 37.53],
                    [126.99, 37.54], [126.97, 37.54],
                    [126.97, 37.53],
                ]],
            },
            floor_altitude_m=0,
            ceiling_altitude_m=400,
        ),
        # 서울 도심 — 허가 필요
        AirspaceZone(
            zone_id="CTRL-001",
            name="서울 도심 관제구역",
            zone_type=ZoneType.CONTROLLED,
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [126.95, 37.54], [127.01, 37.54],
                    [127.01, 37.58], [126.95, 37.58],
                    [126.95, 37.54],
                ]],
            },
            floor_altitude_m=0,
            ceiling_altitude_m=200,
        ),
        # 한강 상공 — 자유 비행
        AirspaceZone(
            zone_id="FREE-001",
            name="한강 자유비행구역",
            zone_type=ZoneType.FREE,
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [126.89, 37.51], [127.10, 37.51],
                    [127.10, 37.53], [126.89, 37.53],
                    [126.89, 37.51],
                ]],
            },
            floor_altitude_m=30,
            ceiling_altitude_m=150,
        ),
    ]
    return zones
