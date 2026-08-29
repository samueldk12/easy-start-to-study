import sys
import subprocess

def main():
    args = sys.argv[1:]
    mode = "all"
    if "--unit" in args:
        mode = "unit"
    elif "--integration" in args:
        mode = "integration"

    print("=" * 70)
    print(f" [*] EXECUTANDO SUITE DE TESTES: MODE={mode.upper()}")
    print("=" * 70)

    cmd = [sys.executable, "-m", "pytest"]
    if mode == "unit":
        cmd.extend(["-m", "unit"])
    elif mode == "integration":
        cmd.extend(["-m", "integration"])
    cmd.extend(["-v", "--tb=short"])

    res = subprocess.run(cmd)
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
