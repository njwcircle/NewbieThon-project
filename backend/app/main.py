from fastapi import FastAPI

from .database import Base, engine
from .routers import (
    agreements,
    auth,
    buildings,
    chat,
    contract_detail,
    contracts,
    dashboard,
    profile,
    push,
    repair_vendors,
    units,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NewbieThon API")

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


@app.get("/health")
def health():
    return {"status": "ok"}
