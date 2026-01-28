"""
Example 3: Session Persistence

Building "Trust" is key. A fresh browser session looks suspicious.
A session with 100+ pages of history and old cookies looks human.

This script demonstrates saving and loading your session.
"""

from titan import TitanScraper
import os

SESSION_FILE = "my_session.json"

def main():
    scraper = TitanScraper()
    
    # 1. Load previous session
    if os.path.exists(SESSION_FILE):
        print("Loading previous session...")
        scraper.load_session(SESSION_FILE)
    else:
        print("Starting fresh session...")

    # 2. Do some work (e.g. Login or Browse)
    # We simulate this by visiting a site that sets cookies
    url = "https://www.google.com" 
    scraper.bypass(url)
    
    print(f"Current Cookies: {len(scraper.cookies)}")

    # 3. Save session for next time
    # This saves Cookies (including cf_clearance) and Headers
    scraper.save_session(SESSION_FILE)
    print(f"Session saved to {SESSION_FILE}")

if __name__ == "__main__":
    main()
