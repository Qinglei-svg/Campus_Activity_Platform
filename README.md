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

首次运行会在 `data/campus_activity.db` 中创建表并写入**默认账号**与**两批综合演示数据**（活动、报名、签到、评价、证书、通知、举报申诉等），分别以活动标题 **`[演示] 人工智能科普讲座`**（批次一）、**`[演示] 批次二-公开辩论邀请赛`**（批次二）为锚点；对应锚点已存在则跳过该批，互不干扰。

仅重建演示数据（不删库）时可执行：

```powershell
python -m database.seed_comprehensive_demo
```

演示账号密码均为 **`demo123456`**。批次一：`demo_li`、`demo_wang`、`demo_zhao`、`demo_qian`、`demo_pub2`。批次二：`demo_sun`、`demo_zhou`、`demo_wu`、`demo_zheng`、`demo_pub3`。执行 `python -m database.purge_sample_data` 会删除除 `admin` / `publisher` / `student` 外的所有用户及业务数据（含上述演示账号）。

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
