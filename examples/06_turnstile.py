"""
Example 6: Cloudflare Turnstile Solver

TitanScraper automatically detects and solves Cloudflare Turnstile.
This includes the "Verify you are human" checkbox.

The BrowserManager uses 'Ghost Cursor' to click the widget human-like.
"""

from titan import TitanScraper

def main():
    scraper = TitanScraper()
    
    # A site known for Turnstile (or just generic Cloudflare)
    # peet.ws is a good test for Turnstile specifically if available
    url = "https://nowsecure.nl" 
    
    print(f"Testing Turnstile Bypass on {url}...")
    
    # We use bypass() which invokes Browser Fallback if needed
    response = scraper.bypass(url)
    
    print(f"Status: {response.status_code}")
    if response.ok:
        print("[+] Success: content retrieved.")
    else:
        print("[-] Failed.")

if __name__ == "__main__":
    main()
