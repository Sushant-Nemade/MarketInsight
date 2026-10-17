import json
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def main():
    wheels = list((ROOT / "dist").glob("market_insight_workbench-*.whl"))
    sources = list((ROOT / "dist").glob("market_insight_workbench-*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise ValueError("Expected one workbench wheel and one complete source archive")
    with zipfile.ZipFile(wheels[0]) as wheel:
        names = wheel.namelist()
        for required in [
            "main.py",
            "MarketInsight/web/index.html",
            "MarketInsight/web/demo.json",
            "MarketInsight/web/third-party-licenses/index.json",
        ]:
            if required not in names:
                raise ValueError("Missing installed application resource: " + required)
        for legal in ["LICENSE", "NOTICE.md"]:
            if not any(name.endswith("/licenses/" + legal) for name in names):
                raise ValueError("Missing distribution legal notice")
        if len(json.loads(wheel.read("MarketInsight/web/third-party-licenses/index.json"))) != 9:
            raise ValueError("Incomplete deployed production dependency notices")
    with tarfile.open(sources[0]) as archive:
        names = archive.getnames()
        for required in [
            "frontend/package-lock.json",
            "frontend/src/Workspace.tsx",
            "frontend/tests/workspace.spec.ts",
            "tests/test_api.py",
            "scripts/verify_release.py",
            "Dockerfile",
            "docs/OPERATIONS.md",
        ]:
            if not any(name.endswith("/" + required) for name in names):
                raise ValueError("Source archive lacks corresponding build/test material: " + required)
        for name in names:
            base = PurePosixPath(name).name
            if (
                (base.startswith(".env") and base != ".env.example")
                or base.endswith((".sqlite", ".pem"))
                or "/node_modules/" in name
                or "/.venv/" in name
            ):
                raise ValueError("Private state or unnecessary dependencies in distribution")
    with tempfile.TemporaryDirectory(prefix="market-wheel-") as directory:
        site = Path(directory) / "site"
        installed = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-deps", "--target", str(site), str(wheels[0])],
            capture_output=True,
            text=True,
            timeout=90,
        )
        installed.check_returncode()
        code = f"import sys;sys.path.insert(0,{str(site)!r});from pathlib import Path;import main;assert Path(main.__file__).is_relative_to(Path({str(site)!r}));from fastapi.testclient import TestClient;client=TestClient(main.create_app());assert client.get('/health').status_code==200;assert client.get('/').status_code==200;assert client.get('/demo.json').status_code==200;assert client.get('/api/reports').status_code==503;print('Installed wheel serves UI and API without credentials')"
        subprocess.run([sys.executable, "-I", "-c", code], cwd=directory, check=True, timeout=30)
    print("Source completeness, GPL notices and installed application verified")


if __name__ == "__main__":
    main()
