# next_button_helpers.py
import re
from typing import Optional
from playwright.async_api import Page, Locator

# ---------- small utilities ----------

async def _scroll_into_view_if_exists(page: Page, selector: str, timeout: int = 1200) -> bool:
    loc = page.locator(selector)
    if await loc.count() == 0:
        return False
    try:
        await loc.first.scroll_into_view_if_needed(timeout=timeout)
        await page.wait_for_timeout(250)
        return True
    except Exception:
        return False

async def _nudge_viewport(page: Page):
    try:
        await page.bring_to_front()
    except Exception:
        pass
    try:
        await page.locator("body").click(position={"x": 10, "y": 10}, timeout=500)
    except Exception:
        pass
    try:
        await page.keyboard.press("PageDown")
        await page.wait_for_timeout(150)
        await page.keyboard.press("End")
        await page.wait_for_timeout(150)
    except Exception:
        pass

async def _scroll_main_containers(page: Page):
    js = """
    () => {
      const scrollers = [
        document.querySelector('nav[aria-label="Pagination"]'),
        document.querySelector('div.search-results-container'),
        document.querySelector('div.scaffold-finite-scroll'),
        document.querySelector('main#workspace'),
        document.querySelector('main[role="main"]'),
        document.scrollingElement
      ].filter(Boolean);
      for (const el of scrollers) {
        try { el.scrollBy({ top: 1200, behavior: 'auto' }); } catch {}
      }
    }
    """
    try:
        await page.evaluate(js)
        await page.wait_for_timeout(300)
    except Exception:
        pass


# ---------- robust finder ----------

async def find_next_button(page: Page, timeout: int = 1500) -> Optional[Locator]:
    """
    Find LinkedIn's 'Next' pagination button using several strategies.
    """

    # Bring pagination bar into view if present
    await _scroll_into_view_if_exists(page, 'nav[aria-label="Pagination"]')

    pagination = page.locator('nav[aria-label="Pagination"]')
    strategies = []

    if await pagination.count() > 0:
        # Scoped strategies (best first)
        strategies.extend([
            pagination.locator("button[data-testid='pagination-control-next-btn']"),
            pagination.locator("button[aria-label*='Next' i], button[aria-label*='Next page' i]"),
            pagination.get_by_role("button", name="Next"),
            pagination.get_by_role("button", name=re.compile(r"^next", re.I)),
        ])

    # Global fallbacks
    strategies.extend([
        page.locator("button[data-testid='pagination-control-next-btn']"),
        page.locator("button[aria-label*='Next' i], button[aria-label*='Next page' i]"),
        page.get_by_role("button", name="Next"),
        page.get_by_role("button", name=re.compile(r"^next", re.I)),
    ])

    for loc in strategies:
        if await loc.count() > 0:
            cand = loc.first
            try:
                await cand.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                await cand.wait_for(state="visible", timeout=timeout)
                return cand
            except Exception:
                # Try the next candidate
                continue

    # Last try: force scrolling and retry once
    await _nudge_viewport(page)
    await _scroll_main_containers(page)
    await _scroll_into_view_if_exists(page, 'nav[aria-label="Pagination"]')

    for loc in strategies:
        if await loc.count() > 0:
            cand = loc.first
            try:
                await cand.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                await cand.wait_for(state="visible", timeout=timeout)
                return cand
            except Exception:
                continue

    return None


# ---------- click helper ----------

async def click_next_page(page: Page, settle_ms: int = 1200) -> bool:
    """
    Clicks the 'Next' button if present & enabled.
    Returns True if clicked, else False.
    """
    btn = await find_next_button(page)
    if not btn:
        return False

    # If disabled, bail
    try:
        disabled = await btn.get_attribute("disabled")
        aria_disabled = await btn.get_attribute("aria-disabled")
        if (disabled is not None) or (aria_disabled and aria_disabled.lower() == "true"):
            return False
    except Exception:
        pass

    await btn.click()
    try:
        await page.wait_for_load_state("networkidle", timeout=settle_ms)
    except Exception:
        await page.wait_for_timeout(settle_ms)
    return True
