#!/usr/bin/env python3
"""
SuperPalmTree Browser Tool - DOM/ARIA Approach
Uses Playwright for browser automation with ARIA accessibility tree snapshots.
Returns semantic element refs instead of heavy HTML - optimized for small models.

Port: 9223 (isolated from system Chrome on 9222)
Profile: ~/.superpalmtree/chromium/
"""

import asyncio
import re
from typing import Optional, Tuple, Dict, List, Any
from pathlib import Path
from dataclasses import dataclass

# Configuration
CHROME_DEBUG_PORT = 9223
DATA_DIR = Path.home() / ".superpalmtree"
CHROMIUM_PROFILE = DATA_DIR / "chromium"


@dataclass
class ElementRef:
    """Reference to a page element"""
    ref: str  # e.g., "e5"
    role: str  # e.g., "link", "button", "textbox"
    name: str  # accessible name
    selector: str  # CSS selector for interaction


class CDPBrowser:
    """
    Browser automation using Playwright with ARIA tree snapshots.
    Compatible with existing agent.py interface.

    Instead of returning raw HTML, returns structured ARIA snapshots:
    - heading "Example Domain" [ref=e3]
    - link "More information..." [ref=e5]

    Agent can then use: click("e5") to interact.
    """

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_headless = True
        self.current_url = ""
        self.element_refs: Dict[str, ElementRef] = {}
        self._ref_counter = 0

    async def start(self, headless: bool = True) -> bool:
        """
        Start browser with isolated profile.

        Args:
            headless: If False, browser window is visible (user can watch)

        Returns:
            True if started successfully
        """
        try:
            from playwright.async_api import async_playwright

            self.is_headless = headless

            # Ensure profile directory exists
            CHROMIUM_PROFILE.mkdir(parents=True, exist_ok=True)

            # Start Playwright
            self.playwright = await async_playwright().start()

            # Launch with persistent context for isolated profile
            self.context = await self.playwright.chromium.launch_persistent_context(
                str(CHROMIUM_PROFILE),
                headless=headless,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            )

            # Get page
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            self.browser = self.context  # For compatibility

            print(f"[browser] Started {'headless' if headless else 'visible'} on port {CHROME_DEBUG_PORT}")
            return True

        except Exception as e:
            print(f"[browser] Failed to start: {e}")
            return False

    async def navigate(self, url: str, wait_for: str = "domcontentloaded") -> Tuple[bool, str]:
        """
        Navigate to URL.

        Args:
            url: URL to navigate to
            wait_for: Wait condition - "domcontentloaded", "load", or "networkidle"

        Returns:
            Tuple of (success, message)
        """
        if not self.page:
            return False, "Browser not started"

        try:
            # Ensure URL has protocol
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            # Navigate
            response = await self.page.goto(url, wait_until=wait_for, timeout=30000)

            self.current_url = self.page.url

            if response and response.ok:
                return True, f"Navigated to {self.current_url}"
            elif response:
                return True, f"Navigated to {self.current_url} (status: {response.status})"
            else:
                return True, f"Navigated to {self.current_url}"

        except Exception as e:
            return False, f"Navigation failed: {e}"

    async def snapshot(self) -> str:
        """
        Get semantic elements from page using Playwright's role selectors.
        Returns elements with refs for interaction.
        """
        if not self.page:
            return "[error] Browser not started"

        try:
            self.element_refs.clear()
            self._ref_counter = 0
            lines = [f"[page] {self.current_url}", ""]

            # Get headings
            headings = await self.page.get_by_role("heading").all()
            for h in headings:
                text = await h.text_content()
                if text:
                    lines.append(f"# {text.strip()}")

            # Get links with refs
            links = await self.page.get_by_role("link").all()
            for link in links:
                text = await link.text_content()
                if text and text.strip():
                    ref = self._add_ref("link", text.strip(), link)
                    lines.append(f"- link \"{text.strip()}\" [ref={ref}]")

            # Get buttons with refs
            buttons = await self.page.get_by_role("button").all()
            for btn in buttons:
                text = await btn.text_content()
                if text and text.strip():
                    ref = self._add_ref("button", text.strip(), btn)
                    lines.append(f"- button \"{text.strip()}\" [ref={ref}]")

            # Get inputs with refs
            inputs = await self.page.get_by_role("textbox").all()
            for inp in inputs:
                placeholder = await inp.get_attribute("placeholder") or "input"
                ref = self._add_ref("textbox", placeholder, inp)
                lines.append(f"- input \"{placeholder}\" [ref={ref}]")

            return "\n".join(lines)

        except Exception as e:
            return f"[error] {e}"

    def _add_ref(self, role: str, name: str, locator) -> str:
        """Add element ref and return ref ID"""
        self._ref_counter += 1
        ref = f"e{self._ref_counter}"
        self.element_refs[ref] = ElementRef(ref=ref, role=role, name=name, selector="")
        self.element_refs[ref].locator = locator  # Store actual locator
        return ref

    def _format_node(self, node: Dict, lines: List[str], indent: int):
        """Recursively format accessibility tree node"""
        role = node.get("role", "")
        name = node.get("name", "")

        # Skip generic/uninteresting nodes
        skip_roles = {"none", "generic", "group", "document", "main", "navigation", "banner", "contentinfo"}

        # Include roles that are actionable or informative
        include_roles = {
            "heading", "link", "button", "textbox", "checkbox", "radio",
            "combobox", "listbox", "option", "menuitem", "tab", "tabpanel",
            "img", "figure", "article", "section", "list", "listitem",
            "text", "paragraph", "table", "row", "cell", "form"
        }

        if role in include_roles and name:
            # Generate ref for interactive elements
            ref = ""
            if role in {"link", "button", "textbox", "checkbox", "radio", "combobox", "option", "menuitem", "tab"}:
                ref = self._generate_ref(node, role, name)

            # Format line
            prefix = "  " * indent
            if role == "heading":
                level = node.get("level", 1)
                line = f"{prefix}{'#' * level} {name}"
            elif role == "link":
                line = f"{prefix}- link \"{name}\" [ref={ref}]"
            elif role == "button":
                line = f"{prefix}- button \"{name}\" [ref={ref}]"
            elif role == "textbox":
                value = node.get("value", "")
                placeholder = f" ({value})" if value else ""
                line = f"{prefix}- input \"{name}\"{placeholder} [ref={ref}]"
            elif role == "img":
                line = f"{prefix}- image \"{name}\""
            elif role == "listitem":
                line = f"{prefix}  * {name}"
            else:
                line = f"{prefix}- {role}: \"{name}\""
                if ref:
                    line += f" [ref={ref}]"

            lines.append(line)

        # Process children
        children = node.get("children", [])
        for child in children:
            self._format_node(child, lines, indent + (1 if role in include_roles else 0))

    def _generate_ref(self, node: Dict, role: str, name: str) -> str:
        """Generate a reference ID and store element info"""
        self._ref_counter += 1
        ref = f"e{self._ref_counter}"

        # Build selector based on role and name
        selector = self._build_selector(role, name)

        self.element_refs[ref] = ElementRef(
            ref=ref,
            role=role,
            name=name,
            selector=selector
        )

        return ref

    def _build_selector(self, role: str, name: str) -> str:
        """Build CSS selector from role and accessible name"""
        # Escape special characters in name for selector
        safe_name = name.replace('"', '\\"').replace("'", "\\'")

        role_selectors = {
            "link": f'a:has-text("{safe_name}")',
            "button": f'button:has-text("{safe_name}"), [role="button"]:has-text("{safe_name}")',
            "textbox": f'input[placeholder*="{safe_name}"], input[aria-label*="{safe_name}"], textarea[placeholder*="{safe_name}"]',
            "checkbox": f'input[type="checkbox"][aria-label*="{safe_name}"]',
            "radio": f'input[type="radio"][aria-label*="{safe_name}"]',
            "combobox": f'select[aria-label*="{safe_name}"], [role="combobox"]:has-text("{safe_name}")',
            "option": f'option:has-text("{safe_name}")',
            "menuitem": f'[role="menuitem"]:has-text("{safe_name}")',
            "tab": f'[role="tab"]:has-text("{safe_name}")',
        }

        return role_selectors.get(role, f':has-text("{safe_name}")')

    async def click(self, ref_or_selector: str) -> bool:
        """
        Click an element by ref or CSS selector.

        Args:
            ref_or_selector: Element ref (e.g., "e5") or CSS selector

        Returns:
            True if clicked successfully
        """
        if not self.page:
            return False

        try:
            # Check if it's a ref
            if ref_or_selector.startswith("e") and ref_or_selector[1:].isdigit():
                element_info = self.element_refs.get(ref_or_selector)
                if element_info:
                    selector = element_info.selector
                    print(f"[browser] Clicking {ref_or_selector} ({element_info.role}: \"{element_info.name}\")")
                else:
                    print(f"[browser] Unknown ref: {ref_or_selector}")
                    return False
            else:
                selector = ref_or_selector
                print(f"[browser] Clicking selector: {selector}")

            # Try to click
            await self.page.click(selector, timeout=10000)

            # Wait for potential navigation/updates
            await asyncio.sleep(0.5)

            return True

        except Exception as e:
            print(f"[browser] Click failed: {e}")
            return False

    async def type_text(self, ref_or_selector: str, text: str) -> bool:
        """
        Type text into an input element.

        Args:
            ref_or_selector: Element ref or CSS selector
            text: Text to type

        Returns:
            True if typed successfully
        """
        if not self.page:
            return False

        try:
            # Resolve ref to selector
            if ref_or_selector.startswith("e") and ref_or_selector[1:].isdigit():
                element_info = self.element_refs.get(ref_or_selector)
                if element_info:
                    selector = element_info.selector
                    print(f"[browser] Typing into {ref_or_selector} ({element_info.name})")
                else:
                    return False
            else:
                selector = ref_or_selector

            # Clear and type
            await self.page.fill(selector, text, timeout=10000)

            return True

        except Exception as e:
            print(f"[browser] Type failed: {e}")
            return False

    async def get_page_content(self) -> str:
        """
        Get page content as ARIA snapshot (not raw HTML).
        This is the main method called by agent.py.

        Returns:
            ARIA tree snapshot
        """
        return await self.snapshot()

    async def screenshot(self, path: Optional[str] = None) -> Optional[bytes]:
        """
        Take screenshot of current page.

        Args:
            path: Optional path to save screenshot

        Returns:
            Screenshot bytes if no path provided
        """
        if not self.page:
            return None

        try:
            if path:
                await self.page.screenshot(path=path, full_page=False)
                print(f"[browser] Screenshot saved to {path}")
                return None
            else:
                return await self.page.screenshot(full_page=False)

        except Exception as e:
            print(f"[browser] Screenshot failed: {e}")
            return None

    async def stop(self):
        """Stop browser and cleanup"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

            print("[browser] Stopped")

        except Exception as e:
            print(f"[browser] Error stopping: {e}")

    # Convenience methods for common actions

    async def press(self, key: str) -> bool:
        """Press a key (e.g., 'Enter', 'Tab', 'Escape')"""
        if not self.page:
            return False
        try:
            await self.page.keyboard.press(key)
            return True
        except Exception as e:
            print(f"[browser] Press failed: {e}")
            return False

    async def wait(self, seconds: float):
        """Wait for specified seconds"""
        await asyncio.sleep(seconds)

    async def scroll(self, direction: str = "down", amount: int = 500):
        """Scroll page up or down"""
        if not self.page:
            return
        try:
            delta = amount if direction == "down" else -amount
            await self.page.mouse.wheel(0, delta)
        except Exception as e:
            print(f"[browser] Scroll failed: {e}")


# Test function
async def test_browser():
    """Test browser tool"""
    browser = CDPBrowser()

    print("Starting browser...")
    if not await browser.start(headless=False):
        print("Failed to start browser")
        return

    print("\nNavigating to example.com...")
    success, msg = await browser.navigate("https://example.com")
    print(f"  {msg}")

    print("\nGetting ARIA snapshot...")
    snapshot = await browser.snapshot()
    print(snapshot)

    print("\nWaiting 5 seconds so you can see...")
    await browser.wait(5)

    print("\nStopping browser...")
    await browser.stop()

    print("Done!")


if __name__ == "__main__":
    asyncio.run(test_browser())
