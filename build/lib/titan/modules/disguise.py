"""
Disguise Module
===============
Enforces 100% consistency across Network (TLS), HTTP (Headers), and Hardware (Browser).
Defines 'Truth Profiles' to defeat advanced fingerprinting (Cloudflare V3, Enterprise).
"""

import random
from typing import Dict, Any, Optional

class DisguiseManager:
    """Manages consistent fingerprint profiles."""
    
    PROFILES = {
        "modern_windows": {
            "name": "modern_windows",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "impersonate": "chrome120", # curl_cffi fingerprint
            "platform": "Win32",
            "vendor": "Google Inc. (NVIDIA)",
            "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "hardware_concurrency": 16,
            "viewport_width": 1920,
            "viewport_height": 1080,
            "device_memory": 8, # GB
        },
        "modern_mac": {
            "name": "modern_mac",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
            "impersonate": "safari15_3", # curl_cffi fingerprint
            "platform": "MacIntel",
            "vendor": "Apple Inc.",
            "renderer": "Apple GPU",
            "hardware_concurrency": 8,
            "viewport_width": 1440,
            "viewport_height": 900,
            "device_memory": 8,
        }
    }
    
    def __init__(self, profile_name: str = "modern_windows"):
        self.set_profile(profile_name)
        
    def set_profile(self, profile_name: str):
        if profile_name not in self.PROFILES:
            raise ValueError(f"Unknown profile: {profile_name}. Valid: {list(self.PROFILES.keys())}")
        self.current_profile = self.PROFILES[profile_name]
        
    def get_profile(self) -> Dict[str, Any]:
        return self.current_profile
        
    def get_random_profile(self) -> Dict[str, Any]:
        name = random.choice(list(self.PROFILES.keys()))
        self.set_profile(name)
        return self.current_profile

    def get_injection_script(self) -> str:
        """Returns JS to force browser properties to match profile."""
        p = self.current_profile
        return f"""
            (() => {{
                // Overwrite Platform
                Object.defineProperty(navigator, 'platform', {{ get: () => '{p['platform']}' }});
                
                // Overwrite Hardware Concurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {p['hardware_concurrency']} }});
                
                // Overwrite Device Memory
                Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {p['device_memory']} }});
                
                // Overwrite WebGL
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    // UNMASKED_VENDOR_WEBGL
                    if (parameter === 37445) return '{p['vendor']}';
                    // UNMASKED_RENDERER_WEBGL
                    if (parameter === 37446) return '{p['renderer']}';
                    return getParameter.apply(this, arguments);
                }};
            }})();
        """
