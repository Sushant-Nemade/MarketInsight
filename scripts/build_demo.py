import json
from pathlib import Path

from MarketInsight.sample import sample_reports


def main():
    destination = Path(__file__).resolve().parents[1] / "frontend/public/demo.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            [report.model_dump(mode="json") for report in sample_reports()], indent=2, ensure_ascii=False
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("Built three explicitly fictional reference reports")


if __name__ == "__main__":
    main()
