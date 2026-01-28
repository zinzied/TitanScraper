"""
Example 5: AI Data Collection

To train the AI model (titan.modules.ai_captcha), you need labeled images.
This script shows how to capture captcha images from a live site.
"""

from titan import TitanScraper
import os
import time
import random

def main():
    scraper = TitanScraper()
    
    # Target URL with a captcha
    url = "https://www.google.com/recaptcha/api2/demo" # Example
    # For a real target, identify the CSS selector of the captcha image
    # e.g. "#captcha-img" or "img.captcha"
    selector = "iframe" # Just capturing the iframe for demo
    
    output_dir = "captured_captchas"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Navigating and capturing...")
    
    # Use Browser Manager to screenshot a specific element
    # This is better than full screenshots because it crops exactly to the captcha
    
    filename = f"{output_dir}/captcha_{int(time.time())}.png"
    
    success = scraper.browser_manager.save_element_screenshot(
        url, 
        selector, 
        filename
    )
    
    if success:
        print(f"[+] Saved {filename}")
        print("Next Step: Manually rename this file to the real text (e.g. 'AB12.png') and move to training folder.")
    else:
        print("[-] Failed to capture. Check selector.")

if __name__ == "__main__":
    main()
