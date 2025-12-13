@echo off
REM EcoFlow API Linting Scripts for Windows
REM Usage: lint.bat [command]

setlocal enabledelayedexpansion

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="lint" goto lint
if "%1"=="format" goto format
if "%1"=="check" goto check
if "%1"=="fix" goto fix
if "%1"=="type-check" goto type-check
if "%1"=="security" goto security
if "%1"=="all" goto all
if "%1"=="install" goto install
goto help

:help
echo 🚀 EcoFlow API Linting Scripts
echo.
echo Available commands:
echo   lint        - Run ruff linting (check only)
echo   format      - Format code with ruff
echo   check       - Run all checks (lint + format check)
echo   fix         - Fix auto-fixable issues
echo   type-check  - Run mypy type checking
echo   security    - Run bandit security check
echo   all         - Run all linting tools
echo   install     - Install linting dependencies
echo.
echo Usage examples:
echo   lint.bat lint
echo   lint.bat fix
echo   lint.bat all
goto end

:lint
echo 🔍 Running ruff linting...
python -m ruff check custom_components/ --no-fix
goto end

:format
echo 📝 Formatting code with ruff...
python -m ruff format custom_components/
goto end

:check
echo 🔍 Running comprehensive checks...
echo Running ruff lint...
python -m ruff check custom_components/ --no-fix
if !errorlevel! neq 0 goto end
echo Checking format...
python -m ruff format custom_components/ --check
if !errorlevel! neq 0 goto end
echo ✅ All checks passed!
goto end

:fix
echo 🔧 Fixing auto-fixable issues...
echo Running ruff fix...
python -m ruff check custom_components/ --fix
if !errorlevel! neq 0 goto end
echo Formatting code...
python -m ruff format custom_components/
echo ✅ All issues fixed!
goto end

:type-check
echo 🔍 Running mypy type checking...
python -m mypy custom_components/
goto end

:security
echo 🔒 Running bandit security check...
python -m bandit -r custom_components/
goto end

:all
echo 🚀 Running all linting tools...
echo.
echo 📝 1. Formatting check...
python -m ruff format custom_components/ --check
if !errorlevel! neq 0 (
    echo ❌ Format check failed
    goto end
)
echo.
echo 🔍 2. Linting...
python -m ruff check custom_components/ --no-fix
if !errorlevel! neq 0 (
    echo ❌ Linting failed
    goto end
)
echo.
echo 🔍 3. Type checking...
python -m mypy custom_components/
if !errorlevel! neq 0 (
    echo ❌ Type checking failed
    goto end
)
echo.
echo 🔒 4. Security check...
python -m bandit -r custom_components/
if !errorlevel! neq 0 (
    echo ❌ Security check failed
    goto end
)
echo.
echo ✅ All checks passed!
goto end

:install
echo 📦 Installing linting dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements-lint.txt
python -m pre_commit install
echo ✅ Installation complete!
goto end

:end
endlocal
