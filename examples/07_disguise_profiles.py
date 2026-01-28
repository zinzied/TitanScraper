"""
Example 7: Disguise Profiles (Consistency Mode)

TitanScraper allows you to disguise your scraper as:
- Modern Windows (Chrome)
- Modern Mac (Safari)

This enforces 100% fingerprint consistency for TLS, Headers, and Hardware.
Use this for Cloudflare Enterprise / V3.
"""

from titan import TitanScraper

def main():
    scraper = TitanScraper()
    
    # 1. Be a Mac
    print("Masking as Mac...")
    scraper.set_disguise("modern_mac")
    
    # Verify
    resp = scraper.get("https://httpbin.org/user-agent")
    print(f"Mac Identity: {resp.json()}")
    
    # 2. Be Windows
    print("\nMasking as Windows...")
    scraper.set_disguise("modern_windows")
    
    # Verify
    resp = scraper.get("https://httpbin.org/user-agent")
    print(f"Windows Identity: {resp.json()}")
    
    # 3. Bypass Hard Target with Disguise
    # Cloudflare checks TLS + UA consistency. Disguise ensures this matches.
    print("\nAttempting Bypass with Consistency...")
    resp = scraper.bypass("https://nowsecure.nl")
    print(f"Status: {resp.status_code}")

if __name__ == "__main__":
    main()
