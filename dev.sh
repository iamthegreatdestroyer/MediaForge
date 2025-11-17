#!/bin/bash
# MediaForge Development Helper Script
set -e
CONTAINER="mediaforge-app"
case "$1" in
    build)
        echo "🔨 Building Docker containers..."
        docker-compose build
        ;;
    start)
        echo "🚀 Starting MediaForge..."
        docker-compose up -d
        docker-compose ps
        ;;
    stop)
        echo "🛑 Stopping MediaForge..."
        docker-compose down
        ;;
    restart)
        echo "🔄 Restarting MediaForge..."
        docker-compose restart
        ;;
    logs)
        echo "📋 Showing logs..."
        docker-compose logs -f
        ;;
    shell)
        echo "🐚 Opening shell in container..."
        docker exec -it $CONTAINER bash
        ;;
    test)
        echo "🧪 Running tests..."
        docker exec $CONTAINER pytest "${@:2}"
        ;;
    format)
        echo "✨ Formatting code..."
        docker exec $CONTAINER black src/ tests/
        ;;
    lint)
        echo "🔍 Linting code..."
        docker exec $CONTAINER flake8 src/ tests/
        ;;
    types)
        echo "📝 Type checking..."
        docker exec $CONTAINER mypy src/
        ;;
    scan)
        echo "📁 Scanning media..."
        docker exec $CONTAINER python -m src.cli.main scan "${@:2}"
        ;;
    cli)
        echo "💻 Running CLI command..."
        docker exec $CONTAINER python -m src.cli.main "${@:2}"
        ;;
    clean)
        echo "🧹 Cleaning up..."
        docker-compose down -v
        docker system prune -f
        ;;
    status)
        echo "📊 MediaForge Status:"
        docker-compose ps
        echo ""
        echo "Container Stats:"
        docker stats $CONTAINER --no-stream
        ;;
    *)
        echo "MediaForge Development Helper"
        echo ""
        echo "Usage: ./dev.sh <command>"
        echo ""
        echo "Commands:"
        echo "  build     - Build Docker containers"
        echo "  start     - Start MediaForge services"
        echo "  stop      - Stop MediaForge services"
        echo "  restart   - Restart MediaForge services"
        echo "  logs      - Show container logs"
        echo "  shell     - Open bash shell in container"
        echo "  test      - Run tests (add pytest args after)"
        echo "  format    - Format code with Black"
        echo "  lint      - Lint code with Flake8"
        echo "  types     - Type check with Mypy"
        echo "  scan      - Scan media directory"
        echo "  cli       - Run MediaForge CLI"
        echo "  clean     - Clean up containers and volumes"
        echo "  status    - Show container status"
        echo ""
        echo "Examples:"
        echo "  ./dev.sh build"
        echo "  ./dev.sh start"
        echo "  ./dev.sh test -v"
        echo "  ./dev.sh scan /media_library"
        echo "  ./dev.sh cli stats"
        ;;
 esac
