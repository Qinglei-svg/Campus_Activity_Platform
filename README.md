# Campus Activity Platform

Local desktop application for a software engineering course project.

## Tech Stack

- Python 3.13
- PySide6
- SQLite
- SQLAlchemy

## Run

```powershell
python main.py
```

## Test

```powershell
python -m pytest tests -q
```

## Build

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

The generated desktop program is:

```text
dist\CampusActivityPlatform\CampusActivityPlatform.exe
```

Runtime data is stored next to the executable under `data\`.

## Stage 1

This stage provides the basic project structure, a PySide6 login screen, role-based quick login buttons, a main window, role-specific side menus, and placeholder pages.
