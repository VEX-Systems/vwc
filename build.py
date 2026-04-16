from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC_ENTRY = ROOT / "scripts" / "launcher.py"
NAME = "VolumeWheelControl"


def main() -> int:
    if not SRC_ENTRY.exists():
        print(f"Entry not found: {SRC_ENTRY}", file=sys.stderr)
        return 1

    dist = ROOT / "dist"
    build_dir = ROOT / "build"
    for path in (dist, build_dir):
        if path.exists():
            shutil.rmtree(path)
    dist.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--onefile",
        "--assume-yes-for-downloads",
        "--enable-plugin=pyqt6",
        "--windows-console-mode=disable",
        f"--output-dir={dist}",
        f"--output-filename={NAME}.exe",
        "--windows-company-name=Volume Wheel Control",
        "--windows-product-name=Volume Wheel Control",
        "--windows-file-version=0.1.0.0",
        "--windows-product-version=0.1.0.0",
        "--windows-file-description=Programmable macros for keyboard volume knobs",
        "--include-package=volume_wheel_control",
        "--include-package=qfluentwidgets",
        "--include-package-data=qfluentwidgets",
        f"--include-data-dir={ROOT / 'src' / 'volume_wheel_control'}=volume_wheel_control",
        "--remove-output",
        str(SRC_ENTRY),
    ]
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(ROOT), env=env)


if __name__ == "__main__":
    sys.exit(main())
