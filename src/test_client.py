"""Test client that connects to the MCP server over SSE and exercises the protocol."""

import json
import threading
import time

import requests

SERVER_URL = "http://localhost:5050"


def listen_sse(session_id_holder, responses, stop_event):
    """Background thread: holds the SSE connection open and collects responses."""
    with requests.get(f"{SERVER_URL}/sse", stream=True, timeout=30) as r:
        for line in r.iter_lines(decode_unicode=True):
            if stop_event.is_set():
                break
            if not line:
                continue
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = line.split(":", 1)[1].strip()
                if event_type == "endpoint":
                    sid = data.split("session_id=")[1]
                    session_id_holder.append(sid)
                elif event_type == "message":
                    responses.append(json.loads(data))


def send_rpc(session_id, method, params, req_id):
    """Send a JSON-RPC request to the server."""
    payload = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method,
        "params": params,
    }
    requests.post(
        f"{SERVER_URL}/messages/?session_id={session_id}",
        json=payload,
        timeout=10,
    )


def main():
    session_id_holder = []
    responses = []
    stop_event = threading.Event()

    listener = threading.Thread(
        target=listen_sse, args=(session_id_holder, responses, stop_event), daemon=True,
    )
    listener.start()

    while not session_id_holder:
        time.sleep(0.1)
    session_id = session_id_holder[0]
    print(f"Connected. Session: {session_id}\n")

    # 1. Initialize
    print("--- Step 1: initialize ---")
    send_rpc(session_id, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0"},
    }, req_id=1)
    time.sleep(1)
    print(json.dumps(responses[-1], indent=2))

    # 2. Notify initialized
    requests.post(
        f"{SERVER_URL}/messages/?session_id={session_id}",
        json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        timeout=10,
    )

    # 3. List tools
    print("\n--- Step 2: tools/list ---")
    send_rpc(session_id, "tools/list", {}, req_id=2)
    time.sleep(1)
    tools = responses[-1]["result"]["tools"]
    for t in tools:
        print(f"  - {t['name']}: {t['description'][:60]}...")

    # 4. Call a tool
    print("\n--- Step 3: tools/call (get_mfi) ---")
    send_rpc(session_id, "tools/call", {
        "name": "get_mfi",
        "arguments": {"interval": "1d", "period": 5},
    }, req_id=3)
    time.sleep(3)
    result = json.loads(responses[-1]["result"]["content"][0]["text"])
    print(json.dumps(result, indent=2))

    stop_event.set()
    print("\nDone.")


if __name__ == "__main__":
    main()
