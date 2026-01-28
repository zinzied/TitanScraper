"""
Example 4: Manual Module Control

Sometimes you don't want the "Magic" bypass() button.
You want full control over specific modules.
"""

from titan import TitanScraper

def main():
    scraper = TitanScraper()
    url = "https://nowsecure.nl"
    
    # --- MODULE 1: JSD SOLVER (Go) ---
    # Check if a site has a Cloudflare "Just a moment" challenge
    print("Checking JSD Solver...")
    if scraper.jsd_solver.is_available():
        result = scraper.jsd_solver.solve(url)
        print(f"JSD Result: {result}")
        # Apply cookies manually if needed
        # scraper.cookies.set("cf_clearance", result['cf_clearance'])
    
    # --- MODULE 2: BROWSER MANAGER (Playwright) ---
    # Launch browser manually to get content, screenshots, or cookies
    print("\nLaunching Browser Manager...")
    
    # Get Cookies only
    try:
        cookies, ua = scraper.browser_manager.get_cookies(url)
        print(f"Extracted {len(cookies)} cookies via Browser")
    except Exception as e:
        print(f"Browser Error: {e}")

    # Ghost Cursor is automatically used in browser calls
    
    # --- MODULE 3: CAPTCHA SOLVER ---
    print("\nChecking Turnstile...")
    # You can inspect HTML for turnstile
    # html = scraper.get(url).text
    # if scraper.captcha_solver.is_turnstile_challenge(html, ...):
    #     pass

if __name__ == "__main__":
    main()
