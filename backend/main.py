from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from api.routes import flight_plan, drone, airspace, weather, chat, scenario, metrics
from api.websocket import telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — 테이블 자동 생성 (마이그레이션 파일 없을 때 대비)
    from db.database import engine, Base, SessionLocal
    import db.orm_models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # 공역 데이터 자동 시드 — 테이블이 비어있으면 한국 공역 데이터 삽입
    from db.crud import bulk_create_airspace_zones
    from core.airspace.manager import create_korean_airspace_zones
    db = SessionLocal()
    try:
        count = bulk_create_airspace_zones(db, create_korean_airspace_zones())
        if count > 0:
            print(f"[SkyMind] 한국 공역 데이터 {count}개 자동 시드 완료")
    finally:
        db.close()

    yield
    # Shutdown


app = FastAPI(
    title="SkyMind API",
    description="AI Drone Air Traffic Controller",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API routes
app.include_router(flight_plan.router, prefix="/api/flight-plans", tags=["Flight Plans"])
app.include_router(drone.router, prefix="/api/drones", tags=["Drones"])
app.include_router(airspace.router, prefix="/api/airspaces", tags=["Airspaces"])
app.include_router(weather.router, prefix="/api/weather", tags=["Weather"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(scenario.router, prefix="/api/scenarios", tags=["Scenarios"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])

# WebSocket
app.include_router(telemetry.router, tags=["Telemetry"])


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "skymind"}
