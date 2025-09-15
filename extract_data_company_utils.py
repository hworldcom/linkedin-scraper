from playwright.async_api import async_playwright
import os
import json
import asyncio
import subprocess
import pyautogui
import random
import time
from next_button_helpers import click_next_page

class WebCrawler:

    def __init__(self, URL, COOKIE_FILE="cookies.json",WINDOW_OFFSET=90):
        self.URL=URL
        self.COOKIE_FILE=COOKIE_FILE
        self.WINDOW_OFFSET=WINDOW_OFFSET

    def __str__(self):
        return f"WebCrawler for {self.URL}"

    async def init(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()

        # Load cookies if available
        await self.__load_cookies()
        self.page = await self.context.new_page()

        await self.safe_login()
        await self.timeout(TIMEOUT_IN_MS=3000)

        is_auth_wall = await self.is_authwall()
        # Check if logged in (e.g., look for profile menu)
        if "login" in self.page.url or "checkpoint" in self.page.url or is_auth_wall==True:
            print("Not logged in. Please log in manually.")
            await self.page.goto(self.URL+"login/")
            print("Waiting for manual login...")
            await self.page.wait_for_timeout(30000)  # Wait 30 seconds to allow manual login
            await self.__save_cookies()
            return True
        else:
            print("Logged in with existing cookies.")
            return True

        return False
    async def start_process(self, URL):
        #start scraping process after login
        await self.page.goto(URL)

    async def start_process_batch(self):
        #start scraping process after login
        return True


    async def is_authwall(self):
        try:
            meta_tag = await self.page.locator('meta[name="pageKey"]').get_attribute('content')
            return meta_tag and meta_tag.startswith("auth_wall")
        except Exception:
            return False


    async def safe_login(self, max_retries=3):
        for attempt in range(max_retries):
            try:
                await self.page.goto("https://www.linkedin.com/login", timeout=6000)
                await self.page.wait_for_load_state("domcontentloaded")
                if "linkedin.com/feed" in self.page.url:
                    print(f"[!] Already Logged in...")
                    return True
                if "linkedin.com/in" in self.page.url:
                    print(f"[!] Already Logged in...")
                    return True
                if "linkedin.com/login" in self.page.url:
                    print(f"[!] Continue to login page...")
                    return True
                print(f"[!] Unexpected URL: {self.page.url}, retrying...")
            except Exception as e:
                print(f"[!] Error loading {self.page.url}: {e}, retrying...")
            await asyncio.sleep(2 + attempt * 2)  # Exponential backoff
        return False


    async def safe_goto(self, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                await self.page.goto(url, timeout=6000)
                await self.page.wait_for_load_state("domcontentloaded")
                if "linkedin.com/feed" in self.page.url:
                    print("[!] Redirected to feed. Trying again")
                    continue
                if "linkedin.com/in/" in self.page.url:
                    return True
                print(f"[!] Unexpected URL: {self.page.url}, retrying...")
            except Exception as e:
                print(f"[!] Error loading {url}: {e}, retrying...")
            await asyncio.sleep(2 + attempt * 2)  # Exponential backoff
        return False

    async def close(self,page=None):
        if page:
            page.close()
        else:
            await self.context.close()  # or await self.page.close()
            await self.browser.close()

    async def locate(self, tag, TIMEOUT=10000):
        location = self.page.locator(tag)
        await location.wait_for(timeout=TIMEOUT)
        return location

    async def locate_no_wait(self, tag:str):
        location = self.page.locator(tag)
        return location

    def locate_within(self, location, tag):
        return location.locator(tag)
    async def locate_all_within(self, location, tag):
        """
        Returns a list of elements matching the tag within the given location.
        """
        locator = location.locator(tag)
        return await locator.all()

    @staticmethod
    def random_scroll(
        min_scrolls=5,
        max_scrolls=15,
        min_delay=0.3,
        max_delay=1.2,
        scroll_speed=0.02  # Lower is faster
    ):
        """
        Simulates human-like scrolling behavior.

        Parameters:
        - min_scrolls / max_scrolls: Number of scroll events
        - min_delay / max_delay: Time between scroll bursts
        - scroll_speed: Time between micro-scroll steps in each event (lower = faster)
        """
        scroll_count = random.randint(min_scrolls, max_scrolls)

        for _ in range(scroll_count):
            total_scroll_units = random.choice([-3, -2, -1, 1, 2, 3])
            steps = abs(total_scroll_units)
            direction = 1 if total_scroll_units > 0 else -1

            for _ in range(steps):
                pyautogui.scroll(direction * 100)  # Typical scroll unit
                time.sleep(scroll_speed + random.uniform(0, 0.01))  # Slight jitter

            time.sleep(random.uniform(min_delay, max_delay))


    @staticmethod
    def random_mouse_movement(margin=5):
        """
        Moves mouse randomly in small steps to simulate idle human behavior.
        Avoids screen edges to prevent FailSafeException.
        """
        screen_width, screen_height = pyautogui.size()
        start_x, start_y = pyautogui.position()

        total_duration = random.uniform(1.5, 3.5)
        step_delay = random.uniform(0.05, 0.15)
        steps = int(total_duration / step_delay)

        for _ in range(steps):
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)

            new_x = max(margin, min(start_x + offset_x, screen_width - margin))
            new_y = max(margin, min(start_y + offset_y, screen_height - margin))

            pyautogui.moveTo(new_x, new_y, duration=random.uniform(0.05, 0.2))
            time.sleep(step_delay)

            start_x, start_y = new_x, new_y

    @staticmethod
    def human_like_mouse_move(dest_x, dest_y, steps=25, jitter=10, total_duration=0.8, margin=5):
        """
        Moves mouse to (dest_x, dest_y) in a human-like, wavy path.
        Ensures it stays away from screen corners.
        """
        screen_width, screen_height = pyautogui.size()

        # Clamp target position inside safe zone
        dest_x = max(margin, min(dest_x, screen_width - margin))
        dest_y = max(margin, min(dest_y, screen_height - margin))

        start_x, start_y = pyautogui.position()
        step_delay = total_duration / steps

        for step in range(steps):
            t = step / steps
            intermediate_x = int(start_x + (dest_x - start_x) * t + random.randint(-jitter, jitter))
            intermediate_y = int(start_y + (dest_y - start_y) * t + random.randint(-jitter, jitter))

            # Clamp every step inside safe zone
            safe_x = max(margin, min(intermediate_x, screen_width - margin))
            safe_y = max(margin, min(intermediate_y, screen_height - margin))

            pyautogui.moveTo(safe_x, safe_y, duration=random.uniform(0.01, 0.03))
            time.sleep(random.uniform(step_delay * 0.8, step_delay * 1.2))

        # Ensure final destination is exact
        pyautogui.moveTo(dest_x, dest_y, duration=0.1)


    async def move_to_location(self, location):

        window_offset = self.__get_window_position()

        # Move to it
        location_box = await location.bounding_box()
        if location_box:
            x =  location_box['x'] + location_box['width'] / 2 + window_offset[0]
            y =  location_box['y'] + location_box['height'] / 2 + window_offset[1]

        #self.random_mouse_movement()
        #self.random_scroll()
        #self.human_like_mouse_move(x, y+self.WINDOW_OFFSET)
        #pyautogui.moveTo(x, y+self.WINDOW_OFFSET, 2, pyautogui.easeOutQuad)

    async def click(self, location):
        await location.click()

    async def wait_to_appear(self,tag):
        await self.page.wait_for_selector(tag, timeout=10000)

    async def type(self, text, DELAY=150):
        await self.page.keyboard.type(text, delay=DELAY)  # type with human-like delay

    async def press_enter(self):
        await self.page.keyboard.press("Enter")

    async def locate_within_scroll(self, text, MAX_SCROLLS=10, DELAY=1): #todo:change scroll number for prod

        for i in range(MAX_SCROLLS):
            # Try to locate the 'Next' button
            next_button = self.page.locator(text)
            #self.random_mouse_movement()

            if await next_button.is_visible():
                # Found the button
                print(f"[✓] Found "+text+" after {i+1} scrolls.")
                return next_button

            await self.page.mouse.wheel(0, 1000)  # Scroll down
            await self.page.wait_for_timeout(DELAY * 1000)



    async def timeout(self, TIMEOUT_IN_MS=5000):
        await self.page.wait_for_timeout(TIMEOUT_IN_MS)

    async def wait_for(self,text, TIMEOUT=10000):
        await self.page.wait_for_selector(text, timeout=TIMEOUT)


    async def __load_cookies(self):

        print("checking cookies...")
        if os.path.exists(self.COOKIE_FILE):
            print("loading cookies")
            with open(self.COOKIE_FILE, "r") as f:
                cookies = json.load(f)
            await self.context.add_cookies(cookies)
    async def locate_all(self, selector, text=None):
        delay = random.uniform(2.5, 4)*1000
        print(f"Sleeping for {delay:.2f} ms...\n")
        await self.page.wait_for_timeout(delay)
        if text:
            return await self.page.locator(selector).filter(has_text=text).all()

        return await self.page.locator(selector).all()

    async def __save_cookies(self):
        print("saving cookies...")
        cookies = await self.context.cookies()
        with open(self.COOKIE_FILE, "w") as f:
            json.dump(cookies, f)

    def __get_window_position(self):
        script = '''
        tell application "System Events"
            tell application process "Chromium"
                set frontWindow to front window
                set pos to position of frontWindow
            end tell
        end tell
        return pos
        '''
        try:
            result = subprocess.check_output(['osascript', '-e', script])
            coords = result.decode().strip().replace("{", "").replace("}", "").split(", ")
            x = int(coords[0])
            y = int(coords[1])
            return x, y
        except Exception as e:
            print(f"[!] AppleScript error: {e}")
            return 0, 0




    async def find_next_button(self):
        # Preferred: LinkedIn's data-testid (most stable)
        btn = self.page.locator('button[data-testid="pagination-control-next-btn"]').first
        if await btn.count():
            return btn

        # Fallback: aria-label contains "Next" (handles "Next page", i18n risk)
        btn = self.page.locator('button[aria-label*="Next" i]').first
        if await btn.count():
            return btn

        # Fallback: role + name (Playwright's accessible name)
        btn = self.page.get_by_role("button", name=lambda n: "next" in n.lower())
        if await btn.count():
            return btn.first

        return None


    async def is_button_disabled(self, btn):
        if not btn:
            return True
        # check multiple patterns
        aria = await btn.get_attribute("aria-disabled")
        if aria and aria.lower() == "true":
            return True
        dis = await btn.get_attribute("disabled")
        if dis is not None:
            return True
        # sometimes class toggles reflect disabled; you can add a heuristic here if needed
        return False

    async def click_next_page(self, results_selector: str, wait_timeout_ms: int = 8000):
        """
        Clicks next and waits for the results to change.
        `results_selector` should be a selector that matches one or more result items.
        Returns True if it navigated, False if there is no next / disabled.
        """
        btn = await self.find_next_button()
        if not btn:
            print("[pagination] Next button not found.")
            return False

        if await self.is_button_disabled(btn):
            print("[pagination] Next is disabled.")
            return False

        # capture a stable thing from current page to detect change
        prev_first = self.page.locator(results_selector).first
        prev_text = ""
        try:
            prev_text = await prev_first.inner_text()
        except Exception:
            pass

        await btn.scroll_into_view_if_needed()
        await btn.click()

        # wait for change: either first item text changes or the list re-renders
        try:
            await self.page.wait_for_timeout(300)  # small debounce
            await self.page.wait_for_function(
                """(sel, prev) => {
                     const el = document.querySelector(sel);
                     if (!el) return false;
                     const t = el.textContent || '';
                     return t.trim() !== (prev || '').trim();
                   }""",
                arg=(results_selector, prev_text),
                timeout=wait_timeout_ms
            )
            return True
        except Exception:
            # as fallback, wait for network idle or small delay
            try:
                await self.page.wait_for_load_state("networkidle", timeout=2000)
            except Exception:
                pass
            return True

async def main():

    COMPANY_NAME = "covivio"
    names, urls = await extract_data_urls_names_company(COMPANY_NAME)

    print("extracted!")


async def extract_data_urls_names_company(crawlingAgent, COMPANY_NAME):
    # Focus the global search
    search_button_location = await crawlingAgent.locate(".search-global-typeahead input")
    await crawlingAgent.click(search_button_location)

    # Search for the company
    await crawlingAgent.type(COMPANY_NAME)
    await crawlingAgent.press_enter()
    await crawlingAgent.timeout()

    # Go to "Companies" tab (support both button and anchor)
    companies_tab = await crawlingAgent.locate("button:has-text('Companies'), a:has-text('Companies')")
    await crawlingAgent.click(companies_tab)

    # Wait for results to render
    await crawlingAgent.wait_to_appear("div.search-results-container")

    # Collect result <li> items
    ul_lists = await crawlingAgent.locate_all("ul[role='list']")
    all_items = []
    for ul in ul_lists:
        items = await crawlingAgent.locate_all_within(ul, "li")
        all_items.extend(items)

    # Pick first valid company result
    company_link = None
    for item in all_items:
        try:
            a_tag = item.locator("a[href*='/company/']").first
            href = await a_tag.get_attribute("href")
            if href and "/company/" in href:
                company_link = a_tag
                break
        except:
            continue

    if not company_link:
        raise Exception("❌ No valid company link found.")

    # Open the company page
    await company_link.click()

    # Click the "employees" link on the org top card
    employee_button = await crawlingAgent.locate(
        "div.org-top-card-summary-info-list div.inline-block >> a:has(span:has-text('employees'))"
    )
    await crawlingAgent.click(employee_button)

    # ---- NEW: robust selector for Connections filter radios ----
    # They are now <div role="radio"> with a <label> containing '1st', '2nd', '3rd+'.
    # We scope to the top filter bar/toolbar to avoid accidental matches.
    # Try '2nd' first; if not visible, fall back to opening the filters bar or retry.
    async def click_connection_degree(degree_text: str):
        # Most reliable: click the label directly (it toggles the underlying checkbox/radio)
        # Narrow scope to filter toolbar: role=toolbar (present on the results page)
        degree_label = crawlingAgent.page.locator(
            "div[role='toolbar'] label:has-text('%s')" % degree_text
        )
        # Fallback: any visible label with text
        if not await degree_label.first.is_visible():
            degree_label = crawlingAgent.page.locator("label:has-text('%s')" % degree_text)

        await degree_label.first.scroll_into_view_if_needed()
        await degree_label.first.click()

        # Wait for results to refresh (either network idle or a small debounce)
        await crawlingAgent.timeout(TIMEOUT_IN_MS=1500)

    # Click "2nd" (or "1st" if you prefer)
    await click_connection_degree("2nd")

    # Optional: ensure it actually toggled (aria-checked="true")
    # We check the closest radio with that label
    second_radio = crawlingAgent.page.locator(
        "div[role='radio']:has(label:has-text('2nd'))"
    ).first
    try:
        await second_radio.wait_for(state="attached", timeout=2000)
        checked = await second_radio.get_attribute("aria-checked")
        if checked != "true":
            # Click again if needed (LinkedIn sometimes swallows clicks on fast pages)
            await (crawlingAgent.page.locator("label:has-text('2nd')").first).click()
            await crawlingAgent.timeout(TIMEOUT_IN_MS=1000)
    except:
        pass

    # ---- extract names/urls from the search results ----
    profile_names = []
    profile_urls = []
    await extract_data_names_urls(crawlingAgent, profile_names, profile_urls)

    return (profile_names, profile_urls)


async def extract_data_names_urls(crawlingAgent, profile_names, profile_urls):
    while True:
        await extract_page_names_urls(crawlingAgent, profile_names, profile_urls)

        try:
            did_advance = await click_next_page(crawlingAgent.page)
            if not did_advance:
                print("[!] No next page (missing or disabled).")
                break
        except Exception as e:
            print(f"[!] Could not go to next page: {e}")
            break




async def extract_page_names_urls(crawlingAgent, profile_names, profile_urls):
    # wait for any result to show
    await crawlingAgent.page.wait_for_selector('[data-view-name="people-search-result"]', timeout=15000)
    cards = await crawlingAgent.page.locator('[data-view-name="people-search-result"]').all()

    for i, card in enumerate(cards):
        try:
            # Prefer the explicit title link
            title_link = card.locator('a[data-view-name="search-result-lockup-title"]').first
            if await title_link.count() > 0:
                name = (await title_link.inner_text()).strip()
                href = await title_link.get_attribute("href")
            else:
                # Fallback: any link to /in/...
                any_profile = card.locator('a[href*="linkedin.com/in/"]').first
                href = await any_profile.get_attribute("href")
                # Fallback name: the first <p> with the lockup title structure
                name_p = card.locator('p >> a[href*="linkedin.com/in/"]').first
                name = (await name_p.inner_text()).strip() if await name_p.count() > 0 else "(unknown)"

            if href:
                profile_urls.append(href)
                profile_names.append(name)
                print(f"[✓] {name} → {href}")
        except Exception as e:
            print(f"[!] Error on card {i}: {e}")

    # small jitter to mimic human dwell, helps with lazy hydration
    await crawlingAgent.page.wait_for_timeout(500 + random.randint(0, 400))



if __name__ == '__main__':
    asyncio.run(main())



