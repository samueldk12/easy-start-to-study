"""
StackStudio Entrypoint Script
Run this script to launch the StackStudio Web UI and API.
"""

import uvicorn
import webbrowser
import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Fix Windows asyncio proactor pipe close ResourceWarning/ValueError on SSE client disconnect
if sys.platform == "win32":
    import asyncio
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _orig_del = _ProactorBasePipeTransport.__del__
        def _safe_del(self):
            try:
                _orig_del(self)
            except Exception:
                pass
        _ProactorBasePipeTransport.__del__ = _safe_del
    except Exception:
        pass
    try:
        from asyncio.base_subprocess import BaseSubprocessTransport
        _orig_sub_del = BaseSubprocessTransport.__del__
        def _safe_sub_del(self):
            try:
                _orig_sub_del(self)
            except Exception:
                pass
        BaseSubprocessTransport.__del__ = _safe_sub_del
    except Exception:
        pass

def main():
    port = int(os.getenv("STUDIO_PORT", "5050"))
    host = os.getenv("STUDIO_HOST", "0.0.0.0")

    print("=" * 65)
    print(" [*] StackStudio: Data Engineering, MLOps, Backend & DevOps")
    print(f" Servidor iniciado em: http://localhost:{port}")
    print(" Pressione Ctrl+C para encerrar o servidor.")
    print("=" * 65)

    if "--no-browser" not in sys.argv:
        try:
            webbrowser.open(f"http://localhost:{port}")
        except Exception:
            pass

    uvicorn.run("studio.app:app", host=host, port=port, reload=False, log_level="info")

if __name__ == "__main__":
    main()
