import random
import time
from collections import OrderedDict
from typing import Dict, Any, Optional

try:
    from fake_useragent import UserAgent
    HAS_UA = True
except ImportError:
    HAS_UA = False

class StealthManager:
    """Stealth mode implementation"""
    
    def __init__(self, 
                 randomize_headers: bool = True,
                 browser_quirks: bool = True,
                 simulate_viewport: bool = True):
        
        self.randomize_headers = randomize_headers
        self.browser_quirks = browser_quirks
        self.simulate_viewport = simulate_viewport
        
        # User Agent rotator
        if HAS_UA:
            try:
                self.ua = UserAgent(browsers=['chrome', 'edge'], os=['windows', 'macos'])
            except:
                self.ua = None
        else:
            self.ua = None
            
        # Generate a session fingerprint that stays consistent for this "User"
        self.fingerprint = self._generate_fingerprint()
        
    def _generate_fingerprint(self) -> Dict[str, Any]:
        """Generate a consistent browser fingerprint."""
        resolutions = [(1920, 1080), (1366, 768), (1536, 864), (1440, 900)]
        screen_w, screen_h = random.choice(resolutions)
        
        ua_string = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        if self.ua:
            try:
                ua_string = self.ua.random
            except:
                pass
                
        return {
            "screen_width": screen_w,
            "screen_height": screen_h,
            "viewport_width": screen_w, # Usually slightly less, but let's keep it simple or safe
            "viewport_height": screen_h - 100,
            "user_agent": ua_string,
            "locale": "en-US",
            "timezone": "America/New_York", # Ideally this should match IP, but we default to common
            "platform": "Win32" if "Windows" in ua_string else "MacIntel"
        }

    def get_fingerprint(self) -> Dict[str, Any]:
        """Return the current session fingerprint."""
        return self.fingerprint
        
    def transform_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Apply stealth transformations to headers"""
        if self.simulate_viewport:
            headers = self._add_screen_info(headers)
        
        if self.randomize_headers:
            headers = self._randomize_headers(headers)
            
        if self.browser_quirks:
            headers = self._order_headers(headers)
            
        # Ensure User-Agent matches fingerprint
        headers['User-Agent'] = self.fingerprint['user_agent']
            
        return headers
            
    def _add_screen_info(self, headers: Dict[str, str]) -> Dict[str, str]:
        headers = headers.copy()
        headers['Viewport-Width'] = str(self.fingerprint['viewport_width'])
        headers['Viewport-Height'] = str(self.fingerprint['viewport_height'])
        headers['Device-Pixel-Ratio'] = str(random.choice([1.0, 1.25, 1.5, 2.0]))
        return headers
    
    def _randomize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        headers = headers.copy()
        # Ensure common headers exist
        if 'Accept-Language' not in headers:
            headers['Accept-Language'] = 'en-US,en;q=0.9'
        if 'Accept-Encoding' not in headers:
            headers['Accept-Encoding'] = 'gzip, deflate, br'
        if 'Connection' not in headers:
            headers['Connection'] = 'keep-alive'
        return headers
        
    def _order_headers(self, headers: Dict[str, str]) -> OrderedDict:
        """Sort headers to match browser behavior"""
        # Chrome order (simplified)
        order = ['Host', 'Connection', 'sec-ch-ua', 'sec-ch-ua-mobile', 
                 'sec-ch-ua-platform', 'User-Agent', 'Accept', 
                 'Sec-Fetch-Site', 'Sec-Fetch-Mode', 'Sec-Fetch-Dest', 
                 'Referer', 'Accept-Encoding', 'Accept-Language', 'Cookie']
                 
        ordered = OrderedDict()
        for key in order:
            # Case insensitive lookup
            matches = [k for k in headers.keys() if k.lower() == key.lower()]
            if matches:
                ordered[matches[0]] = headers[matches[0]]
                
        # Add remaining
        for k, v in headers.items():
            if k not in ordered and k not in [o.lower() for o in order]: # check effectively
                ordered[k] = v
                
        return ordered
        
    def get_browser_args(self) -> list:
        """Return arguments for launching a browser (Playwright/Selenium)"""
        return [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            f"--user-agent={self.fingerprint['user_agent']}",
            f"--window-size={self.fingerprint['screen_width']},{self.fingerprint['screen_height']}"
        ]

    def get_stealth_scripts(self) -> list:
        """Return a list of JS scripts to inject for deep spoofing."""
        scripts = []
        
        # 1. Canvas Spoofing (Noise)
        scripts.append("""
            (() => {
                const toDataURL = HTMLCanvasElement.prototype.toDataURL;
                const getImageData = CanvasRenderingContext2D.prototype.getImageData;
                
                // Add noise to toDataURL
                HTMLCanvasElement.prototype.toDataURL = function(type) {
                    const ctx = this.getContext('2d');
                    if (ctx) {
                        // Draw a tiny invisible pixel with slight randomness
                        const shift = Math.floor(Math.random() * 2) - 1; // -1, 0, or 1
                        ctx.fillStyle = `rgba(0,0,0,0.0${Math.abs(shift)})`;
                        ctx.fillRect(0, 0, 1, 1);
                    }
                    return toDataURL.apply(this, arguments);
                };
                
                // Add noise to getImageData
                CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {
                    const image = getImageData.apply(this, arguments);
                    // Modify a few random channels slightly
                    for (let i = 0; i < image.data.length; i += 4) {
                         if (Math.random() < 0.01) { // 1% of pixels
                             image.data[i] = image.data[i] + (Math.floor(Math.random() * 4) - 2); 
                         }
                    }
                    return image;
                };
            })();
        """)
        
        # 2. WebGL Spoofing (Vendor/Renderer)
        # We want to match the fake UA (Windows/Chrome) if possible, or just be generic.
        # Ideally this should be dynamic based on fingerprint, but for now generic high-end GPU.
        scripts.append("""
            (() => {
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    // UNMASKED_VENDOR_WEBGL
                    if (parameter === 37445) return 'Google Inc. (NVIDIA)';
                    // UNMASKED_RENDERER_WEBGL
                    if (parameter === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)';
                    return getParameter.apply(this, arguments);
                };
            })();
        """)
        
        # 3. AudioContext Spoofing
        scripts.append("""
            (() => {
                const getChannelData = AudioBuffer.prototype.getChannelData;
                AudioBuffer.prototype.getChannelData = function(channel) {
                    const data = getChannelData.apply(this, arguments);
                    // Add tiny noise
                    for (let i = 0; i < data.length; i+=100) {
                        data[i] = data[i] + (Math.random() * 0.0000001);
                    }
                    return data;
                };
            })();
        """)
        
        return scripts
