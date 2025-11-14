from pathlib import Path
import shutil, os

ROOT = Path(__file__).resolve().parent
def rm(p): 
    try:
        if p.is_dir(): shutil.rmtree(p)
        elif p.exists(): p.unlink()
    except Exception as e:
        print(f"skip {p}: {e}")

# __pycache__ and *.pyc
for d in ROOT.rglob("__pycache__"): rm(d)
for f in ROOT.rglob("*.pyc"): rm(f)

# build artifacts
rm(ROOT/"build"); rm(ROOT/"dist"); rm(ROOT/"tpsl_planner.spec")

# project + user matplotlib caches
rm(ROOT/".mplcache")
matp = Path(os.environ.get("LOCALAPPDATA",""))/"matplotlib"
rm(matp)

# app runtime data cache
rm(ROOT/"tpsl_planner"/"data"/"ticker_cache.json")

# per-user app config
rm(Path(os.environ.get("APPDATA",""))/"tpsl_planner")

print("✅ caches cleaned")
