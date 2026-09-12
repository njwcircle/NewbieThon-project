from fastapi import FastAPI

from .database import Base, engine
from .routers import auth, buildings, contracts, units

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NewbieThon API")

app.include_router(auth.router)
app.include_router(buildings.router)
app.include_router(units.router)
app.include_router(contracts.router)


@app.get("/health")
def health():
    return {"status": "ok"}
