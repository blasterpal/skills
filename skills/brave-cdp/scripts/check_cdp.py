#!/usr/bin/env python3
"""Check an existing CDP endpoint without launching or changing a browser."""

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener


def check(endpoint):
    parsed = urlsplit(endpoint)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Expected an HTTP(S) CDP endpoint")
    # Local debugging requests must not pass through an environment proxy.
    opener = build_opener(ProxyHandler({}))
    with opener.open(endpoint.rstrip("/") + "/json/version", timeout=3) as response:
        metadata = json.load(response)
    if not isinstance(metadata, dict):
        raise ValueError("CDP metadata is not an object")
    websocket = metadata.get("webSocketDebuggerUrl")
    if not isinstance(websocket, str):
        raise ValueError("CDP metadata has no browser WebSocket URL")
    address = urlsplit(websocket)
    if address.scheme not in ("ws", "wss") or not address.hostname:
        raise ValueError("CDP metadata has an invalid browser WebSocket URL")
    return {"endpoint": endpoint, "browser": metadata.get("Browser"),
            "webSocketDebuggerUrl": websocket}


def main():
    if len(sys.argv) > 2:
        print("usage: check_cdp.py [http://127.0.0.1:9222]", file=sys.stderr)
        return 2
    endpoint = sys.argv[1] if len(sys.argv) == 2 else "http://127.0.0.1:9222"
    try:
        result = check(endpoint)
    except (HTTPError, URLError, OSError, ValueError) as error:
        print(f"CDP unavailable at {endpoint}: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
