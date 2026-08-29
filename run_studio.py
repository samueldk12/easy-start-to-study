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
