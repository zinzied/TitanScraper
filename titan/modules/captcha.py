"""
Captcha Module
==============
Handles Turnstile and other challenge solving.
"""

import re
import time
import requests
from typing import Dict, Any, Optional

class CaptchaSolver:
    """Base class for captcha solving"""
    def solve(self, url: str, site_key: str, **kwargs) -> str:
        raise NotImplementedError

class TurnstileSolver:
    """Cloudflare Turnstile Solver"""
    
    def __init__(self, provider_config: Dict[str, Any] = None):
        self.provider_config = provider_config or {}
        
    def is_turnstile_challenge(self, html: str, headers: dict, status_code: int) -> bool:
        """Check if response contains Turnstile challenge"""
        if status_code in [403, 429, 503]:
            if 'cloudflare' in headers.get('Server', '').lower():
                if 'turnstile' in html or 'cf-turnstile' in html:
                    return True
        return False

    def extract_turnstile_data(self, html: str) -> Dict[str, str]:
        import re
        site_key = None
        # Try various patterns
        patterns = [
            r'data-sitekey="([0-9A-Za-z]{40})"',
            r'cFPWv\s?:\s?[\'"]([^\'"]+)[\'"]',
            r'["\']sitekey["\']\s*:\s*["\']([^"\']+)["\']'
        ]
        
        for p in patterns:
            match = re.search(p, html)
            if match:
                site_key = match.group(1)
                break
                
        if not site_key:
            raise ValueError("Could not find Turnstile site key")
            
        return {'site_key': site_key}
        
    def solve(self, url: str, html: str) -> str:
        """
        Solve the challenge.
        Note: This requires an external provider (2captcha, capsolver, etc)
        or a browser-based solver.
        """
        data = self.extract_turnstile_data(html)
        site_key = data['site_key']
        
        provider = self.provider_config.get('provider')
        if not provider:
            raise ValueError("No captcha provider configured")
            
        from .external_solvers import ExternalSolver
        api_key = self.provider_config.get('api_key')
        if not api_key:
            raise ValueError(f"API Key required for provider {provider}")
            
        solver = ExternalSolver(provider, api_key, **self.provider_config)
        token = solver.solve_turnstile(site_key, url)
        
        if not token:
            raise ValueError(f"External solver ({provider}) failed to solve Turnstile")
            
        return token
