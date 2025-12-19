"""FastAPI application factory and configuration."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.database import Database


class APIApp:
    """FastAPI application factory with dependency injection."""

    _app: FastAPI = None
    _db: Database = None

    @classmethod
    def create_app(cls) -> FastAPI:
        """Create and configure FastAPI application.
        
        Returns:
            Configured FastAPI application instance
        """
        if cls._app is not None:
            return cls._app

        # Initialize database
        cls._db = Database(settings.database_url)

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncGenerator:
            """Application lifespan context manager."""
            # Startup
            await cls._db.create_tables()
            yield
            # Shutdown
            # Cleanup if needed

        # Create FastAPI app
        cls._app = FastAPI(
            title="MediaForge API",
            description="Personal digital media library management",
            version="0.2.0",
            lifespan=lifespan,
            debug=settings.debug,
        )

        # Configure CORS
        cls._app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:8080"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Include routers
        from src.api.routers import media, tags, collections, health, search
        
        cls._app.include_router(health.router, tags=["health"])
        cls._app.include_router(media.router, prefix="/api/v1/media", tags=["media"])
        cls._app.include_router(tags.router, prefix="/api/v1/tags", tags=["tags"])
        cls._app.include_router(
            collections.router, prefix="/api/v1/collections", tags=["collections"]
        )
        cls._app.include_router(search.router, tags=["AI Features"])

        # Global exception handlers
        @cls._app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "type": type(exc).__name__,
                },
            )

        return cls._app

    @classmethod
    def get_db(cls) -> Database:
        """Get database instance.
        
        Returns:
            Database instance
            
        Raises:
            RuntimeError: If app not initialized
        """
        if cls._db is None:
            raise RuntimeError("App not initialized. Call create_app() first.")
        return cls._db


def get_app() -> FastAPI:
    """Get or create FastAPI application.
    
    Returns:
        FastAPI application instance
    """
    return APIApp.create_app()


def get_db() -> Database:
    """Dependency: Get database instance.
    
    Returns:
        Database instance
    """
    return APIApp.get_db()
