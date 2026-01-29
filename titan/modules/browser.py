"""
Browser Module
==============
Handles Playwright interaction for advanced bypass.
"""

import time
import random
import logging
import math
import numpy as np
from typing import Dict, Any, Tuple, Optional
from .stealth import StealthManager
from .recaptcha import RecaptchaSolver

logger = logging.getLogger(__name__)

def bezier_curve(points, n_steps=100):
        """Generate bezier curve points."""
        n_points = len(points)
        x_points = np.array([p[0] for p in points])
        y_points = np.array([p[1] for p in points])

        t = np.linspace(0.0, 1.0, n_steps)

        polynomial_array = np.array([
            (math.factorial(n_points - 1) / 
             (math.factorial(i) * math.factorial(n_points - 1 - i))) * 
            (t ** i) * ((1 - t) ** (n_points - 1 - i)) 
            for i in range(n_points)
        ])

        xvals = np.dot(x_points, polynomial_array)
        yvals = np.dot(y_points, polynomial_array)

        return list(zip(xvals, yvals))

class BrowserManager:
    """Manages Playwright browser for bypass"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.stealth = StealthManager()
        
    def get_cookies(self, url: str, timeout: int = 30, user_agent: str = None, proxy: Dict[str, str] = None, cookies: Dict = None, viewport: Dict[str, int] = None, extra_scripts: list = None) -> Tuple[Dict[str, str], str]:
        """Get Cloudflare cookies using Playwright with enhanced stealth."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("Playwright not installed. Cannot use browser fallback.")
            return {}, None
            
        cookies_dict = {}
        
        with sync_playwright() as p:
            launch_args = self.stealth.get_browser_args()
            # Add args to reduce detection
            # launch_args.extend([
            #     "--disable-blink-features=AutomationControlled",
            # ]) # Already in stealth.get_browser_args now + UA + Window Size
            
            # Proxy Config
            pw_proxy = None
            if proxy:
                # Assuming requests format: {'http': 'http://user:pass@host:port', 'https': ...}
                # Playwright needs: {'server': 'http://host:port', 'username': 'user', 'password': 'pass'}
                # Simplified parsing for common format "http://user:pass@host:port"
                p_url = proxy.get('https') or proxy.get('http')
                if p_url:
                    if "@" in p_url:
                        from urllib.parse import urlparse
                        parsed = urlparse(p_url)
                        pw_proxy = {
                            "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
                            "username": parsed.username,
                            "password": parsed.password
                        }
                    else:
                        pw_proxy = {"server": p_url}

            browser = p.chromium.launch(
                headless=self.headless, 
                args=launch_args,
                proxy=pw_proxy
            )
            
            # Context with fingerprint details
            fp = self.stealth.get_fingerprint()
            if viewport:
                 fp['viewport_width'] = viewport.get('width', 1920)
                 fp['viewport_height'] = viewport.get('height', 1080)
                 
            context_options = {
                "viewport": {"width": fp['viewport_width'], "height": fp['viewport_height']},
                "device_scale_factor": 1,
                "user_agent": fp['user_agent'],
                "locale": fp['locale'],
                "timezone_id": fp['timezone']
            }
            if user_agent: # Override if provided
                context_options['user_agent'] = user_agent
                
            context = browser.new_context(**context_options)

            # Add cookies if provided
            if cookies:
                # Playwright expects list of dicts: {'name':, 'value':, 'domain':, 'path':}
                # Request cookies are simple dict. We need domain.
                from urllib.parse import urlparse
                domain = urlparse(url).hostname
                p_cookies = []
                for k, v in cookies.items():
                    p_cookies.append({
                        "name": k, "value": v, "domain": domain, "path": "/"
                    })
                context.add_cookies(p_cookies)
            
            # Injection to hide webdriver
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # Inject Deep Stealth Scripts
            for script in self.stealth.get_stealth_scripts():
                context.add_init_script(script)
                
            # Inject Extra Scripts (Disguise)
            if extra_scripts:
                for script in extra_scripts:
                    context.add_init_script(script)
            
            page = context.new_page()
            
            try:
                logger.info(f"Browser: Navigating to {url}...")
                page.goto(url, wait_until='domcontentloaded', timeout=timeout*1000)
                
                # Human behavior simulation
                self._simulate_human_behavior(page)
                
                # Wait for challenge resolution (checking for cf_clearance)
                start_time = time.time()
                while time.time() - start_time < timeout:
                    cookies = context.cookies()
                    cf_clearance = next((c for c in cookies if c['name'] == 'cf_clearance'), None)
                    
                    if cf_clearance:
                        logger.info("Browser: Successfully extracted cf_clearance cookie!")
                        break
                        
                    # Check if we are still on a challenge page
                    content = page.content().lower()
                    if "just a moment" not in content and "checking your browser" not in content:
                        # Maybe we passed it but didn't get the cookie? Or it wasn't a challenge?
                        # Let's wait a bit more to be sure
                        time.sleep(1)
                    else:
                        # Still challenged, move mouse again
                        self._simulate_human_behavior(page)
                        
                    time.sleep(1)
                    
                # Final cookie extraction
                for cookie in context.cookies():
                    cookies_dict[cookie['name']] = cookie['value']
                    
                # Get the actual User Agent used
                final_ua = page.evaluate("navigator.userAgent")
                    
            except Exception as e:
                logger.error(f"Browser Error: {e}")
            finally:
                browser.close()
                
        return cookies_dict, final_ua

    def get_content(self, url: str, timeout: int = 30, user_agent: str = None, proxy: Dict[str, str] = None, cookies: Dict = None, viewport: Dict[str, int] = None, extra_scripts: list = None, captcha_config: Dict = None, block_resources: bool = True) -> Dict[str, Any]:
        """Fetch full page content using Playwright (Ultimate Bypass)."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("Playwright not installed.")
            return {"content": "", "status": 0, "cookies": {}, "ua": None}
            
        result = {"content": "", "status": 0, "cookies": {}, "ua": None}
        
        with sync_playwright() as p:
            launch_args = self.stealth.get_browser_args()
            # launch_args.extend(["--disable-blink-features=AutomationControlled"]) # In stealth args

            # Proxy Logic (Duplicate from get_cookies - Refactor later?)
            pw_proxy = None
            if proxy:
                p_url = proxy.get('https') or proxy.get('http')
                if p_url:
                    if "@" in p_url:
                        from urllib.parse import urlparse
                        parsed = urlparse(p_url)
                        pw_proxy = {
                            "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
                            "username": parsed.username,
                            "password": parsed.password
                        }
                    else:
                        pw_proxy = {"server": p_url}
            
            browser = p.chromium.launch(headless=self.headless, args=launch_args, proxy=pw_proxy)
            
            fp = self.stealth.get_fingerprint()
            if viewport:
                 fp['viewport_width'] = viewport.get('width', 1920)
                 fp['viewport_height'] = viewport.get('height', 1080)

            context_options = {
                "viewport": {"width": fp['viewport_width'], "height": fp['viewport_height']},
                "device_scale_factor": 1,
                "user_agent": fp['user_agent'],
                "locale": fp['locale'],
                "timezone_id": fp['timezone']
            }
            if user_agent:
                context_options['user_agent'] = user_agent
                
            context = browser.new_context(**context_options)
            
            if cookies:
                from urllib.parse import urlparse
                domain = urlparse(url).hostname
                p_cookies = []
                for k, v in cookies.items():
                    p_cookies.append({
                        "name": k, "value": v, "domain": domain, "path": "/"
                    })
                context.add_cookies(p_cookies)

            # Inject Deep Stealth Scripts
            for script in self.stealth.get_stealth_scripts():
                context.add_init_script(script)
                
            # Inject Extra Scripts (Disguise)
            if extra_scripts:
                for script in extra_scripts:
                    context.add_init_script(script)
                
            page = context.new_page()

            # Resource Blocking
            if block_resources:
                def intercept_route(route):
                    if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
                        route.abort()
                    else:
                        route.continue_()
                page.route("**/*", intercept_route)

            try:
                logger.info(f"Browser: Fetching content from {url}...")
                resp = page.goto(url, wait_until='domcontentloaded', timeout=timeout*1000)
                
                # Human behavior simulation
                self._simulate_human_behavior(page)
                
                # Challenge Loop
                start_time = time.time()
                while time.time() - start_time < timeout:
                    content = page.content().lower()
                    
                    # 1. Check Cloudflare
                    if "just a moment" not in content and "checking your browser" not in content:
                        # 2. Check reCAPTCHA
                        # We use the solver to check and solve
                        if "recaptcha" in content:
                           # Try solving
                           logger.info("Browser: reCAPTCHA detected. Attempting to solve...")
                           try:
                               from .recaptcha import RecaptchaSolver
                               solver = RecaptchaSolver(provider_config=captcha_config)
                               if solver.solve_v2(page):
                                   logger.info("Browser: reCAPTCHA solved!")
                                   # Give it a moment to redirect/reload
                                   time.sleep(3)
                                   continue # Re-evaluate content
                           except Exception as e:
                               logger.warning(f"Browser: reCAPTCHA solve error: {e}")

                        # 3. Check Cloudflare Turnstile
                        turnstiles = page.locator("iframe[src*='challenges.cloudflare.com'], .cf-turnstile")
                        if turnstiles.count() > 0:
                             logger.info("Browser: Turnstile detected. Checking if we need to click...")
                             try:
                                 if turnstiles.first.is_visible():
                                     logger.info("Browser: Clicking Turnstile widget...")
                                     self.human_click(page, "iframe[src*='challenges.cloudflare.com']")
                                     time.sleep(2)
                             except Exception as e:
                                 logger.warning(f"Browser: Turnstile click error: {e}")

                        # If no challenges known are present... break?
                        # But wait, what if reCAPTCHA is just a small part of the page (login form)?
                        # For "Full Fetch", we mainly just want to bypass the BLOCKING pages.
                        # If it's a login form captcha, we might process it, but usually we break if the *page content* is loaded.
                        
                        # Assuming blocking pages (CF or explicit captcha page) are the main hurdles.
                        # If we are strictly blocked, we stay in loop.
                        # If "google.com/recaptcha" is in frames but page text is visible, we might be fine.
                        
                        # Simplified: Break if CF is gone.
                        break
                        
                    time.sleep(1)
                    self._simulate_human_behavior(page)
                
                # Capture final state
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except:
                    pass
                    
                result["content"] = page.content()
                result["status"] = 200 # Playwright response status might be 403 originally, but if we passed...
                # Actually, let's use the last response status if possible, but page.content() is what matters.
                # If we passed the challenge, we treat it as 200 (success) usually.
                
                cookies_dict = {}
                for cookie in context.cookies():
                    cookies_dict[cookie['name']] = cookie['value']
                result["cookies"] = cookies_dict
                
                result["ua"] = page.evaluate("navigator.userAgent")
                result["url"] = page.url
                
            except Exception as e:
                logger.error(f"Browser Content Error: {e}")
            finally:
                browser.close()
                
        return result

    def save_element_screenshot(self, url: str, selector: str, output_path: str, timeout: int = 30):
        """
        Navigate to a URL and save a screenshot of a specific element (e.g. captcha image).
        Useful for dataset collection.
        """
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                launch_args = self.stealth.get_browser_args()
                browser = p.chromium.launch(headless=self.headless, args=launch_args)
                context = browser.new_context()
                page = context.new_page()
                
                try:
                    logger.info(f"Browser: Navigating to {url} for screenshot...")
                    page.goto(url, wait_until='domcontentloaded', timeout=timeout*1000)
                    
                    # Wait for element
                    element = page.wait_for_selector(selector, timeout=timeout*1000)
                    if element:
                        element.screenshot(path=output_path)
                        logger.info(f"Screenshot saved to {output_path}")
                        return True
                    else:
                        logger.warning(f"Element {selector} not found.")
                        return False
                        
                finally:
                    browser.close()
                    
        except Exception as e:
            logger.error(f"Screenshot Error: {e}")
            return False

    def _human_move_mouse(self, page, start_x, start_y, end_x, end_y):
        """Move mouse in a human-like bezier curve."""
        try:
            steps = random.randint(20, 50)
            
            # Control points for bezier (add randomness)
            ctrl1_x = start_x + random.randint(-100, 100)
            ctrl1_y = start_y + random.randint(-100, 100)
            ctrl2_x = end_x + random.randint(-100, 100)
            ctrl2_y = end_y + random.randint(-100, 100)

            points = [(start_x, start_y), (ctrl1_x, ctrl1_y), (ctrl2_x, ctrl2_y), (end_x, end_y)]
            path = bezier_curve(points, steps)
            
            for point in path:
                page.mouse.move(point[0], point[1])
                # Variable sleep for realistic velocity
                time.sleep(random.uniform(0.001, 0.003))
                
        except Exception as e:
            logger.error(f"Mouse Move Error: {e}")

    def human_click(self, page, selector: str):
        """Move to element human-like and click."""
        try:
            element = page.wait_for_selector(selector, timeout=5000)
            if element:
                box = element.bounding_box()
                if box:
                    # Current position could be tracked, but let's assume random start or last pos
                    # For simplicity, we just move "from somewhere" to target
                    start_x = random.randint(0, 1000) 
                    start_y = random.randint(0, 1000)
                    
                    target_x = box["x"] + box["width"] / 2
                    target_y = box["y"] + box["height"] / 2
                    
                    # Add some jitter to target
                    target_x += random.uniform(-box["width"]/4, box["width"]/4)
                    target_y += random.uniform(-box["height"]/4, box["height"]/4)
                    
                    self._human_move_mouse(page, start_x, start_y, target_x, target_y)
                    time.sleep(random.uniform(0.1, 0.3))
                    page.mouse.down()
                    time.sleep(random.uniform(0.05, 0.15))
                    page.mouse.up()
                    
        except Exception as e:
            logger.error(f"Human Click Error: {e}")
            return False

    def _simulate_human_behavior(self, page):
        """Simulate random mouse movements to pass heuristic checks."""
        try:
            # Random mouse movements
            for _ in range(3):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                page.mouse.move(x, y, steps=10)
                time.sleep(random.uniform(0.1, 0.3))
        except Exception:
            pass

    async def get_cookies_async(self, url: str, timeout: int = 30) -> Dict[str, str]:
        # Async implementation placeholder
        raise NotImplementedError("Async not yet implemented in Titan")
