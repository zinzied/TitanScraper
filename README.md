# TitanScraper V2

![TitanScraper Banner](banner.png)

**The Ultimate Anti-Bot Scraper for Python.**

TitanScraper is a high-performance scraping library designed to bypass the toughest anti-bot protections (Cloudflare, Akamai, Datadome, etc.). It uses a tiered approach, starting with lightweight requests and escalating to full browser automation with AI solvers only when necessary.

## Features

-   **Tier 1: Intelligent Requests**: Handles headers, TLS fingerprinting (simulated), and simple redirects.
-   **Tier 2: JSD Solver**: Native Go-based solver for Cloudflare JavaScript challenges.
-   **Tier 3: Browser Fallback**: Auto-launches a stealth Playwright browser for 403/503 bypass (G2, CoinList, etc.).
-   **Tier 4: Captcha Solving**:
    -   **Cloudflare Turnstile**: Auto-detects and human-clicks or uses external solvers.
    -   **reCAPTCHA v2/v3**: Native audio solving + Support for **2Captcha, CapMonster, Anti-Captcha**.
    -   **AI Custom Model**: PyTorch-based CNN for text captchas.
-   **Deep Fingerprint Spoofing**: Injects noise into Canvas, WebGL, and AudioContext to defeat device tracking.
-   **Session Persistence**: Save/Load cookies to build "Trust Scores" across sessions.
-   **Smart Auto-Detection**: Automatically identifies protection (Cloudflare, Akamai, AWS WAF) and selects the best bypass strategy (TLS Rotation, Browser, etc.).
-   **Proxies & Stealth**: Built-in support for rotating proxies and fingerprint randomization (User-Agent, Viewport, Locale).

## Installation

```bash
# 1. Install Python packages
pip install TitanScraper-Pro

# 2. Install Playwright Browsers
playwright install chromium

# 3. Setup JSD Solver (Go required)
python setup_jsd.py

# 4. System Requirements
# Install ffmpeg for Audio Captcha solving
```

## Usage

### 1. One-Click Bypass (Recommended)
Automatically handles challenges, captchas, and fallbacks.

```python
from titan import TitanScraper

# Optional: Add Proxies
proxies = {
    "http": "http://user:pass@host:port",
    "https": "http://user:pass@host:port"
}

scraper = TitanScraper(proxies=proxies)

# Just provide the URL
response = scraper.bypass("https://nowsecure.nl")

print(response.status_code)
print(response.content)
```

### 2. Advanced / Manual Control

```python
# Access specific modules
scraper.jsd_solver.solve(url)
cookies = scraper.browser_manager.get_cookies(url)

# Activate Disguise System (100% Consistency)
scraper.set_disguise("modern_mac") # or "modern_windows"
```


### 3. Disguise System (Consistency Engine)

For targets detecting "Mismatched Fingerprints" (Cloudflare V3/Enterprise):

```python
# 1. Masquerade as a Mac user (Safari + MacIntel + Apple GPU)
scraper.set_disguise("modern_mac")

# 2. Masquerade as a Windows user (Chrome + Win32 + NVIDIA)
scraper.set_disguise("modern_windows")

# Now all requests will perfectly match this identity.
scraper.bypass("https://strict-site.com")
```

**Why use this?**
High-end antibots check if your User-Agent matches your TLS Fingerprint and your GPU Renderer.
-   If you just change User-Agent to "iPhone" but use Python TLS, you get banned.
-   The **Disguise System** syncs *everything* to match the chosen profile.

#### Available Profiles & Parameters

| Parameter | `modern_windows` | `modern_mac` |
| :--- | :--- | :--- |
| **User-Agent** | Chrome 120 (Win) | Safari 15.3 (Mac) |
| **TLS Handshake** | `chrome120` | `safari15_3` |
| **Navigator Platform** | `Win32` | `MacIntel` |
| **WebGL Vendor** | `Google Inc. (NVIDIA)` | `Apple Inc.` |
| **WebGL Renderer** | `NVIDIA GeForce RTX 3060...` | `Apple GPU` |
| **Hardware Core Count** | 16 | 8 |
| **Device Memory (GB)** | 8 | 8 |
| **Default Viewport** | 1920x1080 | 1440x900 |

### 4. External Captcha Providers

Use professional services for 100% reliability on hard targets.

```python
captcha_config = {
    "provider": "2captcha", # '2captcha', 'capmonster', 'anticaptcha'
    "api_key": "YOUR_API_KEY"
}

scraper = TitanScraper(captcha_config=captcha_config)
scraper.bypass("https://protected-site.com")
```

### 5. Training the AI Captcha Solver

1.  **Collect Data**:
    ```python
    scraper.browser_manager.save_element_screenshot(url, "#captcha-img", "data/label.png")
    ```
2.  **Train**:
    ```bash
    python train_captcha.py --mode train --data_dir ./data --epochs 20
    ```
3.  **Predict**:
    ```bash
    python train_captcha.py --mode predict --image ./test.png
    ```

## Roadmap & Suggestions

To defeat even more advanced systems:

1.  **Residential Proxy Rotation**: Integrate with providers (BrightData, Smartproxy) to rotate IPs per request.
2.  **Machine Learning Behavior**: Train a model on real user mouse movements instead of just Bezier curves.
