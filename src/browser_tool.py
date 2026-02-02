#!/usr/bin/env python3
"""
Browser Tool - Headless Chromium automation for SuperPalmTree
Uses CDP (Chrome DevTools Protocol) for control
"""

import subprocess
import asyncio
import json
import time
import websockets
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class BrowserElement:
    """Represents a browser element"""
    ref: str
    tag: str
    text: str
    attributes: Dict[str, str]


class CDPBrowser:
    """Headless Chromium browser controller via CDP"""
    
    def __init__(self):
        self.chrome_process = None
        self.ws_url: Optional[str] = None
        self.ws = None
        self.message_id = 0
        self.is_headless = True
        self.connected = False
    
    async def start(self, headless: bool = True) -> bool:
        """Start headless Chromium"""
        self.is_headless = headless
        
        try:
            # Find Chrome/Chromium
            chrome_path = self._find_chrome()
            if not chrome_path:
                print("Chrome/Chromium not found")
                return False
            
            # Launch Chrome with remote debugging
            port = 9223
            args = [
                str(chrome_path),
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
                "--mute-audio",
                "--disable-dev-shm-usage",
            ]
            
            if headless:
                args.append("--headless=new")
                args.append("--no-sandbox")
            
            print(f"Starting Chrome from: {chrome_path}")
            
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
                print("Could not get WebSocket URL")
                return False
            
            # Connect to Chrome
            self.ws = await websockets.connect(self.ws_url)
            
            # Enable page events
            await self._send_command("Page.enable")
            await self._send_command("Runtime.enable")
            
            self.connected = True
            print("✓ Browser started")
            return True
            
        except Exception as e:
            print(f"Error starting browser: {e}")
            return False
    
    def _find_chrome(self) -> Optional[Path]:
        """Find Chrome/Chromium binary"""
        import platform
        
        system = platform.system()
        
        if system == "Linux":
            paths = [
                Path("/usr/bin/chromium-browser"),
                Path("/usr/bin/chromium"),
                Path("/usr/bin/google-chrome"),
                Path("/snap/bin/chromium"),
            ]
        elif system == "Darwin":
            paths = [
                Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
            ]
        elif system == "Windows":
            paths = [
                Path("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"),
                Path("C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"),
                Path(os.environ.get("LOCALAPPDATA", "") + "\\Google\\Chrome\\Application\\chrome.exe"),
            ]
        else:
            paths = []
        
        for path in paths:
            if path.exists():
                return path
        
        return None
    
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
    
    async def navigate(self, url: str) -> Tuple[bool, str]:
        """Navigate to URL"""
        try:
            result = await self._send_command("Page.navigate", {"url": url})
            await asyncio.sleep(3)
            
            # Check for login page
            is_login = await self._is_login_page()
            if is_login:
                return True, "LOGIN_REQUIRED"
            
            return True, f"Navigated to {url}"
        except Exception as e:
            return False, str(e)
    
    async def _is_login_page(self) -> bool:
        """Detect if current page is a login page"""
        try:
            script = """() => {
                const html = document.body.innerText.toLowerCase();
                return (html.includes('login') || html.includes('sign in') || html.includes('password')) && 
                       document.querySelector('input[type="password"]') !== null;
            }"""
            
            result = await self._send_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            return result.get("result", {}).get("result", {}).get("value", False)
        except:
            return False
    
    async def get_page_content(self) -> str:
        """Get page text content"""
        try:
            script = """() => {
                return document.body.innerText || document.body.textContent || '';
            }"""
            
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
            script = f"""() => {{
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
            }}"""
            
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
            print(f"Find error: {e}")
            return None
    
    async def click(self, selector: str) -> Tuple[bool, str]:
        """Click element by CSS selector"""
        try:
            script = f"""() => {{
                const el = document.querySelector('{selector}');
                if (el) {{
                    el.click();
                    return true;
                }}
                return false;
            }}"""
            
            result = await self._send_command("Runtime.evaluate", {
                "expression": script,
                "returnByValue": True
            })
            
            success = result.get("result", {}).get("result", {}).get("value", False)
            return success, f"Clicked {selector}" if success else f"Element not found: {selector}"
            
        except Exception as e:
            return False, str(e)
    
    async def type_text(self, selector: str, text: str) -> Tuple[bool, str]:
        """Type text into element"""
        try:
            await self._send_command("Runtime.evaluate", {
                "expression": f"document.querySelector('{selector}').focus()"
            })
            
            for char in text:
                await self._send_command("Input.dispatchKeyEvent", {
                    "type": "char",
                    "text": char
                })
                await asyncio.sleep(0.01)
            
            return True, f"Typed into {selector}"
            
        except Exception as e:
            return False, str(e)
    
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
    
    async def scroll_down(self, pixels: int = 500) -> Tuple[bool, str]:
        """Scroll down the page"""
        try:
            await self._send_command("Runtime.evaluate", {
                "expression": f"window.scrollBy(0, {pixels})"
            })
            await asyncio.sleep(0.5)
            return True, f"Scrolled {pixels}px"
        except Exception as e:
            return False, str(e)
    
    async def stop(self):
        """Stop browser"""
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
        if self.chrome_process:
            self.chrome_process.terminate()
            try:
                self.chrome_process.wait(timeout=5)
            except:
                self.chrome_process.kill()
        self.connected = False


class BrowserTool:
    """High-level browser tool for agent"""
    
    def __init__(self):
        self.browser = CDPBrowser()
    
    async def start(self) -> bool:
        """Start browser tool in headless mode"""
        return await self.browser.start(headless=True)
    
    async def navigate(self, url: str) -> Tuple[bool, str]:
        """Navigate to URL"""
        return await self.browser.navigate(url)
    
    async def get_content(self) -> str:
        """Get page content"""
        return await self.browser.get_page_content()
    
    async def click(self, selector: str) -> Tuple[bool, str]:
        """Click an element"""
        return await self.browser.click(selector)
    
    async def type(self, selector: str, text: str) -> Tuple[bool, str]:
        """Type text into an element"""
        return await self.browser.type_text(selector, text)
    
    async def stop(self):
        """Stop browser"""
        await self.browser.stop()


# Test function
async def test_browser():
    """Test browser functionality"""
    browser = BrowserTool()
    
    print("Starting browser...")
    if await browser.start():
        print("✓ Browser started")
        
        print("\nNavigating to example.com...")
        success, result = await browser.navigate("https://example.com")
        print(f"Result: {result}")
        
        if success:
            content = await browser.get_content()
            print(f"Content: {content[:200]}...")
        
        await browser.stop()
        print("\n✓ Browser stopped")
    else:
        print("✗ Failed to start browser")


if __name__ == "__main__":
    asyncio.run(test_browser())
