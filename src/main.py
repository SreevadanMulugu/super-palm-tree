#!/usr/bin/env python3
"""
AgentSmith - Zero Setup AI Agent
Single-file agent that "just works" with embedded Ollama and headless browser
"""

import os
import sys
import json
import time
import psutil
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration
APP_NAME = "AgentSmith"
APP_VERSION = "1.0.0"
SANDBOX_DIR = Path.home() / "agentsmith-exp"
CONFIG_DIR = Path.home() / ".agentsmith"
OLLAMA_PORT = 11434


class AgentSmith:
    """Main agent class - zero setup, just works"""
    
    def __init__(self):
        self.ollama_process = None
        self.browser_process = None
        self.model_name = None
        self.context_size = None
        self.config = {}
        
        # Ensure directories exist
        SANDBOX_DIR.mkdir(exist_ok=True)
        CONFIG_DIR.mkdir(exist_ok=True)
        
    def detect_hardware(self) -> Dict[str, Any]:
        """Detect RAM and set appropriate model/context"""
        ram_gb = psutil.virtual_memory().total / (1024**3)
        
        if ram_gb >= 16:
            model = "qwen3:8b"
            ctx = 32768
        elif ram_gb >= 8:
            model = "qwen3:4b"
            ctx = 16384
        elif ram_gb >= 4:
            model = "qwen3:1.7b"
            ctx = 8192
        else:
            model = "qwen3:0.6b"
            ctx = 4096
            
        return {
            "ram_gb": ram_gb,
            "model": model,
            "context_size": ctx
        }
    
    def start_ollama(self) -> bool:
        """Start embedded Ollama server"""
        try:
            # Check if Ollama is already running
            result = subprocess.run(
                ["curl", "-s", f"http://localhost:{OLLAMA_PORT}/api/tags"],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                print("✓ Ollama already running")
                return True
        except:
            pass
        
        # Start Ollama
        print("Starting Ollama server...")
        env = os.environ.copy()
        env["OLLAMA_HOST"] = f"127.0.0.1:{OLLAMA_PORT}"
        
        self.ollama_process = subprocess.Popen(
            ["ollama", "serve"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Wait for server to be ready
        for i in range(30):
            try:
                result = subprocess.run(
                    ["curl", "-s", f"http://localhost:{OLLAMA_PORT}/api/tags"],
                    capture_output=True,
                    timeout=1
                )
                if result.returncode == 0:
                    print("✓ Ollama ready")
                    return True
            except:
                pass
            time.sleep(1)
        
        print("✗ Failed to start Ollama")
        return False
    
    def pull_model(self, model: str) -> bool:
        """Pull required model"""
        print(f"Pulling model: {model}...")
        result = subprocess.run(
            ["ollama", "pull", model],
            capture_output=True
        )
        if result.returncode == 0:
            print(f"✓ Model {model} ready")
            return True
        return False
    
    def chat(self, message: str) -> str:
        """Send message to Ollama and get response"""
        import requests
        
        url = f"http://localhost:{OLLAMA_PORT}/api/generate"
        data = {
            "model": self.model_name,
            "prompt": message,
            "stream": False,
            "options": {
                "num_ctx": self.context_size
            }
        }
        
        try:
            response = requests.post(url, json=data, timeout=300)
            if response.status_code == 200:
                return response.json().get("response", "")
            return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {e}"
    
    def run(self):
        """Main run loop"""
        print(f"\n{'='*50}")
        print(f"  {APP_NAME} v{APP_VERSION}")
        print(f"{'='*50}\n")
        
        # Detect hardware
        hw = self.detect_hardware()
        print(f"Detected: {hw['ram_gb']:.1f}GB RAM")
        print(f"Model: {hw['model']}")
        print(f"Context: {hw['context_size']} tokens\n")
        
        self.model_name = hw['model']
        self.context_size = hw['context_size']
        
        # Start Ollama
        if not self.start_ollama():
            print("Please install Ollama: curl -fsSL https://ollama.com/install.sh | sh")
            return
        
        # Pull model if needed
        self.pull_model(self.model_name)
        
        # Interactive mode
        print(f"\n{APP_NAME} ready! Type 'exit' to quit.\n")
        
        while True:
            try:
                user_input = input("> ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                
                # Process request
                print(f"\nThinking...")
                response = self.chat(user_input)
                print(f"\n{response}\n")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.ollama_process:
            self.ollama_process.terminate()


def main():
    """Entry point"""
    agent = AgentSmith()
    
    try:
        # Check for command line arguments
        if len(sys.argv) > 1:
            # Single command mode
            command = ' '.join(sys.argv[1:])
            print(f"\n{APP_NAME} v{APP_VERSION}")
            
            hw = agent.detect_hardware()
            agent.model_name = hw['model']
            agent.context_size = hw['context_size']
            
            if not agent.start_ollama():
                print("Please install Ollama first")
                sys.exit(1)
            
            agent.pull_model(agent.model_name)
            response = agent.chat(command)
            print(f"\n{response}")
        else:
            # Interactive mode
            agent.run()
    finally:
        agent.cleanup()


if __name__ == "__main__":
    main()
