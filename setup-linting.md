# Linting Setup for EcoFlow API

This project now includes comprehensive linting and code quality tools.

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
# Option 1: Use our scripts
.\install-linting.ps1          # PowerShell
python -m scripts install      # Python module
make install                   # Makefile (Unix/Linux)

# Option 2: Manual install
pip install -r requirements-lint.txt
pre-commit install
```

### 2. Run Linting (Choose Your Preferred Method)

#### 🎯 **Recommended: Use Scripts**
```powershell
# PowerShell (Windows)
.\scripts.ps1 lint      # Check only
.\scripts.ps1 fix       # Fix auto-fixable issues
.\scripts.ps1 all       # Run all checks
.\scripts.ps1 format    # Format code
```

```bash
# Batch files (Windows)
lint.bat lint
lint.bat fix
lint.bat all
lint.bat format
```

```bash
# Makefile (Unix/Linux/Mac)
make lint
make fix
make all
make format
```

```bash
# Python module (cross-platform)
python -m scripts lint
python -m scripts fix
python -m scripts all
python -m scripts format
```

#### 🔧 **Manual Commands**
```bash
# Check for issues
python -m ruff check custom_components/

# Auto-fix issues
python -m ruff check custom_components/ --fix

# Format code
python -m ruff format custom_components/

# Type checking
python -m mypy custom_components/

# Security check
python -m bandit -r custom_components/

# Run all checks
python -m pre_commit run --all-files
```

## 📋 Available Scripts & Commands

### 🎯 **Script Commands (All Platforms)**
| Command | PowerShell | Batch | Makefile | Python Module | Description |
|---------|------------|-------|----------|---------------|-------------|
| **lint** | `.\scripts.ps1 lint` | `lint.bat lint` | `make lint` | `python -m scripts lint` | Check code issues |
| **format** | `.\scripts.ps1 format` | `lint.bat format` | `make format` | `python -m scripts format` | Format code |
| **check** | `.\scripts.ps1 check` | `lint.bat check` | `make check` | `python -m scripts check` | Run all checks |
| **fix** | `.\scripts.ps1 fix` | `lint.bat fix` | `make fix` | `python -m scripts fix` | Fix auto-fixable issues |
| **type-check** | `.\scripts.ps1 type-check` | `lint.bat type-check` | `make type-check` | `python -m scripts type-check` | Type checking |
| **security** | `.\scripts.ps1 security` | `lint.bat security` | `make security` | `python -m scripts security` | Security check |
| **all** | `.\scripts.ps1 all` | `lint.bat all` | `make all` | `python -m scripts all` | Run all linting tools |
| **install** | `.\scripts.ps1 install` | `lint.bat install` | `make install` | `python -m scripts install` | Install dependencies |

### 🛠️ **Available Tools**

#### **Ruff** - Fast Python Linter & Formatter
- **Linting**: `ruff check .`
- **Formatting**: `ruff format .`
- **Auto-fix**: `ruff check . --fix`

### **MyPy** - Type Checking
- **Run**: `mypy custom_components/`
- **Config**: See `[tool.mypy]` in `pyproject.toml`

### **Bandit** - Security Linter
- **Run**: `bandit -r custom_components/`
- **Config**: See `[tool.bandit]` in `pyproject.toml`

### **Flake8** - Additional Linting
- **Run**: `flake8 custom_components/`
- **Focus**: Docstrings and additional checks

### **Pre-commit** - Git Hooks
- **Install**: `pre-commit install`
- **Run all**: `pre-commit run --all-files`
- **Run on specific file**: `pre-commit run --files custom_components/ecoflow_api/binary_sensor.py`

## 📁 Configuration Files

- **`pyproject.toml`** - Main configuration for all tools
- **`.pre-commit-config.yaml`** - Pre-commit hooks setup
- **`requirements-lint.txt`** - Linting dependencies

## 🔧 IDE Integration

### VSCode / Windsurf
Add to your settings.json:
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "charliermarsh.ruff",
  "editor.codeActionsOnSave": {
    "source.organizeImports.ruff": true
  },
  "python.linting.enabled": true,
  "python.linting.ruff.enabled": true,
  "python.linting.mypy.enabled": true
}
```

## 📊 Coverage
```bash
pytest --cov=custom_components --cov-report=html
```

## 🎯 Best Practices

1. **Run pre-commit before committing**: `pre-commit run --all-files`
2. **Fix Ruff issues automatically**: `ruff check . --fix`
3. **Check types regularly**: `mypy custom_components/`
4. **Monitor coverage**: Keep it above 80%
5. **Security checks**: Run `bandit` before releases

## 🐛 Common Issues

### Import Errors
- Add `__init__.py` files to packages
- Check `PYTHONPATH` includes project root

### Type Errors
- Add type hints to function signatures
- Use `typing` module for complex types
- Ignore specific errors with `# type: ignore`

### Formatting Issues
- Run `ruff format .` to fix automatically
- Configure line length in `pyproject.toml`

## 🔄 CI/CD Integration

Add to your CI pipeline:
```yaml
- name: Lint with Ruff
  run: |
    pip install ruff
    ruff check .
    ruff format --check .

- name: Type check with MyPy
  run: |
    pip install mypy
    mypy custom_components/

- name: Security check with Bandit
  run: |
    pip install bandit
    bandit -r custom_components/
```
