"""
Example 2: Advanced Configuration (Proxies & TLS)

This script demonstrates how to:
1. Use Proxies (Rotational or Static)
2. Change the TLS Fingerprint (Impersonate Safari/Chrome/etc)
"""

from titan import TitanScraper

def main():
    # --- PROXIES ---
    # Supports HTTP/HTTPS/SOCKS5
    proxies = {
        # "http": "http://user:pass@host:port",
        # "https": "http://user:pass@host:port",
    }
    
    # --- TLS FINGERPRINTS ---
    # Available: chrome100, chrome110, chrome120, safari15_3, firefox109
    # Use this to match the traffic to a specific browser profile.
    fingerprint = "safari15_3"

    print(f"Initializing with {fingerprint} and custom proxies...")
    
    # Initialize with proxies
    scraper = TitanScraper(proxies=proxies)
    
    target = "https://httpbin.org/headers" # Good for checking headers
    
    # Use .get() directly with 'impersonate' argument
    # This uses the 'browserless' curl_cffi backend
    resp = scraper.get(target, impersonate=fingerprint)
    
    print(f"Status: {resp.status_code}")
    print("Headers received by server:")
    print(resp.text)

if __name__ == "__main__":
    main()
