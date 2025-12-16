"""Health check and status endpoints."""
from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "MediaForge API",
        "version": "0.2.0",
    }


@router.get("/ready")
async def readiness_check() -> dict:
    """Readiness check endpoint (for Kubernetes/orchestration).
    
    Returns:
        Readiness status
    """
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/")
async def root() -> dict:
    """API root endpoint with documentation links.
    
    Returns:
        API information
    """
    return {
        "name": "MediaForge API",
        "version": "0.2.0",
        "description": "Personal digital media library management",
        "docs": "/docs",
        "openapi_schema": "/openapi.json",
        "endpoints": {
            "media": "/api/v1/media",
            "tags": "/api/v1/tags",
            "collections": "/api/v1/collections",
        },
    }
