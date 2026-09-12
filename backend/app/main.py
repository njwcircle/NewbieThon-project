from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import (
    agreements,
    auth,
    buildings,
    chat,
    contract_detail,
    contracts,
    dashboard,
    issues,
    legal,
    profile,
    push,
    repair_vendors,
    units,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NewbieThon API")

# 임시 테스트용 프론트(frontend-test/)에서 자유롭게 호출할 수 있게 개발 단계에서는 전체 허용.
# 실제 배포 시에는 allow_origins를 실제 프론트 도메인으로 좁혀야 한다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(buildings.router)
app.include_router(units.router)
app.include_router(contracts.router)
app.include_router(contract_detail.router)
app.include_router(profile.router)
app.include_router(repair_vendors.router)
app.include_router(agreements.router)
app.include_router(dashboard.router)
app.include_router(chat.router)
app.include_router(push.router)
app.include_router(issues.upload_router)
app.include_router(issues.router)
app.include_router(legal.router)
app.mount("/uploads", StaticFiles(directory="uploads", check_dir=False), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}
