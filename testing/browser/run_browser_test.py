
import subprocess
import sys
from pathlib import Path

ROOT = Path(
    "/content/drive/MyDrive/"
    "FutureMind_Lab_V7_RC2_LANGUAGE_FULL_FIX_WORKING_20260807"
)

RUNTIME = (
    ROOT /
    "testing" /
    "browser" /
    "runtime_check.py"
)

print("=" * 70)
print("FUTUREMIND V7 RC2 — BROWSER TEST LAUNCHER")
print("=" * 70)

result = subprocess.run(
    [sys.executable, str(RUNTIME)],
    text=True
)

sys.exit(result.returncode)
