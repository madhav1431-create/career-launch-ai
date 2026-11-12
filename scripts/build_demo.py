"""Export the synthetic dashboard for static hosting."""

import argparse
import json
from pathlib import Path

from api import ROOT, app


DEMO_MARKER = "<!-- STATIC_DEMO_DATA -->"
STATIC_POLICY = (
    '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
    "script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; "
    "form-action 'none'; base-uri 'none'\">"
)


def build_demo(output_dir):
    with app.test_client() as client:
        response = client.post("/demo")
        response_status = response.status_code
        data = response.get_json()
    if response_status != 200 or not data or not data.get("demo") or data.get("ai_enabled"):
        raise RuntimeError("The synthetic analysis could not be exported.")

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    if html.count(DEMO_MARKER) != 1 or html.count("<head>") != 1:
        raise RuntimeError("The dashboard must include one head and one static demo placeholder.")

    # Keep embedded JSON from closing the script element.
    payload = json.dumps(data, ensure_ascii=True, separators=(",", ":")).replace("<", "\\u003c")
    fixture = f'<script type="application/json" id="staticDemoData">{payload}</script>'
    html = html.replace("<head>", f"<head>\n{STATIC_POLICY}").replace(DEMO_MARKER, fixture)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(html, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    build_demo(parser.parse_args().output_dir)


if __name__ == "__main__":
    main()
