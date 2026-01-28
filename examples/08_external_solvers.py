"""
Example 8: External Captcha Providers
=====================================
Shows how to use 3rd party services (2Captcha, CapMonster, Anti-Captcha)
to solve challenges that local solvers might struggle with.

Supported providers: '2captcha', 'capmonster', 'anticaptcha'
"""

import logging
from titan import TitanScraper

# Configure logging to see the solve steps
logging.basicConfig(level=logging.INFO)

def main():
    # 1. Configuration for External Solver
    # Replace with your actual API key!
    captcha_config = {
        "provider": "2captcha", # or 'capmonster', 'anticaptcha'
        "api_key": "YOUR_API_KEY_HERE"
    }
    
    # 2. Initialize TitanScraper with the config
    scraper = TitanScraper(captcha_config=captcha_config)
    
    print("Masking as Windows for consistency...")
    scraper.set_disguise("modern_windows")
    
    # 3. Target URL with reCAPTCHA or Turnstile
    # This URL is a common test target for Cloudflare
    url = "https://nowsecure.nl"
    
    print(f"\nAttempting to bypass {url} using {captcha_config['provider']}...")
    
    try:
        # The bypass method will automatically use the external solver 
        # if a challenge is detected that requires it.
        response = scraper.bypass(url)
        
        print(f"\nStatus Code: {response.status_code}")
        if response.status_code == 200:
            print("[+] Successfully bypassed challenge!")
            print(f"Content Length: {len(response.text)} characters")
        else:
            print("[-] Bypass failed or returned non-200 status.")
            
    except Exception as e:
        print(f"[-] An error occurred: {e}")

if __name__ == "__main__":
    # NOTE: Run this with a valid API key to see it in action.
    # If you don't have a key, it will log an error during the polling step.
    main()
