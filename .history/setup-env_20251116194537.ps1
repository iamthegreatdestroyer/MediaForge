# MediaForge Development Environment Setup Script
# Run this script to create/update the Python virtual environment

param(
    [switch]$Force,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$venvPath = Join-Path $PSScriptRoot '.venv'

# Prefer Python 3.11 (project target) if available via py launcher; fallback to current python
$pythonCmd = 'python'
try {
    & py -3.11 -V *> $null
    if ($LASTEXITCODE -eq 0) {
        $pythonCmd = 'py -3.11'
        Write-Host "🔍 Using Python 3.11 interpreter" -ForegroundColor Green
    } else {
        Write-Host "🔍 Python 3.11 not found, using default interpreter ($(& python -V))" -ForegroundColor Yellow
    }
} catch {
    Write-Host "🔍 Python 3.11 not found, using default interpreter ($(& python -V))" -ForegroundColor Yellow
}

Write-Host "MediaForge Environment Setup" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# Remove existing venv if Force flag is set
if ($Force -and (Test-Path $venvPath)) {
    Write-Host "🗑️  Removing existing virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $venvPath
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path $venvPath)) {
    Write-Host "📦 Creating virtual environment with $pythonCmd..." -ForegroundColor Green
    & $pythonCmd -m venv $venvPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Virtual environment created at $venvPath" -ForegroundColor Green
}
else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate the virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Green
& "$venvPath\Scripts\Activate.ps1"

if (-not $SkipInstall) {
    # Upgrade pip, setuptools, and wheel
    Write-Host "⬆️  Upgrading pip, setuptools, and wheel..." -ForegroundColor Green
    python -m pip install --upgrade pip setuptools wheel --quiet
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Warning: Failed to upgrade pip tooling" -ForegroundColor Yellow
    }
    
    # Install requirements
    $requirementsFile = Join-Path $PSScriptRoot 'requirements.txt'
    
    if (Test-Path $requirementsFile) {
        Write-Host "📥 Installing dependencies from requirements.txt..." -ForegroundColor Green
        pip install -r $requirementsFile
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "✅ All dependencies installed successfully" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  Warning: requirements.txt not found" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🚀 Environment ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  • To reactivate later: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
if (($pythonCmd -eq 'python') -and ((python -V) -notmatch '3\.11')) {
    Write-Host "  • Recommended: Install Python 3.11 for pinned dependencies (winget install -e --id Python.Python.3.11) then re-run: ./setup-env.ps1 -Force" -ForegroundColor Yellow
}
Write-Host "  • Run tests: pytest tests/ -v" -ForegroundColor White
Write-Host "  • Format code: black src/ tests/" -ForegroundColor White
Write-Host "  • Type check: mypy src/" -ForegroundColor White
Write-Host "  • Lint: flake8 src/ tests/" -ForegroundColor White
Write-Host ""
