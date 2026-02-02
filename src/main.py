#!/usr/bin/env python3
"""
SuperPalmTree - Zero Setup AI Agent
Complete self-contained app with embedded Ollama + Model + Web UI
No external dependencies - everything bundled and works immediately
"""

import os
import sys
import json
import time
import http.server
import socketserver
import threading
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import psutil

# Configuration
APP_NAME = "SuperPalmTree"
APP_VERSION = "1.0.0"
SANDBOX_DIR = Path.home() / "superpalmtree-exp"
CONFIG_DIR = Path.home() / ".superpalmtree"
OLLAMA_PORT = 11434

# Paths to bundled binaries (relative to the app bundle)
BUNDLE_DIR = Path(__file__).parent.parent / "embedded"

# Bundled model path (embed in the executable)
BUNDLED_MODEL = BUNDLE_DIR / "models" / "qwen3-1.7b.gguf"


def get_platform() -> str:
    """Get current platform"""
    if sys.platform.startswith("linux"):
        return "linux"
    elif sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"
    return "linux"


def detect_hardware() -> Dict[str, Any]:
    """Detect RAM and set appropriate model"""
    ram_gb = psutil.virtual_memory().total / (1024**3)
    
    # Use 1.7b model for 4GB+ RAM (what we bundle)
    # For systems with more RAM, this still works well
    if ram_gb >= 16:
        model = "qwen3:8b"
        ctx = 32768
    elif ram_gb >= 8:
        model = "qwen3:4b"
        ctx = 16384
    else:
        model = "qwen3:1.7b"
        ctx = 8192
    
    return {"ram_gb": round(ram_gb, 1), "model": model, "context_size": ctx}


class OllamaManager:
    """Manages bundled Ollama instance - fully self-contained"""
    
    def __init__(self):
        self.process = None
        self.platform = get_platform()
        self.model_name = None
        self.context_size = None
        self.model_ready = False
        # Status fields exposed to the Web UI
        self.phase = "starting"
        self.status_message = "Starting bundled Ollama..."
        self.progress = 0  # 0–100, mainly used during downloads
        
        SANDBOX_DIR.mkdir(exist_ok=True)
        CONFIG_DIR.mkdir(exist_ok=True)
    
    def get_ollama_binary(self) -> Optional[Path]:
        """Get bundled Ollama binary path"""
        platform_paths = {
            "linux": BUNDLE_DIR / "bin" / "linux" / "ollama",
            "macos": BUNDLE_DIR / "bin" / "macos" / "ollama",
            "windows": BUNDLE_DIR / "bin" / "windows" / "ollama.exe",
        }
        
        path = platform_paths.get(self.platform)
        if path and path.exists():
            path.chmod(0o755)
            return path
        
        # Also check flat structure
        alt_path = BUNDLE_DIR / "ollama"
        if alt_path.exists():
            alt_path.chmod(0o755)
            return alt_path
        
        return None
    
    def is_running(self) -> bool:
        """Check if Ollama is responding"""
        try:
            import urllib.request
            urllib.request.urlopen(f"http://127.0.0.1:{OLLAMA_PORT}/api/tags", timeout=2)
            return True
        except:
            return False
    
    def start(self) -> bool:
        """Start bundled Ollama - no external dependencies"""
        if self.is_running():
            print("Ollama already running")
            self.phase = "running"
            self.status_message = "Ollama already running"
            self.progress = 100
            return True
        
        ollama_path = self.get_ollama_binary()
        if not ollama_path:
            print("ERROR: Ollama binary not found in embedded/bin/")
            print(f"Expected: {ollama_path}")
            self.phase = "error"
            self.status_message = "Bundled Ollama binary not found"
            self.progress = 0
            return False
        
        print(f"Starting bundled Ollama from: {ollama_path}")
        
        env = os.environ.copy()
        env["OLLAMA_HOST"] = f"127.0.0.1:{OLLAMA_PORT}"
        env["OLLAMA_MODELS"] = str(CONFIG_DIR / "models")
        
        try:
            self.process = subprocess.Popen(
                [str(ollama_path), "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env
            )
            
            self.phase = "starting_ollama"
            self.status_message = "Starting embedded Ollama server..."
            self.progress = 10

            # Wait for Ollama to be ready
            for i in range(30):
                time.sleep(1)
                if self.is_running():
                    print("Ollama ready")
                    self.phase = "ollama_ready"
                    self.status_message = "Ollama server is running"
                    self.progress = 30
                    return True
            
            print("Ollama failed to start")
            self.phase = "error"
            self.status_message = "Failed to start Ollama"
            self.progress = 0
            return False
        except Exception as e:
            print(f"Error starting Ollama: {e}")
            self.phase = "error"
            self.status_message = f"Error starting Ollama: {e}"
            self.progress = 0
            return False
    
    def _download_model(self) -> bool:
        """
        Best-effort fallback: download the model if it was not bundled.
        This is only used when the embedded GGUF is missing (e.g. dev builds).
        """
        import urllib.request

        BUNDLED_MODEL.parent.mkdir(parents=True, exist_ok=True)

        url = (
            "https://huggingface.co/bartowski/qwen3-1.7b-GGUF/resolve/main/"
            "qwen3-1.7b-q4_0.gguf"
        )

        print(f"Downloading model from {url}")
        self.phase = "downloading_model"
        self.status_message = "Downloading model (first run on this machine)..."
        self.progress = 35

        try:
            with urllib.request.urlopen(url, timeout=600) as response, open(
                BUNDLED_MODEL, "wb"
            ) as out_file:
                total = int(response.headers.get("Content-Length", "0") or "0")
                downloaded = 0
                chunk_size = 1024 * 1024

                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        percent = int(downloaded * 100 / total)
                        # Console-only progress; UI polls status_message
                        print(f"\rDownloading model... {percent}% ", end="", flush=True)
                        self.progress = max(35, min(90, percent))

            print("\nModel download complete")
            self.status_message = "Model downloaded. Preparing model..."
            self.progress = 90
            return True
        except Exception as e:
            print(f"\nFailed to download model: {e}")
            self.phase = "error"
            self.status_message = (
                "Failed to download model. Please check your network or reinstall."
            )
            self.progress = 0
            return False

    def ensure_model(self) -> bool:
        """Load bundled model; download once if it was not bundled."""
        if not BUNDLED_MODEL.exists():
            print(f"Bundled model not found at {BUNDLED_MODEL}")
            # Best effort: download the model so a fresh system still works
            if not self._download_model():
                return False
        
        print(f"Loading model file: {BUNDLED_MODEL.name}")
        self.phase = "preparing_model"
        self.status_message = "Preparing local model..."
        # If we got here without download, jump progress a bit ahead.
        if self.progress < 40:
            self.progress = 40
        
        # Create Modelfile for the embedded model
        modelfile_content = f"""FROM {BUNDLED_MODEL}
PARAMETER num_ctx {self.context_size}
PARAMETER temperature 0.7
"""
        
        modelfile_path = CONFIG_DIR / "Modelfile"
        modelfile_path.write_text(modelfile_content)
        
        # Create model from file
        ollama_path = self.get_ollama_binary()
        if not ollama_path:
            return False
        
        print(f"Creating model '{self.model_name}' from embedded file...")
        
        result = subprocess.run(
            [str(ollama_path), "create", self.model_name, "-f", str(modelfile_path)],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode == 0:
            print(f"Model {self.model_name} ready")
            self.model_ready = True
            self.phase = "ready"
            self.status_message = "Model ready. You can start chatting."
            self.progress = 100
            return True
        else:
            print(f"Model creation failed: {result.stderr}")
            self.phase = "error"
            self.status_message = "Failed to prepare model"
            self.progress = 0
            return False
    
    def chat(self, message: str) -> str:
        """Send message to LLM and get response"""
        try:
            import urllib.request
            
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": message}],
                "stream": False,
                "options": {
                    "num_ctx": self.context_size
                }
            }
            
            req = urllib.request.Request(
                f"http://127.0.0.1:{OLLAMA_PORT}/api/chat",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode())
                return data.get("message", {}).get("content", "No response")
                
        except Exception as e:
            return f"Error: {e}"
    
    def stop(self):
        """Stop Ollama"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                self.process.kill()


class WebUI:
    """Serves the web UI and handles API requests"""
    
    def __init__(self, ollama: OllamaManager, port: int = 8080):
        self.ollama = ollama
        self.port = port
        self.static_dir = Path(__file__).parent.parent / "static"
    
    def start(self):
        """Start web server in background thread"""
        handler = self.create_handler()
        server = socketserver.TCPServer(("", self.port), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(f"Web UI: http://localhost:{self.port}")
        return server


class APIHandler(http.server.SimpleHTTPRequestHandler):
    """Handle API requests for the AI agent"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent.parent / "static"), **kwargs)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/api/chat":
            self.handle_chat()
        else:
            self.send_error(404)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/api/status":
            self.handle_status()
        else:
            super().do_GET()
    
    def handle_chat(self):
        """Handle chat API request"""
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            message = data.get("message", "")
            
            # Get Ollama instance from global
            ollama = getattr(APIHandler, 'ollama', None)
            if ollama and ollama.model_ready:
                response = ollama.chat(message)
            else:
                response = "Error: Model not ready"
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"response": response}).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def handle_status(self):
        """Return system status"""
        ollama = getattr(APIHandler, 'ollama', None)
        status = {
            "ready": ollama.model_ready if ollama else False,
            "model": ollama.model_name if ollama else None,
            "phase": getattr(ollama, "phase", None) if ollama else None,
            "status_message": getattr(ollama, "status_message", "Starting...") if ollama else "Starting...",
            "progress": getattr(ollama, "progress", 0) if ollama else 0,
        }
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(status).encode())
    
    def log_message(self, format, *args):
        """Suppress logging"""
        pass


def main():
    """Main entry point - zero setup, just works"""
    print(f"\n{'='*50}")
    print(f"  {APP_NAME} v{APP_VERSION}")
    print(f"  Zero Setup AI Agent")
    print(f"{'='*50}\n")
    
    # Detect hardware
    print("Detecting hardware...")
    hw = detect_hardware()
    print(f"  RAM: {hw['ram_gb']}GB")
    
    # Initialize Ollama
    ollama = OllamaManager()
    ollama.model_name = hw["model"]
    ollama.context_size = hw["context_size"]
    
    print("\nStarting bundled Ollama...")
    if not ollama.start():
        print("\nERROR: Failed to start Ollama")
        print("Please ensure the bundled Ollama binary is included.")
        sys.exit(1)
    
    print("\nLoading bundled model...")
    if not ollama.ensure_model():
        print("\nERROR: Failed to load model")
        sys.exit(1)
    
    # Setup API handler with Ollama reference
    APIHandler.ollama = ollama
    
    # Start web UI
    print("\nStarting web interface...")
    webui = WebUI(ollama, port=8080)
    server = webui.start()
    
    print(f"\n{'='*50}")
    print("  Ready! Open: http://localhost:8080")
    print(f"{'='*50}\n")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        ollama.stop()
        server.shutdown()


if __name__ == "__main__":
    main()
