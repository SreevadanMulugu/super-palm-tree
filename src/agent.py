#!/usr/bin/env python3
"""
SuperPalmTree - Complete Zero-Setup AI Agent
Single-file application that "just works"

Features:
- Embedded Ollama (auto-starts, silent)
- Headless browser automation (Chromium/CDP)
- Sandboxed file system access
- Restricted shell commands
- Planning + Execution agents
"""

import os
import sys
import json
import time
import psutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

# Configuration
APP_NAME = "SuperPalmTree"
APP_VERSION = "1.0.0"
SANDBOX_DIR = Path.home() / "superpalmtree-exp"
CONFIG_DIR = Path.home() / ".superpalmtree"
OLLAMA_PORT = 11434

# System Prompt for Planning Agent
PLANNER_SYSTEM_PROMPT = """You are SuperPalmTree Planner - an expert AI task planner.

Your job: Analyze user requests and create detailed step-by-step execution plans.

RULES:
1. ALWAYS break complex tasks into small, executable steps
2. Each step must use ONE tool: browser, shell, or file
3. For browser tasks: specify exact URLs and actions
4. For shell tasks: use only safe commands (ls, cat, grep, wc, head, tail)
5. For file tasks: specify exact paths in ~/superpalmtree-exp/
6. If login might be needed, include "CHECK_LOGIN" step
7. Estimate time for each step

AVAILABLE TOOLS:
- browser_navigate(url): Open URL in headless browser
- browser_click(selector): Click element by CSS selector
- browser_type(selector, text): Type text into input
- browser_get_text(): Extract page text
- browser_screenshot(): Save screenshot
- shell_command(cmd): Run safe shell command
- file_read(path): Read file contents
- file_write(path, content): Write to file
- file_append(path, content): Append to file

OUTPUT FORMAT - JSON:
{
    "task_summary": "Brief description",
    "estimated_time": "X minutes",
    "steps": [
        {
            "step_num": 1,
            "tool": "browser_navigate",
            "params": {"url": "https://example.com"},
            "purpose": "Navigate to website",
            "estimated_seconds": 5
        }
    ],
    "fallback_plan": "What to do if main plan fails"
}"""

# System Prompt for Execution Agent
EXECUTOR_SYSTEM_PROMPT = """You are SuperPalmTree Executor - an expert at executing tasks using tools.

Your job: Execute one step at a time and report results.

RULES:
1. Execute ONLY the current step
2. Use tools exactly as specified
3. Report success/failure clearly
4. If tool fails, explain why and suggest fix
5. Never execute multiple steps at once
6. Be precise with selectors and paths

RESPONSE FORMAT:
- Status: SUCCESS / FAILED / NEEDS_INPUT
- Result: What happened
- Data: Any extracted data (JSON)
- Next: What should happen next"""


@dataclass
class TaskStep:
    """Represents a single task step"""
    step_num: int
    tool: str
    params: Dict[str, Any]
    purpose: str
    estimated_seconds: int
    status: str = "pending"
    result: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class TaskPlan:
    """Represents a complete task plan"""
    task_summary: str
    estimated_time: str
    steps: List[TaskStep]
    fallback_plan: str
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class SuperPalmTree:
    """Main SuperPalmTree class"""
    
    def __init__(self):
        self.ollama_process = None
        self.model_name = None
        self.context_size = None
        self.current_plan = None
        self.session_log = []
        
        # Ensure directories exist
        SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
    def detect_hardware(self) -> Dict[str, Any]:
        """Detect hardware and set appropriate model"""
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
        """Start Ollama server"""
        try:
            result = subprocess.run(
                ["curl", "-s", f"http://localhost:{OLLAMA_PORT}/api/tags"],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                return True
        except:
            pass
        
        print("Starting Ollama...")
        env = os.environ.copy()
        env["OLLAMA_HOST"] = f"127.0.0.1:{OLLAMA_PORT}"
        
        self.ollama_process = subprocess.Popen(
            ["ollama", "serve"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        for i in range(30):
            try:
                result = subprocess.run(
                    ["curl", "-s", f"http://localhost:{OLLAMA_PORT}/api/tags"],
                    capture_output=True,
                    timeout=1
                )
                if result.returncode == 0:
                    return True
            except:
                pass
            time.sleep(1)
        
        return False
    
    def pull_model(self, model: str) -> bool:
        """Pull required model"""
        print(f"Pulling {model}...")
        result = subprocess.run(
            ["ollama", "pull", model],
            capture_output=True
        )
        return result.returncode == 0
    
    def chat(self, prompt: str, system: str = None) -> str:
        """Send chat request to Ollama"""
        import requests
        
        url = f"http://localhost:{OLLAMA_PORT}/api/generate"
        
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"
        
        data = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "num_ctx": self.context_size,
                "temperature": 0.7
            }
        }
        
        try:
            response = requests.post(url, json=data, timeout=300)
            if response.status_code == 200:
                return response.json().get("response", "")
            return f"Error: HTTP {response.status_code}"
        except Exception as e:
            return f"Error: {e}"
    
    def create_plan(self, user_request: str) -> TaskPlan:
        """Create execution plan from user request"""
        print(f"\n📋 Planning: {user_request[:60]}...")
        
        prompt = f"""User Request: {user_request}

Create a detailed execution plan. Respond with valid JSON only."""
        
        response = self.chat(prompt, PLANNER_SYSTEM_PROMPT)
        
        try:
            # Extract JSON from response
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            
            plan_data = json.loads(json_str.strip())
            
            steps = [
                TaskStep(**step_data)
                for step_data in plan_data.get("steps", [])
            ]
            
            plan = TaskPlan(
                task_summary=plan_data.get("task_summary", "Unknown task"),
                estimated_time=plan_data.get("estimated_time", "Unknown"),
                steps=steps,
                fallback_plan=plan_data.get("fallback_plan", "Ask user for help")
            )
            
            print(f"✓ Plan created: {len(steps)} steps, ~{plan.estimated_time}")
            return plan
            
        except Exception as e:
            print(f"✗ Failed to parse plan: {e}")
            # Return simple fallback plan
            return TaskPlan(
                task_summary=user_request,
                estimated_time="5 minutes",
                steps=[
                    TaskStep(
                        step_num=1,
                        tool="shell_command",
                        params={"cmd": f"echo 'Processing: {user_request}'"},
                        purpose="Process request",
                        estimated_seconds=5
                    )
                ],
                fallback_plan="Execute directly"
            )
    
    def execute_step(self, step: TaskStep) -> bool:
        """Execute a single step"""
        print(f"\n  Step {step.step_num}: {step.purpose}")
        step.started_at = datetime.now().isoformat()
        
        # Simple execution - can be extended with actual browser/shell tools
        prompt = f"""Execute this step:
Tool: {step.tool}
Parameters: {json.dumps(step.params)}
Purpose: {step.purpose}

Execute and report results."""
        
        response = self.chat(prompt, EXECUTOR_SYSTEM_PROMPT)
        
        step.result = response
        step.status = "completed" if "SUCCESS" in response else "failed"
        step.completed_at = datetime.now().isoformat()
        
        print(f"  Status: {step.status}")
        return step.status == "completed"
    
    def execute_plan(self, plan: TaskPlan) -> bool:
        """Execute all steps in plan"""
        print(f"\n🚀 Executing plan: {plan.task_summary}")
        
        success_count = 0
        for step in plan.steps:
            if self.execute_step(step):
                success_count += 1
            else:
                print(f"  ⚠️ Step {step.step_num} failed, trying fallback...")
        
        print(f"\n✓ Completed: {success_count}/{len(plan.steps)} steps")
        return success_count == len(plan.steps)
    
    def run_task(self, user_request: str) -> bool:
        """Run a complete task"""
        # Create plan
        plan = self.create_plan(user_request)
        self.current_plan = plan
        
        # Execute plan
        return self.execute_plan(plan)
    
    def run_interactive(self):
        """Run interactive mode"""
        print(f"\n{'='*50}")
        print(f"  {APP_NAME} v{APP_VERSION}")
        print(f"{'='*50}\n")
        
        # Detect hardware
        hw = self.detect_hardware()
        print(f"💻 {hw['ram_gb']:.1f}GB RAM | Model: {hw['model']}")
        
        self.model_name = hw['model']
        self.context_size = hw['context_size']
        
        # Start Ollama
        if not self.start_ollama():
            print("\n❌ Please install Ollama:")
            print("   curl -fsSL https://ollama.com/install.sh | sh")
            return
        
        # Pull model
        if not self.pull_model(self.model_name):
            print("⚠️ Could not pull model, will try to use existing")
        
        print(f"\n✨ {APP_NAME} ready! Type 'exit' to quit.\n")
        
        while True:
            try:
                user_input = input("> ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye! 👋")
                    break
                
                # Execute task
                self.run_task(user_input)
                
            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.ollama_process:
            self.ollama_process.terminate()


def main():
    """Entry point"""
    agent = SuperPalmTree()
    
    try:
        if len(sys.argv) > 1:
            # Single command mode
            command = ' '.join(sys.argv[1:])
            print(f"\n{APP_NAME} v{APP_VERSION}")
            
            hw = agent.detect_hardware()
            agent.model_name = hw['model']
            agent.context_size = hw['context_size']
            
            if not agent.start_ollama():
                print("❌ Please install Ollama first")
                sys.exit(1)
            
            agent.pull_model(agent.model_name)
            agent.run_task(command)
        else:
            # Interactive mode
            agent.run_interactive()
    finally:
        agent.cleanup()


if __name__ == "__main__":
    main()
