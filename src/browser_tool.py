#!/usr/bin/env python3
"""
Browser Tool - Headless Chromium automation for AgentSmith
Uses CDP (Chrome DevTools Protocol) for control
"""

import subprocess
import asyncio
import json
import time
import websockets
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class BrowserElement:
    """Represents a browser element"""
    ref: str
    tag: str
    text: str
    attributes: Dict[str, str]


class HeadlessBrowser:
    """Headless Chromium browser controller"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.chrome_process = None
        self.ws_url = None
        self.ws = None
        self.page_id = None
        self.message_id = 0
        
    async def start(self) -> bool:
        """Start headless Chromium"""
        try:
            # Find Chrome/Chromium
            chrome_paths = [
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/usr/bin/google-chrome",
                "/usr/bin/chrome",
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            ]
            
            chrome_path = None
            for path in chrome_paths:
                if Path(path).exists():
                    chrome_path = path
                    break
            
            if not chrome_path:
                print("✗ Chrome/Chromium not found")
                return False
            
            # Launch Chrome with remote debugging
            port = 9222
            args = [
                chrome_path,
                f"--remote-debugging-port={port}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-popup-blocking",
                "--disable-translate",
                "--disable-extensions",
                "--disable-background-networking",
                "--safebrowsing-disable-auto-update",
                "--disable-sync",
                "--metrics-recording-only",
                "--disable-default-apps",
                "--mute-audio",
                "--no-sandbox" if self.headless else "",
            ]
            
            if self.headless:
                args.append("--headless=new")
            
            # Filter empty strings
            args = [a for a in args if a]
            
            self.chrome_process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for Chrome to start
            await asyncio.sleep(2)
            
            # Get WebSocket URL
            import urllib.request
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=10) as resp:
                data = json.loads(resp.read().decode())
                self.ws_url = data.get("webSocketDebuggerUrl")
            
            if not self.ws_url:
                print("✗ Could not get WebSocket URL")
                return False
            
            # Connect to Chrome
            self.ws = await websockets.connect(self.ws_url)
            
            # Enable page events
            await self._send_command("Page.enable")
            await self._send_command("Runtime.enable")
            
            print("✓ Browser started")
            return True
            
        except Exception as e:
            print(f"✗ Error starting browser: {e}")
            return False
    
    async def _send_command(self, method: str, params: Dict = None) -> Dict:
        """Send CDP command"""
        self.message_id += 1
        message = {
            "id": self.message_id,
            "method": method,
            "params": params or {}
        }
        
        await self.ws.send(json.dumps(message))
        
        # Wait for response
        while True:
            response = await self.ws.recv()
            data = json.loads(response)
            if data.get("id") == self.message_id:
                return data
    
    async def navigate(self, url: str) -> bool:
        """Navigate to URL"""
        try:
            result = await self._send_command("Page.navigate", {"url": url})
            # Wait for load
            await asyncio.sleep(2)
            return "error" not in result
        except Exception as e:
            print(f"✗ Navigation error: {e}")
            return False
    
    async def get_page_content(self) -> str:
        """Get page text content"""
        try:
            script = """
                () => {
                    return document.body.innerText;
                }
            """
            
            result = await self._send_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            return result.get("result", {}).get("result", {}).get("value", "")
        except Exception as e:
            return f"Error: {e}"
    
    async def find_element(self, selector: str) -> Optional[BrowserElement]:
        """Find element by CSS selector"""
        try:
            script = f"""
                () => {{
                    const el = document.querySelector('{selector}');
                    if (!el) return null;
                    return {{
                        tag: el.tagName,
                        text: el.innerText || el.textContent || '',
                        attributes: Array.from(el.attributes).reduce((acc, attr) => {{
                            acc[attr.name] = attr.value;
                            return acc;
                        }}, {{}})
                    }};
                }}
            """
            
            result = await self._send_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            data = result.get("result", {}).get("result", {}).get("value")
            if data:
                return BrowserElement(
                    ref=selector,
                    tag=data.get("tag", ""),
                    text=data.get("text", ""),
                    attributes=data.get("attributes", {})
                )
            return None
            
        except Exception as e:
            print(f"✗ Find error: {e}")
            return None
    
    async def click(self, selector: str) -> bool:
        """Click element"""
        try:
            script = f"""
                () => {{
                    const el = document.querySelector('{selector}');
                    if (el) {{
                        el.click();
                        return true;
                    }}
                    return false;
                }}
            """
            
            result = await self._send_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            return result.get("result", {}).get("result", {}).get("value", False)
            
        except Exception as e:
            print(f"✗ Click error: {e}")
            return False
    
    async def type_text(self, selector: str, text: str) -> bool:
        """Type text into element"""
        try:
            # Focus element
            await self._send_command("Runtime.evaluate", {
                "expression": f"document.querySelector('{selector}').focus()"
            })
            
            # Type text
            for char in text:
                await self._send_command("Input.dispatchKeyEvent", {
                    "type": "char",
                    "text": char
                })
                await asyncio.sleep(0.01)
            
            return True
            
        except Exception as e:
            print(f"✗ Type error: {e}")
            return False
    
    async def get_current_url(self) -> str:
        """Get current page URL"""
        try:
            result = await self._send_command("Runtime.evaluate", {
                "expression": "window.location.href",
                "returnByValue": True
            })
            return result.get("result", {}).get("result", {}).get("value", "")
        except:
            return ""
    
    async def is_login_page(self) -> bool:
        """Detect if current page is a login page"""
        try:
            script = """
                () => {
                    const html = document.body.innerText.toLowerCase();
                    const hasLogin = html.includes('login') || html.includes('sign in');
                    const hasPassword = document.querySelector('input[type="password"]') !== null;
                    return hasLogin && hasPassword;
                }
            """
            
            result = await self._send_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            return result.get("result", {}).get("result", {}).get("value", False)
            
        except:
            return False
    
    async def stop(self):
        """Stop browser"""
        if self.ws:
            await self.ws.close()
        if self.chrome_process:
            self.chrome_process.terminate()
            try:
                self.chrome_process.wait(timeout=5)
            except:
                self.chrome_process.kill()


class BrowserTool:
    """High-level browser tool for agent"""
    
    def __init__(self):
        self.browser = HeadlessBrowser(headless=True)
        self.visible_browser = None
        
    async def start(self) -> bool:
        """Start browser tool"""
        return await self.browser.start()
    
    async def execute_task(self, task: str, url: str = None) -> str:
        """Execute a browser task"""
        try:
            if url:
                await self.browser.navigate(url)
                await asyncio.sleep(2)
            
            # Check if login page
            if await self.browser.is_login_page():
                return "LOGIN_REQUIRED"
            
            # Get page content
            content = await self.browser.get_page_content()
            
            # Return truncated content
            if len(content) > 2000:
                content = content[:2000] + "..."
            
            return content
            
        except Exception as e:
            return f"Browser error: {e}"
    
    async def switch_to_visible(self):
        """Switch to visible browser for login"""
        await self.browser.stop()
        self.visible_browser = HeadlessBrowser(headless=False)
        return await self.visible_browser.start()
    
    async def switch_to_headless(self):
        """Switch back to headless after login"""
        if self.visible_browser:
            await self.visible_browser.stop()
        self.browser = HeadlessBrowser(headless=True)
        return await self.browser.start()
    
    async def stop(self):
        """Stop all browsers"""
        await self.browser.stop()
        if self.visible_browser:
            await self.visible_browser.stop()


# Test
async def test_browser():
    """Test browser functionality"""
    browser = BrowserTool()
    
    print("Starting browser...")
    if await browser.start():
        print("✓ Browser started")
        
        print("\nNavigating to example.com...")
        result = await browser.execute_task("Get page content", "https://example.com")
        print(f"Result: {result[:200]}...")
        
        await browser.stop()
        print("\n✓ Browser stopped")
    else:
        print("✗ Failed to start browser")


if __name__ == "__main__":
    asyncio.run(test_browser())
