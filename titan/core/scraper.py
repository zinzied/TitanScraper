"""
TitanScraper Core
=================
The main scraper class that integrates all anti-detection modules.
"""

import requests
import logging
from typing import Dict, Any, Union

from ..modules.ml import MLBypassOrchestrator
from ..modules.tls import TLSManager
from ..modules.stealth import StealthManager
from ..modules.browser import BrowserManager
from ..modules.captcha import TurnstileSolver
from ..modules.jsd_solver import JSDSolver
from ..modules.disguise import DisguiseManager
from urllib.parse import urlparse

try:
    from curl_cffi import requests as crequests
    HAS_CURL = True
except ImportError:
    HAS_CURL = False
    
# Base class selection
BaseSession = crequests.Session if HAS_CURL else requests.Session

class TitanScraper(BaseSession):
    """
    The main TitanScraper class.
    Inherits from curl_cffi.requests.Session (if available) for TLS impersonation.
    """
    
    def __init__(self, 
                 browser_type: str = 'chrome',
                 use_ml: bool = True,
                 use_captcha: bool = True,
                 proxies: dict = None,
                 captcha_config: dict = None):
                 
        super().__init__()
        
        # Core Components
        self.browser_type = browser_type
        self.use_ml = use_ml
        # self.proxies is inherited from requests.Session, but we can init it
        if proxies:
            self.proxies.update(proxies)
            
        self.use_playwright = False # Toggle specific to request wrapperlize modules
        self.tls = TLSManager(browser_type)
        self.stealth = StealthManager()
        self.ml_orchestrator = MLBypassOrchestrator(self) if use_ml else None
        self.browser_manager = BrowserManager()
        self.captcha_config = captcha_config or {}
        self.captcha_solver = TurnstileSolver(provider_config=self.captcha_config)
        self.jsd_solver = JSDSolver()
        self.disguise = DisguiseManager("modern_windows") # Default Disguise
        
        # Configure initial headers
        self.headers.update(self.stealth.transform_headers({
            'User-Agent': self.disguise.get_profile()['user_agent'],
        }))
        
        # Mount adapters if needed (for TLS - placeholder)
        # self.mount('https://', TLSAdapter(self.tls.ssl_context))

    def set_disguise(self, profile_name: str):
        """Set the consistency profile (e.g. 'modern_mac', 'modern_windows')."""
        self.disguise.set_profile(profile_name)
        p = self.disguise.get_profile()
        self.headers['User-Agent'] = p['user_agent']
        logging.info(f"Disguise set to: {profile_name}")

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Override request to inject anti-detection logic.
        """
        
        # 1. ML Optimization
        if self.ml_orchestrator:
            optimization = self.ml_orchestrator.optimize_request(url)
            if optimization.get('optimized'):
                # Apply strategy logic here (adjust timeouts, headers, etc)
                pass

        # 2. Stealth Headers
        if 'headers' in kwargs:
            kwargs['headers'] = self.stealth.transform_headers(kwargs['headers'])
        else:
            # Refresh default headers
            self.headers = self.stealth.transform_headers(self.headers)

        # 3. Execution
        try:
            # Check if we should use Playwright directly
            if self.use_playwright:
                return self._request_via_playwright(method, url, **kwargs)
                
            # TLS Impersonation (curl_cffi)
            if HAS_CURL and "impersonate" not in kwargs:
                # Default to the active Disguise Profile
                kwargs["impersonate"] = self.disguise.get_profile()["impersonate"]
                
            # If standard requests (no curl), we might want to ensure verify is set or handled
            
            # Super call (handles either requests.Session or curl_cffi.Session)
            if HAS_CURL:
                # curl_cffi uses 'impersonate' arg
                response = super().request(method, url, **kwargs)
            else:
                # Strip incompatible args if fallback to standard requests
                kwargs.pop("impersonate", None)
                response = super().request(method, url, **kwargs)
            
            # 4. Challenge Handling
            if response.status_code in [403, 503]:
                 # Check for Cloudflare JSD challenge
                 if "Just a moment" in response.text and self.jsd_solver.is_available():
                     logging.info(f"Detected Cloudflare challenge on {url}. Attempting to solve with JSD Solver...")
                     result = self.jsd_solver.solve(url)
                     
                     if result.get("success"):
                         logging.info("JSD Solver success! Updating cookies and retrying...")
                         # Set cf_clearance cookie
                         domain = urlparse(url).hostname
                         self.cookies.set("cf_clearance", result.get("cf_clearance"), domain=domain)
                         
                         # Retry the request with new cookies
                         return super().request(method, url, **kwargs)
                     else:
                         logging.warning(f"JSD Solver failed: {result.get('error')}")

                 # Fallback: Browser Solver
                 # Broaden check: If we are here (403/503) and JSD didn't fix it, try Browser if it looks like a challenge OR simple 403
                 is_challenge_text = "Just a moment" in response.text or "checking your browser" in response.text.lower()
                 
                 if is_challenge_text or response.status_code == 403:
                     logging.info("Falling back to Browser Solver (Full Fetch)...")
                     
                     # Pass current UA and Cookies
                     current_ua = self.headers.get('User-Agent')
                     current_cookies = self.cookies.get_dict()
                     
                     result = self.browser_manager.get_content(
                         url, 
                         user_agent=current_ua,
                         proxy=kwargs.get("proxies") or self.proxies,
                         cookies=current_cookies
                     )
                     
                     if result.get("content"):
                         logging.info(f"Browser Fetch Success! UA: {str(result.get('ua'))[:20]}...")
                         
                         # Update session with new cookies/UA for future requests
                         if result.get("cookies"):
                             self.cookies.update(result["cookies"])
                         if result.get("ua"):
                             self.headers['User-Agent'] = result["ua"]
                             
                         # Construct a Response object
                         new_resp = requests.Response()
                         new_resp.status_code = result.get("status", 200)
                         new_resp._content = result["content"].encode('utf-8')
                         new_resp.url = result.get("url", url)
                         # Simple headers
                         new_resp.headers = requests.structures.CaseInsensitiveDict({
                             "Content-Type": "text/html",
                             "User-Agent": result.get("ua")
                         })
                         
                         return new_resp
                     else:
                         logging.warning("Browser Solver failed to fetch content.")

                 if self.captcha_solver.is_turnstile_challenge(response.text, response.headers, response.status_code):
                     # Logic to solve turnstile would go here
                     # For now we might fallback to playwright if regular solve fails
                     pass

            # 5. ML Recording
            if self.ml_orchestrator:
                self.ml_orchestrator.record_outcome(url, response.ok, 0.5, response.status_code)

            return response

        except Exception as e:
            if self.ml_orchestrator:
                self.ml_orchestrator.record_outcome(url, False, 0.0, 0)
            raise e

    def save_session(self, path: str):
        """Save current cookies and headers to a file."""
        import json
        data = {
            "cookies": self.cookies.get_dict(),
            # "headers": dict(self.headers) # Headers might be too much, but cookies are key
        }
        with open(path, 'w') as f:
            json.dump(data, f)
        logging.info(f"Session saved to {path}")

    def load_session(self, path: str):
        """Load cookies from a file."""
        import json
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            if "cookies" in data:
                self.cookies.update(data["cookies"])
            logging.info(f"Session loaded from {path}")
        except FileNotFoundError:
            logging.warning(f"Session file {path} not found.")

    def _detect_protection(self, response: requests.Response) -> str:
        """Identify the Anti-Bot system based on headers and content."""
        headers = response.headers
        text = response.text.lower()
        
        # Cloudflare
        if "server" in headers and "cloudflare" in headers["server"].lower():
            if "just a moment" in text or "turnstile" in text:
                return "cloudflare_challenge"
            return "cloudflare_generic"
            
        # Akamai
        if "akamai" in text or "akamai" in headers.get("server", "").lower() or "akamai" in headers.get("x-akamai-transformed", "").lower():
            return "akamai"
            
        # Incapsula / Imperva
        if "visid_incap" in response.cookies or "incapsula" in text or "_incap_" in text:
            return "incapsula"
            
        # Datadome
        if "datadome" in response.cookies or "datadome" in text:
            return "datadome"
            
        # AWS WAF
        if "awselb" in response.cookies or "x-amz-request-id" in headers:
            if response.status_code == 403:
                return "aws_waf"
                
        # Generic 403
        if response.status_code == 403:
            return "generic_403"
            
        return "none"

    def bypass(self, url: str) -> requests.Response:
        """
        Unified 'One-Click' method to bypass antibot protections.
        Automatically detects protection type and selects the best strategy.
        """
        logging.info(f"TitanScraper: Analyzing {url}...")
        
        # 1. Initial Probe (Lightweight)
        # Use a standard Chrome fingerprint
        try:
            resp = self.get(url, impersonate="chrome120")
        except Exception:
            # If plain connection fails, assume network block or aggressive filter
            resp = None

        if resp and resp.ok:
            # Double check it's not a "200 OK" challenge page
            protection = self._detect_protection(resp)
            if protection == "none":
                return resp
                
        # 2. Analyze Protection
        protection = self._detect_protection(resp) if resp else "unknown"
        logging.info(f"TitanScraper: Detected Protection = {protection.upper()}")
        
        # 3. Select Strategy
        if protection in ["cloudflare_challenge", "cloudflare_generic"]:
             # Strategy: Try JSD -> If fail, Browser
             if self.jsd_solver.is_available():
                 # request() hook handles checking for JSD success
                 # We just need to trigger a request that might trigger the hook
                 # usage of .get() with the hook enabled in request() should work
                 logging.info("Strategy: Engaging Cloudflare Solvers...")
                 pass 
             
             # If we are here, it means JSD might have run inside `self.get` above or detection found it.
             # Let's try the Ultimate Fallback immediately for challenges
             logging.info("Strategy: Cloudflare detected. Triggering Browser Engine...")
             return self._browser_fallback(url)

        elif protection in ["akamai", "incapsula", "datadome"]:
            # Strategy: Browser is usually required for these JS-heavy checks
            logging.info(f"Strategy: {protection} detected. Converting to Browser Engine...")
            return self._browser_fallback(url)
            
        elif protection == "aws_waf" or protection == "generic_403":
            # Strategy: Rotate TLS Fingerprints
            # AWS WAF often blocks specific TLS fingerprints (e.g. Python requests)
            # We already tried chrome120. Let's try others.
            logging.info("Strategy: 403 Forbidden. Rotating TLS Fingerprints...")
            
            fingerprints = ["safari15_3", "firefox109", "ios15_5"] # curl_cffi options
            for fp in fingerprints:
                logging.info(f"Trying TLS: {fp}...")
                try:
                    retry_resp = self.get(url, impersonate=fp)
                    if retry_resp.ok:
                        logging.info(f"Success with {fp}!")
                        return retry_resp
                except Exception as e:
                    logging.warning(f"TLS {fp} failed: {e}")
                    
            # If all TLS fail, try browser
            return self._browser_fallback(url)

        # Default: Return the probe response or browser fallback if None
        if resp:
            return resp
        return self._browser_fallback(url)

    def _browser_fallback(self, url: str) -> requests.Response:
        """Helper to run browser fallback and wrap response."""
        
        # Disguise Configuration
        profile = self.disguise.get_profile()
        init_script = self.disguise.get_injection_script()
        viewport = {"width": profile["viewport_width"], "height": profile["viewport_height"]}
        
        result = self.browser_manager.get_content(
            url, 
            user_agent=profile["user_agent"], # Enforce Disguise UA
            proxy=self.proxies,
            cookies=self.cookies.get_dict(),
            viewport=viewport,
            extra_scripts=[init_script],
            captcha_config=self.captcha_config
        )
        
        # Sync Session
        if result.get("cookies"):
            self.cookies.update(result["cookies"])
        if result.get("ua"): # Should match profile UA
            self.headers['User-Agent'] = result["ua"]

        # Construct Response
        new_resp = requests.Response()
        new_resp.status_code = result.get("status", 200)
        new_resp._content = result["content"].encode('utf-8') if isinstance(result.get("content"), str) else b""
        new_resp.url = result.get("url", url)
        new_resp.headers = requests.structures.CaseInsensitiveDict({
             "Content-Type": "text/html",
             "User-Agent": result.get("ua")
        })
        return new_resp

    def _request_via_playwright(self, method, url, **kwargs):
        """Fallback/Direct use of Playwright"""
        # This returns a requests.Response object constructed from Playwright response
        # Placeholder implementation
        import requests
        resp = requests.Response()
        resp.status_code = 200
        resp._content = b"Content fetched via Playwright (Placeholder)"
        return resp

    def get_tokens(self, url: str):
        """Helper to get cookies/tokens via Playwright"""
        return self.browser_manager.get_cookies(url)
