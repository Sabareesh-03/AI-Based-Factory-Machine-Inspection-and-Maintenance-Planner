"""
AI-Based Factory Machine Inspection and Maintenance Planner
FastAPI Backend — Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.routers import health, machines, technicians, alerts, dashboard, inspection, planner, rules


# ── Startup / Shutdown ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB tables on startup (safe to call multiple times)."""
    from database.db import Base, engine
    import app.models  # noqa: F401 — registers all models with metadata
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables initialized")
    yield
    print("👋 Factory Maintenance Planner API shutting down")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Factory Maintenance Planner API",
    description=(
        "AI-powered decision-support system for factory maintenance management. "
        "Uses Intelligent Agents, Heuristic Search, CSP, and Rule-Based Reasoning."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router,       prefix="/api", tags=["Health"])
app.include_router(dashboard.router,    prefix="/api", tags=["Dashboard"])
app.include_router(machines.router,     prefix="/api", tags=["Machines"])
app.include_router(technicians.router,  prefix="/api", tags=["Technicians"])
app.include_router(alerts.router,       prefix="/api", tags=["Alerts"])
app.include_router(inspection.router,                   tags=["Inspection & Risk Analysis"])
app.include_router(planner.router,                      tags=["AI Problem Formulation & Heuristic Priority"])
app.include_router(rules.router,                        tags=["Knowledge-Based Rule Management & Explainable AI"])

# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Factory Maintenance Planner API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "endpoints": {
            "health":     "/api/health",
            "stats":      "/api/dashboard/stats",
            "machines":   "/api/machines",
            "technicians":"/api/technicians",
            "alerts":     "/api/alerts",
            "inspection": "/api/inspection/run-all",
            "planner":    "/api/planner/priority",
            "rules":      "/api/rules",
        },
    }
