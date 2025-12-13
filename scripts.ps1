# EcoFlow API Linting Scripts
# Usage: .\scripts.ps1 [command]

param(
    [Parameter(Position=0)]
    [ValidateSet("lint", "format", "check", "fix", "type-check", "security", "all", "install")]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "🚀 EcoFlow API Linting Scripts" -ForegroundColor Green
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Yellow
    Write-Host "  lint        - Run ruff linting (check only)" -ForegroundColor Gray
    Write-Host "  format      - Format code with ruff" -ForegroundColor Gray
    Write-Host "  check       - Run all checks (lint + format check)" -ForegroundColor Gray
    Write-Host "  fix         - Fix auto-fixable issues" -ForegroundColor Gray
    Write-Host "  type-check  - Run mypy type checking" -ForegroundColor Gray
    Write-Host "  security    - Run bandit security check" -ForegroundColor Gray
    Write-Host "  all         - Run all linting tools" -ForegroundColor Gray
    Write-Host "  install     - Install linting dependencies" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Usage examples:" -ForegroundColor Yellow
    Write-Host "  .\scripts.ps1 lint" -ForegroundColor Gray
    Write-Host "  .\scripts.ps1 fix" -ForegroundColor Gray
    Write-Host "  .\scripts.ps1 all" -ForegroundColor Gray
}

function Invoke-Lint {
    Write-Host "🔍 Running ruff linting..." -ForegroundColor Yellow
    python -m ruff check custom_components/ --no-fix
}

function Invoke-Format {
    Write-Host "📝 Formatting code with ruff..." -ForegroundColor Yellow
    python -m ruff format custom_components/
}

function Invoke-Check {
    Write-Host "🔍 Running comprehensive checks..." -ForegroundColor Yellow
    Write-Host "Running ruff lint..." -ForegroundColor Cyan
    python -m ruff check custom_components/ --no-fix
    if ($LASTEXITCODE -ne 0) { return }

    Write-Host "Checking format..." -ForegroundColor Cyan
    python -m ruff format custom_components/ --check
    if ($LASTEXITCODE -ne 0) { return }

    Write-Host "✅ All checks passed!" -ForegroundColor Green
}

function Invoke-Fix {
    Write-Host "🔧 Fixing auto-fixable issues..." -ForegroundColor Yellow
    Write-Host "Running ruff fix..." -ForegroundColor Cyan
    python -m ruff check custom_components/ --fix
    if ($LASTEXITCODE -ne 0) { return }

    Write-Host "Formatting code..." -ForegroundColor Cyan
    python -m ruff format custom_components/

    Write-Host "✅ All issues fixed!" -ForegroundColor Green
}

function Invoke-TypeCheck {
    Write-Host "🔍 Running mypy type checking..." -ForegroundColor Yellow
    python -m mypy custom_components/
}

function Invoke-Security {
    Write-Host "🔒 Running bandit security check..." -ForegroundColor Yellow
    python -m bandit -r custom_components/
}

function Invoke-All {
    Write-Host "🚀 Running all linting tools..." -ForegroundColor Yellow

    Write-Host "`n📝 1. Formatting check..." -ForegroundColor Cyan
    python -m ruff format custom_components/ --check
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Format check failed" -ForegroundColor Red
        return
    }

    Write-Host "`n🔍 2. Linting..." -ForegroundColor Cyan
    python -m ruff check custom_components/ --no-fix
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Linting failed" -ForegroundColor Red
        return
    }

    Write-Host "`n🔍 3. Type checking..." -ForegroundColor Cyan
    python -m mypy custom_components/
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Type checking failed" -ForegroundColor Red
        return
    }

    Write-Host "`n🔒 4. Security check..." -ForegroundColor Cyan
    python -m bandit -r custom_components/
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Security check failed" -ForegroundColor Red
        return
    }

    Write-Host "`n✅ All checks passed!" -ForegroundColor Green
}

function Invoke-Install {
    Write-Host "📦 Installing linting dependencies..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    python -m pip install -r requirements-lint.txt
    python -m pre_commit install
    Write-Host "✅ Installation complete!" -ForegroundColor Green
}

# Main execution
switch ($Command) {
    "lint" { Invoke-Lint }
    "format" { Invoke-Format }
    "check" { Invoke-Check }
    "fix" { Invoke-Fix }
    "type-check" { Invoke-TypeCheck }
    "security" { Invoke-Security }
    "all" { Invoke-All }
    "install" { Invoke-Install }
    default { Show-Help }
}
