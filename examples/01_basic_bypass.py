"""
Example 1: Basic One-Click Bypass

This script demonstrates the simplest way to use TitanScraper.
The bypass() method automatically handles:
1. Detecting antibots
2. Mimicking Chrome 120 (TLS)
3. Solving JSD (if needed)
4. Falling back to Browser (if needed)
5. Solving Captchas (if needed)
"""

from titan import TitanScraper

def main():
    # 1. Initialize
    scraper = TitanScraper()
    
    # 2. Target URL
    url = "https://nowsecure.nl" # Easier target
    # url = "https://coinlist.co/login" # Harder target

    print(f"Bypassing {url}...")

    # 3. One-Click Bypass
    response = scraper.bypass(url)

    # 4. Results
    print(f"Status: {response.status_code}")
    print(f"Title: {response.text.split('<title>')[1].split('</title>')[0] if '<title>' in response.text else 'Unknown'}")
    
if __name__ == "__main__":
    main()
