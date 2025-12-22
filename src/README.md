# GPO Autofish - Source Code Structure

This directory contains the refactored source code for GPO Autofish, organized into modular components.

## Python Version Requirement

**IMPORTANT**: This application requires **Python 3.12 or 3.13 only**.

- ❌ Python 3.14+ is NOT supported due to package compatibility issues
- ✅ Use Python 3.13.0 (recommended) or Python 3.12.7

## File Structure

- `main.py` - Entry point for the application
- `gui.py` - Main GUI class and UI components
- `fishing.py` - Fishing bot logic and auto-purchase system
- `overlay.py` - Overlay window management
- `webhook.py` - Discord webhook notifications
- `updater.py` - Auto-update functionality
- `settings.py` - Settings management (save/load/presets)
- `utils.py` - Utility classes (ToolTip, CollapsibleFrame)

## Running the Application

From the project root directory:

**Development mode (with console, macOS):**

```
./run_dev.sh
```

or explicitly use the venv Python:

```
./.venv/bin/python src/main.py
```

**Silent mode (no console, macOS):**

```
nohup python3 src/main.py >/dev/null 2>&1 &
```

or use the shell script:

```
./run.sh
```

## Building Application

Use the provided shell script:

```
./MakeItAPP.sh
```

This will create a standalone executable in the `dist/` folder.
