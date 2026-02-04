import asyncio
import random
import re
from playwright.async_api import async_playwright
from browser_manager import BrowserManager


QUESTS_MAP = [
    {
        "title": "Daily Check in", 
        "button": "CHECK IN"
    }
]
class BotLogic:
    def __init__(self, log_callback):
        self.log = log_callback
        self.stop_event = asyncio.Event()
        self.browser_manager = BrowserManager()

    async def run_batch(self, items, thread_count):
    
        self.stop_event.clear()
        semaphore = asyncio.Semaphore(thread_count)
        
        async def worker(item):
            async with semaphore:
                if self.stop_event.is_set(): return
                profile_id = item['id']
                await self.process_profile(profile_id)

        tasks = [worker(item) for item in items]
        await asyncio.gather(*tasks)
        self.log("Batch sequence completed.")

    async def emergency_stop(self):
        self.stop_event.set()
        self.log("Stopping all threads...", "error")

    async def process_profile(self, profile_id):
        if self.stop_event.is_set(): return
        
        self.log(f"[{profile_id}] Starting AdsPower...")
    
        ws_url = self.browser_manager.start_profile(profile_id)
        
        if not ws_url:
            self.log(f"[{profile_id}] Failed to open browser (Check AdsPower is running).", "error")
            return

        playwright = None
        browser = None
        page = None
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.connect_over_cdp(ws_url)
            
            if not browser.contexts:
                self.log(f"[{profile_id}] No context found.", "error")
                return

            context = browser.contexts[0]
            
            page = await context.new_page()
            
            await self.navigate_to_quest(page, profile_id)

            await self.execute_quests(page, profile_id)

        except Exception as e:
            self.log(f"[{profile_id}] Critical Error: {str(e)}", "error")
        finally:
            if page: 
                try: await page.close()
                except: pass
            if browser: 
                try: await browser.close()
                except: pass
            if playwright: 
                try: await playwright.stop()
                except: pass
            
            self.browser_manager.stop_profile(profile_id)
            self.log(f"[{profile_id}] Session ended.")

    async def navigate_to_quest(self, page, profile_id):
        for attempt in range(3):
            if self.stop_event.is_set(): return
            try:
                self.log(f"[{profile_id}] Loading portal...")
                await page.goto("https://www.trex.xyz/portal/quest", timeout=60000, wait_until='domcontentloaded')
                
                try:
                    await page.wait_for_selector("text=Daily Check in", timeout=15000)
                    return 
                except:
                    if await page.get_by_text("Login").count() > 0 or await page.get_by_text("Sign in").count() > 0:
                        raise Exception("Login required")
                    self.log(f"[{profile_id}] Slow load, retrying...")
            
            except Exception as e:
                if "Login required" in str(e): raise e
                self.log(f"[{profile_id}] Load attempt {attempt+1} failed.", "warn")
                await asyncio.sleep(2)
        
        raise Exception("Failed to load page")

    async def execute_quests(self, page, profile_id):
        self.log(f"[{profile_id}] Scanning for 'Daily Check in'...")
        
        for quest in QUESTS_MAP:
            if self.stop_event.is_set(): return
            
            title = quest['title']
            btn_text = quest['button']
            
            try:
                quest_card = page.locator("div").filter(has_text=title).filter(has=page.locator("button")).last
                
                if await quest_card.count() == 0:
                    self.log(f"[{profile_id}] Quest not found (Already done?).", "warn")
                    continue

                btn = quest_card.get_by_role("button", name=btn_text).first
                
                if await btn.is_visible() and await btn.is_enabled():
                    await btn.click()
                    self.log(f"[{profile_id}] SUCCESS: Clicked CHECK IN")
                    await asyncio.sleep(3) 
                else:
                    self.log(f"[{profile_id}] Button not active or already clicked.")

            except Exception as e:
                self.log(f"[{profile_id}] Error: {e}", "error")