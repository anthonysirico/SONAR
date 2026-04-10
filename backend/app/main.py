from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import db
from app.routers import graph, ingest, reports, cases, sources

app = FastAPI(
    title="SONAR",
    description="Suspicious Organization and Network Analysis & Reporting",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])
app.include_router(cases.router, prefix="/api/cases", tags=["Cases"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["Ingest"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(sources.router, prefix="/api/sources", tags=["Sources"])

@app.on_event("startup")
async def startup():
    db.verify()

@app.on_event("shutdown")
async def shutdown():
    db.close()

@app.get("/")
async def root():
    return {"status": "SONAR online"}