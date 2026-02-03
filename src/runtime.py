#!/usr/bin/env python3
"""Isolated runtime - Ollama on 11435, Chromium on 9223"""

import os
import subprocess
import time
from pathlib import Path

DATA_DIR = Path.home() / ".superpalmtree"
OLLAMA_PORT = 11435
CHROME_PORT = 9223


class Runtime:
    def __init__(self):
        self.ollama_proc = None
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / "models").mkdir(exist_ok=True)
        (DATA_DIR / "workspace").mkdir(exist_ok=True)

    def start_ollama(self) -> bool:
        """Start isolated Ollama on port 11435"""
        env = os.environ.copy()
        env["OLLAMA_HOST"] = f"127.0.0.1:{OLLAMA_PORT}"
        env["OLLAMA_MODELS"] = str(DATA_DIR / "models")

        # Check if already running
        try:
            import requests
            r = requests.get(f"http://127.0.0.1:{OLLAMA_PORT}/api/tags", timeout=2)
            if r.ok:
                return True
        except:
            pass

        # Start Ollama
        self.ollama_proc = subprocess.Popen(
            ["ollama", "serve"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for ready
        for _ in range(30):
            try:
                import requests
                if requests.get(f"http://127.0.0.1:{OLLAMA_PORT}/api/tags", timeout=1).ok:
                    return True
            except:
                pass
            time.sleep(1)
        return False

    def stop(self):
        if self.ollama_proc:
            self.ollama_proc.terminate()


# Singleton
_runtime = None

def get_runtime() -> Runtime:
    global _runtime
    if not _runtime:
        _runtime = Runtime()
    return _runtime
