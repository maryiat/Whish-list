#!/usr/bin/env python3
"""Simple multi-user wish list server.

Serves the SPA and exposes a tiny JSON API so multiple users share claim state.
"""

from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = 4173
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "wishes_data.json"
LOCK = threading.Lock()

DEFAULT_WISHES: list[dict[str, Any]] = [
    {"id": 1, "name": "Wireless Headphones", "image": "https://picsum.photos/seed/headphones/180/180", "claimed": False},
    {"id": 2, "name": "Kindle Paperwhite", "image": "https://picsum.photos/seed/kindle/180/180", "claimed": False},
    {"id": 3, "name": "Yoga Mat Set", "image": "https://picsum.photos/seed/yoga/180/180", "claimed": False},
    {"id": 4, "name": "Coffee Gift Box", "image": "https://picsum.photos/seed/coffee/180/180", "claimed": False},
    {"id": 5, "name": "Aromatherapy Diffuser", "image": "https://picsum.photos/seed/diffuser/180/180", "claimed": False},
    {"id": 6, "name": "Sketchbook Collection", "image": "https://picsum.photos/seed/sketchbook/180/180", "claimed": False},
    {"id": 7, "name": "Board Game Night Pack", "image": "https://picsum.photos/seed/boardgame/180/180", "claimed": False},
    {"id": 8, "name": "Travel Backpack", "image": "https://picsum.photos/seed/backpack/180/180", "claimed": False},
    {"id": 9, "name": "Smart Water Bottle", "image": "https://picsum.photos/seed/waterbottle/180/180", "claimed": False},
    {"id": 10, "name": "Mini Projector", "image": "https://picsum.photos/seed/projector/180/180", "claimed": False},
    {"id": 11, "name": "Cooking Class Voucher", "image": "https://picsum.photos/seed/cooking/180/180", "claimed": False},
    {"id": 12, "name": "Polaroid Camera", "image": "https://picsum.photos/seed/polaroid/180/180", "claimed": False},
    {"id": 13, "name": "Cozy Blanket", "image": "https://picsum.photos/seed/blanket/180/180", "claimed": False},
    {"id": 14, "name": "Plant Starter Kit", "image": "https://picsum.photos/seed/plants/180/180", "claimed": False},
    {"id": 15, "name": "Perfume Set", "image": "https://picsum.photos/seed/perfume/180/180", "claimed": False},
    {"id": 16, "name": "Spa Day Certificate", "image": "https://picsum.photos/seed/spa/180/180", "claimed": False},
    {"id": 17, "name": "Bluetooth Speaker", "image": "https://picsum.photos/seed/speaker/180/180", "claimed": False},
    {"id": 18, "name": "Custom Jewelry", "image": "https://picsum.photos/seed/jewelry/180/180", "claimed": False},
    {"id": 19, "name": "Weekend Getaway Bag", "image": "https://picsum.photos/seed/getaway/180/180", "claimed": False},
    {"id": 20, "name": "Art Museum Tickets", "image": "https://picsum.photos/seed/museum/180/180", "claimed": False},
]


def load_wishes() -> list[dict[str, Any]]:
    if not DATA_FILE.exists():
        save_wishes(DEFAULT_WISHES)
        return [dict(item) for item in DEFAULT_WISHES]

    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        return [dict(item) for item in DEFAULT_WISHES]

    return data


def save_wishes(wishes: list[dict[str, Any]]) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(wishes, file, indent=2)


class WishListHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def _write_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/wishes":
            with LOCK:
                wishes = load_wishes()
            self._write_json({"wishes": wishes})
            return

        if parsed.path == "/":
            self.path = "/index.html"

        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/wishes":
            self._write_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)

        try:
            payload = json.loads(raw.decode("utf-8"))
            wish_id = int(payload["id"])
            claimed = bool(payload["claimed"])
        except (ValueError, KeyError, json.JSONDecodeError):
            self._write_json({"error": "Invalid payload"}, HTTPStatus.BAD_REQUEST)
            return

        with LOCK:
            wishes = load_wishes()
            for wish in wishes:
                if wish["id"] == wish_id:
                    wish["claimed"] = claimed
                    save_wishes(wishes)
                    self._write_json({"ok": True, "wish": wish})
                    return

        self._write_json({"error": "Wish not found"}, HTTPStatus.NOT_FOUND)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), WishListHandler)
    print(f"Serving at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
