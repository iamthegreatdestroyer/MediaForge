"""FastAPI application entry point."""
import uvicorn
from pathlib import Path

from src.api.app import get_app
from src.core.config import settings


def main():
    """Main entry point for running the FastAPI server."""
    app = get_app()
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )


if __name__ == "__main__":
    main()
