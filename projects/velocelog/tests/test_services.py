"""
=============================================================================
AUTOMATED END-TO-END SERVICE HEALTH & FUNCTIONAL TEST SUITE
Project: velocelog
=============================================================================
"""

import sys
import time
import socket
import urllib.request
import urllib.error
import json

ENABLED_TOOLS = set(['vscode'])
CUSTOM_PORTS = {}

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def check_tcp_port(host, port, timeout=3.0):
    start = time.time()
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True, (time.time() - start) * 1000
    except Exception as e:
        return False, str(e)


def check_http_endpoint(url, timeout=4.0):
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "StackStudio-Tester/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            latency = (time.time() - start) * 1000
            return True, f"HTTP {response.status} ({latency:.1f}ms)"
    except urllib.error.HTTPError as e:
        latency = (time.time() - start) * 1000
        if e.code in (200, 302, 401, 403, 404):
            return True, f"HTTP {e.code} ({latency:.1f}ms)"
        return False, f"HTTP Error {e.code}"
    except Exception as e:
        return False, str(e)


def run_all_tests():
    print("=" * 70)
    print(f" {Colors.BOLD}{Colors.CYAN}[*] STACKSTUDIO SERVICE TEST SUITE: VELOCELOG{Colors.END}")
    print("=" * 70)

    results = []

    for tool_id in sorted(ENABLED_TOOLS):
        port = CUSTOM_PORTS.get(tool_id)
        if port:
            ok, detail = check_tcp_port("localhost", port)
            results.append((tool_id, port, ok, detail))

    passed = sum(1 for r in results if r[2])
    total = len(results)

    print(f"\nTestes concluidos: {passed}/{total} serviços responsivos.")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
